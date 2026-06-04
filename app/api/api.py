"""
API 路由配置

统一管理所有路由，各业务模块只负责定义路由函数。
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.common.routes import router as common_router
from app.api.websocket.routes import router as ws_router

# 创建主路由器
api_router = APIRouter()

# 认证 & 通用
api_router.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
api_router.include_router(common_router, prefix="/api/docs", tags=["Common"])
api_router.include_router(ws_router, tags=["WebSocket"])
