"""
Tests for the Surveyor User API.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_user():
    email = f"api-{uuid4()}@example.com"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": "securepassword123",
                "full_name": "API Surveyor",
                "mobile": "9876543210",
            },
        )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == email
    assert body["full_name"] == "API Surveyor"
    assert body["mobile"] == "9876543210"
    assert body["status"] == "active"

    # Password must never appear in the API response.
    assert "password" not in body
    assert "password_hash" not in body

    return body["id"]


@pytest.mark.asyncio
async def test_get_user():
    email = f"get-{uuid4()}@example.com"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        create_response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": "securepassword123",
                "full_name": "Get Surveyor",
            },
        )

        assert create_response.status_code == 201

        user_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/users/{user_id}",
        )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == user_id
    assert body["email"] == email
    assert body["full_name"] == "Get Surveyor"


@pytest.mark.asyncio
async def test_update_user():
    email = f"update-api-{uuid4()}@example.com"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        create_response = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": "securepassword123",
                "full_name": "Original Surveyor",
            },
        )

        assert create_response.status_code == 201

        user_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/users/{user_id}",
            json={
                "full_name": "Updated Surveyor",
                "mobile": "9999999999",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["full_name"] == "Updated Surveyor"
    assert body["mobile"] == "9999999999"


@pytest.mark.asyncio
async def test_get_nonexistent_user():
    user_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/users/{user_id}",
        )

    assert response.status_code == 404