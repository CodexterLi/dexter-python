"""
任务注册表

提供任务的自动发现和注册机制。
"""

from app.core.logging import logger
from app.scheduler.base import BaseJob

# 全局任务注册表
_job_registry: dict[str, type[BaseJob]] = {}


def register_job(job_class: type[BaseJob]) -> type[BaseJob]:
    """
    注册任务装饰器

    Args:
        job_class: 任务类

    Returns:
        原任务类

    Example:
        @register_job
        class MyJob(BaseJob):
            ...
    """
    job_id = job_class.config.job_id
    if job_id in _job_registry:
        logger.warning(f"任务 {job_id} 已存在，将被覆盖")
    _job_registry[job_id] = job_class
    logger.debug(f"注册任务: {job_id} -> {job_class.__name__}")
    return job_class


def get_all_jobs() -> dict[str, type[BaseJob]]:
    """获取所有已注册的任务"""
    return _job_registry.copy()


def get_job(job_id: str) -> type[BaseJob] | None:
    """
    获取指定任务

    Args:
        job_id: 任务 ID

    Returns:
        任务类或 None
    """
    return _job_registry.get(job_id)


def get_enabled_jobs() -> dict[str, type[BaseJob]]:
    """获取所有已启用的任务"""
    return {job_id: job_class for job_id, job_class in _job_registry.items() if job_class.config.enabled}


def clear_registry() -> None:
    """清空注册表 (用于测试)"""
    _job_registry.clear()
