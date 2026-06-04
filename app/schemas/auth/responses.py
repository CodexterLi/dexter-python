"""
认证响应 Schema
"""

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from app.models.user import User


class UserResponse(BaseModel):
    """用户信息响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    totp_enabled: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_user(cls, user: "User") -> dict:
        """将用户对象转换为响应字典"""
        return cls.model_validate(user).model_dump()


class TokenResponse(BaseModel):
    """令牌响应"""

    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）


class TOTPSetupResponse(BaseModel):
    """TOTP 设置响应"""

    secret: str
    uri: str


# ============ 钱包登录 ============


class WalletNonceResponse(BaseModel):
    """钱包 Nonce 响应"""

    nonce: str
    message: str


class WalletLoginResponse(BaseModel):
    """钱包登录响应"""

    user_id: int
    wallet_address: str


# ============ API Key ============


class CreateApiKeyResponse(BaseModel):
    """创建 API Key 响应（含明文 secret，仅返回一次）"""

    id: int
    name: str
    key: str
    secret: str
    expires_at: datetime | None = None
    created_at: datetime


class ApiKeyResponse(BaseModel):
    """API Key 列表项"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key: str
    is_active: bool
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime
