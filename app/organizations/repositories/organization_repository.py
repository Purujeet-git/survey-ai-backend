"""
SurveyAI Backend

Module:
Organization Repository

Purpose:
Data access layer for Organization entity.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.organizations.models.organization import Organization


class OrganizationRepository:
    """
    Handles database operations for Organization entity.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)
        return organization

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(Organization.code == code)
        )
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[Organization]:
        result = await self.session.execute(
            select(Organization)
            .order_by(Organization.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, organization: Organization) -> Organization:
        await self.session.commit()
        await self.session.refresh(organization)
        return organization

    async def delete(self, organization: Organization) -> None:
        await self.session.delete(organization)
        await self.session.commit()
