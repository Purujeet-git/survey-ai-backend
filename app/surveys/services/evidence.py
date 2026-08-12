"""
SurveyAI Backend

Module:
Survey Evidence Service

Purpose:
Provides business logic for survey evidence operations.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.claims.repositories.claim import ClaimRepository
from app.shared.exceptions import NotFoundError
from app.surveys.models.evidence import SurveyEvidence
from app.surveys.repositories.evidence import SurveyEvidenceRepository
from app.surveys.repositories.survey import SurveyRepository


class SurveyEvidenceService:
    """
    Service layer for survey evidence operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.evidence_repository = SurveyEvidenceRepository(
            session
        )
        self.survey_repository = SurveyRepository(
            session
        )
        self.claim_repository = ClaimRepository(
            session
        )

    async def _verify_survey_ownership(
        self,
        user_id: UUID,
        survey_id: UUID,
    ):
        """
        Verify that the survey belongs to the specified user.
        """

        survey = await self.survey_repository.get_by_id(
            survey_id
        )

        if survey is None:
            raise NotFoundError("Survey not found")

        claim = await self.claim_repository.get_by_id(
            survey.claim_id
        )

        if claim is None or claim.user_id != user_id:
            raise NotFoundError("Survey not found")

        return survey

    async def create_evidence(
        self,
        user_id: UUID,
        survey_id: UUID,
        **evidence_data,
    ) -> SurveyEvidence:
        """
        Create evidence for a survey owned by the user.
        """

        await self._verify_survey_ownership(
            user_id=user_id,
            survey_id=survey_id,
        )

        evidence = SurveyEvidence(
            survey_id=survey_id,
            **evidence_data,
        )

        return await self.evidence_repository.create(
            evidence
        )

    async def get_evidence(
        self,
        user_id: UUID,
        evidence_id: UUID,
    ) -> SurveyEvidence:
        """
        Retrieve evidence belonging to the user's survey.
        """

        evidence = await self.evidence_repository.get_by_id(
            evidence_id
        )

        if evidence is None:
            raise NotFoundError("Evidence not found")

        await self._verify_survey_ownership(
            user_id=user_id,
            survey_id=evidence.survey_id,
        )

        return evidence

    async def get_survey_evidence(
        self,
        user_id: UUID,
        survey_id: UUID,
    ) -> list[SurveyEvidence]:
        """
        Retrieve all evidence belonging to a survey
        owned by the user.
        """

        await self._verify_survey_ownership(
            user_id=user_id,
            survey_id=survey_id,
        )

        return await self.evidence_repository.get_by_survey_id(
            survey_id
        )

    async def update_evidence(
        self,
        user_id: UUID,
        evidence_id: UUID,
        **updates,
    ) -> SurveyEvidence:
        """
        Update evidence belonging to the user's survey.
        """

        evidence = await self.get_evidence(
            user_id=user_id,
            evidence_id=evidence_id,
        )

        for field, value in updates.items():
            if hasattr(evidence, field):
                setattr(evidence, field, value)

        return await self.evidence_repository.update(
            evidence
        )

    async def delete_evidence(
        self,
        user_id: UUID,
        evidence_id: UUID,
    ) -> None:
        """
        Delete evidence belonging to the user's survey.
        """

        evidence = await self.get_evidence(
            user_id=user_id,
            evidence_id=evidence_id,
        )

        await self.evidence_repository.delete(
            evidence
        )