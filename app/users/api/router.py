"""
SurveyAI Backend

Module:
User API

Purpose:
Provides API endpoints for Surveyor accounts.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.users.schemas import UserCreate, UserResponse, UserUpdate
from app.users.services import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Surveyor account",
)
async def create_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create a new Surveyor account.
    """

    service = UserService(session)

    user = await service.create_user(data)

    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Surveyor account",
)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Retrieve a Surveyor account by ID.
    """

    service = UserService(session)

    user = await service.get_user(user_id)

    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Surveyor account",
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update a Surveyor account.
    """

    service = UserService(session)

    user = await service.update_user(
        user_id,
        data,
    )

    return UserResponse.model_validate(user)