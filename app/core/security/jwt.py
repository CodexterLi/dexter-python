"""JWT 令牌模块."""

from datetime import UTC, datetime, timedelta

import jwt
from pydantic import BaseModel

from app.config.settings import settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class TokenData(BaseModel):
    """令牌数据模型."""

    sub: str | None = None
    exp: int | None = None
    typ: str | None = None


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建访问令牌."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    to_encode["typ"] = TOKEN_TYPE_ACCESS
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建刷新令牌."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode["exp"] = expire
    to_encode["typ"] = TOKEN_TYPE_REFRESH
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, *, expected_type: str | None = None) -> dict:
    """解码 JWT 令牌，并按需校验令牌用途."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub", "typ"]},
    )
    if expected_type is not None and payload.get("typ") != expected_type:
        raise jwt.InvalidTokenError("Token type mismatch")
    return payload
