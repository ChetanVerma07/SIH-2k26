def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "passive-shelter-api"
    assert "version" in body


def test_create_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "location": "Delhi, India", "description": "desc"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Test Project"
    assert body["id"].startswith("proj_")
    assert body["design_ids"] == []


def test_list_projects(client, sample_project):
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert sample_project["id"] in ids


def test_get_project(client, sample_project):
    resp = client.get(f"/api/v1/projects/{sample_project['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sample_project["id"]


def test_get_project_invalid_id(client):
    resp = client.get("/api/v1/projects/does_not_exist")
    assert resp.status_code == 404


def test_delete_project(client, sample_project):
    resp = client.delete(f"/api/v1/projects/{sample_project['id']}")
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/projects/{sample_project['id']}")
    assert resp.status_code == 404


def test_create_project_invalid_input(client):
    resp = client.post("/api/v1/projects", json={"name": "", "location": "X"})
    assert resp.status_code == 422
