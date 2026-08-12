"""
Tests for the Survey Evidence multipart upload API.
"""

from io import BytesIO
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
    Create a real surveyor for the API test.
    """

    user = User(
        email=f"evidence-upload-api-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Evidence Upload Surveyor",
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


def override_dependencies(
    async_session,
    user,
):
    """
    Override authentication and database dependencies
    for the API test.
    """

    async def override_get_db():
        yield async_session

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[
        get_current_user
    ] = override_get_current_user


def clear_dependencies():
    """
    Clear FastAPI dependency overrides.
    """

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_jpeg(
    async_session,
):
    """
    Verify that a JPEG can be uploaded through the API.
    """

    user = await create_test_user(
        async_session
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    override_dependencies(
        async_session,
        user,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.post(
                f"/api/v1/surveys/{survey.id}/evidence/upload",
                files={
                    "file": (
                        "vehicle-front.jpg",
                        BytesIO(b"fake jpeg content"),
                        "image/jpeg",
                    )
                },
            )

        assert response.status_code == 201

        data = response.json()

        assert data["survey_id"] == str(survey.id)
        assert data["file_name"] == "vehicle-front.jpg"
        assert data["content_type"] == "image/jpeg"
        assert data["file_size"] == len(
            b"fake jpeg content"
        )
        assert data["processing_status"] == "uploaded"
        assert data["file_hash"] is not None
        assert data["storage_key"] is not None

    finally:
        clear_dependencies()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename,content_type",
    [
        ("vehicle-front.jpg", "image/jpeg"),
        ("vehicle-side.png", "image/png"),
        ("vehicle-rear.webp", "image/webp"),
    ],
)
async def test_upload_supported_image_types(
    async_session,
    filename,
    content_type,
):
    """
    Verify that all supported image types can be uploaded.
    """

    user = await create_test_user(
        async_session
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    override_dependencies(
        async_session,
        user,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.post(
                f"/api/v1/surveys/{survey.id}/evidence/upload",
                files={
                    "file": (
                        filename,
                        BytesIO(b"test image"),
                        content_type,
                    )
                },
            )

        assert response.status_code == 201

    finally:
        clear_dependencies()


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_file_type(
    async_session,
):
    """
    Verify that unsupported file types are rejected.
    """

    user = await create_test_user(
        async_session
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    override_dependencies(
        async_session,
        user,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.post(
                f"/api/v1/surveys/{survey.id}/evidence/upload",
                files={
                    "file": (
                        "document.pdf",
                        BytesIO(b"pdf content"),
                        "application/pdf",
                    )
                },
            )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Unsupported evidence file type"
        )

    finally:
        clear_dependencies()


@pytest.mark.asyncio
async def test_upload_rejects_empty_file(
    async_session,
):
    """
    Verify that empty files are rejected.
    """

    user = await create_test_user(
        async_session
    )

    survey = await create_test_survey(
        async_session,
        user.id,
    )

    override_dependencies(
        async_session,
        user,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.post(
                f"/api/v1/surveys/{survey.id}/evidence/upload",
                files={
                    "file": (
                        "empty.jpg",
                        BytesIO(b""),
                        "image/jpeg",
                    )
                },
            )

        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Evidence file cannot be empty"
        )

    finally:
        clear_dependencies()


@pytest.mark.asyncio
async def test_upload_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot upload evidence
    to another surveyor's survey.
    """

    owner = await create_test_user(
        async_session
    )

    other_user = await create_test_user(
        async_session
    )

    survey = await create_test_survey(
        async_session,
        owner.id,
    )

    override_dependencies(
        async_session,
        other_user,
    )

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:

            response = await client.post(
                f"/api/v1/surveys/{survey.id}/evidence/upload",
                files={
                    "file": (
                        "unauthorized.jpg",
                        BytesIO(b"test image"),
                        "image/jpeg",
                    )
                },
            )

        assert response.status_code == 404

    finally:
        clear_dependencies()


@pytest.mark.asyncio
async def test_upload_requires_authentication():
    """
    Verify that the upload endpoint requires authentication.
    """

    survey_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            f"/api/v1/surveys/{survey_id}/evidence/upload",
            files={
                "file": (
                    "vehicle.jpg",
                    BytesIO(b"test image"),
                    "image/jpeg",
                )
            },
        )

    assert response.status_code == 401