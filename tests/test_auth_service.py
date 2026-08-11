"""
Tests for authentication security services.
"""

from app.auth.service import AuthService


def test_password_hash_is_not_plaintext():
    service = AuthService()

    password = "securepassword123"

    password_hash = service.hash_password(password)

    assert password_hash != password


def test_password_hash_can_be_verified():
    service = AuthService()

    password = "securepassword123"

    password_hash = service.hash_password(password)

    assert service.verify_password(
        password,
        password_hash,
    )


def test_wrong_password_fails_verification():
    service = AuthService()

    password_hash = service.hash_password(
        "securepassword123"
    )

    assert not service.verify_password(
        "wrongpassword",
        password_hash,
    )


def test_same_password_generates_different_hashes():
    service = AuthService()

    password = "securepassword123"

    first_hash = service.hash_password(password)
    second_hash = service.hash_password(password)

    assert first_hash != second_hash