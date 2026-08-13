"""
SurveyAI Backend

Module:
Report Schemas

Purpose:
Defines Pydantic request and response schemas for Report endpoints and export payloads.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SurveyReportResponse(BaseModel):
    """
    Schema for survey report details.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    user_id: UUID
    version: int
    status: str
    excel_storage_key: str | None
    docx_storage_key: str | None
    summary_data: dict
    created_at: datetime
    updated_at: datetime


class ReportGenerateRequest(BaseModel):
    """
    Optional overrides for generating surveyor reports.
    """

    less_excess: float = Field(default=1000.0, description="Policy compulsory deductible excess")
    salvage_value: float = Field(default=500.0, description="Estimated salvage value of replaced parts")
    comments: str | None = Field(default=None, description="Surveyor notes/comments")
