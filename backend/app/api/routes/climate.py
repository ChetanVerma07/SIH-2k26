from fastapi import APIRouter, Depends

from app.dependencies import get_climate_service, get_weather_service
from app.schemas.climate import ClimateCreate, ClimateResponse
from app.services.climate_service import ClimateService
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/climate", tags=["climate"])


@router.get("/presets", response_model=list[ClimateResponse], summary="List predefined climate presets")
def list_presets(service: ClimateService = Depends(get_climate_service)):
    return service.list_presets()


@router.post("", response_model=ClimateResponse, status_code=201, summary="Create a custom climate record")
def create_climate(payload: ClimateCreate, service: ClimateService = Depends(get_climate_service)):
    return service.create_custom_climate(payload)


@router.get("/current/{location}", response_model=ClimateResponse, summary="Get current weather with preset fallback")
def get_current_weather(location: str, service: WeatherService = Depends(get_weather_service)):
    return service.get_current(location)


@router.get("/{location}", response_model=ClimateResponse, summary="Get climate information by location name")
def get_climate_by_location(location: str, service: ClimateService = Depends(get_climate_service)):
    return service.get_by_location(location)
