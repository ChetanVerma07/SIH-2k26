from datetime import date, timedelta
from weather_module.models.location import Location
from weather_module.providers.mock import MockWeatherProvider


def test_mock_current_weather():
    provider = MockWeatherProvider()
    loc = Location(name="ladakh")
    obs = provider.get_current_weather(loc)
    assert obs.temperature_c is not None
    assert obs.data_source.value == "MOCK"


def test_mock_forecast_length():
    provider = MockWeatherProvider()
    loc = Location(latitude=34.15, longitude=77.57)
    series = provider.get_forecast(loc, hours=24, interval_minutes=60)
    assert len(series) == 24


def test_mock_historical_deterministic():
    provider = MockWeatherProvider()
    loc = Location(latitude=34.15, longitude=77.57)
    d = date(2026, 1, 1)
    series1 = provider.get_historical_weather(loc, start=d)
    series2 = provider.get_historical_weather(loc, start=d)
    assert [o.temperature_c for o in series1] == [o.temperature_c for o in series2]


def test_mock_historical_range():
    provider = MockWeatherProvider()
    loc = Location(latitude=34.15, longitude=77.57)
    start = date(2026, 1, 1)
    end = start + timedelta(days=1)
    series = provider.get_historical_weather(loc, start=start, end=end)
    assert len(series) == 48


def test_mock_solar_radiation_estimated_label():
    provider = MockWeatherProvider()
    loc = Location(name="ladakh")
    obs = provider.get_current_weather(loc)
    assert obs.solar_radiation_source.value == "ESTIMATED"


def test_ladakh_demo_preset():
    provider = MockWeatherProvider()
    obs_list, location = provider.get_demo_profile_24h(preset="ladakh")
    assert len(obs_list) == 24
    assert location.name == "Ladakh"
