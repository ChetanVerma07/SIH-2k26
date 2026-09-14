"""
Shelter geometry, orientation and opening models.

Units:
    length, width, height : m
    *_area                : m^2

ORIENTATION SIMPLIFICATION (documented, see README "Orientation" section):
    The shelter is treated as a rectangular box. One "front" facade (of
    area width * height) is assumed to face the compass direction given
    by `orientation`. Solar exposure of that facade is scaled by an
    `orientation_factor` (1.0 = full exposure, facing the sun; lower
    values approximate a facade that is oblique or facing away from the
    sun for a chunk of the day). The roof is always assumed to receive
    the full supplied solar_radiation (it faces the sky). This is a
    simplification, not a full solar-geometry / sun-path engine.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

from app.models.material import Material, MaterialAssembly, as_layers

# Simplified orientation -> solar exposure factor for the "front" facade.
# South is the reference full-exposure direction (northern-hemisphere,
# passive-solar-design convention used widely in India/the Himalayas).
ORIENTATION_SOLAR_FACTOR = {
    "S": 1.0,
    "SE": 0.85,
    "SW": 0.85,
    "E": 0.6,
    "W": 0.6,
    "NE": 0.4,
    "NW": 0.4,
    "N": 0.2,
}


class Orientation(str, Enum):
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"

    @property
    def solar_factor(self) -> float:
        return ORIENTATION_SOLAR_FACTOR[self.value]


class OpeningProperties(BaseModel):
    """Windows, doors, and other openings (vents, skylights, etc.)."""

    window_area: float = Field(0.0, ge=0, description="Total window area, m^2")
    door_area: float = Field(0.0, ge=0, description="Total door area, m^2")
    other_opening_area: float = Field(
        0.0, ge=0, description="Other openings (vents, skylights...), m^2"
    )
    opening_u_value: float = Field(
        5.8,
        gt=0,
        description=(
            "Overall U-value applied to all openings, W/(m^2*K). "
            "Default 5.8 approximates a typical single-glazed window/door."
        ),
    )
    window_shgc: float = Field(
        0.6,
        ge=0,
        le=1,
        description=(
            "Solar Heat Gain Coefficient for windows only: fraction of "
            "incident solar radiation transmitted indoors as direct gain. "
            "Doors and other openings are treated as opaque (no solar "
            "transmission) in this simplified model."
        ),
    )

    @property
    def total_area(self) -> float:
        return self.window_area + self.door_area + self.other_opening_area


class ShelterConfig(BaseModel):
    """Complete geometric + material description of a passive shelter."""

    name: str = Field("shelter", description="Identifier for this design")
    length: float = Field(..., gt=0, description="Footprint length, m")
    width: float = Field(..., gt=0, description="Footprint width, m")
    height: float = Field(..., gt=0, description="Wall height, m")
    orientation: Orientation = Field(
        Orientation.S, description="Compass direction the 'front' facade faces"
    )

    wall_material: MaterialAssembly = Field(
        ..., description="Single Material or ordered list of layers for walls"
    )
    roof_material: MaterialAssembly = Field(
        ..., description="Single Material or ordered list of layers for the roof"
    )
    floor_material: MaterialAssembly = Field(
        ..., description="Single Material or ordered list of layers for the floor"
    )

    openings: OpeningProperties = Field(default_factory=OpeningProperties)

    structural_mass_fraction: float = Field(
        0.3,
        ge=0,
        le=1,
        description=(
            "Fraction of the wall/roof/floor structural heat capacity that "
            "is thermally coupled to the indoor air node each timestep. "
            "This is a simplification standing in for a full multi-node "
            "(wall-surface / core / indoor-air) RC network - see README."
        ),
    )

    @model_validator(mode="after")
    def _validate_openings_fit_on_walls(self) -> "ShelterConfig":
        wall_area = self.gross_wall_area
        opening_area = self.openings.total_area
        if opening_area > wall_area:
            raise ValueError(
                f"Total opening area ({opening_area:.2f} m^2) exceeds the "
                f"gross wall area ({wall_area:.2f} m^2) available to hold them."
            )
        return self

    # ---- Derived geometry -------------------------------------------------

    @property
    def gross_wall_area(self) -> float:
        """Total wall area before subtracting openings, m^2."""
        return 2.0 * (self.length + self.width) * self.height

    @property
    def net_wall_area(self) -> float:
        """
        Wall area actually conducting heat (openings removed so they are
        not double-counted between wall and opening heat loss terms).
        """
        return max(self.gross_wall_area - self.openings.total_area, 0.0)

    @property
    def front_facade_area(self) -> float:
        """
        Area of the single facade assumed to face `orientation`, used only
        for the simplified solar-gain calculation (see module docstring).
        """
        return self.width * self.height

    @property
    def front_facade_opening_share(self) -> float:
        """
        Share of total opening area assumed to sit on the front facade,
        for the purposes of excluding it from the front facade's solar-
        absorbing area. Assumes openings are evenly distributed across the
        four facades.
        """
        return self.openings.total_area / 4.0

    @property
    def roof_area(self) -> float:
        return self.length * self.width

    @property
    def floor_area(self) -> float:
        return self.length * self.width

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height

    # ---- Derived thermal properties ----------------------------------------

    def wall_layers(self) -> list[Material]:
        return as_layers(self.wall_material)

    def roof_layers(self) -> list[Material]:
        return as_layers(self.roof_material)

    def floor_layers(self) -> list[Material]:
        return as_layers(self.floor_material)
