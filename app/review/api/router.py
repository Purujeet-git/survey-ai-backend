"""
SurveyAI Backend

Module:
Human Review API Router

Purpose:
REST API endpoints for inspecting, approving, rejecting, overriding findings item-by-item and committing human gates.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.review.schemas.review import (
    BatchReviewRequest,
    ClaimReviewSummary,
    FindingReviewRequest,
)
from app.review.services.review_service import ReviewService
from app.users.models import User

router = APIRouter(
    prefix="/claims",
    tags=["Human Review Gate"],
)


@router.get(
    "/{claim_id}/review",
    response_model=ClaimReviewSummary,
    summary="Get Claim Review Items & Finding Decisions",
)
async def get_claim_review(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Retrieves all AI findings and itemized human review decisions for a claim.
    """
    service = ReviewService(session)
    return await service.get_review_summary(claim_id=claim_id, user_id=current_user.id)


@router.post(
    "/{claim_id}/review/findings/{finding_id}",
    response_model=ClaimReviewSummary,
    summary="Review Individual Finding (Approve / Reject / Edit)",
)
async def review_finding_item(
    claim_id: UUID,
    finding_id: str,
    body: FindingReviewRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Applies an Approve, Reject, or Edit decision to an individual finding.
    Rejecting one finding does not discard or affect other findings.
    """
    service = ReviewService(session)
    return await service.review_finding(
        claim_id=claim_id,
        finding_id=finding_id,
        review_req=body,
        user_id=current_user.id,
    )


@router.post(
    "/{claim_id}/review/batch",
    response_model=ClaimReviewSummary,
    summary="Submit Batch Review Decisions (Machine Interface)",
)
async def batch_review_findings(
    claim_id: UUID,
    body: BatchReviewRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Batch applies decisions to multiple findings at once for programmatic/machine driving.
    """
    service = ReviewService(session)
    return await service.batch_review(
        claim_id=claim_id,
        decisions=body.decisions,
        user_id=current_user.id,
    )


@router.post(
    "/{claim_id}/review/commit",
    response_model=ClaimReviewSummary,
    summary="Commit & Finalize Human Review Decisions",
)
async def commit_claim_review(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Commits all reviewed decisions, locks the findings gate, and logs the timeline audit record.
    """
    service = ReviewService(session)
    return await service.commit_review(claim_id=claim_id, user_id=current_user.id)
