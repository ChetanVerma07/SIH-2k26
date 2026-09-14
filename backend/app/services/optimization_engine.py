"""
OptimizationEngine abstraction.

`OptimizationEngine` defines the interface used by OptimizationService.
`MockOptimizationEngine` generates candidate designs deterministically by
perturbing the baseline design's insulation thickness and opening
percentage, then scores each candidate using the ThermalEngine. A future
phase can swap in a real AI/optimization component behind this interface.
"""
import copy
from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any, Dict, List, Tuple

from app.models.climate import ClimateRecord
from app.models.design import ShelterDesign
from app.models.material import Material
from app.models.optimization import CandidateDesign
from app.services.thermal_engine import ThermalEngine


class OptimizationEngine(ABC):
    @abstractmethod
    def generate_candidates(
        self,
        baseline_design: ShelterDesign,
        parameters: Dict[str, Any],
    ) -> List[Tuple[ShelterDesign, Dict[str, Any]]]:
        raise NotImplementedError

    @abstractmethod
    def score(
        self,
        design: ShelterDesign,
        climate: ClimateRecord,
        materials: Dict[str, Material],
        target_metric: str,
    ) -> CandidateDesign:
        raise NotImplementedError


class MockOptimizationEngine(OptimizationEngine):
    def __init__(self, thermal_engine: ThermalEngine):
        self.thermal_engine = thermal_engine

    def generate_candidates(
        self,
        baseline_design: ShelterDesign,
        parameters: Dict[str, Any],
    ) -> List[Tuple[ShelterDesign, Dict[str, Any]]]:
        insulation_options = parameters.get("insulation_search_range", [0.02, 0.05, 0.08, 0.12])
        opening_options = parameters.get("opening_search_range", [5, 10, 15, 20])
        max_candidates = parameters.get("max_candidates", 5)

        candidates: List[Tuple[ShelterDesign, Dict[str, Any]]] = []
        for insulation in insulation_options:
            for opening in opening_options:
                if len(candidates) >= max_candidates:
                    break
                candidate_design = replace(
                    copy.deepcopy(baseline_design),
                    insulation_thickness=float(insulation),
                    opening_percentage=float(opening),
                )
                modifications = {
                    "insulation_thickness": float(insulation),
                    "opening_percentage": float(opening),
                }
                candidates.append((candidate_design, modifications))
            if len(candidates) >= max_candidates:
                break

        return candidates

    def score(
        self,
        design: ShelterDesign,
        climate: ClimateRecord,
        materials: Dict[str, Material],
        target_metric: str,
    ) -> CandidateDesign:
        raw = self.thermal_engine.simulate(design, climate, materials, duration=24, timestep=1)

        comfort = raw["comfort_percentage"]
        heat_loss = raw["total_heat_loss"]
        solar_gain = raw["total_solar_gain"]

        # Composite score: reward comfort, penalize excess heat loss.
        # Normalize heat_loss's penalty so it doesn't dominate arbitrarily.
        penalty = heat_loss / (heat_loss + 1000.0) * 100.0
        score = round(max(comfort - 0.5 * penalty, 0.0), 2)

        return CandidateDesign(
            design_id=design.id,
            score=score,
            comfort_percentage=comfort,
            total_heat_loss=heat_loss,
            total_solar_gain=solar_gain,
            modifications={},
        )
