"""
SurveyAI Backend

Module:
Claim Service

Purpose:
Provides business logic for claim operations.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.claims.models.claim import Claim
from app.claims.repositories.claim import ClaimRepository
from app.shared.exceptions import NotFoundError


class ClaimService:
    """
    Service layer for claim operations.
    """

    def __init__(self, session: AsyncSession):
        self.repository = ClaimRepository(session)

    async def create_claim(
        self,
        user_id: UUID,
        **claim_data,
    ) -> Claim:
        """
        Create a new claim for a surveyor.
        """

        claim = Claim(
            user_id=user_id,
            **claim_data,
        )

        return await self.repository.create(claim)

    async def get_claim(
        self,
        user_id: UUID,
        claim_id: UUID,
    ) -> Claim:
        """
        Retrieve a claim belonging to the specified surveyor.
        """

        claim = await self.repository.get_by_id(claim_id)

        if claim is None or claim.user_id != user_id:
            raise NotFoundError("Claim not found")

        return claim

    async def update_claim(
        self,
        user_id: UUID,
        claim_id: UUID,
        **updates,
    ) -> Claim:
        """
        Update a claim belonging to the specified surveyor.
        """

        claim = await self.get_claim(
            user_id=user_id,
            claim_id=claim_id,
        )

        for field, value in updates.items():
            if hasattr(claim, field):
                setattr(claim, field, value)

        return await self.repository.update(claim)

    async def delete_claim(
        self,
        user_id: UUID,
        claim_id: UUID,
    ) -> None:
        """
        Delete a claim belonging to the specified surveyor.
        """

        claim = await self.get_claim(
            user_id=user_id,
            claim_id=claim_id,
        )

        await self.repository.delete(claim)