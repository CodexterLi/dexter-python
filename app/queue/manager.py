"""
消费者管理器

管理多个 Redis Stream 消费者的生命周期。

Features:
- 注册多个消费者
- 统一启动/停止
- 状态查询
- 单例模式
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import logger

if TYPE_CHECKING:
    from app.queue.base import StreamConsumer


class ConsumerManager:
    """
    消费者管理器

    统一管理多个 Stream 消费者的生命周期。

    Example:
        >>> manager = ConsumerManager()
        >>> manager.register(EnergyDepositConsumer(redis, session_factory))
        >>> manager.register(OrderNotificationConsumer(redis))
        >>>
        >>> await manager.start_all()
        >>> # ... 应用运行 ...
        >>> await manager.stop_all()
    """

    _instance: ConsumerManager | None = None

    def __init__(self):
        """初始化管理器"""
        self._consumers: list[StreamConsumer] = []
        self._running = False

    @classmethod
    def get_instance(cls) -> ConsumerManager:
        """
        获取单例实例

        Returns:
            ConsumerManager 实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, consumer: StreamConsumer) -> None:
        """
        注册消费者

        Args:
            consumer: StreamConsumer 实例
        """
        # 检查是否已注册同名消费者
        existing = next(
            (c for c in self._consumers if c.stream_name == consumer.stream_name),
            None,
        )
        if existing:
            logger.warning(f"Consumer for stream '{consumer.stream_name}' already registered, replacing")
            self._consumers.remove(existing)

        self._consumers.append(consumer)
        logger.info(f"Registered consumer: {consumer.stream_name}")

    def unregister(self, stream_name: str) -> bool:
        """
        注销消费者

        Args:
            stream_name: 队列名称

        Returns:
            是否成功注销
        """
        consumer = next(
            (c for c in self._consumers if c.stream_name == stream_name),
            None,
        )
        if consumer:
            self._consumers.remove(consumer)
            logger.info(f"Unregistered consumer: {stream_name}")
            return True
        return False

    async def start_all(self) -> None:
        """启动所有消费者"""
        if self._running:
            logger.warning("ConsumerManager is already running")
            return

        if not self._consumers:
            logger.warning("No consumers registered")
            return

        logger.info(f"Starting {len(self._consumers)} consumer(s)...")

        for consumer in self._consumers:
            try:
                await consumer.start()
            except Exception as e:
                logger.error(f"Failed to start consumer {consumer.stream_name}: {e}")

        self._running = True
        logger.info("All consumers started")

    async def stop_all(self) -> None:
        """停止所有消费者"""
        if not self._running:
            return

        logger.info(f"Stopping {len(self._consumers)} consumer(s)...")

        for consumer in self._consumers:
            try:
                await consumer.stop()
            except Exception as e:
                logger.error(f"Failed to stop consumer {consumer.stream_name}: {e}")

        self._running = False
        logger.info("All consumers stopped")

    async def start_one(self, stream_name: str) -> bool:
        """
        启动单个消费者

        Args:
            stream_name: 队列名称

        Returns:
            是否成功启动
        """
        consumer = next(
            (c for c in self._consumers if c.stream_name == stream_name),
            None,
        )
        if not consumer:
            logger.warning(f"Consumer not found: {stream_name}")
            return False

        try:
            await consumer.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start consumer {stream_name}: {e}")
            return False

    async def stop_one(self, stream_name: str) -> bool:
        """
        停止单个消费者

        Args:
            stream_name: 队列名称

        Returns:
            是否成功停止
        """
        consumer = next(
            (c for c in self._consumers if c.stream_name == stream_name),
            None,
        )
        if not consumer:
            logger.warning(f"Consumer not found: {stream_name}")
            return False

        try:
            await consumer.stop()
            return True
        except Exception as e:
            logger.error(f"Failed to stop consumer {stream_name}: {e}")
            return False

    @property
    def is_running(self) -> bool:
        """检查管理器是否运行中"""
        return self._running

    @property
    def consumer_count(self) -> int:
        """获取注册的消费者数量"""
        return len(self._consumers)

    def get_consumer(self, stream_name: str) -> StreamConsumer | None:
        """
        获取指定消费者

        Args:
            stream_name: 队列名称

        Returns:
            消费者实例，不存在返回 None
        """
        return next(
            (c for c in self._consumers if c.stream_name == stream_name),
            None,
        )

    async def get_status(self) -> dict:
        """
        获取所有消费者状态

        Returns:
            状态字典
        """
        consumers_status = []
        for consumer in self._consumers:
            try:
                status = await consumer.get_status()
                consumers_status.append(status)
            except Exception as e:
                consumers_status.append(
                    {
                        "stream_name": consumer.stream_name,
                        "error": str(e),
                    }
                )

        return {
            "running": self._running,
            "consumer_count": len(self._consumers),
            "consumers": consumers_status,
        }
