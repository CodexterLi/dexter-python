"""
数据清理任务

定期清理过期数据、临时文件等。
"""

from app.core.logging import logger
from app.scheduler.base import BaseJob, JobConfig, TriggerType
from app.scheduler.registry import register_job


@register_job
class DataCleanupJob(BaseJob):
    """
    数据清理任务

    定期清理:
    - 过期的会话数据
    - 临时文件
    - 过期的日志记录
    """

    config = JobConfig(
        job_id="data_cleanup",
        name="数据清理",
        trigger_type=TriggerType.CRON,
        trigger_args={
            "hour": 3,  # 凌晨 3 点执行
            "minute": 0,
        },
        enabled=False,  # 默认禁用
    )

    async def execute(self) -> None:
        """执行数据清理"""
        logger.info("开始数据清理...")

        # 1. 清理过期会话
        await self._cleanup_expired_sessions()

        # 2. 清理临时数据
        await self._cleanup_temp_data()

        logger.info("数据清理完成")

    async def _cleanup_expired_sessions(self) -> None:
        """清理过期会话"""
        try:
            # TODO: 实现过期会话清理逻辑
            # 例如: 清理 Redis 中过期的 session 数据
            logger.debug("清理过期会话...")
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")

    async def _cleanup_temp_data(self) -> None:
        """清理临时数据"""
        try:
            # TODO: 实现临时数据清理逻辑
            logger.debug("清理临时数据...")
        except Exception as e:
            logger.error(f"清理临时数据失败: {e}")

    async def on_success(self) -> None:
        """清理成功回调"""
        logger.info("数据清理任务执行成功")
