import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from optimizer.models.climate import SCENARIOS
from optimizer.thermal.simplified_model import FastThermalEvaluator
from optimizer.algorithms.genetic import run_genetic_algorithm
from optimizer.analysis.sensitivity import run_sensitivity_analysis
from optimizer.analysis.scenarios import run_scenario_analysis
from optimizer.explanation.generator import generate_full_explanation
from optimizer.surrogate.model import ThermalSurrogate

CLIMATE = SCENARIOS["cold_winter_day"]


def _quick_ga_result():
    evaluator = FastThermalEvaluator()
    return run_genetic_algorithm(CLIMATE, evaluator, population_size=16, generations=8, seed=11)


def test_optimization_output_structure():
    result = _quick_ga_result()
    metrics = result["best_metrics"]
    for key in ("avg_indoor_temp_c", "min_indoor_temp_c", "max_indoor_temp_c",
                "comfort_percentage", "total_heat_loss_kwh", "total_solar_gain_kwh",
                "heating_requirement_kwh", "score"):
        assert key in metrics


def test_sensitivity_analysis_ranks_parameters():
    result = _quick_ga_result()
    evaluator = FastThermalEvaluator()
    sens = run_sensitivity_analysis(result["best_design"], CLIMATE, evaluator)
    assert "ranked_parameters" in sens
    ranks = [item["rank"] for item in sens["ranked_parameters"]]
    assert ranks == sorted(ranks)
    impacts = [item["percent_impact"] for item in sens["ranked_parameters"]]
    assert impacts == sorted(impacts, reverse=True)


def test_scenario_analysis_covers_all_scenarios():
    result = _quick_ga_result()
    evaluator = FastThermalEvaluator()
    scen = run_scenario_analysis(result["best_design"], SCENARIOS, evaluator)
    assert set(scen["per_scenario"].keys()) == set(SCENARIOS.keys())
    assert "worst_case_comfort_percentage" in scen
    assert scen["worst_case_comfort_percentage"] <= max(
        v["comfort_percentage"] for v in scen["per_scenario"].values()
    )


def test_explanation_generation_uses_real_metrics():
    result = _quick_ga_result()
    evaluator = FastThermalEvaluator()
    sens = run_sensitivity_analysis(result["best_design"], CLIMATE, evaluator)
    explanation = generate_full_explanation(result["top_designs"], sens)
    assert "selection_reasoning" in explanation
    assert isinstance(explanation["selection_reasoning"], str) and len(explanation["selection_reasoning"]) > 0
    assert result["best_design"].wall_material in explanation["material_reasoning"]


def test_surrogate_model_trains_and_predicts():
    result = run_genetic_algorithm(
        CLIMATE, FastThermalEvaluator(), population_size=20, generations=6, seed=2,
    )
    evaluations = result["all_evaluations"]
    assert len(evaluations) >= 40
    train, test = evaluations[:80], evaluations[80:100]
    surrogate = ThermalSurrogate().fit(train)
    genome, _ = test[0]
    prediction = surrogate.predict(genome)
    assert "predicted_comfort_percentage" in prediction
    assert "predicted_total_heat_loss_kwh" in prediction

    report = surrogate.evaluate_against_ground_truth(test)
    assert report["n_samples"] == len(test)
    assert report["mean_absolute_error_comfort_pct"] is not None
