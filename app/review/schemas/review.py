"""
SurveyAI Backend

Module:
Human Review Schemas

Purpose:
Pydantic schemas defining data contracts for itemized human review decisions, approvals, rejections, overrides, and audit summaries.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ReviewActionEnum(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    EDIT = "EDIT"
    PENDING = "PENDING"


class FindingReviewRequest(BaseModel):
    action: ReviewActionEnum = Field(..., description="Action to apply: APPROVE, REJECT, or EDIT")
    comment: str | None = Field(default=None, description="Optional surveyor comment or feedback reason")
    override_value: Any | None = Field(default=None, description="Overridden value if action is EDIT")


class BatchReviewRequest(BaseModel):
    decisions: dict[str, FindingReviewRequest] = Field(
        ..., description="Dictionary mapping finding_id to its review decision"
    )


class FindingReviewItem(BaseModel):
    id: str
    title: str
    finding_type: str
    severity: str
    description: str
    recommendation: str | None = None
    status: ReviewActionEnum = ReviewActionEnum.PENDING
    comment: str | None = None
    override_value: Any | None = None
    reviewed_by: str | None = None
    reviewed_at: str | None = None


class ClaimReviewSummary(BaseModel):
    claim_id: str
    claim_number: str
    total_findings: int
    approved_count: int
    rejected_count: int
    edited_count: int
    pending_count: int
    is_committed: bool
    findings: list[FindingReviewItem]
