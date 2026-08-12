"""
Tests for the Survey Evidence repository.
"""

from uuid import uuid4

import pytest

from app.claims.models.claim import Claim
from app.surveys.models.evidence import SurveyEvidence
from app.surveys.models.survey import Survey
from app.surveys.repositories.evidence import SurveyEvidenceRepository
from app.users.models.user import User


async def create_test_survey(async_session):
    """
    Create a real user, claim, and survey for evidence tests.
    """

    user = User(
        email=f"evidence-repo-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Evidence Repository Surveyor",
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


def create_test_evidence(survey_id):
    """
    Create an unsaved SurveyEvidence instance.
    """

    return SurveyEvidence(
        survey_id=survey_id,
        evidence_type="photo",
        file_name="vehicle-front.jpg",
        storage_key=f"surveys/{survey_id}/evidence/{uuid4()}.jpg",
        content_type="image/jpeg",
        file_size=1024,
        file_hash="a" * 64,
        metadata_source="exif",
        processing_status="uploaded",
        extra_data={
            "camera_make": "Test Camera",
        },
    )


@pytest.mark.asyncio
async def test_create_evidence(async_session):
    """
    Verify that survey evidence can be created.
    """

    _, _, survey = await create_test_survey(async_session)

    repository = SurveyEvidenceRepository(async_session)

    evidence = create_test_evidence(survey.id)

    created = await repository.create(evidence)

    assert created is not None
    assert created.id is not None
    assert created.survey_id == survey.id
    assert created.file_name == "vehicle-front.jpg"
    assert created.evidence_type == "photo"
    assert created.processing_status == "uploaded"


@pytest.mark.asyncio
async def test_get_evidence_by_id(async_session):
    """
    Verify that evidence can be retrieved by ID.
    """

    _, _, survey = await create_test_survey(async_session)

    repository = SurveyEvidenceRepository(async_session)

    evidence = create_test_evidence(survey.id)

    created = await repository.create(evidence)

    retrieved = await repository.get_by_id(
        created.id,
    )

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.survey_id == survey.id


@pytest.mark.asyncio
async def test_get_evidence_by_id_returns_none_for_missing_evidence(
    async_session,
):
    """
    Verify that retrieving a nonexistent evidence record
    returns None.
    """

    repository = SurveyEvidenceRepository(async_session)

    evidence = await repository.get_by_id(uuid4())

    assert evidence is None


@pytest.mark.asyncio
async def test_get_evidence_by_survey_id(async_session):
    """
    Verify that all evidence belonging to a survey can be retrieved.
    """

    _, _, survey = await create_test_survey(async_session)

    repository = SurveyEvidenceRepository(async_session)

    first = create_test_evidence(survey.id)

    second = SurveyEvidence(
        survey_id=survey.id,
        evidence_type="photo",
        file_name="vehicle-rear.jpg",
        storage_key=f"surveys/{survey.id}/evidence/{uuid4()}.jpg",
        content_type="image/jpeg",
        file_size=2048,
        processing_status="uploaded",
        extra_data={},
    )

    await repository.create(first)
    await repository.create(second)

    evidence_list = await repository.get_by_survey_id(
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
async def test_get_evidence_by_survey_id_does_not_return_other_surveys(
    async_session,
):
    """
    Verify that evidence retrieval is scoped to the requested survey.
    """

    _, _, first_survey = await create_test_survey(
        async_session,
    )

    _, _, second_survey = await create_test_survey(
        async_session,
    )

    repository = SurveyEvidenceRepository(async_session)

    first_evidence = create_test_evidence(
        first_survey.id,
    )

    second_evidence = create_test_evidence(
        second_survey.id,
    )

    await repository.create(first_evidence)
    await repository.create(second_evidence)

    evidence_list = await repository.get_by_survey_id(
        first_survey.id,
    )

    assert len(evidence_list) == 1
    assert evidence_list[0].id == first_evidence.id


@pytest.mark.asyncio
async def test_update_evidence(async_session):
    """
    Verify that evidence metadata can be updated.
    """

    _, _, survey = await create_test_survey(async_session)

    repository = SurveyEvidenceRepository(async_session)

    evidence = create_test_evidence(survey.id)

    created = await repository.create(evidence)

    created.processing_status = "processed"
    created.processing_error = None
    created.extra_data = {
        "camera_make": "Test Camera",
        "ai_processed": True,
    }

    updated = await repository.update(created)

    assert updated.processing_status == "processed"
    assert updated.processing_error is None
    assert updated.extra_data["ai_processed"] is True


@pytest.mark.asyncio
async def test_delete_evidence(async_session):
    """
    Verify that evidence can be deleted.
    """

    _, _, survey = await create_test_survey(async_session)

    repository = SurveyEvidenceRepository(async_session)

    evidence = create_test_evidence(survey.id)

    created = await repository.create(evidence)

    evidence_id = created.id

    await repository.delete(created)

    deleted = await repository.get_by_id(
        evidence_id,
    )

    assert deleted is None