"""
Tests for the Claim repository.
"""

from uuid import uuid4

import pytest

from app.database import models  # noqa: F401
from app.claims.models.claim import Claim
from app.claims.repositories.claim import ClaimRepository
from app.users.models.user import User


async def create_test_user(async_session):
    user = User(
        email=f"claim-test-{uuid4()}@example.com",
        password_hash="test-password-hash",
        full_name = "Claim Test Surveyor",
    )
    async_session.add(user)
    await async_session.flush()
    
    return user


@pytest.mark.asyncio
async def test_create_and_get_claim(async_session):
    """
    Verify that a claim can be created and retrieved by ID.
    """

    user = await create_test_user(async_session)
    

    claim = Claim(
        user_id=user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    repository = ClaimRepository(async_session)
    
    await repository.create(claim)
    
    result = await repository.get_by_id(claim.id)
    
    assert result is not None
    assert result.id == claim.id

    created_claim = await repository.create(claim)

    assert created_claim.id == claim.id
    assert created_claim.user_id == user.id
    assert created_claim.claim_number == claim.claim_number

    retrieved_claim = await repository.get_by_id(claim.id)

    assert retrieved_claim is not None
    assert retrieved_claim.id == claim.id
    assert retrieved_claim.claim_number == claim.claim_number


@pytest.mark.asyncio
async def test_get_claim_by_claim_number(async_session):
    """
    Verify that a claim can be retrieved using its
    claim number within a surveyor account.
    """

    user = await create_test_user(async_session)
    claim_number = f"CLM-{uuid4()}"

    claim = Claim(
        user_id=user.id,
        claim_number=claim_number,
        status="draft",
        extra_data={},
    )

    repository = ClaimRepository(async_session)

    await repository.create(claim)

    retrieved_claim = await repository.get_by_claim_number(
        user.id,
        claim_number,
    )

    assert retrieved_claim is not None
    assert retrieved_claim.id == claim.id
    assert retrieved_claim.user_id == user.id


@pytest.mark.asyncio
async def test_claim_number_is_scoped_to_user(async_session):
    """
    Verify that a claim belonging to one surveyor cannot
    be retrieved using another surveyor's ID.
    """

    owner_user = await create_test_user(async_session)
    other_user = await create_test_user(async_session)

    claim_number = f"CLM-{uuid4()}"

    claim = Claim(
        user_id=owner_user.id,
        claim_number=claim_number,
        status="draft",
        extra_data={},
    )

    repository = ClaimRepository(async_session)

    await repository.create(claim)

    retrieved_claim = await repository.get_by_claim_number(
        other_user.id,
        claim_number,
    )

    assert retrieved_claim is None


@pytest.mark.asyncio
async def test_list_claims_by_user(async_session):
    """
    Verify that only claims belonging to the requested
    surveyor are returned.
    """

    user = await create_test_user(async_session)
    other_user = await create_test_user(async_session)

    first_claim = Claim(
        user_id=user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    second_claim = Claim(
        user_id=user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    other_claim = Claim(
        user_id=other_user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    repository = ClaimRepository(async_session)

    await repository.create(first_claim)
    await repository.create(second_claim)
    await repository.create(other_claim)

    claims = await repository.list_by_user(user.id)

    claim_ids = {claim.id for claim in claims}

    assert first_claim.id in claim_ids
    assert second_claim.id in claim_ids
    assert other_claim.id not in claim_ids


@pytest.mark.asyncio
async def test_update_claim(async_session):
    """
    Verify that an existing claim can be updated.
    """
    user = await create_test_user(async_session)
    
    claim = Claim(
        user_id=user.id,
        claim_number=f"CLM-{uuid4()}",
        owner_name="Original Owner",
        status="draft",
        extra_data={},
    )

    repository = ClaimRepository(async_session)

    await repository.create(claim)

    claim.owner_name = "Updated Owner"
    claim.status = "in_progress"

    updated_claim = await repository.update(claim)

    assert updated_claim.owner_name == "Updated Owner"
    assert updated_claim.status == "in_progress"

    retrieved_claim = await repository.get_by_id(claim.id)

    assert retrieved_claim is not None
    assert retrieved_claim.owner_name == "Updated Owner"
    assert retrieved_claim.status == "in_progress"


@pytest.mark.asyncio
async def test_delete_claim(async_session):
    """
    Verify that a claim can be deleted.
    """
    
    user = await create_test_user(async_session)

    claim = Claim(
        user_id=user.id,
        claim_number=f"CLM-{uuid4()}",
        status="draft",
        extra_data={},
    )

    repository = ClaimRepository(async_session)

    await repository.create(claim)

    claim_id = claim.id

    await repository.delete(claim)

    deleted_claim = await repository.get_by_id(claim_id)

    assert deleted_claim is None