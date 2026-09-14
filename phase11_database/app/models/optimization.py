from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class OptimizationStatus(str, enum.Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OptimizationRun(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "optimization_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    baseline_design_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id"), nullable=True
    )
    best_design_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id"), nullable=True
    )

    algorithm: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[OptimizationStatus] = mapped_column(
        Enum(OptimizationStatus, name="optimization_status"),
        nullable=False,
        default=OptimizationStatus.CREATED,
    )
    candidate_count: Mapped[Optional[int]] = mapped_column(Integer)
    iterations: Mapped[Optional[int]] = mapped_column(Integer)
    best_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship("Project", back_populates="optimization_runs")
    baseline_design: Mapped[Optional["Design"]] = relationship(
        "Design", foreign_keys=[baseline_design_id]
    )
    best_design: Mapped[Optional["Design"]] = relationship("Design", foreign_keys=[best_design_id])

    candidates: Mapped[List["OptimizationCandidate"]] = relationship(
        "OptimizationCandidate", back_populates="optimization_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OptimizationRun id={self.id} status={self.status}>"
