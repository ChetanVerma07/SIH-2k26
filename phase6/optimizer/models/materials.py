"""
Material library for Phase 6.

Each Material carries the physical properties needed by the thermal
evaluator. `thickness` on the Material is only a *reference/typical*
value (as requested in the spec) — the thickness that is actually used
in a given shelter design comes from the ShelterDesign object
(wall_thickness, roof_thickness, floor_thickness, insulation_thickness),
because the same material can be used at different thicknesses in
different candidate designs.

Materials are tagged with a `category` so the optimizer knows which
materials are valid choices for which building element:
    - "structural"  -> usable for wall / roof / floor
    - "insulation"  -> usable for the insulation layer
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    name: str
    conductivity: float        # W/(m.K)
    density: float              # kg/m3
    specific_heat: float        # J/(kg.K)
    thickness: float            # m (typical/reference thickness)
    solar_absorptivity: float   # 0-1 (fraction of incident solar absorbed)
    emissivity: float           # 0-1
    cost_factor: float          # relative cost per m3 (dimensionless index)
    category: str                # "structural" or "insulation"


MATERIAL_LIBRARY = {
    # ---- structural / envelope materials ----
    "concrete_block": Material(
        name="concrete_block", conductivity=1.35, density=2000, specific_heat=880,
        thickness=0.20, solar_absorptivity=0.65, emissivity=0.90, cost_factor=3.0,
        category="structural",
    ),
    "fired_brick": Material(
        name="fired_brick", conductivity=0.72, density=1700, specific_heat=840,
        thickness=0.23, solar_absorptivity=0.60, emissivity=0.90, cost_factor=2.5,
        category="structural",
    ),
    "stone_masonry": Material(
        name="stone_masonry", conductivity=1.70, density=2400, specific_heat=850,
        thickness=0.30, solar_absorptivity=0.55, emissivity=0.90, cost_factor=2.2,
        category="structural",
    ),
    "rammed_earth": Material(
        name="rammed_earth", conductivity=0.55, density=1900, specific_heat=900,
        thickness=0.35, solar_absorptivity=0.70, emissivity=0.90, cost_factor=1.2,
        category="structural",
    ),
    "timber_frame": Material(
        name="timber_frame", conductivity=0.13, density=500, specific_heat=1600,
        thickness=0.15, solar_absorptivity=0.50, emissivity=0.85, cost_factor=3.5,
        category="structural",
    ),
    "cavity_wall_composite": Material(
        name="cavity_wall_composite", conductivity=0.45, density=1200, specific_heat=900,
        thickness=0.25, solar_absorptivity=0.55, emissivity=0.88, cost_factor=2.8,
        category="structural",
    ),
    # ---- insulation materials ----
    "eps_insulation": Material(
        name="eps_insulation", conductivity=0.035, density=20, specific_heat=1450,
        thickness=0.05, solar_absorptivity=0.40, emissivity=0.60, cost_factor=4.0,
        category="insulation",
    ),
    "mineral_wool": Material(
        name="mineral_wool", conductivity=0.040, density=100, specific_heat=840,
        thickness=0.08, solar_absorptivity=0.40, emissivity=0.60, cost_factor=4.5,
        category="insulation",
    ),
    "xps_insulation": Material(
        name="xps_insulation", conductivity=0.029, density=35, specific_heat=1450,
        thickness=0.05, solar_absorptivity=0.40, emissivity=0.60, cost_factor=5.5,
        category="insulation",
    ),
    "straw_bale": Material(
        name="straw_bale", conductivity=0.070, density=110, specific_heat=1500,
        thickness=0.35, solar_absorptivity=0.45, emissivity=0.75, cost_factor=1.0,
        category="insulation",
    ),
    "cellulose_fiber": Material(
        name="cellulose_fiber", conductivity=0.040, density=45, specific_heat=1900,
        thickness=0.10, solar_absorptivity=0.40, emissivity=0.70, cost_factor=2.0,
        category="insulation",
    ),
}


def structural_materials():
    return [m for m in MATERIAL_LIBRARY.values() if m.category == "structural"]


def insulation_materials():
    return [m for m in MATERIAL_LIBRARY.values() if m.category == "insulation"]


def get_material(name: str) -> Material:
    if name not in MATERIAL_LIBRARY:
        raise KeyError(f"Unknown material '{name}'. Available: {list(MATERIAL_LIBRARY)}")
    return MATERIAL_LIBRARY[name]
