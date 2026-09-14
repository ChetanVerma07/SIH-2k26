"""
simulation.py
=============

Transient (time-stepping) thermal simulation of a :class:`Shelter`.

Model summary
-------------

At every timestep the engine:

1. Reads the ambient temperature and solar radiation for that timestep
   (constant or time-varying, see :func:`_resample_to_steps`).
2. Computes conductive heat loss through walls, roof, floor and openings
   using ``Q = U * A * (T_indoor - T_outdoor)``.
3. Computes solar heat gain using ``Q_solar = I * A_eff * alpha``.
4. Sums these into a net heat flow into the shelter.
5. Updates the indoor temperature using a lumped-capacitance explicit
   Euler step: ``dT = net_heat_flow * dt / C``.
6. Records every quantity for that timestep.

This is a single-node ("lumped") model: the entire indoor air volume plus
building fabric is treated as one uniform temperature. It is a reasonable
level of fidelity for an early-stage design-comparison tool, but it is
**not** a substitute for a full transient CFD/finite-element simulation
(e.g. ANSYS). See the project README for a full list of assumptions and
limitations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

import numpy as np
import pandas as pd

from .physics import conduction_heat_flow, solar_heat_gain, temperature_change
from .shelter import Shelter
from .validation import (
    validate_comfort_range,
    validate_non_negative_sequence,
    validate_positive,
    validate_temperature_celsius,
)

# A time-varying input can be given as a constant number, a plain list/tuple,
# a NumPy array, or a Pandas Series.
TimeSeriesInput = Union[float, int, list, tuple, np.ndarray, pd.Series]


@dataclass
class SimulationResult:
    """
    Structured results from a :func:`simulate_shelter` run.

    Attributes:
        timeseries: A ``pandas.DataFrame`` with one row per timestep and
            the columns documented in :func:`simulate_shelter`.
        summary: A dict of scalar summary metrics (see
            :func:`simulate_shelter`).
        shelter: The :class:`Shelter` configuration that was simulated.
    """

    timeseries: pd.DataFrame
    summary: dict
    shelter: Shelter

    def __repr__(self) -> str:  # pragma: no cover - cosmetic only
        return (
            f"SimulationResult(shelter={self.shelter.name!r}, "
            f"steps={len(self.timeseries)}, "
            f"avg_indoor_temp={self.summary['average_indoor_temperature']:.2f}C)"
        )


def simulate_shelter(
    shelter: Shelter,
    ambient_temperature: TimeSeriesInput,
    solar_radiation: TimeSeriesInput,
    duration_hours: float,
    time_step_hours: float = 1.0,
    comfort_range: tuple[float, float] | None = None,
) -> SimulationResult:
    """
    Run a transient thermal simulation of a shelter.

    Args:
        shelter: The shelter configuration to simulate.
        ambient_temperature: Outdoor air temperature, in Celsius. Either a
            single constant number (held fixed for the whole run) or a
            time series (list/tuple/NumPy array/Pandas Series). A time
            series does not need to have exactly one value per timestep:
            it is linearly resampled onto the simulation's timestep grid,
            so e.g. 24 hourly values can drive a 15-minute-timestep run.
        solar_radiation: Incident solar radiation, in W/m^2. Same
            constant-or-time-series rules as ``ambient_temperature``.
            Must be non-negative.
        duration_hours: Total simulated duration, in hours. Must be > 0.
        time_step_hours: Simulation timestep, in hours. Must be > 0 and
            should typically be << duration_hours. Defaults to 1.0 (hourly).
        comfort_range: Optional (min, max) indoor comfort band in Celsius.
            If provided, the summary will include the fraction/duration of
            time the indoor temperature stayed within this band.

    Returns:
        A :class:`SimulationResult` containing the full per-timestep
        DataFrame and a dict of summary metrics.

    Raises:
        ThermalEngineValidationError: if any input is physically invalid.
    """
    validate_positive(duration_hours, "duration_hours")
    validate_positive(time_step_hours, "time_step_hours")
    validate_comfort_range(comfort_range)

    if time_step_hours > duration_hours:
        raise ValueError(
            f"'time_step_hours' ({time_step_hours}) cannot exceed "
            f"'duration_hours' ({duration_hours})."
        )

    num_steps = int(round(duration_hours / time_step_hours))
    if num_steps < 1:
        raise ValueError("Simulation must have at least one timestep.")

    dt_seconds = time_step_hours * 3600.0

    ambient_series = _resample_to_steps(
        ambient_temperature, num_steps, "ambient_temperature"
    )
    solar_series = _resample_to_steps(solar_radiation, num_steps, "solar_radiation")

    for t in ambient_series:
        validate_temperature_celsius(float(t), "ambient_temperature")
    validate_non_negative_sequence(solar_series.tolist(), "solar_radiation")

    thermal_capacity = shelter.thermal_capacity

    # Pre-computed, time-invariant quantities.
    wall_u = shelter.wall_u_value
    roof_u = shelter.roof_u_value
    floor_u = shelter.floor_u_value
    opening_u = shelter.opening_u_value
    wall_area = shelter.net_wall_area
    roof_area = shelter.roof_area
    floor_area = shelter.floor_area
    opening_area = shelter.total_opening_area
    solar_area = shelter.solar_exposed_area
    solar_absorptivity = shelter.roof_material.solar_absorptivity

    records = []
    indoor_temp = shelter.initial_indoor_temperature

    for step in range(num_steps):
        time_hours = step * time_step_hours
        t_amb = float(ambient_series[step])
        i_solar = float(solar_series[step])

        wall_loss = conduction_heat_flow(wall_u, wall_area, indoor_temp, t_amb)
        roof_loss = conduction_heat_flow(roof_u, roof_area, indoor_temp, t_amb)
        floor_loss = conduction_heat_flow(floor_u, floor_area, indoor_temp, t_amb)
        opening_loss = conduction_heat_flow(
            opening_u, opening_area, indoor_temp, t_amb
        )
        total_loss = wall_loss + roof_loss + floor_loss + opening_loss

        gain = solar_heat_gain(i_solar, solar_area, solar_absorptivity)

        net_flow = gain - total_loss

        records.append(
            {
                "time_hours": time_hours,
                "ambient_temperature": t_amb,
                "indoor_temperature": indoor_temp,
                "solar_radiation": i_solar,
                "solar_gain": gain,
                "wall_heat_loss": wall_loss,
                "roof_heat_loss": roof_loss,
                "floor_heat_loss": floor_loss,
                "opening_heat_loss": opening_loss,
                "total_heat_loss": total_loss,
                "net_heat_flow": net_flow,
            }
        )

        # Advance indoor temperature for the *next* timestep.
        indoor_temp = indoor_temp + temperature_change(
            net_flow, thermal_capacity, dt_seconds
        )

    df = pd.DataFrame.from_records(records)
    summary = _compute_summary(df, time_step_hours, comfort_range)

    return SimulationResult(timeseries=df, summary=summary, shelter=shelter)


def _compute_summary(
    df: pd.DataFrame,
    time_step_hours: float,
    comfort_range: tuple[float, float] | None,
) -> dict:
    """Compute scalar summary metrics from a completed simulation DataFrame."""
    summary = {
        "average_indoor_temperature": float(df["indoor_temperature"].mean()),
        "minimum_indoor_temperature": float(df["indoor_temperature"].min()),
        "maximum_indoor_temperature": float(df["indoor_temperature"].max()),
        "average_ambient_temperature": float(df["ambient_temperature"].mean()),
        "total_solar_energy_wh": float(df["solar_gain"].sum() * time_step_hours),
        "total_heat_loss_wh": float(df["total_heat_loss"].sum() * time_step_hours),
        "average_heat_loss_w": float(df["total_heat_loss"].mean()),
        "net_energy_balance_wh": float(
            (df["solar_gain"].sum() - df["total_heat_loss"].sum()) * time_step_hours
        ),
        "duration_hours": float(len(df) * time_step_hours),
    }

    if comfort_range is not None:
        low, high = comfort_range
        in_comfort = df["indoor_temperature"].between(low, high)
        summary["comfort_range"] = (float(low), float(high))
        summary["time_in_comfort_hours"] = float(in_comfort.sum() * time_step_hours)
        summary["fraction_time_in_comfort"] = float(in_comfort.mean())
    else:
        summary["comfort_range"] = None
        summary["time_in_comfort_hours"] = None
        summary["fraction_time_in_comfort"] = None

    return summary


def _resample_to_steps(
    values: TimeSeriesInput, num_steps: int, name: str
) -> np.ndarray:
    """
    Normalise a constant-or-time-series input onto the simulation's grid.

    - A single number is broadcast to every timestep.
    - A list/tuple/ndarray/Series is linearly resampled (via
      ``numpy.interp``) from its own index range onto ``num_steps`` evenly
      spaced points. If its length already equals ``num_steps``, this is
      equivalent to using it as-is.

    Args:
        values: constant number or 1-D sequence of numbers.
        num_steps: number of simulation timesteps to produce.
        name: input name, used only for error messages.

    Returns:
        A 1-D NumPy array of length ``num_steps``.
    """
    if isinstance(values, (int, float)) and not isinstance(values, bool):
        return np.full(num_steps, float(values))

    if isinstance(values, pd.Series):
        raw = values.to_numpy(dtype=float)
    elif isinstance(values, np.ndarray):
        raw = values.astype(float)
    elif isinstance(values, (list, tuple)):
        raw = np.asarray(values, dtype=float)
    else:
        raise TypeError(
            f"'{name}' must be a number, list, tuple, NumPy array or Pandas "
            f"Series, got {type(values).__name__}."
        )

    if raw.ndim != 1:
        raise ValueError(f"'{name}' must be one-dimensional.")
    if raw.size == 0:
        raise ValueError(f"'{name}' must not be empty.")

    if raw.size == num_steps:
        return raw

    # Linearly resample from the source's own index range onto num_steps
    # evenly spaced points, so e.g. 24 hourly readings can drive a run with
    # a different number/size of timesteps.
    source_x = np.linspace(0.0, 1.0, raw.size)
    target_x = np.linspace(0.0, 1.0, num_steps)
    return np.interp(target_x, source_x, raw)
