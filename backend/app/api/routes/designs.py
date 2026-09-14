from fastapi import APIRouter, Depends

from app.dependencies import get_design_service
from app.schemas.design import DesignCreate, DesignResponse, DesignUpdate
from app.services.design_service import DesignService

router = APIRouter(prefix="/designs", tags=["designs"])


@router.post("", response_model=DesignResponse, status_code=201, summary="Create a shelter design")
def create_design(payload: DesignCreate, service: DesignService = Depends(get_design_service)):
    return service.create_design(payload)


@router.get("", response_model=list[DesignResponse], summary="List shelter designs")
def list_designs(service: DesignService = Depends(get_design_service)):
    return service.list_designs()


@router.get("/{design_id}", response_model=DesignResponse, summary="Get design details")
def get_design(design_id: str, service: DesignService = Depends(get_design_service)):
    return service.get_design(design_id)


@router.put("/{design_id}", response_model=DesignResponse, summary="Update a design")
def update_design(design_id: str, payload: DesignUpdate, service: DesignService = Depends(get_design_service)):
    return service.update_design(design_id, payload)


@router.delete("/{design_id}", status_code=204, summary="Delete a design")
def delete_design(design_id: str, service: DesignService = Depends(get_design_service)):
    service.delete_design(design_id)
