"""
Tests for the Survey Evidence API.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.users.models.user import User
from app.claims.models.claim import Claim
from app.surveys.models.survey import Survey


async def create_test_user(async_session):
    """
    Create a real surveyor for API tests.
    """

    user = User(
        email=f"evidence-api-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Evidence API Surveyor",
    )

    async_session.add(user)
    await async_session.flush()

    return user


async def create_test_survey(
    async_session,
    user_id,
):
    """
    Create a claim and survey owned by the specified user.
    """

    claim = Claim(
        user_id=user_id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    async_session.add(claim)
    await async_session.flush()

    survey = Survey(
        claim_id=claim.id,
        survey_number=f"SUR-{uuid4()}",
        status="draft",
        extra_data={},
    )

    async_session.add(survey)
    await async_session.flush()

    return survey


def evidence_payload():
    """
    Return valid evidence request data.
    """

    return {
        "evidence_type": "photo",
        "file_name": "vehicle-front.jpg",
        "storage_key": f"surveys/evidence/{uuid4()}.jpg",
        "content_type": "image/jpeg",
        "file_size": 1024,
        "file_hash": "a" * 64,
        "metadata_source": "exif",
        "processing_status": "uploaded",
        "extra_data": {
            "camera_make": "Test Camera",
        },
    }


def client():
    """
    Create an HTTP test client.
    """

    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


@pytest.mark.asyncio
async def test_create_evidence(
    async_session,
):
    """
    Verify that an authenticated surveyor can create
    evidence for their own survey.
    """

    user = await create_test_user(
        async_session,
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    app.dependency_overrides[get_db] = (
        lambda: async_session
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user
    )

    try:
        async with client() as http_client:
            response = await http_client.post(
                f"/api/v1/surveys/{survey.id}/evidence",
                json=evidence_payload(),
            )

        assert response.status_code == 201

        data = response.json()

        assert data["survey_id"] == str(survey.id)
        assert data["evidence_type"] == "photo"
        assert data["file_name"] == "vehicle-front.jpg"
        assert data["processing_status"] == "uploaded"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_survey_evidence(
    async_session,
):
    """
    Verify that a surveyor can retrieve evidence
    belonging to their survey.
    """

    user = await create_test_user(
        async_session,
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    app.dependency_overrides[get_db] = (
        lambda: async_session
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user
    )

    try:
        async with client() as http_client:
            create_response = await http_client.post(
                f"/api/v1/surveys/{survey.id}/evidence",
                json=evidence_payload(),
            )

            assert create_response.status_code == 201

            response = await http_client.get(
                f"/api/v1/surveys/{survey.id}/evidence",
            )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 1
        assert data[0]["survey_id"] == str(survey.id)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_evidence(
    async_session,
):
    """
    Verify that a surveyor can retrieve a specific
    evidence record.
    """

    user = await create_test_user(
        async_session,
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    app.dependency_overrides[get_db] = (
        lambda: async_session
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user
    )

    try:
        async with client() as http_client:
            create_response = await http_client.post(
                f"/api/v1/surveys/{survey.id}/evidence",
                json=evidence_payload(),
            )

            assert create_response.status_code == 201

            evidence_id = create_response.json()["id"]

            response = await http_client.get(
                f"/api/v1/surveys/evidence/{evidence_id}",
            )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == evidence_id
        assert data["survey_id"] == str(survey.id)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_evidence(
    async_session,
):
    """
    Verify that a surveyor can update their evidence.
    """

    user = await create_test_user(
        async_session,
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    app.dependency_overrides[get_db] = (
        lambda: async_session
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user
    )

    try:
        async with client() as http_client:
            create_response = await http_client.post(
                f"/api/v1/surveys/{survey.id}/evidence",
                json=evidence_payload(),
            )

            assert create_response.status_code == 201

            evidence_id = create_response.json()["id"]

            response = await http_client.patch(
                f"/api/v1/surveys/evidence/{evidence_id}",
                json={
                    "processing_status": "processed",
                    "extra_data": {
                        "ai_processed": True,
                    },
                },
            )

        assert response.status_code == 200

        data = response.json()

        assert data["processing_status"] == "processed"
        assert data["extra_data"]["ai_processed"] is True

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_evidence(
    async_session,
):
    """
    Verify that a surveyor can delete their evidence.
    """

    user = await create_test_user(
        async_session,
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    app.dependency_overrides[get_db] = (
        lambda: async_session
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user
    )

    try:
        async with client() as http_client:
            create_response = await http_client.post(
                f"/api/v1/surveys/{survey.id}/evidence",
                json=evidence_payload(),
            )

            assert create_response.status_code == 201

            evidence_id = create_response.json()["id"]

            response = await http_client.delete(
                f"/api/v1/surveys/evidence/{evidence_id}",
            )

        assert response.status_code == 204

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_evidence_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot create evidence
    for another surveyor's survey.
    """

    owner = await create_test_user(
        async_session,
    )

    other_user = await create_test_user(
        async_session,
    )

    survey = await create_test_survey(
        async_session,
        owner.id,
    )

    app.dependency_overrides[get_db] = (
        lambda: async_session
    )

    app.dependency_overrides[get_current_user] = (
        lambda: other_user
    )

    try:
        async with client() as http_client:
            response = await http_client.post(
                f"/api/v1/surveys/{survey.id}/evidence",
                json=evidence_payload(),
            )

        assert response.status_code == 404

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_evidence_requires_authentication():
    """
    Verify that evidence endpoints require authentication.
    """

    evidence_id = uuid4()

    async with client() as http_client:
        response = await http_client.get(
            f"/api/v1/surveys/evidence/{evidence_id}",
        )

    assert response.status_code == 401