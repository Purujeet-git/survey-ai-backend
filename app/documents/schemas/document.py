"""
SurveyAI Backend

Module:
Document Schemas

Purpose:
Defines Pydantic request and response schemas for Document API endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentUpdate(BaseModel):
    """
    Schema for updating document properties.
    """

    document_type: str | None = None
    processing_status: str | None = None
    extracted_text: str | None = None
    doc_metadata: dict | None = None


class DocumentResponse(BaseModel):
    """
    Schema for returning document details.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    user_id: UUID
    organization_id: UUID | None
    document_type: str
    file_name: str
    storage_key: str
    content_type: str
    file_size: int
    file_hash: str
    version: int
    parent_document_id: UUID | None
    is_latest: bool
    processing_status: str
    extracted_text: str | None
    classification_confidence: float | None
    doc_metadata: dict
    created_at: datetime
    updated_at: datetime


class DocumentClassificationResponse(BaseModel):
    """
    Schema for document classification output.
    """

    document_id: UUID
    document_type: str
    confidence: float
    reason: str


class DocumentExtractionResponse(BaseModel):
    """
    Schema for document text extraction output.
    """

    document_id: UUID
    extracted_text: str
    word_count: int
    page_count: int | None = None
