"""
Cookie 管理模块
"""

from datetime import UTC, datetime, timedelta

from fastapi import Response

from app.config.settings import settings
from app.core.logging import logger
from packages.common.time import tz

# Cookie 名称
ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"


def _set_cookie(response: Response, key: str, value: str, expires: datetime, debug_name: str) -> None:
    """设置 HTTP-Only Cookie"""
    expires_utc = expires.astimezone(UTC)
    logger.debug(f"设置{debug_name}cookie, 过期时间(UTC): {expires_utc}")

    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        samesite="lax",
        expires=expires_utc,
        path="/",
    )


def set_access_token_cookie(response: Response, access_token: str) -> None:
    """设置访问令牌 Cookie"""
    expires = tz.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    _set_cookie(response, ACCESS_TOKEN_COOKIE_NAME, access_token, expires, "访问令牌")


def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """设置刷新令牌 Cookie"""
    expires = tz.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    _set_cookie(response, REFRESH_TOKEN_COOKIE_NAME, refresh_token, expires, "刷新令牌")


def clear_auth_cookies(response: Response) -> None:
    """清除认证 Cookie"""
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME, path="/")
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_NAME, path="/")
