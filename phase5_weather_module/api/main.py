"""FastAPI service for Phase 5 - Weather & Climate Data Module.

Run with:
    uvicorn api.main:app --reload

The API never exposes provider-specific structures — only normalized
Pydantic models built from WeatherObservation.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from weather_module.models.location import Location
from weather_module.processing.cache import TTLCache, RateLimiter
from weather_module.providers.base import ProviderError, InvalidLocationError
from weather_module.services.weather_service import WeatherService

app = FastAPI(
    title="Phase 5 - Weather & Climate Data Module",
    description=(
        "Standalone weather/climate data service for passive-shelter thermal "
        "simulation. Works fully offline via the built-in mock provider."
    ),
    version="1.0.0",
)

service = WeatherService()
cache = TTLCache(ttl_seconds=300.0)
limiter = RateLimiter(max_calls=60, period_seconds=60.0)


# ---------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------
class ObservationOut(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    solar_radiation_wm2: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    cloud_cover_pct: Optional[float] = None
    precipitation_mm: Optional[float] = None
    solar_radiation_source: str
    data_source: str
    quality: str
    quality_reason: Optional[str] = None


class ProfileRequest(BaseModel):
    location_name: Optional[str] = Field(None, description="Named location, e.g. 'ladakh'")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    duration_hours: int = Field(24, ge=1, le=240)
    interval_minutes: int = Field(60, description="15, 30, or 60 minutes recommended")


class SimulationProfileOut(BaseModel):
    location: str
    latitude: Optional[float]
    longitude: Optional[float]
    duration_hours: int
    interval_minutes: int
    provider: str
    quality_summary: dict
    observations: List[ObservationOut]


class HealthOut(BaseModel):
    status: str
    provider: str


# ---------------------------------------------------------------------
def _build_location(name: Optional[str], lat: Optional[float], lon: Optional[float]) -> Location:
    try:
        if lat is not None and lon is not None:
            return Location(name=name, latitude=lat, longitude=lon)
        if name:
            return Location(name=name)
        raise HTTPException(status_code=422, detail="Provide either a location name or latitude+longitude.")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def _check_rate_limit(key: str = "global"):
    if not limiter.allow(key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please slow down.")


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------
@app.get("/api/health", response_model=HealthOut)
def health():
    return HealthOut(status="ok", provider=service.provider.name)


@app.get("/api/weather/current", response_model=ObservationOut)
def current_weather(
    location: Optional[str] = Query(None, description="Location name, e.g. 'ladakh', 'delhi'"),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
):
    _check_rate_limit()
    loc = _build_location(location, lat, lon)
    cache_key = f"current:{loc.display_name()}"
    try:
        obs = cache.get_or_set(cache_key, lambda: service.get_current(loc))
    except InvalidLocationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=f"Weather provider unavailable: {e}")
    return ObservationOut(**obs.to_dict())


@app.get("/api/weather/forecast", response_model=List[ObservationOut])
def forecast(
    location: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    hours: int = Query(24, ge=1, le=240),
    interval_minutes: int = Query(60),
):
    _check_rate_limit()
    loc = _build_location(location, lat, lon)
    try:
        series = service.get_forecast(loc, hours=hours, interval_minutes=interval_minutes)
    except InvalidLocationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=f"Weather provider unavailable: {e}")
    return [ObservationOut(**o.to_dict()) for o in series]


@app.get("/api/weather/historical", response_model=List[ObservationOut])
def historical(
    location: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    start: date = Query(...),
    end: Optional[date] = Query(None),
):
    _check_rate_limit()
    loc = _build_location(location, lat, lon)
    try:
        series = service.get_historical(loc, start=start, end=end)
    except InvalidLocationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=f"Weather provider unavailable: {e}")
    return [ObservationOut(**o.to_dict()) for o in series]


@app.post("/api/weather/profile", response_model=SimulationProfileOut)
def simulation_profile(req: ProfileRequest):
    _check_rate_limit()
    loc = _build_location(req.location_name, req.latitude, req.longitude)
    try:
        profile = service.generate_simulation_profile(
            loc, duration_hours=req.duration_hours, interval_minutes=req.interval_minutes
        )
    except InvalidLocationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=f"Weather provider unavailable: {e}")
    return SimulationProfileOut(**profile)


@app.get("/api/weather/demo", response_model=SimulationProfileOut)
def demo(interval_minutes: int = Query(60)):
    """Offline Ladakh demo — no API key or network required."""
    profile = service.demo_ladakh_profile(interval_minutes=interval_minutes)
    profile.pop("data_label", None)
    profile.pop("elevation_m", None)
    return SimulationProfileOut(**profile)
