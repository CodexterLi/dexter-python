"""
定时任务实现

导入所有任务以触发自动注册。
"""

# 导入所有任务模块以触发 @register_job 装饰器
from app.scheduler.jobs.cleanup import DataCleanupJob
from app.scheduler.jobs.health_check import HealthCheckJob
from app.scheduler.jobs.report import DailyReportJob

__all__ = [
    "DailyReportJob",
    "DataCleanupJob",
    "HealthCheckJob",
]
