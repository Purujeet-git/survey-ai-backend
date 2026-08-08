"""
SurveyAI Database

Module:
Models Registry

Purpose:
Central import registry for SQLAlchemy models.

Alembic uses this module to discover all database models.
"""

from app.database.base import Base

__all__ = ["Base"]