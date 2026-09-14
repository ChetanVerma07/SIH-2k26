from datetime import datetime, timedelta, timezone
from weather_module.models.weather import WeatherObservation, QualityFlag
from weather_module.processing.validator import (
    validate_single, validate_series, detect_duplicate_timestamps, detect_sudden_jumps,
)


def make_obs(**kwargs):
    defaults = dict(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        latitude=34.0, longitude=77.0,
        temperature_c=10.0, humidity_pct=50.0, pressure_hpa=1000.0,
        solar_radiation_wm2=500.0,
    )
    defaults.update(kwargs)
    return WeatherObservation(**defaults)


def test_impossible_temperature_flagged():
    obs = make_obs(temperature_c=500.0)
    validate_single(obs)
    assert obs.quality == QualityFlag.SUSPECT


def test_impossible_humidity_corrected():
    obs = make_obs(humidity_pct=150.0)
    validate_single(obs)
    assert obs.humidity_pct == 100.0
    assert obs.quality == QualityFlag.CORRECTED


def test_impossible_pressure_flagged():
    obs = make_obs(pressure_hpa=5000.0)
    validate_single(obs)
    assert obs.quality == QualityFlag.SUSPECT


def test_negative_solar_radiation_corrected():
    obs = make_obs(solar_radiation_wm2=-50.0)
    validate_single(obs)
    assert obs.solar_radiation_wm2 == 0.0
    assert obs.quality == QualityFlag.CORRECTED


def test_missing_value_flagged():
    obs = make_obs(temperature_c=None)
    validate_single(obs)
    assert obs.quality == QualityFlag.MISSING


def test_invalid_coordinates_flagged():
    obs = make_obs(latitude=999.0)
    validate_single(obs)
    assert obs.quality == QualityFlag.SUSPECT


def test_duplicate_timestamp_detection():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    o1 = make_obs(timestamp=t)
    o2 = make_obs(timestamp=t)
    detect_duplicate_timestamps([o1, o2])
    assert o1.quality == QualityFlag.SUSPECT
    assert o2.quality == QualityFlag.SUSPECT


def test_sudden_jump_detection():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    o1 = make_obs(timestamp=t0, temperature_c=10.0)
    o2 = make_obs(timestamp=t0 + timedelta(hours=1), temperature_c=40.0)
    detect_sudden_jumps([o1, o2])
    assert o2.quality == QualityFlag.SUSPECT


def test_validate_series_stats():
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    obs = [make_obs(timestamp=t0 + timedelta(hours=i)) for i in range(5)]
    stats = validate_series(obs)
    assert stats.total == 5
    assert stats.valid == 5
