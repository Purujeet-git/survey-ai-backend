"""
Tests for request ID middleware.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.middleware.request_id import RequestIDMiddleware


def create_test_app() -> FastAPI:
    """
    Create a minimal application for middleware testing.
    """

    app = FastAPI()

    app.add_middleware(RequestIDMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


def test_request_id_is_generated():
    """Verify that a request ID is generated automatically."""

    client = TestClient(create_test_app())

    response = client.get("/test")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) == 36


def test_existing_request_id_is_preserved():
    """Verify that a valid incoming request ID is preserved."""

    client = TestClient(create_test_app())

    request_id = "550e8400-e29b-41d4-a716-446655440000"

    response = client.get(
        "/test",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_invalid_request_id_is_replaced():
    """Verify that an invalid incoming request ID is replaced."""

    client = TestClient(create_test_app())

    response = client.get(
        "/test",
        headers={
            "X-Request-ID": "invalid-request-id",
        },
    )

    assert response.status_code == 200

    generated_request_id = response.headers.get("X-Request-ID")

    assert generated_request_id is not None
    assert generated_request_id != "invalid-request-id"
    assert len(generated_request_id) == 36