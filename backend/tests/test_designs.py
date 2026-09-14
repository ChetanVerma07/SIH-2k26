from tests.conftest import make_design_payload


def test_create_design(client, sample_project, sample_materials):
    payload = make_design_payload(sample_materials, project_id=sample_project["id"])
    resp = client.post("/api/v1/designs", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"].startswith("design_")
    assert body["project_id"] == sample_project["id"]

    # project should now list this design
    proj_resp = client.get(f"/api/v1/projects/{sample_project['id']}")
    assert body["id"] in proj_resp.json()["design_ids"]


def test_create_design_invalid_temperature_range(client, sample_materials):
    payload = make_design_payload(sample_materials)
    payload["target_min_temperature"] = 25
    payload["target_max_temperature"] = 20  # invalid: max <= min
    resp = client.post("/api/v1/designs", json=payload)
    assert resp.status_code == 422


def test_create_design_invalid_orientation(client, sample_materials):
    payload = make_design_payload(sample_materials)
    payload["orientation"] = "XX"
    resp = client.post("/api/v1/designs", json=payload)
    assert resp.status_code == 422


def test_create_design_unknown_material(client, sample_materials):
    payload = make_design_payload(sample_materials)
    payload["wall_material"] = "mat_does_not_exist"
    resp = client.post("/api/v1/designs", json=payload)
    assert resp.status_code == 422


def test_get_list_update_delete_design(client, sample_design):
    design_id = sample_design["id"]

    resp = client.get("/api/v1/designs")
    assert resp.status_code == 200
    assert any(d["id"] == design_id for d in resp.json())

    resp = client.get(f"/api/v1/designs/{design_id}")
    assert resp.status_code == 200

    resp = client.put(f"/api/v1/designs/{design_id}", json={"opening_percentage": 15})
    assert resp.status_code == 200
    assert resp.json()["opening_percentage"] == 15

    resp = client.delete(f"/api/v1/designs/{design_id}")
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/designs/{design_id}")
    assert resp.status_code == 404


def test_get_design_invalid_id(client):
    resp = client.get("/api/v1/designs/nope")
    assert resp.status_code == 404
