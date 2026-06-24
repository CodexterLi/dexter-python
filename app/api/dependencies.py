"""
API 层通用依赖注入

集中放置可跨业务路由复用的 FastAPI 依赖。
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    TOKEN_TYPE_ACCESS,
    decode_token,
)
from app.db.postgres import get_db
from app.models.user import User
from app.services.auth import AuthService

DBSessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_auth_service(db: DBSessionDep) -> AuthService:
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


async def get_current_user(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    token: Annotated[str | None, Depends(get_token)],
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
        payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
        username = payload.get("sub")
        if not username:
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception from None

    user = await auth_service.get_user_by_username(username)
    if not user:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user


# ============ API Key 认证 ============


async def get_current_user_from_api_key(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
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
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    灵活认证：优先 JWT (Cookie/Header)，其次 API Key

    适用于同时支持浏览器和程序化访问的端点
    """
    # 1. 尝试 JWT
    token = await get_token(request)
    if token:
        try:
            payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
            username = payload.get("sub")
            if username:
                user = await auth_service.get_user_by_username(username)
                if user:
                    return user
        except jwt.PyJWTError:
            pass

    # 2. 尝试 API Key
    api_key = request.headers.get("X-Api-Key")
    api_secret = request.headers.get("X-Api-Secret")
    if api_key and api_secret:
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
        payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
        username = payload.get("sub")
        if not username:
            return None

        async for db in get_db():
            auth_service = AuthService(db)
            user = await auth_service.get_user_by_username(username)
            if user and user.is_active:
                return user
            break

        return None
    except jwt.PyJWTError:
        return None
    except Exception as e:
        logger.error(f"从令牌获取用户失败: {e}")
        return None


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]
SuperUser = Annotated[User, Depends(get_current_superuser)]
FlexibleCurrentUser = Annotated[User, Depends(get_current_user_flexible)]
