from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin, CreatedAtMixin


class ClimateProfile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "climate_profiles"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    location: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[Optional[float]]
    longitude: Mapped[Optional[float]]
    climate_type: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    climate_data: Mapped[List["ClimateData"]] = relationship(
        "ClimateData", back_populates="climate_profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ClimateProfile id={self.id} name={self.name!r}>"


class ClimateData(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "climate_data"

    climate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("climate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    temperature: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)  # deg C
    humidity: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # %
    pressure: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))  # hPa
    solar_radiation: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=0)  # W/m^2
    wind_speed: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))  # m/s
    wind_direction: Mapped[Optional[float]] = mapped_column(Numeric(5, 1))  # degrees

    climate_profile: Mapped["ClimateProfile"] = relationship(
        "ClimateProfile", back_populates="climate_data"
    )

    __table_args__ = (
        Index("ix_climate_data_profile_timestamp", "climate_profile_id", "timestamp"),
        CheckConstraint("humidity >= 0 AND humidity <= 100", name="ck_climate_data_humidity_range"),
        CheckConstraint("solar_radiation >= 0", name="ck_climate_data_solar_radiation_nonneg"),
        CheckConstraint(
            "wind_direction IS NULL OR (wind_direction >= 0 AND wind_direction < 360)",
            name="ck_climate_data_wind_direction_range",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ClimateData id={self.id} profile={self.climate_profile_id} ts={self.timestamp}>"
