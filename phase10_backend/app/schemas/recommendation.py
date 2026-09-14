from typing import Any, Dict, List

from pydantic import BaseModel, Field


class RecommendationResponse(BaseModel):
    project_id: str
    recommended_design_id: str
    score: float
    performance: Dict[str, Any]
    explanation: str
    assumptions: List[str]
    limitations: List[str]


class ComparisonRequest(BaseModel):
    design_ids: List[str] = Field(..., min_length=2, max_length=10)


class ComparisonMetric(BaseModel):
    design_id: str
    comfort_percentage: float
    total_heat_loss: float
    total_solar_gain: float
    energy_requirement: float
    overall_score: float


class ComparisonResponse(BaseModel):
    design_ids: List[str]
    metrics: List[ComparisonMetric]
    best_design_id: str
