"""
Snowflake ID Generator

与 Go bwmarrin/snowflake 库兼容:
- 时间戳: 41 bits (69年)
- 机器ID: 10 bits (0-1023)
- 序列号: 12 bits (4096/ms)

Machine ID 分配策略:
- 通过环境变量 SNOWFLAKE_MACHINE_ID 配置
- Go 端和 Python 端各自独立配置，确保不冲突
- 建议: Go 端使用 0-511，Python 端使用 512-1023
"""

from __future__ import annotations

import os
import threading
import time

# Twitter Snowflake 默认 epoch (2010-11-04 01:42:54 UTC)
# 与 bwmarrin/snowflake Go 库一致
EPOCH = 1288834974657

# 位分配
MACHINE_ID_BITS = 10
SEQUENCE_BITS = 12
MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1  # 1023
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1  # 4095

# 位移量
MACHINE_ID_SHIFT = SEQUENCE_BITS
TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS


class SnowflakeGenerator:
    """
    Snowflake ID 生成器

    线程安全，单例模式

    Example:
        >>> from app.utils.snowflake import generate_id
        >>> id = generate_id()
        >>> print(id)  # 类似 7449876543210123456
    """

    _instance: SnowflakeGenerator | None = None
    _lock = threading.Lock()

    def __init__(self, machine_id: int):
        """
        初始化生成器

        Args:
            machine_id: 机器 ID (0-1023)

        Raises:
            ValueError: machine_id 超出范围
        """
        if machine_id < 0 or machine_id > MAX_MACHINE_ID:
            raise ValueError(f"machine_id must be between 0 and {MAX_MACHINE_ID}")

        self._machine_id = machine_id
        self._sequence = 0
        self._last_timestamp = -1
        self._seq_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> SnowflakeGenerator:
        """
        获取单例实例

        从环境变量 SNOWFLAKE_MACHINE_ID 读取机器 ID
        默认值为 512 (Python 服务默认使用 512-1023 范围)

        Returns:
            SnowflakeGenerator 实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    machine_id = int(os.environ.get("SNOWFLAKE_MACHINE_ID", "512"))
                    cls._instance = cls(machine_id)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """重置单例实例 (仅用于测试)"""
        with cls._lock:
            cls._instance = None

    def generate(self) -> int:
        """
        生成一个 Snowflake ID

        线程安全，同一毫秒内最多生成 4096 个 ID

        Returns:
            64 位整数 ID

        Raises:
            RuntimeError: 时钟回拨
        """
        with self._seq_lock:
            timestamp = self._current_millis()

            # 检查时钟回拨
            if timestamp < self._last_timestamp:
                raise RuntimeError(
                    f"Clock moved backwards. Refusing to generate ID for {self._last_timestamp - timestamp}ms"
                )

            if timestamp == self._last_timestamp:
                # 同一毫秒内，序列号递增
                self._sequence = (self._sequence + 1) & MAX_SEQUENCE
                if self._sequence == 0:
                    # 序列号溢出，等待下一毫秒
                    timestamp = self._wait_next_millis(self._last_timestamp)
            else:
                # 新的毫秒，序列号归零
                self._sequence = 0

            self._last_timestamp = timestamp

            # 组装 ID: timestamp | machine_id | sequence
            return ((timestamp - EPOCH) << TIMESTAMP_SHIFT) | (self._machine_id << MACHINE_ID_SHIFT) | self._sequence

    def _current_millis(self) -> int:
        """获取当前时间戳 (毫秒)"""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last: int) -> int:
        """等待下一毫秒"""
        timestamp = self._current_millis()
        while timestamp <= last:
            timestamp = self._current_millis()
        return timestamp

    @property
    def machine_id(self) -> int:
        """获取机器 ID"""
        return self._machine_id


def generate_id() -> int:
    """
    生成一个 Snowflake ID

    便捷函数，使用全局单例生成器

    Returns:
        64 位整数 ID

    Example:
        >>> id = generate_id()
        >>> print(id)
    """
    return SnowflakeGenerator.get_instance().generate()


def parse_id(snowflake_id: int) -> dict:
    """
    解析 Snowflake ID

    Args:
        snowflake_id: 要解析的 ID

    Returns:
        包含 timestamp, machine_id, sequence 的字典

    Example:
        >>> info = parse_id(7449876543210123456)
        >>> print(info['timestamp'])  # Unix 时间戳 (毫秒)
        >>> print(info['machine_id'])  # 机器 ID
        >>> print(info['sequence'])  # 序列号
    """
    timestamp = ((snowflake_id >> TIMESTAMP_SHIFT) & 0x1FFFFFFFFFF) + EPOCH
    machine_id = (snowflake_id >> MACHINE_ID_SHIFT) & MAX_MACHINE_ID
    sequence = snowflake_id & MAX_SEQUENCE

    return {
        "timestamp": timestamp,
        "machine_id": machine_id,
        "sequence": sequence,
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000)),
    }


def id_to_str(snowflake_id: int) -> str:
    """
    将 Snowflake ID 转换为字符串

    用于 JSON 序列化，避免 JavaScript 大数精度丢失

    Args:
        snowflake_id: Snowflake ID

    Returns:
        字符串形式的 ID
    """
    return str(snowflake_id)


def str_to_id(id_str: str) -> int:
    """
    将字符串转换为 Snowflake ID

    Args:
        id_str: 字符串形式的 ID

    Returns:
        整数 ID
    """
    return int(id_str)
