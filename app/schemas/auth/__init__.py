"""
认证相关 Schema
"""

from app.schemas.auth.requests import (
    CreateApiKeyRequest,
    LoginRequest,
    TOTPVerifyRequest,
    UserCreate,
    WalletLoginRequest,
    WalletNonceRequest,
)
from app.schemas.auth.responses import (
    ApiKeyResponse,
    CreateApiKeyResponse,
    TokenResponse,
    TOTPSetupResponse,
    UserResponse,
    WalletLoginResponse,
    WalletNonceResponse,
)

__all__ = [
    "ApiKeyResponse",
    "CreateApiKeyRequest",
    "CreateApiKeyResponse",
    "LoginRequest",
    "TOTPSetupResponse",
    "TOTPVerifyRequest",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    "WalletLoginRequest",
    "WalletLoginResponse",
    "WalletNonceRequest",
    "WalletNonceResponse",
]
