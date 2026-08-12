"""
SurveyAI Database

Module:
Models Registry

Purpose:
Central import registry for SQLAlchemy models.
Alembic uses this module to discover all database models.
"""

from app.auth.models import AuthSession
from app.database.base import Base
from app.users.models import User
from app.claims.models.claim import Claim
from app.surveys.models.survey import Survey
__all__ = [
    "Base",
    "User",
    "AuthSession",
    "Claim",
    "Survey",
]