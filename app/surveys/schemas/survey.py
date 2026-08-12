"""
SurveyAI Backend

Module:
Survey Schemas

Purpose:
Defines request and response schemas for survey operations.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SurveyCreate(BaseModel):
    """
    Schema for creating a survey.
    """

    claim_id: UUID

    survey_number: str | None = Field(
        default=None,
        max_length=100,
    )

    survey_date: date | None = None

    survey_location: str | None = None

    latitude: float | None = None

    longitude: float | None = None

    location_source: str | None = Field(
        default=None,
        max_length=50,
    )

    odometer_reading: int | None = Field(
        default=None,
        ge=0,
    )

    cause_of_accident: str | None = None

    notes: str | None = None

    status: str = Field(
        default="draft",
        max_length=30,
    )

    extra_data: dict = Field(
        default_factory=dict,
    )


class SurveyUpdate(BaseModel):
    """
    Schema for updating an existing survey.

    All fields are optional so PATCH requests can update
    only the fields that were supplied.
    """

    survey_number: str | None = Field(
        default=None,
        max_length=100,
    )

    survey_date: date | None = None

    survey_location: str | None = None

    latitude: float | None = None

    longitude: float | None = None

    location_source: str | None = Field(
        default=None,
        max_length=50,
    )

    odometer_reading: int | None = Field(
        default=None,
        ge=0,
    )

    cause_of_accident: str | None = None

    notes: str | None = None

    status: str | None = Field(
        default=None,
        max_length=30,
    )

    extra_data: dict | None = None


class SurveyResponse(BaseModel):
    """
    Schema returned by the Survey API.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    claim_id: UUID

    survey_number: str | None
    survey_date: date | None
    survey_location: str | None

    latitude: float | None
    longitude: float | None
    location_source: str | None

    odometer_reading: int | None

    cause_of_accident: str | None
    notes: str | None

    status: str
    extra_data: dict

    created_at: datetime
    updated_at: datetime