"""
认证请求 Schema
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """登录请求"""

    username: str
    password: str
    totp_code: str | None = None


class UserCreate(BaseModel):
    """用户创建请求"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class TOTPVerifyRequest(BaseModel):
    """TOTP 验证请求"""

    totp_code: str = Field(..., min_length=6, max_length=6)


# ============ 钱包登录 ============


class WalletNonceRequest(BaseModel):
    """钱包 Nonce 请求"""

    wallet_address: str = Field(..., min_length=42, max_length=42)


class WalletLoginRequest(BaseModel):
    """钱包登录请求"""

    wallet_address: str = Field(..., min_length=42, max_length=42)
    signature: str = Field(...)
    message: str = Field(...)


# ============ API Key ============


class CreateApiKeyRequest(BaseModel):
    """创建 API Key 请求"""

    name: str = Field(..., min_length=1, max_length=50)
    expires_in: int | None = Field(None, description="过期时间（秒），不传则永不过期")
