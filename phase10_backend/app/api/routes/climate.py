from fastapi import APIRouter, Depends

from app.dependencies import get_climate_service
from app.schemas.climate import ClimateCreate, ClimateResponse
from app.services.climate_service import ClimateService

router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("/presets", response_model=list[ClimateResponse], summary="List predefined climate presets")
def list_presets(service: ClimateService = Depends(get_climate_service)):
    return service.list_presets()


@router.post("", response_model=ClimateResponse, status_code=201, summary="Create a custom climate record")
def create_climate(payload: ClimateCreate, service: ClimateService = Depends(get_climate_service)):
    return service.create_custom_climate(payload)


@router.get("/{location}", response_model=ClimateResponse, summary="Get climate information by location name")
def get_climate_by_location(location: str, service: ClimateService = Depends(get_climate_service)):
    return service.get_by_location(location)
