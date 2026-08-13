"""
SurveyAI Backend

Module:
Document API Router

Purpose:
REST API endpoints for Document upload, storage, metadata, versioning, classification, and OCR extraction.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.documents.schemas.document import (
    DocumentClassificationResponse,
    DocumentExtractionResponse,
    DocumentResponse,
)
from app.documents.services.document_service import DocumentService
from app.users.models import User

router = APIRouter(tags=["Documents"])


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
