from __future__ import annotations

from typing import List, Optional

from sqlalchemy import CheckConstraint, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Project(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    climate_type: Mapped[Optional[str]] = mapped_column(String(100))

    designs: Mapped[List["Design"]] = relationship(
        "Design", back_populates="project", cascade="all, delete-orphan"
    )
    simulations: Mapped[List["Simulation"]] = relationship(
        "Simulation", back_populates="project", cascade="all, delete-orphan"
    )
    optimization_runs: Mapped[List["OptimizationRun"]] = relationship(
        "OptimizationRun", back_populates="project", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="project", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_projects_location", "location"),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name="ck_projects_latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name="ck_projects_longitude_range",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Project id={self.id} name={self.name!r}>"
