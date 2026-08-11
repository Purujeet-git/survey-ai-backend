"""
Tests for the Surveyor account service.
"""

from uuid import uuid4

import pytest

from app.shared.exceptions import NotFoundError
from app.users.schemas import UserCreate, UserUpdate
from app.users.services import UserService


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
        ),
    )

    assert user.email == email
    assert user.full_name == "Test Surveyor"
    assert user.status == "active"

    # Password must be hashed before persistence.
    assert user.password_hash != "securepassword123"
    assert user.password_hash

    retrieved_user = await service.get_user(user.id)

    assert retrieved_user.id == user.id
    assert retrieved_user.email == email
    assert retrieved_user.full_name == "Test Surveyor"
    assert retrieved_user.password_hash != "securepassword123"


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
    )

    original_password_hash = user.password_hash

    updated_user = await service.update_user(
        user.id,
        UserUpdate(
            full_name="Updated Name",
            mobile="9999999999",
        ),
    )

    assert updated_user.full_name == "Updated Name"
    assert updated_user.mobile == "9999999999"

    # Updating the profile must not alter the password hash.
    assert updated_user.password_hash == original_password_hash