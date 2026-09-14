from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Material:
    id: str
    name: str
    category: str
    thermal_conductivity: float  # W/m.K
    density: float  # kg/m3
    specific_heat: float  # J/kg.K
    emissivity: float
    solar_absorptivity: float
    cost_factor: float
    is_custom: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
