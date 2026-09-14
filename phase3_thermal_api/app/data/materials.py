"""
Example material definitions.

These are illustrative, commonly-cited property values for materials used
in passive shelter construction. They are provided for convenience and
demo purposes only - the API is NOT hard-coded around them. Any caller can
submit fully custom Material objects with their own values.

Sources for the ballpark values used here: standard building-physics
references (e.g. ASHRAE Handbook of Fundamentals, CIBSE Guide A) rounded
to representative figures. Real designs should use site- and
supplier-specific measured values.
"""
from __future__ import annotations

from app.models.material import Material

EXAMPLE_MATERIALS: dict[str, Material] = {
    "adobe_mud_brick": Material(
        name="Adobe / Mud Brick",
        thermal_conductivity=0.6,
        density=1600,
        specific_heat=850,
        thickness=0.30,
        solar_absorptivity=0.65,
        emissivity=0.90,
    ),
    "rammed_earth": Material(
        name="Rammed Earth",
        thermal_conductivity=0.70,
        density=2000,
        specific_heat=800,
        thickness=0.40,
        solar_absorptivity=0.65,
        emissivity=0.90,
    ),
    "fired_clay_brick": Material(
        name="Fired Clay Brick",
        thermal_conductivity=0.72,
        density=1700,
        specific_heat=840,
        thickness=0.23,
        solar_absorptivity=0.60,
        emissivity=0.90,
    ),
    "concrete_dense": Material(
        name="Dense Concrete",
        thermal_conductivity=1.40,
        density=2300,
        specific_heat=880,
        thickness=0.15,
        solar_absorptivity=0.65,
        emissivity=0.90,
    ),
    "straw_bale": Material(
        name="Straw Bale (insulating)",
        thermal_conductivity=0.07,
        density=110,
        specific_heat=1500,
        thickness=0.45,
        solar_absorptivity=0.50,
        emissivity=0.85,
    ),
    "timber_softwood": Material(
        name="Softwood Timber",
        thermal_conductivity=0.14,
        density=500,
        specific_heat=1600,
        thickness=0.05,
        solar_absorptivity=0.55,
        emissivity=0.90,
    ),
    "natural_stone_granite": Material(
        name="Granite / Natural Stone",
        thermal_conductivity=2.50,
        density=2600,
        specific_heat=790,
        thickness=0.40,
        solar_absorptivity=0.55,
        emissivity=0.90,
    ),
    "eps_insulation": Material(
        name="EPS Rigid Insulation",
        thermal_conductivity=0.035,
        density=30,
        specific_heat=1450,
        thickness=0.05,
        solar_absorptivity=0.40,
        emissivity=0.90,
    ),
    "corrugated_metal_sheet": Material(
        name="Corrugated Metal Roofing Sheet",
        thermal_conductivity=50.0,
        density=7850,
        specific_heat=490,
        thickness=0.002,
        solar_absorptivity=0.70,
        emissivity=0.25,
    ),
    "single_glazed_window": Material(
        name="Single-Glazed Window Pane",
        thermal_conductivity=1.0,
        density=2500,
        specific_heat=840,
        thickness=0.006,
        solar_absorptivity=0.10,
        emissivity=0.90,
    ),
}


def get_example_materials() -> dict[str, Material]:
    return EXAMPLE_MATERIALS
