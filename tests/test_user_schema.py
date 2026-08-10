"""
Tests for Surveyor account schemas.
"""

from uuid import uuid4
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.users.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
)


def test_user_create_schema():
    user = UserCreate(
        email="surveyor@example.com",
        password="securepassword123",
        full_name="John Surveyor",
        mobile="9876543210",
    )

    assert user.email == "surveyor@example.com"
    assert user.full_name == "John Surveyor"
    assert user.mobile == "9876543210"


def test_user_create_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreate(
            email="surveyor@example.com",
            password="short",
            full_name="John Surveyor",
        )


def test_user_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            password="securepassword123",
            full_name="John Surveyor",
        )


def test_user_update_allows_partial_update():
    user = UserUpdate(
        full_name="Updated Surveyor",
    )

    assert user.full_name == "Updated Surveyor"
    assert user.email is None
    assert user.mobile is None


def test_user_response_excludes_password_hash():
    response = UserResponse(
        id=uuid4(),
        email="surveyor@example.com",
        full_name="John Surveyor",
        mobile=None,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert "password_hash" not in response.model_dump()