from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Enum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class MaterialCategory(str, enum.Enum):
    WALL = "WALL"
    ROOF = "ROOF"
    FLOOR = "FLOOR"
    INSULATION = "INSULATION"


class Material(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "materials"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    category: Mapped[MaterialCategory] = mapped_column(
        Enum(MaterialCategory, name="material_category"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text)

    # W/(m*K)
    thermal_conductivity: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    # kg/m^3
    density: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # J/(kg*K)
    specific_heat: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # 0-1
    emissivity: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    # 0-1
    solar_absorptivity: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    # relative cost multiplier, > 0
    cost_factor: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False, default=1.0)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("thermal_conductivity > 0", name="ck_materials_thermal_conductivity_positive"),
        CheckConstraint("density > 0", name="ck_materials_density_positive"),
        CheckConstraint("specific_heat > 0", name="ck_materials_specific_heat_positive"),
        CheckConstraint("emissivity >= 0 AND emissivity <= 1", name="ck_materials_emissivity_range"),
        CheckConstraint(
            "solar_absorptivity >= 0 AND solar_absorptivity <= 1",
            name="ck_materials_solar_absorptivity_range",
        ),
        CheckConstraint("cost_factor > 0", name="ck_materials_cost_factor_positive"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Material id={self.id} name={self.name!r} category={self.category}>"
