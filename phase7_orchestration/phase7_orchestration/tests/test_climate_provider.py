from app.interfaces.climate import ClimateProvider


def test_mock_implements_interface(climate_provider):
    assert isinstance(climate_provider, ClimateProvider)


def test_get_climate_profile_cold_high_altitude(climate_provider):
    profile = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    assert profile.location == "Ladakh"
    assert profile.avg_outdoor_temp_c < 5
    assert profile.altitude_m == 3500.0
    assert profile.source == "mock"


def test_get_climate_profile_unknown_description_flags_missing(climate_provider):
    profile = climate_provider.get_climate_profile("Nowhere", "totally unknown climate xyz")
    assert "climate_zone_lookup" in profile.missing_fields


def test_get_scenarios_returns_five_named_scenarios(climate_provider):
    base = climate_provider.get_climate_profile("Ladakh", "cold high-altitude")
    scenarios = climate_provider.get_scenarios(base)
    assert len(scenarios) == 5
    names = {s.name for s in scenarios}
    assert "Cold + low solar radiation" in names
    assert "Clear winter day" in names
