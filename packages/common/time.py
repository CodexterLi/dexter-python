"""Time helpers shared by backend services."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

UTC_PLUS_8 = timezone(timedelta(hours=8))


def utc_now() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(UTC)


class TimezoneUtils:
    """UTC+8 convenience helpers used by auth token and cookie code."""

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC_PLUS_8)

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(UTC_PLUS_8)

    @staticmethod
    def now_naive() -> datetime:
        return datetime.now(UTC_PLUS_8).replace(tzinfo=None)

    @staticmethod
    def timestamp() -> float:
        return datetime.now(UTC_PLUS_8).timestamp()

    @staticmethod
    def timestamp_int() -> int:
        return int(datetime.now(UTC_PLUS_8).timestamp())

    @staticmethod
    def isoformat() -> str:
        return datetime.now(UTC_PLUS_8).isoformat()

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        return datetime.fromtimestamp(timestamp, UTC_PLUS_8)

    @staticmethod
    def to_utc8(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC_PLUS_8)
        return dt.astimezone(UTC_PLUS_8)

    @staticmethod
    def get_okx_timestamp() -> str:
        return datetime.now(UTC_PLUS_8).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


tz = TimezoneUtils()
