from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select

from app.models.project import Project
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    def get_by_name(self, name: str) -> Optional[Project]:
        stmt = select(Project).where(Project.name == name)
        return self.session.execute(stmt).scalars().first()

    def list_by_location(self, location: str) -> List[Project]:
        stmt = select(Project).where(Project.location == location)
        return list(self.session.execute(stmt).scalars().all())
