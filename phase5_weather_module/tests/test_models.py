from datetime import datetime, timezone
import pytest

from weather_module.models.location import Location
from weather_module.models.weather import WeatherObservation, QualityFlag, DataSource


def test_location_requires_name_or_coords():
    with pytest.raises(ValueError):
        Location()


def test_location_valid_coords():
    loc = Location(latitude=34.15, longitude=77.57)
    assert loc.has_coordinates()


def test_location_invalid_latitude():
    with pytest.raises(ValueError):
        Location(latitude=999, longitude=10)


def test_observation_to_dict():
    obs = WeatherObservation(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        latitude=10.0, longitude=20.0, temperature_c=25.0,
    )
    d = obs.to_dict()
    assert d["temperature_c"] == 25.0
    assert d["quality"] == QualityFlag.VALID.value
    assert d["data_source"] == DataSource.MEASURED.value
