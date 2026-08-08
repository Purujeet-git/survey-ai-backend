"""
Tests for shared API response schemas.
"""

from app.shared.schemas import (
    APIErrorResponse,
    APIResponse,
    ErrorDetail,
)


def test_success_response():
    """Verify the standard success response."""

    response = APIResponse(
        data={"message": "Success"},
        request_id="test-request-id",
    )

    assert response.success is True
    assert response.data == {"message": "Success"}
    assert response.error is None
    assert response.request_id == "test-request-id"


def test_error_response():
    """Verify the standard error response."""

    response = APIErrorResponse(
        error=ErrorDetail(
            code="TEST_ERROR",
            message="Something went wrong.",
        ),
        request_id="test-request-id",
    )

    assert response.success is False
    assert response.data is None
    assert response.error.code == "TEST_ERROR"
    assert response.error.message == "Something went wrong."
    assert response.request_id == "test-request-id"