"""
SurveyAI Backend

Module:
User Schemas

Purpose:
Defines Pydantic schemas used by the Surveyor account API.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """
    Schema used when creating a Surveyor account.
    """

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    full_name: str = Field(
        min_length=1,
        max_length=255,
    )

    mobile: str | None = Field(
        default=None,
        max_length=30,
    )

    organization_id: UUID | None = None
    role: str = Field(default="surveyor", max_length=50)


class UserUpdate(BaseModel):
    """
    Schema used when updating a Surveyor account.

    All fields are optional so partial updates are supported.
    """

    email: EmailStr | None = None

    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    mobile: str | None = Field(
        default=None,
        max_length=30,
    )

    status: str | None = Field(
        default=None,
        max_length=20,
    )

    organization_id: UUID | None = None
    role: str | None = Field(default=None, max_length=50)


class UserResponse(BaseModel):
    """
    Public representation of a Surveyor account.

    Password hashes are intentionally excluded.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID | None = None
    role: str = "surveyor"
    email: EmailStr
    full_name: str
    mobile: str | None
    status: str
    created_at: datetime
    updated_at: datetime
