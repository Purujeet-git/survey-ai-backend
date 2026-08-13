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
from app.claims.workflow import validate_status_transition
from app.shared.exceptions import NotFoundError
from app.timeline.repositories.timeline_repository import TimelineRepository
from app.timeline.schemas.timeline import TimelineEventCreate
from app.timeline.services.timeline_service import TimelineService


class ClaimService:
    """
    Service layer for claim operations with workflow and audit logging.
    """

    def __init__(self, session: AsyncSession):
        self.repository = ClaimRepository(session)
        self.timeline_service = TimelineService(TimelineRepository(session))

    async def create_claim(
        self,
        user_id: UUID,
        **claim_data,
    ) -> Claim:
        """
        Create a new claim for a surveyor and log initial timeline event.
        """

        claim = Claim(
            user_id=user_id,
            **claim_data,
        )

        created_claim = await self.repository.create(claim)

        await self.timeline_service.log_event(
            TimelineEventCreate(
                claim_id=created_claim.id,
                actor_id=user_id,
                event_type="CLAIM_CREATED",
                description=f"Claim '{created_claim.claim_number}' created.",
                payload={"status": created_claim.status},
            )
        )

        return created_claim

    async def get_claim(
        self,
        user_id: UUID | None,
        claim_id: UUID,
    ) -> Claim:
        """
        Retrieve a claim by ID, optionally verifying user permissions.
        """

        claim = await self.repository.get_by_id(claim_id)

        if claim is None:
            raise NotFoundError("Claim not found")

        if user_id is not None and claim.user_id != user_id and claim.assigned_to_id != user_id:
            raise NotFoundError("Claim not found")

        return claim

    async def list_claims(
        self,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
    ) -> list[Claim]:
        """
        List claims filtered by user or organization.
        """
        if organization_id:
            return await self.repository.list_by_organization(organization_id)
        if user_id:
            return await self.repository.list_by_user(user_id)
        return await self.repository.list_by_user(user_id)

    async def update_claim(
        self,
        user_id: UUID | None,
        claim_id: UUID,
        **updates,
    ) -> Claim:
        """
        Update a claim and log changes.
        """

        claim = await self.get_claim(
            user_id=user_id,
            claim_id=claim_id,
        )

        if "status" in updates and updates["status"] and updates["status"] != claim.status:
            validate_status_transition(claim.status, updates["status"])
            old_status = claim.status
            new_status = updates["status"]
            await self.timeline_service.log_event(
                TimelineEventCreate(
                    claim_id=claim.id,
                    actor_id=user_id,
                    event_type="STATUS_CHANGED",
                    description=f"Claim status changed from '{old_status}' to '{new_status}'.",
                    payload={"old_status": old_status, "new_status": new_status, "reason": updates.get("reason")},
                )
            )

        for field, value in updates.items():
            if field != "reason" and hasattr(claim, field) and value is not None:
                setattr(claim, field, value)

        return await self.repository.update(claim)

    async def update_claim_status(
        self,
        user_id: UUID | None,
        claim_id: UUID,
        new_status: str,
        reason: str | None = None,
    ) -> Claim:
        """
        Update claim status strictly enforcing workflow state machine.
        """
        return await self.update_claim(
            user_id=user_id,
            claim_id=claim_id,
            status=new_status,
            reason=reason,
        )

    async def delete_claim(
        self,
        user_id: UUID | None,
        claim_id: UUID,
    ) -> None:
        """
        Delete a claim.
        """

        claim = await self.get_claim(
            user_id=user_id,
            claim_id=claim_id,
        )

        await self.repository.delete(claim)
