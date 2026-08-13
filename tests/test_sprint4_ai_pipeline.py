"""
Test suite for Sprint 4 — AI Pipeline (LangGraph):
- LangGraph ClaimState & Checkpointer
- Intake Node
- Semantic Classification Node
- Structured Entity Extraction Node
- Accident Understanding Node
- StateGraph Assembly & Resumable Execution
"""

import pytest
import app.database.models  # Ensures all SQLAlchemy models are registered
from uuid import uuid4

from app.ai.checkpointer import StateCheckpointer
from app.ai.graph import ClaimAIPipelineService, build_claim_processing_graph
from app.ai.nodes.accident import accident_understanding_node
from app.ai.nodes.classification import classification_node
from app.ai.nodes.extraction import extraction_node
from app.ai.nodes.intake import intake_node
from app.ai.state import ClaimState


@pytest.mark.asyncio
async def test_intake_node():
    state: ClaimState = {
        "claim_id": str(uuid4()),
        "documents": [
            {"id": "doc1", "file_name": "fir.pdf", "extracted_text": "Police FIR report"},
        ],
    }

    result = await intake_node(state)
    assert result["status"] == "intake_completed"
    assert len(result["execution_logs"]) == 1
    assert result["execution_logs"][0]["node"] == "IntakeNode"


@pytest.mark.asyncio
async def test_classification_node():
    state: ClaimState = {
        "documents": [
            {
                "id": "doc1",
                "file_name": "Police_FIR_Copy.pdf",
                "content_type": "application/pdf",
                "extracted_text": "First Information Report Police Thana",
            },
            {
                "id": "doc2",
                "file_name": "Driver_License.jpg",
                "content_type": "image/jpeg",
                "extracted_text": "Driving License Transport Authority",
            },
        ],
    }

    result = await classification_node(state)
    assert "classification_results" in result
    classifications = result["classification_results"]

    assert classifications["doc1"]["classified_type"] == "FIR"
    assert classifications["doc2"]["classified_type"] == "DRIVING_LICENSE"


@pytest.mark.asyncio
async def test_extraction_node():
    state: ClaimState = {
        "documents": [
            {
                "id": "doc1",
                "document_type": "DRIVING_LICENSE",
                "file_name": "DL.jpg",
                "extracted_text": "Driving License DL MH0220200012345",
            },
            {
                "id": "doc2",
                "document_type": "REGISTRATION_CERTIFICATE",
                "file_name": "RC.pdf",
                "extracted_text": "Registration Certificate MH02CB1234 Chassis MA3EYD21S00984321 Engine K12M1492042",
            },
            {
                "id": "doc3",
                "document_type": "FIR",
                "file_name": "FIR.pdf",
                "extracted_text": "FIR No 2026/812 Police Station Central",
            },
            {
                "id": "doc4",
                "document_type": "REPAIR_ESTIMATE",
                "file_name": "Estimate.pdf",
                "extracted_text": "Garage Repair Quotation INR 45,000.00",
            },
        ],
    }

    result = await extraction_node(state)
    entities = result["extracted_entities"]

    assert entities["driver"]["dl_number"] == "MH0220200012345"
    assert entities["vehicle"]["registration_number"] == "MH02CB1234"
    assert entities["fir"]["fir_number"] == "2026/812"
    assert entities["estimate"]["total_amount"] == 45000.0


@pytest.mark.asyncio
async def test_accident_understanding_node():
    state: ClaimState = {
        "extracted_entities": {
            "fir": {"fir_number": "FIR-1029"},
        },
        "documents": [
            {"file_name": "notes.txt", "extracted_text": "Vehicle hit from behind in rear-end collision on highway."},
        ],
    }

    result = await accident_understanding_node(state)
    analysis = result["accident_analysis"]

    assert analysis["collision_type"] == "Rear-end Collision"
    assert analysis["impact_direction"] == "Rear"
    assert "rear-end collision" in analysis["consistency_analysis"].lower()


@pytest.mark.asyncio
async def test_stategraph_pipeline_execution():
    pipeline = ClaimAIPipelineService()
    claim_id = str(uuid4())

    initial_state: ClaimState = {
        "claim_id": claim_id,
        "claim_number": "CLM-9901",
        "user_id": str(uuid4()),
        "status": "intake",
        "documents": [
            {
                "id": "doc1",
                "file_name": "FIR_report.pdf",
                "document_type": "FIR",
                "content_type": "application/pdf",
                "extracted_text": "First Information Report of rear collision",
            }
        ],
        "classification_results": {},
        "extracted_entities": {},
        "accident_analysis": {},
        "execution_logs": [],
    }

    final_state = await pipeline.run_pipeline(initial_state)

    assert final_state["current_node"] == "ConflictDetectionNode"
    assert len(final_state["execution_logs"]) >= 4


    # Test Checkpoint retrieval
    retrieved_checkpoint = pipeline.get_pipeline_state(claim_id)
    assert retrieved_checkpoint is not None
    assert retrieved_checkpoint["claim_id"] == claim_id
