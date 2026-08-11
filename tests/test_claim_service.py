"""
Tests for the Claim service.
"""

from uuid import uuid4

import pytest

from app.claims.models.claim import Claim
from app.claims.services.claim import ClaimService
from app.users.models.user import User
from app.shared.exceptions import NotFoundError


async def create_test_user(async_session):
    """
    Create a real user for claim ownership tests.
    """

    user = User(
        email=f"claim-service-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name="Claim Service Surveyor",
    )

    async_session.add(user)
    await async_session.flush()

    return user


@pytest.mark.asyncio
async def test_create_claim(async_session):
    """
    Verify that a claim can be created for a surveyor.
    """

    user = await create_test_user(async_session)

    service = ClaimService(async_session)

    claim = await service.create_claim(
        user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    assert claim is not None
    assert claim.user_id == user.id
    assert claim.status == "draft"


@pytest.mark.asyncio
async def test_get_claim(async_session):
    """
    Verify that a surveyor can retrieve their own claim.
    """

    user = await create_test_user(async_session)

    service = ClaimService(async_session)

    claim = await service.create_claim(
        user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    retrieved_claim = await service.get_claim(
        user.id,
        claim.id,
    )

    assert retrieved_claim.id == claim.id
    assert retrieved_claim.user_id == user.id


@pytest.mark.asyncio
async def test_get_claim_rejects_wrong_user(async_session):
    """
    Verify that a surveyor cannot access another
    surveyor's claim.
    """

    owner = await create_test_user(async_session)
    other_user = await create_test_user(async_session)

    service = ClaimService(async_session)

    claim = await service.create_claim(
        owner.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    with pytest.raises(NotFoundError):
        await service.get_claim(
            other_user.id,
            claim.id,
        )


@pytest.mark.asyncio
async def test_update_claim(async_session):
    """
    Verify that a surveyor can update their own claim.
    """

    user = await create_test_user(async_session)

    service = ClaimService(async_session)

    claim = await service.create_claim(
        user.id,
        claim_number=f"CLM-{uuid4()}",
        owner_name="Original Owner",
        status="draft",
        extra_data={},
    )

    updated_claim = await service.update_claim(
        user.id,
        claim.id,
        owner_name="Updated Owner",
        cause_of_accident="Rear-end collision",
    )

    assert updated_claim.owner_name == "Updated Owner"
    assert updated_claim.cause_of_accident == "Rear-end collision"


@pytest.mark.asyncio
async def test_update_claim_rejects_wrong_user(async_session):
    """
    Verify that a surveyor cannot update another
    surveyor's claim.
    """

    owner = await create_test_user(async_session)
    other_user = await create_test_user(async_session)

    service = ClaimService(async_session)

    claim = await service.create_claim(
        owner.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    with pytest.raises(NotFoundError):
        await service.update_claim(
            other_user.id,
            claim.id,
            owner_name="Unauthorized Update",
        )


@pytest.mark.asyncio
async def test_delete_claim(async_session):
    """
    Verify that a surveyor can delete their own claim.
    """

    user = await create_test_user(async_session)

    service = ClaimService(async_session)

    claim = await service.create_claim(
        user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    await service.delete_claim(
        user.id,
        claim.id,
    )

    with pytest.raises(NotFoundError):
        await service.get_claim(
            user.id,
            claim.id,
        )