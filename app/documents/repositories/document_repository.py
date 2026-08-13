"""
SurveyAI Backend

Module:
Document Repository

Purpose:
Data access layer for Document entity.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.models.document import Document


class DocumentRepository:
    """
    Handles database operations for Document entities.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_by_claim(self, claim_id: UUID, latest_only: bool = True) -> list[Document]:
        stmt = select(Document).where(Document.claim_id == claim_id)
        if latest_only:
            stmt = stmt.where(Document.is_latest.is_(True))
        stmt = stmt.order_by(Document.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_versions(self, parent_id: UUID) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where((Document.id == parent_id) | (Document.parent_document_id == parent_id))
            .order_by(Document.version.asc())
        )
        return list(result.scalars().all())

    async def update(self, document: Document) -> Document:
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)
        await self.session.commit()
