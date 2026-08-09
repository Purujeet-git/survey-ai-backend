"""
SurveyAI Shared Middleware

Module:
Request ID Middleware

Purpose:
Assigns a unique identifier to every HTTP request and
exposes it through the request state and response headers.
"""

from uuid import UUID, uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware responsible for request ID generation and propagation.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = self._get_request_id(request)

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers[REQUEST_ID_HEADER] = request_id

        return response

    @staticmethod
    def _get_request_id(request: Request) -> str:
        """
        Retrieve a valid request ID from the incoming request.

        If no valid request ID is supplied, generate a new UUID.
        """

        incoming_request_id = request.headers.get(REQUEST_ID_HEADER)

        if incoming_request_id:
            try:
                return str(UUID(incoming_request_id))
            except ValueError:
                pass

        return str(uuid4())