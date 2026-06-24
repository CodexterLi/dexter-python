from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config.settings import settings
from app.core.security.jwt import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_create_access_token_sets_access_type_and_utc_expiration() -> None:
    token = create_access_token({"sub": "alice"}, expires_delta=timedelta(minutes=5))

    payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)

    assert payload["sub"] == "alice"
    assert payload["typ"] == TOKEN_TYPE_ACCESS
    expires_in = payload["exp"] - int(datetime.now(UTC).timestamp())
    assert 0 < expires_in <= 300


def test_create_refresh_token_sets_refresh_type() -> None:
    token = create_refresh_token({"sub": "alice"}, expires_delta=timedelta(days=1))

    payload = decode_token(token, expected_type=TOKEN_TYPE_REFRESH)

    assert payload["sub"] == "alice"
    assert payload["typ"] == TOKEN_TYPE_REFRESH


def test_decode_token_rejects_refresh_token_when_access_expected() -> None:
    token = create_refresh_token({"sub": "alice"})

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, expected_type=TOKEN_TYPE_ACCESS)


def test_decode_token_rejects_access_token_when_refresh_expected() -> None:
    token = create_access_token({"sub": "alice"})

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, expected_type=TOKEN_TYPE_REFRESH)


def test_decode_token_requires_standard_claims() -> None:
    token = jwt.encode({"sub": "alice"}, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_token(token)


def test_decode_token_rejects_expired_token() -> None:
    token = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
