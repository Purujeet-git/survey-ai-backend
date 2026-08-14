"""
SurveyAI Backend

Module:
Human Review Service

Purpose:
Encapsulates business logic for itemized human review, approving/rejecting/editing AI findings, and maintaining immutable audit trails.
"""

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.claims.services.claim import ClaimService
from app.review.schemas.review import (
    ClaimReviewSummary,
    FindingReviewItem,
    FindingReviewRequest,
    ReviewActionEnum,
)
from app.timeline.repositories.timeline_repository import TimelineRepository
from app.timeline.schemas.timeline import TimelineEventCreate
from app.timeline.services.timeline_service import TimelineService
from app.shared.exceptions import NotFoundException, ValidationException


class ReviewService:
    """
    Service orchestrating human review gates and item-by-item decisions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.claim_service = ClaimService(session)
        self.timeline_service = TimelineService(TimelineRepository(session))

    async def get_review_summary(self, claim_id: UUID, user_id: UUID) -> ClaimReviewSummary:
        """
        Retrieves the itemized review summary for a claim.
        """
        claim = await self.claim_service.get_claim(claim_id=claim_id, user_id=user_id)
        extra_data = claim.extra_data or {}
        ai_findings = extra_data.get("ai_findings", [])
        reviews_map = extra_data.get("human_reviews", {})
        is_committed = extra_data.get("review_committed", False)

        items: list[FindingReviewItem] = []
        approved_count = 0
        rejected_count = 0
        edited_count = 0
        pending_count = 0

        for f in ai_findings:
            f_id = f.get("id", "")
            rev = reviews_map.get(f_id, {})
            status_str = rev.get("status", ReviewActionEnum.PENDING.value)
            try:
                status_enum = ReviewActionEnum(status_str)
            except ValueError:
                status_enum = ReviewActionEnum.PENDING

            if status_enum == ReviewActionEnum.APPROVE:
                approved_count += 1
            elif status_enum == ReviewActionEnum.REJECT:
                rejected_count += 1
            elif status_enum == ReviewActionEnum.EDIT:
                edited_count += 1
            else:
                pending_count += 1

            items.append(
                FindingReviewItem(
                    id=f_id,
                    title=f.get("title", "Finding"),
                    finding_type=f.get("finding_type", "GENERAL"),
                    severity=f.get("severity", "MEDIUM"),
                    description=f.get("description", ""),
                    recommendation=f.get("recommendation"),
                    status=status_enum,
                    comment=rev.get("comment"),
                    override_value=rev.get("override_value"),
                    reviewed_by=rev.get("reviewed_by"),
                    reviewed_at=rev.get("reviewed_at"),
                )
            )

        return ClaimReviewSummary(
            claim_id=str(claim.id),
            claim_number=claim.claim_number,
            total_findings=len(items),
            approved_count=approved_count,
            rejected_count=rejected_count,
            edited_count=edited_count,
            pending_count=pending_count,
            is_committed=is_committed,
            findings=items,
        )

    async def review_finding(
        self,
        claim_id: UUID,
        finding_id: str,
        review_req: FindingReviewRequest,
        user_id: UUID,
    ) -> ClaimReviewSummary:
        """
        Applies a review decision to an individual finding item.
        """
        claim = await self.claim_service.get_claim(claim_id=claim_id, user_id=user_id)
        extra_data = dict(claim.extra_data or {})
        ai_findings = extra_data.get("ai_findings", [])

        # Verify finding exists
        target_finding = next((f for f in ai_findings if f.get("id") == finding_id), None)
        if not target_finding:
            raise NotFoundException(f"Finding '{finding_id}' not found on claim '{claim_id}'.")

        reviews_map = dict(extra_data.get("human_reviews", {}))
        now_iso = datetime.now(timezone.utc).isoformat()

        reviews_map[finding_id] = {
            "status": review_req.action.value,
            "comment": review_req.comment,
            "override_value": review_req.override_value,
            "reviewed_by": str(user_id),
            "reviewed_at": now_iso,
        }

        extra_data["human_reviews"] = reviews_map
        await self.claim_service.update_claim(claim_id=claim.id, user_id=user_id, extra_data=extra_data)

        # Log timeline audit event
        await self.timeline_service.log_event(
            TimelineEventCreate(
                claim_id=claim.id,
                actor_id=user_id,
                event_type="HUMAN_REVIEW_ITEM_UPDATED",
                description=f"Human reviewer set finding '{target_finding.get('title')}' status to {review_req.action.value}.",
                payload={
                    "finding_id": finding_id,
                    "action": review_req.action.value,
                    "comment": review_req.comment,
                    "override_value": review_req.override_value,
                },
            )
        )

        return await self.get_review_summary(claim_id, user_id)

    async def batch_review(
        self,
        claim_id: UUID,
        decisions: dict[str, FindingReviewRequest],
        user_id: UUID,
    ) -> ClaimReviewSummary:
        """
        Applies batch review decisions programmatically or via UI.
        """
        claim = await self.claim_service.get_claim(claim_id=claim_id, user_id=user_id)
        extra_data = dict(claim.extra_data or {})
        reviews_map = dict(extra_data.get("human_reviews", {}))
        now_iso = datetime.now(timezone.utc).isoformat()

        for finding_id, decision in decisions.items():
            reviews_map[finding_id] = {
                "status": decision.action.value,
                "comment": decision.comment,
                "override_value": decision.override_value,
                "reviewed_by": str(user_id),
                "reviewed_at": now_iso,
            }

        extra_data["human_reviews"] = reviews_map
        await self.claim_service.update_claim(claim_id=claim.id, user_id=user_id, extra_data=extra_data)

        await self.timeline_service.log_event(
            TimelineEventCreate(
                claim_id=claim.id,
                actor_id=user_id,
                event_type="HUMAN_REVIEW_BATCH_UPDATED",
                description=f"Applied batch review decisions to {len(decisions)} finding(s).",
                payload={"decisions_count": len(decisions)},
            )
        )

        return await self.get_review_summary(claim_id, user_id)

    async def commit_review(self, claim_id: UUID, user_id: UUID) -> ClaimReviewSummary:
        """
        Finalizes human review decisions, locking findings and syncing to report state.
        """
        claim = await self.claim_service.get_claim(claim_id=claim_id, user_id=user_id)
        extra_data = dict(claim.extra_data or {})
        extra_data["review_committed"] = True
        extra_data["review_committed_at"] = datetime.now(timezone.utc).isoformat()
        extra_data["review_committed_by"] = str(user_id)

        await self.claim_service.update_claim(claim_id=claim.id, user_id=user_id, extra_data=extra_data)

        await self.timeline_service.log_event(
            TimelineEventCreate(
                claim_id=claim.id,
                actor_id=user_id,
                event_type="HUMAN_REVIEW_COMMITTED",
                description="Human reviewer committed and finalized all review decisions.",
                payload={"committed_at": extra_data["review_committed_at"]},
            )
        )

        return await self.get_review_summary(claim_id, user_id)
