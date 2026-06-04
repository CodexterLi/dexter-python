"""
用户注册
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.dependencies import get_auth_service, get_current_active_user
from app.core.responses import created
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """注册新用户（需要管理员权限）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    try:
        user = await auth_service.register_user(user_in)
        return created(data=UserResponse.from_user(user))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
