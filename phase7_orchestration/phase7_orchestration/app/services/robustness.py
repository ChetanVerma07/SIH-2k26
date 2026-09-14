"""Multi-scenario robustness evaluation."""
from app.interfaces.thermal import ThermalSimulator
from app.models.climate import ClimateProfile, ScenarioDefinition
from app.models.design import ShelterDesign
from app.models.request import ComfortRange
from app.models.results import ScenarioResult, RobustnessSummary

# A scenario "passes" if the design maintains at least this much of the
# simulated period within the comfort band. Documented, not arbitrary.
PASS_THRESHOLD_COMFORT_PERCENT = 60.0


def evaluate_robustness(
    design: ShelterDesign,
    climate: ClimateProfile,
    scenarios: list[ScenarioDefinition],
    thermal_simulator: ThermalSimulator,
    comfort_range: ComfortRange,
    duration_hours: int,
) -> RobustnessSummary:
    results: list[ScenarioResult] = []

    for scenario in scenarios:
        perf = thermal_simulator.simulate(
            design=design,
            climate=climate,
            comfort_range=comfort_range,
            duration_hours=duration_hours,
            outdoor_temp_offset_c=scenario.outdoor_temp_offset_c,
            solar_radiation_factor=scenario.solar_radiation_factor,
        )
        results.append(
            ScenarioResult(
                scenario_name=scenario.name,
                description=scenario.description,
                min_indoor_temp_c=perf.min_indoor_temp_c,
                max_indoor_temp_c=perf.max_indoor_temp_c,
                avg_indoor_temp_c=perf.avg_indoor_temp_c,
                comfort_percentage=perf.comfort_percentage,
                heat_loss_kwh=perf.total_heat_loss_kwh,
                solar_gain_kwh=perf.solar_gain_kwh,
            )
        )

    comfort_values = [r.comfort_percentage for r in results]
    scenarios_passed = sum(1 for c in comfort_values if c >= PASS_THRESHOLD_COMFORT_PERCENT)
    worst_case = min(comfort_values) if comfort_values else 0.0
    average = sum(comfort_values) / len(comfort_values) if comfort_values else 0.0

    # Robustness score rewards both a high average AND a high worst-case
    # (so a design cannot score well by excelling in one scenario only).
    robustness_score = round(0.5 * average + 0.5 * worst_case, 2)

    return RobustnessSummary(
        scenarios=results,
        scenarios_evaluated=len(results),
        scenarios_passed=scenarios_passed,
        worst_case_comfort_percentage=round(worst_case, 2),
        average_comfort_percentage=round(average, 2),
        robustness_score=robustness_score,
    )
