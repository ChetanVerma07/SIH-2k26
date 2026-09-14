import json
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, status

from app.core.logging import logger
from app.models.material import Material
from app.repositories.memory_repository import RepositoryRegistry, new_id
from app.schemas.material import MaterialCreate

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MATERIALS_FILE = DATA_DIR / "materials.json"


class MaterialService:
    def __init__(self, repos: RepositoryRegistry):
        self.repos = repos
        self._loaded = False
        self._load_seed_materials()

    def _load_seed_materials(self) -> None:
        if self._loaded or not MATERIALS_FILE.exists():
            return
        with open(MATERIALS_FILE, "r") as f:
            materials = json.load(f)

        for m in materials:
            material_id = m.get("id") or new_id("mat")
            if self.repos.materials.exists(material_id):
                continue
            material = Material(
                id=material_id,
                name=m["name"],
                category=m["category"],
                thermal_conductivity=m["thermal_conductivity"],
                density=m["density"],
                specific_heat=m["specific_heat"],
                emissivity=m["emissivity"],
                solar_absorptivity=m["solar_absorptivity"],
                cost_factor=m["cost_factor"],
                is_custom=False,
            )
            self.repos.materials.add(material.id, material)
        self._loaded = True

    def list_materials(self, category: Optional[str] = None) -> List[Material]:
        materials = self.repos.materials.list()
        if category:
            materials = [m for m in materials if m.category.lower() == category.lower()]
        return materials

    def get_material(self, material_id: str) -> Material:
        material = self.repos.materials.get(material_id)
        if material is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material '{material_id}' not found",
            )
        return material

    def create_material(self, payload: MaterialCreate) -> Material:
        material = Material(
            id=new_id("mat"),
            name=payload.name,
            category=payload.category,
            thermal_conductivity=payload.thermal_conductivity,
            density=payload.density,
            specific_heat=payload.specific_heat,
            emissivity=payload.emissivity,
            solar_absorptivity=payload.solar_absorptivity,
            cost_factor=payload.cost_factor,
            is_custom=True,
        )
        self.repos.materials.add(material.id, material)
        logger.info("Created custom material %s (%s)", material.id, material.name)
        return material
