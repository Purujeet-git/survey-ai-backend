"""
SurveyAI Backend

Module:
Timeline Repository

Purpose:
Data access layer for TimelineEvent entity.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.timeline.models.timeline import TimelineEvent


class TimelineRepository:
    """
    Handles database operations for timeline events.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, event: TimelineEvent) -> TimelineEvent:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list_by_claim(self, claim_id: UUID) -> list[TimelineEvent]:
        result = await self.session.execute(
            select(TimelineEvent)
            .where(TimelineEvent.claim_id == claim_id)
            .order_by(TimelineEvent.created_at.asc())
        )
        return list(result.scalars().all())
