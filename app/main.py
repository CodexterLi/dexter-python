"""
Drexor 应用入口

提供用户认证、数据库连接、Redis缓存、WebSocket 和 AI Agent Gateway。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import ValidationError

from app.api.router import api_router
from app.config.settings import settings
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    internal_exception_handler,
    pydantic_validation_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.db.postgres import close_db, init_db
from app.db.redis import close_redis, init_redis

# 初始化日志系统
setup_logging()

# 获取配置
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
API_DEBUG = settings.API_DEBUG


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    await init_redis()
    logger.info("应用启动完成")

    yield

    await close_redis()
    await close_db()
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Drexor",
    description="Drexor - AI Agent Platform with Web3 Authentication",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册异常处理器
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(Exception, internal_exception_handler)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"启动服务器: {API_HOST}:{API_PORT}, 调试模式: {API_DEBUG}")
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=API_DEBUG)
