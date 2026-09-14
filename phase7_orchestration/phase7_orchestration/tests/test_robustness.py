from app.services.robustness import evaluate_robustness, PASS_THRESHOLD_COMFORT_PERCENT
from app.models.design import ShelterDesign, WallMaterial, RoofMaterial, FloorMaterial
from app.models.request import ComfortRange


def _design() -> ShelterDesign:
    return ShelterDesign(
        design_id="robustness-test",
        length_m=6.0,
        width_m=4.0,
        height_m=2.7,
        orientation_deg=180.0,
        wall_material=WallMaterial.STONE_INSULATED,
        roof_material=RoofMaterial.INSULATED_METAL,
        floor_material=FloorMaterial.INSULATED_CONCRETE,
        insulation_thickness_m=0.15,
        opening_area_m2=3.0,
    )


def test_evaluates_all_scenarios(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    scenarios = climate_provider.get_scenarios(climate)
    comfort = ComfortRange(min_c=18, max_c=26)

    summary = evaluate_robustness(_design(), climate, scenarios, thermal_simulator, comfort, 24)

    assert summary.scenarios_evaluated == len(scenarios)
    assert len(summary.scenarios) == len(scenarios)


def test_scenarios_passed_matches_threshold(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    scenarios = climate_provider.get_scenarios(climate)
    comfort = ComfortRange(min_c=18, max_c=26)

    summary = evaluate_robustness(_design(), climate, scenarios, thermal_simulator, comfort, 24)

    manual_passed = sum(
        1 for s in summary.scenarios if s.comfort_percentage >= PASS_THRESHOLD_COMFORT_PERCENT
    )
    assert summary.scenarios_passed == manual_passed


def test_robustness_score_considers_worst_case_not_just_average(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    scenarios = climate_provider.get_scenarios(climate)
    comfort = ComfortRange(min_c=18, max_c=26)

    summary = evaluate_robustness(_design(), climate, scenarios, thermal_simulator, comfort, 24)

    expected_score = round(
        0.5 * summary.average_comfort_percentage + 0.5 * summary.worst_case_comfort_percentage, 2
    )
    assert summary.robustness_score == expected_score
    assert summary.worst_case_comfort_percentage <= summary.average_comfort_percentage
