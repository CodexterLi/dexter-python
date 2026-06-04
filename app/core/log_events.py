"""
日志事件格式化工具

提供统一的日志框格式，用于 gRPC、Stream、API 等场景的事件日志。

使用示例:
    from app.core.log_events import build_log_box

    logger.info(
        build_log_box(
            "gRPC 请求: StoreEncryptedKey",
            {"user_id": 123, "wallet_address": "0x..."},
        )
    )

规范文档: .claude/rules/log-events.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

# 敏感字段列表 - 这些字段会被自动遮蔽
SENSITIVE_FIELDS: set[str] = {
    "encrypted_key",
    "private_key",
    "secret",
    "password",
    "token",
    "api_key",
    "api_secret",
}


def build_log_box(
    title: str,
    fields: dict[str, Any],
    *,
    success: bool | None = None,
    mask_fields: set[str] | None = None,
    field_width: int = 18,
) -> str:
    """
    构建格式化的日志框

    参考 Go 代码风格的 ASCII 边框日志格式。

    Args:
        title: 日志标题 (如 "gRPC 请求: StoreEncryptedKey")
        fields: 要打印的字段字典
        success: 可选，标记成功/失败状态
        mask_fields: 需要遮蔽的字段名集合 (默认使用 SENSITIVE_FIELDS)
        field_width: 字段名宽度 (默认 18)

    Returns:
        格式化的日志字符串

    Example:
        >>> build_log_box("gRPC 请求: Test", {"user_id": 123}, success=True)
        ╔════...════╗
        ║ [2026-01-28 10:30:00] gRPC 请求: Test (成功)
        ╠════...════╣
        ║ user_id:           123
        ╚════...════╝
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = ""
    if success is not None:
        status = " (成功)" if success else " (失败)"

    mask_set = mask_fields if mask_fields is not None else SENSITIVE_FIELDS

    lines = [
        "",
        "╔══════════════════════════════════════════════════════════════════════════════╗",
        f"║ [{timestamp}] {title}{status}",
        "╠══════════════════════════════════════════════════════════════════════════════╣",
    ]

    for key, value in fields.items():
        # 处理敏感字段 - 只显示前后几个字符
        if key in mask_set and value:
            value = mask_sensitive(str(value))
        lines.append(f"║ {key + ':':<{field_width}} {value}")

    lines.append("╚══════════════════════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def mask_sensitive(value: str, visible_chars: int = 8) -> str:
    """
    遮蔽敏感信息，只显示前后几个字符

    Args:
        value: 原始字符串
        visible_chars: 前后各显示的字符数

    Returns:
        遮蔽后的字符串

    Example:
        >>> mask_sensitive("abcdefghijklmnopqrstuvwxyz")
        'abcdefgh...stuvwxyz (len=26)'
    """
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
    return f"{value[:visible_chars]}...{value[-visible_chars:]} (len={len(value)})"
