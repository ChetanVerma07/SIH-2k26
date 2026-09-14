from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class ClimateRecord:
    id: str
    location: Optional[str]
    temperature: float
    humidity: float
    pressure: float
    solar_radiation: float
    wind_speed: float
    wind_direction: float
    is_preset: bool = False
    time_series: Optional[List[dict]] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
