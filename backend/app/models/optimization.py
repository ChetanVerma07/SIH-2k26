from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class OptimizationStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class CandidateDesign:
    design_id: str
    score: float
    comfort_percentage: float
    total_heat_loss: float
    total_solar_gain: float
    modifications: dict


@dataclass
class Optimization:
    id: str
    project_id: str
    baseline_design_id: str
    parameters: dict
    status: OptimizationStatus = OptimizationStatus.CREATED
    candidates: List[CandidateDesign] = field(default_factory=list)
    best_candidate_design_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
