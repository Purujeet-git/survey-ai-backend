"""
Tests for the EvidenceAnalysis model.
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.surveys.models.evidence_analysis import EvidenceAnalysis


def test_evidence_analysis_model_can_be_created():
    """
    Verify that an EvidenceAnalysis instance can be created
    with the required fields.
    """

    evidence_id = uuid4()

    analysis = EvidenceAnalysis(
        evidence_id=evidence_id,
        analysis_type="vehicle_damage",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.id is None
    assert analysis.evidence_id == evidence_id
    assert analysis.analysis_type == "vehicle_damage"


def test_evidence_analysis_accepts_provider_and_model():
    """
    Verify provider and model information can be stored.
    """

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        provider="gemini",
        model="gemini-model",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.provider == "gemini"
    assert analysis.model == "gemini-model"


def test_evidence_analysis_status_can_be_set_to_pending():
    """
    Verify that an analysis can explicitly use the pending status.
    """

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        status="pending",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.status == "pending"
    
    
def test_evidence_analysis_accepts_completed_status():
    """
    Verify completed analysis status.
    """

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        status="completed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.status == "completed"


def test_evidence_analysis_accepts_empty_result():
    """
    Verify that an analysis can explicitly use an empty result.
    """

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        result={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.result == {}

def test_evidence_analysis_accepts_structured_result():
    """
    Verify structured AI results can be stored.
    """

    result = {
        "vehicle_part": "front_bumper",
        "damage_type": "dent",
        "severity": "moderate",
        "observations": [
            "Visible deformation",
            "Paint scratches",
        ],
    }

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        result=result,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.result == result
    assert analysis.result["vehicle_part"] == "front_bumper"
    assert analysis.result["severity"] == "moderate"


def test_evidence_analysis_accepts_confidence():
    """
    Verify confidence can be stored.
    """

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        confidence=0.91,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.confidence == 0.91


def test_evidence_analysis_accepts_prompt_version():
    """
    Verify prompt version can be stored.
    """

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        prompt_version="v1",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.prompt_version == "v1"


def test_evidence_analysis_accepts_error():
    """
    Verify an analysis failure can store an error message.
    """

    analysis = EvidenceAnalysis(
        evidence_id=uuid4(),
        analysis_type="vehicle_damage",
        status="failed",
        error="AI provider request failed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert analysis.status == "failed"
    assert analysis.error == "AI provider request failed"