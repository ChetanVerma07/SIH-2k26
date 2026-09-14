import json
import os
import tempfile
from datetime import datetime, timezone

from weather_module.models.weather import WeatherObservation
from weather_module.export.exporter import export_csv, export_json


def make_obs():
    return [
        WeatherObservation(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            latitude=34.0, longitude=77.0, temperature_c=5.0,
        )
    ]


def test_export_csv():
    obs = make_obs()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.csv")
        export_csv(obs, path)
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "temperature_c" in content


def test_export_json():
    obs = make_obs()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "out.json")
        export_json(obs, path, meta={"source": "test"})
        with open(path) as f:
            data = json.load(f)
        assert data["count"] == 1
        assert data["meta"]["source"] == "test"
