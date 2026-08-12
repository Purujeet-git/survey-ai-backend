"""
SurveyAI Backend

Module:
Survey Model

Purpose:
Defines the database model for a vehicle survey.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime,Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Survey(Base):
    """
    Represents a physical vehicle survey performed for a claim.

    A claim can have multiple surveys, for example:
    - Initial survey
    - Re-survey
    - Final survey
    """

    __tablename__ = "surveys"

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

    survey_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    survey_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    survey_location: Mapped[str | None] = mapped_column(
        Text,
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

    location_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    odometer_reading: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    cause_of_accident: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="draft",
        server_default="draft",
        index=True,
    )

    extra_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
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