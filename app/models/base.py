"""
模型基础模块

提供所有模型共用的:
- 时区感知的 UTC 时间函数
- 常用类型导入
"""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """
    获取当前 UTC 时间 (时区感知)

    替代已弃用的 datetime.utcnow()

    Returns:
        datetime: 当前 UTC 时间，带时区信息
    """
    return datetime.now(UTC)
