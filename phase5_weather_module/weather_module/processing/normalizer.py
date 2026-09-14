"""Unit normalization helpers.

Converts common provider unit variants into the module's SI standard:
    temperature -> Celsius
    pressure    -> hPa
    wind speed  -> m/s
    solar rad   -> W/m^2
"""
from __future__ import annotations
from typing import Optional


def fahrenheit_to_celsius(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def kelvin_to_celsius(k: float) -> float:
    return k - 273.15


def pa_to_hpa(pa: float) -> float:
    return pa / 100.0


def mph_to_ms(mph: float) -> float:
    return mph * 0.44704


def kmh_to_ms(kmh: float) -> float:
    return kmh / 3.6


def kwh_m2_to_wm2(kwh_m2: float, interval_hours: float) -> float:
    """Convert accumulated energy (kWh/m^2) over an interval to average power (W/m^2)."""
    if interval_hours <= 0:
        return 0.0
    return (kwh_m2 * 1000.0) / interval_hours


def clamp_pct(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return max(0.0, min(100.0, value))


def normalize_wind_direction(deg: Optional[float]) -> Optional[float]:
    if deg is None:
        return None
    return deg % 360.0
