"""Resampling / interpolation of a WeatherObservation time series.

Supports converting a series with one native interval (e.g. 3-hourly
forecast data) into a different target interval (e.g. 30 minutes),
using linear interpolation of numeric fields. Interpolated points are
marked with data_source=INTERPOLATED and quality=CORRECTED, with a
quality_reason explaining the synthesis.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional

from weather_module.models.weather import WeatherObservation, QualityFlag, DataSource

NUMERIC_FIELDS = [
    "temperature_c", "humidity_pct", "pressure_hpa", "solar_radiation_wm2",
    "wind_speed_ms", "wind_direction_deg", "cloud_cover_pct", "precipitation_mm",
]


def _lerp(a: Optional[float], b: Optional[float], t: float) -> Optional[float]:
    if a is None or b is None:
        return a if a is not None else b
    return a + (b - a) * t


def resample(
    observations: List[WeatherObservation], interval_minutes: int
) -> List[WeatherObservation]:
    """Resample a sorted observation list to a fixed interval via linear interpolation.

    Requires at least 2 observations. Observations must be sorted by timestamp
    (this function sorts them defensively). Output spans [first.timestamp, last.timestamp].
    """
    if not observations:
        return []
    obs = sorted(observations, key=lambda o: o.timestamp)
    if len(obs) == 1:
        return [obs[0]]

    step = timedelta(minutes=interval_minutes)
    start, end = obs[0].timestamp, obs[-1].timestamp
    result: List[WeatherObservation] = []

    t = start
    idx = 0
    while t <= end:
        # advance idx so that obs[idx] <= t <= obs[idx+1]
        while idx < len(obs) - 2 and obs[idx + 1].timestamp <= t:
            idx += 1
        left, right = obs[idx], obs[min(idx + 1, len(obs) - 1)]

        if t == left.timestamp:
            result.append(left)
        elif t == right.timestamp:
            result.append(right)
        else:
            span = (right.timestamp - left.timestamp).total_seconds()
            frac = 0.0 if span == 0 else (t - left.timestamp).total_seconds() / span
            kwargs = {}
            for field_name in NUMERIC_FIELDS:
                kwargs[field_name] = _lerp(
                    getattr(left, field_name), getattr(right, field_name), frac
                )
            new_obs = WeatherObservation(
                timestamp=t,
                latitude=left.latitude,
                longitude=left.longitude,
                location_name=left.location_name,
                data_source=DataSource.INTERPOLATED,
                solar_radiation_source=DataSource.INTERPOLATED,
                quality=QualityFlag.CORRECTED,
                quality_reason=f"Linearly interpolated between {left.timestamp.isoformat()} "
                               f"and {right.timestamp.isoformat()}",
                **kwargs,
            )
            result.append(new_obs)
        t += step

    return result
