from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select

from app.models.material import Material, MaterialCategory
from app.repositories.base_repository import BaseRepository


class MaterialRepository(BaseRepository[Material]):
    model = Material

    def get_by_name(self, name: str) -> Optional[Material]:
        stmt = select(Material).where(Material.name == name)
        return self.session.execute(stmt).scalars().first()

    def list_by_category(self, category: MaterialCategory, active_only: bool = True) -> List[Material]:
        stmt = select(Material).where(Material.category == category)
        if active_only:
            stmt = stmt.where(Material.is_active.is_(True))
        return list(self.session.execute(stmt).scalars().all())

    def list_active(self) -> List[Material]:
        stmt = select(Material).where(Material.is_active.is_(True))
        return list(self.session.execute(stmt).scalars().all())
