"""
用户信息
"""

from typing import Any

from fastapi import APIRouter, Depends

from app.api.auth.dependencies import get_current_active_user
from app.core.responses import ok
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter()


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取当前用户信息"""
    return ok(data=UserResponse.from_user(current_user))
