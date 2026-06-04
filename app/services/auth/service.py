"""
认证服务层

处理用户认证相关的业务逻辑：密码登录、钱包登录、API Key 管理
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.core.logging import logger
from app.core.security import (
    build_sign_message,
    create_access_token,
    create_refresh_token,
    generate_api_key,
    generate_api_secret,
    generate_nonce,
    generate_totp_secret,
    get_totp_uri,
    hash_secret,
    verify_password,
    verify_secret,
    verify_totp,
    verify_wallet_signature,
)
from app.models.api_key import ApiKey
from app.models.user import User
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate


class AuthService:
    """认证服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
        self.api_key_repository = ApiKeyRepository(db)

    # ============ 密码登录 ============

    async def register_user(self, user_data: UserCreate) -> User:
        """注册新用户"""
        return await self.user_repository.create_user(user_data)

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """验证用户凭据"""
        user = await self.user_repository.get_by_username(username)
        if not user or not user.hashed_password:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def login(self, username: str, password: str, totp_code: str | None = None) -> tuple[User, dict]:
        """用户登录"""
        user = await self.authenticate_user(username, password)
        if not user:
            raise ValueError("用户名或密码错误")

        if not user.is_active:
            raise ValueError("用户未激活")

        if user.totp_enabled:
            if not totp_code:
                raise ValueError("需要TOTP验证码")
            if not verify_totp(user.totp_secret, totp_code):
                raise ValueError("无效的TOTP验证码")

        logger.info(f"用户 {user.username} 登录成功")
        tokens = self._create_tokens(user.username)
        await self.user_repository.update_last_login(user.id)
        return user, tokens

    # ============ 钱包登录 ============

    async def get_wallet_nonce(self, wallet_address: str) -> tuple[str, str]:
        """
        获取钱包签名随机数

        Returns:
            (nonce, message): nonce 和待签名消息
        """
        nonce = generate_nonce()
        message = build_sign_message(nonce)
        # TODO: 存储到 Redis 进行验证，5 分钟过期
        return nonce, message

    async def wallet_login(self, wallet_address: str, signature: str, message: str) -> tuple[User, dict]:
        """
        钱包登录（签名验证 + 自动注册）

        Returns:
            (user, tokens)
        """
        # 1. 验证签名
        if not verify_wallet_signature(wallet_address, message, signature):
            raise ValueError("签名验证失败")

        addr = wallet_address.lower()

        # 2. 查找或创建用户
        user = await self.user_repository.get_by_wallet_address(addr)
        if not user:
            user = await self.user_repository.create_wallet_user(addr)

        if not user.is_active:
            raise ValueError("用户未激活")

        # 3. 生成令牌
        logger.info(f"钱包用户 {addr} 登录成功")
        tokens = self._create_tokens(user.username)
        await self.user_repository.update_last_login(user.id)
        return user, tokens

    # ============ API Key 管理 ============

    async def create_api_key(self, user_id: int, name: str, expires_in: int | None = None) -> tuple[ApiKey, str]:
        """
        创建 API Key

        Returns:
            (api_key, plain_secret): 明文 secret 仅返回一次
        """
        key = generate_api_key()
        secret = generate_api_secret()
        secret_hashed = hash_secret(secret)

        now = datetime.now(UTC).replace(tzinfo=None)

        ak = ApiKey(
            user_id=user_id,
            name=name,
            key=key,
            secret_hash=secret_hashed,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        if expires_in:
            ak.expires_at = now + timedelta(seconds=expires_in)

        ak = await self.api_key_repository.create(ak)
        return ak, secret

    async def authenticate_api_key(self, key: str, secret: str) -> User:
        """
        通过 API Key + Secret 认证，返回对应用户

        Raises:
            ValueError: 认证失败
        """
        ak = await self.api_key_repository.get_by_key(key)
        if not ak:
            raise ValueError("无效的 API Key")

        # 检查过期
        if ak.expires_at:
            now = datetime.now(UTC).replace(tzinfo=None)
            if ak.expires_at.replace(tzinfo=None) < now:
                raise ValueError("API Key 已过期")

        # 验证 secret
        if not verify_secret(secret, ak.secret_hash):
            raise ValueError("无效的 API Secret")

        # 更新最后使用时间
        await self.api_key_repository.update_last_used(ak.id)

        # 加载用户
        user = await self.user_repository.get_by_id(ak.user_id)
        if not user or not user.is_active:
            raise ValueError("用户不存在或未激活")

        return user

    async def list_api_keys(self, user_id: int) -> list[ApiKey]:
        """列出用户的所有 API Key"""
        return await self.api_key_repository.list_by_user_id(user_id)

    async def revoke_api_key(self, api_key_id: int, user_id: int) -> bool:
        """吊销 API Key"""
        return await self.api_key_repository.revoke(api_key_id, user_id)

    async def delete_api_key(self, api_key_id: int, user_id: int) -> bool:
        """删除 API Key"""
        return await self.api_key_repository.delete_key(api_key_id, user_id)

    # ============ Token 管理 ============

    def _create_tokens(self, username: str) -> dict:
        """创建访问令牌和刷新令牌"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": username}, expires_delta=refresh_token_expires)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh_tokens(self, username: str) -> tuple[User, dict]:
        """刷新用户令牌"""
        user = await self.user_repository.get_by_username(username)
        if not user or not user.is_active:
            raise ValueError("用户不存在或未激活")
        tokens = self._create_tokens(user.username)
        return user, tokens

    # ============ TOTP ============

    async def setup_totp(self, user_id: int, username: str) -> dict:
        """设置 TOTP 两步验证"""
        secret = generate_totp_secret()
        uri = get_totp_uri(secret, username)
        await self.user_repository.setup_totp(user_id, secret)
        return {"secret": secret, "uri": uri}

    async def verify_and_enable_totp(self, user_id: int, totp_secret: str, totp_code: str) -> User:
        """验证并启用 TOTP"""
        if not totp_secret:
            raise ValueError("未设置TOTP密钥")
        if not verify_totp(totp_secret, totp_code):
            raise ValueError("验证码无效或已过期")
        return await self.user_repository.enable_totp(user_id)

    async def disable_totp(self, user_id: int, totp_enabled: bool) -> User:
        """禁用 TOTP"""
        if not totp_enabled:
            raise ValueError("未启用两步验证")
        return await self.user_repository.disable_totp(user_id)
