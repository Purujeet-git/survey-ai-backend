"""
SurveyAI Shared Exceptions

Module:
Exception Handlers

Purpose:
Converts application exceptions into standardized HTTP responses.
"""

from fastapi import Request
from fastapi.responses import ORJSONResponse

from app.shared.exceptions.base import SurveyAIException
from app.shared.schemas import APIErrorResponse, ErrorDetail
from app.shared.types import get_request_id


async def survey_ai_exception_handler(
    request: Request,
    exc: SurveyAIException,
) -> ORJSONResponse:
    """
    Convert a SurveyAIException into a standardized HTTP response.
    """

    request_id = get_request_id(request)

    response = APIErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
        ),
        request_id=request_id,
    )

    return ORJSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(),
        headers={
            "X-Request-ID": request_id,
        }
        if request_id
        else None,
    )