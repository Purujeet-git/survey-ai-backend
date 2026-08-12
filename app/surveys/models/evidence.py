"""
SurveyAI Backend

Module:
Survey Evidence Model

Purpose:
Defines database records for evidence attached to surveys.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SurveyEvidence(Base):
    """
    Represents a piece of evidence attached to a survey.

    The physical file is stored outside the database.
    This model stores the file reference and associated metadata.
    """

    __tablename__ = "survey_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    survey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "surveys.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    evidence_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="photo",
        server_default="photo",
        index=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    captured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    metadata_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    processing_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
        index=True,
    )

    processing_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extra_data: Mapped[dict] = mapped_column(
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