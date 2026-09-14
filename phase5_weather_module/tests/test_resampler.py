from datetime import datetime, timedelta, timezone
from weather_module.models.weather import WeatherObservation
from weather_module.processing.resampler import resample


def make_obs(t, temp):
    return WeatherObservation(timestamp=t, latitude=10.0, longitude=20.0, temperature_c=temp)


def test_resample_interpolates_between_points():
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=1)
    obs = [make_obs(t0, 10.0), make_obs(t1, 20.0)]
    result = resample(obs, interval_minutes=30)
    assert len(result) == 3
    assert result[1].temperature_c == 15.0


def test_resample_single_observation_passthrough():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    obs = [make_obs(t0, 10.0)]
    result = resample(obs, interval_minutes=30)
    assert result == obs
