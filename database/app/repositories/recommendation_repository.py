from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select

from app.models.recommendation import Recommendation
from app.repositories.base_repository import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    model = Recommendation

    def list_by_project(self, project_id: uuid.UUID) -> List[Recommendation]:
        stmt = select(Recommendation).where(Recommendation.project_id == project_id)
        return list(self.session.execute(stmt).scalars().all())
