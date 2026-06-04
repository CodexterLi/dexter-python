"""
TOTP 两步验证
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.dependencies import get_auth_service, get_current_active_user
from app.core.responses import ok
from app.models.user import User
from app.schemas.auth import TOTPSetupResponse, TOTPVerifyRequest, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/totp/setup")
async def setup_totp(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """设置 TOTP 两步验证"""
    result = await auth_service.setup_totp(current_user.id, current_user.username)
    return ok(data=TOTPSetupResponse(**result).model_dump(by_alias=True))


@router.post("/totp/verify")
async def verify_totp(
    totp_data: TOTPVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """验证并启用 TOTP 两步验证"""
    try:
        updated_user = await auth_service.verify_and_enable_totp(
            user_id=current_user.id,
            totp_secret=current_user.totp_secret,
            totp_code=totp_data.totp_code,
        )
        return ok(data=UserResponse.from_user(updated_user))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None


@router.post("/totp/disable")
async def disable_totp(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """禁用 TOTP 两步验证"""
    try:
        updated_user = await auth_service.disable_totp(
            user_id=current_user.id,
            totp_enabled=current_user.totp_enabled,
        )
        return ok(data=UserResponse.from_user(updated_user))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
