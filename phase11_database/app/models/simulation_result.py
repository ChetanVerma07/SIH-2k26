from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class SimulationResult(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "simulation_results"

    simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    indoor_temperature: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    outdoor_temperature: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    heat_loss: Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    solar_gain: Mapped[Optional[float]] = mapped_column(Numeric(12, 3))
    comfort_status: Mapped[Optional[str]] = mapped_column(String(50))

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="results")

    __table_args__ = (
        Index("ix_simulation_results_simulation_timestamp", "simulation_id", "timestamp"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SimulationResult id={self.id} sim={self.simulation_id} ts={self.timestamp}>"
