"""
Tests for the Claim API.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_claim():
    """
    Verify that an authenticated surveyor can create a claim.
    """

    email = f"claim-api-{uuid4()}@example.com"
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
                "full_name": "Claim API Surveyor",
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

        response = await client.post(
            "/api/v1/claims",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_number": f"CLM-{uuid4()}",
                "status": "draft",
                "extra_data": {},
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_get_claim():
    """
    Verify that an authenticated surveyor can retrieve
    their own claim.
    """

    email = f"claim-get-{uuid4()}@example.com"
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
                "full_name": "Claim Get Surveyor",
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

        create = await client.post(
            "/api/v1/claims",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_number": f"CLM-{uuid4()}",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        claim_id = create.json()["id"]

        response = await client.get(
            f"/api/v1/claims/{claim_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert response.status_code == 200
    assert response.json()["id"] == claim_id


@pytest.mark.asyncio
async def test_claim_requires_authentication():
    """
    Verify that claims cannot be accessed without authentication.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/api/v1/claims",
            json={
                "claim_number": f"CLM-{uuid4()}",
                "status": "draft",
                "extra_data": {},
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_nonexistent_claim_returns_404():
    """
    Verify that requesting a nonexistent claim returns 404.
    """

    email = f"claim-404-{uuid4()}@example.com"
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
                "full_name": "Claim 404 Surveyor",
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
            f"/api/v1/claims/{uuid4()}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_claim():
    """
    Verify that an authenticated surveyor can update
    their own claim.
    """

    email = f"claim-update-{uuid4()}@example.com"
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
                "full_name": "Claim Update Surveyor",
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

        create = await client.post(
            "/api/v1/claims",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_number": f"CLM-{uuid4()}",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        claim_id = create.json()["id"]

        response = await client.patch(
            f"/api/v1/claims/{claim_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "owner_name": "Updated Owner",
                "cause_of_accident": "Rear-end collision",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["owner_name"] == "Updated Owner"
    assert data["cause_of_accident"] == "Rear-end collision"


@pytest.mark.asyncio
async def test_delete_claim():
    """
    Verify that an authenticated surveyor can delete
    their own claim.
    """

    email = f"claim-delete-{uuid4()}@example.com"
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
                "full_name": "Claim Delete Surveyor",
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

        create = await client.post(
            "/api/v1/claims",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_number": f"CLM-{uuid4()}",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        claim_id = create.json()["id"]

        response = await client.delete(
            f"/api/v1/claims/{claim_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 204

        get_response = await client.get(
            f"/api/v1/claims/{claim_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_claim_cannot_be_accessed_by_another_user():
    """
    Verify that one surveyor cannot access another surveyor's claim.
    """

    first_email = f"claim-owner-{uuid4()}@example.com"
    second_email = f"claim-other-{uuid4()}@example.com"
    password = "securepassword123"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        first_register = await client.post(
            "/api/v1/users",
            json={
                "email": first_email,
                "password": password,
                "full_name": "Claim Owner",
            },
        )

        assert first_register.status_code == 201

        first_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": first_email,
                "password": password,
            },
        )

        assert first_login.status_code == 200

        first_token = first_login.json()["access_token"]

        create = await client.post(
            "/api/v1/claims",
            headers={
                "Authorization": f"Bearer {first_token}",
            },
            json={
                "claim_number": f"CLM-{uuid4()}",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        claim_id = create.json()["id"]

        second_register = await client.post(
            "/api/v1/users",
            json={
                "email": second_email,
                "password": password,
                "full_name": "Other Surveyor",
            },
        )

        assert second_register.status_code == 201

        second_login = await client.post(
            "/api/v1/auth/login",
            json={
                "email": second_email,
                "password": password,
            },
        )

        assert second_login.status_code == 200

        second_token = second_login.json()["access_token"]

        response = await client.get(
            f"/api/v1/claims/{claim_id}",
            headers={
                "Authorization": f"Bearer {second_token}",
            },
        )

    assert response.status_code == 404