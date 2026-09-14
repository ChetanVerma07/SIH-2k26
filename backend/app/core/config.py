"""
Application configuration.

Settings are loaded from environment variables (or a .env file).
See .env.example for the full list of configurable options.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Passive Shelter API"
    app_version: str = "1.0.0"
    debug: bool = True
    allowed_origins: str = "http://localhost:5173"
    weather_api_key: str | None = None
    weather_api_base_url: str = "https://api.openweathermap.org/data/2.5"
    weather_timeout_seconds: float = 5.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
