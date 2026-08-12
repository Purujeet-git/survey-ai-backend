"""
Tests for Survey schemas.
"""

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.surveys.schemas.survey import (
    SurveyCreate,
    SurveyResponse,
    SurveyUpdate,
)


def test_survey_create_schema():
    """
    Verify that a valid SurveyCreate payload is accepted.
    """

    claim_id = uuid4()

    data = SurveyCreate(
        claim_id=claim_id,
        survey_number="SUR-001",
        survey_date=date(2026, 8, 12),
        survey_location="Patna",
        latitude=25.5941,
        longitude=85.1376,
        location_source="photo_exif",
        odometer_reading=45231,
        cause_of_accident="Rear-end collision",
        notes="Vehicle inspected at survey location.",
        status="draft",
        extra_data={
            "custom_field": "custom value",
        },
    )

    assert data.claim_id == claim_id
    assert data.survey_number == "SUR-001"
    assert data.survey_date == date(2026, 8, 12)
    assert data.survey_location == "Patna"
    assert data.latitude == 25.5941
    assert data.longitude == 85.1376
    assert data.location_source == "photo_exif"
    assert data.odometer_reading == 45231
    assert data.cause_of_accident == "Rear-end collision"
    assert data.status == "draft"
    assert data.extra_data["custom_field"] == "custom value"


def test_survey_create_defaults():
    """
    Verify defaults used when optional fields are omitted.
    """

    data = SurveyCreate(
        claim_id=uuid4(),
    )

    assert data.survey_number is None
    assert data.survey_date is None
    assert data.survey_location is None
    assert data.latitude is None
    assert data.longitude is None
    assert data.location_source is None
    assert data.odometer_reading is None
    assert data.cause_of_accident is None
    assert data.notes is None
    assert data.status == "draft"
    assert data.extra_data == {}


def test_survey_create_requires_claim_id():
    """
    Verify that claim_id is required when creating a survey.
    """

    with pytest.raises(ValidationError):
        SurveyCreate()


def test_survey_create_rejects_negative_odometer():
    """
    Verify that an odometer reading cannot be negative.
    """

    with pytest.raises(ValidationError):
        SurveyCreate(
            claim_id=uuid4(),
            odometer_reading=-1,
        )


def test_survey_update_schema():
    """
    Verify that a valid SurveyUpdate payload is accepted.
    """

    data = SurveyUpdate(
        survey_number="SUR-002",
        survey_date=date(2026, 8, 12),
        survey_location="Ranchi",
        latitude=23.3441,
        longitude=85.3096,
        location_source="manual",
        odometer_reading=50000,
        cause_of_accident="Front collision",
        notes="Updated notes",
        status="completed",
        extra_data={
            "damage_count": 4,
        },
    )

    assert data.survey_number == "SUR-002"
    assert data.status == "completed"
    assert data.odometer_reading == 50000
    assert data.extra_data["damage_count"] == 4


def test_survey_update_allows_partial_updates():
    """
    Verify that SurveyUpdate allows partial payloads.
    """

    data = SurveyUpdate(
        notes="Only notes updated.",
    )

    assert data.notes == "Only notes updated."
    assert data.survey_number is None
    assert data.status is None


def test_survey_update_rejects_negative_odometer():
    """
    Verify that an odometer reading cannot be negative.
    """

    with pytest.raises(ValidationError):
        SurveyUpdate(
            odometer_reading=-100,
        )


def test_survey_response_schema():
    """
    Verify that a complete SurveyResponse can be created.
    """

    survey_id = uuid4()
    claim_id = uuid4()

    now = datetime.now(timezone.utc)

    data = SurveyResponse(
        id=survey_id,
        claim_id=claim_id,
        survey_number="SUR-001",
        survey_date=date(2026, 8, 12),
        survey_location="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        location_source="photo_exif",
        odometer_reading=45000,
        cause_of_accident="Side collision",
        notes="Survey completed.",
        status="completed",
        extra_data={
            "template_field": "value",
        },
        created_at=now,
        updated_at=now,
    )

    assert data.id == survey_id
    assert data.claim_id == claim_id
    assert data.status == "completed"
    assert data.extra_data["template_field"] == "value"
    assert data.created_at == now
    assert data.updated_at == now


def test_survey_response_supports_optional_fields():
    """
    Verify that optional survey fields may be None.
    """

    now = datetime.now(timezone.utc)

    data = SurveyResponse(
        id=uuid4(),
        claim_id=uuid4(),
        survey_number=None,
        survey_date=None,
        survey_location=None,
        latitude=None,
        longitude=None,
        location_source=None,
        odometer_reading=None,
        cause_of_accident=None,
        notes=None,
        status="draft",
        extra_data={},
        created_at=now,
        updated_at=now,
    )

    assert data.survey_number is None
    assert data.survey_date is None
    assert data.latitude is None
    assert data.longitude is None
    assert data.odometer_reading is None