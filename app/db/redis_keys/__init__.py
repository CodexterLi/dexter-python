"""
Redis Key 统一管理包

所有 Redis key 的定义都在这个包中，确保:
- 统一前缀: dexter:
- 类型安全: 方法生成 key
- 按领域分文件: cache, agent, scheduler 等

Key 命名规范:
    {prefix}:{namespace}:{resource}:{identifier}

Example:
    dexter:cache:prompt:123
    dexter:user:sessions:0x123...
    dexter:ratelimit:192.168.1.1:1m

使用方式:

    from app.db.redis_keys import CacheKeys, TTL

    prompt_key = CacheKeys.prompt(123)
    await redis.setex(prompt_key, TTL.CACHE_LONG, data)

包结构:
    redis_keys/
    ├── __init__.py       # 导出所有 Key 类
    ├── base.py           # PREFIX, TTL, Namespace, 工具函数
    └── cache.py          # CacheKeys, UserKeys, RateLimitKeys, QueueKeys
"""

from app.db.redis_keys.base import PREFIX, TTL, Namespace, build_key, build_pattern
from app.db.redis_keys.cache import CacheKeys, QueueKeys, RateLimitKeys, UserKeys

__all__ = [
    "PREFIX",
    "TTL",
    "CacheKeys",
    "Namespace",
    "QueueKeys",
    "RateLimitKeys",
    "UserKeys",
    "build_key",
    "build_pattern",
]
