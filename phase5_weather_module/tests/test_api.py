from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_current_weather_named_location():
    r = client.get("/api/weather/current", params={"location": "ladakh"})
    assert r.status_code == 200
    body = r.json()
    assert body["temperature_c"] is not None


def test_current_weather_coords():
    r = client.get("/api/weather/current", params={"lat": 34.15, "lon": 77.57})
    assert r.status_code == 200


def test_forecast():
    r = client.get("/api/weather/forecast", params={"location": "delhi", "hours": 12, "interval_minutes": 60})
    assert r.status_code == 200
    assert len(r.json()) == 12


def test_historical():
    r = client.get(
        "/api/weather/historical",
        params={"location": "delhi", "start": "2026-01-01", "end": "2026-01-01"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 24


def test_profile_post():
    r = client.post(
        "/api/weather/profile",
        json={"location_name": "ladakh", "duration_hours": 24, "interval_minutes": 60},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["observations"]) == 24


def test_demo_endpoint():
    r = client.get("/api/weather/demo")
    assert r.status_code == 200
    body = r.json()
    assert len(body["observations"]) == 24


def test_missing_location_returns_422():
    r = client.get("/api/weather/current")
    assert r.status_code == 422
