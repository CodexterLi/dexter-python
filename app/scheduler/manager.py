"""
调度器管理器

提供调度器的统一管理，包括启动、停止和任务管理。
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logging import logger
from app.scheduler.base import BaseJob, TriggerType
from app.scheduler.registry import get_all_jobs, get_enabled_jobs

# 全局调度器实例
_scheduler: AsyncIOScheduler | None = None


def _get_trigger(job: BaseJob) -> CronTrigger | IntervalTrigger | DateTrigger:
    """
    根据任务配置获取触发器

    Args:
        job: 任务实例

    Returns:
        APScheduler 触发器
    """
    config = job.config
    trigger_args = config.trigger_args

    match config.trigger_type:
        case TriggerType.CRON:
            return CronTrigger(**trigger_args)
        case TriggerType.INTERVAL:
            return IntervalTrigger(**trigger_args)
        case TriggerType.DATE:
            return DateTrigger(**trigger_args)
        case _:
            raise ValueError(f"未知的触发器类型: {config.trigger_type}")


async def _execute_job(job: BaseJob) -> None:
    """
    执行任务的包装函数

    Args:
        job: 任务实例
    """
    job_id = job.config.job_id
    logger.info(f"开始执行任务: {job_id}")

    try:
        await job.execute()
        await job.on_success()
        logger.info(f"任务执行成功: {job_id}")
    except Exception as e:
        logger.error(f"任务执行失败: {job_id}, 错误: {e}")
        await job.on_error(e)


def get_scheduler() -> AsyncIOScheduler:
    """
    获取调度器实例

    Returns:
        AsyncIOScheduler 实例

    Raises:
        RuntimeError: 如果调度器未初始化
    """
    if _scheduler is None:
        raise RuntimeError("调度器未初始化，请先调用 init_scheduler()")
    return _scheduler


def init_scheduler() -> AsyncIOScheduler:
    """
    初始化调度器

    Returns:
        AsyncIOScheduler 实例
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("调度器已初始化")
        return _scheduler

    _scheduler = AsyncIOScheduler(
        timezone="UTC",
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        },
    )

    logger.info("调度器初始化完成")
    return _scheduler


def load_jobs(only_enabled: bool = True) -> int:
    """
    加载任务到调度器

    Args:
        only_enabled: 是否只加载已启用的任务

    Returns:
        加载的任务数量
    """
    scheduler = get_scheduler()
    jobs = get_enabled_jobs() if only_enabled else get_all_jobs()
    loaded_count = 0

    for job_id, job_class in jobs.items():
        try:
            job_instance = job_class()
            config = job_instance.config

            scheduler.add_job(
                _execute_job,
                trigger=_get_trigger(job_instance),
                args=[job_instance],
                id=config.job_id,
                name=config.name,
                max_instances=config.max_instances,
                coalesce=config.coalesce,
                misfire_grace_time=config.misfire_grace_time,
                replace_existing=True,
            )
            loaded_count += 1
            logger.info(f"加载任务: {job_id} ({config.name})")

        except Exception as e:
            logger.error(f"加载任务失败: {job_id}, 错误: {e}")

    logger.info(f"共加载 {loaded_count} 个任务")
    return loaded_count


def start_scheduler() -> None:
    """启动调度器"""
    scheduler = get_scheduler()
    if scheduler.running:
        logger.warning("调度器已在运行")
        return

    scheduler.start()
    logger.info("调度器已启动")


def stop_scheduler(wait: bool = True) -> None:
    """
    停止调度器

    Args:
        wait: 是否等待当前任务完成
    """
    global _scheduler

    if _scheduler is None:
        return

    if _scheduler.running:
        _scheduler.shutdown(wait=wait)
        logger.info("调度器已停止")

    _scheduler = None


def pause_job(job_id: str) -> bool:
    """
    暂停任务

    Args:
        job_id: 任务 ID

    Returns:
        是否成功
    """
    try:
        scheduler = get_scheduler()
        scheduler.pause_job(job_id)
        logger.info(f"任务已暂停: {job_id}")
        return True
    except Exception as e:
        logger.error(f"暂停任务失败: {job_id}, 错误: {e}")
        return False


def resume_job(job_id: str) -> bool:
    """
    恢复任务

    Args:
        job_id: 任务 ID

    Returns:
        是否成功
    """
    try:
        scheduler = get_scheduler()
        scheduler.resume_job(job_id)
        logger.info(f"任务已恢复: {job_id}")
        return True
    except Exception as e:
        logger.error(f"恢复任务失败: {job_id}, 错误: {e}")
        return False


def remove_job(job_id: str) -> bool:
    """
    移除任务

    Args:
        job_id: 任务 ID

    Returns:
        是否成功
    """
    try:
        scheduler = get_scheduler()
        scheduler.remove_job(job_id)
        logger.info(f"任务已移除: {job_id}")
        return True
    except Exception as e:
        logger.error(f"移除任务失败: {job_id}, 错误: {e}")
        return False


def get_job_status() -> list[dict]:
    """
    获取所有任务状态

    Returns:
        任务状态列表
    """
    scheduler = get_scheduler()
    jobs = scheduler.get_jobs()

    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "pending": job.pending,
        }
        for job in jobs
    ]
