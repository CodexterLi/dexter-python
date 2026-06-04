"""
服务层模块包

按业务模块组织:
- auth/: 认证服务
"""

from app.services.auth import AuthService

__all__ = [
    "AuthService",
]
