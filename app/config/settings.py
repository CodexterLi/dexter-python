"""
配置管理模块

使用 Pydantic 的 Settings 类管理应用配置，提供类型检查和验证功能。
所有配置项从环境变量加载，支持 .env 文件。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    # ============ 环境配置 ============
    ENVIRONMENT: str = "development"  # production, development, test

    # ============ API配置 ============
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True

    # ============ 安全配置 ============
    SECRET_KEY: str = "your-super-secret-key-change-in-production"  # 用于加密敏感数据

    # ============ JWT配置 ============
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 访问令牌过期时间（分钟）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 刷新令牌过期时间（天）

    # ============ Cookie配置 ============
    COOKIE_SECURE: bool = False  # 开发环境设置为False，生产环境设置为True
    COOKIE_DOMAIN: str | None = None  # 域名，如果设置则Cookie只在该域名下有效

    # ============ TOTP配置 ============
    TOTP_ISSUER: str = "Drexor"  # TOTP发行者名称
    TOTP_ENCRYPTION_SALT: str = "totp_encryption_salt_v1"  # TOTP加密盐值

    # ============ Redis配置 ============
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_USERNAME: str | None = None
    REDIS_URL: str | None = None
    REDIS_USE_SSL: bool = False
    REDIS_TIMEOUT: int = 10
    REDIS_POOL_MIN_SIZE: int = 5  # 连接池最小连接数
    REDIS_POOL_MAX_SIZE: int = 20  # 连接池最大连接数

    # ============ 数据库配置 ============
    DATABASE_URL: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: int | None = None
    DB_NAME: str | None = None
    DB_SSL: bool = False
    DB_ECHO: bool = False  # 是否输出 SQL 日志

    # ============ 日志配置 ============
    LOG_LEVEL: str = "INFO"

    # ============ 跨域配置 ============
    CORS_ORIGINS: list[str] = ["*"]

    # ============ Worker配置 ============
    WORKER_INSTANCE_ID: str | None = None
    WORKER_SHUTDOWN_TIMEOUT_SECONDS: int = 30

    # ============ Scheduler配置 ============
    SCHEDULER_ENABLED: bool = False
    SCHEDULER_LOAD_ONLY_ENABLED_JOBS: bool = True

    # ============ Queue Worker配置 ============
    QUEUE_WORKER_ENABLED: bool = False
    QUEUE_WORKER_CONSUMERS: list[str] = []

    # Pydantic v2 中使用 model_config 替代 Config 类
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")


# 创建全局配置实例
settings = Settings()
