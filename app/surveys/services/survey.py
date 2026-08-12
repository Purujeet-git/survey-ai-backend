"""
SurveyAI Backend

Module:
Survey Service

Purpose:
Provides business logic for survey operations.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.claims.repositories.claim import ClaimRepository
from app.shared.exceptions import NotFoundError
from app.surveys.models.survey import Survey
from app.surveys.repositories.survey import SurveyRepository


class SurveyService:
    """
    Service layer for survey operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.survey_repository = SurveyRepository(session)
        self.claim_repository = ClaimRepository(session)

    async def _verify_claim_ownership(
        self,
        user_id: UUID,
        claim_id: UUID,
    ):
        """
        Verify that the claim belongs to the specified surveyor.
        """

        claim = await self.claim_repository.get_by_id(
            claim_id
        )

        if claim is None or claim.user_id != user_id:
            raise NotFoundError("Claim not found")

        return claim

    async def create_survey(
        self,
        user_id: UUID,
        claim_id: UUID,
        **survey_data,
    ) -> Survey:
        """
        Create a survey for a claim owned by the surveyor.
        """

        await self._verify_claim_ownership(
            user_id=user_id,
            claim_id=claim_id,
        )

        survey = Survey(
            claim_id=claim_id,
            **survey_data,
        )

        return await self.survey_repository.create(
            survey
        )

    async def get_survey(
        self,
        user_id: UUID,
        survey_id: UUID,
    ) -> Survey:
        """
        Retrieve a survey belonging to the surveyor.
        """

        survey = await self.survey_repository.get_by_id(
            survey_id
        )

        if survey is None:
            raise NotFoundError("Survey not found")

        await self._verify_claim_ownership(
            user_id=user_id,
            claim_id=survey.claim_id,
        )

        return survey

    async def get_claim_surveys(
        self,
        user_id: UUID,
        claim_id: UUID,
    ) -> list[Survey]:
        """
        Retrieve all surveys belonging to a claim owned
        by the surveyor.
        """

        await self._verify_claim_ownership(
            user_id=user_id,
            claim_id=claim_id,
        )

        return await self.survey_repository.get_by_claim_id(
            claim_id
        )

    async def update_survey(
        self,
        user_id: UUID,
        survey_id: UUID,
        **updates,
    ) -> Survey:
        """
        Update a survey belonging to the surveyor.
        """

        survey = await self.get_survey(
            user_id=user_id,
            survey_id=survey_id,
        )

        for field, value in updates.items():
            if hasattr(survey, field):
                setattr(survey, field, value)

        return await self.survey_repository.update(
            survey
        )

    async def delete_survey(
        self,
        user_id: UUID,
        survey_id: UUID,
    ) -> None:
        """
        Delete a survey belonging to the surveyor.
        """

        survey = await self.get_survey(
            user_id=user_id,
            survey_id=survey_id,
        )

        await self.survey_repository.delete(
            survey
        )