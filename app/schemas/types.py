"""
通用 Schema 类型定义

提供项目中复用的自定义 Pydantic 类型。
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema


def _validate_snowflake_id(value: Any) -> int:
    """
    验证并转换 Snowflake ID

    接受 int 或 str 类型，统一转换为 int 存储。
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError(f"Invalid Snowflake ID: {value}")


def _serialize_snowflake_id(value: int) -> str:
    """
    序列化 Snowflake ID 为字符串

    避免 JavaScript Number 精度丢失 (超过 2^53 - 1)。
    """
    return str(value)


# Snowflake ID 类型
# - 内部存储为 int (与数据库一致)
# - JSON 序列化为 str (避免前端精度丢失)
# - 接受 int 或 str 输入
# - OpenAPI schema 显示为 string (让前端正确生成类型)
SnowflakeId = Annotated[
    int,
    BeforeValidator(_validate_snowflake_id),
    PlainSerializer(_serialize_snowflake_id, return_type=str),
    WithJsonSchema({"type": "string", "description": "Snowflake ID (string to avoid precision loss)"}),
]
