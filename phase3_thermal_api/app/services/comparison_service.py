"""
Comparison service.

Runs the thermal simulation for several shelter configurations under the
same climate, then ranks them using a configurable, non-ML weighted score:

    score = w_comfort   * normalized(comfort_percentage)
          + w_heat_loss  * normalized(-total_heat_loss)   # lower loss -> higher score
          + w_solar_gain * normalized(total_solar_energy_gained)

Each metric is min-max normalized across the compared designs so that the
three criteria (measured in very different units/scales) can be combined
fairly. If every design ties on a metric, that metric contributes a
neutral 1.0 to every design's score for that term.
"""
from __future__ import annotations

from typing import Dict, List

from app.models.simulation import (
    CompareRequest,
    CompareResult,
    RankedDesign,
    SimulationRequest,
    SimulationResult,
)
from app.services.simulation_service import run_and_summarize

DEFAULT_WEIGHTS = {"comfort": 0.5, "heat_loss": 0.3, "solar_gain": 0.2}


def _normalize(values: List[float], invert: bool = False) -> List[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0 for _ in values]
    if invert:
        return [(hi - v) / (hi - lo) for v in values]
    return [(v - lo) / (hi - lo) for v in values]


def run_comparison(request: CompareRequest) -> CompareResult:
    weights: Dict[str, float] = dict(DEFAULT_WEIGHTS)
    if request.ranking_weights:
        weights.update(request.ranking_weights)

    results: List[SimulationResult] = []
    for shelter in request.shelters:
        sim_request = SimulationRequest(
            climate=request.climate, shelter=shelter, settings=request.settings
        )
        results.append(run_and_summarize(shelter, sim_request))

    comfort_scores = _normalize([r.summary.comfort_percentage for r in results])
    heat_loss_scores = _normalize([r.summary.total_heat_loss for r in results], invert=True)
    solar_scores = _normalize([r.summary.total_solar_energy_gained for r in results])

    combined = []
    for i, result in enumerate(results):
        score = (
            weights.get("comfort", 0.0) * comfort_scores[i]
            + weights.get("heat_loss", 0.0) * heat_loss_scores[i]
            + weights.get("solar_gain", 0.0) * solar_scores[i]
        )
        combined.append((result, score))

    combined.sort(key=lambda pair: pair[1], reverse=True)

    ranked_designs = [
        RankedDesign(shelter_name=result.shelter_name, rank=i + 1, score=score, result=result)
        for i, (result, score) in enumerate(combined)
    ]

    return CompareResult(ranking_weights=weights, designs=ranked_designs)
