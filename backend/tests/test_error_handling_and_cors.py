def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["docs"] == "/docs"


def test_docs_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_openapi_schema_available(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/projects" in schema["paths"]


def test_404_for_unknown_route(client):
    resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404


def test_cors_preflight_allowed_origin(client):
    resp = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_validation_error_shape(client):
    resp = client.post("/api/v1/projects", json={"location": "Somewhere"})  # missing "name"
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
