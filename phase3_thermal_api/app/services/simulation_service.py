"""
Simulation service.

Runs the transient thermal simulator for a single shelter/climate/settings
combination and converts the raw per-step results into the API's
SimulationResult response model, including summary statistics and the
heat-loss breakdown.
"""
from __future__ import annotations

from typing import List

from app.models.shelter import ShelterConfig
from app.models.simulation import (
    HeatLossBreakdown,
    SimulationRequest,
    SimulationResult,
    SimulationSummary,
    TimeStepResult,
)
from app.thermal.simulator import TimeStepRaw, run_simulation


def _energy_wh(power_series: List[float], time_step_hours: float) -> float:
    """Integrate a series of instantaneous power values (W) into energy (Wh)
    using simple rectangular integration: each sample represents the power
    held constant for one time_step_hours interval."""
    return sum(power_series) * time_step_hours


def run_and_summarize(shelter: ShelterConfig, request: SimulationRequest) -> SimulationResult:
    raw: List[TimeStepRaw] = run_simulation(shelter, request.climate, request.settings)

    time_series = [
        TimeStepResult(
            time=r.time,
            ambient_temperature=r.ambient_temperature,
            indoor_temperature=r.indoor_temperature,
            solar_radiation=r.solar_radiation,
            solar_gain=r.solar_gain,
            wall_heat_loss=r.wall_heat_loss,
            roof_heat_loss=r.roof_heat_loss,
            floor_heat_loss=r.floor_heat_loss,
            opening_heat_loss=r.opening_heat_loss,
            total_heat_loss=r.total_heat_loss,
            net_heat_flow=r.net_heat_flow,
        )
        for r in raw
    ]

    dt_h = request.settings.time_step_hours
    indoor_temps = [r.indoor_temperature for r in raw]

    total_solar = _energy_wh([r.solar_gain for r in raw], dt_h)
    total_wall_loss = _energy_wh([r.wall_heat_loss for r in raw], dt_h)
    total_roof_loss = _energy_wh([r.roof_heat_loss for r in raw], dt_h)
    total_floor_loss = _energy_wh([r.floor_heat_loss for r in raw], dt_h)
    total_opening_loss = _energy_wh([r.opening_heat_loss for r in raw], dt_h)
    total_loss = total_wall_loss + total_roof_loss + total_floor_loss + total_opening_loss

    comfort_min = request.settings.comfort_min
    comfort_max = request.settings.comfort_max
    in_comfort = sum(1 for t in indoor_temps if comfort_min <= t <= comfort_max)
    comfort_percentage = 100.0 * in_comfort / len(indoor_temps)

    summary = SimulationSummary(
        average_indoor_temperature=sum(indoor_temps) / len(indoor_temps),
        minimum_indoor_temperature=min(indoor_temps),
        maximum_indoor_temperature=max(indoor_temps),
        total_solar_energy_gained=total_solar,
        total_heat_loss=total_loss,
        net_thermal_energy=total_solar - total_loss,
        comfort_percentage=comfort_percentage,
    )

    breakdown = HeatLossBreakdown(
        walls=total_wall_loss,
        roof=total_roof_loss,
        floor=total_floor_loss,
        openings=total_opening_loss,
    )

    return SimulationResult(
        shelter_name=shelter.name,
        summary=summary,
        heat_loss_breakdown=breakdown,
        time_series=time_series,
    )
