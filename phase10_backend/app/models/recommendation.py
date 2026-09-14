from dataclasses import dataclass, field
from typing import List


@dataclass
class Recommendation:
    project_id: str
    recommended_design_id: str
    score: float
    performance: dict
    explanation: str
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
