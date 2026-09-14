from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.optimization import OptimizationStatus


class OptimizationParameters(BaseModel):
    max_candidates: int = Field(5, ge=1, le=20)
    target_metric: str = Field("comfort_percentage", examples=["comfort_percentage", "total_heat_loss"])
    insulation_search_range: List[float] = Field(
        default=[0.02, 0.05, 0.08, 0.12], description="Candidate insulation thicknesses (m)"
    )
    opening_search_range: List[float] = Field(
        default=[5, 10, 15, 20], description="Candidate opening percentages"
    )


class OptimizationCreate(BaseModel):
    project_id: str
    baseline_design_id: str
    parameters: OptimizationParameters = Field(default_factory=OptimizationParameters)


class CandidateDesignResponse(BaseModel):
    design_id: str
    score: float
    comfort_percentage: float
    total_heat_loss: float
    total_solar_gain: float
    modifications: Dict[str, Any]


class OptimizationResponse(BaseModel):
    id: str
    project_id: str
    baseline_design_id: str
    parameters: Dict[str, Any]
    status: OptimizationStatus
    candidates: List[CandidateDesignResponse] = []
    best_candidate_design_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
