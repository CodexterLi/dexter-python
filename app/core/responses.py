"""
Google 风格 API 响应格式

遵循 Google JSON Style Guide，直接返回数据，依赖 HTTP 状态码表示结果。

示例:
    # 成功响应 (HTTP 200) - 直接返回数据
    {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com"
    }

    # 列表响应 (HTTP 200)
    {
        "items": [...],
        "totalCount": 100,
        "nextPageToken": "xxx"
    }

    # 错误响应 (HTTP 4xx/5xx)
    {
        "error": {
            "code": 400,
            "message": "Invalid request",
            "details": [...]
        }
    }
"""

from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

# ============ 响应工具函数 ============


def ok(
    data: Any = None,
    status_code: int = status.HTTP_200_OK,
    headers: dict | None = None,
) -> JSONResponse:
    """
    成功响应 - 直接返回数据

    Args:
        data: 响应数据（直接作为响应体）
        status_code: HTTP 状态码，默认 200
        headers: 可选的响应头

    Returns:
        JSONResponse

    Example:
        >>> return ok({"id": 1, "username": "admin"})
        # Response (HTTP 200):
        # {"id": 1, "username": "admin"}
    """
    content = jsonable_encoder(data) if data is not None else None

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
    )


def created(
    data: Any = None,
    headers: dict | None = None,
) -> JSONResponse:
    """
    创建成功响应 (HTTP 201) - 直接返回数据

    Args:
        data: 创建的资源数据
        headers: 可选的响应头

    Returns:
        JSONResponse

    Example:
        >>> return created({"id": 2, "username": "newuser"})
        # Response (HTTP 201):
        # {"id": 2, "username": "newuser"}
    """
    return ok(data=data, status_code=status.HTTP_201_CREATED, headers=headers)


def no_content() -> JSONResponse:
    """
    无内容响应 (HTTP 204)

    用于删除操作等不需要返回数据的场景

    Returns:
        JSONResponse
    """
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


def list_response(
    items: list[Any],
    total_count: int | None = None,
    next_page_token: str | None = None,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """
    列表响应 - 直接返回列表结构

    Args:
        items: 列表数据
        total_count: 总数量（可选）
        next_page_token: 下一页令牌（可选）
        status_code: HTTP 状态码

    Returns:
        JSONResponse

    Example:
        >>> return list_response(users, total_count=100)
        # Response (HTTP 200):
        # {"items": [...], "totalCount": 100}
    """
    data = {
        "items": jsonable_encoder(items),
    }

    if total_count is not None:
        data["totalCount"] = total_count

    if next_page_token is not None:
        data["nextPageToken"] = next_page_token

    return JSONResponse(
        status_code=status_code,
        content=data,
    )


def error(
    message: str,
    code: int = status.HTTP_400_BAD_REQUEST,
    details: list[dict] | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    """
    错误响应

    Args:
        message: 错误消息
        code: HTTP 状态码
        details: 错误详情列表
        headers: 可选的响应头

    Returns:
        JSONResponse

    Example:
        >>> return error("Invalid request", code=400, details=[
        ...     {"field": "email", "message": "Invalid email format"}
        ... ])
        # Response (HTTP 400):
        # {"error": {"code": 400, "message": "Invalid request", "details": [...]}}
    """
    content = {
        "error": {
            "code": code,
            "message": message,
        }
    }

    if details:
        content["error"]["details"] = details

    return JSONResponse(
        status_code=code,
        content=content,
        headers=headers,
    )
