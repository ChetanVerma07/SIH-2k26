from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SimulationStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class SimulationResults:
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


@dataclass
class Simulation:
    id: str
    project_id: str
    design_id: str
    climate_id: str
    duration: float
    timestep: float
    status: SimulationStatus = SimulationStatus.CREATED
    progress: float = 0.0
    backend: str = "MOCK"
    results: Optional[SimulationResults] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
