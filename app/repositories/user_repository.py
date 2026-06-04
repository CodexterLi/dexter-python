"""
用户仓库 负责用户相关的数据库操作

"""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import encrypt_totp_secret, get_password_hash
from app.models.user import User
from app.schemas.auth import UserCreate


class UserRepository:
    """
    用户仓库

    负责用户相关的数据库操作
    """

    def __init__(self, db: AsyncSession):
        """
        初始化用户仓库

        Args:
            db: 数据库会话
        """
        self.db = db

    async def get_by_username(self, username: str) -> User | None:
        """
        通过用户名获取用户

        Args:
            username: 用户名

        Returns:
            Optional[User]: 用户对象，如果不存在则返回None
        """
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """
        通过邮箱获取用户

        Args:
            email: 邮箱

        Returns:
            Optional[User]: 用户对象，如果不存在则返回None
        """
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """通过ID获取用户"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_wallet_address(self, wallet_address: str) -> User | None:
        """通过钱包地址获取用户"""
        query = select(User).where(User.wallet_address == wallet_address.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_wallet_user(self, wallet_address: str) -> User:
        """
        通过钱包地址创建用户（自动注册）

        钱包用户的 username 为钱包地址缩写，email 为占位符，无密码。
        """
        try:
            addr = wallet_address.lower()
            now = datetime.now(UTC).replace(tzinfo=None)

            user = User(
                username=f"{addr[:6]}...{addr[-4:]}",
                email=f"{addr}@wallet.local",
                wallet_address=addr,
                hashed_password=None,
                is_active=True,
                is_superuser=False,
                totp_enabled=False,
                created_at=now,
                updated_at=now,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建钱包用户出错: {e!s}")
            raise

    async def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户

        Args:
            user_data: 用户数据

        Returns:
            User: 创建的用户
        """
        try:
            # 检查用户名是否已存在
            existing_user = await self.get_by_username(user_data.username)
            if existing_user:
                raise ValueError("用户名已存在")

            # 检查邮箱是否已存在
            existing_email = await self.get_by_email(user_data.email)
            if existing_email:
                raise ValueError("邮箱已存在")

            # 创建用户
            hashed_password = get_password_hash(user_data.password)
            # 使用不带时区的datetime对象
            now = datetime.now(UTC).replace(tzinfo=None)

            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False,
                totp_enabled=False,
                created_at=now,
                updated_at=now,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建用户出错: {e!s}")
            raise

    async def update_last_login(self, user_id: int) -> None:
        """
        更新用户的最后登录时间

        Args:
            user_id: 用户ID
        """
        try:
            # 使用不带时区的datetime对象
            now = datetime.now(UTC).replace(tzinfo=None)

            query = update(User).where(User.id == user_id).values(last_login_at=now, updated_at=now)

            await self.db.execute(query)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新用户最后登录时间出错: {e!s}")
            raise

    async def setup_totp(self, user_id: int, totp_secret: str) -> None:
        """
        设置TOTP密钥（加密存储）

        Args:
            user_id: 用户ID
            totp_secret: TOTP密钥（明文）
        """
        try:
            # 加密 TOTP secret
            encrypted_secret = encrypt_totp_secret(totp_secret)

            # 使用datetime.now(timezone.utc)创建带时区的datetime对象，然后使用replace(tzinfo=None)移除时区信息
            current_time = datetime.now(UTC).replace(tzinfo=None)

            query = (
                update(User)
                .where(User.id == user_id)
                .values(
                    totp_secret=encrypted_secret,  # 存储加密后的 secret
                    updated_at=current_time,
                )
            )

            await self.db.execute(query)
            await self.db.commit()

            logger.info(f"用户 {user_id} 的 TOTP secret 已加密存储")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"设置TOTP密钥出错: {e!s}")
            raise

    async def enable_totp(self, user_id: int) -> User:
        """
        启用TOTP两步验证

        Args:
            user_id: 用户ID

        Returns:
            User: 更新后的用户对象
        """
        try:
            # 使用datetime.now(timezone.utc)创建带时区的datetime对象，然后使用replace(tzinfo=None)移除时区信息
            current_time = datetime.now(UTC).replace(tzinfo=None)

            query = (
                update(User)
                .where(User.id == user_id)
                .values(totp_enabled=True, updated_at=current_time)
                .returning(User)
            )

            result = await self.db.execute(query)
            user = result.scalar_one()
            await self.db.commit()

            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"启用TOTP两步验证出错: {e!s}")
            raise

    async def disable_totp(self, user_id: int) -> User:
        """
        禁用TOTP两步验证

        Args:
            user_id: 用户ID

        Returns:
            User: 更新后的用户对象
        """
        try:
            # 使用datetime.now(timezone.utc)创建带时区的datetime对象，然后使用replace(tzinfo=None)移除时区信息
            current_time = datetime.now(UTC).replace(tzinfo=None)

            query = (
                update(User)
                .where(User.id == user_id)
                .values(totp_enabled=False, totp_secret=None, updated_at=current_time)
                .returning(User)
            )

            result = await self.db.execute(query)
            user = result.scalar_one()
            await self.db.commit()

            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"禁用TOTP两步验证出错: {e!s}")
            raise
