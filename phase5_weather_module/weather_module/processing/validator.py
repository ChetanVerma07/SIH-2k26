"""Data quality validation for weather observations.

Checks performed:
  - missing values (required fields absent)
  - duplicate timestamps within a series
  - impossible temperature values (outside physically plausible range)
  - impossible humidity values (outside 0-100%)
  - impossible pressure values (outside plausible sea-level-adjusted range)
  - negative solar radiation
  - unrealistic sudden jumps between consecutive observations
  - invalid coordinates (outside valid lat/lon range)

Suspicious data is never silently deleted. Each observation is annotated
with a quality flag (VALID / MISSING / SUSPECT / CORRECTED) and a reason.
Where practical, a repaired value is substituted (CORRECTED) but the
original problem is always recorded in `quality_reason`.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from weather_module.models.weather import WeatherObservation, QualityFlag, FieldQuality

# Physically plausible bounds (generous, to cover extreme but real climates)
TEMP_MIN_C, TEMP_MAX_C = -90.0, 60.0
HUMIDITY_MIN, HUMIDITY_MAX = 0.0, 100.0
PRESSURE_MIN_HPA, PRESSURE_MAX_HPA = 300.0, 1100.0  # 300 hPa covers high-altitude sites
WIND_MIN_MS, WIND_MAX_MS = 0.0, 120.0

# Sudden-jump thresholds between consecutive observations of a series
MAX_TEMP_JUMP_C = 15.0          # per single sampling step
MAX_PRESSURE_JUMP_HPA = 20.0
MAX_HUMIDITY_JUMP_PCT = 60.0


@dataclass
class QualityStats:
    total: int = 0
    valid: int = 0
    missing: int = 0
    suspect: int = 0
    corrected: int = 0

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "valid": self.valid,
            "missing": self.missing,
            "suspect": self.suspect,
            "corrected": self.corrected,
        }


def _flag(obs: WeatherObservation, field: str, quality: QualityFlag, reason: str) -> None:
    obs.field_quality[field] = FieldQuality(quality=quality, reason=reason)
    # Escalate the observation-level flag: MISSING/SUSPECT/CORRECTED > VALID.
    # Priority: SUSPECT worst, then MISSING, then CORRECTED, then VALID.
    priority = {
        QualityFlag.SUSPECT: 3,
        QualityFlag.MISSING: 2,
        QualityFlag.CORRECTED: 1,
        QualityFlag.VALID: 0,
    }
    if priority[quality] > priority.get(obs.quality, 0):
        obs.quality = quality
        obs.quality_reason = reason


def validate_coordinates(obs: WeatherObservation) -> None:
    if not (-90.0 <= obs.latitude <= 90.0) or not (-180.0 <= obs.longitude <= 180.0):
        _flag(obs, "coordinates", QualityFlag.SUSPECT,
              f"Invalid coordinates ({obs.latitude}, {obs.longitude})")


def validate_temperature(obs: WeatherObservation) -> None:
    if obs.temperature_c is None:
        _flag(obs, "temperature_c", QualityFlag.MISSING, "Temperature value missing")
    elif not (TEMP_MIN_C <= obs.temperature_c <= TEMP_MAX_C):
        _flag(obs, "temperature_c", QualityFlag.SUSPECT,
              f"Temperature {obs.temperature_c}\u00b0C outside plausible range "
              f"[{TEMP_MIN_C}, {TEMP_MAX_C}]")


def validate_humidity(obs: WeatherObservation) -> None:
    if obs.humidity_pct is None:
        _flag(obs, "humidity_pct", QualityFlag.MISSING, "Humidity value missing")
    elif not (HUMIDITY_MIN <= obs.humidity_pct <= HUMIDITY_MAX):
        original = obs.humidity_pct
        repaired = max(HUMIDITY_MIN, min(HUMIDITY_MAX, obs.humidity_pct))
        obs.humidity_pct = repaired
        _flag(obs, "humidity_pct", QualityFlag.CORRECTED,
              f"Humidity {original}% outside [0,100]; clamped to {repaired}%")


def validate_pressure(obs: WeatherObservation) -> None:
    if obs.pressure_hpa is None:
        _flag(obs, "pressure_hpa", QualityFlag.MISSING, "Pressure value missing")
    elif not (PRESSURE_MIN_HPA <= obs.pressure_hpa <= PRESSURE_MAX_HPA):
        _flag(obs, "pressure_hpa", QualityFlag.SUSPECT,
              f"Pressure {obs.pressure_hpa} hPa outside plausible range "
              f"[{PRESSURE_MIN_HPA}, {PRESSURE_MAX_HPA}]")


def validate_solar_radiation(obs: WeatherObservation) -> None:
    if obs.solar_radiation_wm2 is None:
        _flag(obs, "solar_radiation_wm2", QualityFlag.MISSING, "Solar radiation value missing")
    elif obs.solar_radiation_wm2 < 0:
        original = obs.solar_radiation_wm2
        obs.solar_radiation_wm2 = 0.0
        _flag(obs, "solar_radiation_wm2", QualityFlag.CORRECTED,
              f"Negative solar radiation {original} W/m^2 clamped to 0")
    elif obs.solar_radiation_wm2 > 1500:
        _flag(obs, "solar_radiation_wm2", QualityFlag.SUSPECT,
              f"Solar radiation {obs.solar_radiation_wm2} W/m^2 exceeds plausible maximum")


def validate_single(obs: WeatherObservation) -> WeatherObservation:
    """Run all single-observation checks (no series context)."""
    validate_coordinates(obs)
    validate_temperature(obs)
    validate_humidity(obs)
    validate_pressure(obs)
    validate_solar_radiation(obs)
    return obs


def detect_duplicate_timestamps(observations: List[WeatherObservation]) -> None:
    seen = {}
    for obs in observations:
        key = obs.timestamp
        if key in seen:
            _flag(obs, "timestamp", QualityFlag.SUSPECT,
                  f"Duplicate timestamp {obs.timestamp.isoformat()}")
            _flag(seen[key], "timestamp", QualityFlag.SUSPECT,
                  f"Duplicate timestamp {obs.timestamp.isoformat()}")
        else:
            seen[key] = obs


def detect_sudden_jumps(observations: List[WeatherObservation]) -> None:
    ordered = sorted(observations, key=lambda o: o.timestamp)
    for prev, curr in zip(ordered, ordered[1:]):
        if prev.temperature_c is not None and curr.temperature_c is not None:
            if abs(curr.temperature_c - prev.temperature_c) > MAX_TEMP_JUMP_C:
                _flag(curr, "temperature_c", QualityFlag.SUSPECT,
                      f"Abrupt temperature change of "
                      f"{curr.temperature_c - prev.temperature_c:.1f}\u00b0C since previous observation")
        if prev.pressure_hpa is not None and curr.pressure_hpa is not None:
            if abs(curr.pressure_hpa - prev.pressure_hpa) > MAX_PRESSURE_JUMP_HPA:
                _flag(curr, "pressure_hpa", QualityFlag.SUSPECT,
                      f"Abrupt pressure change of "
                      f"{curr.pressure_hpa - prev.pressure_hpa:.1f} hPa since previous observation")
        if prev.humidity_pct is not None and curr.humidity_pct is not None:
            if abs(curr.humidity_pct - prev.humidity_pct) > MAX_HUMIDITY_JUMP_PCT:
                _flag(curr, "humidity_pct", QualityFlag.SUSPECT,
                      f"Abrupt humidity change of "
                      f"{curr.humidity_pct - prev.humidity_pct:.1f}% since previous observation")


def validate_series(observations: List[WeatherObservation]) -> QualityStats:
    """Validate an entire time series in place and return summary statistics."""
    for obs in observations:
        validate_single(obs)
    detect_duplicate_timestamps(observations)
    detect_sudden_jumps(observations)

    stats = QualityStats(total=len(observations))
    for obs in observations:
        stats.total += 0
        if obs.quality == QualityFlag.VALID:
            stats.valid += 1
        elif obs.quality == QualityFlag.MISSING:
            stats.missing += 1
        elif obs.quality == QualityFlag.SUSPECT:
            stats.suspect += 1
        elif obs.quality == QualityFlag.CORRECTED:
            stats.corrected += 1
    return stats
