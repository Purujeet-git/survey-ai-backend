"""
SurveyAI Database

Module:
Database Base

Purpose:
Defines the SQLAlchemy declarative base used by all database models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SurveyAI SQLAlchemy models.
    """

    pass