"""
认证模块依赖注入

提供认证相关的 FastAPI 依赖函数
"""

from datetime import datetime

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    decode_token,
)
from app.db.postgres import get_db
from app.models.user import User
from app.services.auth import AuthService
from packages.common.time import tz


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)


# ============ 令牌获取 ============


async def get_token_from_cookie(request: Request) -> str | None:
    """从 Cookie 获取令牌"""
    return request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)


async def get_token_from_header(request: Request) -> str | None:
    """从 Authorization 头获取令牌 (支持 Bearer/MCP)"""
    auth = request.headers.get("Authorization")
    if not auth:
        return None

    for prefix in ("Bearer ", "MCP "):
        if auth.startswith(prefix):
            return auth[len(prefix) :]
    return None


async def get_token(request: Request) -> str | None:
    """获取令牌 (优先 Header，其次 Cookie)"""
    return await get_token_from_header(request) or await get_token_from_cookie(request)


# ============ 用户认证依赖 ============


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """通过用户名获取用户"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(get_token),
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise credentials_exception

        exp_timestamp = payload.get("exp")
        if exp_timestamp and tz.now_naive() > datetime.fromtimestamp(exp_timestamp):
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception from None

    user = await get_user_by_username(db, username)
    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user


# ============ API Key 认证 ============


async def get_current_user_from_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    通过 X-Api-Key + X-Api-Secret 认证

    用于程序化 API 访问（SDK、脚本等）
    """
    api_key = request.headers.get("X-Api-Key")
    api_secret = request.headers.get("X-Api-Secret")

    if not api_key or not api_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing X-Api-Key or X-Api-Secret",
        )

    auth_service = AuthService(db)
    try:
        return await auth_service.authenticate_api_key(api_key, api_secret)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from None


# ============ 灵活认证 (JWT 或 API Key) ============


async def get_current_user_flexible(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    灵活认证：优先 JWT (Cookie/Header)，其次 API Key

    适用于同时支持浏览器和程序化访问的端点
    """
    # 1. 尝试 JWT
    token = await get_token(request)
    if token:
        try:
            payload = decode_token(token)
            username = payload.get("sub")
            if username:
                exp_timestamp = payload.get("exp")
                if not exp_timestamp or tz.now_naive() <= datetime.fromtimestamp(exp_timestamp):
                    user = await get_user_by_username(db, username)
                    if user:
                        return user
        except jwt.PyJWTError:
            pass

    # 2. 尝试 API Key
    api_key = request.headers.get("X-Api-Key")
    api_secret = request.headers.get("X-Api-Secret")
    if api_key and api_secret:
        auth_service = AuthService(db)
        try:
            return await auth_service.authenticate_api_key(api_key, api_secret)
        except ValueError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ============ 工具函数 ============


async def get_current_user_from_token(token: str) -> User | None:
    """从令牌获取用户（用于 WebSocket 等场景）"""
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            return None

        exp = payload.get("exp")
        if exp and tz.now_naive() > datetime.fromtimestamp(exp):
            return None

        from app.db.postgres import get_db

        async for db in get_db():
            user = await get_user_by_username(db, username)
            if user and user.is_active:
                return user
            break

        return None
    except jwt.PyJWTError:
        return None
    except Exception as e:
        logger.error(f"从令牌获取用户失败: {e}")
        return None
