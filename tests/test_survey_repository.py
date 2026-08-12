"""
Tests for the Survey repository.
"""

from uuid import uuid4

import pytest

from app.claims.models.claim import Claim
from app.surveys.models.survey import Survey
from app.surveys.repositories.survey import SurveyRepository
from app.users.models.user import User


async def create_test_claim(async_session):
    """
    Create a real user and claim for survey repository tests.
    """

    user = User(
        email=f"survey-repository-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Survey Repository Surveyor",
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

    return claim


@pytest.mark.asyncio
async def test_create_survey(async_session):
    """
    Verify that a survey can be created.
    """

    claim = await create_test_claim(async_session)

    repository = SurveyRepository(async_session)

    survey = Survey(
        claim_id=claim.id,
        survey_number=f"SUR-{uuid4()}",
        status="draft",
        extra_data={},
    )

    created_survey = await repository.create(survey)

    assert created_survey is not None
    assert created_survey.id is not None
    assert created_survey.claim_id == claim.id
    assert created_survey.status == "draft"


@pytest.mark.asyncio
async def test_get_survey_by_id(async_session):
    """
    Verify that a survey can be retrieved by ID.
    """

    claim = await create_test_claim(async_session)

    repository = SurveyRepository(async_session)

    survey = Survey(
        claim_id=claim.id,
        survey_number=f"SUR-{uuid4()}",
        status="draft",
        extra_data={},
    )

    await repository.create(survey)

    retrieved_survey = await repository.get_by_id(
        survey.id
    )

    assert retrieved_survey is not None
    assert retrieved_survey.id == survey.id
    assert retrieved_survey.claim_id == claim.id


@pytest.mark.asyncio
async def test_get_survey_by_id_returns_none_for_missing_survey(
    async_session,
):
    """
    Verify that a nonexistent survey returns None.
    """

    repository = SurveyRepository(async_session)

    result = await repository.get_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_surveys_by_claim_id(async_session):
    """
    Verify that surveys belonging to a claim can be retrieved.
    """

    claim = await create_test_claim(async_session)

    repository = SurveyRepository(async_session)

    first_survey = Survey(
        claim_id=claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    second_survey = Survey(
        claim_id=claim.id,
        survey_number="SUR-002",
        status="completed",
        extra_data={},
    )

    async_session.add_all([
        first_survey,
        second_survey,
    ])

    await async_session.flush()

    surveys = await repository.get_by_claim_id(
        claim.id
    )

    assert len(surveys) == 2

    survey_ids = {survey.id for survey in surveys}

    assert first_survey.id in survey_ids
    assert second_survey.id in survey_ids


@pytest.mark.asyncio
async def test_get_surveys_by_claim_id_returns_empty_for_missing_claim(
    async_session,
):
    """
    Verify that no surveys are returned for a claim
    with no surveys.
    """

    repository = SurveyRepository(async_session)

    surveys = await repository.get_by_claim_id(
        uuid4()
    )

    assert surveys == []


@pytest.mark.asyncio
async def test_update_survey(async_session):
    """
    Verify that an existing survey can be updated.
    """

    claim = await create_test_claim(async_session)

    repository = SurveyRepository(async_session)

    survey = Survey(
        claim_id=claim.id,
        survey_number="SUR-001",
        status="draft",
        notes="Initial notes",
        extra_data={},
    )

    await repository.create(survey)

    survey.status = "completed"
    survey.notes = "Updated survey notes"

    updated_survey = await repository.update(survey)

    assert updated_survey.status == "completed"
    assert updated_survey.notes == "Updated survey notes"


@pytest.mark.asyncio
async def test_delete_survey(async_session):
    """
    Verify that an existing survey can be deleted.
    """

    claim = await create_test_claim(async_session)

    repository = SurveyRepository(async_session)

    survey = Survey(
        claim_id=claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    await repository.create(survey)

    survey_id = survey.id

    await repository.delete(survey)

    deleted_survey = await repository.get_by_id(
        survey_id
    )

    assert deleted_survey is None