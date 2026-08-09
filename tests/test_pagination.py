"""
Tests for shared pagination schemas.
"""

from app.shared.schemas import (
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)


def test_pagination_defaults():
    """Verify pagination defaults."""

    params = PaginationParams()

    assert params.page == 1
    assert params.page_size == 20
    assert params.offset == 0


def test_pagination_offset():
    """Verify pagination offset calculation."""

    params = PaginationParams(
        page=3,
        page_size=20,
    )

    assert params.offset == 40


def test_pagination_meta():
    """Verify pagination metadata."""

    meta = PaginationMeta(
        page=2,
        page_size=20,
        total=45,
        total_pages=3,
    )

    assert meta.page == 2
    assert meta.page_size == 20
    assert meta.total == 45
    assert meta.total_pages == 3


def test_paginated_response():
    """Verify paginated response structure."""

    response = PaginatedResponse(
        items=[
            {"id": 1},
            {"id": 2},
        ],
        pagination=PaginationMeta(
            page=1,
            page_size=20,
            total=2,
            total_pages=1,
        ),
    )

    assert len(response.items) == 2
    assert response.pagination.total == 2