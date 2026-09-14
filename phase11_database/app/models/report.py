from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class ReportFormat(str, enum.Enum):
    JSON = "JSON"
    MARKDOWN = "MARKDOWN"


class Report(UUIDPKMixin, CreatedAtMixin, Base):
    __tablename__ = "reports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, name="report_format"), nullable=False, default=ReportFormat.JSON
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="reports")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Report id={self.id} title={self.title!r} format={self.format}>"
