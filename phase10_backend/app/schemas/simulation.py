from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.simulation import SimulationStatus


class SimulationCreate(BaseModel):
    project_id: str
    design_id: str
    climate_id: str
    duration: float = Field(24, gt=0, le=8760, description="Simulation duration in hours")
    timestep: float = Field(1, gt=0, le=24, description="Timestep in hours")


class SimulationResponse(BaseModel):
    id: str
    project_id: str
    design_id: str
    climate_id: str
    duration: float
    timestep: float
    status: SimulationStatus
    progress: float
    backend: str
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SimulationResultsResponse(BaseModel):
    simulation_id: str
    indoor_temperature: float
    outdoor_temperature: float
    heat_loss: float
    solar_gain: float
    average_temperature: float
    minimum_temperature: float
    maximum_temperature: float
    comfort_percentage: float
    total_heat_loss: float
    total_solar_gain: float
