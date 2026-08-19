"""
SurveyAI Backend

Module:
Authentication Schemas

Purpose:
Defines request and response schemas for authentication.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Login credentials.
    """

    email: EmailStr
    password: str


class LoginOrRegisterRequest(BaseModel):
    """Credentials used by the first-time sign-in flow."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


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


class LoginOrRegisterResponse(TokenResponse):
    """Tokens plus whether a new account was created for this sign-in."""

    is_new_user: bool = False
