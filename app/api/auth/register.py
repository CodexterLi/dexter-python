"""
用户注册
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import AuthServiceDep, CurrentUser
from app.core.responses import created
from app.schemas.auth import UserCreate, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
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
