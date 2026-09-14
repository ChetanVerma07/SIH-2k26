"""
Deterministic material seed data.

Run with:
    python -m app.seed.seed_materials

Safe to run repeatedly: each material is upserted by its unique `name`,
so re-running never creates duplicates.

NOTE: thermal property values below are representative, commonly-cited
approximations used for early-stage passive design screening. They are
NOT certified engineering values and must not be used as a substitute
for material datasheets or lab-tested values in a real build.
"""
from __future__ import annotations

from app.core.database import get_session
from app.models.material import MaterialCategory
from app.repositories.material_repository import MaterialRepository

MATERIALS = [
    dict(
        name="Concrete (standard, dense)",
        category=MaterialCategory.WALL,
        description="Common cast in-situ dense concrete, uninsulated.",
        thermal_conductivity=1.7500,
        density=2400.00,
        specific_heat=880.00,
        emissivity=0.900,
        solar_absorptivity=0.650,
        cost_factor=1.000,
    ),
    dict(
        name="Fired Clay Brick",
        category=MaterialCategory.WALL,
        description="Standard fired clay brick masonry.",
        thermal_conductivity=0.7200,
        density=1700.00,
        specific_heat=840.00,
        emissivity=0.900,
        solar_absorptivity=0.700,
        cost_factor=0.850,
    ),
    dict(
        name="Local Stone (granite-type)",
        category=MaterialCategory.WALL,
        description="Dense natural stone masonry, common in Ladakh-type cold construction.",
        thermal_conductivity=2.8000,
        density=2600.00,
        specific_heat=790.00,
        emissivity=0.900,
        solar_absorptivity=0.600,
        cost_factor=0.900,
    ),
    dict(
        name="Timber (softwood framing)",
        category=MaterialCategory.WALL,
        description="Softwood timber, structural/framing grade.",
        thermal_conductivity=0.1300,
        density=500.00,
        specific_heat=1600.00,
        emissivity=0.900,
        solar_absorptivity=0.600,
        cost_factor=1.100,
    ),
    dict(
        name="Insulated Sandwich Panel",
        category=MaterialCategory.ROOF,
        description="Metal-faced insulated sandwich panel for roofing.",
        thermal_conductivity=0.0400,
        density=45.00,
        specific_heat=1400.00,
        emissivity=0.300,
        solar_absorptivity=0.400,
        cost_factor=1.400,
    ),
    dict(
        name="Mineral Wool Insulation",
        category=MaterialCategory.INSULATION,
        description="Rock/mineral wool batt insulation.",
        thermal_conductivity=0.0400,
        density=100.00,
        specific_heat=840.00,
        emissivity=0.900,
        solar_absorptivity=0.500,
        cost_factor=1.000,
    ),
    dict(
        name="EPS (Expanded Polystyrene)",
        category=MaterialCategory.INSULATION,
        description="Rigid EPS foam board insulation.",
        thermal_conductivity=0.0350,
        density=20.00,
        specific_heat=1450.00,
        emissivity=0.600,
        solar_absorptivity=0.500,
        cost_factor=0.800,
    ),
    dict(
        name="XPS (Extruded Polystyrene)",
        category=MaterialCategory.INSULATION,
        description="Rigid XPS foam board insulation, higher density/moisture resistance than EPS.",
        thermal_conductivity=0.0300,
        density=35.00,
        specific_heat=1450.00,
        emissivity=0.600,
        solar_absorptivity=0.500,
        cost_factor=1.050,
    ),
    dict(
        name="Rammed Earth",
        category=MaterialCategory.WALL,
        description="Compacted earth wall, high thermal mass, traditional passive construction.",
        thermal_conductivity=1.1000,
        density=2000.00,
        specific_heat=1000.00,
        emissivity=0.900,
        solar_absorptivity=0.700,
        cost_factor=0.600,
    ),
    dict(
        name="Concrete Floor Slab",
        category=MaterialCategory.FLOOR,
        description="Standard poured concrete floor slab.",
        thermal_conductivity=1.6500,
        density=2300.00,
        specific_heat=880.00,
        emissivity=0.900,
        solar_absorptivity=0.650,
        cost_factor=0.950,
    ),
]


def run() -> None:
    with get_session() as session:
        repo = MaterialRepository(session)
        created, skipped = 0, 0
        for material in MATERIALS:
            existing = repo.get_by_name(material["name"])
            if existing:
                skipped += 1
                continue
            repo.create(**material)
            created += 1
        print(f"Materials seed complete: {created} created, {skipped} already present.")


if __name__ == "__main__":
    run()
