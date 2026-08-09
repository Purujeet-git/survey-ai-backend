"""
SurveyAI Shared Types

Module:
Request Types

Purpose:
Provides helpers for accessing request-scoped information.
"""

from fastapi import Request


def get_request_id(request: Request) -> str | None:
    """
    Retrieve the request ID assigned by RequestIDMiddleware.
    """

    return getattr(
        request.state,
        "request_id",
        None,
    )