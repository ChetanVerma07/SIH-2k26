from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Project:
    id: str
    name: str
    location: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    design_ids: list = field(default_factory=list)
