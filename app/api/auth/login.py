"""
登录、登出、刷新令牌
"""

from typing import Any

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.auth.dependencies import get_auth_service, get_current_active_user
from app.core.security import (
    REFRESH_TOKEN_COOKIE_NAME,
    clear_auth_cookies,
    decode_token,
    set_access_token_cookie,
    set_refresh_token_cookie,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login")
async def login(
    response: Response,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """用户登录"""
    try:
        _user, tokens = await auth_service.login(
            username=login_data.username,
            password=login_data.password,
            totp_code=login_data.totp_code,
        )

        set_access_token_cookie(response, tokens["access_token"])
        set_refresh_token_cookie(response, tokens["refresh_token"])

        # 直接返回数据，Cookie 会通过 response 对象设置
        return TokenResponse(
            token_type="bearer",
            expires_in=tokens["expires_in"],
        ).model_dump(by_alias=True)

    except ValueError as e:
        error_msg = str(e)
        if "需要TOTP" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            ) from None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
        ) from None


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """刷新访问令牌"""
    refresh_token_cookie = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    try:
        payload = decode_token(refresh_token_cookie)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        _user, tokens = await auth_service.refresh_tokens(username)

        set_access_token_cookie(response, tokens["access_token"])
        set_refresh_token_cookie(response, tokens["refresh_token"])

        # 直接返回数据，Cookie 会通过 response 对象设置
        return TokenResponse(
            token_type="bearer",
            expires_in=tokens["expires_in"],
        ).model_dump(by_alias=True)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from None
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_active_user),
) -> None:
    """用户登出"""
    clear_auth_cookies(response)
