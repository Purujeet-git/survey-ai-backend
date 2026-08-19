"""
SurveyAI Backend

Module:
Document Service

Purpose:
Orchestrates file upload, zero-cost storage, metadata extraction, classification, OCR, and audit logging.
"""

from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models.document import Document
from app.documents.repositories.document_repository import DocumentRepository
from app.documents.services.classification_service import DocumentClassificationService
from app.documents.services.extraction_service import DocumentExtractionService
from app.documents.services.metadata_service import DocumentMetadataService
from app.documents.services.versioning_service import DocumentVersioningService
from app.ai.security_guardrails import SecurityGuardrails
from app.shared.exceptions import NotFoundException, ValidationException
from app.storage.base import BaseStorage
from app.storage.local import LocalDiskStorage
from app.timeline.repositories.timeline_repository import TimelineRepository
from app.timeline.schemas.timeline import TimelineEventCreate
from app.timeline.services.timeline_service import TimelineService


class DocumentService:
    """
    Main service orchestrator for Claim Document lifecycle.
    """

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

    def __init__(
        self,
        session: AsyncSession,
        storage: BaseStorage | None = None,
    ) -> None:
        self.session = session
        self.repository = DocumentRepository(session)
        self.storage = storage or LocalDiskStorage()
        self.metadata_service = DocumentMetadataService()
        self.classification_service = DocumentClassificationService()
        self.extraction_service = DocumentExtractionService()
        self.versioning_service = DocumentVersioningService(self.repository)
        self.timeline_service = TimelineService(TimelineRepository(session))

    async def upload_document(
        self,
        claim_id: UUID,
        user_id: UUID,
        file: UploadFile,
        organization_id: UUID | None = None,
        document_type: str | None = None,
    ) -> tuple[Document, bytes]:
        """
        Process upload, save file, run classification & extraction, and log timeline event.
        Returns (Document model instance, in-memory file content bytes for instant LLM vision analysis).
        """
        content_type = file.content_type or "application/octet-stream"
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationException(f"Unsupported document file type '{content_type}'.")

        content = await file.read()
        file_size = len(content)

        if file_size <= 0:
            raise ValidationException("Uploaded file cannot be empty.")
        if file_size > self.MAX_FILE_SIZE:
            raise ValidationException("Uploaded file exceeds 25 MB size limit.")

        file_name = Path(file.filename or "document").name
        folder = f"claims/{claim_id}"

        # Extract metadata & compute SHA256 checksum
        metadata = self.metadata_service.extract_metadata(content, content_type)
        file_hash = metadata["hash"]

        # Extract text & auto-classify
        extracted_text = self.extraction_service.extract_text(content, content_type)
        safe_text, injection_detected = SecurityGuardrails.sanitize_untrusted_text(extracted_text)
        metadata["prompt_injection_detected"] = injection_detected
        classified_type, confidence, _ = self.classification_service.classify(
            file_name=file_name,
            content_type=content_type,
            text=safe_text,
        )

        final_type = document_type or classified_type

        # Save to local zero-cost storage
        storage_key = await self.storage.save(
            folder=folder,
            file_name=file_name,
            content=content,
        )

        doc = Document(
            claim_id=claim_id,
            user_id=user_id,
            organization_id=organization_id,
            document_type=final_type,
            file_name=file_name,
            storage_key=storage_key,
            content_type=content_type,
            file_size=file_size,
            file_hash=file_hash,
            version=1,
            is_latest=True,
            processing_status="uploaded",
            extracted_text=extracted_text,
            classification_confidence=confidence,
            doc_metadata=metadata,
        )

        created_doc = await self.repository.create(doc)

        await self.timeline_service.log_event(
            TimelineEventCreate(
                claim_id=claim_id,
                actor_id=user_id,
                event_type="DOCUMENT_UPLOADED",
                description=f"Document '{file_name}' uploaded (Type: {final_type}).",
                payload={
                    "document_id": str(created_doc.id),
                    "file_name": file_name,
                    "document_type": final_type,
                    "file_size": file_size,
                },
            )
        )

        return created_doc, content

    async def get_document(self, document_id: UUID) -> Document:
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise NotFoundException(f"Document '{document_id}' not found.")
        return doc

    async def get_document_bytes(self, document_id: UUID) -> bytes:
        doc = await self.get_document(document_id)
        return await self.storage.get(doc.storage_key)

    async def list_claim_documents(
        self, claim_id: UUID, latest_only: bool = True
    ) -> list[Document]:
        return await self.repository.list_by_claim(claim_id, latest_only=latest_only)

    async def upload_new_version(
        self,
        document_id: UUID,
        user_id: UUID,
        file: UploadFile,
    ) -> Document:
        parent_doc = await self.get_document(document_id)
        content_type = file.content_type or parent_doc.content_type
        content = await file.read()

        file_name = Path(file.filename or parent_doc.file_name).name
        folder = f"claims/{parent_doc.claim_id}"

        metadata = self.metadata_service.extract_metadata(content, content_type)
        file_hash = metadata["hash"]
        extracted_text = self.extraction_service.extract_text(content, content_type)
        safe_text, injection_detected = SecurityGuardrails.sanitize_untrusted_text(extracted_text)
        metadata["prompt_injection_detected"] = injection_detected

        storage_key = await self.storage.save(
            folder=folder,
            file_name=file_name,
            content=content,
        )

        new_doc = await self.versioning_service.create_new_version(
            parent_document_id=parent_doc.id,
            new_file_name=file_name,
            storage_key=storage_key,
            content_type=content_type,
            file_size=len(content),
            file_hash=file_hash,
            document_type=parent_doc.document_type,
            extracted_text=extracted_text,
            doc_metadata=metadata,
        )

        await self.timeline_service.log_event(
            TimelineEventCreate(
                claim_id=parent_doc.claim_id,
                actor_id=user_id,
                event_type="DOCUMENT_REVISION_UPLOADED",
                description=f"New version v{new_doc.version} uploaded for '{file_name}'.",
                payload={
                    "document_id": str(new_doc.id),
                    "parent_document_id": str(parent_doc.id),
                    "version": new_doc.version,
                },
            )
        )

        return new_doc

    async def classify_document(self, document_id: UUID) -> tuple[str, float, str]:
        doc = await self.get_document(document_id)
        doc_type, confidence, explanation = self.classification_service.classify(
            file_name=doc.file_name,
            content_type=doc.content_type,
            text=SecurityGuardrails.sanitize_untrusted_text(doc.extracted_text or "")[0],
        )
        doc.document_type = doc_type
        doc.classification_confidence = confidence
        await self.repository.update(doc)
        return doc_type, confidence, explanation

    async def extract_text(self, document_id: UUID) -> str:
        doc = await self.get_document(document_id)
        if not doc.extracted_text:
            content = await self.storage.get(doc.storage_key)
            doc.extracted_text = self.extraction_service.extract_text(content, doc.content_type)
            await self.repository.update(doc)
        return doc.extracted_text or ""

    async def delete_document(self, document_id: UUID, user_id: UUID | None = None) -> None:
        doc = await self.get_document(document_id)
        await self.storage.delete(doc.storage_key)
        await self.repository.delete(doc)
