"""
Tests for the EvidenceAnalysis repository.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio

from app.surveys.models.evidence import SurveyEvidence
from app.surveys.models.evidence_analysis import EvidenceAnalysis
from app.surveys.models.survey import Survey
from app.claims.models.claim import Claim
from app.users.models.user import User
from app.surveys.repositories.evidence_analysis import (
    EvidenceAnalysisRepository,
)


@pytest_asyncio.fixture
async def evidence(async_session):
    """
    Create a complete User -> Claim -> Survey ->
    SurveyEvidence hierarchy for repository tests.
    """

    user = User(
        email=f"test-evidence-{uuid4()}@example.com",
        password_hash="test-hash",
        full_name="Evidence Test User",
    )


    async_session.add(user)
    await async_session.flush()

    claim = Claim(
        user_id=user.id,
        claim_number=f"TEST-{uuid4()}",
        status="created",
        extra_data={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    async_session.add(claim)
    await async_session.flush()

    survey = Survey(
        claim_id=claim.id,
        status="draft",
        extra_data={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    async_session.add(survey)
    await async_session.flush()

    evidence = SurveyEvidence(
        survey_id=survey.id,
        evidence_type="photo",
        file_name="test.jpg",
        storage_key=f"test/{uuid4()}.jpg",
        content_type="image/jpeg",
        file_size=1024,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    async_session.add(evidence)
    await async_session.flush()

    return evidence


@pytest.mark.asyncio
async def test_create_analysis(
    async_session,
    evidence,
):
    """
    Verify that an evidence analysis can be created.
    """

    repository = EvidenceAnalysisRepository(async_session)

    analysis = EvidenceAnalysis(
        evidence_id=evidence.id,
        analysis_type="vehicle_damage",
        provider="gemini",
        model="gemini-model",
        status="pending",
        result={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    created = await repository.create(analysis)

    assert created.id is not None
    assert created.evidence_id == evidence.id
    assert created.analysis_type == "vehicle_damage"
    assert created.provider == "gemini"

    await async_session.rollback()


@pytest.mark.asyncio
async def test_get_by_id(
    async_session,
    evidence,
):
    """
    Verify that an evidence analysis can be retrieved by ID.
    """

    repository = EvidenceAnalysisRepository(async_session)

    analysis = EvidenceAnalysis(
        evidence_id=evidence.id,
        analysis_type="vehicle_damage",
        status="completed",
        result={
            "severity": "moderate",
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await repository.create(analysis)

    analysis_id = analysis.id

    result = await repository.get_by_id(analysis_id)

    assert result is not None
    assert result.id == analysis_id
    assert result.evidence_id == evidence.id
    assert result.result["severity"] == "moderate"

    await async_session.rollback()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_missing_analysis(
    async_session,
):
    """
    Verify that get_by_id returns None for an unknown ID.
    """

    repository = EvidenceAnalysisRepository(async_session)

    result = await repository.get_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_by_evidence_id(
    async_session,
    evidence,
):
    """
    Verify that all analyses belonging to an evidence item
    can be retrieved.
    """

    repository = EvidenceAnalysisRepository(async_session)

    first = EvidenceAnalysis(
        evidence_id=evidence.id,
        analysis_type="vehicle_damage",
        status="completed",
        result={
            "severity": "minor",
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    second = EvidenceAnalysis(
        evidence_id=evidence.id,
        analysis_type="general_observation",
        status="completed",
        result={
            "vehicle_visible": True,
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await repository.create(first)
    await repository.create(second)

    results = await repository.get_by_evidence_id(
        evidence.id
    )

    assert len(results) == 2

    analysis_types = {
        analysis.analysis_type
        for analysis in results
    }

    assert analysis_types == {
        "vehicle_damage",
        "general_observation",
    }

    await async_session.rollback()


@pytest.mark.asyncio
async def test_get_by_evidence_id_returns_empty_list(
    async_session,
):
    """
    Verify that no analyses returns an empty list.
    """

    repository = EvidenceAnalysisRepository(async_session)

    results = await repository.get_by_evidence_id(
        uuid4()
    )

    assert results == []


@pytest.mark.asyncio
async def test_update_analysis(
    async_session,
    evidence,
):
    """
    Verify that an existing analysis can be updated.
    """

    repository = EvidenceAnalysisRepository(async_session)

    analysis = EvidenceAnalysis(
        evidence_id=evidence.id,
        analysis_type="vehicle_damage",
        status="pending",
        result={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await repository.create(analysis)

    analysis.status = "completed"
    analysis.result = {
        "damage_type": "dent",
        "severity": "moderate",
    }
    analysis.confidence = 0.91
    analysis.updated_at = datetime.now(timezone.utc)

    updated = await repository.update(analysis)

    assert updated.status == "completed"
    assert updated.result["damage_type"] == "dent"
    assert updated.confidence == 0.91

    await async_session.rollback()


@pytest.mark.asyncio
async def test_delete_analysis(
    async_session,
    evidence,
):
    """
    Verify that an evidence analysis can be deleted.
    """

    repository = EvidenceAnalysisRepository(async_session)

    analysis = EvidenceAnalysis(
        evidence_id=evidence.id,
        analysis_type="vehicle_damage",
        status="completed",
        result={
            "severity": "minor",
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    await repository.create(analysis)

    analysis_id = analysis.id

    await repository.delete(analysis)

    result = await repository.get_by_id(
        analysis_id
    )

    assert result is None

    await async_session.rollback()