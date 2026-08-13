"""
SurveyAI Backend

Module:
Document Versioning Service

Purpose:
Manages document revision chains, version numbers (v1 -> v2), and parent-child document links.
"""

from uuid import UUID

from app.documents.models.document import Document
from app.documents.repositories.document_repository import DocumentRepository
from app.shared.exceptions import NotFoundException


class DocumentVersioningService:
    """
    Handles document version increments and revision history.
    """

    def __init__(self, repository: DocumentRepository) -> None:
        self.repository = repository

    async def create_new_version(
        self,
        parent_document_id: UUID,
        new_file_name: str,
        storage_key: str,
        content_type: str,
        file_size: int,
        file_hash: str,
        document_type: str | None = None,
        extracted_text: str | None = None,
        doc_metadata: dict | None = None,
    ) -> Document:
        """
        Create a new version of an existing document.
        """
        parent = await self.repository.get_by_id(parent_document_id)
        if not parent:
            raise NotFoundException(f"Parent document '{parent_document_id}' not found.")

        # Demote existing latest versions in chain
        root_parent_id = parent.parent_document_id or parent.id
        all_versions = await self.repository.list_versions(root_parent_id)

        for doc in all_versions:
            if doc.is_latest:
                doc.is_latest = False
                await self.repository.update(doc)

        new_version_number = max([d.version for d in all_versions] + [parent.version]) + 1

        new_doc = Document(
            claim_id=parent.claim_id,
            user_id=parent.user_id,
            organization_id=parent.organization_id,
            document_type=document_type or parent.document_type,
            file_name=new_file_name,
            storage_key=storage_key,
            content_type=content_type,
            file_size=file_size,
            file_hash=file_hash,
            version=new_version_number,
            parent_document_id=root_parent_id,
            is_latest=True,
            processing_status="uploaded",
            extracted_text=extracted_text,
            doc_metadata=doc_metadata or {},
        )

        return await self.repository.create(new_doc)

    async def get_version_history(self, document_id: UUID) -> list[Document]:
        """
        Get all versions in the document revision chain.
        """
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise NotFoundException(f"Document '{document_id}' not found.")

        root_id = doc.parent_document_id or doc.id
        return await self.repository.list_versions(root_id)
