"""
Tests for authentication session management.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_refresh_access_token():
    email = f"refresh-{uuid4()}@example.com"
    password = "securepassword123"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        register = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": password,
                "full_name": "Refresh Surveyor",
            },
        )

        assert register.status_code == 201

        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login.status_code == 200

        tokens = login.json()

        refresh = await client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": tokens["refresh_token"],
            },
        )

    assert refresh.status_code == 200

    body = refresh.json()

    assert body["access_token"]
    assert body["refresh_token"] == tokens["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_invalid_refresh_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "invalid-token",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token."


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token():
    email = f"logout-{uuid4()}@example.com"
    password = "securepassword123"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        register = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": password,
                "full_name": "Logout Surveyor",
            },
        )

        assert register.status_code == 201

        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login.status_code == 200

        refresh_token = login.json()["refresh_token"]

        logout = await client.post(
            "/api/v1/auth/logout",
            json={
                "refresh_token": refresh_token,
            },
        )

        assert logout.status_code == 204

        refresh = await client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )

    assert refresh.status_code == 401
    assert refresh.json()["detail"] == "Invalid refresh token."