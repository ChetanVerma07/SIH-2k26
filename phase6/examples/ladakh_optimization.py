"""
End-to-end demo: optimize a passive shelter design for a cold,
high-altitude climate representative of Ladakh.

Run with:
    python examples/ladakh_optimization.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from optimizer.models.climate import LADAKH_WINTER, SCENARIOS
from optimizer.thermal.simplified_model import FastThermalEvaluator
from optimizer.algorithms.genetic import run_genetic_algorithm
from optimizer.algorithms.differential_evolution import run_differential_evolution
from optimizer.analysis.sensitivity import run_sensitivity_analysis
from optimizer.analysis.scenarios import run_scenario_analysis
from optimizer.explanation.generator import generate_full_explanation
from optimizer.objectives.fitness import DEFAULT_WEIGHTS


def main():
    climate = LADAKH_WINTER
    evaluator = FastThermalEvaluator()
    weights = DEFAULT_WEIGHTS

    print("=" * 60)
    print("PHASE 6 - AI-ASSISTED PASSIVE SHELTER OPTIMIZER")
    print(f"Climate: {climate.name} (avg {climate.outdoor_temp_avg} C)")
    print("=" * 60)

    print("\nRunning Genetic Algorithm ...")
    ga_result = run_genetic_algorithm(
        climate, evaluator, population_size=40, generations=25, seed=1,
    )
    print(f"GA best score: {ga_result['best_metrics']['score']:.3f}  "
          f"(comfort {ga_result['best_metrics']['comfort_percentage']:.1f}%)")

    print("\nRunning Differential Evolution ...")
    de_result = run_differential_evolution(
        climate, evaluator, population_size=40, generations=25, seed=1,
    )
    print(f"DE best score: {de_result['best_metrics']['score']:.3f}  "
          f"(comfort {de_result['best_metrics']['comfort_percentage']:.1f}%)")

    if ga_result["best_metrics"]["score"] >= de_result["best_metrics"]["score"]:
        winner_label, winner = "Genetic Algorithm", ga_result
    else:
        winner_label, winner = "Differential Evolution", de_result

    print(f"\nOverall winner: {winner_label}")

    best_design = winner["best_design"]
    best_metrics = winner["best_metrics"]

    print("\nRunning sensitivity analysis on the recommended design ...")
    sensitivity_result = run_sensitivity_analysis(best_design, climate, evaluator, weights=weights)

    print("Evaluating recommended design across multiple climate scenarios ...")
    scenario_result = run_scenario_analysis(best_design, SCENARIOS, evaluator, weights=weights)

    explanation = generate_full_explanation(winner["top_designs"], sensitivity_result)

    d = best_design.summary_dict()
    print("\nOPTIMIZATION COMPLETE\n")
    print("Recommended Design")
    print("-" * 18)
    print(f"Length: {d['length_m']} m")
    print(f"Width: {d['width_m']} m")
    print(f"Height: {d['height_m']} m")
    print()
    print(f"Wall: {d['wall_material']} ({d['wall_thickness_m']*100:.1f} cm)")
    print(f"Roof: {d['roof_material']} ({d['roof_thickness_m']*100:.1f} cm)")
    print(f"Floor: {d['floor_material']} ({d['floor_thickness_m']*100:.1f} cm)")
    print(f"Insulation: {d['insulation_material']} ({d['insulation_thickness_m']*100:.1f} cm)")
    print()
    print(f"Opening Area: {d['opening_area_m2']} m2")
    print(f"Orientation: {d['orientation_deg']} deg")

    print("\nPerformance")
    print("-" * 11)
    print(f"Comfort: {best_metrics['comfort_percentage']:.1f} %")
    print(f"Heat Loss: {best_metrics['total_heat_loss_kwh']:.2f} kWh/day")
    print(f"Solar Gain: {best_metrics['total_solar_gain_kwh']:.2f} kWh/day")
    print(f"Heating Requirement: {best_metrics['heating_requirement_kwh']:.2f} kWh/day")
    print(f"Score: {best_metrics['score']:.3f}")

    print("\nSCENARIO ROBUSTNESS")
    print("-" * 20)
    for name, res in scenario_result["per_scenario"].items():
        print(f"  {name:18s} comfort={res['comfort_percentage']:5.1f}%  "
              f"heat_loss={res['total_heat_loss_kwh']:6.2f} kWh  score={res['score']:.3f}")
    print(f"Worst-case comfort: {scenario_result['worst_case_comfort_percentage']:.1f}%")
    print(f"Average heat loss across scenarios: {scenario_result['average_heat_loss_kwh']:.2f} kWh/day")

    print("\nTOP PARAMETER SENSITIVITY")
    print("-" * 26)
    for item in sensitivity_result["ranked_parameters"][:5]:
        print(f"  {item['rank']}. {item['parameter']:22s} impact={item['impact_level']:6s} "
              f"(~{item['percent_impact']:.1f}%)")

    print("\nWHY THIS DESIGN?")
    print("-" * 16)
    print(explanation["selection_reasoning"])
    print(explanation["material_reasoning"])
    print(explanation["insulation_reasoning"])
    print(explanation["orientation_reasoning"])
    print(explanation["opening_area_reasoning"])

    return {
        "ga_result": ga_result,
        "de_result": de_result,
        "winner_label": winner_label,
        "sensitivity_result": sensitivity_result,
        "scenario_result": scenario_result,
        "explanation": explanation,
    }


if __name__ == "__main__":
    main()
