"""Incoming user request models and validation."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ComfortRange(BaseModel):
    min_c: float
    max_c: float

    @field_validator("max_c")
    @classmethod
    def max_must_exceed_min(cls, v: float, info) -> float:
        min_c = info.data.get("min_c")
        if min_c is not None and v <= min_c:
            raise ValueError("comfort range max_c must be greater than min_c")
        return v


class ShelterDesignRequest(BaseModel):
    """High-level user request describing what shelter to design."""

    location: str = Field(..., min_length=1)
    climate_description: str = Field(..., min_length=1)
    comfort_range: ComfortRange
    objectives: list[str] = Field(
        default_factory=lambda: [
            "maximize thermal comfort",
            "minimize heat loss",
            "minimize external energy requirement",
        ]
    )
    budget: Optional[float] = Field(default=None, ge=0)
    available_materials: Optional[list[str]] = Field(default=None)
    simulation_duration_hours: int = Field(default=24, gt=0, le=8760)
    run_ansys_validation: bool = Field(default=True)

    @field_validator("location", "climate_description")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must not be blank")
        return v.strip()


class WhatIfRequest(BaseModel):
    """Request to vary a single design parameter and observe the effect."""

    location: str
    climate_description: str
    comfort_range: ComfortRange
    base_design_id: Optional[str] = Field(
        default=None, description="If omitted, the top-ranked design from a fresh run is used"
    )
    parameter: str = Field(
        ..., description="One of: insulation_thickness_m, window_area_m2, wall_material, orientation_deg"
    )
    new_value: float | str

    @field_validator("parameter")
    @classmethod
    def known_parameter(cls, v: str) -> str:
        allowed = {"insulation_thickness_m", "window_area_m2", "wall_material", "orientation_deg"}
        if v not in allowed:
            raise ValueError(f"parameter must be one of {sorted(allowed)}")
        return v


class CompareRequest(BaseModel):
    """Request to compare two or more designs directly."""

    location: str
    climate_description: str
    comfort_range: ComfortRange
    design_ids: list[str] = Field(default_factory=list, max_length=10)
