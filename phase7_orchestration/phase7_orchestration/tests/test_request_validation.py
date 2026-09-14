import pytest
from pydantic import ValidationError

from app.models.request import ComfortRange, ShelterDesignRequest


def test_valid_request_constructs():
    req = ShelterDesignRequest(
        location="Ladakh",
        climate_description="cold high-altitude",
        comfort_range=ComfortRange(min_c=18, max_c=26),
    )
    assert req.location == "Ladakh"
    assert req.simulation_duration_hours == 24


def test_comfort_range_rejects_inverted_bounds():
    with pytest.raises(ValidationError):
        ComfortRange(min_c=26, max_c=18)


def test_blank_location_rejected():
    with pytest.raises(ValidationError):
        ShelterDesignRequest(
            location="   ",
            climate_description="cold",
            comfort_range=ComfortRange(min_c=18, max_c=26),
        )


def test_negative_budget_rejected():
    with pytest.raises(ValidationError):
        ShelterDesignRequest(
            location="Ladakh",
            climate_description="cold",
            comfort_range=ComfortRange(min_c=18, max_c=26),
            budget=-100,
        )


def test_default_objectives_populated():
    req = ShelterDesignRequest(
        location="Ladakh",
        climate_description="cold",
        comfort_range=ComfortRange(min_c=18, max_c=26),
    )
    assert "maximize thermal comfort" in req.objectives
