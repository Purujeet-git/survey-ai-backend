"""
SurveyAI Backend

Module:
Claim Model

Purpose:
Defines the database model for a survey claim.
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Claim(Base):
    """
    Represents an insurance survey claim belonging to a Surveyor.

    Core claim information is stored in structured columns.
    Template-specific information is stored in extra_data.
    """

    __tablename__ = "claims"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "claim_number",
            name="uq_claims_user_claim_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Claim / Insurance
    # ------------------------------------------------------------------

    claim_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    policy_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Vehicle
    # ------------------------------------------------------------------

    registration_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    chassis_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    engine_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    owner_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    owner_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    financer_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    manufacturing_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    registration_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Driver
    # ------------------------------------------------------------------

    driver_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    driving_license_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    license_issuing_authority: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    license_issue_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    license_valid_until: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    permitted_vehicle_classes: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Accident / Survey
    # ------------------------------------------------------------------

    cause_of_accident: Mapped[str | None] = mapped_column(
        Text,
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

    odometer_reading: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="created",
        index=True,
    )

    # ------------------------------------------------------------------
    # Template-specific / dynamic fields
    # ------------------------------------------------------------------

    extra_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------

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