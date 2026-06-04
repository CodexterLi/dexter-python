"""
定时任务基类

提供所有定时任务的抽象基类，定义任务的基本结构和配置。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TriggerType(StrEnum):
    """触发器类型"""

    CRON = "cron"  # Cron 表达式触发
    INTERVAL = "interval"  # 固定间隔触发
    DATE = "date"  # 一次性触发


@dataclass
class JobConfig:
    """
    任务配置

    Attributes:
        job_id: 任务唯一标识
        name: 任务名称
        trigger_type: 触发器类型
        trigger_args: 触发器参数
        enabled: 是否启用
        max_instances: 最大并发实例数
        coalesce: 是否合并错过的执行
        misfire_grace_time: 错过执行的容忍时间 (秒)
    """

    job_id: str
    name: str
    trigger_type: TriggerType
    trigger_args: dict[str, Any] = field(default_factory=dict)
    enabled: bool = False
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int = 60


class BaseJob(ABC):
    """
    定时任务抽象基类

    所有定时任务需要继承此类并实现 execute 方法。

    Example:
        class MyJob(BaseJob):
            config = JobConfig(
                job_id="my_job",
                name="示例任务",
                trigger_type=TriggerType.INTERVAL,
                trigger_args={"minutes": 5},
                enabled=True,
            )

            async def execute(self) -> None:
                # 执行任务逻辑
                pass
    """

    config: JobConfig

    @abstractmethod
    async def execute(self) -> None:
        """
        执行任务

        子类必须实现此方法。
        """
        raise NotImplementedError

    async def on_success(self) -> None:
        """任务成功回调 (可选重写)"""
        return None

    async def on_error(self, error: Exception) -> None:
        """
        任务失败回调 (可选重写)

        Args:
            error: 异常实例
        """
        _ = error

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.config.job_id} enabled={self.config.enabled}>"
