"""
SurveyAI Backend

Module:
Organization Schemas

Purpose:
Defines Pydantic models for Organization REST requests and responses.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationCreate(BaseModel):
    """
    Schema for creating a new Organization.
    """

    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=50)
    contact_email: EmailStr | None = None
    address: str | None = None
    settings: dict = Field(default_factory=dict)


class OrganizationUpdate(BaseModel):
    """
    Schema for updating an existing Organization.
    """

    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    contact_email: EmailStr | None = None
    address: str | None = None
    status: str | None = Field(default=None, max_length=20)
    settings: dict | None = None


class OrganizationResponse(BaseModel):
    """
    Schema for Organization API responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    contact_email: EmailStr | None
    address: str | None
    status: str
    settings: dict
    created_at: datetime
    updated_at: datetime
