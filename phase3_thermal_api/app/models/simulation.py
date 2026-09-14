"""
Simulation settings, request, and result models.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.climate import ClimateInput
from app.models.shelter import ShelterConfig


class SimulationSettings(BaseModel):
    """Controls for a transient thermal simulation run."""

    duration_hours: float = Field(..., gt=0, le=8760, description="Total simulated time, hours")
    time_step_minutes: float = Field(
        30.0, gt=0, le=120, description="Simulation time step, minutes (<=120 for stability)"
    )
    initial_indoor_temperature: float = Field(
        ..., description="Indoor temperature at t=0, degC"
    )
    comfort_min: float = Field(..., description="Lower bound of the comfort band, degC")
    comfort_max: float = Field(..., description="Upper bound of the comfort band, degC")

    @model_validator(mode="after")
    def _check_comfort_range(self) -> "SimulationSettings":
        if self.comfort_max <= self.comfort_min:
            raise ValueError("comfort_max must be greater than comfort_min")
        return self

    @property
    def time_step_hours(self) -> float:
        return self.time_step_minutes / 60.0

    @property
    def num_steps(self) -> int:
        # Number of samples including t=0, spaced time_step_hours apart,
        # covering at least duration_hours.
        return int(round(self.duration_hours / self.time_step_hours)) + 1


class SimulationRequest(BaseModel):
    climate: ClimateInput = Field(..., description="Constant climate object or time-series list")
    shelter: ShelterConfig
    settings: SimulationSettings


class CompareRequest(BaseModel):
    climate: ClimateInput
    shelters: List[ShelterConfig] = Field(..., min_length=2)
    settings: SimulationSettings
    ranking_weights: Optional[Dict[str, float]] = Field(
        None,
        description=(
            "Optional weights for ranking, keys among "
            "'comfort', 'heat_loss', 'solar_gain'. Defaults to "
            "{'comfort': 0.5, 'heat_loss': 0.3, 'solar_gain': 0.2}."
        ),
    )


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


class TimeStepResult(BaseModel):
    time: float = Field(..., description="Hours from simulation start")
    ambient_temperature: float
    indoor_temperature: float
    solar_radiation: float
    solar_gain: float = Field(..., description="Instantaneous solar heat gain, W")
    wall_heat_loss: float = Field(..., description="Instantaneous wall conduction loss, W")
    roof_heat_loss: float = Field(..., description="Instantaneous roof conduction loss, W")
    floor_heat_loss: float = Field(..., description="Instantaneous floor conduction loss, W")
    opening_heat_loss: float = Field(..., description="Instantaneous opening conduction loss, W")
    total_heat_loss: float = Field(..., description="Sum of wall+roof+floor+opening losses, W")
    net_heat_flow: float = Field(..., description="solar_gain - total_heat_loss, W")


class HeatLossBreakdown(BaseModel):
    walls: float = Field(..., description="Total wall heat loss over the run, Wh")
    roof: float = Field(..., description="Total roof heat loss over the run, Wh")
    floor: float = Field(..., description="Total floor heat loss over the run, Wh")
    openings: float = Field(..., description="Total opening heat loss over the run, Wh")


class SimulationSummary(BaseModel):
    average_indoor_temperature: float
    minimum_indoor_temperature: float
    maximum_indoor_temperature: float
    total_solar_energy_gained: float = Field(..., description="Wh over the whole run")
    total_heat_loss: float = Field(..., description="Wh over the whole run")
    net_thermal_energy: float = Field(..., description="Wh, solar gained minus heat lost")
    comfort_percentage: float = Field(
        ..., description="Percent of timesteps with indoor temperature inside the comfort band"
    )


class SimulationResult(BaseModel):
    shelter_name: str
    summary: SimulationSummary
    heat_loss_breakdown: HeatLossBreakdown
    time_series: List[TimeStepResult]


class RankedDesign(BaseModel):
    shelter_name: str
    rank: int
    score: float
    result: SimulationResult


class CompareResult(BaseModel):
    ranking_weights: Dict[str, float]
    designs: List[RankedDesign]
