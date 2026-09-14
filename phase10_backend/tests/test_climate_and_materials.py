def test_list_climate_presets(client):
    resp = client.get("/api/v1/climate/presets")
    assert resp.status_code == 200
    locations = [c["location"] for c in resp.json()]
    assert "Ladakh" in locations
    assert "Hot and Dry" in locations
    assert "Warm and Humid" in locations
    assert "Composite" in locations


def test_get_climate_by_location(client):
    resp = client.get("/api/v1/climate/Ladakh")
    assert resp.status_code == 200
    body = resp.json()
    assert body["location"] == "Ladakh"
    assert body["is_preset"] is True


def test_get_climate_unknown_location(client):
    resp = client.get("/api/v1/climate/Atlantis")
    assert resp.status_code == 404


def test_create_custom_climate(client):
    resp = client.post(
        "/api/v1/climate",
        json={
            "location": "Custom Site A",
            "temperature": 20.0,
            "humidity": 40.0,
            "pressure": 1010.0,
            "solar_radiation": 600.0,
            "wind_speed": 8.0,
            "wind_direction": 90.0,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["is_preset"] is False


def test_create_custom_climate_invalid(client):
    resp = client.post(
        "/api/v1/climate",
        json={
            "temperature": 20.0,
            "humidity": 400.0,  # invalid, > 100
            "pressure": 1010.0,
            "solar_radiation": 600.0,
            "wind_speed": 8.0,
            "wind_direction": 90.0,
        },
    )
    assert resp.status_code == 422


def test_list_materials(client):
    resp = client.get("/api/v1/materials")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_list_materials_filtered_by_category(client):
    resp = client.get("/api/v1/materials?category=insulation")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) > 0
    assert all(m["category"] == "insulation" for m in body)


def test_get_material(client):
    all_materials = client.get("/api/v1/materials").json()
    material_id = all_materials[0]["id"]
    resp = client.get(f"/api/v1/materials/{material_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == material_id


def test_get_material_invalid_id(client):
    resp = client.get("/api/v1/materials/mat_nope")
    assert resp.status_code == 404


def test_create_custom_material(client):
    resp = client.post(
        "/api/v1/materials",
        json={
            "name": "Test Foam",
            "category": "insulation",
            "thermal_conductivity": 0.03,
            "density": 30,
            "specific_heat": 1400,
            "emissivity": 0.9,
            "solar_absorptivity": 0.5,
            "cost_factor": 4.0,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["is_custom"] is True


def test_create_custom_material_invalid_physical_value(client):
    resp = client.post(
        "/api/v1/materials",
        json={
            "name": "Bad Material",
            "category": "insulation",
            "thermal_conductivity": -1,  # invalid, must be > 0
            "density": 30,
            "specific_heat": 1400,
            "emissivity": 0.9,
            "solar_absorptivity": 0.5,
            "cost_factor": 4.0,
        },
    )
    assert resp.status_code == 422
