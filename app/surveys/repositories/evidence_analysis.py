"""
SurveyAI Backend

Module:
Evidence Analysis Repository

Purpose:
Provides database operations for evidence analysis records.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.surveys.models.evidence_analysis import EvidenceAnalysis


class EvidenceAnalysisRepository:
    """
    Repository for evidence analysis database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        analysis: EvidenceAnalysis,
    ) -> EvidenceAnalysis:
        """
        Create a new evidence analysis.
        """

        self.session.add(analysis)

        await self.session.flush()

        return analysis

    async def get_by_id(
        self,
        analysis_id: UUID,
    ) -> EvidenceAnalysis | None:
        """
        Retrieve an evidence analysis by its ID.
        """

        result = await self.session.execute(
            select(EvidenceAnalysis).where(
                EvidenceAnalysis.id == analysis_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_evidence_id(
        self,
        evidence_id: UUID,
    ) -> list[EvidenceAnalysis]:
        """
        Retrieve all analyses belonging to an evidence item.
        """

        result = await self.session.execute(
            select(EvidenceAnalysis)
            .where(
                EvidenceAnalysis.evidence_id == evidence_id
            )
            .order_by(
                EvidenceAnalysis.created_at
            )
        )

        return list(result.scalars().all())

    async def update(
        self,
        analysis: EvidenceAnalysis,
    ) -> EvidenceAnalysis:
        """
        Update an existing evidence analysis.
        """

        self.session.add(analysis)

        await self.session.flush()

        return analysis

    async def delete(
        self,
        analysis: EvidenceAnalysis,
    ) -> None:
        """
        Delete an existing evidence analysis.
        """

        await self.session.delete(analysis)

        await self.session.flush()