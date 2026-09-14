import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["mock_mode"] is True


def test_demo_endpoint():
    resp = client.get("/api/demo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["location"] == "Ladakh"
    assert "recommended_design" in data


def test_analyze_endpoint_valid_request():
    payload = {
        "location": "Ladakh",
        "climate_description": "cold high-altitude",
        "comfort_range": {"min_c": 18, "max_c": 26},
        "simulation_duration_hours": 24,
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_design"]["design_id"]
    assert "confidence" in data
    assert "robustness" in data


def test_analyze_endpoint_rejects_invalid_comfort_range():
    payload = {
        "location": "Ladakh",
        "climate_description": "cold high-altitude",
        "comfort_range": {"min_c": 26, "max_c": 18},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 422


def test_what_if_endpoint():
    payload = {
        "location": "Ladakh",
        "climate_description": "cold high-altitude",
        "comfort_range": {"min_c": 18, "max_c": 26},
        "parameter": "insulation_thickness_m",
        "new_value": 0.3,
    }
    resp = client.post("/api/what-if", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["parameter"] == "insulation_thickness_m"
    assert "narrative" in data


def test_compare_endpoint_defaults_to_first_three_designs():
    payload = {
        "location": "Ladakh",
        "climate_description": "cold high-altitude",
        "comfort_range": {"min_c": 18, "max_c": 26},
    }
    resp = client.post("/api/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["compared"]) == 3


def test_compare_endpoint_unknown_design_id_returns_404():
    payload = {
        "location": "Ladakh",
        "climate_description": "cold high-altitude",
        "comfort_range": {"min_c": 18, "max_c": 26},
        "design_ids": ["does-not-exist"],
    }
    resp = client.post("/api/compare", json=payload)
    assert resp.status_code == 404
