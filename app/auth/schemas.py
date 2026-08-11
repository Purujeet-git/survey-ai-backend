"""
SurveyAI Backend

Module:
Authentication Schemas

Purpose:
Defines request and response schemas for authentication.
"""

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    """
    Login credentials.
    """

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """
    Refresh-token request.
    """

    refresh_token: str


class TokenResponse(BaseModel):
    """
    Authentication token response.
    """

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int