from fastapi import APIRouter, Depends, Query

from app.dependencies import get_comparison_service
from app.schemas.recommendation import ComparisonRequest, ComparisonResponse
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("", response_model=ComparisonResponse, summary="Compare multiple designs")
def compare_designs(
    payload: ComparisonRequest,
    climate_location: str = Query("Composite", description="Climate preset to evaluate designs against"),
    service: ComparisonService = Depends(get_comparison_service),
):
    return service.compare(payload.design_ids, climate_location)
