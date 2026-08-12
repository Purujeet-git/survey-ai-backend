"""
SurveyAI Backend

Module:
Survey Evidence Repository

Purpose:
Provides database operations for survey evidence.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.surveys.models.evidence import SurveyEvidence


class SurveyEvidenceRepository:
    """
    Repository for SurveyEvidence database operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        evidence: SurveyEvidence,
    ) -> SurveyEvidence:
        """
        Create a new survey evidence record.
        """

        self.session.add(evidence)

        await self.session.flush()
        await self.session.refresh(evidence)

        return evidence

    async def get_by_id(
        self,
        evidence_id: UUID,
    ) -> SurveyEvidence | None:
        """
        Retrieve evidence by its ID.
        """

        result = await self.session.execute(
            select(SurveyEvidence).where(
                SurveyEvidence.id == evidence_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_survey_id(
        self,
        survey_id: UUID,
    ) -> list[SurveyEvidence]:
        """
        Retrieve all evidence belonging to a survey.
        """

        result = await self.session.execute(
            select(SurveyEvidence)
            .where(
                SurveyEvidence.survey_id == survey_id,
            )
            .order_by(
                SurveyEvidence.created_at,
            )
        )

        return list(result.scalars().all())

    async def update(
        self,
        evidence: SurveyEvidence,
    ) -> SurveyEvidence:
        """
        Update an existing survey evidence record.
        """

        await self.session.flush()
        await self.session.refresh(evidence)

        return evidence

    async def delete(
        self,
        evidence: SurveyEvidence,
    ) -> None:
        """
        Delete a survey evidence record.
        """

        await self.session.delete(evidence)

        await self.session.flush()