from typing import List

from fastapi import HTTPException, status

from app.core.logging import logger
from app.models.design import ShelterDesign
from app.repositories.memory_repository import RepositoryRegistry, new_id
from app.schemas.design import DesignCreate, DesignUpdate


class DesignService:
    def __init__(self, repos: RepositoryRegistry):
        self.repos = repos

    def create_design(self, payload: DesignCreate) -> ShelterDesign:
        if payload.project_id and not self.repos.projects.exists(payload.project_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{payload.project_id}' not found",
            )
        for field_name in ("wall_material", "roof_material", "floor_material", "insulation_material"):
            material_id = getattr(payload, field_name)
            if not self.repos.materials.exists(material_id):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unknown material id for {field_name}: '{material_id}'",
                )

        design = ShelterDesign(
            id=new_id("design"),
            project_id=payload.project_id,
            length=payload.length,
            width=payload.width,
            height=payload.height,
            wall_thickness=payload.wall_thickness,
            roof_thickness=payload.roof_thickness,
            floor_thickness=payload.floor_thickness,
            insulation_thickness=payload.insulation_thickness,
            opening_percentage=payload.opening_percentage,
            orientation=payload.orientation,
            wall_material=payload.wall_material,
            roof_material=payload.roof_material,
            floor_material=payload.floor_material,
            insulation_material=payload.insulation_material,
            occupants=payload.occupants,
            floor_area=payload.floor_area,
            target_min_temperature=payload.target_min_temperature,
            target_max_temperature=payload.target_max_temperature,
        )
        self.repos.designs.add(design.id, design)

        if payload.project_id:
            project = self.repos.projects.get(payload.project_id)
            if project and design.id not in project.design_ids:
                project.design_ids.append(design.id)

        logger.info("Created design %s", design.id)
        return design

    def list_designs(self) -> List[ShelterDesign]:
        return self.repos.designs.list()

    def get_design(self, design_id: str) -> ShelterDesign:
        design = self.repos.designs.get(design_id)
        if design is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Design '{design_id}' not found",
            )
        return design

    def update_design(self, design_id: str, payload: DesignUpdate) -> ShelterDesign:
        design = self.get_design(design_id)
        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(design, key, value)

        from datetime import datetime, timezone
        design.updated_at = datetime.now(timezone.utc)

        min_t = design.target_min_temperature
        max_t = design.target_max_temperature
        if max_t <= min_t:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="target_max_temperature must be greater than target_min_temperature",
            )

        logger.info("Updated design %s", design_id)
        return design

    def delete_design(self, design_id: str) -> None:
        self.get_design(design_id)
        self.repos.designs.delete(design_id)
        logger.info("Deleted design %s", design_id)
