"""
SurveyAI Backend

Module:
Authentication Dependencies

Purpose:
Provides reusable dependencies for authenticated API requests.
"""

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repository import AuthRepository
from app.config import settings
from app.database import get_db
from app.users.models import User


bearer_scheme = HTTPBearer(
    auto_error=False,
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the currently authenticated user from a JWT access token.

    Authentication requirements:

    - Authorization header must contain a Bearer token.
    - JWT signature must be valid.
    - Token must not be expired.
    - Token type must be 'access'.
    - Subject must contain a valid user UUID.
    - User must exist.
    - User must be active.
    """

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    if credentials.scheme.lower() != "bearer":
        raise unauthorized

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise unauthorized

    if payload.get("type") != "access":
        raise unauthorized

    subject = payload.get("sub")

    if not subject:
        raise unauthorized

    try:
        user_id = UUID(subject)
    except (ValueError, TypeError):
        raise unauthorized

    repository = AuthRepository(session)

    user = await repository.get_user_by_id(user_id)

    if user is None:
        raise unauthorized

    if user.status != "active":
        raise unauthorized

    return user