"""
SurveyAI Backend

Module:
Survey Repository

Purpose:
Provides database operations for survey records.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.surveys.models.survey import Survey


class SurveyRepository:
    """
    Repository for survey database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        survey: Survey,
    ) -> Survey:
        """
        Create a new survey.
        """

        self.session.add(survey)

        await self.session.flush()

        return survey

    async def get_by_id(
        self,
        survey_id: UUID,
    ) -> Survey | None:
        """
        Retrieve a survey by its ID.
        """

        result = await self.session.execute(
            select(Survey).where(
                Survey.id == survey_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_claim_id(
        self,
        claim_id: UUID,
    ) -> list[Survey]:
        """
        Retrieve all surveys belonging to a claim.
        """

        result = await self.session.execute(
            select(Survey)
            .where(Survey.claim_id == claim_id)
            .order_by(Survey.created_at)
        )

        return list(result.scalars().all())

    async def update(
        self,
        survey: Survey,
    ) -> Survey:
        """
        Update an existing survey.
        """

        self.session.add(survey)

        await self.session.flush()

        return survey

    async def delete(
        self,
        survey: Survey,
    ) -> None:
        """
        Delete an existing survey.
        """

        await self.session.delete(survey)

        await self.session.flush()