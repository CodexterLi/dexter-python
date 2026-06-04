"""
Redis Key 基础模块

定义全局前缀、TTL 常量和基础工具函数。

Key 命名规范:
    {prefix}:{namespace}:{resource}:{identifier}

Example:
    dexter:user:sessions:0x123...
    dexter:queue:stream:example
    dexter:ratelimit:192.168.1.1:1m
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

# ============================================================================
# 全局前缀
# ============================================================================
PREFIX: Final[str] = "dexter"


# ============================================================================
# TTL 常量 (秒)
# ============================================================================
class TTL:
    """
    Redis Key 过期时间常量

    按功能分组，便于查找和维护。

    Example:
        >>> await redis.setex(key, TTL.CACHE_SHORT, data)
    """

    # ==================== 通用 ====================
    SESSION: Final[int] = 3600  # 会话: 1 小时
    LOCK: Final[int] = 30  # 锁: 30 秒

    # ==================== Cache 相关 ====================
    CACHE_REALTIME: Final[int] = 10  # 实时数据缓存: 10 秒
    CACHE_SHORT: Final[int] = 300  # 短期缓存: 5 分钟
    CACHE_MEDIUM: Final[int] = 1800  # 中期缓存: 30 分钟
    CACHE_LONG: Final[int] = 3600  # 长期缓存: 1 小时
    CACHE_DAY: Final[int] = 86400  # 日缓存: 24 小时


# ============================================================================
# 命名空间枚举
# ============================================================================
class Namespace(StrEnum):
    """
    Redis 命名空间

    用于 key 的第二级分类，确保不同功能的 key 隔离。
    """

    USER = "user"
    CACHE = "cache"
    RATELIMIT = "ratelimit"
    QUEUE = "queue"


# ============================================================================
# 工具函数
# ============================================================================
def build_key(*parts: str) -> str:
    """
    构建 Redis key

    自动添加全局前缀并用冒号连接。

    Args:
        *parts: key 的各个部分

    Returns:
        完整的 Redis key

    Example:
        >>> build_key("user", "sessions", "0x123")
        "dexter:user:sessions:0x123"
    """
    return ":".join([PREFIX, *parts])


def build_pattern(*parts: str) -> str:
    """
    构建 Redis key 匹配模式

    用于 SCAN/KEYS 命令。

    Args:
        *parts: 模式的各个部分

    Returns:
        匹配模式字符串

    Example:
        >>> build_pattern("user", "sessions", "*")
        "dexter:user:sessions:*"
    """
    return ":".join([PREFIX, *parts])
