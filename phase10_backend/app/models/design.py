from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ShelterDesign:
    id: str
    project_id: Optional[str]

    # Geometry
    length: float
    width: float
    height: float
    wall_thickness: float
    roof_thickness: float
    floor_thickness: float
    insulation_thickness: float
    opening_percentage: float
    orientation: str

    # Materials (material IDs)
    wall_material: str
    roof_material: str
    floor_material: str
    insulation_material: str

    # Requirements
    occupants: int
    floor_area: float
    target_min_temperature: float
    target_max_temperature: float

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
