from fastapi import APIRouter, Depends

from app.dependencies import get_simulation_service
from app.schemas.simulation import SimulationCreate, SimulationResponse, SimulationResultsResponse
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", response_model=SimulationResponse, status_code=201, summary="Create a simulation")
def create_simulation(payload: SimulationCreate, service: SimulationService = Depends(get_simulation_service)):
    return service.create_simulation(payload)


@router.post("/{simulation_id}/run", response_model=SimulationResponse, summary="Run a simulation (mock engine)")
def run_simulation(simulation_id: str, service: SimulationService = Depends(get_simulation_service)):
    return service.run_simulation(simulation_id)


@router.get("/{simulation_id}", response_model=SimulationResponse, summary="Get simulation status")
def get_simulation(simulation_id: str, service: SimulationService = Depends(get_simulation_service)):
    return service.get_simulation(simulation_id)


@router.get(
    "/{simulation_id}/results",
    response_model=SimulationResultsResponse,
    summary="Get simulation results",
)
def get_simulation_results(simulation_id: str, service: SimulationService = Depends(get_simulation_service)):
    results = service.get_results(simulation_id)
    return SimulationResultsResponse(simulation_id=simulation_id, **results.__dict__)
