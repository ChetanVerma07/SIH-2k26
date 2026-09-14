from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import logger
from app.models.climate import ClimateRecord
from app.repositories.memory_repository import new_id
from app.services.climate_service import ClimateService

class OpenWeatherMain(BaseModel):
    temp: float
    humidity: float
    pressure: float

class OpenWeatherWind(BaseModel):
    speed: float = 0.0
    deg: float = 0.0

class OpenWeatherResponse(BaseModel):
    main: OpenWeatherMain
    wind: OpenWeatherWind = Field(default_factory=OpenWeatherWind)
    name: str = ""


class WeatherService:
    """Backend-only weather adapter with deterministic climate fallback."""

    def __init__(self, climate_service: ClimateService):
        self.climate_service = climate_service
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.weather_api_key)

    def get_current(self, location: str) -> ClimateRecord:
        if not self.is_configured:
            return self._fallback(location, "weather_api_not_configured")

        try:
            response = httpx.get(
                f"{self.settings.weather_api_base_url.rstrip('/')}/weather",
                params={"q": location, "appid": self.settings.weather_api_key, "units": "metric"},
                timeout=self.settings.weather_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            return self._adapt_openweather(payload, location)
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            logger.warning("Weather API fallback for '%s' due to %s: %s", location, type(exc).__name__, exc)
            return self._fallback(location, f"weather_api_fallback:{type(exc).__name__}")

    def _fallback(self, location: str, source: str) -> ClimateRecord:
        try:
            preset = self.climate_service.get_by_location(location)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"No climate data found for location '{location}'")

        return ClimateRecord(
            id=preset.id,
            location=preset.location,
            temperature=preset.temperature,
            humidity=preset.humidity,
            pressure=preset.pressure,
            solar_radiation=preset.solar_radiation,
            wind_speed=preset.wind_speed,
            wind_direction=preset.wind_direction,
            is_preset=preset.is_preset,
            data_source=source,
            time_series=preset.time_series,
            created_at=preset.created_at,
        )

    @staticmethod
    def _adapt_openweather(payload: dict[str, Any], requested_location: str) -> ClimateRecord:
        validated = OpenWeatherResponse.model_validate(payload)
        name = validated.name or requested_location
        return ClimateRecord(
            id=new_id("weather"),
            location=name,
            temperature=validated.main.temp,
            humidity=validated.main.humidity,
            pressure=validated.main.pressure,
            solar_radiation=0.0,
            wind_speed=validated.wind.speed * 3.6,  # Convert m/s to km/h
            wind_direction=validated.wind.deg,
            is_preset=False,
            data_source="openweather",
            created_at=datetime.now(timezone.utc),
        )
