"""
API Key 管理端点
"""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, status

from app.api.dependencies import AuthServiceDep, CurrentUser
from app.schemas.auth import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
)

router = APIRouter()


@router.post("/api-keys", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    req: CreateApiKeyRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
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


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> Any:
    """列出当前用户的所有 API Key"""
    keys = await auth_service.list_api_keys(current_user.id)
    return [ApiKeyResponse.model_validate(k).model_dump() for k in keys]


@router.put("/api-keys/{api_key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: Annotated[int, Path(description="API Key ID")],
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> None:
    """吊销 API Key"""
    revoked = await auth_service.revoke_api_key(api_key_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: Annotated[int, Path(description="API Key ID")],
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
) -> None:
    """删除 API Key"""
    deleted = await auth_service.delete_api_key(api_key_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")
