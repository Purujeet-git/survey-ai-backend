"""
SurveyAI Exception Package.
"""

from app.shared.exceptions.base import SurveyAIException
from app.shared.exceptions.common import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)

ValidationException = ValidationError
ConflictException = ConflictError
NotFoundException = NotFoundError

__all__ = [
    "SurveyAIException",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "ExternalServiceError",
    "ValidationException",
    "ConflictException",
    "NotFoundException",
]