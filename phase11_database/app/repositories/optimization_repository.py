from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select

from app.models.optimization import OptimizationRun
from app.models.optimization_candidate import OptimizationCandidate
from app.repositories.base_repository import BaseRepository


class OptimizationRepository(BaseRepository[OptimizationRun]):
    model = OptimizationRun

    def list_by_project(self, project_id: uuid.UUID) -> List[OptimizationRun]:
        stmt = select(OptimizationRun).where(OptimizationRun.project_id == project_id)
        return list(self.session.execute(stmt).scalars().all())

    def add_candidate(self, optimization_run_id: uuid.UUID, **kwargs) -> OptimizationCandidate:
        record = OptimizationCandidate(optimization_run_id=optimization_run_id, **kwargs)
        self.session.add(record)
        self.session.flush()
        self.session.refresh(record)
        return record

    def list_candidates(self, optimization_run_id: uuid.UUID) -> List[OptimizationCandidate]:
        stmt = (
            select(OptimizationCandidate)
            .where(OptimizationCandidate.optimization_run_id == optimization_run_id)
            .order_by(OptimizationCandidate.rank)
        )
        return list(self.session.execute(stmt).scalars().all())
