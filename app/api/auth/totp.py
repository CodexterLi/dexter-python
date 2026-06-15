"""
TOTP 两步验证
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthServiceDep, CurrentUser
from app.core.responses import ok
from app.schemas.auth import TOTPSetupResponse, TOTPVerifyRequest, UserResponse

router = APIRouter()


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> Any:
    """设置 TOTP 两步验证"""
    result = await auth_service.setup_totp(current_user.id, current_user.username)
    return ok(data=TOTPSetupResponse(**result).model_dump(by_alias=True))


@router.post("/totp/verify", response_model=UserResponse)
async def verify_totp(
    totp_data: TOTPVerifyRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
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


@router.post("/totp/disable", response_model=UserResponse)
async def disable_totp(
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
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
