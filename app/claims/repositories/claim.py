"""
SurveyAI Backend

Module:
Claim Repository

Purpose:
Provides database operations for the Claim domain.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.claims.models import Claim


class ClaimRepository:
    """
    Repository for Claim database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        claim_id: UUID,
    ) -> Claim | None:
        """
        Retrieve a claim by its ID.
        """

        result = await self.session.execute(
            select(Claim).where(
                Claim.id == claim_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_claim_number(
        self,
        user_id: UUID,
        claim_number: str,
    ) -> Claim | None:
        """
        Retrieve a claim by claim number for a specific surveyor.
        """

        result = await self.session.execute(
            select(Claim).where(
                Claim.user_id == user_id,
                Claim.claim_number == claim_number,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
    ) -> list[Claim]:
        """
        Retrieve all claims belonging to a surveyor.
        """

        result = await self.session.execute(
            select(Claim)
            .where(Claim.user_id == user_id)
            .order_by(Claim.created_at.desc())
        )

        return list(result.scalars().all())

    async def list_by_organization(
        self,
        organization_id: UUID,
    ) -> list[Claim]:
        """
        Retrieve all claims for an organization.
        """

        result = await self.session.execute(
            select(Claim)
            .where(Claim.organization_id == organization_id)
            .order_by(Claim.created_at.desc())
        )

        return list(result.scalars().all())

    async def create(
        self,
        claim: Claim,
    ) -> Claim:
        """
        Persist a new claim.
        """

        self.session.add(claim)
        await self.session.commit()
        await self.session.refresh(claim)
        return claim

    async def update(
        self,
        claim: Claim,
    ) -> Claim:
        """
        Persist changes to an existing claim.
        """

        await self.session.commit()
        await self.session.refresh(claim)
        return claim

    async def delete(
        self,
        claim: Claim,
    ) -> None:
        """
        Delete a claim.
        """

        await self.session.delete(claim)
        await self.session.commit()