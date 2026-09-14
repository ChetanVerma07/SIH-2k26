from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MaterialCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Rammed Earth"])
    category: str = Field(..., min_length=1, max_length=50, examples=["wall"])
    thermal_conductivity: float = Field(..., gt=0, le=500, description="W/m.K")
    density: float = Field(..., gt=0, le=25000, description="kg/m3")
    specific_heat: float = Field(..., gt=0, le=5000, description="J/kg.K")
    emissivity: float = Field(..., ge=0, le=1)
    solar_absorptivity: float = Field(..., ge=0, le=1)
    cost_factor: float = Field(..., gt=0, le=100)


class MaterialResponse(BaseModel):
    id: str
    name: str
    category: str
    thermal_conductivity: float
    density: float
    specific_heat: float
    emissivity: float
    solar_absorptivity: float
    cost_factor: float
    is_custom: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
