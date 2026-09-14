from app.services.what_if import apply_what_if
from app.models.design import ShelterDesign, WallMaterial, RoofMaterial, FloorMaterial
from app.models.request import ComfortRange


def _design() -> ShelterDesign:
    return ShelterDesign(
        design_id="whatif-test",
        length_m=6.0,
        width_m=4.0,
        height_m=2.7,
        orientation_deg=90.0,
        wall_material=WallMaterial.STONE_INSULATED,
        roof_material=RoofMaterial.INSULATED_METAL,
        floor_material=FloorMaterial.INSULATED_CONCRETE,
        insulation_thickness_m=0.1,
        opening_area_m2=3.0,
    )


def test_increase_insulation_reduces_heat_loss(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    result = apply_what_if(
        _design(), "insulation_thickness_m", 0.3, climate, comfort, 24, thermal_simulator
    )

    assert result.heat_loss_change_kwh < 0


def test_increase_window_area_increases_solar_gain(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    result = apply_what_if(
        _design(), "window_area_m2", 8.0, climate, comfort, 24, thermal_simulator
    )

    assert result.solar_gain_change_kwh > 0


def test_orientation_change_affects_solar_gain(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    result = apply_what_if(
        _design(), "orientation_deg", 180.0, climate, comfort, 24, thermal_simulator
    )

    assert result.solar_gain_change_kwh > 0  # moving from east (90) to south (180)


def test_wall_material_change_reported(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    result = apply_what_if(
        _design(), "wall_material", "timber_insulated", climate, comfort, 24, thermal_simulator
    )

    assert result.original_value == "stone_insulated"
    assert result.new_value == "timber_insulated"
    assert result.heat_loss_change_kwh < 0
