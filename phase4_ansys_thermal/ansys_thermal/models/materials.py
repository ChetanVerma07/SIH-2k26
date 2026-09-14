"""
Material property model.

Independent of the ANSYS execution layer: this module only describes
material properties in engineering units. The ANSYS input generator is
responsible for translating these into ANSYS material definitions
(Engineering Data / APDL MP commands).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Material:
    """Thermal material properties.

    Units:
        thermal_conductivity_w_mk : W/(m.K)
        density_kg_m3             : kg/m^3
        specific_heat_j_kgk       : J/(kg.K)
        emissivity                : dimensionless [0, 1]
        solar_absorptivity        : dimensionless [0, 1]
    """

    name: str
    thermal_conductivity_w_mk: float
    density_kg_m3: float
    specific_heat_j_kgk: float
    emissivity: float = 0.9
    solar_absorptivity: float = 0.6

    def thermal_diffusivity_m2_s(self) -> float:
        """alpha = k / (rho * cp)"""
        denom = self.density_kg_m3 * self.specific_heat_j_kgk
        if denom <= 0:
            return 0.0
        return self.thermal_conductivity_w_mk / denom

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["derived"] = {
            "thermal_diffusivity_m2_s": self.thermal_diffusivity_m2_s(),
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Material":
        data = dict(data)
        data.pop("derived", None)
        return cls(**data)


@dataclass
class MaterialAssignment:
    """Assigns a Material to each major building element."""

    wall_material: Material
    roof_material: Material
    floor_material: Material
    window_material: Material

    def as_dict(self) -> Dict[str, Any]:
        return {
            "wall_material": self.wall_material.as_dict(),
            "roof_material": self.roof_material.as_dict(),
            "floor_material": self.floor_material.as_dict(),
            "window_material": self.window_material.as_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaterialAssignment":
        return cls(
            wall_material=Material.from_dict(data["wall_material"]),
            roof_material=Material.from_dict(data["roof_material"]),
            floor_material=Material.from_dict(data["floor_material"]),
            window_material=Material.from_dict(data["window_material"]),
        )


# ---------------------------------------------------------------------
# Example material library.
#
# These are commonly cited approximate engineering values for building
# materials. They are provided as convenient defaults/examples only.
# For a real design, values should be confirmed against manufacturer
# datasheets or material testing, and then validated in ANSYS.
# ---------------------------------------------------------------------

EXAMPLE_MATERIALS: Dict[str, Material] = {
    "rammed_earth": Material(
        name="Rammed Earth",
        thermal_conductivity_w_mk=1.1,
        density_kg_m3=2000.0,
        specific_heat_j_kgk=900.0,
        emissivity=0.9,
        solar_absorptivity=0.65,
    ),
    "burnt_clay_brick": Material(
        name="Burnt Clay Brick",
        thermal_conductivity_w_mk=0.72,
        density_kg_m3=1700.0,
        specific_heat_j_kgk=840.0,
        emissivity=0.9,
        solar_absorptivity=0.7,
    ),
    "concrete_dense": Material(
        name="Dense Concrete",
        thermal_conductivity_w_mk=1.75,
        density_kg_m3=2400.0,
        specific_heat_j_kgk=880.0,
        emissivity=0.9,
        solar_absorptivity=0.6,
    ),
    "aac_block": Material(
        name="Autoclaved Aerated Concrete (AAC) Block",
        thermal_conductivity_w_mk=0.16,
        density_kg_m3=550.0,
        specific_heat_j_kgk=1000.0,
        emissivity=0.9,
        solar_absorptivity=0.5,
    ),
    "expanded_polystyrene": Material(
        name="Expanded Polystyrene (EPS) Insulation",
        thermal_conductivity_w_mk=0.034,
        density_kg_m3=20.0,
        specific_heat_j_kgk=1300.0,
        emissivity=0.6,
        solar_absorptivity=0.3,
    ),
    "single_glass": Material(
        name="Single Pane Glass",
        thermal_conductivity_w_mk=1.0,
        density_kg_m3=2500.0,
        specific_heat_j_kgk=840.0,
        emissivity=0.84,
        solar_absorptivity=0.06,
    ),
    "double_glass": Material(
        name="Double Pane Glass (air gap)",
        thermal_conductivity_w_mk=0.7,
        density_kg_m3=2500.0,
        specific_heat_j_kgk=840.0,
        emissivity=0.84,
        solar_absorptivity=0.05,
    ),
    "timber_softwood": Material(
        name="Softwood Timber",
        thermal_conductivity_w_mk=0.13,
        density_kg_m3=500.0,
        specific_heat_j_kgk=1600.0,
        emissivity=0.9,
        solar_absorptivity=0.6,
    ),
}


def get_example_material(key: str) -> Material:
    """Look up a bundled example material by key.

    Raises KeyError with the list of valid keys if not found, so
    callers get a clear, documented error rather than a silent
    fallback / invented value.
    """
    try:
        return EXAMPLE_MATERIALS[key]
    except KeyError as exc:
        valid = ", ".join(sorted(EXAMPLE_MATERIALS.keys()))
        raise KeyError(
            f"Unknown example material '{key}'. Valid options: {valid}"
        ) from exc
