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
            {"id": "doc1", "document_type": "ACCIDENT_PHOTO", "file_name": "front_damage.jpg"}
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
