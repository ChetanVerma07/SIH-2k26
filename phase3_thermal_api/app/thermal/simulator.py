"""
Transient thermal simulator.

Integrates the indoor air temperature forward in time using explicit
(forward) Euler integration of the lumped-capacitance heat balance:

    T_indoor(t + dt) = T_indoor(t) + (dt_seconds / C_total) * Q_net(t)

where:
    C_total  = effective thermal mass of the indoor air node, J/K
               (see app.thermal.heat_balance.effective_thermal_mass)
    Q_net(t) = Q_solar(t) - Q_loss(t), W
    dt_seconds = simulation time step, seconds

This makes indoor temperature at each step depend on the previous step,
i.e. the model is genuinely transient rather than a series of independent
steady-state snapshots.

Stability note: explicit Euler is conditionally stable. SimulationSettings
caps time_step_minutes at 120 minutes to stay well within the stable range
for realistic shelter thermal masses; see README "Limitations".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

import numpy as np
import pandas as pd

from app.models.climate import ClimatePoint, ConstantClimate
from app.models.shelter import ShelterConfig
from app.models.simulation import SimulationSettings
from app.thermal.heat_balance import compute_heat_balance, effective_thermal_mass

ClimateInputType = Union[ConstantClimate, List[ClimatePoint]]


@dataclass
class TimeStepRaw:
    time: float
    ambient_temperature: float
    ground_temperature: float
    solar_radiation: float
    indoor_temperature: float
    solar_gain: float
    wall_heat_loss: float
    roof_heat_loss: float
    floor_heat_loss: float
    opening_heat_loss: float
    total_heat_loss: float
    net_heat_flow: float


def build_climate_series(climate: ClimateInputType, settings: SimulationSettings) -> pd.DataFrame:
    """
    Produce a DataFrame of climate values sampled at every simulation
    timestep (0, dt, 2*dt, ... duration_hours), regardless of whether the
    input climate was constant or an irregularly-spaced time series.
    """
    times = np.linspace(
        0.0, settings.duration_hours, settings.num_steps
    )

    if isinstance(climate, ConstantClimate):
        ambient = np.full_like(times, climate.ambient_temperature, dtype=float)
        solar = np.full_like(times, climate.solar_radiation, dtype=float)
        ground_val = (
            climate.ground_temperature
            if climate.ground_temperature is not None
            else climate.ambient_temperature
        )
        ground = np.full_like(times, ground_val, dtype=float)
    else:
        points = sorted(climate, key=lambda p: p.time)
        src_times = np.array([p.time for p in points], dtype=float)
        src_ambient = np.array([p.ambient_temperature for p in points], dtype=float)
        src_solar = np.array([p.solar_radiation for p in points], dtype=float)
        src_ground = np.array(
            [
                p.ground_temperature if p.ground_temperature is not None else p.ambient_temperature
                for p in points
            ],
            dtype=float,
        )
        # np.interp clamps to the edge values outside the supplied range,
        # which is the documented behaviour for extrapolation.
        ambient = np.interp(times, src_times, src_ambient)
        solar = np.interp(times, src_times, src_solar)
        ground = np.interp(times, src_times, src_ground)

    return pd.DataFrame(
        {
            "time": times,
            "ambient_temperature": ambient,
            "solar_radiation": solar,
            "ground_temperature": ground,
        }
    )


def run_simulation(
    shelter: ShelterConfig,
    climate: ClimateInputType,
    settings: SimulationSettings,
) -> List[TimeStepRaw]:
    """Run the full transient simulation and return per-step raw results."""
    climate_df = build_climate_series(climate, settings)
    c_total = effective_thermal_mass(shelter)
    dt_seconds = settings.time_step_hours * 3600.0

    results: List[TimeStepRaw] = []
    indoor_t = settings.initial_indoor_temperature

    for row in climate_df.itertuples(index=False):
        balance = compute_heat_balance(
            shelter=shelter,
            indoor_temperature=indoor_t,
            ambient_temperature=row.ambient_temperature,
            ground_temperature=row.ground_temperature,
            solar_radiation=row.solar_radiation,
        )

        results.append(
            TimeStepRaw(
                time=row.time,
                ambient_temperature=row.ambient_temperature,
                ground_temperature=row.ground_temperature,
                solar_radiation=row.solar_radiation,
                indoor_temperature=indoor_t,
                solar_gain=balance.solar_gain,
                wall_heat_loss=balance.wall_heat_loss,
                roof_heat_loss=balance.roof_heat_loss,
                floor_heat_loss=balance.floor_heat_loss,
                opening_heat_loss=balance.opening_heat_loss,
                total_heat_loss=balance.total_heat_loss,
                net_heat_flow=balance.net_heat_flow,
            )
        )

        # Advance indoor temperature to the next timestep (explicit Euler).
        indoor_t = indoor_t + (dt_seconds / c_total) * balance.net_heat_flow

    return results
