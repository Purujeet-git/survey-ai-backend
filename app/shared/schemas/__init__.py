"""
SurveyAI Shared Schemas.
"""

from app.shared.schemas.pagination import (
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)
from app.shared.schemas.response import (
    APIErrorResponse,
    APIResponse,
    ErrorDetail,
)

__all__ = [
    "APIResponse",
    "APIErrorResponse",
    "ErrorDetail",
    "PaginationParams",
    "PaginationMeta",
    "PaginatedResponse",
]