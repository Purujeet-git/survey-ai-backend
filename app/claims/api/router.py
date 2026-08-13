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
from app.claims.schemas.claim import ClaimCreate, ClaimResponse, ClaimStatusUpdate, ClaimUpdate
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
    Create a new claim for the authenticated surveyor/organization.
    """

    service = ClaimService(session)

    payload = data.model_dump()
    if not payload.get("organization_id") and current_user.organization_id:
        payload["organization_id"] = current_user.organization_id

    claim = await service.create_claim(
        current_user.id,
        **payload,
    )

    return ClaimResponse.model_validate(claim)


@router.get(
    "",
    response_model=list[ClaimResponse],
    status_code=status.HTTP_200_OK,
    summary="List claims",
)
async def list_claims(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ClaimResponse]:
    """
    List claims accessible by the authenticated user/organization.
    """

    service = ClaimService(session)
    claims = await service.list_claims(
        user_id=current_user.id if not current_user.organization_id else None,
        organization_id=current_user.organization_id,
    )

    return [ClaimResponse.model_validate(c) for c in claims]


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
    Retrieve a claim by ID.
    """

    service = ClaimService(session)

    claim = await service.get_claim(
        user_id=current_user.id if current_user.role != "super_admin" else None,
        claim_id=claim_id,
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
    Update a claim.
    """

    service = ClaimService(session)

    claim = await service.update_claim(
        user_id=current_user.id if current_user.role != "super_admin" else None,
        claim_id=claim_id,
        **data.model_dump(exclude_unset=True),
    )

    return ClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/status",
    response_model=ClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Transition claim status",
)
async def update_claim_status(
    claim_id: UUID,
    data: ClaimStatusUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """
    Transition a claim's status through the workflow state machine.
    """

    service = ClaimService(session)

    claim = await service.update_claim_status(
        user_id=current_user.id,
        claim_id=claim_id,
        new_status=data.status,
        reason=data.reason,
    )

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
    Delete a claim.
    """

    service = ClaimService(session)

    await service.delete_claim(
        user_id=current_user.id if current_user.role != "super_admin" else None,
        claim_id=claim_id,
    )
