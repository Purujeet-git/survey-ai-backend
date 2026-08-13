"""
SurveyAI Database

Module:
Database Enums

Purpose:
Contains shared database enumeration definitions.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """
    Roles available to users within SurveyAI.
    """

    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    ADMIN = "admin"
    SURVEYOR = "surveyor"
    ADJUSTER = "adjuster"
    REVIEWER = "reviewer"


class ClaimStatus(StrEnum):
    """
    Lifecycle states of an insurance claim.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CLOSED = "closed"