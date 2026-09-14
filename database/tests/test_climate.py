"""
Tests 4-5: Climate profile CRUD + climate time-series insertion.
"""
from datetime import datetime, timedelta, timezone

from app.repositories.climate_repository import ClimateRepository


def test_climate_profile_crud(db_session):
    repo = ClimateRepository(db_session)
    profile = repo.create(name="Test Cold Profile", climate_type="COLD_HIGH_ALTITUDE")
    assert profile.id is not None
    fetched = repo.get_by_name("Test Cold Profile")
    assert fetched.id == profile.id


def test_climate_data_bulk_insert_and_query(db_session):
    repo = ClimateRepository(db_session)
    profile = repo.create(name="Bulk Insert Profile", climate_type="HOT_DRY")

    base = datetime(2026, 6, 1, tzinfo=timezone.utc)
    rows = [
        dict(
            timestamp=base + timedelta(hours=h),
            temperature=25 + h,
            humidity=20,
            solar_radiation=500,
        )
        for h in range(24)
    ]
    inserted = repo.bulk_add_climate_data(profile.id, rows)
    assert len(inserted) == 24

    fetched = repo.get_climate_data(profile.id)
    assert len(fetched) == 24
    assert fetched[0].timestamp <= fetched[-1].timestamp
