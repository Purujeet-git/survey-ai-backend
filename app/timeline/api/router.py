"""
SurveyAI Backend

Module:
Timeline API Router

Purpose:
REST API endpoints for claim timeline audit logs.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.timeline.repositories.timeline_repository import TimelineRepository
from app.timeline.schemas.timeline import TimelineEventResponse
from app.timeline.services.timeline_service import TimelineService
from app.users.models import User

router = APIRouter(
    prefix="/claims",
    tags=["Timeline"],
)


def get_timeline_service(
    session: AsyncSession = Depends(get_db),
) -> TimelineService:
    repository = TimelineRepository(session)
    return TimelineService(repository)


@router.get(
    "/{claim_id}/timeline",
    response_model=list[TimelineEventResponse],
    summary="Get Timeline Audit Trail for a Claim",
)
async def get_claim_timeline(
    claim_id: UUID,
    service: TimelineService = Depends(get_timeline_service),
    current_user: User = Depends(get_current_user),
):
    return await service.get_claim_timeline(claim_id)
