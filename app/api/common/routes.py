"""
通用路由
"""

from fastapi import APIRouter

from app.core.responses import ok

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    return ok(data={"status": "healthy"})


@router.get("/info")
async def api_info():
    """获取 API 信息"""
    return ok(
        data={
            "name": "Drexor",
            "version": "0.1.0",
            "description": "Drexor backend with authentication, database, Redis and WebSocket",
        }
    )
