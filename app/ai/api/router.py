"""
SurveyAI Backend

Module:
AI Pipeline API Router

Purpose:
REST API endpoints to trigger, inspect, and resume LangGraph AI pipeline execution.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.graph import ClaimAIPipelineService
from app.ai.state import ClaimState
from app.auth.dependencies import get_current_user
from app.claims.services.claim import ClaimService
from app.database import get_db
from app.documents.services.document_service import DocumentService
from app.users.models import User

router = APIRouter(
    prefix="/claims",
    tags=["AI Pipeline"],
)


@router.post(
    "/{claim_id}/ai/process",
    summary="Trigger or resume AI Processing Pipeline",
)
async def process_claim_ai(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Triggers or resumes the LangGraph AI processing pipeline for a claim.
    """
    claim_service = ClaimService(session)
    document_service = DocumentService(session)

    claim = await claim_service.get_claim(claim_id=claim_id, user_id=current_user.id)
    documents = await document_service.list_claim_documents(claim_id=claim_id, latest_only=True)

    doc_manifests = [
        {
            "id": str(d.id),
            "file_name": d.file_name,
            "document_type": d.document_type,
            "content_type": d.content_type,
            "storage_key": d.storage_key,
            "file_size": d.file_size,
            "extracted_text": d.extracted_text or "",
            "doc_metadata": d.doc_metadata,
        }
        for d in documents
    ]

    initial_state: ClaimState = {
        "claim_id": str(claim.id),
        "claim_number": claim.claim_number,
        "organization_id": str(claim.organization_id) if claim.organization_id else None,
        "user_id": str(current_user.id),
        "assigned_to_id": str(claim.assigned_to_id) if claim.assigned_to_id else None,
        "status": "intake",
        "documents": doc_manifests,
        "classification_results": {},
        "extracted_entities": {},
        "accident_analysis": {},
        "execution_logs": [],
        "current_node": "START",
        "error": None,
    }

    pipeline = ClaimAIPipelineService()
    final_state = await pipeline.run_pipeline(initial_state)

    # Persist extracted entities and damage intelligence to Claim extra_data
    if final_state.get("extracted_entities"):
        claim.extra_data = {
            **claim.extra_data,
            "ai_extracted_entities": final_state["extracted_entities"],
            "ai_accident_analysis": final_state.get("accident_analysis", {}),
            "ai_photo_analysis": final_state.get("photo_analysis", {}),
            "ai_expected_damage": final_state.get("expected_damage", {}),
            "ai_evidence_validation": final_state.get("evidence_validation", []),
            "ai_findings": final_state.get("findings", []),
        }
        await claim_service.update_claim(claim_id=claim.id, user_id=current_user.id, extra_data=claim.extra_data)

    return {
        "claim_id": str(claim.id),
        "status": final_state.get("status"),
        "current_node": final_state.get("current_node"),
        "classification_results": final_state.get("classification_results"),
        "extracted_entities": final_state.get("extracted_entities"),
        "accident_analysis": final_state.get("accident_analysis"),
        "photo_analysis": final_state.get("photo_analysis"),
        "expected_damage": final_state.get("expected_damage"),
        "evidence_validation": final_state.get("evidence_validation"),
        "findings": final_state.get("findings"),
        "execution_logs": final_state.get("execution_logs"),
    }



@router.post(
    "/{claim_id}/ai/process-stream",
    summary="Trigger AI Pipeline with Real-time SSE Event Streaming",
)
async def process_claim_ai_stream(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Triggers or resumes the LangGraph AI processing pipeline, yielding Server-Sent Events (SSE) in real time.
    """
    import json
    from fastapi.responses import StreamingResponse

    claim_service = ClaimService(session)
    document_service = DocumentService(session)

    claim = await claim_service.get_claim(claim_id=claim_id, user_id=current_user.id)
    documents = await document_service.list_claim_documents(claim_id=claim_id, latest_only=True)

    doc_manifests = [
        {
            "id": str(d.id),
            "file_name": d.file_name,
            "document_type": d.document_type,
            "content_type": d.content_type,
            "storage_key": d.storage_key,
            "file_size": d.file_size,
            "extracted_text": d.extracted_text or "",
            "doc_metadata": d.doc_metadata,
        }
        for d in documents
    ]

    initial_state: ClaimState = {
        "claim_id": str(claim.id),
        "claim_number": claim.claim_number,
        "organization_id": str(claim.organization_id) if claim.organization_id else None,
        "user_id": str(current_user.id),
        "assigned_to_id": str(claim.assigned_to_id) if claim.assigned_to_id else None,
        "status": "intake",
        "documents": doc_manifests,
        "classification_results": {},
        "extracted_entities": {},
        "accident_analysis": {},
        "execution_logs": [],
        "current_node": "START",
        "error": None,
    }

    pipeline = ClaimAIPipelineService()

    async def event_generator():
        async for event in pipeline.astream_pipeline(initial_state):
            # If pipeline finished, persist claim extra_data
            if event.get("event") == "PIPELINE_FINISHED":
                final_state = event.get("final_state", {})
                if final_state.get("extracted_entities"):
                    claim.extra_data = {
                        **claim.extra_data,
                        "ai_extracted_entities": final_state["extracted_entities"],
                        "ai_accident_analysis": final_state.get("accident_analysis", {}),
                        "ai_photo_analysis": final_state.get("photo_analysis", {}),
                        "ai_expected_damage": final_state.get("expected_damage", {}),
                        "ai_evidence_validation": final_state.get("evidence_validation", []),
                        "ai_findings": final_state.get("findings", []),
                    }
                    await claim_service.update_claim(claim_id=claim.id, user_id=current_user.id, extra_data=claim.extra_data)

            payload = json.dumps(event)
            yield f"data: {payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/{claim_id}/ai/state",
    summary="Get AI Pipeline State and Checkpoint",
)
async def get_claim_ai_state(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves stored graph state snapshot and node execution logs for a claim.
    """
    pipeline = ClaimAIPipelineService()
    state = pipeline.get_pipeline_state(str(claim_id))

    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No AI pipeline state checkpoint found for claim '{claim_id}'.",
        )

    return state
