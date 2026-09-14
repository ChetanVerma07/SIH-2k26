from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import select

from app.models.climate import ClimateData, ClimateProfile
from app.repositories.base_repository import BaseRepository


class ClimateRepository(BaseRepository[ClimateProfile]):
    model = ClimateProfile

    def get_by_name(self, name: str) -> Optional[ClimateProfile]:
        stmt = select(ClimateProfile).where(ClimateProfile.name == name)
        return self.session.execute(stmt).scalars().first()

    def add_climate_data_point(self, climate_profile_id: uuid.UUID, **kwargs) -> ClimateData:
        record = ClimateData(climate_profile_id=climate_profile_id, **kwargs)
        self.session.add(record)
        self.session.flush()
        self.session.refresh(record)
        return record

    def bulk_add_climate_data(
        self, climate_profile_id: uuid.UUID, rows: Sequence[dict]
    ) -> List[ClimateData]:
        records = [ClimateData(climate_profile_id=climate_profile_id, **row) for row in rows]
        self.session.add_all(records)
        self.session.flush()
        return records

    def get_climate_data(
        self,
        climate_profile_id: uuid.UUID,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[ClimateData]:
        stmt = select(ClimateData).where(ClimateData.climate_profile_id == climate_profile_id)
        if start is not None:
            stmt = stmt.where(ClimateData.timestamp >= start)
        if end is not None:
            stmt = stmt.where(ClimateData.timestamp <= end)
        stmt = stmt.order_by(ClimateData.timestamp)
        return list(self.session.execute(stmt).scalars().all())
