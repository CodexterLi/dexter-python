"""
API Key 模型

存储用户的 API Key 凭据，用于程序化访问 API。

表名: api_keys
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base
from app.models.base import utc_now


class ApiKey(Base):
    """
    API Key 表

    Attributes:
        id: 主键
        user_id: 所属用户
        name: 密钥名称
        key: API Key (明文，用于查找)
        secret_hash: API Secret 的 bcrypt 哈希
        is_active: 是否启用
        expires_at: 过期时间
        last_used_at: 最后使用时间
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="主键")
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="所属用户"
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="密钥名称")
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="API Key")
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="Secret 哈希")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="过期时间")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="最后使用时间")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, comment="更新时间"
    )

    __table_args__ = (
        Index("idx_api_keys_key", "key"),
        Index("idx_api_keys_user_id", "user_id"),
        {"comment": "API Key 表 - 用于程序化 API 访问"},
    )
