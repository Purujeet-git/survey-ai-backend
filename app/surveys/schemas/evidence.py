from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SurveyEvidenceCreate(BaseModel):
    """
    Data required to create survey evidence.

    survey_id is intentionally excluded because it is
    supplied through the API URL.
    """

    evidence_type: str = "photo"
    file_name: str = Field(..., max_length=255)
    storage_key: str = Field(..., max_length=500)
    content_type: str = Field(..., max_length=100)
    file_size: int = Field(..., ge=0)
    file_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    captured_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    metadata_source: str | None = Field(
        default=None,
        max_length=50,
    )
    processing_status: str = "uploaded"
    processing_error: str | None = None
    extra_data: dict = Field(default_factory=dict)


class SurveyEvidenceUpdate(BaseModel):
    """
    Fields that can be updated on survey evidence.
    """

    evidence_type: str | None = None
    file_name: str | None = Field(
        default=None,
        max_length=255,
    )
    content_type: str | None = Field(
        default=None,
        max_length=100,
    )
    file_size: int | None = Field(
        default=None,
        ge=0,
    )
    file_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    captured_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    metadata_source: str | None = Field(
        default=None,
        max_length=50,
    )
    processing_status: str | None = None
    processing_error: str | None = None
    extra_data: dict | None = None


class SurveyEvidenceResponse(BaseModel):
    """
    Survey evidence API response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    survey_id: UUID
    evidence_type: str
    file_name: str
    storage_key: str
    content_type: str
    file_size: int
    file_hash: str | None
    captured_at: datetime | None
    latitude: float | None
    longitude: float | None
    metadata_source: str | None
    processing_status: str
    processing_error: str | None
    extra_data: dict
    created_at: datetime
    updated_at: datetime