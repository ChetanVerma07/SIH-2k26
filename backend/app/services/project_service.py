from typing import List, Optional

from fastapi import HTTPException, status

from app.core.logging import logger
from app.models.project import Project
from app.repositories.memory_repository import RepositoryRegistry, new_id
from app.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, repos: RepositoryRegistry):
        self.repos = repos

    def create_project(self, payload: ProjectCreate) -> Project:
        project = Project(
            id=new_id("proj"),
            name=payload.name,
            location=payload.location,
            description=payload.description,
        )
        self.repos.projects.add(project.id, project)
        logger.info("Created project %s (%s)", project.id, project.name)
        return project

    def list_projects(self) -> List[Project]:
        return self.repos.projects.list()

    def get_project(self, project_id: str) -> Project:
        project = self.repos.projects.get(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found",
            )
        return project

    def get_project_or_none(self, project_id: str) -> Optional[Project]:
        return self.repos.projects.get(project_id)

    def delete_project(self, project_id: str) -> None:
        self.get_project(project_id)  # 404 if missing
        self.repos.projects.delete(project_id)
        logger.info("Deleted project %s", project_id)

    def attach_design(self, project_id: str, design_id: str) -> None:
        project = self.repos.projects.get(project_id)
        if project is not None and design_id not in project.design_ids:
            project.design_ids.append(design_id)
