from app.interfaces.thermal import ThermalSimulator
from app.models.design import ShelterDesign, WallMaterial, RoofMaterial, FloorMaterial
from app.models.request import ComfortRange


def _design(**overrides) -> ShelterDesign:
    base = dict(
        design_id="test-design",
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
    base.update(overrides)
    return ShelterDesign(**base)


def test_mock_implements_interface(thermal_simulator):
    assert isinstance(thermal_simulator, ThermalSimulator)


def test_more_insulation_reduces_heat_loss(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    low = thermal_simulator.simulate(_design(insulation_thickness_m=0.02), climate, comfort, 24)
    high = thermal_simulator.simulate(_design(insulation_thickness_m=0.3), climate, comfort, 24)

    assert high.total_heat_loss_kwh < low.total_heat_loss_kwh
    assert high.estimated_heating_requirement_kwh < low.estimated_heating_requirement_kwh


def test_larger_openings_increase_heat_loss_and_solar_gain(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    small = thermal_simulator.simulate(_design(opening_area_m2=1.5), climate, comfort, 24)
    large = thermal_simulator.simulate(_design(opening_area_m2=6.0), climate, comfort, 24)

    assert large.total_heat_loss_kwh > small.total_heat_loss_kwh
    assert large.solar_gain_kwh > small.solar_gain_kwh


def test_lower_conductivity_wall_material_reduces_heat_loss(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    worse = thermal_simulator.simulate(
        _design(wall_material=WallMaterial.CONCRETE_BLOCK), climate, comfort, 24
    )
    better = thermal_simulator.simulate(
        _design(wall_material=WallMaterial.TIMBER_INSULATED), climate, comfort, 24
    )

    assert better.total_heat_loss_kwh < worse.total_heat_loss_kwh


def test_higher_solar_radiation_increases_solar_gain(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    low_solar = thermal_simulator.simulate(
        _design(), climate, comfort, 24, solar_radiation_factor=0.3
    )
    high_solar = thermal_simulator.simulate(
        _design(), climate, comfort, 24, solar_radiation_factor=1.5
    )

    assert high_solar.solar_gain_kwh > low_solar.solar_gain_kwh


def test_orientation_changes_solar_gain(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)

    south = thermal_simulator.simulate(_design(orientation_deg=180.0), climate, comfort, 24)
    north = thermal_simulator.simulate(_design(orientation_deg=0.0), climate, comfort, 24)

    assert south.solar_gain_kwh > north.solar_gain_kwh


def test_comfort_percentage_bounded(thermal_simulator, climate_provider):
    climate = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    comfort = ComfortRange(min_c=18, max_c=26)
    perf = thermal_simulator.simulate(_design(), climate, comfort, 24)
    assert 0.0 <= perf.comfort_percentage <= 100.0
