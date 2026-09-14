from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ClimateTimeSeriesPoint(BaseModel):
    timestamp: str = Field(..., description="ISO timestamp or hour label")
    temperature: float
    solar_radiation: Optional[float] = None
    humidity: Optional[float] = None


class ClimateCreate(BaseModel):
    location: Optional[str] = Field(None, examples=["Custom Site A"])
    temperature: float = Field(..., ge=-60, le=60, description="Ambient temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity %")
    pressure: float = Field(..., ge=800, le=1100, description="Atmospheric pressure in hPa")
    solar_radiation: float = Field(..., ge=0, le=1500, description="Solar radiation in W/m2")
    wind_speed: float = Field(..., ge=0, le=150, description="Wind speed in km/h")
    wind_direction: float = Field(..., ge=0, le=360, description="Wind direction in degrees")
    time_series: Optional[List[ClimateTimeSeriesPoint]] = None


class ClimateResponse(BaseModel):
    id: str
    location: Optional[str] = None
    temperature: float
    humidity: float
    pressure: float
    solar_radiation: float
    wind_speed: float
    wind_direction: float
    is_preset: bool = False
    data_source: str = "preset"
    time_series: Optional[List[ClimateTimeSeriesPoint]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
