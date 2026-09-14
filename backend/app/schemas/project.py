from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, examples=["Ladakh Winter Shelter"])
    location: str = Field(..., min_length=1, max_length=200, examples=["Leh, Ladakh, India"])
    description: Optional[str] = Field(None, max_length=2000)


class ProjectResponse(BaseModel):
    id: str
    name: str
    location: str
    description: Optional[str] = None
    created_at: datetime
    design_ids: List[str] = []

    model_config = {"from_attributes": True}
