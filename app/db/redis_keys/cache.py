"""
Cache / User / RateLimit / Queue 相关 Redis Key

按命名空间管理各类 key 的生成。

Key 结构:
    dexter:cache:prompt:{prompt_id}        # Prompt 缓存 (Hash)
    dexter:cache:apikey:{key_hash}         # API Key 缓存 (String)
    dexter:user:sessions:{wallet}          # 用户会话列表 (Set)
    dexter:ratelimit:{identifier}:{window} # 限流计数器 (String)
    dexter:queue:stream:{name}             # 队列 Stream (Stream)
"""

from __future__ import annotations

from app.db.redis_keys.base import Namespace, build_key, build_pattern


class CacheKeys:
    """
    Cache 相关 Key 生成器

    Example:
        >>> from app.db.redis_keys import CacheKeys, TTL
        >>> prompt_key = CacheKeys.prompt(123)
        >>> await redis.setex(prompt_key, TTL.CACHE_LONG, data)
    """

    _NS = Namespace.CACHE.value

    # ==================== Prompt 缓存 ====================

    @classmethod
    def prompt(cls, prompt_id: int | str) -> str:
        """Prompt 缓存 (Hash)"""
        return build_key(cls._NS, "prompt", str(prompt_id))

    # ==================== API Key 缓存 ====================

    @classmethod
    def api_key(cls, key_hash: str) -> str:
        """API Key 缓存 (String, JSON 元数据)"""
        return build_key(cls._NS, "apikey", key_hash)

    # ==================== 通用缓存 ====================

    @classmethod
    def generic(cls, category: str, identifier: str) -> str:
        """
        通用缓存 key

        用于临时或不常用的缓存场景。

        Args:
            category: 缓存类别
            identifier: 唯一标识

        Returns:
            Redis key
        """
        return build_key(cls._NS, category, identifier)

    # ==================== Pattern 生成器 ====================

    @classmethod
    def pattern_prompts(cls) -> str:
        """匹配所有 Prompt 缓存"""
        return build_pattern(cls._NS, "prompt", "*")


class UserKeys:
    """
    User 相关 Key 生成器

    Example:
        >>> from app.db.redis_keys import UserKeys
        >>> sessions_key = UserKeys.sessions("0x123...")
    """

    _NS = Namespace.USER.value

    @classmethod
    def sessions(cls, wallet_address: str) -> str:
        """用户的所有会话列表 (Set)"""
        return build_key(cls._NS, "sessions", wallet_address)

    # ==================== Pattern 生成器 ====================

    @classmethod
    def pattern_sessions(cls) -> str:
        """匹配所有用户会话"""
        return build_pattern(cls._NS, "sessions", "*")


class RateLimitKeys:
    """
    Rate Limit 相关 Key 生成器

    Example:
        >>> from app.db.redis_keys import RateLimitKeys, TTL
        >>> limit_key = RateLimitKeys.counter("192.168.1.1", "1m")
    """

    _NS = Namespace.RATELIMIT.value

    @classmethod
    def counter(cls, identifier: str, window: str) -> str:
        """
        速率限制计数器 (String, INCR)

        Args:
            identifier: 用户标识 (IP/wallet/user_id)
            window: 时间窗口 (1m/1h/1d)

        Returns:
            Redis key
        """
        return build_key(cls._NS, identifier, window)

    # ==================== Pattern 生成器 ====================

    @classmethod
    def pattern_by_identifier(cls, identifier: str) -> str:
        """匹配指定标识的所有限流 key"""
        return build_pattern(cls._NS, identifier, "*")


class QueueKeys:
    """
    Queue (Redis Streams) 相关 Key 生成器

    用于内部 Redis Streams 消费者框架。

    Example:
        >>> from app.db.redis_keys import QueueKeys
        >>> stream_key = QueueKeys.stream("example")
    """

    _NS = Namespace.QUEUE.value

    @classmethod
    def stream(cls, stream_name: str) -> str:
        """队列 Stream key (Stream)"""
        return build_key(cls._NS, "stream", stream_name)

    @classmethod
    def consumer_group(cls, stream_name: str) -> str:
        """消费者组名称"""
        return f"{stream_name}-consumer-group"

    @classmethod
    def dlq(cls, stream_name: str) -> str:
        """死信队列 key (Stream)"""
        return build_key(cls._NS, "dlq", stream_name)

    @classmethod
    def consumer_name(cls, stream_name: str, instance_id: str) -> str:
        """消费者实例名称"""
        return f"{stream_name}-consumer-{instance_id}"
