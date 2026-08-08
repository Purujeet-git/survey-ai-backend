"""
SurveyAI Shared Exceptions

Module:
Common Exceptions

Purpose:
Defines reusable application-level exceptions.
"""

from app.shared.exceptions.base import SurveyAIException


class ValidationError(SurveyAIException):
    """
    Raised when application-level validation fails.
    """

    def __init__(
        self,
        message: str = "The provided data is invalid.",
    ) -> None:
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=400,
        )


class NotFoundError(SurveyAIException):
    """
    Raised when a requested resource does not exist.
    """

    def __init__(
        self,
        message: str = "The requested resource was not found.",
    ) -> None:
        super().__init__(
            message,
            code="NOT_FOUND",
            status_code=404,
        )


class AuthenticationError(SurveyAIException):
    """
    Raised when authentication fails.
    """

    def __init__(
        self,
        message: str = "Authentication is required.",
    ) -> None:
        super().__init__(
            message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(SurveyAIException):
    """
    Raised when an authenticated user lacks permission.
    """

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
    ) -> None:
        super().__init__(
            message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class ConflictError(SurveyAIException):
    """
    Raised when an operation conflicts with existing state.
    """

    def __init__(
        self,
        message: str = "The requested operation conflicts with existing data.",
    ) -> None:
        super().__init__(
            message,
            code="CONFLICT_ERROR",
            status_code=409,
        )


class ExternalServiceError(SurveyAIException):
    """
    Raised when an external service fails.
    """

    def __init__(
        self,
        message: str = "An external service failed to process the request.",
    ) -> None:
        super().__init__(
            message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
        )