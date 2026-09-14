"""
Transparent, configurable multi-objective scoring function.

score = w_comfort   * comfort_score           (maximize)
      - w_heatloss  * heat_loss_score         (minimize)
      + w_solar     * solar_utilization_score  (maximize, but capped -
                                                 see note below)
      - w_material  * material_cost_score      (minimize)

All four component scores are normalized to roughly [0, 1] using
floor-area-relative reference scales, so the weights are portable
across differently-sized shelters. This normalization is a heuristic,
documented choice (see README) — not a physical law.

Design constraint violations are handled by a large additive penalty
rather than silently discarding the candidate, so the optimizer can
still learn a gradient back towards the feasible region.
"""

from optimizer.models.materials import get_material

DEFAULT_WEIGHTS = {
    "comfort": 1.0,        # high importance
    "heat_loss": 1.0,       # high importance
    "solar": 0.5,            # moderate importance
    "material_cost": 0.4,     # moderate importance
}

CONSTRAINT_VIOLATION_PENALTY = 50.0  # per violated constraint

# Reference scales (kWh per m2 of floor area per day) used purely for
# normalization so the score is comparable across shelter sizes.
REF_HEAT_LOSS_KWH_PER_M2 = 6.0
REF_SOLAR_GAIN_KWH_PER_M2 = 3.0
REF_COST_PER_M2 = 120.0


def material_cost_index(design) -> float:
    """Relative material-cost index (not real currency) = sum of
    (layer volume x material cost_factor) across wall, roof, floor and
    insulation layers."""
    wall_mat = get_material(design.wall_material)
    roof_mat = get_material(design.roof_material)
    floor_mat = get_material(design.floor_material)
    ins_mat = get_material(design.insulation_material)

    wall_vol = design.net_wall_area() * design.wall_thickness
    roof_vol = design.floor_area() * design.roof_thickness
    floor_vol = design.floor_area() * design.floor_thickness
    # insulation applied once across wall+roof+floor envelope area
    ins_area = design.net_wall_area() + 2 * design.floor_area()
    ins_vol = ins_area * design.insulation_thickness

    cost = (
        wall_vol * wall_mat.cost_factor
        + roof_vol * roof_mat.cost_factor
        + floor_vol * floor_mat.cost_factor
        + ins_vol * ins_mat.cost_factor
    )
    return cost


def evaluate_candidate(design, climate, evaluator, constraints=None, weights=None) -> dict:
    """Evaluate one ShelterDesign end-to-end: physics + constraints + score.

    Returns a dict with the raw metrics AND the final score, so callers
    (including the explanation generator) can see exactly *why* a
    design scored the way it did.
    """
    weights = weights or DEFAULT_WEIGHTS
    violations = design.validate(constraints)

    metrics = evaluator.evaluate(design, climate)
    cost_index = material_cost_index(design)
    floor_area = max(design.floor_area(), 1e-6)

    comfort_score = metrics["comfort_percentage"] / 100.0
    heat_loss_score = min(
        (metrics["total_heat_loss_kwh"] / floor_area) / REF_HEAT_LOSS_KWH_PER_M2, 2.0
    )
    # Solar utilization: reward solar gain up to the point it meaningfully
    # offsets heating need; beyond that (risk of summer overheating) the
    # marginal benefit is capped rather than rewarded further.
    solar_raw = (metrics["total_solar_gain_kwh"] / floor_area) / REF_SOLAR_GAIN_KWH_PER_M2
    solar_score = min(solar_raw, 1.2)
    material_score = min((cost_index / floor_area) / REF_COST_PER_M2, 2.0)

    score = (
        weights.get("comfort", 1.0) * comfort_score
        - weights.get("heat_loss", 1.0) * heat_loss_score
        + weights.get("solar", 0.5) * solar_score
        - weights.get("material_cost", 0.4) * material_score
    )

    score -= CONSTRAINT_VIOLATION_PENALTY * len(violations)

    return {
        "score": score,
        "valid": len(violations) == 0,
        "violations": violations,
        "comfort_score": comfort_score,
        "heat_loss_score": heat_loss_score,
        "solar_score": solar_score,
        "material_score": material_score,
        "material_cost_index": cost_index,
        **metrics,
    }
