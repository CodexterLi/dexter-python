"""
Redis Stream 消息队列包

提供统一的 Redis Stream 消费者架构，支持:
- 通用 StreamConsumer 基类
- ConsumerManager 管理多个消费者
- 自动消费者组创建
- Pending 消息恢复
- 死信队列 (DLQ)

使用方式:

    from app.queue import ConsumerManager, StreamConsumer

    # 1. 实现自定义消费者
    class MyConsumer(StreamConsumer):
        stream_name = "my_queue"

        async def process(self, message: StreamMessage) -> bool:
            # 处理消息
            return True

    # 2. 注册并启动
    manager = ConsumerManager(redis, session_factory)
    manager.register(MyConsumer())
    await manager.start_all()

包结构:
    queue/
    ├── __init__.py           # 导出公共接口
    ├── base.py               # StreamConsumer 基类、StreamMessage
    ├── manager.py            # ConsumerManager
    └── consumers/            # 具体消费者实现
        ├── __init__.py
        └── example.py        # 示例消费者
"""

from app.queue.base import StreamConsumer, StreamMessage
from app.queue.consumers import ExampleConsumer
from app.queue.manager import ConsumerManager

__all__ = [
    "ConsumerManager",
    "ExampleConsumer",
    "StreamConsumer",
    "StreamMessage",
]
