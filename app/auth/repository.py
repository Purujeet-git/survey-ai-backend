"""
SurveyAI Backend

Module:
Authentication Repository

Purpose:
Provides database operations for authentication.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthSession
from app.users.models import User
from datetime import datetime, timezone


class AuthRepository:
    """
    Repository for authentication-related database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Retrieve a user by email address.
        """

        result = await self.session.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()

    async def create_session(
        self,
        session_id:UUID,
        user_id: UUID,
        refresh_token_hash: str,
        expires_at,
    ) -> AuthSession:
        """
        Create a new authentication session.
        """

        session = AuthSession(
            id=session_id,
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        self.session.add(session)

        await self.session.flush()

        return session
    
    async def get_session_by_id(
        self,
        session_id: UUID,
    ) -> AuthSession | None:
        """
        Retrieve an authentication session by ID.
        """

        result = await self.session.execute(
            select(AuthSession).where(
                AuthSession.id == session_id
            )
        )

        return result.scalar_one_or_none()

    
    
        

    async def get_user_sessions(
        self,
        user_id: UUID,
    ) -> list[AuthSession]:
        """
        Retrieve authentication sessions belonging to a user.
        """

        result = await self.session.execute(
            select(AuthSession).where(
                AuthSession.user_id == user_id
            )
        )

        return list(result.scalars().all())


    async def revoke_session(
        self,
        auth_session: AuthSession,
    ) -> None:
        """
        Revoke an authentication session.
        """

        auth_session.revoked_at = datetime.now(timezone.utc)

        await self.session.flush()
    
    
    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        """
        Retrieve a user by ID.
        """

        result = await self.session.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()