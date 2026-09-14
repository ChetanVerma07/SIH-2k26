from app.models.climate import ConstantClimate
from app.models.material import assembly_r_value, assembly_u_value
from app.models.simulation import SimulationSettings
from app.thermal.conduction import conductive_heat_flow
from app.thermal.heat_balance import compute_heat_balance, effective_thermal_mass
from app.thermal.simulator import build_climate_series, run_simulation


def test_r_and_u_value_relationship(wall_material):
    r = assembly_r_value(wall_material)
    u = assembly_u_value(wall_material)
    assert r == wall_material.thickness / wall_material.thermal_conductivity
    assert abs(u - 1.0 / r) < 1e-9


def test_conductive_heat_flow_formula():
    # Q = U * A * dT
    assert conductive_heat_flow(u_value=2.0, area=10.0, delta_t=5.0) == 100.0
    # Reversed temperature gradient flips the sign (heat flows inward).
    assert conductive_heat_flow(u_value=2.0, area=10.0, delta_t=-5.0) == -100.0


def test_effective_thermal_mass_is_positive(basic_shelter):
    c_total = effective_thermal_mass(basic_shelter)
    assert c_total > 0


def test_heat_balance_no_sun_no_gradient_is_zero_net(basic_shelter):
    balance = compute_heat_balance(
        shelter=basic_shelter,
        indoor_temperature=10.0,
        ambient_temperature=10.0,
        ground_temperature=10.0,
        solar_radiation=0.0,
    )
    assert balance.solar_gain == 0.0
    assert abs(balance.total_heat_loss) < 1e-9
    assert abs(balance.net_heat_flow) < 1e-9


def test_build_climate_series_constant(basic_settings):
    climate = ConstantClimate(ambient_temperature=-5.0, solar_radiation=250.0)
    settings = SimulationSettings(**basic_settings)
    df = build_climate_series(climate, settings)
    assert (df["ambient_temperature"] == -5.0).all()
    assert (df["solar_radiation"] == 250.0).all()
    assert (df["ground_temperature"] == -5.0).all()  # defaults to ambient


def test_run_simulation_produces_expected_number_of_steps(basic_shelter, basic_settings):
    climate = ConstantClimate(ambient_temperature=-5.0, solar_radiation=100.0)
    settings = SimulationSettings(**basic_settings)
    results = run_simulation(basic_shelter, climate, settings)
    assert len(results) == settings.num_steps
    assert results[0].indoor_temperature == settings.initial_indoor_temperature
