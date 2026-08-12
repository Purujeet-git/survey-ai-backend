"""
Tests for the Survey Evidence service.
"""

from uuid import uuid4

import pytest

from app.claims.models.claim import Claim
from app.shared.exceptions import NotFoundError
from app.surveys.models.evidence import SurveyEvidence
from app.surveys.models.survey import Survey
from app.surveys.services.evidence import SurveyEvidenceService
from app.users.models.user import User


async def create_test_survey(async_session):
    """
    Create a real user, claim, and survey for evidence tests.
    """

    user = User(
        email=f"evidence-service-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Evidence Service Surveyor",
    )

    async_session.add(user)
    await async_session.flush()

    claim = Claim(
        user_id=user.id,
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

    return user, claim, survey


def evidence_data():
    """
    Return valid test evidence data.
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


@pytest.mark.asyncio
async def test_create_evidence(async_session):
    """
    Verify that a surveyor can create evidence for
    their own survey.
    """

    user, _, survey = await create_test_survey(
        async_session
    )

    service = SurveyEvidenceService(async_session)

    evidence = await service.create_evidence(
        user.id,
        survey.id,
        **evidence_data(),
    )

    assert evidence is not None
    assert evidence.survey_id == survey.id
    assert evidence.evidence_type == "photo"
    assert evidence.file_name == "vehicle-front.jpg"
    assert evidence.processing_status == "uploaded"


@pytest.mark.asyncio
async def test_create_evidence_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot create evidence
    for another surveyor's survey.
    """

    owner, _, survey = await create_test_survey(
        async_session
    )

    other_user = User(
        email=f"other-evidence-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Other Surveyor",
    )

    async_session.add(other_user)
    await async_session.flush()

    service = SurveyEvidenceService(async_session)

    with pytest.raises(NotFoundError):
        await service.create_evidence(
            other_user.id,
            survey.id,
            **evidence_data(),
        )


@pytest.mark.asyncio
async def test_get_evidence(async_session):
    """
    Verify that a surveyor can retrieve their own evidence.
    """

    user, _, survey = await create_test_survey(
        async_session
    )

    service = SurveyEvidenceService(async_session)

    evidence = await service.create_evidence(
        user.id,
        survey.id,
        **evidence_data(),
    )

    retrieved = await service.get_evidence(
        user.id,
        evidence.id,
    )

    assert retrieved.id == evidence.id
    assert retrieved.survey_id == survey.id


@pytest.mark.asyncio
async def test_get_evidence_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot retrieve another
    surveyor's evidence.
    """

    owner, _, survey = await create_test_survey(
        async_session
    )

    other_user = User(
        email=f"other-get-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Other Surveyor",
    )

    async_session.add(other_user)
    await async_session.flush()

    service = SurveyEvidenceService(async_session)

    evidence = await service.create_evidence(
        owner.id,
        survey.id,
        **evidence_data(),
    )

    with pytest.raises(NotFoundError):
        await service.get_evidence(
            other_user.id,
            evidence.id,
        )


@pytest.mark.asyncio
async def test_get_survey_evidence(async_session):
    """
    Verify that a surveyor can retrieve all evidence
    belonging to their survey.
    """

    user, _, survey = await create_test_survey(
        async_session
    )

    service = SurveyEvidenceService(async_session)

    first = await service.create_evidence(
        user.id,
        survey.id,
        **evidence_data(),
    )

    second_data = evidence_data()
    second_data["file_name"] = "vehicle-rear.jpg"

    second = await service.create_evidence(
        user.id,
        survey.id,
        **second_data,
    )

    evidence_list = await service.get_survey_evidence(
        user.id,
        survey.id,
    )

    assert len(evidence_list) == 2

    evidence_ids = {
        evidence.id
        for evidence in evidence_list
    }

    assert first.id in evidence_ids
    assert second.id in evidence_ids


@pytest.mark.asyncio
async def test_get_survey_evidence_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot list evidence from
    another surveyor's survey.
    """

    owner, _, survey = await create_test_survey(
        async_session
    )

    other_user = User(
        email=f"other-list-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Other Surveyor",
    )

    async_session.add(other_user)
    await async_session.flush()

    service = SurveyEvidenceService(async_session)

    await service.create_evidence(
        owner.id,
        survey.id,
        **evidence_data(),
    )

    with pytest.raises(NotFoundError):
        await service.get_survey_evidence(
            other_user.id,
            survey.id,
        )


@pytest.mark.asyncio
async def test_update_evidence(async_session):
    """
    Verify that a surveyor can update their own evidence.
    """

    user, _, survey = await create_test_survey(
        async_session
    )

    service = SurveyEvidenceService(async_session)

    evidence = await service.create_evidence(
        user.id,
        survey.id,
        **evidence_data(),
    )

    updated = await service.update_evidence(
        user.id,
        evidence.id,
        processing_status="processed",
        extra_data={
            "camera_make": "Test Camera",
            "ai_processed": True,
        },
    )

    assert updated.processing_status == "processed"
    assert updated.extra_data["ai_processed"] is True


@pytest.mark.asyncio
async def test_update_evidence_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot update another
    surveyor's evidence.
    """

    owner, _, survey = await create_test_survey(
        async_session
    )

    other_user = User(
        email=f"other-update-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Other Surveyor",
    )

    async_session.add(other_user)
    await async_session.flush()

    service = SurveyEvidenceService(async_session)

    evidence = await service.create_evidence(
        owner.id,
        survey.id,
        **evidence_data(),
    )

    with pytest.raises(NotFoundError):
        await service.update_evidence(
            other_user.id,
            evidence.id,
            processing_status="processed",
        )


@pytest.mark.asyncio
async def test_delete_evidence(async_session):
    """
    Verify that a surveyor can delete their own evidence.
    """

    user, _, survey = await create_test_survey(
        async_session
    )

    service = SurveyEvidenceService(async_session)

    evidence = await service.create_evidence(
        user.id,
        survey.id,
        **evidence_data(),
    )

    await service.delete_evidence(
        user.id,
        evidence.id,
    )

    with pytest.raises(NotFoundError):
        await service.get_evidence(
            user.id,
            evidence.id,
        )


@pytest.mark.asyncio
async def test_delete_evidence_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot delete another
    surveyor's evidence.
    """

    owner, _, survey = await create_test_survey(
        async_session
    )

    other_user = User(
        email=f"other-delete-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Other Surveyor",
    )

    async_session.add(other_user)
    await async_session.flush()

    service = SurveyEvidenceService(async_session)

    evidence = await service.create_evidence(
        owner.id,
        survey.id,
        **evidence_data(),
    )

    with pytest.raises(NotFoundError):
        await service.delete_evidence(
            other_user.id,
            evidence.id,
        )