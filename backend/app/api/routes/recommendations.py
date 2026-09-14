from fastapi import APIRouter, Depends, Query

from app.dependencies import get_recommendation_service
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/projects", tags=["recommendations"])


@router.get(
    "/{project_id}/recommendation",
    response_model=RecommendationResponse,
    summary="Get an explainable design recommendation for a project",
)
def get_recommendation(
    project_id: str,
    climate_location: str = Query("Composite", description="Climate preset to evaluate against"),
    service: RecommendationService = Depends(get_recommendation_service),
):
    return service.recommend(project_id, climate_location)
