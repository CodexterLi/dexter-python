"""
消费者实现包

包含所有具体的 Stream 消费者实现。

消费者列表:
- ExampleConsumer: 示例消费者 (可作为模板)
"""

from app.queue.consumers.example import ExampleConsumer

__all__ = [
    "ExampleConsumer",
]
