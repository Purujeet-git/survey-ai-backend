"""
SurveyAI Backend

Module:
Evidence Analysis Schemas

Purpose:
Defines request and response schemas for AI analysis
records associated with survey evidence.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvidenceAnalysisCreate(BaseModel):
    """
    Schema for creating an evidence analysis record.
    """

    evidence_id: UUID

    analysis_type: str = Field(
        min_length=1,
        max_length=50,
    )

    provider: str | None = Field(
        default=None,
        max_length=50,
    )

    model: str | None = Field(
        default=None,
        max_length=100,
    )

    status: str = Field(
        default="pending",
        min_length=1,
        max_length=30,
    )

    prompt_version: str | None = Field(
        default=None,
        max_length=50,
    )

    result: dict[str, Any] = Field(
        default_factory=dict,
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    error: str | None = None


class EvidenceAnalysisUpdate(BaseModel):
    """
    Schema for partially updating an evidence analysis.
    """

    analysis_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    provider: str | None = Field(
        default=None,
        max_length=50,
    )

    model: str | None = Field(
        default=None,
        max_length=100,
    )

    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    prompt_version: str | None = Field(
        default=None,
        max_length=50,
    )

    result: dict[str, Any] | None = None

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    error: str | None = None


class EvidenceAnalysisResponse(BaseModel):
    """
    Schema returned by the API for an evidence analysis.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    evidence_id: UUID
    analysis_type: str
    provider: str | None
    model: str | None
    status: str
    prompt_version: str | None
    result: dict[str, Any]
    confidence: float | None
    error: str | None
    created_at: datetime
    updated_at: datetime