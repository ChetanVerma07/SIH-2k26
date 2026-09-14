from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

VALID_ORIENTATIONS = {"N", "S", "E", "W", "NE", "NW", "SE", "SW"}


class DesignBase(BaseModel):
    length: float = Field(..., gt=0, le=100, description="Length in meters")
    width: float = Field(..., gt=0, le=100, description="Width in meters")
    height: float = Field(..., gt=0, le=20, description="Height in meters")
    wall_thickness: float = Field(..., gt=0, le=2, description="Wall thickness in meters")
    roof_thickness: float = Field(..., gt=0, le=2, description="Roof thickness in meters")
    floor_thickness: float = Field(..., gt=0, le=2, description="Floor thickness in meters")
    insulation_thickness: float = Field(..., ge=0, le=1, description="Insulation thickness in meters")
    opening_percentage: float = Field(..., ge=0, le=90, description="% of wall area that is openings")
    orientation: str = Field(..., examples=["S"])

    wall_material: str
    roof_material: str
    floor_material: str
    insulation_material: str

    occupants: int = Field(..., ge=1, le=200)
    floor_area: float = Field(..., gt=0, le=10000)
    target_min_temperature: float = Field(..., ge=-40, le=40)
    target_max_temperature: float = Field(..., ge=-40, le=50)

    @field_validator("orientation")
    @classmethod
    def validate_orientation(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in VALID_ORIENTATIONS:
            raise ValueError(f"orientation must be one of {sorted(VALID_ORIENTATIONS)}")
        return v_upper

    @field_validator("target_max_temperature")
    @classmethod
    def validate_temp_range(cls, v: float, info):
        min_t = info.data.get("target_min_temperature")
        if min_t is not None and v <= min_t:
            raise ValueError("target_max_temperature must be greater than target_min_temperature")
        return v


class DesignCreate(DesignBase):
    project_id: Optional[str] = Field(None, description="Optional owning project id")


class DesignUpdate(BaseModel):
    length: Optional[float] = Field(None, gt=0, le=100)
    width: Optional[float] = Field(None, gt=0, le=100)
    height: Optional[float] = Field(None, gt=0, le=20)
    wall_thickness: Optional[float] = Field(None, gt=0, le=2)
    roof_thickness: Optional[float] = Field(None, gt=0, le=2)
    floor_thickness: Optional[float] = Field(None, gt=0, le=2)
    insulation_thickness: Optional[float] = Field(None, ge=0, le=1)
    opening_percentage: Optional[float] = Field(None, ge=0, le=90)
    orientation: Optional[str] = None
    wall_material: Optional[str] = None
    roof_material: Optional[str] = None
    floor_material: Optional[str] = None
    insulation_material: Optional[str] = None
    occupants: Optional[int] = Field(None, ge=1, le=200)
    floor_area: Optional[float] = Field(None, gt=0, le=10000)
    target_min_temperature: Optional[float] = Field(None, ge=-40, le=40)
    target_max_temperature: Optional[float] = Field(None, ge=-40, le=50)


class DesignResponse(DesignBase):
    id: str
    project_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
