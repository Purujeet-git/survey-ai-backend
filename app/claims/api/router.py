"""
SurveyAI Backend

Module:
Claim API Router

Purpose:
Provides authenticated API endpoints for claim management.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.claims.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate
from app.claims.services.claim import ClaimService
from app.database import get_db
from app.users.models.user import User


router = APIRouter(
    prefix="/claims",
    tags=["Claims"],
)


@router.post(
    "",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create claim",
)
async def create_claim(
    data: ClaimCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """
    Create a new claim for the authenticated surveyor.
    """

    service = ClaimService(session)

    claim = await service.create_claim(
        current_user.id,
        **data.model_dump(),
    )

    await session.commit()
    
    return ClaimResponse.model_validate(claim)


@router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Get claim",
)
async def get_claim(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """
    Retrieve a claim belonging to the authenticated surveyor.
    """

    service = ClaimService(session)

    claim = await service.get_claim(
        current_user.id,
        claim_id,
    )

    return ClaimResponse.model_validate(claim)


@router.patch(
    "/{claim_id}",
    response_model=ClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Update claim",
)
async def update_claim(
    claim_id: UUID,
    data: ClaimUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """
    Update a claim belonging to the authenticated surveyor.
    """

    service = ClaimService(session)

    claim = await service.update_claim(
        current_user.id,
        claim_id,
        **data.model_dump(exclude_unset=True),
    )
    await session.commit()

    return ClaimResponse.model_validate(claim)


@router.delete(
    "/{claim_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete claim",
)
async def delete_claim(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a claim belonging to the authenticated surveyor.
    """

    service = ClaimService(session)

    await service.delete_claim(
        current_user.id,
        claim_id,
    )
    
    await session.commit()