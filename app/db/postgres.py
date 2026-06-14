"""
PostgreSQL 数据库配置模块

提供 SQLAlchemy 异步会话和基础模型类,包含:
- 异步引擎配置
- 连接池管理
- 会话工厂
- 健康检查
"""

import urllib.parse
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config.settings import settings
from app.core.logging import logger

# ============ 全局变量 ============

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker | None = None

# 创建基类
Base = declarative_base()


# ============ 数据库 URL 构建 ============


def get_database_url() -> str:
    """
    构建数据库连接 URL

    Returns:
        str: PostgreSQL 连接 URL

    Raises:
        ValueError: 数据库配置不完整
    """
    if settings.DATABASE_URL:
        return _normalize_database_url(settings.DATABASE_URL)

    if not all(
        [
            settings.DB_USER,
            settings.DB_PASSWORD,
            settings.DB_HOST,
            settings.DB_PORT,
            settings.DB_NAME,
        ]
    ):
        raise ValueError("数据库配置不完整，请检查环境变量: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME")

    encoded_password = urllib.parse.quote_plus(settings.DB_PASSWORD, encoding="utf-8")

    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{encoded_password}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def _normalize_database_url(url: str) -> str:
    """Normalize external PostgreSQL URLs for SQLAlchemy asyncpg."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"postgresql", "postgres", "postgresql+asyncpg"}:
        return url

    normalized = parsed._replace(scheme="postgresql+asyncpg", query="")
    return urllib.parse.urlunparse(normalized)


def _requires_ssl() -> bool:
    if settings.DB_SSL:
        return True
    if settings.DATABASE_URL:
        parsed = urllib.parse.urlparse(settings.DATABASE_URL)
        query = urllib.parse.parse_qs(parsed.query)
        sslmode = query.get("sslmode", [""])[0]
        return sslmode in {"require", "verify-ca", "verify-full"}
    return bool(settings.DB_HOST and settings.DB_HOST.endswith(".neon.tech"))


# ============ 连接池配置 ============


def get_pool_config() -> dict:
    """根据环境获取连接池配置"""
    if settings.ENVIRONMENT == "production":
        return {
            "pool_size": 20,
            "max_overflow": 30,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "pool_pre_ping": True,
        }
    elif settings.ENVIRONMENT == "development":
        return {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,
        }
    else:  # test
        return {"poolclass": NullPool}


# ============ 引擎和会话工厂 ============


def get_engine() -> AsyncEngine:
    """获取数据库引擎（延迟初始化）"""
    global _engine
    if _engine is None:
        pool_config = get_pool_config()
        # 添加连接初始化回调，确保使用 UTF-8 编码
        connect_args = {
            "server_settings": {
                "client_encoding": "UTF8",
            }
        }
        if _requires_ssl():
            connect_args["ssl"] = True
        _engine = create_async_engine(
            get_database_url(),
            echo=settings.DB_ECHO,
            connect_args=connect_args,
            **pool_config,
        )
    return _engine


def get_session_factory() -> async_sessionmaker:
    """获取会话工厂（延迟初始化）"""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_factory


# 兼容旧代码的别名
@property
def engine() -> AsyncEngine:
    return get_engine()


@property
def async_session_factory() -> async_sessionmaker:
    return get_session_factory()


# ============ 数据库会话依赖 ============


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    提供数据库会话的依赖函数

    用于 FastAPI 的 Depends,确保会话在请求结束时正确关闭
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            await session.close()


# ============ 数据库初始化 ============


async def init_db(drop_all: bool = False) -> None:
    """
    初始化数据库,创建所有表

    Args:
        drop_all: 是否先删除所有表 (仅测试环境)
    """
    engine = get_engine()
    async with engine.begin() as conn:
        if drop_all:
            if settings.ENVIRONMENT == "production":
                raise RuntimeError("生产环境禁止删除数据库表!")
            logger.warning("删除所有数据库表...")
            await conn.run_sync(Base.metadata.drop_all)

        await conn.run_sync(Base.metadata.create_all)


# ============ 数据库关闭 ============


async def close_db() -> None:
    """关闭数据库连接"""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


# ============ 数据库健康检查 ============


async def check_db_health() -> bool:
    """检查数据库连接是否健康"""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("数据库健康检查通过")
        return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False


# ============ 导出 ============

__all__ = [
    "Base",
    "check_db_health",
    "close_db",
    "get_database_url",
    "get_db",
    "get_engine",
    "get_session_factory",
    "init_db",
]
