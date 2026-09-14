from fastapi import APIRouter, Depends, Query

from app.dependencies import get_optimization_service
from app.schemas.optimization import OptimizationCreate, OptimizationResponse
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/optimization", tags=["optimization"])


@router.post("", response_model=OptimizationResponse, status_code=201, summary="Create an optimization run")
def create_optimization(payload: OptimizationCreate, service: OptimizationService = Depends(get_optimization_service)):
    return service.create_optimization(payload)


@router.post(
    "/{optimization_id}/run",
    response_model=OptimizationResponse,
    summary="Run the optimization (mock optimizer, generates & scores candidate designs)",
)
def run_optimization(
    optimization_id: str,
    climate_location: str = Query("Composite", description="Climate preset location to evaluate candidates against"),
    service: OptimizationService = Depends(get_optimization_service),
):
    return service.run_optimization(optimization_id, climate_location)


@router.get("/{optimization_id}", response_model=OptimizationResponse, summary="Get optimization status/results")
def get_optimization(optimization_id: str, service: OptimizationService = Depends(get_optimization_service)):
    return service.get_optimization(optimization_id)
