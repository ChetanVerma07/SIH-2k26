"""
Phase 8 - Thermal performance metrics extractor.

Turns a raw indoor-temperature / heat-flux time series (from ANSYS or the
simplified model) into the handful of engineering metrics that actually
matter for judging a passive shelter design.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, asdict

from core.results_importer import ThermalTimeSeries


@dataclass
class ThermalMetrics:
    peak_indoor_temp_c: float
    min_indoor_temp_c: float
    mean_indoor_temp_c: float
    indoor_temp_swing_c: float
    peak_ambient_temp_c: float
    ambient_temp_swing_c: float
    decrement_factor: float          # indoor swing / ambient swing
    thermal_lag_hours: float         # time offset between ambient peak and indoor peak
    comfort_hours: float             # hours within comfort band
    comfort_pct: float
    peak_heat_flux_w_m2: float
    mean_heat_flux_w_m2: float
    total_heat_gain_kwh: float       # integrated positive heat flux over wall/roof area proxy

    def to_dict(self) -> dict:
        return asdict(self)


def extract_metrics(series: ThermalTimeSeries,
                     ambient_profile_c: list,
                     comfort_low_c: float,
                     comfort_high_c: float,
                     envelope_area_m2: float = 1.0) -> ThermalMetrics:

    temps = series.indoor_temp_c
    flux = series.heat_flux_w_m2
    hours = series.time_h

    peak_indoor = max(temps)
    min_indoor = min(temps)
    mean_indoor = statistics.fmean(temps)
    indoor_swing = peak_indoor - min_indoor

    peak_ambient = max(ambient_profile_c)
    min_ambient = min(ambient_profile_c)
    ambient_swing = peak_ambient - min_ambient

    decrement_factor = (indoor_swing / ambient_swing) if ambient_swing > 1e-6 else 0.0

    # thermal lag: hour-of-day of indoor peak minus hour-of-day of ambient peak
    peak_indoor_idx = temps.index(peak_indoor)
    peak_indoor_hour = hours[peak_indoor_idx] % 24
    peak_ambient_hour = ambient_profile_c.index(peak_ambient)
    thermal_lag = (peak_indoor_hour - peak_ambient_hour) % 24

    in_comfort = [1 for t in temps if comfort_low_c <= t <= comfort_high_c]
    total_duration_h = hours[-1] - hours[0] if len(hours) > 1 else 1.0
    step_h = total_duration_h / max(len(temps) - 1, 1)
    comfort_hours = len(in_comfort) * step_h
    comfort_pct = 100.0 * len(in_comfort) / len(temps)

    peak_flux = max(flux)
    mean_flux = statistics.fmean(flux)

    # crude trapezoidal integration of positive heat flux -> energy (kWh)
    gain_kwh = 0.0
    for i in range(1, len(flux)):
        dt_h = hours[i] - hours[i - 1]
        avg_flux = (max(flux[i], 0) + max(flux[i - 1], 0)) / 2.0
        gain_kwh += avg_flux * dt_h * envelope_area_m2 / 1000.0

    return ThermalMetrics(
        peak_indoor_temp_c=round(peak_indoor, 2),
        min_indoor_temp_c=round(min_indoor, 2),
        mean_indoor_temp_c=round(mean_indoor, 2),
        indoor_temp_swing_c=round(indoor_swing, 2),
        peak_ambient_temp_c=round(peak_ambient, 2),
        ambient_temp_swing_c=round(ambient_swing, 2),
        decrement_factor=round(decrement_factor, 3),
        thermal_lag_hours=round(thermal_lag, 2),
        comfort_hours=round(comfort_hours, 2),
        comfort_pct=round(comfort_pct, 1),
        peak_heat_flux_w_m2=round(peak_flux, 2),
        mean_heat_flux_w_m2=round(mean_flux, 2),
        total_heat_gain_kwh=round(gain_kwh, 3),
    )
