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
    LoginOrRegisterRequest,
    LoginOrRegisterResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.auth.service import AuthService
from app.database import get_db
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate
from app.users.services import UserService


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


@router.post(
    "/login-or-register",
    response_model=LoginOrRegisterResponse,
    summary="Sign in or create a Surveyor account",
)
async def login_or_register(
    data: LoginOrRegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> LoginOrRegisterResponse:
    """Sign in an existing user, or create and sign in a new user."""

    auth_service = AuthService()
    auth_repository = AuthRepository(session)
    user_repository = UserRepository(session)
    user = await user_repository.get_by_email(data.email)
    is_new_user = user is None

    if is_new_user:
        local_name = data.email.split("@", 1)[0]
        full_name = " ".join(
            part.capitalize()
            for part in local_name.replace(".", " ").replace("_", " ").replace("-", " ").split()
        ) or "Surveyor"

        try:
            await UserService(session).create_user(
                UserCreate(email=data.email, password=data.password, full_name=full_name)
            )
        except ValueError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists. Please sign in.",
            ) from exc

    try:
        response = await auth_service.authenticate(
            LoginRequest(email=data.email, password=data.password),
            auth_repository,
        )
        await session.commit()
        return LoginOrRegisterResponse(**response.model_dump(), is_new_user=is_new_user)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc
