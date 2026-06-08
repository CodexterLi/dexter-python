"""
API Key 服务

负责 API Key 的创建、验证和管理。
使用 SHA-256 哈希存储，Redis 缓存加速查找。
"""

import hashlib
import json
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, UnauthorizedException
from app.core.logging import logger
from app.db.redis import get_redis
from app.db.redis_keys.base import TTL
from app.db.redis_keys.cache import CacheKeys
from app.models.api_key import ApiKey
from app.repositories.api_key_repository import ApiKeyRepository
from packages.common.snowflake import generate_id

# API Key 前缀
KEY_PREFIX = "dxt_"


def _hash_key(raw_key: str) -> str:
    """SHA-256 哈希 API Key"""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _generate_raw_key() -> str:
    """生成原始 API Key: dxt_ + 32 字节 base62"""
    return KEY_PREFIX + secrets.token_urlsafe(32)


class ApiKeyService:
    """API Key 服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ApiKeyRepository(db)

    async def create_key(self, user_id: int, label: str, permissions: list[str] | None = None) -> tuple[str, ApiKey]:
        """
        创建 API Key

        Returns:
            (明文 key, ApiKey 对象) — 明文 key 仅此一次返回
        """
        raw_key = _generate_raw_key()
        key_hash = _hash_key(raw_key)

        api_key = ApiKey(
            id=generate_id(),
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=raw_key[:12],
            label=label,
            permissions=permissions or [],
        )

        api_key = await self.repo.create(api_key)
        logger.info(f"API Key 已创建: user={user_id}, prefix={api_key.key_prefix}")
        return raw_key, api_key

    async def authenticate(self, raw_key: str) -> tuple[int, ApiKey]:
        """
        验证 API Key

        Returns:
            (user_id, ApiKey 对象)

        Raises:
            UnauthorizedException: Key 无效或已停用
        """
        key_hash = _hash_key(raw_key)

        # 1. 尝试 Redis 缓存
        cached = await self._get_cached(key_hash)
        if cached:
            return cached["user_id"], cached["api_key_obj"]

        # 2. 查数据库
        api_key = await self.repo.get_by_hash(key_hash)
        if not api_key:
            raise UnauthorizedException("无效的 API Key")

        # 3. 更新最后使用时间
        await self.repo.update_last_used(api_key.id)

        # 4. 写入 Redis 缓存
        await self._set_cached(key_hash, api_key)

        return api_key.user_id, api_key

    async def list_keys(self, user_id: int) -> list[ApiKey]:
        """列出用户所有 API Key"""
        return await self.repo.get_by_user(user_id)

    async def revoke_key(self, key_id: int, user_id: int) -> None:
        """撤销 API Key"""
        success = await self.repo.deactivate(key_id, user_id)
        if not success:
            raise NotFoundException("API Key 不存在")
        logger.info(f"API Key 已撤销: id={key_id}, user={user_id}")

    async def _get_cached(self, key_hash: str) -> dict | None:
        """从 Redis 缓存获取 API Key 信息"""
        try:
            redis = get_redis()
            cache_key = CacheKeys.api_key(key_hash)
            data = await redis.get(cache_key)
            if not data:
                return None

            info = json.loads(data)
            # 缓存只存元数据，需要从 DB 获取完整对象进行权限检查
            api_key = await self.repo.get_by_hash(key_hash)
            if not api_key:
                await redis.delete(cache_key)
                return None

            return {"user_id": info["user_id"], "api_key_obj": api_key}
        except Exception:
            return None

    async def _set_cached(self, key_hash: str, api_key: ApiKey) -> None:
        """写入 Redis 缓存"""
        try:
            redis = get_redis()
            cache_key = CacheKeys.api_key(key_hash)
            data = json.dumps({"user_id": api_key.user_id, "key_id": api_key.id})
            await redis.setex(cache_key, TTL.CACHE_SHORT, data)
        except Exception:
            pass  # 缓存写入失败不影响主流程
