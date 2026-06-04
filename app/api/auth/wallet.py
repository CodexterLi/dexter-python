"""
钱包登录端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.auth.dependencies import get_auth_service
from app.core.security import set_access_token_cookie, set_refresh_token_cookie
from app.schemas.auth import (
    WalletLoginRequest,
    WalletLoginResponse,
    WalletNonceRequest,
    WalletNonceResponse,
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/wallet/nonce")
async def get_wallet_nonce(
    req: WalletNonceRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """获取钱包签名随机数"""
    nonce, message = await auth_service.get_wallet_nonce(req.wallet_address)
    return WalletNonceResponse(nonce=nonce, message=message).model_dump()


@router.post("/wallet/login")
async def wallet_login(
    response: Response,
    req: WalletLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Any:
    """钱包登录（签名验证 + 自动注册）"""
    try:
        user, tokens = await auth_service.wallet_login(
            wallet_address=req.wallet_address,
            signature=req.signature,
            message=req.message,
        )

        set_access_token_cookie(response, tokens["access_token"])
        set_refresh_token_cookie(response, tokens["refresh_token"])

        return WalletLoginResponse(
            user_id=user.id,
            wallet_address=user.wallet_address,
        ).model_dump()

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from None
