"""
SurveyAI Backend

Module:
Authentication Service

Purpose:
Provides authentication-related security operations.
"""

from pwdlib import PasswordHash


class AuthService:
    """
    Authentication service.

    Handles password hashing and verification.
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