"""
Snowflake ID generator shared by backend services.

Compatible with Go bwmarrin/snowflake:
- 41-bit timestamp
- 10-bit machine id
- 12-bit sequence
"""

from __future__ import annotations

import os
import threading
import time
from typing import TypedDict

EPOCH = 1288834974657

MACHINE_ID_BITS = 10
SEQUENCE_BITS = 12
MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1

MACHINE_ID_SHIFT = SEQUENCE_BITS
TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS


class ParsedSnowflake(TypedDict):
    timestamp: int
    machine_id: int
    sequence: int
    datetime: str


class SnowflakeGenerator:
    """Thread-safe Snowflake ID generator."""

    _instance: SnowflakeGenerator | None = None
    _lock = threading.Lock()

    def __init__(self, machine_id: int):
        if machine_id < 0 or machine_id > MAX_MACHINE_ID:
            raise ValueError(f"machine_id must be between 0 and {MAX_MACHINE_ID}")

        self._machine_id = machine_id
        self._sequence = 0
        self._last_timestamp = -1
        self._seq_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> SnowflakeGenerator:
        """Return the process-wide generator using SNOWFLAKE_MACHINE_ID, defaulting to 512."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    machine_id = int(os.environ.get("SNOWFLAKE_MACHINE_ID", "512"))
                    cls._instance = cls(machine_id)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton, intended for tests."""
        with cls._lock:
            cls._instance = None

    def generate(self) -> int:
        with self._seq_lock:
            timestamp = self._current_millis()

            if timestamp < self._last_timestamp:
                raise RuntimeError(
                    f"Clock moved backwards. Refusing to generate ID for {self._last_timestamp - timestamp}ms"
                )

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & MAX_SEQUENCE
                if self._sequence == 0:
                    timestamp = self._wait_next_millis(self._last_timestamp)
            else:
                self._sequence = 0

            self._last_timestamp = timestamp
            return ((timestamp - EPOCH) << TIMESTAMP_SHIFT) | (self._machine_id << MACHINE_ID_SHIFT) | self._sequence

    def _current_millis(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last: int) -> int:
        timestamp = self._current_millis()
        while timestamp <= last:
            timestamp = self._current_millis()
        return timestamp

    @property
    def machine_id(self) -> int:
        return self._machine_id


def generate_id() -> int:
    """Generate a Snowflake ID using the process-wide generator."""
    return SnowflakeGenerator.get_instance().generate()


def parse_id(snowflake_id: int) -> ParsedSnowflake:
    """Parse a Snowflake ID into timestamp, machine id, sequence, and local datetime string."""
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
    """Convert an ID to a string for JSON clients that cannot safely handle int64."""
    return str(snowflake_id)


def str_to_id(id_str: str) -> int:
    """Convert an ID string back to int."""
    return int(id_str)
