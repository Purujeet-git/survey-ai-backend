"""
Tests for Evidence Analysis schemas.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.surveys.schemas.evidence_analysis import (
    EvidenceAnalysisCreate,
    EvidenceAnalysisResponse,
    EvidenceAnalysisUpdate,
)


def test_create_schema_accepts_valid_data():
    """
    Verify that valid evidence analysis data is accepted.
    """

    evidence_id = uuid4()

    schema = EvidenceAnalysisCreate(
        evidence_id=evidence_id,
        analysis_type="vehicle_damage",
        provider="gemini",
        model="gemini-model",
        status="pending",
        prompt_version="v1",
        result={
            "vehicle_part": "front_bumper",
            "damage_type": "dent",
        },
        confidence=0.91,
        error=None,
    )

    assert schema.evidence_id == evidence_id
    assert schema.analysis_type == "vehicle_damage"
    assert schema.provider == "gemini"
    assert schema.model == "gemini-model"
    assert schema.status == "pending"
    assert schema.prompt_version == "v1"
    assert schema.result["vehicle_part"] == "front_bumper"
    assert schema.confidence == 0.91
    assert schema.error is None


def test_create_schema_has_correct_defaults():
    """
    Verify defaults for a new evidence analysis.
    """

    schema = EvidenceAnalysisCreate(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
    )

    assert schema.status == "pending"
    assert schema.result == {}
    assert schema.provider is None
    assert schema.model is None
    assert schema.prompt_version is None
    assert schema.confidence is None
    assert schema.error is None


def test_create_schema_rejects_empty_analysis_type():
    """
    Verify analysis_type cannot be empty.
    """

    with pytest.raises(ValidationError):
        EvidenceAnalysisCreate(
            evidence_id=uuid4(),
            analysis_type="",
        )


def test_create_schema_rejects_invalid_confidence():
    """
    Verify confidence must remain between 0 and 1.
    """

    with pytest.raises(ValidationError):
        EvidenceAnalysisCreate(
            evidence_id=uuid4(),
            analysis_type="vehicle_damage",
            confidence=1.5,
        )

    with pytest.raises(ValidationError):
        EvidenceAnalysisCreate(
            evidence_id=uuid4(),
            analysis_type="vehicle_damage",
            confidence=-0.1,
        )


def test_create_schema_accepts_confidence_boundaries():
    """
    Verify 0 and 1 are valid confidence values.
    """

    lower = EvidenceAnalysisCreate(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        confidence=0.0,
    )

    upper = EvidenceAnalysisCreate(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        confidence=1.0,
    )

    assert lower.confidence == 0.0
    assert upper.confidence == 1.0


def test_create_schema_accepts_null_optional_fields():
    """
    Verify nullable fields can explicitly be set to None.
    """

    schema = EvidenceAnalysisCreate(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        provider=None,
        model=None,
        prompt_version=None,
        confidence=None,
        error=None,
    )

    assert schema.provider is None
    assert schema.model is None
    assert schema.prompt_version is None
    assert schema.confidence is None
    assert schema.error is None


def test_update_schema_accepts_partial_updates():
    """
    Verify that individual fields can be updated independently.
    """

    schema = EvidenceAnalysisUpdate(
        status="completed",
        confidence=0.95,
    )

    assert schema.status == "completed"
    assert schema.confidence == 0.95
    assert schema.analysis_type is None
    assert schema.provider is None


def test_update_schema_allows_empty_update():
    """
    Verify that an empty update schema is valid.
    """

    schema = EvidenceAnalysisUpdate()

    assert schema.model_dump(exclude_unset=True) == {}


def test_update_schema_rejects_invalid_confidence():
    """
    Verify update confidence validation.
    """

    with pytest.raises(ValidationError):
        EvidenceAnalysisUpdate(
            confidence=2.0,
        )

    with pytest.raises(ValidationError):
        EvidenceAnalysisUpdate(
            confidence=-0.5,
        )

def test_response_schema_from_attributes():
    """
    Verify that the response schema can be created from
    ORM-style attributes.
    """

    from datetime import datetime, timezone

    analysis_id = uuid4()
    evidence_uuid = uuid4()

    created_timestamp = datetime.now(timezone.utc)
    updated_timestamp = datetime.now(timezone.utc)

    class AnalysisObject:
        def __init__(self):
            self.id = analysis_id
            self.evidence_id = evidence_uuid
            self.analysis_type = "vehicle_damage"
            self.provider = "gemini"
            self.model = "gemini-model"
            self.status = "completed"
            self.prompt_version = "v1"
            self.result = {
                "vehicle_part": "front_bumper",
                "severity": "moderate",
            }
            self.confidence = 0.91
            self.error = None
            self.created_at = created_timestamp
            self.updated_at = updated_timestamp

    schema = EvidenceAnalysisResponse.model_validate(
        AnalysisObject()
    )

    assert schema.id == analysis_id
    assert schema.evidence_id == evidence_uuid
    assert schema.analysis_type == "vehicle_damage"
    assert schema.provider == "gemini"
    assert schema.model == "gemini-model"
    assert schema.status == "completed"
    assert schema.prompt_version == "v1"
    assert schema.result["severity"] == "moderate"
    assert schema.confidence == 0.91
    assert schema.error is None
    assert schema.created_at == created_timestamp
    assert schema.updated_at == updated_timestamp