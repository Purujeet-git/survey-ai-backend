"""
SurveyAI Backend

Module:
Authentication API

Purpose:
Provides authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repository import AuthRepository
from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.auth.service import AuthService
from app.database import get_db


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate Surveyor",
)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a Surveyor and issue access/refresh tokens.
    """

    service = AuthService()
    repository = AuthRepository(session)

    try:
        response = await service.authenticate(
            data,
            repository,
        )

        await session.commit()

        return response

    except ValueError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc
        
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Issue a new access token using a valid refresh token.
    """

    service = AuthService()
    repository = AuthRepository(session)

    try:
        response = await service.refresh_access_token(
            data.refresh_token,
            repository,
        )

        await session.commit()

        return response

    except ValueError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc
        
        
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout Surveyor",
)
async def logout(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke the refresh-token session.
    """

    service = AuthService()
    repository = AuthRepository(session)

    try:
        await service.logout(
            data.refresh_token,
            repository,
        )

        await session.commit()

    except ValueError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc