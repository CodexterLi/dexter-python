"""
API Key 仓库

负责 API Key 相关的数据库操作
"""

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.api_key import ApiKey


class ApiKeyRepository:
    """API Key 仓库"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, api_key: ApiKey) -> ApiKey:
        """创建 API Key"""
        try:
            self.db.add(api_key)
            await self.db.commit()
            await self.db.refresh(api_key)
            return api_key
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建 API Key 出错: {e!s}")
            raise

    async def get_by_key(self, key: str) -> ApiKey | None:
        """根据 API Key 查找（仅活跃的）"""
        query = select(ApiKey).where(ApiKey.key == key, ApiKey.is_active.is_(True))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user_id(self, user_id: int) -> list[ApiKey]:
        """列出用户的所有 API Key"""
        query = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_last_used(self, api_key_id: int) -> None:
        """更新最后使用时间"""
        try:
            now = datetime.now(UTC).replace(tzinfo=None)
            query = update(ApiKey).where(ApiKey.id == api_key_id).values(last_used_at=now)
            await self.db.execute(query)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新 API Key 最后使用时间出错: {e!s}")

    async def revoke(self, api_key_id: int, user_id: int) -> bool:
        """吊销 API Key"""
        try:
            now = datetime.now(UTC).replace(tzinfo=None)
            query = (
                update(ApiKey)
                .where(ApiKey.id == api_key_id, ApiKey.user_id == user_id)
                .values(is_active=False, updated_at=now)
            )
            result = await self.db.execute(query)
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"吊销 API Key 出错: {e!s}")
            raise

    async def delete_key(self, api_key_id: int, user_id: int) -> bool:
        """删除 API Key"""
        try:
            query = delete(ApiKey).where(ApiKey.id == api_key_id, ApiKey.user_id == user_id)
            result = await self.db.execute(query)
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除 API Key 出错: {e!s}")
            raise
