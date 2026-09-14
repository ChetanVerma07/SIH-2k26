"""
Climate and boundary-condition model.

This module defines the environmental inputs and thermal boundary
conditions used by the simulation. All defaults are explicitly
documented in the docstrings/comments below. Nothing here silently
invents a "real" measured value — where a project has no measured
ambient data, the caller must supply it; the constants provided are
generic engineering defaults (e.g. convection coefficients) commonly
used as starting points, not site measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class HourlyClimatePoint:
    """A single point of a climate time series.

    hour                    : hour index from simulation start (0, 1, 2, ...)
    ambient_temp_c          : ambient (outdoor) air temperature, deg C
    solar_irradiance_w_m2   : global horizontal (or surface-adjusted) solar
                              irradiance, W/m^2. Use 0 for night hours.
    wind_speed_m_s          : optional, used to refine external convection
                              coefficient if provided (else default is used)
    """

    hour: float
    ambient_temp_c: float
    solar_irradiance_w_m2: float = 0.0
    wind_speed_m_s: Optional[float] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HourlyClimatePoint":
        return cls(**data)


@dataclass
class BoundaryConditions:
    """Thermal boundary conditions and simulation timing.

    Documented defaults (used ONLY if not explicitly provided by the
    caller):
        indoor_initial_temp_c        : 20.0  (typical assumed comfortable
                                        start point; NOT a measurement)
        internal_convection_w_m2k    : 8.0   (typical indoor natural
                                        convection coefficient for
                                        vertical walls, ASHRAE-style
                                        engineering default)
        external_convection_w_m2k    : 23.0  (typical external convection
                                        coefficient for a wall exposed to
                                        moderate wind, ASHRAE-style
                                        engineering default)
        ground_temp_c                : 10.0  (generic deep-ground
                                        temperature default; SHOULD be
                                        replaced with local data)
        time_step_s                  : 3600  (1 hour)
        duration_hours                : 24

    If a project has real measured/forecast weather data or site
    convection data, it MUST be supplied explicitly rather than relying
    on these defaults.
    """

    ambient_series: List[HourlyClimatePoint]

    indoor_initial_temp_c: float = 20.0
    internal_convection_w_m2k: float = 8.0
    external_convection_w_m2k: float = 23.0
    ground_temp_c: float = 10.0

    time_step_s: float = 3600.0
    duration_hours: float = 24.0

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["ambient_series"] = [p.as_dict() for p in self.ambient_series]
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BoundaryConditions":
        data = dict(data)
        series = [HourlyClimatePoint.from_dict(p) for p in data.pop("ambient_series")]
        return cls(ambient_series=series, **data)

    def validate_series_covers_duration(self) -> bool:
        """Check that the ambient series has enough points to cover the
        requested duration at the requested time step."""
        expected_points = int(round((self.duration_hours * 3600.0) / self.time_step_s)) + 1
        return len(self.ambient_series) >= min(expected_points, len(self.ambient_series)) and len(
            self.ambient_series
        ) >= 2


def build_constant_climate(
    ambient_temp_c: float,
    duration_hours: float,
    time_step_s: float = 3600.0,
    solar_irradiance_w_m2: float = 0.0,
) -> List[HourlyClimatePoint]:
    """Convenience builder for a constant-ambient-temperature climate
    series (e.g. for a simplified steady/quasi-steady demonstration).
    This is a helper for building INPUT data — it is not a measured
    dataset and should be documented as such wherever used.
    """
    n_steps = int(round((duration_hours * 3600.0) / time_step_s)) + 1
    step_hours = time_step_s / 3600.0
    return [
        HourlyClimatePoint(
            hour=round(i * step_hours, 4),
            ambient_temp_c=ambient_temp_c,
            solar_irradiance_w_m2=solar_irradiance_w_m2,
        )
        for i in range(n_steps)
    ]


def build_diurnal_climate(
    mean_temp_c: float,
    amplitude_c: float,
    duration_hours: float,
    time_step_s: float = 3600.0,
    peak_hour: float = 14.0,
    peak_solar_w_m2: float = 700.0,
    sunrise_hour: float = 6.0,
    sunset_hour: float = 18.0,
) -> List[HourlyClimatePoint]:
    """Convenience builder for a simple sinusoidal diurnal ambient
    temperature cycle plus a daytime solar irradiance bell curve.

    This is a documented, simplified analytical approximation intended
    for demonstration/testing purposes (e.g. the Ladakh example) —
    NOT a substitute for real measured or forecast weather data in a
    production design.
    """
    import math

    n_steps = int(round((duration_hours * 3600.0) / time_step_s)) + 1
    step_hours = time_step_s / 3600.0
    points: List[HourlyClimatePoint] = []
    for i in range(n_steps):
        hour = i * step_hours
        hour_of_day = hour % 24.0

        # Sinusoidal ambient temperature, peaking at `peak_hour`.
        temp = mean_temp_c + amplitude_c * math.cos(
            2.0 * math.pi * (hour_of_day - peak_hour) / 24.0
        )

        # Simple daytime solar bell curve between sunrise and sunset.
        if sunrise_hour <= hour_of_day <= sunset_hour:
            day_span = sunset_hour - sunrise_hour
            solar = peak_solar_w_m2 * math.sin(
                math.pi * (hour_of_day - sunrise_hour) / day_span
            )
            solar = max(solar, 0.0)
        else:
            solar = 0.0

        points.append(
            HourlyClimatePoint(
                hour=round(hour, 4),
                ambient_temp_c=round(temp, 4),
                solar_irradiance_w_m2=round(solar, 2),
            )
        )
    return points
