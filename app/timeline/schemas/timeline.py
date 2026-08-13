"""
SurveyAI Backend

Module:
Timeline Schemas

Purpose:
Defines Pydantic models for Timeline API requests and responses.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TimelineEventCreate(BaseModel):
    """
    Schema for recording a new timeline audit event.
    """

    claim_id: UUID
    actor_id: UUID | None = None
    event_type: str = Field(min_length=1, max_length=100)
    description: str
    payload: dict = Field(default_factory=dict)


class TimelineEventResponse(BaseModel):
    """
    Schema for returning a timeline audit event.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    actor_id: UUID | None
    event_type: str
    description: str
    payload: dict
    created_at: datetime
