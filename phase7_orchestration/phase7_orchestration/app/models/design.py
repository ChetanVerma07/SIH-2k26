"""Shelter design candidate models."""
from enum import Enum
from pydantic import BaseModel, Field


class WallMaterial(str, Enum):
    MUD_BRICK = "mud_brick"
    RAMMED_EARTH = "rammed_earth"
    STONE_INSULATED = "stone_insulated"
    TIMBER_INSULATED = "timber_insulated"
    CONCRETE_BLOCK = "concrete_block"


class RoofMaterial(str, Enum):
    THATCH = "thatch"
    INSULATED_METAL = "insulated_metal"
    EARTH_ROOF = "earth_roof"
    TIMBER_INSULATED = "timber_insulated"


class FloorMaterial(str, Enum):
    COMPACTED_EARTH = "compacted_earth"
    INSULATED_CONCRETE = "insulated_concrete"
    RAISED_TIMBER = "raised_timber"


# Approximate thermal conductivity (W/mK) — used by the mock thermal simulator
# to respond logically to material choice. These are illustrative, not
# validated engineering constants (see README limitations section).
MATERIAL_CONDUCTIVITY = {
    WallMaterial.MUD_BRICK: 0.90,
    WallMaterial.RAMMED_EARTH: 0.70,
    WallMaterial.STONE_INSULATED: 0.35,
    WallMaterial.TIMBER_INSULATED: 0.18,
    WallMaterial.CONCRETE_BLOCK: 1.10,
}

MATERIAL_COST_FACTOR = {
    WallMaterial.MUD_BRICK: 0.6,
    WallMaterial.RAMMED_EARTH: 0.7,
    WallMaterial.STONE_INSULATED: 1.3,
    WallMaterial.TIMBER_INSULATED: 1.5,
    WallMaterial.CONCRETE_BLOCK: 1.0,
}


class ShelterDesign(BaseModel):
    """A single candidate shelter design."""

    design_id: str
    label: str = Field(default="Design")
    length_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    height_m: float = Field(gt=0)
    orientation_deg: float = Field(
        ge=0, lt=360, description="0 = main facade faces true north, 180 = south-facing"
    )
    wall_material: WallMaterial
    roof_material: RoofMaterial
    floor_material: FloorMaterial
    insulation_thickness_m: float = Field(ge=0, le=1.0)
    opening_area_m2: float = Field(ge=0, description="Total window/door glazing area")
    is_baseline: bool = Field(default=False)

    @property
    def floor_area_m2(self) -> float:
        return self.length_m * self.width_m

    @property
    def wall_area_m2(self) -> float:
        return 2 * (self.length_m + self.width_m) * self.height_m

    @property
    def dimensions_str(self) -> str:
        return f"{self.length_m:.1f}m x {self.width_m:.1f}m x {self.height_m:.1f}m"
