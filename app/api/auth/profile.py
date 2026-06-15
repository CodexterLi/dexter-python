"""
用户信息
"""

from typing import Any

from fastapi import APIRouter

from app.api.dependencies import CurrentUser
from app.core.responses import ok
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
) -> Any:
    """获取当前用户信息"""
    return ok(data=UserResponse.from_user(current_user))
