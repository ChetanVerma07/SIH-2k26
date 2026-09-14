"""
Application configuration.

All database configuration comes from environment variables. Nothing is
hard-coded. Values are read via pydantic-settings, which will also pick
up a local .env file if present (see .env.example).
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://postgres:password@localhost:5432/passive_shelter"
    TEST_DATABASE_URL: str | None = None
    SQL_ECHO: bool = False

    def resolved_test_database_url(self) -> str:
        if self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        # Fall back: derive "<db>_test" from DATABASE_URL.
        if self.DATABASE_URL.rsplit("/", 1)[-1].endswith("_test"):
            return self.DATABASE_URL
        base, _, dbname = self.DATABASE_URL.rpartition("/")
        return f"{base}/{dbname}_test"


@lru_cache
def get_settings() -> Settings:
    return Settings()
