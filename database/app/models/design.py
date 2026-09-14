from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Design(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "designs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    design_name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_baseline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Geometry (meters / degrees)
    length: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    width: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    height: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    wall_thickness: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    roof_thickness: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    floor_thickness: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    insulation_thickness: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    opening_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    orientation: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))  # degrees from north

    # Requirements
    occupants: Mapped[Optional[int]]
    floor_area: Mapped[Optional[float]] = mapped_column(Numeric(10, 3))
    target_min_temperature: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    target_max_temperature: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    budget: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))

    # Materials
    wall_material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id"), nullable=True
    )
    roof_material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id"), nullable=True
    )
    floor_material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id"), nullable=True
    )
    insulation_material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id"), nullable=True
    )

    project: Mapped["Project"] = relationship("Project", back_populates="designs")
    wall_material: Mapped[Optional["Material"]] = relationship("Material", foreign_keys=[wall_material_id])
    roof_material: Mapped[Optional["Material"]] = relationship("Material", foreign_keys=[roof_material_id])
    floor_material: Mapped[Optional["Material"]] = relationship("Material", foreign_keys=[floor_material_id])
    insulation_material: Mapped[Optional["Material"]] = relationship(
        "Material", foreign_keys=[insulation_material_id]
    )

    simulations: Mapped[List["Simulation"]] = relationship(
        "Simulation", back_populates="design", foreign_keys="Simulation.design_id"
    )

    __table_args__ = (
        CheckConstraint("length > 0 AND width > 0 AND height > 0", name="ck_designs_dimensions_positive"),
        CheckConstraint("wall_thickness > 0", name="ck_designs_wall_thickness_positive"),
        CheckConstraint("roof_thickness > 0", name="ck_designs_roof_thickness_positive"),
        CheckConstraint("floor_thickness > 0", name="ck_designs_floor_thickness_positive"),
        CheckConstraint("insulation_thickness >= 0", name="ck_designs_insulation_thickness_nonneg"),
        CheckConstraint(
            "opening_percentage >= 0 AND opening_percentage <= 100",
            name="ck_designs_opening_percentage_range",
        ),
        CheckConstraint(
            "target_min_temperature IS NULL OR target_max_temperature IS NULL "
            "OR target_min_temperature <= target_max_temperature",
            name="ck_designs_target_temperature_order",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Design id={self.id} project={self.project_id}>"
