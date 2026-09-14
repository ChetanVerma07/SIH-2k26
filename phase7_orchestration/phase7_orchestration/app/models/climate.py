"""Climate-related Pydantic models."""
from typing import Optional
from pydantic import BaseModel, Field


class ClimateProfile(BaseModel):
    """Represents the climatic conditions used to drive simulation."""

    location: str
    climate_zone: str = Field(..., description="e.g. 'cold high-altitude'")
    avg_outdoor_temp_c: float
    min_outdoor_temp_c: float
    max_outdoor_temp_c: float
    avg_solar_radiation_wm2: float = Field(
        ..., description="Average solar radiation in W/m^2 over the simulated period"
    )
    wind_speed_ms: float = Field(default=3.0, description="Average wind speed in m/s")
    humidity_percent: float = Field(default=30.0)
    altitude_m: Optional[float] = Field(default=None)
    data_points_available: int = Field(
        default=24, description="Number of discrete climate data points supplied (e.g. hourly)"
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Names of climate fields that were unavailable and had to be estimated/defaulted",
    )
    source: str = Field(default="mock", description="Origin of the climate data, e.g. 'mock' or 'api'")


class ScenarioDefinition(BaseModel):
    """A named environmental scenario used for robustness testing."""

    name: str
    description: str
    outdoor_temp_offset_c: float = Field(
        default=0.0, description="Offset applied to the base climate's average outdoor temp"
    )
    solar_radiation_factor: float = Field(
        default=1.0, description="Multiplier applied to the base climate's solar radiation"
    )
    wind_speed_ms: Optional[float] = Field(default=None)
