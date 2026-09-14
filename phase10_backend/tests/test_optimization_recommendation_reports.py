def test_create_and_run_optimization(client, sample_project, sample_design):
    create_resp = client.post(
        "/api/v1/optimization",
        json={"project_id": sample_project["id"], "baseline_design_id": sample_design["id"]},
    )
    assert create_resp.status_code == 201
    optimization_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "CREATED"

    run_resp = client.post(f"/api/v1/optimization/{optimization_id}/run")
    assert run_resp.status_code == 200
    body = run_resp.json()
    assert body["status"] == "COMPLETED"
    assert len(body["candidates"]) > 0
    assert body["best_candidate_design_id"] is not None
    # best candidate should be one of the generated candidates
    candidate_ids = [c["design_id"] for c in body["candidates"]]
    assert body["best_candidate_design_id"] in candidate_ids

    status_resp = client.get(f"/api/v1/optimization/{optimization_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "COMPLETED"


def test_create_optimization_invalid_project(client, sample_design):
    resp = client.post(
        "/api/v1/optimization",
        json={"project_id": "proj_nope", "baseline_design_id": sample_design["id"]},
    )
    assert resp.status_code == 404


def test_get_optimization_invalid_id(client):
    resp = client.get("/api/v1/optimization/opt_nope")
    assert resp.status_code == 404


def test_recommendation(client, sample_project, sample_design):
    resp = client.get(f"/api/v1/projects/{sample_project['id']}/recommendation")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project_id"] == sample_project["id"]
    assert body["recommended_design_id"] == sample_design["id"]
    assert "explanation" in body and len(body["explanation"]) > 0
    assert len(body["assumptions"]) > 0
    assert len(body["limitations"]) > 0


def test_recommendation_no_designs(client, sample_project):
    resp = client.get(f"/api/v1/projects/{sample_project['id']}/recommendation")
    assert resp.status_code == 404


def test_recommendation_invalid_project(client):
    resp = client.get("/api/v1/projects/proj_nope/recommendation")
    assert resp.status_code == 404


def test_comparison(client, sample_project, sample_materials):
    from tests.conftest import make_design_payload

    d1 = client.post(
        "/api/v1/designs", json=make_design_payload(sample_materials, project_id=sample_project["id"])
    ).json()
    d2 = client.post(
        "/api/v1/designs",
        json=make_design_payload(sample_materials, project_id=sample_project["id"], insulation_thickness=0.15),
    ).json()

    resp = client.post("/api/v1/comparisons", json={"design_ids": [d1["id"], d2["id"]]})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["metrics"]) == 2
    assert body["best_design_id"] in (d1["id"], d2["id"])


def test_comparison_requires_two_designs(client, sample_design):
    resp = client.post("/api/v1/comparisons", json={"design_ids": [sample_design["id"]]})
    assert resp.status_code == 422


def test_report_json(client, sample_project, sample_design):
    resp = client.get(f"/api/v1/projects/{sample_project['id']}/report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["project"]["id"] == sample_project["id"]
    assert "climate" in body
    assert "recommendation" in body
    assert "assumptions" in body
    assert "limitations" in body


def test_report_markdown(client, sample_project, sample_design):
    resp = client.get(f"/api/v1/projects/{sample_project['id']}/report/markdown")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert sample_project["name"] in resp.text


def test_report_invalid_project(client):
    resp = client.get("/api/v1/projects/proj_nope/report")
    assert resp.status_code == 404
