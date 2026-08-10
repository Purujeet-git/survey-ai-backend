"""
SurveyAI Backend

Module:
User Service

Purpose:
Contains business logic for Surveyor accounts.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.exceptions import NotFoundError
from app.users.models import User
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserUpdate


class UserService:
    """
    Service layer for Surveyor accounts.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    async def create_user(
        self,
        data: UserCreate,
        password_hash: str,
    ) -> User:
        existing_user = await self.repository.get_by_email(
            data.email
        )

        if existing_user:
            raise ValueError(
                "A user with this email already exists."
            )

        user = await self.repository.create(
            email=data.email,
            password_hash=password_hash,
            full_name=data.full_name,
            mobile=data.mobile,
        )

        await self.session.commit()

        return user

    async def get_user(
        self,
        user_id: UUID,
    ) -> User:
        user = await self.repository.get_by_id(user_id)

        if user is None:
            raise NotFoundError(
                "Surveyor account not found."
            )

        return user

    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate,
    ) -> User:
        user = await self.get_user(user_id)

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        if "email" in update_data:
            existing_user = await self.repository.get_by_email(
                update_data["email"]
            )

            if (
                existing_user
                and existing_user.id != user.id
            ):
                raise ValueError(
                    "A user with this email already exists."
                )

        user = await self.repository.update(
            user,
            **update_data,
        )

        await self.session.commit()

        return user