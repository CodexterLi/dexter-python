"""
时区工具类
提供统一的UTC+8时间处理功能
"""

from datetime import datetime, timedelta, timezone

# 定义UTC+8时区
UTC_PLUS_8 = timezone(timedelta(hours=8))


class TimezoneUtils:
    """时区工具类"""

    @staticmethod
    def now() -> datetime:
        """
        获取当前UTC+8时间

        Returns:
            datetime: 当前UTC+8时间
        """
        return datetime.now(UTC_PLUS_8)

    @staticmethod
    def utcnow() -> datetime:
        """
        获取当前UTC+8时间（替代datetime.utcnow()）

        Returns:
            datetime: 当前UTC+8时间
        """
        return datetime.now(UTC_PLUS_8)

    @staticmethod
    def now_naive() -> datetime:
        """
        获取当前UTC+8时间（无时区信息）
        用于与数据库兼容

        Returns:
            datetime: 当前UTC+8时间（无时区信息）
        """
        return datetime.now(UTC_PLUS_8).replace(tzinfo=None)

    @staticmethod
    def timestamp() -> float:
        """
        获取当前UTC+8时间戳

        Returns:
            float: 当前时间戳
        """
        return datetime.now(UTC_PLUS_8).timestamp()

    @staticmethod
    def timestamp_int() -> int:
        """
        获取当前UTC+8时间戳（整数）

        Returns:
            int: 当前时间戳（整数）
        """
        return int(datetime.now(UTC_PLUS_8).timestamp())

    @staticmethod
    def isoformat() -> str:
        """
        获取当前UTC+8时间的ISO格式字符串

        Returns:
            str: ISO格式时间字符串
        """
        return datetime.now(UTC_PLUS_8).isoformat()

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        """
        从时间戳创建UTC+8时间

        Args:
            timestamp: 时间戳

        Returns:
            datetime: UTC+8时间
        """
        return datetime.fromtimestamp(timestamp, UTC_PLUS_8)

    @staticmethod
    def to_utc8(dt: datetime) -> datetime:
        """
        将datetime对象转换为UTC+8时区

        Args:
            dt: datetime对象

        Returns:
            datetime: UTC+8时区的datetime对象
        """
        if dt.tzinfo is None:
            # 如果没有时区信息，假设为UTC+8
            return dt.replace(tzinfo=UTC_PLUS_8)
        else:
            # 如果有时区信息，转换为UTC+8
            return dt.astimezone(UTC_PLUS_8)

    @staticmethod
    def get_okx_timestamp() -> str:
        """
        获取OKX API所需的时间戳格式

        Returns:
            str: OKX时间戳格式
        """
        return datetime.now(UTC_PLUS_8).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# 全局时区工具实例
tz = TimezoneUtils()
