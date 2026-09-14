"""
Scenario comparison: evaluate one design across multiple
ClimateConditions to check robustness rather than overfitting to a
single weather pattern.
"""

from optimizer.objectives.fitness import evaluate_candidate


def run_scenario_analysis(design, scenarios: dict, evaluator, constraints=None, weights=None):
    """scenarios: dict of scenario_name -> ClimateCondition"""
    per_scenario = {}
    for name, climate in scenarios.items():
        result = evaluate_candidate(design, climate, evaluator, constraints, weights)
        per_scenario[name] = {
            "score": result["score"],
            "comfort_percentage": result["comfort_percentage"],
            "total_heat_loss_kwh": result["total_heat_loss_kwh"],
            "total_solar_gain_kwh": result["total_solar_gain_kwh"],
            "heating_requirement_kwh": result["heating_requirement_kwh"],
            "avg_indoor_temp_c": result["avg_indoor_temp_c"],
        }

    scores = [v["score"] for v in per_scenario.values()]
    comforts = [v["comfort_percentage"] for v in per_scenario.values()]
    heat_losses = [v["total_heat_loss_kwh"] for v in per_scenario.values()]

    return {
        "per_scenario": per_scenario,
        "overall_average_score": sum(scores) / len(scores),
        "worst_case_score": min(scores),
        "worst_case_comfort_percentage": min(comforts),
        "average_heat_loss_kwh": sum(heat_losses) / len(heat_losses),
    }
