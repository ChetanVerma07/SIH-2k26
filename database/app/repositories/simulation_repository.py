from __future__ import annotations

import uuid
from typing import List, Sequence

from sqlalchemy import select

from app.models.simulation import Simulation
from app.models.simulation_result import SimulationResult
from app.repositories.base_repository import BaseRepository


class SimulationRepository(BaseRepository[Simulation]):
    model = Simulation

    def list_by_project(self, project_id: uuid.UUID) -> List[Simulation]:
        stmt = select(Simulation).where(Simulation.project_id == project_id)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_design(self, design_id: uuid.UUID) -> List[Simulation]:
        stmt = select(Simulation).where(Simulation.design_id == design_id)
        return list(self.session.execute(stmt).scalars().all())

    def add_result(self, simulation_id: uuid.UUID, **kwargs) -> SimulationResult:
        record = SimulationResult(simulation_id=simulation_id, **kwargs)
        self.session.add(record)
        self.session.flush()
        self.session.refresh(record)
        return record

    def bulk_add_results(
        self, simulation_id: uuid.UUID, rows: Sequence[dict]
    ) -> List[SimulationResult]:
        records = [SimulationResult(simulation_id=simulation_id, **row) for row in rows]
        self.session.add_all(records)
        self.session.flush()
        return records

    def get_results(self, simulation_id: uuid.UUID) -> List[SimulationResult]:
        stmt = (
            select(SimulationResult)
            .where(SimulationResult.simulation_id == simulation_id)
            .order_by(SimulationResult.timestamp)
        )
        return list(self.session.execute(stmt).scalars().all())
