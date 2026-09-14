import json
from pathlib import Path
from typing import Dict, List

from fastapi import HTTPException, status

from app.core.logging import logger
from app.models.climate import ClimateRecord
from app.repositories.memory_repository import RepositoryRegistry, new_id
from app.schemas.climate import ClimateCreate

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PRESETS_FILE = DATA_DIR / "climate_presets.json"


class ClimateService:
    def __init__(self, repos: RepositoryRegistry):
        self.repos = repos
        self._presets_by_location: Dict[str, dict] = {}
        self._load_presets_into_repo()

    def _load_presets_into_repo(self) -> None:
        if not PRESETS_FILE.exists():
            return
        with open(PRESETS_FILE, "r") as f:
            presets = json.load(f)

        for preset in presets:
            location_key = preset["location"].lower()
            if location_key in self._presets_by_location:
                continue
            record = ClimateRecord(
                id=new_id("climate"),
                location=preset["location"],
                temperature=preset["temperature"],
                humidity=preset["humidity"],
                pressure=preset["pressure"],
                solar_radiation=preset["solar_radiation"],
                wind_speed=preset["wind_speed"],
                wind_direction=preset["wind_direction"],
                is_preset=True,
                data_source="preset",
            )
            self.repos.climate_records.add(record.id, record)
            self._presets_by_location[location_key] = record

    def list_presets(self) -> List[ClimateRecord]:
        return [r for r in self.repos.climate_records.list() if r.is_preset]

    def get_by_location(self, location: str) -> ClimateRecord:
        key = location.lower()
        record = self._presets_by_location.get(key)
        if record is None:
            # fall back to scanning all records (covers custom named climates too)
            for r in self.repos.climate_records.list():
                if r.location and r.location.lower() == key:
                    record = r
                    break
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No climate data found for location '{location}'",
            )
        return record

    def create_custom_climate(self, payload: ClimateCreate) -> ClimateRecord:
        record = ClimateRecord(
            id=new_id("climate"),
            location=payload.location,
            temperature=payload.temperature,
            humidity=payload.humidity,
            pressure=payload.pressure,
            solar_radiation=payload.solar_radiation,
            wind_speed=payload.wind_speed,
            wind_direction=payload.wind_direction,
            is_preset=False,
            time_series=[p.model_dump() for p in payload.time_series] if payload.time_series else None,
        )
        self.repos.climate_records.add(record.id, record)
        logger.info("Created custom climate record %s", record.id)
        return record

    def get_climate(self, climate_id: str) -> ClimateRecord:
        record = self.repos.climate_records.get(climate_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Climate record '{climate_id}' not found",
            )
        return record
