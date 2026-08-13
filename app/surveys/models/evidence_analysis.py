"""
SurveyAI Backend

Module:
Evidence Analysis Model

Purpose:
Stores AI analysis results generated from survey evidence.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvidenceAnalysis(Base):
    """
    Stores an analysis performed on a survey evidence item.
    """

    __tablename__ = "evidence_analysis"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "survey_evidence.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    analysis_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    prompt_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    result: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )