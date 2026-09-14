from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select

from app.models.design import Design
from app.repositories.base_repository import BaseRepository


class DesignRepository(BaseRepository[Design]):
    model = Design

    def list_by_project(self, project_id: uuid.UUID) -> List[Design]:
        stmt = select(Design).where(Design.project_id == project_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_baseline(self, project_id: uuid.UUID) -> Design | None:
        stmt = select(Design).where(
            Design.project_id == project_id, Design.is_baseline.is_(True)
        )
        return self.session.execute(stmt).scalars().first()
