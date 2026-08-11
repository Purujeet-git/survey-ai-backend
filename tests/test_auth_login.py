"""
Tests for authentication login flow.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_login_success():
    email = f"login-{uuid4()}@example.com"
    password = "securepassword123"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        register_response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": password,
                "full_name": "Login Surveyor",
            },
        )

        assert register_response.status_code == 201

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_wrong_password():
    email = f"wrong-password-{uuid4()}@example.com"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        register_response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": "correct-password",
                "full_name": "Login Surveyor",
            },
        )

        assert register_response.status_code == 201

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_unknown_email():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": f"unknown-{uuid4()}@example.com",
                "password": "securepassword123",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."