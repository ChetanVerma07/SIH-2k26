"""
Climate input models.

Two input modes are supported (see README for examples):

MODE 1 - CONSTANT:
    A single ConstantClimate object applies the same ambient temperature
    and solar radiation for the entire simulation.

MODE 2 - TIME SERIES:
    A list of ClimatePoint objects, each tagged with a time (in hours from
    the start of the simulation). Values between supplied timestamps are
    linearly interpolated to whatever time step the simulation uses.

Units:
    time                 : hours from simulation start, >= 0
    ambient_temperature  : degrees Celsius
    solar_radiation      : W/m^2 (global horizontal irradiance, >= 0)
    ground_temperature   : degrees Celsius (optional; defaults to
                            ambient_temperature if not supplied - a
                            documented simplification, see README)
"""
from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator


class ConstantClimate(BaseModel):
    """Constant climate conditions held fixed for the whole simulation."""

    ambient_temperature: float = Field(
        ..., description="Constant outdoor air temperature, degC"
    )
    solar_radiation: float = Field(
        ..., ge=0, description="Constant global horizontal solar radiation, W/m^2"
    )
    ground_temperature: Optional[float] = Field(
        None,
        description=(
            "Ground/sub-floor temperature, degC. Defaults to "
            "ambient_temperature if omitted."
        ),
    )


class ClimatePoint(BaseModel):
    """A single point in a climate time series."""

    time: float = Field(..., ge=0, description="Time from simulation start, hours")
    ambient_temperature: float = Field(..., description="Outdoor air temperature, degC")
    solar_radiation: float = Field(
        ..., ge=0, description="Global horizontal solar radiation, W/m^2"
    )
    ground_temperature: Optional[float] = Field(
        None, description="Ground temperature, degC. Defaults to ambient_temperature."
    )


class ClimateTimeSeries(BaseModel):
    """Wrapper so a bare list can also be validated with a friendly error."""

    points: List[ClimatePoint] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _sorted_unique_times(self) -> "ClimateTimeSeries":
        times = [p.time for p in self.points]
        if len(times) != len(set(times)):
            raise ValueError("climate time series contains duplicate 'time' values")
        if times != sorted(times):
            raise ValueError("climate time series must be sorted by 'time'")
        return self


ClimateInput = Union[ConstantClimate, List[ClimatePoint]]
