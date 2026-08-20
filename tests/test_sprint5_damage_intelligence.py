"""
Test suite for Sprint 5 — Damage Intelligence:
- Multimodal Photo Damage Analysis Node
- Expected Damage Prediction Node
- Evidence Validation Node
- Conflict Detection Node
- Full LangGraph End-to-End Pipeline
"""

import pytest
import app.database.models  # Ensures all SQLAlchemy models are registered
from uuid import uuid4

from app.ai.graph import ClaimAIPipelineService
from app.ai.nodes.conflict_detection import conflict_detection_node
from app.ai.nodes.evidence_validation import evidence_validation_node
from app.ai.nodes.expected_damage import expected_damage_node
from app.ai.nodes.photo_analysis import photo_analysis_node
from app.ai.state import ClaimState


@pytest.mark.asyncio
async def test_photo_analysis_node():
    state: ClaimState = {
        "accident_analysis": {"impact_direction": "Front", "estimated_severity": "Severe"},
        "documents": [
            {"id": "doc1", "document_type": "ACCIDENT_PHOTO", "file_name": "front_damage.jpg", "doc_metadata": {"vision_analysis": {"detected_parts": [{"part_name": "Front Bumper", "severity": "Severe", "recommended_action": "REPLACE"}]}}}
        ],
    }

    result = await photo_analysis_node(state)
    photo_res = result["photo_analysis"]

    assert len(photo_res["detected_parts"]) > 0
    parts = [p["part_name"] for p in photo_res["detected_parts"]]
    assert "Front Bumper" in parts


@pytest.mark.asyncio
async def test_expected_damage_node():
    state: ClaimState = {
        "accident_analysis": {
            "status": "GROUNDED",
            "impact_direction": "Front",
            "collision_type": "Frontal Impact",
        }
    }

    result = await expected_damage_node(state)
    expected = result["expected_damage"]

    assert "Frontal Crumple Zone" in expected["expected_zones"]
    comp_names = [c["component"] for c in expected["expected_components"]]
    assert "Front Bumper Assembly" in comp_names


@pytest.mark.asyncio
async def test_evidence_validation_node():
    state: ClaimState = {
        "accident_analysis": {"impact_direction": "Front"},
        "photo_analysis": {
            "detected_parts": [
                {"part_name": "Front Bumper", "severity": "Severe", "recommended_action": "REPLACE"}
            ]
        },
        "extracted_entities": {
            "estimate": {
                "line_items": [
                    {"description": "Front Bumper Assembly", "cost": 18500.0, "type": "REPLACEMENT"},
                    {"description": "Rear Door Panel", "cost": 12000.0, "type": "REPLACEMENT"},
                ]
            }
        },
    }

    result = await evidence_validation_node(state)
    validations = result["evidence_validation"]

    assert len(validations) == 2
    supported_item = next(v for v in validations if v["estimate_item"] == "Front Bumper Assembly")
    unsupported_item = next(v for v in validations if v["estimate_item"] == "Rear Door Panel")

    assert supported_item["status"] == "SUPPORTED"
    assert unsupported_item["status"] == "UNSUPPORTED"


@pytest.mark.asyncio
async def test_evidence_validation_never_invents_missing_estimate_items():
    result = await evidence_validation_node({"extracted_entities": {"estimate": {"line_items": []}}, "photo_analysis": {"detected_parts": []}})
    assert result["evidence_validation"] == []


@pytest.mark.asyncio
async def test_photo_analysis_never_invents_damage_without_photos():
    result = await photo_analysis_node({"documents": [], "accident_analysis": {"impact_direction": "Front"}})
    assert result["photo_analysis"]["photo_count"] == 0
    assert result["photo_analysis"]["detected_parts"] == []


@pytest.mark.asyncio
async def test_accident_analysis_does_not_invent_missing_dynamics():
    from app.ai.nodes.accident import accident_understanding_node

    result = await accident_understanding_node({"documents": [], "extracted_entities": {}})
    analysis = result["accident_analysis"]

    assert analysis["status"] == "INSUFFICIENT_EVIDENCE"
    assert analysis["collision_type"] == "UNKNOWN"
    assert analysis["impact_direction"] == "UNKNOWN"
    assert analysis["speed_estimate"] == "UNKNOWN"
    assert analysis["citations"] == []


@pytest.mark.asyncio
async def test_expected_damage_does_not_infer_from_ungrounded_direction():
    result = await expected_damage_node({"accident_analysis": {"impact_direction": "Front"}})

    assert result["expected_damage"]["expected_zones"] == []
    assert result["expected_damage"]["expected_components"] == []
    assert result["expected_damage"]["confidence"] == 0.0


@pytest.mark.asyncio
async def test_conflict_detection_node():
    state: ClaimState = {
        "evidence_validation": [
            {
                "estimate_item": "Rear Door Panel",
                "claimed_cost": 12000.0,
                "status": "UNSUPPORTED",
                "reason": "Collision impact vector was frontal and rear door is intact in photos.",
            }
        ],
        "extracted_entities": {
            "policy": {"sum_insured": 500000.0},
            "estimate": {"total_amount": 650000.0},
            "fir": {"incident_date": "2026-08-12"},
        },
    }

    result = await conflict_detection_node(state)
    findings = result["findings"]

    assert len(findings) >= 2
    types = [f["finding_type"] for f in findings]
    assert "UNSUPPORTED_REPAIR" in types
    assert "COST_OVERRUN" in types


@pytest.mark.asyncio
async def test_policy_and_cost_findings_include_source_citations():
    result = await conflict_detection_node({
        "documents": [
            {
                "id": "fir-1",
                "file_name": "incident_fir.pdf",
                "document_type": "FIR",
                "extracted_text": "Incident date: 2026-08-12",
            },
            {
                "id": "policy-1",
                "file_name": "policy_schedule.pdf",
                "document_type": "POLICY_SCHEDULE",
                "extracted_text": "Policy expiry: 2026-08-01; Sum insured: INR 500000",
            },
            {
                "id": "estimate-1",
                "file_name": "repair_estimate.pdf",
                "document_type": "REPAIR_ESTIMATE",
                "extracted_text": "Total estimate: INR 650000",
            },
        ],
        "extracted_entities": {
            "fir": {"incident_date": "2026-08-12"},
            "policy": {"expiry_date": "2026-08-01", "sum_insured": 500000.0},
            "estimate": {"total_amount": 650000.0},
        },
        "evidence_validation": [],
    })

    findings = {finding["finding_type"]: finding for finding in result["findings"]}
    date_citations = findings["DATE_MISMATCH"]["citations"]
    cost_citations = findings["COST_OVERRUN"]["citations"]

    assert {citation["document_id"] for citation in date_citations} == {"fir-1", "policy-1"}
    assert {citation["document_id"] for citation in cost_citations} == {"estimate-1", "policy-1"}
    assert all(citation["quote"] for citation in date_citations + cost_citations)


@pytest.mark.asyncio
async def test_full_damage_intelligence_pipeline():
    pipeline = ClaimAIPipelineService()
    claim_id = str(uuid4())

    initial_state: ClaimState = {
        "claim_id": claim_id,
        "claim_number": "CLM-5501",
        "user_id": str(uuid4()),
        "status": "intake",
        "documents": [
            {
                "id": "doc1",
                "file_name": "FIR_report.pdf",
                "document_type": "FIR",
                "content_type": "application/pdf",
                "extracted_text": "First Information Report of front collision",
            },
            {
                "id": "doc2",
                "file_name": "front_damage_photo.jpg",
                "document_type": "ACCIDENT_PHOTO",
                "content_type": "image/jpeg",
                "extracted_text": "[Damage Photo]",
            },
        ],
        "execution_logs": [],
    }

    final_state = await pipeline.run_pipeline(initial_state)

    assert final_state["current_node"] == "ConflictDetectionNode"
    assert "photo_analysis" in final_state
    assert "expected_damage" in final_state
    assert "evidence_validation" in final_state
    assert "findings" in final_state
    assert len(final_state["execution_logs"]) == 8
