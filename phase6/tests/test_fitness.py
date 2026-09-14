import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from optimizer.models.design import ShelterDesign
from optimizer.models.climate import SCENARIOS
from optimizer.thermal.simplified_model import FastThermalEvaluator
from optimizer.objectives.fitness import evaluate_candidate, material_cost_index, DEFAULT_WEIGHTS


def base_design():
    return ShelterDesign(
        length=6.0, width=5.0, height=2.8,
        wall_thickness=0.25, roof_thickness=0.20, floor_thickness=0.15,
        insulation_thickness=0.08,
        wall_material="rammed_earth", roof_material="timber_frame",
        floor_material="stone_masonry", insulation_material="mineral_wool",
        opening_area=3.0, door_area=2.0, orientation=0.0,
    )


def test_valid_candidate_has_no_violations():
    evaluator = FastThermalEvaluator()
    result = evaluate_candidate(base_design(), SCENARIOS["cold_winter_day"], evaluator)
    assert result["valid"] is True
    assert result["violations"] == []


def test_invalid_candidate_is_penalized():
    evaluator = FastThermalEvaluator()
    design = base_design()
    design.length = 1.0  # violates min length
    result = evaluate_candidate(design, SCENARIOS["cold_winter_day"], evaluator)
    assert result["valid"] is False
    assert len(result["violations"]) > 0
    valid_result = evaluate_candidate(base_design(), SCENARIOS["cold_winter_day"], evaluator)
    assert result["score"] < valid_result["score"]


def test_weights_change_the_score():
    evaluator = FastThermalEvaluator()
    design = base_design()
    climate = SCENARIOS["cold_winter_day"]

    default_result = evaluate_candidate(design, climate, evaluator, weights=DEFAULT_WEIGHTS)
    heat_loss_focused = dict(DEFAULT_WEIGHTS)
    heat_loss_focused["heat_loss"] = 5.0
    focused_result = evaluate_candidate(design, climate, evaluator, weights=heat_loss_focused)

    assert focused_result["score"] != default_result["score"]


def test_material_cost_index_scales_with_thickness():
    thin = base_design()
    thin.wall_thickness = 0.10
    thick = base_design()
    thick.wall_thickness = 0.40

    assert material_cost_index(thick) > material_cost_index(thin)
