"""
定时任务调度模块

基于 APScheduler 实现的定时任务调度系统。

使用示例:
    # 1. 初始化调度器
    from app.scheduler import init_scheduler, load_jobs, start_scheduler

    init_scheduler()
    load_jobs()
    start_scheduler()

    # 2. 在 FastAPI lifespan 中使用
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_scheduler()
        load_jobs()
        start_scheduler()
        yield
        stop_scheduler()

创建新任务:
    from app.scheduler.base import BaseJob, JobConfig, TriggerType
    from app.scheduler.registry import register_job

    @register_job
    class MyJob(BaseJob):
        config = JobConfig(
            job_id="my_job",
            name="我的任务",
            trigger_type=TriggerType.INTERVAL,
            trigger_args={"minutes": 10},
            enabled=True,
        )

        async def execute(self) -> None:
            # 任务逻辑
            pass
"""

from app.scheduler.base import BaseJob, JobConfig, TriggerType
from app.scheduler.jobs import *  # noqa: F403
from app.scheduler.manager import (
    get_job_status,
    get_scheduler,
    init_scheduler,
    load_jobs,
    pause_job,
    remove_job,
    resume_job,
    start_scheduler,
    stop_scheduler,
)
from app.scheduler.registry import (
    get_all_jobs,
    get_enabled_jobs,
    get_job,
    register_job,
)

__all__ = [
    "BaseJob",
    "JobConfig",
    "TriggerType",
    "get_all_jobs",
    "get_enabled_jobs",
    "get_job",
    "get_job_status",
    "get_scheduler",
    "init_scheduler",
    "load_jobs",
    "pause_job",
    "register_job",
    "remove_job",
    "resume_job",
    "start_scheduler",
    "stop_scheduler",
]
