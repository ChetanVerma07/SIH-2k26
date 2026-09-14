from fastapi import APIRouter, Depends

from app.dependencies import get_project_service
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201, summary="Create a project")
def create_project(payload: ProjectCreate, service: ProjectService = Depends(get_project_service)):
    return service.create_project(payload)


@router.get("", response_model=list[ProjectResponse], summary="List projects")
def list_projects(service: ProjectService = Depends(get_project_service)):
    return service.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get project details")
def get_project(project_id: str, service: ProjectService = Depends(get_project_service)):
    return service.get_project(project_id)


@router.delete("/{project_id}", status_code=204, summary="Delete a project")
def delete_project(project_id: str, service: ProjectService = Depends(get_project_service)):
    service.delete_project(project_id)
