from weather_module.models.location import Location
from weather_module.providers.mock import MockWeatherProvider
from weather_module.services.weather_service import WeatherService


def test_generate_simulation_profile_structure():
    service = WeatherService(provider=MockWeatherProvider())
    loc = Location(name="ladakh")
    profile = service.generate_simulation_profile(loc, duration_hours=24, interval_minutes=60)
    assert profile["duration_hours"] == 24
    assert profile["interval_minutes"] == 60
    assert len(profile["observations"]) == 24
    assert "quality_summary" in profile


def test_demo_ladakh_profile():
    service = WeatherService(provider=MockWeatherProvider())
    profile = service.demo_ladakh_profile()
    assert profile["data_label"] == "DEMO / MOCK DATA"
    assert len(profile["observations"]) == 24


def test_custom_interval_resampling():
    service = WeatherService(provider=MockWeatherProvider())
    loc = Location(name="delhi")
    profile = service.generate_simulation_profile(loc, duration_hours=6, interval_minutes=15)
    assert profile["interval_minutes"] == 15
    assert len(profile["observations"]) == 24  # 6h * 60 / 15
