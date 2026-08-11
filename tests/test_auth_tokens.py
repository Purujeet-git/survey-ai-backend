"""
Tests for authentication token operations.
"""

from uuid import uuid4

import jwt

from app.auth.service import AuthService
from app.config import settings


def test_create_access_token():
    service = AuthService()

    user_id = str(uuid4())

    token = service.create_access_token(user_id)

    assert token
    assert isinstance(token, str)


def test_access_token_contains_expected_claims():
    service = AuthService()

    user_id = str(uuid4())

    token = service.create_access_token(user_id)

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload


def test_access_token_cannot_be_decoded_with_wrong_secret():
    service = AuthService()

    user_id = str(uuid4())

    token = service.create_access_token(user_id)

    try:
        jwt.decode(
            token,
            "incorrect-secret",
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert False, "Token should not verify with the wrong secret."

    except jwt.InvalidSignatureError:
        pass


def test_create_refresh_token():
    service = AuthService()

    token = service.create_refresh_token(str(uuid4()))

    assert token
    assert isinstance(token, str)


def test_refresh_tokens_are_different():
    service = AuthService()

    first = service.create_refresh_token(str(uuid4()))
    second = service.create_refresh_token(str(uuid4()))

    assert first != second


def test_refresh_token_can_be_hashed_and_verified():
    service = AuthService()

    token = service.create_refresh_token(str(uuid4()))

    token_hash = service.hash_refresh_token(token)

    assert token_hash != token

    assert service.verify_refresh_token(
        token,
        token_hash,
    )


def test_wrong_refresh_token_fails_verification():
    service = AuthService()

    token = service.create_refresh_token(str(uuid4()))
    wrong_token = service.create_refresh_token(str(uuid4()))

    token_hash = service.hash_refresh_token(token)

    assert not service.verify_refresh_token(
        wrong_token,
        token_hash,
    )