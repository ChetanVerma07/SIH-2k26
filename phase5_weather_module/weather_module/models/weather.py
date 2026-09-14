"""Standardized weather observation model, quality flags, and data source labels.

All units are SI unless otherwise noted:
    temperature_c      : degrees Celsius
    humidity_pct        : relative humidity, percent (0-100)
    pressure_hpa         : atmospheric pressure, hectopascals (hPa)
    solar_radiation_wm2   : W/m^2 (global horizontal irradiance)
    wind_speed_ms         : meters/second
    wind_direction_deg    : degrees (0=N, 90=E, 180=S, 270=W)
    cloud_cover_pct       : percent (0-100)
    precipitation_mm      : millimeters (accumulated over the observation interval)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional


class QualityFlag(str, Enum):
    VALID = "VALID"
    MISSING = "MISSING"
    SUSPECT = "SUSPECT"
    CORRECTED = "CORRECTED"


class DataSource(str, Enum):
    """Provenance of a data value. Never present ESTIMATED/MOCK as MEASURED."""
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    MOCK = "MOCK"
    FORECAST = "FORECAST"
    INTERPOLATED = "INTERPOLATED"


@dataclass
class FieldQuality:
    """Per-field quality metadata for one observation."""
    quality: QualityFlag = QualityFlag.VALID
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {"quality": self.quality.value, "reason": self.reason}


@dataclass
class WeatherObservation:
    """A single, normalized weather observation at a point in time."""

    timestamp: datetime
    latitude: float
    longitude: float
    location_name: Optional[str] = None

    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    solar_radiation_wm2: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    cloud_cover_pct: Optional[float] = None
    precipitation_mm: Optional[float] = None

    solar_radiation_source: DataSource = DataSource.MEASURED
    data_source: DataSource = DataSource.MEASURED

    # Overall observation-level quality (worst-case of field-level checks)
    quality: QualityFlag = QualityFlag.VALID
    quality_reason: Optional[str] = None

    # Optional per-field quality detail, populated by the validator
    field_quality: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "timestamp": self.timestamp.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_name": self.location_name,
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "pressure_hpa": self.pressure_hpa,
            "solar_radiation_wm2": self.solar_radiation_wm2,
            "wind_speed_ms": self.wind_speed_ms,
            "wind_direction_deg": self.wind_direction_deg,
            "cloud_cover_pct": self.cloud_cover_pct,
            "precipitation_mm": self.precipitation_mm,
            "solar_radiation_source": self.solar_radiation_source.value,
            "data_source": self.data_source.value,
            "quality": self.quality.value,
            "quality_reason": self.quality_reason,
        }
        if self.field_quality:
            d["field_quality"] = {
                k: (v.to_dict() if isinstance(v, FieldQuality) else v)
                for k, v in self.field_quality.items()
            }
        return d

    @staticmethod
    def field_names():
        return [
            "timestamp", "latitude", "longitude", "location_name",
            "temperature_c", "humidity_pct", "pressure_hpa",
            "solar_radiation_wm2", "wind_speed_ms", "wind_direction_deg",
            "cloud_cover_pct", "precipitation_mm",
            "solar_radiation_source", "data_source", "quality", "quality_reason",
        ]
