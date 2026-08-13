"""
SurveyAI Backend

Module:
Timeline Service

Purpose:
Encapsulates business logic for logging and viewing timeline audit events.
"""

from uuid import UUID

from app.timeline.models.timeline import TimelineEvent
from app.timeline.repositories.timeline_repository import TimelineRepository
from app.timeline.schemas.timeline import TimelineEventCreate


class TimelineService:
    """
    Business logic service for claim timeline audit events.
    """

    def __init__(self, repository: TimelineRepository) -> None:
        self.repository = repository

    async def log_event(self, schema: TimelineEventCreate) -> TimelineEvent:
        event = TimelineEvent(
            claim_id=schema.claim_id,
            actor_id=schema.actor_id,
            event_type=schema.event_type,
            description=schema.description,
            payload=schema.payload,
        )
        return await self.repository.create(event)

    async def get_claim_timeline(self, claim_id: UUID) -> list[TimelineEvent]:
        return await self.repository.list_by_claim(claim_id)
