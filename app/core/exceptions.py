"""
异常处理模块

定义自定义异常类和全局异常处理器。
采用 Google 风格的错误响应格式。

错误响应格式:
{
    "error": {
        "code": 400,
        "message": "Invalid request",
        "details": [
            {"field": "email", "message": "Invalid email format"}
        ]
    }
}
"""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# ============ 自定义异常类 ============


class APIException(Exception):
    """API 基础异常类"""

    def __init__(
        self,
        message: str,
        code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message
        self.code = code
        self.details = details
        self.headers = headers
        super().__init__(message)


class BadRequestException(APIException):
    """请求参数错误异常 (400)"""

    def __init__(
        self,
        message: str = "Bad request",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            message=message,
            code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class UnauthorizedException(APIException):
    """未授权异常 (401)"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(APIException):
    """禁止访问异常 (403)"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, code=status.HTTP_403_FORBIDDEN)


class NotFoundException(APIException):
    """资源未找到异常 (404)"""

    def __init__(self, message: str = "Not found"):
        super().__init__(message=message, code=status.HTTP_404_NOT_FOUND)


class ConflictException(APIException):
    """资源冲突异常 (409)"""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message=message, code=status.HTTP_409_CONFLICT)


class UnprocessableEntityException(APIException):
    """无法处理的实体异常 (422)"""

    def __init__(
        self,
        message: str = "Unprocessable entity",
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(
            message=message,
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ServiceUnavailableException(APIException):
    """服务不可用异常 (503)"""

    def __init__(self, message: str = "Service unavailable"):
        super().__init__(
            message=message,
            code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ============ 异常处理器 ============


def _build_error_response(
    code: int,
    message: str,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """构建 Google 风格的错误响应"""
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


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """处理自定义 API 异常"""
    return _build_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """处理请求验证异常"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        details.append(
            {
                "field": field,
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", ""),
            }
        )

    return _build_error_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        details=details,
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """处理 Pydantic 验证异常"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        details.append(
            {
                "field": field,
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", ""),
            }
        )

    return _build_error_response(
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        details=details,
    )


async def internal_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """处理未捕获的内部异常"""
    return _build_error_response(
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="Internal server error",
    )
