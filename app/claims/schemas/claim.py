"""
SurveyAI Backend

Module:
Claim Schemas

Purpose:
Defines request and response schemas for claims.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClaimCreate(BaseModel):
    """
    Data required to create a claim.
    """

    claim_number: str = Field(
        min_length=1,
        max_length=100,
    )

    policy_number: str | None = None
    registration_number: str | None = None

    chassis_number: str | None = None
    engine_number: str | None = None

    owner_name: str | None = None
    owner_address: str | None = None
    financer_name: str | None = None

    manufacturing_date: date | None = None
    registration_date: date | None = None

    driver_name: str | None = None
    driving_license_number: str | None = None
    license_issuing_authority: str | None = None
    license_issue_date: date | None = None
    license_valid_until: date | None = None

    permitted_vehicle_classes: list[str] | None = None

    cause_of_accident: str | None = None

    survey_date: date | None = None
    survey_location: str | None = None

    odometer_reading: int | None = None

    status: str = "draft"

    extra_data: dict = Field(
        default_factory=dict,
    )


class ClaimUpdate(BaseModel):
    """
    Fields that can be updated on an existing claim.
    """

    claim_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    policy_number: str | None = None
    registration_number: str | None = None

    chassis_number: str | None = None
    engine_number: str | None = None

    owner_name: str | None = None
    owner_address: str | None = None
    financer_name: str | None = None

    manufacturing_date: date | None = None
    registration_date: date | None = None

    driver_name: str | None = None
    driving_license_number: str | None = None
    license_issuing_authority: str | None = None
    license_issue_date: date | None = None
    license_valid_until: date | None = None

    permitted_vehicle_classes: list[str] | None = None

    cause_of_accident: str | None = None

    survey_date: date | None = None
    survey_location: str | None = None

    odometer_reading: int | None = None

    status: str | None = None

    extra_data: dict | None = None


class ClaimResponse(BaseModel):
    """
    API representation of a claim.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    user_id: UUID

    claim_number: str

    policy_number: str | None
    registration_number: str | None

    chassis_number: str | None
    engine_number: str | None

    owner_name: str | None
    owner_address: str | None
    financer_name: str | None

    manufacturing_date: date | None
    registration_date: date | None

    driver_name: str | None
    driving_license_number: str | None
    license_issuing_authority: str | None
    license_issue_date: date | None
    license_valid_until: date | None

    permitted_vehicle_classes: list[str] | None

    cause_of_accident: str | None

    survey_date: date | None
    survey_location: str | None

    odometer_reading: int | None

    status: str

    extra_data: dict

    created_at: datetime
    updated_at: datetime