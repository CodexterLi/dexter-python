"""
JWT 令牌模块
"""

from datetime import datetime, timedelta

import jwt
from pydantic import BaseModel

from app.config.settings import settings
from app.utils.timezone import tz


class TokenData(BaseModel):
    """令牌数据模型"""

    username: str | None = None
    exp: datetime | None = None


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = tz.now_naive() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = tz.now_naive() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解码JWT令牌"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
