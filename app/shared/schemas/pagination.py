"""
SurveyAI Shared Schemas

Module:
Pagination

Purpose:
Defines standard pagination request and response structures.
"""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """
    Standard pagination parameters.
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Page number.",
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of records per page.",
    )

    @property
    def offset(self) -> int:
        """
        Calculate the database offset for this page.
        """

        return (self.page - 1) * self.page_size


class PaginationMeta(BaseModel):
    """
    Metadata describing a paginated result.
    """

    page: int = Field(
        ...,
        ge=1,
    )

    page_size: int = Field(
        ...,
        ge=1,
        le=100,
    )

    total: int = Field(
        ...,
        ge=0,
    )

    total_pages: int = Field(
        ...,
        ge=0,
    )


class PaginatedResponse(BaseModel):
    """
    Standard structure for paginated API results.
    """

    items: list
    pagination: PaginationMeta