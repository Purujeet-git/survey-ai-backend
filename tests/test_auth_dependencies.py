"""
Tests for JWT authentication dependencies.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.auth.service import AuthService


@pytest.mark.asyncio
async def test_authenticated_user_can_access_protected_endpoint():
    """
    Verify that a valid access token allows access to /users/me.
    """

    email = f"dependency-{uuid4()}@example.com"
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
                "full_name": "Dependency Surveyor",
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

        access_token = login.json()["access_token"]

        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == email
    assert body["full_name"] == "Dependency Surveyor"
    assert "password_hash" not in body
    assert "password" not in body


@pytest.mark.asyncio
async def test_missing_authorization_header_is_rejected():
    """
    Verify that protected endpoints reject requests without credentials.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/api/v1/users/me",
        )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_invalid_access_token_is_rejected():
    """
    Verify that an invalid JWT is rejected.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": "Bearer invalid-token",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_wrong_jwt_signature_is_rejected():
    """
    Verify that a JWT signed with the wrong secret is rejected.
    """

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        "wrong-secret-that-is-not-the-real-key",
        algorithm=settings.JWT_ALGORITHM,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_access_token_is_rejected():
    """
    Verify that an expired access token is rejected.
    """

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "type": "access",
            "iat": now - timedelta(minutes=30),
            "exp": now - timedelta(minutes=15),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_access_protected_endpoint():
    """
    Verify that a refresh token cannot be used as an access token.
    """

    email = f"refresh-auth-{uuid4()}@example.com"
    password = "securepassword123"

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as client:

        register = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": password,
                "full_name": "Refresh Token Test",
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

        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {refresh_token}",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_with_nonexistent_user_is_rejected():
    """
    Verify that a validly signed token for a nonexistent
    user cannot access protected endpoints.
    """

    service = AuthService()

    token = service.create_access_token(
        str(uuid4())
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_is_rejected():
    """
    Verify that an inactive user cannot access protected endpoints.
    """

    email = f"inactive-{uuid4()}@example.com"
    password = "securepassword123"

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as client:

        register = await client.post(
            "/api/v1/users",
            json={
                "email": email,
                "password": password,
                "full_name": "Inactive Surveyor",
            },
        )

        assert register.status_code == 201

        user = register.json()

        login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login.status_code == 200

        access_token = login.json()["access_token"]

        update = await client.patch(
            f"/api/v1/users/{user['id']}",
            json={
                "status": "inactive",
            },
        )

        assert update.status_code == 200

        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert response.status_code == 401