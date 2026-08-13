"""
SurveyAI Backend

Module:
Claim Workflow State Machine

Purpose:
Defines valid claim status transitions and validation logic.
"""

from app.database.enums import ClaimStatus
from app.shared.exceptions import ValidationException

VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    ClaimStatus.DRAFT: {ClaimStatus.SUBMITTED, ClaimStatus.PROCESSING},
    ClaimStatus.SUBMITTED: {ClaimStatus.PROCESSING, ClaimStatus.UNDER_REVIEW},
    ClaimStatus.PROCESSING: {ClaimStatus.IN_PROGRESS, ClaimStatus.UNDER_REVIEW},
    ClaimStatus.IN_PROGRESS: {ClaimStatus.UNDER_REVIEW, ClaimStatus.APPROVED, ClaimStatus.REJECTED},
    ClaimStatus.UNDER_REVIEW: {ClaimStatus.APPROVED, ClaimStatus.REJECTED, ClaimStatus.IN_PROGRESS},
    ClaimStatus.APPROVED: {ClaimStatus.COMPLETED, ClaimStatus.CLOSED},
    ClaimStatus.REJECTED: {ClaimStatus.CLOSED, ClaimStatus.DRAFT},
    ClaimStatus.COMPLETED: {ClaimStatus.CLOSED},
    ClaimStatus.CLOSED: set(),
}


def validate_status_transition(current_status: str, new_status: str) -> None:
    """
    Validate whether transitioning from current_status to new_status is allowed.
    """
    if current_status == new_status:
        return

    allowed_next_states = VALID_STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next_states:
        raise ValidationException(
            f"Invalid claim status transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions from '{current_status}' are: {sorted(list(allowed_next_states))}."
        )
