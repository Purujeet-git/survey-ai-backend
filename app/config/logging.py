"""
Logging configuration for SurveyAI.
"""

import logging

from app.config.settings import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )