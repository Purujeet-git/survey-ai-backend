"""
Tests for Survey Evidence schemas.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.surveys.schemas.evidence import (
    SurveyEvidenceCreate,
    SurveyEvidenceResponse,
    SurveyEvidenceUpdate,
)


def valid_create_data() -> dict:
    """
    Return valid data for SurveyEvidenceCreate.
    """

    return {
        "survey_id": uuid4(),
        "evidence_type": "photo",
        "file_name": "vehicle-front.jpg",
        "storage_key": "surveys/test/evidence/front.jpg",
        "content_type": "image/jpeg",
        "file_size": 1024,
        "file_hash": "a" * 64,
        "captured_at": datetime.now(timezone.utc),
        "latitude": 25.5941,
        "longitude": 85.1376,
        "metadata_source": "exif",
        "processing_status": "uploaded",
        "extra_data": {
            "camera_make": "Test Camera",
        },
    }


def test_create_schema_accepts_valid_data():
    """
    Verify that valid evidence data is accepted.
    """

    data = SurveyEvidenceCreate(
        **valid_create_data()
    )

    assert data.evidence_type == "photo"
    assert data.file_name == "vehicle-front.jpg"
    assert data.content_type == "image/jpeg"
    assert data.file_size == 1024
    assert data.extra_data["camera_make"] == "Test Camera"


def test_create_schema_has_correct_defaults():
    """
    Verify default values for evidence creation.
    """

    data = SurveyEvidenceCreate(
        survey_id=uuid4(),
        file_name="front.jpg",
        storage_key="surveys/test/front.jpg",
        content_type="image/jpeg",
        file_size=100,
    )

    assert data.evidence_type == "photo"
    assert data.processing_status == "uploaded"
    assert data.extra_data == {}


def test_create_schema_rejects_negative_file_size():
    """
    Verify that negative file sizes are rejected.
    """

    data = valid_create_data()
    data["file_size"] = -1

    with pytest.raises(ValidationError):
        SurveyEvidenceCreate(**data)


def test_create_schema_rejects_invalid_file_hash():
    """
    Verify that file hashes must contain exactly 64 characters.
    """

    data = valid_create_data()
    data["file_hash"] = "invalid-hash"

    with pytest.raises(ValidationError):
        SurveyEvidenceCreate(**data)


def test_create_schema_accepts_null_optional_fields():
    """
    Verify that optional metadata fields may be omitted or null.
    """

    data = SurveyEvidenceCreate(
        survey_id=uuid4(),
        file_name="front.jpg",
        storage_key="surveys/test/front.jpg",
        content_type="image/jpeg",
        file_size=100,
        file_hash=None,
        captured_at=None,
        latitude=None,
        longitude=None,
        metadata_source=None,
        processing_error=None,
    )

    assert data.file_hash is None
    assert data.captured_at is None
    assert data.latitude is None
    assert data.longitude is None
    assert data.metadata_source is None


def test_update_schema_accepts_partial_updates():
    """
    Verify that evidence can be partially updated.
    """

    data = SurveyEvidenceUpdate(
        processing_status="processed",
        processing_error=None,
        extra_data={
            "ai_processed": True,
        },
    )

    assert data.processing_status == "processed"
    assert data.extra_data["ai_processed"] is True


def test_update_schema_allows_empty_update():
    """
    Verify that an empty update payload is valid.
    """

    data = SurveyEvidenceUpdate()

    assert data.model_dump(exclude_unset=True) == {}


def test_update_schema_rejects_negative_file_size():
    """
    Verify that negative file sizes are rejected during updates.
    """

    with pytest.raises(ValidationError):
        SurveyEvidenceUpdate(
            file_size=-100,
        )

def test_response_schema_from_attributes():
    """
    Verify that the response schema can be created from
    ORM-style attributes.
    """

    evidence_id = uuid4()
    survey_id = uuid4()
    now = datetime.now(timezone.utc)

    class EvidenceObject:
        pass

    evidence = EvidenceObject()

    evidence.id = evidence_id
    evidence.survey_id = survey_id
    evidence.evidence_type = "photo"
    evidence.file_name = "front.jpg"
    evidence.storage_key = "surveys/test/front.jpg"
    evidence.content_type = "image/jpeg"
    evidence.file_size = 2048
    evidence.file_hash = "b" * 64
    evidence.captured_at = now
    evidence.latitude = 25.5941
    evidence.longitude = 85.1376
    evidence.metadata_source = "exif"
    evidence.processing_status = "processed"
    evidence.processing_error = None
    evidence.extra_data = {
        "ai_processed": True,
    }
    evidence.created_at = now
    evidence.updated_at = now

    response = SurveyEvidenceResponse.model_validate(
        evidence
    )

    assert response.id == evidence_id
    assert response.survey_id == survey_id
    assert response.evidence_type == "photo"
    assert response.processing_status == "processed"
    assert response.extra_data["ai_processed"] is True