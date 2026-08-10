"""
Tests for the Surveyor account service.
"""

from uuid import uuid4

import pytest

from app.users.schemas import UserCreate, UserUpdate
from app.users.services import UserService
from app.shared.exceptions import NotFoundError


@pytest.mark.asyncio
async def test_get_user_not_found(async_session):
    """
    Verify that requesting a non-existent user raises NotFoundError.
    """

    service = UserService(async_session)

    with pytest.raises(NotFoundError):
        await service.get_user(uuid4())


@pytest.mark.asyncio
async def test_create_and_get_user(async_session):
    """
    Verify that a user can be created and retrieved.
    """

    email = f"test-{uuid4()}@example.com"

    service = UserService(async_session)

    user = await service.create_user(
        UserCreate(
            email=email,
            password="securepassword123",
            full_name="Test Surveyor",
            mobile="9876543210",
        ),
        password_hash="hashed-password",
    )

    assert user.email == email
    assert user.full_name == "Test Surveyor"
    assert user.status == "active"

    retrieved_user = await service.get_user(user.id)

    assert retrieved_user.id == user.id
    assert retrieved_user.email == email


@pytest.mark.asyncio
async def test_update_user(async_session):
    """
    Verify that a user's profile can be updated.
    """

    email = f"update-{uuid4()}@example.com"

    service = UserService(async_session)

    user = await service.create_user(
        UserCreate(
            email=email,
            password="securepassword123",
            full_name="Original Name",
        ),
        password_hash="hashed-password",
    )

    updated_user = await service.update_user(
        user.id,
        UserUpdate(
            full_name="Updated Name",
            mobile="9999999999",
        ),
    )

    assert updated_user.full_name == "Updated Name"
    assert updated_user.mobile == "9999999999"