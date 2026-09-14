"""End-to-end demo: passive shelter design analysis for Ladakh.

Run with:
    python examples/ladakh_demo.py
(from the phase7_orchestration/ directory, with dependencies installed)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.mocks.ansys import MockANSYSValidator
from app.mocks.climate import MockClimateProvider
from app.mocks.optimizer import MockDesignOptimizer
from app.mocks.thermal import MockThermalSimulator
from app.models.request import ComfortRange, ShelterDesignRequest
from app.reporting.report_generator import write_report_files
from app.services.orchestrator import Orchestrator


def main() -> None:
    request = ShelterDesignRequest(
        location="Ladakh",
        climate_description="cold high-altitude",
        comfort_range=ComfortRange(min_c=18, max_c=26),
        objectives=[
            "maximize thermal comfort",
            "minimize heat loss",
            "minimize external energy requirement",
        ],
        simulation_duration_hours=24,
        run_ansys_validation=True,
    )

    orchestrator = Orchestrator(
        climate_provider=MockClimateProvider(),
        thermal_simulator=MockThermalSimulator(),
        optimizer=MockDesignOptimizer(),
        ansys_validator=MockANSYSValidator(),
    )

    report = orchestrator.run_design_analysis(request)

    d = report.recommended_design
    r = report.results
    c = report.comparison
    rb = report.robustness

    print("=" * 60)
    print("PASSIVE SHELTER DESIGN ANALYSIS")
    print("=" * 60)
    print()
    print(f"Location:\n{report.location}")
    print()
    print("Recommended Design:")
    print("-------------------")
    print(f"Dimensions:    {d.dimensions_str}")
    print(f"Orientation:   {d.orientation_deg:.0f} deg")
    print(f"Wall:          {d.wall_material.value}")
    print(f"Roof:          {d.roof_material.value}")
    print(f"Floor:         {d.floor_material.value}")
    print(f"Insulation:    {d.insulation_thickness_m:.2f} m")
    print(f"Opening Area:  {d.opening_area_m2:.1f} m^2")
    print()
    print("Performance:")
    print("------------")
    print(f"Comfort:             {r.comfort_percentage:.1f}%")
    print(f"Heat Loss:           {r.total_heat_loss_kwh:.1f} kWh")
    print(f"Solar Gain:          {r.solar_gain_kwh:.1f} kWh")
    print(f"Heating Requirement: {r.estimated_heating_requirement_kwh:.1f} kWh")
    print(f"Overall Score:       {r.overall_score:.1f}")
    print()
    print("Baseline Comparison:")
    print("--------------------")
    print(f"Heat Loss Improvement: {c.heat_loss_improvement_percent:.1f}%")
    print(f"Comfort Improvement:   {c.comfort_improvement_points:.1f} percentage points")
    print()
    print("Robustness:")
    print("-----------")
    print(f"Scenarios Passed: {rb.scenarios_passed}/{rb.scenarios_evaluated}")
    print(f"Robustness Score: {rb.robustness_score:.1f}/100")
    print()
    print("Recommendation:")
    print("---------------")
    print(report.recommendation.headline)
    print()

    json_path, md_path = write_report_files(
        report, output_dir=str(Path(__file__).resolve().parent / "output"), basename="ladakh_report"
    )
    print(f"Full JSON report written to: {json_path}")
    print(f"Full Markdown report written to: {md_path}")


if __name__ == "__main__":
    main()
