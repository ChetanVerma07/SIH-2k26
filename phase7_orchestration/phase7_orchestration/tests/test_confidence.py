from app.services.confidence import assess_confidence
from app.services.robustness import evaluate_robustness
from app.models.design import ShelterDesign, WallMaterial, RoofMaterial, FloorMaterial
from app.models.request import ComfortRange


def _design() -> ShelterDesign:
    return ShelterDesign(
        design_id="confidence-test",
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


def test_confidence_values_in_bounds(thermal_simulator, climate_provider, ansys_validator):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    scenarios = climate_provider.get_scenarios(climate)
    comfort = ComfortRange(min_c=18, max_c=26)
    design = _design()

    robustness = evaluate_robustness(design, climate, scenarios, thermal_simulator, comfort, 24)
    job_id = ansys_validator.validate_design(design)
    ansys_result = ansys_validator.get_validation_results(job_id, design)

    confidence = assess_confidence(climate, robustness, ansys_result)

    assert 0.0 <= confidence.data_confidence <= 100.0
    assert 0.0 <= confidence.simulation_confidence <= 100.0
    assert 0.0 <= confidence.recommendation_confidence <= 100.0
    assert confidence.explanation


def test_missing_climate_fields_lower_data_confidence(thermal_simulator, climate_provider):
    good_climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    poor_climate = climate_provider.get_climate_profile("Nowhere", "completely unrecognized zone")
    scenarios = climate_provider.get_scenarios(good_climate)
    comfort = ComfortRange(min_c=18, max_c=26)
    design = _design()

    robustness = evaluate_robustness(design, good_climate, scenarios, thermal_simulator, comfort, 24)

    good_confidence = assess_confidence(good_climate, robustness, None)
    poor_confidence = assess_confidence(poor_climate, robustness, None)

    assert poor_confidence.data_confidence < good_confidence.data_confidence


def test_ansys_validation_increases_simulation_confidence(thermal_simulator, climate_provider, ansys_validator):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    scenarios = climate_provider.get_scenarios(climate)
    comfort = ComfortRange(min_c=18, max_c=26)
    design = _design()

    robustness = evaluate_robustness(design, climate, scenarios, thermal_simulator, comfort, 24)
    job_id = ansys_validator.validate_design(design)
    ansys_result = ansys_validator.get_validation_results(job_id, design)

    without_ansys = assess_confidence(climate, robustness, None)
    with_ansys = assess_confidence(climate, robustness, ansys_result)

    assert with_ansys.simulation_confidence > without_ansys.simulation_confidence
