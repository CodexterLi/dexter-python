"""
数据仓库包

包含所有数据访问层的仓库类。
"""

from app.repositories.user_repository import UserRepository

__all__ = [
    "UserRepository",
]
