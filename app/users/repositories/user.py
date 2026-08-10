"""
SurveyAI Backend

Module:
User Repository

Purpose:
Provides database operations for Surveyor accounts.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User


class UserRepository:
    """
    Repository responsible for User database operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        mobile: str | None = None,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            mobile=mobile,
        )

        self.session.add(user)

        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        user: User,
        **fields,
    ) -> User:
        for field, value in fields.items():
            if value is not None:
                setattr(user, field, value)

        await self.session.flush()
        await self.session.refresh(user)

        return user