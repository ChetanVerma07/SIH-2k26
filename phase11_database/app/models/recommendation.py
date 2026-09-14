from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class Recommendation(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "recommendations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    design_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id"), nullable=True
    )
    optimization_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("optimization_runs.id"), nullable=True
    )

    score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    # Flexible structured fields.
    trade_offs: Mapped[Optional[dict]] = mapped_column(JSONB)
    assumptions: Mapped[Optional[dict]] = mapped_column(JSONB)
    limitations: Mapped[Optional[dict]] = mapped_column(JSONB)

    project: Mapped["Project"] = relationship("Project", back_populates="recommendations")
    design: Mapped[Optional["Design"]] = relationship("Design")
    optimization_run: Mapped[Optional["OptimizationRun"]] = relationship("OptimizationRun")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Recommendation id={self.id} project={self.project_id}>"
