"""
Tests for the Survey API.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def create_user_and_login(
    client: AsyncClient,
    name: str,
):
    """
    Register a user and return the access token and user data.
    """

    email = f"survey-api-{uuid4()}@example.com"
    password = "securepassword123"

    register = await client.post(
        "/api/v1/users",
        json={
            "email": email,
            "password": password,
            "full_name": name,
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

    return user, access_token


async def create_claim(
    client: AsyncClient,
    access_token: str,
):
    """
    Create a claim for the authenticated user.
    """

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

    return response.json()


@pytest.mark.asyncio
async def test_create_survey():
    """
    Verify that an authenticated surveyor can create
    a survey for their own claim.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, access_token = await create_user_and_login(
            client,
            "Survey API Owner",
        )

        claim = await create_claim(
            client,
            access_token,
        )

        response = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "SUR-001",
                "survey_location": "Patna",
                "odometer_reading": 45000,
                "cause_of_accident": "Rear-end collision",
                "status": "draft",
                "extra_data": {
                    "damage_count": 3,
                },
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["claim_id"] == claim["id"]
    assert data["survey_number"] == "SUR-001"
    assert data["survey_location"] == "Patna"
    assert data["odometer_reading"] == 45000
    assert data["extra_data"]["damage_count"] == 3


@pytest.mark.asyncio
async def test_create_survey_requires_authentication():
    """
    Verify that survey creation requires authentication.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/api/v1/surveys",
            json={
                "claim_id": str(uuid4()),
                "survey_number": "SUR-001",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_survey_rejects_other_users_claim():
    """
    Verify that a surveyor cannot create a survey
    for another surveyor's claim.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, owner_token = await create_user_and_login(
            client,
            "Claim Owner",
        )

        claim = await create_claim(
            client,
            owner_token,
        )

        _, other_token = await create_user_and_login(
            client,
            "Other Surveyor",
        )

        response = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {other_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "UNAUTHORIZED",
                "status": "draft",
                "extra_data": {},
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_survey():
    """
    Verify that a surveyor can retrieve their own survey.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, access_token = await create_user_and_login(
            client,
            "Survey Reader",
        )

        claim = await create_claim(
            client,
            access_token,
        )

        create = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "SUR-GET",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        survey = create.json()

        response = await client.get(
            f"/api/v1/surveys/{survey['id']}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert response.status_code == 200
    assert response.json()["id"] == survey["id"]


@pytest.mark.asyncio
async def test_get_survey_rejects_wrong_user():
    """
    Verify that a survey cannot be accessed by another
    surveyor.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, owner_token = await create_user_and_login(
            client,
            "Survey Owner",
        )

        claim = await create_claim(
            client,
            owner_token,
        )

        create = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {owner_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "SUR-PRIVATE",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        survey = create.json()

        _, other_token = await create_user_and_login(
            client,
            "Other Surveyor",
        )

        response = await client.get(
            f"/api/v1/surveys/{survey['id']}",
            headers={
                "Authorization": f"Bearer {other_token}",
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_claim_surveys():
    """
    Verify that a surveyor can retrieve all surveys
    belonging to their claim.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, access_token = await create_user_and_login(
            client,
            "Survey List Owner",
        )

        claim = await create_claim(
            client,
            access_token,
        )

        for survey_number in ("SUR-001", "SUR-002"):
            response = await client.post(
                "/api/v1/surveys",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                json={
                    "claim_id": claim["id"],
                    "survey_number": survey_number,
                    "status": "draft",
                    "extra_data": {},
                },
            )

            assert response.status_code == 201

        response = await client.get(
            f"/api/v1/surveys/claim/{claim['id']}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert response.status_code == 200

    surveys = response.json()

    assert len(surveys) == 2

    survey_numbers = {
        survey["survey_number"]
        for survey in surveys
    }

    assert survey_numbers == {
        "SUR-001",
        "SUR-002",
    }


@pytest.mark.asyncio
async def test_get_claim_surveys_rejects_wrong_user():
    """
    Verify that a surveyor cannot list surveys belonging
    to another surveyor's claim.
    """

    async with AsyncClient(
        transport=ASGITransport(app),
        base_url="http://test",
    ) as client:

        _, owner_token = await create_user_and_login(
            client,
            "Claim Owner",
        )

        claim = await create_claim(
            client,
            owner_token,
        )

        _, other_token = await create_user_and_login(
            client,
            "Other Surveyor",
        )

        response = await client.get(
            f"/api/v1/surveys/claim/{claim['id']}",
            headers={
                "Authorization": f"Bearer {other_token}",
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_survey():
    """
    Verify that a surveyor can update their own survey.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, access_token = await create_user_and_login(
            client,
            "Survey Update Owner",
        )

        claim = await create_claim(
            client,
            access_token,
        )

        create = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "SUR-UPDATE",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        survey = create.json()

        response = await client.patch(
            f"/api/v1/surveys/{survey['id']}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "status": "completed",
                "notes": "Survey completed successfully.",
                "odometer_reading": 52000,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["notes"] == "Survey completed successfully."
    assert data["odometer_reading"] == 52000


@pytest.mark.asyncio
async def test_update_survey_rejects_wrong_user():
    """
    Verify that a surveyor cannot update another
    surveyor's survey.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, owner_token = await create_user_and_login(
            client,
            "Survey Owner",
        )

        claim = await create_claim(
            client,
            owner_token,
        )

        create = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {owner_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "SUR-PROTECTED",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        survey = create.json()

        _, other_token = await create_user_and_login(
            client,
            "Other Surveyor",
        )

        response = await client.patch(
            f"/api/v1/surveys/{survey['id']}",
            headers={
                "Authorization": f"Bearer {other_token}",
            },
            json={
                "notes": "Unauthorized update",
            },
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_survey():
    """
    Verify that a surveyor can delete their own survey.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, access_token = await create_user_and_login(
            client,
            "Survey Delete Owner",
        )

        claim = await create_claim(
            client,
            access_token,
        )

        create = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "SUR-DELETE",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        survey = create.json()

        response = await client.delete(
            f"/api/v1/surveys/{survey['id']}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

        assert response.status_code == 204

        get_response = await client.get(
            f"/api/v1/surveys/{survey['id']}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_survey_rejects_wrong_user():
    """
    Verify that a surveyor cannot delete another
    surveyor's survey.
    """

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        _, owner_token = await create_user_and_login(
            client,
            "Survey Owner",
        )

        claim = await create_claim(
            client,
            owner_token,
        )

        create = await client.post(
            "/api/v1/surveys",
            headers={
                "Authorization": f"Bearer {owner_token}",
            },
            json={
                "claim_id": claim["id"],
                "survey_number": "SUR-PROTECTED",
                "status": "draft",
                "extra_data": {},
            },
        )

        assert create.status_code == 201

        survey = create.json()

        _, other_token = await create_user_and_login(
            client,
            "Other Surveyor",
        )

        response = await client.delete(
            f"/api/v1/surveys/{survey['id']}",
            headers={
                "Authorization": f"Bearer {other_token}",
            },
        )

    assert response.status_code == 404