"""
SurveyAI Shared Exceptions

Module:
Base Exceptions

Purpose:
Defines the base exception used by the SurveyAI application.
"""


class SurveyAIException(Exception):
    """
    Base exception for all expected SurveyAI application errors.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "APPLICATION_ERROR",
        status_code: int = 500,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.code = code
        self.status_code = status_code