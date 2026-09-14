import copy

from app.models.shelter import ShelterConfig


def _sim_payload(shelter_dict, climate, settings):
    return {"climate": climate, "shelter": shelter_dict, "settings": settings}


# 1. API health endpoint -----------------------------------------------------


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


# GET /api/materials ----------------------------------------------------------


def test_materials_endpoint(client):
    resp = client.get("/api/materials")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert len(body) > 0
    sample = next(iter(body.values()))
    for key in ("name", "thermal_conductivity", "density", "specific_heat", "thickness"):
        assert key in sample


# 2. Valid simulation request --------------------------------------------------


def test_valid_simulation_request(client, basic_shelter, constant_climate, basic_settings):
    payload = _sim_payload(basic_shelter.model_dump(mode="json"), constant_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "time_series" in body
    assert "heat_loss_breakdown" in body
    expected_steps = int(round(basic_settings["duration_hours"] / (basic_settings["time_step_minutes"] / 60))) + 1
    assert len(body["time_series"]) == expected_steps


# 3. Invalid material -----------------------------------------------------------


def test_invalid_material_negative_conductivity(client, basic_shelter, constant_climate, basic_settings):
    shelter_dict = basic_shelter.model_dump(mode="json")
    shelter_dict["wall_material"]["thermal_conductivity"] = -0.5
    payload = _sim_payload(shelter_dict, constant_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 422


def test_invalid_material_zero_density(client, basic_shelter, constant_climate, basic_settings):
    shelter_dict = basic_shelter.model_dump(mode="json")
    shelter_dict["roof_material"]["density"] = 0
    payload = _sim_payload(shelter_dict, constant_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 422


# 4. Invalid shelter dimensions --------------------------------------------------


def test_invalid_shelter_negative_dimension(client, basic_shelter, constant_climate, basic_settings):
    shelter_dict = basic_shelter.model_dump(mode="json")
    shelter_dict["length"] = -5.0
    payload = _sim_payload(shelter_dict, constant_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 422


def test_invalid_shelter_zero_dimension(client, basic_shelter, constant_climate, basic_settings):
    shelter_dict = basic_shelter.model_dump(mode="json")
    shelter_dict["height"] = 0
    payload = _sim_payload(shelter_dict, constant_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 422


# 5. Constant climate simulation --------------------------------------------------


def test_constant_climate_simulation_runs(client, basic_shelter, constant_climate, basic_settings):
    payload = _sim_payload(basic_shelter.model_dump(mode="json"), constant_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    ambients = {row["ambient_temperature"] for row in body["time_series"]}
    assert ambients == {constant_climate["ambient_temperature"]}


# 6. Time-series climate simulation --------------------------------------------------


def test_timeseries_climate_simulation_interpolates(
    client, basic_shelter, timeseries_climate, basic_settings
):
    payload = _sim_payload(basic_shelter.model_dump(mode="json"), timeseries_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    time_series = body["time_series"]
    # A timestep that falls between two supplied climate points (e.g. t=3h,
    # between t=0 and t=6) should be linearly interpolated, not equal to
    # either endpoint's raw value (endpoints: -10.0 at t=0, -14.0 at t=6).
    midpoint = next(row for row in time_series if abs(row["time"] - 3.0) < 1e-6)
    assert -14.0 < midpoint["ambient_temperature"] < -10.0


# 7. Solar gain calculation --------------------------------------------------


def test_solar_gain_zero_when_no_sun(client, basic_shelter, basic_settings):
    climate = {"ambient_temperature": -10.0, "solar_radiation": 0.0}
    payload = _sim_payload(basic_shelter.model_dump(mode="json"), climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    body = resp.json()
    assert all(row["solar_gain"] == 0.0 for row in body["time_series"])


def test_solar_gain_positive_and_scales_with_radiation(client, basic_shelter, basic_settings):
    low = {"ambient_temperature": -10.0, "solar_radiation": 200.0}
    high = {"ambient_temperature": -10.0, "solar_radiation": 800.0}

    resp_low = client.post(
        "/api/simulate", json=_sim_payload(basic_shelter.model_dump(mode="json"), low, basic_settings)
    )
    resp_high = client.post(
        "/api/simulate", json=_sim_payload(basic_shelter.model_dump(mode="json"), high, basic_settings)
    )
    gain_low = resp_low.json()["time_series"][0]["solar_gain"]
    gain_high = resp_high.json()["time_series"][0]["solar_gain"]
    assert gain_low > 0
    assert gain_high > gain_low


# 8. Heat-loss calculation --------------------------------------------------


def test_heat_loss_positive_when_indoor_warmer_than_outdoor(client, basic_shelter, basic_settings):
    climate = {"ambient_temperature": -20.0, "solar_radiation": 0.0}
    settings = dict(basic_settings)
    settings["initial_indoor_temperature"] = 20.0
    payload = _sim_payload(basic_shelter.model_dump(mode="json"), climate, settings)
    resp = client.post("/api/simulate", json=payload)
    body = resp.json()
    first_step = body["time_series"][0]
    assert first_step["wall_heat_loss"] > 0
    assert first_step["roof_heat_loss"] > 0
    assert first_step["opening_heat_loss"] > 0
    assert first_step["total_heat_loss"] > 0


# 9. Indoor temperature evolution --------------------------------------------------


def test_indoor_temperature_is_transient_not_static(
    client, basic_shelter, timeseries_climate, basic_settings
):
    payload = _sim_payload(basic_shelter.model_dump(mode="json"), timeseries_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    body = resp.json()
    temps = [row["indoor_temperature"] for row in body["time_series"]]
    # Indoor temperature should change over time (not remain exactly at the
    # initial value throughout), confirming the transient update ran.
    assert len(set(round(t, 6) for t in temps)) > 1
    assert temps[0] == basic_settings["initial_indoor_temperature"]


def test_indoor_temperature_no_nan_or_extreme_blowup(
    client, basic_shelter, timeseries_climate, basic_settings
):
    payload = _sim_payload(basic_shelter.model_dump(mode="json"), timeseries_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    body = resp.json()
    temps = [row["indoor_temperature"] for row in body["time_series"]]
    assert all(-100 < t < 200 for t in temps)


# 10. Design comparison --------------------------------------------------


def test_design_comparison_ranks_all_designs(
    client, basic_shelter, timeseries_climate, basic_settings
):
    shelter_a = basic_shelter.model_dump(mode="json")
    shelter_a["name"] = "Design A - Baseline"

    shelter_b = copy.deepcopy(shelter_a)
    shelter_b["name"] = "Design B - Thicker Insulated Wall"
    shelter_b["wall_material"]["thickness"] = 0.6

    shelter_c = copy.deepcopy(shelter_a)
    shelter_c["name"] = "Design C - Larger Windows"
    shelter_c["openings"]["window_area"] = 6.0

    payload = {
        "climate": timeseries_climate,
        "shelters": [shelter_a, shelter_b, shelter_c],
        "settings": basic_settings,
    }
    resp = client.post("/api/compare", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["designs"]) == 3
    ranks = sorted(d["rank"] for d in body["designs"])
    assert ranks == [1, 2, 3]
    scores = [d["score"] for d in body["designs"]]
    assert scores == sorted(scores, reverse=True)


# 11. Opening-area validation --------------------------------------------------


def test_opening_area_exceeding_wall_area_is_rejected(
    client, basic_shelter, constant_climate, basic_settings
):
    shelter_dict = basic_shelter.model_dump(mode="json")
    # Gross wall area for this shelter is 2*(6+4)*2.7 = 54 m^2; request an
    # absurdly large opening area that exceeds it.
    shelter_dict["openings"]["window_area"] = 40.0
    shelter_dict["openings"]["door_area"] = 20.0
    payload = _sim_payload(shelter_dict, constant_climate, basic_settings)
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 422
