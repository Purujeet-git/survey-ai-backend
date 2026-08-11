"""
SurveyAI Backend

Module:
Authentication Service

Purpose:
Provides authentication-related security operations.
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.auth.repository import AuthRepository
from app.auth.schemas import LoginRequest, TokenResponse
from app.config import settings


class AuthService:
    """
    Authentication service.

    Handles password hashing, authentication,
    access tokens, refresh tokens, and sessions.
    """

    def __init__(self) -> None:
        self.password_hasher = PasswordHash.recommended()

    def hash_password(self, password: str) -> str:
        """
        Hash a plaintext password.

        The plaintext password must never be persisted.
        """

        return self.password_hasher.hash(password)

    def verify_password(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        """
        Verify a plaintext password against its stored hash.
        """

        return self.password_hasher.verify(
            password,
            password_hash,
        )

    def create_access_token(
        self,
        user_id: str,
    ) -> str:
        """
        Create a short-lived JWT access token.
        """

        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        payload = {
            "sub": user_id,
            "type": "access",
            "iat": now,
            "exp": expires_at,
        }

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def create_refresh_token(
        self,
        session_id: uuid.UUID,
    ) -> str:
        """
        Create a cryptographically secure opaque refresh token.

        The session ID is included so that the server can locate
        the corresponding authentication session without storing
        the raw refresh token.
        """

        secret = secrets.token_urlsafe(64)

        return f"{session_id}.{secret}"

    def hash_refresh_token(
        self,
        refresh_token: str,
    ) -> str:
        """
        Hash a refresh token before database persistence.
        """

        return self.password_hasher.hash(refresh_token)

    def verify_refresh_token(
        self,
        refresh_token: str,
        refresh_token_hash: str,
    ) -> bool:
        """
        Verify a refresh token against its stored hash.
        """

        return self.password_hasher.verify(
            refresh_token,
            refresh_token_hash,
        )

    async def authenticate(
        self,
        data: LoginRequest,
        repository: AuthRepository,
    ) -> TokenResponse:
        """
        Authenticate a user and create an authentication session.
        """

        user = await repository.get_user_by_email(
            data.email
        )

        if user is None:
            raise ValueError("Invalid email or password.")

        if user.status != "active":
            raise ValueError("Invalid email or password.")

        password_valid = self.verify_password(
            data.password,
            user.password_hash,
        )

        if not password_valid:
            raise ValueError("Invalid email or password.")

        access_token = self.create_access_token(
            str(user.id)
        )

        session_id = uuid.uuid4()

        refresh_token = self.create_refresh_token(
            session_id
        )

        refresh_token_hash = self.hash_refresh_token(
            refresh_token
        )

        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        await repository.create_session(
            session_id=session_id,
            user_id=user.id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
        repository: AuthRepository,
    ) -> TokenResponse:
        """
        Validate a refresh token and issue a new access token.
        """

        try:
            session_id_string, _secret = refresh_token.split(
                ".",
                maxsplit=1,
            )

            session_id = uuid.UUID(session_id_string)

        except (ValueError, AttributeError):
            raise ValueError("Invalid refresh token.")

        auth_session = await repository.get_session_by_id(
            session_id
        )

        if auth_session is None:
            raise ValueError("Invalid refresh token.")

        if auth_session.revoked_at is not None:
            raise ValueError("Invalid refresh token.")

        now = datetime.now(timezone.utc)

        if auth_session.expires_at <= now:
            raise ValueError("Invalid refresh token.")

        if not self.verify_refresh_token(
            refresh_token,
            auth_session.refresh_token_hash,
        ):
            raise ValueError("Invalid refresh token.")

        auth_session.last_used_at = now

        access_token = self.create_access_token(
            str(auth_session.user_id)
        )

        await repository.session.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(
        self,
        refresh_token: str,
        repository: AuthRepository,
    ) -> None:
        """
        Revoke the session associated with a refresh token.
        """

        try:
            session_id_string, _secret = refresh_token.split(
                ".",
                maxsplit=1,
            )

            session_id = uuid.UUID(session_id_string)

        except (ValueError, AttributeError):
            raise ValueError("Invalid refresh token.")

        auth_session = await repository.get_session_by_id(
            session_id
        )

        if auth_session is None:
            raise ValueError("Invalid refresh token.")

        if auth_session.revoked_at is not None:
            return

        if not self.verify_refresh_token(
            refresh_token,
            auth_session.refresh_token_hash,
        ):
            raise ValueError("Invalid refresh token.")

        await repository.revoke_session(
            auth_session
        )