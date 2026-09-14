def _get_climate_id(client, location="Ladakh"):
    presets = client.get("/api/v1/climate/presets").json()
    return next(c["id"] for c in presets if c["location"] == location)


def test_create_simulation(client, sample_project, sample_design):
    climate_id = _get_climate_id(client)
    resp = client.post(
        "/api/v1/simulations",
        json={
            "project_id": sample_project["id"],
            "design_id": sample_design["id"],
            "climate_id": climate_id,
            "duration": 24,
            "timestep": 1,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "CREATED"
    assert body["id"].startswith("sim_")


def test_create_simulation_invalid_project(client, sample_design):
    climate_id = _get_climate_id(client)
    resp = client.post(
        "/api/v1/simulations",
        json={
            "project_id": "proj_nope",
            "design_id": sample_design["id"],
            "climate_id": climate_id,
        },
    )
    assert resp.status_code == 404


def test_run_simulation_and_get_results(client, sample_project, sample_design):
    climate_id = _get_climate_id(client)
    create_resp = client.post(
        "/api/v1/simulations",
        json={
            "project_id": sample_project["id"],
            "design_id": sample_design["id"],
            "climate_id": climate_id,
        },
    )
    simulation_id = create_resp.json()["id"]

    run_resp = client.post(f"/api/v1/simulations/{simulation_id}/run")
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["status"] == "COMPLETED"
    assert body["progress"] == 1.0
    assert body["backend"] == "MOCK"

    status_resp = client.get(f"/api/v1/simulations/{simulation_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "COMPLETED"

    results_resp = client.get(f"/api/v1/simulations/{simulation_id}/results")
    assert results_resp.status_code == 200
    results = results_resp.json()
    for key in (
        "indoor_temperature",
        "outdoor_temperature",
        "heat_loss",
        "solar_gain",
        "average_temperature",
        "minimum_temperature",
        "maximum_temperature",
        "comfort_percentage",
        "total_heat_loss",
        "total_solar_gain",
    ):
        assert key in results


def test_get_results_before_run_fails(client, sample_project, sample_design):
    climate_id = _get_climate_id(client)
    create_resp = client.post(
        "/api/v1/simulations",
        json={
            "project_id": sample_project["id"],
            "design_id": sample_design["id"],
            "climate_id": climate_id,
        },
    )
    simulation_id = create_resp.json()["id"]
    resp = client.get(f"/api/v1/simulations/{simulation_id}/results")
    assert resp.status_code == 422


def test_get_simulation_invalid_id(client):
    resp = client.get("/api/v1/simulations/sim_nope")
    assert resp.status_code == 404


def test_more_insulation_reduces_heat_loss(client, sample_project, sample_materials):
    """Sanity check on the mock thermal engine's physical direction."""
    from tests.conftest import make_design_payload

    climate_id = _get_climate_id(client)

    low_ins = make_design_payload(sample_materials, project_id=sample_project["id"], insulation_thickness=0.02)
    high_ins = make_design_payload(sample_materials, project_id=sample_project["id"], insulation_thickness=0.15)

    low_design = client.post("/api/v1/designs", json=low_ins).json()
    high_design = client.post("/api/v1/designs", json=high_ins).json()

    def run_and_get_heat_loss(design_id):
        sim = client.post(
            "/api/v1/simulations",
            json={"project_id": sample_project["id"], "design_id": design_id, "climate_id": climate_id},
        ).json()
        client.post(f"/api/v1/simulations/{sim['id']}/run")
        results = client.get(f"/api/v1/simulations/{sim['id']}/results").json()
        return results["total_heat_loss"]

    low_ins_heat_loss = run_and_get_heat_loss(low_design["id"])
    high_ins_heat_loss = run_and_get_heat_loss(high_design["id"])

    assert high_ins_heat_loss < low_ins_heat_loss
