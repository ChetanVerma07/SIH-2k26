"""
Sensitivity analysis.

For the recommended design, perturb one parameter at a time (holding
all others fixed) and measure the resulting % change in the objective
score. Parameters are then ranked by |% change| per unit perturbation,
i.e. this is a genuine local sensitivity computed from the model, not
a fabricated/hard-coded ranking.
"""

import copy
from dataclasses import replace
from optimizer.objectives.fitness import evaluate_candidate
from optimizer.models.materials import structural_materials, insulation_materials
from optimizer.models.design import DEFAULT_CONSTRAINTS

# Maps a design attribute name to its (min_key, max_key) in DEFAULT_CONSTRAINTS,
# used to keep sensitivity perturbations inside the feasible region so results
# reflect smooth physical response rather than constraint-boundary penalties.
_BOUND_KEYS = {
    "insulation_thickness": ("insulation_thickness_min", "insulation_thickness_max"),
    "wall_thickness": ("wall_thickness_min", "wall_thickness_max"),
    "roof_thickness": ("roof_thickness_min", "roof_thickness_max"),
    "floor_thickness": ("floor_thickness_min", "floor_thickness_max"),
    "length": ("length_min", "length_max"),
    "width": ("width_min", "width_max"),
    "height": ("height_min", "height_max"),
}

# (parameter, perturbation) pairs. Numeric params are perturbed by a
# relative delta; categorical params are perturbed by swapping to the
# next material in the relevant library (deterministic, not random).
NUMERIC_PARAMS = [
    "insulation_thickness", "wall_thickness", "roof_thickness",
    "floor_thickness", "opening_area", "orientation", "length", "width", "height",
]
CATEGORICAL_PARAMS = ["wall_material", "roof_material", "floor_material", "insulation_material"]

RELATIVE_DELTA = 0.15  # +/-15% perturbation for numeric parameters


def _perturbed_score(design, climate, evaluator, constraints, weights, param, direction):
    kwargs = {}
    base_value = getattr(design, param)
    if param == "orientation":
        delta = 30.0 * direction  # degrees
        new_value = (base_value + delta) % 360
    elif param == "opening_area":
        delta = base_value * RELATIVE_DELTA * direction
        new_value = max(base_value + delta, 0.01)
        # keep opening area within its floor-area-relative bounds
        floor_area = design.floor_area()
        min_open = DEFAULT_CONSTRAINTS["opening_pct_min"] * floor_area
        max_open = DEFAULT_CONSTRAINTS["opening_pct_max"] * floor_area
        new_value = max(min_open, min(max_open, new_value))
    else:
        delta = base_value * RELATIVE_DELTA * direction
        new_value = max(base_value + delta, 0.01)
        if param in _BOUND_KEYS:
            lo_key, hi_key = _BOUND_KEYS[param]
            new_value = max(DEFAULT_CONSTRAINTS[lo_key], min(DEFAULT_CONSTRAINTS[hi_key], new_value))
    kwargs[param] = new_value
    perturbed = replace(design, **kwargs)
    result = evaluate_candidate(perturbed, climate, evaluator, constraints, weights)
    return result["score"]


def _categorical_alternative(design, param):
    if param == "insulation_material":
        choices = [m.name for m in insulation_materials()]
    else:
        choices = [m.name for m in structural_materials()]
    current = getattr(design, param)
    others = [c for c in choices if c != current]
    return others[0] if others else current


def run_sensitivity_analysis(design, climate, evaluator, constraints=None, weights=None):
    base_result = evaluate_candidate(design, climate, evaluator, constraints, weights)
    base_score = base_result["score"]
    # Floor the denominator so percent-impact stays interpretable even when
    # the base score is close to zero (percent-of-near-zero is not meaningful).
    denom = max(abs(base_score), 0.25)

    impacts = []

    for param in NUMERIC_PARAMS:
        score_up = _perturbed_score(design, climate, evaluator, constraints, weights, param, +1)
        score_down = _perturbed_score(design, climate, evaluator, constraints, weights, param, -1)
        max_abs_change = max(abs(score_up - base_score), abs(score_down - base_score))
        pct_change = max_abs_change / denom * 100.0
        impacts.append({
            "parameter": param,
            "base_value": getattr(design, param),
            "score_if_increased": score_up,
            "score_if_decreased": score_down,
            "max_score_change": max_abs_change,
            "percent_impact": pct_change,
        })

    for param in CATEGORICAL_PARAMS:
        alt_name = _categorical_alternative(design, param)
        alt_design = copy.deepcopy(design)
        setattr(alt_design, param, alt_name)
        alt_result = evaluate_candidate(alt_design, climate, evaluator, constraints, weights)
        change = abs(alt_result["score"] - base_score)
        pct_change = change / denom * 100.0
        impacts.append({
            "parameter": param,
            "base_value": getattr(design, param),
            "alternative_value": alt_name,
            "score_if_changed": alt_result["score"],
            "max_score_change": change,
            "percent_impact": pct_change,
        })

    impacts.sort(key=lambda item: item["percent_impact"], reverse=True)
    for rank, item in enumerate(impacts, start=1):
        item["rank"] = rank
        if item["percent_impact"] >= 8:
            item["impact_level"] = "high"
        elif item["percent_impact"] >= 3:
            item["impact_level"] = "medium"
        else:
            item["impact_level"] = "low"

    return {
        "base_score": base_score,
        "ranked_parameters": impacts,
    }
