"""
SurveyAI Backend

Module:
Document API Router

Purpose:
REST API endpoints for Document upload, storage, metadata, versioning, classification, and OCR extraction.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.documents.schemas.document import (
    DocumentClassificationResponse,
    DocumentExtractionResponse,
    DocumentResponse,
)
from app.documents.services.document_service import DocumentService
from app.documents.services.watcher_service import WatcherManager
from app.claims.services.claim import ClaimService
from app.users.models import User

router = APIRouter(tags=["Documents"])


def get_watcher_manager(request: Request) -> WatcherManager:
    manager = getattr(request.app.state, "watcher_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Watcher service is not available")
    return manager


def get_document_service(session: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(session)


@router.post(
    "/claims/{claim_id}/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document or photo to a claim",
)
async def upload_document(
    claim_id: UUID,
    file: UploadFile = File(...),
    document_type: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc, _ = await service.upload_document(
        claim_id=claim_id,
        user_id=current_user.id,
        file=file,
        organization_id=current_user.organization_id,
        document_type=document_type,
    )
    return DocumentResponse.model_validate(doc)


@router.post(
    "/claims/{claim_id}/watchers",
    status_code=status.HTTP_201_CREATED,
    summary="Register a watched folder for a claim",
)
async def register_watcher(
    claim_id: UUID,
    payload: dict[str, str],
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    manager: WatcherManager = Depends(get_watcher_manager),
):
    await ClaimService(session).get_claim(claim_id=claim_id, user_id=current_user.id)
    try:
        return await manager.register(str(claim_id), payload.get("path", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/claims/{claim_id}/watchers",
    summary="List watched folders for a claim",
)
async def list_watchers(
    claim_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    manager: WatcherManager = Depends(get_watcher_manager),
):
    await ClaimService(session).get_claim(claim_id=claim_id, user_id=current_user.id)
    return await manager.list_for_claim(str(claim_id))


@router.post(
    "/claims/{claim_id}/watchers/{watch_id}/start",
    summary="Start watching a registered folder",
)
async def start_watcher(
    claim_id: UUID,
    watch_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    manager: WatcherManager = Depends(get_watcher_manager),
):
    await ClaimService(session).get_claim(claim_id=claim_id, user_id=current_user.id)
    try:
        result = await manager.start(watch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result["claim_id"] != str(claim_id):
        raise HTTPException(status_code=404, detail="Watcher does not belong to this claim")
    return result


@router.post(
    "/claims/{claim_id}/watchers/{watch_id}/stop",
    summary="Stop watching a registered folder",
)
async def stop_watcher(
    claim_id: UUID,
    watch_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    manager: WatcherManager = Depends(get_watcher_manager),
):
    await ClaimService(session).get_claim(claim_id=claim_id, user_id=current_user.id)
    try:
        result = await manager.stop(watch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result["claim_id"] != str(claim_id):
        raise HTTPException(status_code=404, detail="Watcher does not belong to this claim")
    return result


@router.get(
    "/claims/{claim_id}/watchers/{watch_id}",
    summary="Get watched folder status",
)
async def get_watcher_status(
    claim_id: UUID,
    watch_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    manager: WatcherManager = Depends(get_watcher_manager),
):
    await ClaimService(session).get_claim(claim_id=claim_id, user_id=current_user.id)
    try:
        result = await manager.status(watch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result["claim_id"] != str(claim_id):
        raise HTTPException(status_code=404, detail="Watcher does not belong to this claim")
    return result


@router.get(
    "/claims/{claim_id}/documents",
    response_model=list[DocumentResponse],
    summary="List claim documents",
)
async def list_claim_documents(
    claim_id: UUID,
    latest_only: bool = Query(True),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    docs = await service.list_claim_documents(claim_id=claim_id, latest_only=latest_only)
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.get_document(document_id)
    return DocumentResponse.model_validate(doc)


@router.post(
    "/documents/{document_id}/version",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload new version of a document",
)
async def upload_document_version(
    document_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc = await service.upload_new_version(
        document_id=document_id,
        user_id=current_user.id,
        file=file,
    )
    return DocumentResponse.model_validate(doc)


@router.get(
    "/documents/{document_id}/versions",
    response_model=list[DocumentResponse],
    summary="Get version history of a document",
)
async def get_document_versions(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    versions = await service.versioning_service.get_version_history(document_id)
    return [DocumentResponse.model_validate(v) for v in versions]


@router.post(
    "/documents/{document_id}/classify",
    response_model=DocumentClassificationResponse,
    summary="Classify document type",
)
async def classify_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    doc_type, confidence, explanation = await service.classify_document(document_id)
    return DocumentClassificationResponse(
        document_id=document_id,
        document_type=doc_type,
        confidence=confidence,
        reason=explanation,
    )


@router.post(
    "/documents/{document_id}/extract",
    response_model=DocumentExtractionResponse,
    summary="Extract text content / OCR from document",
)
async def extract_document_text(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    extracted_text = await service.extract_text(document_id)
    word_count = len(extracted_text.split()) if extracted_text else 0
    return DocumentExtractionResponse(
        document_id=document_id,
        extracted_text=extracted_text,
        word_count=word_count,
    )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    await service.delete_document(document_id=document_id, user_id=current_user.id)
