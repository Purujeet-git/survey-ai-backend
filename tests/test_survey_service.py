"""
Tests for the Survey service.
"""

from uuid import uuid4

import pytest

from app.claims.models.claim import Claim
from app.shared.exceptions import NotFoundError
from app.surveys.models.survey import Survey
from app.surveys.services.survey import SurveyService
from app.users.models.user import User


async def create_test_user(
    async_session,
    name: str = "Survey Service Surveyor",
):
    """
    Create a real user for survey service tests.
    """

    user = User(
        email=f"survey-service-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name=name,
    )

    async_session.add(user)
    await async_session.flush()

    return user


async def create_test_claim(
    async_session,
    user: User,
):
    """
    Create a real claim belonging to the supplied user.
    """

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
    Verify that a survey can be created for the
    surveyor's own claim.
    """

    user = await create_test_user(async_session)
    claim = await create_test_claim(
        async_session,
        user,
    )

    service = SurveyService(async_session)

    survey = await service.create_survey(
        user.id,
        claim.id,
        survey_number=f"SUR-{uuid4()}",
        status="draft",
        extra_data={},
    )

    assert survey is not None
    assert survey.claim_id == claim.id
    assert survey.status == "draft"


@pytest.mark.asyncio
async def test_create_survey_rejects_other_users_claim(
    async_session,
):
    """
    Verify that a survey cannot be created for
    another surveyor's claim.
    """

    owner = await create_test_user(
        async_session,
        "Claim Owner",
    )

    other_user = await create_test_user(
        async_session,
        "Other Surveyor",
    )

    claim = await create_test_claim(
        async_session,
        owner,
    )

    service = SurveyService(async_session)

    with pytest.raises(NotFoundError):
        await service.create_survey(
            other_user.id,
            claim.id,
            survey_number=f"SUR-{uuid4()}",
            status="draft",
            extra_data={},
        )


@pytest.mark.asyncio
async def test_get_survey(async_session):
    """
    Verify that a survey can be retrieved by its owner.
    """

    user = await create_test_user(async_session)
    claim = await create_test_claim(
        async_session,
        user,
    )

    service = SurveyService(async_session)

    survey = await service.create_survey(
        user.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    retrieved_survey = await service.get_survey(
        user.id,
        survey.id,
    )

    assert retrieved_survey.id == survey.id
    assert retrieved_survey.claim_id == claim.id


@pytest.mark.asyncio
async def test_get_survey_rejects_wrong_user(
    async_session,
):
    """
    Verify that a survey cannot be accessed by
    another surveyor.
    """

    owner = await create_test_user(
        async_session,
        "Survey Owner",
    )

    other_user = await create_test_user(
        async_session,
        "Other Surveyor",
    )

    claim = await create_test_claim(
        async_session,
        owner,
    )

    service = SurveyService(async_session)

    survey = await service.create_survey(
        owner.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    with pytest.raises(NotFoundError):
        await service.get_survey(
            other_user.id,
            survey.id,
        )


@pytest.mark.asyncio
async def test_get_claim_surveys(async_session):
    """
    Verify that all surveys belonging to the
    surveyor's claim can be retrieved.
    """

    user = await create_test_user(async_session)
    claim = await create_test_claim(
        async_session,
        user,
    )

    service = SurveyService(async_session)

    first_survey = await service.create_survey(
        user.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    second_survey = await service.create_survey(
        user.id,
        claim.id,
        survey_number="SUR-002",
        status="completed",
        extra_data={},
    )

    surveys = await service.get_claim_surveys(
        user.id,
        claim.id,
    )

    assert len(surveys) == 2

    survey_ids = {survey.id for survey in surveys}

    assert first_survey.id in survey_ids
    assert second_survey.id in survey_ids


@pytest.mark.asyncio
async def test_get_claim_surveys_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot list surveys belonging
    to another surveyor's claim.
    """

    owner = await create_test_user(
        async_session,
        "Claim Owner",
    )

    other_user = await create_test_user(
        async_session,
        "Other Surveyor",
    )

    claim = await create_test_claim(
        async_session,
        owner,
    )

    service = SurveyService(async_session)

    await service.create_survey(
        owner.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    with pytest.raises(NotFoundError):
        await service.get_claim_surveys(
            other_user.id,
            claim.id,
        )


@pytest.mark.asyncio
async def test_update_survey(async_session):
    """
    Verify that a surveyor can update their own survey.
    """

    user = await create_test_user(async_session)
    claim = await create_test_claim(
        async_session,
        user,
    )

    service = SurveyService(async_session)

    survey = await service.create_survey(
        user.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        notes="Initial survey",
        extra_data={},
    )

    updated_survey = await service.update_survey(
        user.id,
        survey.id,
        status="completed",
        notes="Survey completed",
    )

    assert updated_survey.status == "completed"
    assert updated_survey.notes == "Survey completed"


@pytest.mark.asyncio
async def test_update_survey_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot update another
    surveyor's survey.
    """

    owner = await create_test_user(
        async_session,
        "Survey Owner",
    )

    other_user = await create_test_user(
        async_session,
        "Other Surveyor",
    )

    claim = await create_test_claim(
        async_session,
        owner,
    )

    service = SurveyService(async_session)

    survey = await service.create_survey(
        owner.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    with pytest.raises(NotFoundError):
        await service.update_survey(
            other_user.id,
            survey.id,
            notes="Unauthorized update",
        )


@pytest.mark.asyncio
async def test_delete_survey(async_session):
    """
    Verify that a surveyor can delete their own survey.
    """

    user = await create_test_user(async_session)
    claim = await create_test_claim(
        async_session,
        user,
    )

    service = SurveyService(async_session)

    survey = await service.create_survey(
        user.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    await service.delete_survey(
        user.id,
        survey.id,
    )

    with pytest.raises(NotFoundError):
        await service.get_survey(
            user.id,
            survey.id,
        )


@pytest.mark.asyncio
async def test_delete_survey_rejects_wrong_user(
    async_session,
):
    """
    Verify that a surveyor cannot delete another
    surveyor's survey.
    """

    owner = await create_test_user(
        async_session,
        "Survey Owner",
    )

    other_user = await create_test_user(
        async_session,
        "Other Surveyor",
    )

    claim = await create_test_claim(
        async_session,
        owner,
    )

    service = SurveyService(async_session)

    survey = await service.create_survey(
        owner.id,
        claim.id,
        survey_number="SUR-001",
        status="draft",
        extra_data={},
    )

    with pytest.raises(NotFoundError):
        await service.delete_survey(
            other_user.id,
            survey.id,
        )