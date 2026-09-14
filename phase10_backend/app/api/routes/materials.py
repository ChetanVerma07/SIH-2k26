from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_material_service
from app.schemas.material import MaterialCreate, MaterialResponse
from app.services.material_service import MaterialService

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", response_model=list[MaterialResponse], summary="List materials, optionally filtered by category")
def list_materials(
    category: Optional[str] = Query(None, description="Filter by category e.g. insulation, wall, roof, floor"),
    service: MaterialService = Depends(get_material_service),
):
    return service.list_materials(category)


@router.post("", response_model=MaterialResponse, status_code=201, summary="Create a custom material")
def create_material(payload: MaterialCreate, service: MaterialService = Depends(get_material_service)):
    return service.create_material(payload)


@router.get("/{material_id}", response_model=MaterialResponse, summary="Get material details")
def get_material(material_id: str, service: MaterialService = Depends(get_material_service)):
    return service.get_material(material_id)
