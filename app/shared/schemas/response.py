"""
SurveyAI Shared Schemas

Module:
Standard API Responses

Purpose:
Defines the common response structure returned by SurveyAI APIs.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorDetail(BaseModel):
    """
    Represents a structured application error.
    """

    code: str = Field(
        ...,
        description="Machine-readable error code.",
    )

    message: str = Field(
        ...,
        description="Human-readable error message.",
    )


class APIResponse(BaseModel, Generic[T]):
    """
    Standard successful API response.
    """

    success: bool = True

    data: T | None = None

    error: ErrorDetail | None = None

    request_id: str | None = Field(
        default=None,
        description="Unique identifier for tracing the request.",
    )


class APIErrorResponse(BaseModel):
    """
    Standard API error response.
    """

    success: bool = False

    data: None = None

    error: ErrorDetail

    request_id: str | None = Field(
        default=None,
        description="Unique identifier for tracing the request.",
    )