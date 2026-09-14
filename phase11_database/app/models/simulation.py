from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class SimulationStatus(str, enum.Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SimulationBackend(str, enum.Enum):
    MOCK = "MOCK"
    ANSYS = "ANSYS"


class Simulation(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "simulations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("designs.id", ondelete="CASCADE"), nullable=False
    )
    climate_profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("climate_profiles.id"), nullable=True
    )

    duration_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=24)
    timestep_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    status: Mapped[SimulationStatus] = mapped_column(
        Enum(SimulationStatus, name="simulation_status"),
        nullable=False,
        default=SimulationStatus.CREATED,
    )
    backend: Mapped[SimulationBackend] = mapped_column(
        Enum(SimulationBackend, name="simulation_backend"),
        nullable=False,
        default=SimulationBackend.MOCK,
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Aggregate summary metrics, populated once the simulation completes.
    average_temperature: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    minimum_temperature: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    maximum_temperature: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    comfort_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    total_heat_loss: Mapped[Optional[float]] = mapped_column(Numeric(14, 3))
    total_solar_gain: Mapped[Optional[float]] = mapped_column(Numeric(14, 3))
    external_energy_requirement: Mapped[Optional[float]] = mapped_column(Numeric(14, 3))

    project: Mapped["Project"] = relationship("Project", back_populates="simulations")
    design: Mapped["Design"] = relationship(
        "Design", back_populates="simulations", foreign_keys=[design_id]
    )
    climate_profile: Mapped[Optional["ClimateProfile"]] = relationship("ClimateProfile")

    results: Mapped[List["SimulationResult"]] = relationship(
        "SimulationResult", back_populates="simulation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Simulation id={self.id} status={self.status}>"
