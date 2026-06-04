"""
用户模型

用户核心表，存储用户基本信息和认证信息。

表名: users
字段数: 11
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base
from app.models.base import utc_now


class User(Base):
    """
    用户核心表

    存储用户基本信息和认证信息，包括:
    - 基本信息: 用户名、邮箱
    - 认证信息: 密码哈希、TOTP 配置
    - 状态标记: 是否激活、是否超级管理员
    - 时间戳: 创建时间、更新时间、最后登录时间

    Attributes:
        id: 主键 ID
        username: 用户名 (唯一)
        email: 邮箱 (唯一)
        hashed_password: 密码哈希
        is_active: 是否激活
        is_superuser: 是否超级管理员
        totp_secret: TOTP 密钥 (加密存储)
        totp_enabled: 是否启用两步验证
        created_at: 创建时间
        updated_at: 更新时间
        last_login_at: 最后登录时间
    """

    __tablename__ = "users"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="主键 ID",
    )

    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="用户名",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="邮箱",
    )
    wallet_address: Mapped[str | None] = mapped_column(
        String(42),
        unique=True,
        comment="钱包地址 (EVM, 小写)",
    )

    # 认证信息
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        comment="密码哈希 (钱包登录用户可为空)",
    )

    # 状态标记
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否超级管理员",
    )

    # TOTP 两步验证
    totp_secret: Mapped[str | None] = mapped_column(
        String(255),
        comment="TOTP 密钥 (加密存储)",
    )
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否启用两步验证",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        comment="创建时间 (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        comment="更新时间 (UTC)",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        comment="最后登录时间",
    )

    __table_args__ = (
        # 索引
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_wallet_address", "wallet_address", unique=True),
        # 表注释
        {"comment": "用户核心表 - 存储用户基本信息和认证信息"},
    )
