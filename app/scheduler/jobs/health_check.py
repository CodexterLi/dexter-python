"""
健康检查任务

定期检查系统各组件的健康状态。
"""

from app.core.logging import logger
from app.scheduler.base import BaseJob, JobConfig, TriggerType
from app.scheduler.registry import register_job


@register_job
class HealthCheckJob(BaseJob):
    """
    健康检查任务

    定期检查数据库、Redis 等组件的连接状态。
    """

    config = JobConfig(
        job_id="health_check",
        name="系统健康检查",
        trigger_type=TriggerType.INTERVAL,
        trigger_args={"minutes": 5},
        enabled=False,  # 默认禁用，需要时启用
    )

    async def execute(self) -> None:
        """执行健康检查"""
        logger.info("执行健康检查...")

        # 1. 检查数据库连接
        await self._check_database()

        # 2. 检查 Redis 连接
        await self._check_redis()

        logger.info("健康检查完成")

    async def _check_database(self) -> None:
        """检查数据库连接"""
        try:
            from app.db.postgres import check_db_health

            is_healthy = await check_db_health()
            if is_healthy:
                logger.debug("数据库连接正常")
            else:
                logger.warning("数据库连接异常")
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")

    async def _check_redis(self) -> None:
        """检查 Redis 连接"""
        try:
            from app.db.redis import get_redis

            redis = get_redis()
            await redis.ping()
            logger.debug("Redis 连接正常")
        except Exception as e:
            logger.error(f"Redis 健康检查失败: {e}")

    async def on_error(self, error: Exception) -> None:
        """健康检查失败时的处理"""
        logger.error(f"健康检查任务异常: {error}")
        # 可以在这里发送告警通知
