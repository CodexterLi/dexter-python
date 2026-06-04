"""
API Key 管理端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth.dependencies import get_auth_service, get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    req: CreateApiKeyRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """创建 API Key（secret 仅返回一次）"""
    ak, secret = await auth_service.create_api_key(
        user_id=current_user.id,
        name=req.name,
        expires_in=req.expires_in,
    )

    return CreateApiKeyResponse(
        id=ak.id,
        name=ak.name,
        key=ak.key,
        secret=secret,
        expires_at=ak.expires_at,
        created_at=ak.created_at,
    ).model_dump()


@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """列出当前用户的所有 API Key"""
    keys = await auth_service.list_api_keys(current_user.id)
    return [ApiKeyResponse.model_validate(k).model_dump() for k in keys]


@router.put("/api-keys/{api_key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """吊销 API Key"""
    revoked = await auth_service.revoke_api_key(api_key_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """删除 API Key"""
    deleted = await auth_service.delete_api_key(api_key_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")
