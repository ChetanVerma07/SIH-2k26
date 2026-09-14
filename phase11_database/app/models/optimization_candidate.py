from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class OptimizationCandidate(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "optimization_candidates"

    optimization_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False
    )
    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id", ondelete="CASCADE"), nullable=False
    )

    generation: Mapped[Optional[int]] = mapped_column(Integer)
    score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    comfort_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    heat_loss_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    energy_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    cost_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    rank: Mapped[Optional[int]] = mapped_column(Integer)

    optimization_run: Mapped["OptimizationRun"] = relationship(
        "OptimizationRun", back_populates="candidates"
    )
    design: Mapped["Design"] = relationship("Design")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OptimizationCandidate id={self.id} run={self.optimization_run_id} rank={self.rank}>"
