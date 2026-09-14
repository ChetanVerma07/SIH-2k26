from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select

from app.models.report import Report
from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report

    def list_by_project(self, project_id: uuid.UUID) -> List[Report]:
        stmt = select(Report).where(Report.project_id == project_id)
        return list(self.session.execute(stmt).scalars().all())
