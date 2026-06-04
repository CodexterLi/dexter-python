"""
示例消费者

这是一个基础的 Stream 消费者示例，展示如何实现自定义消费者。

使用方式:
    1. 复制此文件，重命名为你的消费者名称
    2. 修改 stream_name 为你的队列名称
    3. 实现 process() 方法处理具体业务逻辑
    4. 在 ConsumerManager 中注册消费者
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import logger
from app.queue.base import StreamConsumer, StreamMessage

if TYPE_CHECKING:
    from redis import asyncio as aioredis
    from sqlalchemy.ext.asyncio import async_sessionmaker


class ExampleConsumer(StreamConsumer):
    """
    示例消费者

    演示 StreamConsumer 的基本用法。

    Features:
    - 继承 StreamConsumer 基类
    - 设置队列配置
    - 实现 process() 方法

    Example:
        >>> consumer = ExampleConsumer(redis, session_factory)
        >>> await consumer.start()
    """

    # =========================================================================
    # 配置
    # =========================================================================

    stream_name = "example"
    """队列名称 (用于日志和 Key 生成)"""

    # 可选: 指定外部 Stream Key (默认使用 QueueKeys 生成)
    # stream_key = "external:events"
    # group_name = "my-consumer-group"

    batch_size = 10
    """每次读取的消息数量"""

    block_ms = 5000
    """阻塞等待时间 (毫秒)"""

    max_retries = 3
    """最大重试次数"""

    # =========================================================================
    # 初始化
    # =========================================================================

    def __init__(
        self,
        redis: aioredis.Redis,
        session_factory: async_sessionmaker,
        *,
        instance_id: str = "0",
    ):
        """
        初始化消费者

        Args:
            redis: Redis 客户端
            session_factory: 数据库会话工厂
            instance_id: 实例 ID (多实例部署时区分)
        """
        super().__init__(redis, instance_id=instance_id)
        self._session_factory = session_factory

    # =========================================================================
    # 消息处理
    # =========================================================================

    async def process(self, message: StreamMessage) -> bool:
        """
        处理消息

        Args:
            message: Stream 消息

        Returns:
            True 表示处理成功 (将 ACK)，False 表示失败 (将重试)
        """
        logger.info(f"[{self.stream_name}] Processing message: {message.id}")
        logger.debug(f"[{self.stream_name}] Message data: {message.data}")

        try:
            # TODO: 在这里实现你的业务逻辑
            # 例如:
            # async with self._session_factory() as session:
            #     # 处理数据库操作
            #     await session.commit()

            # 示例: 打印消息内容
            for key, value in message.data.items():
                logger.debug(f"  {key}: {value}")

            logger.info(f"[{self.stream_name}] Message {message.id} processed successfully")
            return True

        except Exception as e:
            logger.error(f"[{self.stream_name}] Failed to process message {message.id}: {e}")
            return False
