"""
SurveyAI Backend

Module:
Survey Report Model

Purpose:
Defines database model for generated surveyor reports, spreadsheet versions, and document paths.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SurveyReport(Base):
    """
    Represents a generated survey report record containing Excel & Word report artifacts.
    """

    __tablename__ = "survey_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
        index=True,
    )

    excel_storage_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    docx_storage_key: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    summary_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    claim: Mapped["Claim"] = relationship("Claim")
    user: Mapped["User"] = relationship("User")
