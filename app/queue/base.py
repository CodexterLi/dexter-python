"""
Redis Stream 消费者基类

提供通用的 Stream 消费者实现，子类只需实现 process() 方法。

Features:
- 自动创建消费者组
- XREADGROUP 阻塞读取
- 自动 ACK 成功消息
- Pending 消息恢复 (重启后自动认领)
- 失败重试 + 死信队列 (DLQ)
- 优雅关闭
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.core.logging import logger
from app.db.redis_keys import QueueKeys

if TYPE_CHECKING:
    from redis import asyncio as aioredis


@dataclass
class StreamMessage:
    """
    Stream 消息封装

    Attributes:
        id: 消息 ID (如 "1234567890123-0")
        data: 消息数据字典
        stream: 来源 Stream Key
        retry_count: 已重试次数
        first_seen: 首次处理时间戳 (毫秒)
    """

    id: str
    data: dict[str, str]
    stream: str
    retry_count: int = 0
    first_seen: int = field(default_factory=lambda: int(time.time() * 1000))


class StreamConsumer(ABC):
    """
    Redis Stream 消费者基类

    子类需要:
    1. 设置 stream_name 类属性
    2. 实现 process() 方法

    Example:
        >>> class MyConsumer(StreamConsumer):
        ...     stream_name = "my_queue"
        ...
        ...     async def process(self, message: StreamMessage) -> bool:
        ...         print(f"Processing: {message.data}")
        ...         return True
    """

    # =========================================================================
    # 配置 (子类可重写)
    # =========================================================================

    stream_name: str
    """队列名称，用于日志和内部队列 Key 生成 (必须由子类设置)"""

    # 外部 Stream 配置 (可选，设置后直接使用，否则使用 QueueKeys 生成)
    stream_key: str | None = None
    """直接指定 Stream Key (用于外部 Stream，如 asset:events)"""

    group_name: str | None = None
    """直接指定消费者组名称"""

    batch_size: int = 10
    """每次 XREADGROUP 读取的消息数量"""

    block_ms: int = 5000
    """XREADGROUP 阻塞等待时间 (毫秒)"""

    max_retries: int = 3
    """消息最大重试次数，超过后移入 DLQ"""

    claim_idle_ms: int = 60000
    """认领空闲消息的阈值 (毫秒)，默认 60 秒"""

    # =========================================================================
    # 初始化
    # =========================================================================

    def __init__(
        self,
        redis: aioredis.Redis,
        *,
        instance_id: str = "0",
    ):
        """
        初始化消费者

        Args:
            redis: Redis 客户端
            instance_id: 实例 ID，用于多实例部署区分消费者
        """
        self._redis = redis
        self._instance_id = instance_id
        self._running = False
        self._task: asyncio.Task | None = None

        # 生成 Key 和名称
        # 如果设置了 stream_key，使用外部 Stream；否则使用内部队列
        if self.stream_key:
            # 外部 Stream 模式
            self._stream_key = self.stream_key
            self._group_name = self.group_name or f"{self.stream_name}-consumer-group"
        else:
            # 内部队列模式
            self._stream_key = QueueKeys.stream(self.stream_name)
            self._group_name = QueueKeys.consumer_group(self.stream_name)

        # DLQ 和 consumer name 始终使用内部命名
        self._dlq_key = QueueKeys.dlq(self.stream_name)
        self._consumer_name = QueueKeys.consumer_name(self.stream_name, instance_id)

    # =========================================================================
    # 生命周期
    # =========================================================================

    async def start(self) -> None:
        """启动消费者"""
        if self._running:
            logger.warning(f"[{self.stream_name}] Consumer is already running")
            return

        logger.info(f"[{self.stream_name}] Starting consumer: {self._consumer_name}")

        # 确保消费者组存在
        await self._ensure_group()

        self._running = True
        self._task = asyncio.create_task(
            self._consumer_loop(),
            name=f"consumer-{self.stream_name}",
        )

        logger.info(f"[{self.stream_name}] Consumer started")

    async def stop(self) -> None:
        """停止消费者"""
        if not self._running:
            return

        logger.info(f"[{self.stream_name}] Stopping consumer...")
        self._running = False

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        logger.info(f"[{self.stream_name}] Consumer stopped")

    @property
    def is_running(self) -> bool:
        """检查消费者是否运行中"""
        return self._running

    # =========================================================================
    # 抽象方法
    # =========================================================================

    @abstractmethod
    async def process(self, message: StreamMessage) -> bool:
        """
        处理单条消息

        子类必须实现此方法。

        Args:
            message: 消息对象

        Returns:
            True 表示处理成功 (将 ACK)，False 表示失败 (将重试或移入 DLQ)
        """
        pass

    # =========================================================================
    # 内部方法
    # =========================================================================

    async def _ensure_group(self) -> None:
        """确保消费者组存在"""
        try:
            await self._redis.xgroup_create(
                self._stream_key,
                self._group_name,
                id="0",
                mkstream=True,
            )
            logger.info(f"[{self.stream_name}] Created consumer group: {self._group_name}")
        except Exception as e:
            # BUSYGROUP 表示组已存在，忽略
            if "BUSYGROUP" in str(e):
                logger.debug(f"[{self.stream_name}] Consumer group already exists")
            else:
                raise

    async def _consumer_loop(self) -> None:
        """主消费循环"""
        logger.debug(f"[{self.stream_name}] Consumer loop started")

        # 首先处理 pending 消息 (重启恢复)
        await self._claim_pending()

        while self._running:
            try:
                # 从 Stream 读取新消息
                messages = await self._redis.xreadgroup(
                    groupname=self._group_name,
                    consumername=self._consumer_name,
                    streams={self._stream_key: ">"},
                    count=self.batch_size,
                    block=self.block_ms,
                )

                if not messages:
                    continue

                # 处理消息
                for _stream_key, entries in messages:
                    for msg_id, msg_data in entries:
                        await self._handle_message(msg_id, msg_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.stream_name}] Consumer loop error: {e}", exc_info=True)
                await asyncio.sleep(1)

        logger.debug(f"[{self.stream_name}] Consumer loop stopped")

    async def _claim_pending(self) -> None:
        """认领并处理 pending 消息 (用于重启恢复)"""
        try:
            # 获取 pending 消息信息
            pending = await self._redis.xpending_range(
                self._stream_key,
                self._group_name,
                min="-",
                max="+",
                count=100,
            )

            if not pending:
                logger.debug(f"[{self.stream_name}] No pending messages")
                return

            logger.info(f"[{self.stream_name}] Found {len(pending)} pending messages")

            # 认领空闲时间超过阈值的消息
            msg_ids = [p["message_id"] for p in pending if p["time_since_delivered"] >= self.claim_idle_ms]

            if not msg_ids:
                return

            # XCLAIM 认领消息
            claimed = await self._redis.xclaim(
                self._stream_key,
                self._group_name,
                self._consumer_name,
                min_idle_time=self.claim_idle_ms,
                message_ids=msg_ids,
            )

            logger.info(f"[{self.stream_name}] Claimed {len(claimed)} pending messages")

            # 处理认领的消息
            for msg_id, msg_data in claimed:
                # 查找 pending 信息获取重试次数
                pending_info = next((p for p in pending if p["message_id"] == msg_id), None)
                retry_count = pending_info["times_delivered"] if pending_info else 0

                await self._handle_message(msg_id, msg_data, retry_count=retry_count)

        except Exception as e:
            logger.error(f"[{self.stream_name}] Failed to claim pending: {e}", exc_info=True)

    async def _handle_message(
        self,
        msg_id: bytes | str,
        msg_data: dict,
        *,
        retry_count: int = 0,
    ) -> None:
        """
        处理单条消息

        Args:
            msg_id: 消息 ID
            msg_data: 消息数据 (bytes key/value)
            retry_count: 已重试次数
        """
        # 解码消息 ID
        if isinstance(msg_id, bytes):
            msg_id = msg_id.decode("utf-8")

        # 解码消息数据
        decoded_data: dict[str, str] = {}
        for k, v in msg_data.items():
            key = k.decode("utf-8") if isinstance(k, bytes) else k
            value = v.decode("utf-8") if isinstance(v, bytes) else v
            decoded_data[key] = value

        message = StreamMessage(
            id=msg_id,
            data=decoded_data,
            stream=self._stream_key,
            retry_count=retry_count,
        )

        try:
            # 调用子类的处理方法
            success = await self.process(message)

            if success:
                # 处理成功，ACK 消息
                await self._redis.xack(self._stream_key, self._group_name, msg_id)
                logger.debug(f"[{self.stream_name}] Message {msg_id} processed and ACKed")
            else:
                # 处理失败
                await self._handle_failure(message, "Process returned False")

        except Exception as e:
            logger.error(f"[{self.stream_name}] Failed to process message {msg_id}: {e}")
            await self._handle_failure(message, str(e))

    async def _handle_failure(self, message: StreamMessage, error: str) -> None:
        """
        处理失败的消息

        Args:
            message: 消息对象
            error: 错误信息
        """
        if message.retry_count >= self.max_retries:
            # 超过最大重试次数，移入 DLQ
            await self._move_to_dlq(message, error)
            # ACK 原消息 (从 pending 中移除)
            await self._redis.xack(self._stream_key, self._group_name, message.id)
            logger.warning(
                f"[{self.stream_name}] Message {message.id} moved to DLQ after {message.retry_count} retries"
            )
        else:
            # 保留在 pending 中，等待下次 claim
            logger.debug(
                f"[{self.stream_name}] Message {message.id} will be retried "
                f"(attempt {message.retry_count + 1}/{self.max_retries})"
            )

    async def _move_to_dlq(self, message: StreamMessage, error: str) -> None:
        """
        将消息移入死信队列

        Args:
            message: 消息对象
            error: 错误信息
        """
        dlq_data = {
            **message.data,
            "_original_id": message.id,
            "_original_stream": message.stream,
            "_error": error,
            "_retry_count": str(message.retry_count),
            "_failed_at": str(int(time.time() * 1000)),
        }

        await self._redis.xadd(self._dlq_key, dlq_data)

    # =========================================================================
    # 状态查询
    # =========================================================================

    async def get_status(self) -> dict:
        """
        获取消费者状态

        Returns:
            状态字典
        """
        try:
            # 获取 Stream 长度
            stream_len = await self._redis.xlen(self._stream_key)

            # 获取 pending 数量
            pending_info = await self._redis.xpending(self._stream_key, self._group_name)
            pending_count = pending_info["pending"] if pending_info else 0

            # 获取 DLQ 长度
            dlq_len = await self._redis.xlen(self._dlq_key)

            return {
                "stream_name": self.stream_name,
                "consumer_name": self._consumer_name,
                "running": self._running,
                "stream_length": stream_len,
                "pending_count": pending_count,
                "dlq_length": dlq_len,
            }
        except Exception as e:
            return {
                "stream_name": self.stream_name,
                "consumer_name": self._consumer_name,
                "running": self._running,
                "error": str(e),
            }
