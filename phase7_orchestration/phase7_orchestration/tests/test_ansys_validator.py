from app.interfaces.ansys import ANSYSValidator
from app.models.design import ShelterDesign, WallMaterial, RoofMaterial, FloorMaterial


def _design() -> ShelterDesign:
    return ShelterDesign(
        design_id="ansys-test",
        length_m=6.0,
        width_m=4.0,
        height_m=2.7,
        orientation_deg=180.0,
        wall_material=WallMaterial.STONE_INSULATED,
        roof_material=RoofMaterial.INSULATED_METAL,
        floor_material=FloorMaterial.INSULATED_CONCRETE,
        insulation_thickness_m=0.1,
        opening_area_m2=3.0,
    )


def test_mock_implements_interface(ansys_validator):
    assert isinstance(ansys_validator, ANSYSValidator)


def test_validate_and_retrieve_results_are_clearly_mock(ansys_validator):
    design = _design()
    job_id = ansys_validator.validate_design(design)
    result = ansys_validator.get_validation_results(job_id, design)

    assert result.is_mock is True
    assert "MOCK" in result.notes.upper()
    assert result.design_id == design.design_id


def test_higher_opening_ratio_flagged_higher_risk(ansys_validator):
    low_risk_design = _design()
    high_risk_design = _design()
    high_risk_design = high_risk_design.model_copy(update={"opening_area_m2": 10.0})

    low = ansys_validator.get_validation_results(
        ansys_validator.validate_design(low_risk_design), low_risk_design
    )
    high = ansys_validator.get_validation_results(
        ansys_validator.validate_design(high_risk_design), high_risk_design
    )

    risk_order = {"low": 0, "medium": 1, "high": 2}
    assert risk_order[high.predicted_thermal_bridging_risk] >= risk_order[low.predicted_thermal_bridging_risk]
