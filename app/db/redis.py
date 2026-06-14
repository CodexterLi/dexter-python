"""
Redis 数据库连接管理

提供异步 Redis 客户端，使用连接池管理连接。
"""

from redis import asyncio as aioredis
from redis.asyncio.connection import ConnectionPool, SSLConnection

from app.config.settings import settings
from app.core.logging import logger

# 全局 Redis 客户端实例
_redis_client: aioredis.Redis | None = None
_connection_pool: ConnectionPool | None = None


def _normalize_redis_url(url: str) -> str:
    """Use rediss:// when SSL is enabled for URL-based Redis connections."""
    if settings.REDIS_USE_SSL and url.startswith("redis://"):
        return "rediss://" + url.removeprefix("redis://")
    return url


async def init_redis() -> aioredis.Redis:
    """
    初始化 Redis 连接

    使用连接池管理连接，支持 ACL 认证和 SSL。

    Returns:
        Redis 客户端实例
    """
    global _redis_client, _connection_pool

    if _redis_client is not None:
        return _redis_client

    try:
        if settings.REDIS_URL:
            _redis_client = aioredis.from_url(
                _normalize_redis_url(settings.REDIS_URL),
                db=settings.REDIS_DB,
                encoding="utf-8",
                decode_responses=False,
                socket_timeout=settings.REDIS_TIMEOUT,
                socket_connect_timeout=settings.REDIS_TIMEOUT,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=settings.REDIS_POOL_MAX_SIZE,
            )
            _connection_pool = _redis_client.connection_pool
            await _redis_client.ping()
            logger.info(f"✅ Redis 连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
            return _redis_client

        # 1. 构建连接池配置
        pool_config: dict = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB,
            "encoding": "utf-8",
            "decode_responses": False,  # 保持 bytes 格式，在使用时手动解码
            "socket_timeout": settings.REDIS_TIMEOUT,
            "socket_connect_timeout": settings.REDIS_TIMEOUT,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "max_connections": settings.REDIS_POOL_MAX_SIZE,
        }

        # 2. 认证配置
        if settings.REDIS_USERNAME and settings.REDIS_PASSWORD:
            # ACL 认证 (Redis 6.0+)
            pool_config["username"] = settings.REDIS_USERNAME
            pool_config["password"] = settings.REDIS_PASSWORD
        elif settings.REDIS_PASSWORD:
            # 传统密码认证
            pool_config["password"] = settings.REDIS_PASSWORD

        # 3. SSL 配置
        if settings.REDIS_USE_SSL:
            pool_config["connection_class"] = SSLConnection

        # 4. 创建连接池
        _connection_pool = ConnectionPool(**pool_config)

        # 5. 创建 Redis 客户端
        _redis_client = aioredis.Redis(connection_pool=_connection_pool)

        # 6. 测试连接
        await _redis_client.ping()

        logger.info(
            f"✅ Redis 连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB} "
            f"(pool: {settings.REDIS_POOL_MAX_SIZE})"
        )

        return _redis_client

    except Exception as e:
        logger.error(f"❌ Redis 连接失败: {e}")
        logger.error(f"   配置: host={settings.REDIS_HOST}, port={settings.REDIS_PORT}, db={settings.REDIS_DB}")
        raise


async def close_redis() -> None:
    """关闭 Redis 连接和连接池"""
    global _redis_client, _connection_pool

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None

    if _connection_pool is not None:
        await _connection_pool.disconnect()
        _connection_pool = None

    logger.info("Redis 连接已关闭")


def get_redis() -> aioredis.Redis:
    """
    获取 Redis 客户端实例

    Returns:
        Redis 客户端实例

    Raises:
        RuntimeError: 如果 Redis 未初始化
    """
    if _redis_client is None:
        raise RuntimeError("Redis 未初始化，请先调用 init_redis()")
    return _redis_client


async def get_pool_info() -> dict:
    """
    获取连接池状态信息

    Returns:
        连接池状态字典
    """
    if _connection_pool is None:
        return {"status": "not_initialized"}

    return {
        "status": "active",
        "max_connections": _connection_pool.max_connections,
        "current_connections": len(_connection_pool._available_connections),
        "in_use_connections": len(_connection_pool._in_use_connections),
    }
