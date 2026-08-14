"""
SurveyAI Backend

Module:
Sprint 7 - Human Review Gate Automated Tests

Purpose:
Validates item-by-item review, independent approval and rejection, value override, batch programmatic driving, and audit logging.
"""

from uuid import uuid4
import pytest
import app.database.models  # Ensures all SQLAlchemy models are registered in metadata
from app.claims.models.claim import Claim
from app.review.schemas.review import (
    BatchReviewRequest,
    FindingReviewRequest,
    ReviewActionEnum,
)
from app.review.services.review_service import ReviewService
from app.users.models.user import User


@pytest.mark.asyncio
async def test_human_review_gate_lifecycle(async_session):
    """
    Tests the complete Sprint 7 Human Review Gate workflow:
    1. Retrieval of findings manifest.
    2. Approving one finding.
    3. Rejecting a second finding (verifying rejection does not discard the first).
    4. Overriding/editing a third finding.
    5. Batch review programmatic execution.
    6. Committing review gate and verifying audit trail.
    """
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"surveyor-{user_id.hex[:8]}@surveyai.com",
        password_hash="hash",
        full_name="Senior Surveyor",
        status="active",
    )
    async_session.add(user)
    await async_session.flush()

    findings_sample = [
        {
            "id": "find-1",
            "title": "Front Bumper Replacement",
            "finding_type": "DAMAGE_VERIFIED",
            "severity": "LOW",
            "description": "Front bumper cracked, matches photo evidence.",
            "recommendation": "Approve replacement cost of INR 1,483.90.",
        },
        {
            "id": "find-2",
            "title": "Unsupported Rear Door Repair",
            "finding_type": "UNSUPPORTED_REPAIR",
            "severity": "HIGH",
            "description": "Impact was frontal, rear door intact in photos.",
            "recommendation": "Reject claimed repair cost of INR 500.00.",
        },
        {
            "id": "find-3",
            "title": "Labor Rate Anomaly",
            "finding_type": "COST_ANOMALY",
            "severity": "MEDIUM",
            "description": "Painting labor rate 20% higher than regional norm.",
            "recommendation": "Override to benchmark rate INR 1,200.00.",
        },
    ]

    claim = Claim(
        id=uuid4(),
        claim_number="CLM-REV-2026-001",
        status="SUBMITTED",
        organization_id=None,
        user_id=user.id,
        extra_data={
            "ai_findings": findings_sample,
            "human_reviews": {},
        },
    )
    async_session.add(claim)
    await async_session.commit()

    service = ReviewService(async_session)

    # 1. Initial State: All 3 findings are PENDING
    summary = await service.get_review_summary(claim.id, user.id)
    assert summary.total_findings == 3
    assert summary.pending_count == 3
    assert summary.approved_count == 0
    assert summary.rejected_count == 0
    assert summary.edited_count == 0
    assert summary.is_committed is False

    # 2. Approve Finding 1
    req1 = FindingReviewRequest(
        action=ReviewActionEnum.APPROVE,
        comment="Confirmed by on-site photo inspection."
    )
    summary = await service.review_finding(claim.id, "find-1", req1, user.id)
    assert summary.approved_count == 1
    assert summary.pending_count == 2
    assert summary.findings[0].status == ReviewActionEnum.APPROVE

    # 3. Reject Finding 2 (Crucial: Rejecting find-2 DOES NOT discard find-1)
    req2 = FindingReviewRequest(
        action=ReviewActionEnum.REJECT,
        comment="Disagree with garage, collision was frontal only."
    )
    summary = await service.review_finding(claim.id, "find-2", req2, user.id)
    assert summary.approved_count == 1
    assert summary.rejected_count == 1
    assert summary.pending_count == 1
    # Verify find-1 remains APPROVED
    find_1_item = next(f for f in summary.findings if f.id == "find-1")
    assert find_1_item.status == ReviewActionEnum.APPROVE
    # Verify find-2 is REJECTED
    find_2_item = next(f for f in summary.findings if f.id == "find-2")
    assert find_2_item.status == ReviewActionEnum.REJECT

    # 4. Edit / Override Finding 3
    req3 = FindingReviewRequest(
        action=ReviewActionEnum.EDIT,
        comment="Adjusted rate to regional standard.",
        override_value={"adjusted_labor_rate": 1200.0},
    )
    summary = await service.review_finding(claim.id, "find-3", req3, user.id)
    assert summary.approved_count == 1
    assert summary.rejected_count == 1
    assert summary.edited_count == 1
    assert summary.pending_count == 0

    # 5. Test Batch Review (Machine Driving Interface)
    batch_req = {
        "find-1": FindingReviewRequest(action=ReviewActionEnum.APPROVE, comment="Batch approved."),
        "find-2": FindingReviewRequest(action=ReviewActionEnum.REJECT, comment="Batch rejected."),
    }
    summary = await service.batch_review(claim.id, batch_req, user.id)
    assert summary.approved_count == 1
    assert summary.rejected_count == 1

    # 6. Commit Review Gate
    summary = await service.commit_review(claim.id, user.id)
    assert summary.is_committed is True

    # 7. Check timeline audit trail
    timeline = await service.timeline_service.get_claim_timeline(claim.id)
    event_types = [t.event_type for t in timeline]
    assert "HUMAN_REVIEW_ITEM_UPDATED" in event_types
    assert "HUMAN_REVIEW_COMMITTED" in event_types
