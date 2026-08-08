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

    ADMIN = "admin"
    SURVEYOR = "surveyor"
    REVIEWER = "reviewer"


class ClaimStatus(StrEnum):
    """
    Lifecycle states of an insurance claim.
    """

    DRAFT = "draft"
    PROCESSING = "processing"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    COMPLETED = "completed"