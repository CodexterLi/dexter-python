"""
统一日志配置模块 这个模块提供了统一的日志配置，将标准logging模块与loguru进行桥接，
使得无论使用哪种日志库，日志都能正确显示。
"""

import logging
import os
import sys
from pathlib import Path

from loguru import logger

# 日志文件路径
LOG_PATH = Path("logs")
LOG_PATH.mkdir(exist_ok=True)

# 从环境变量读取日志级别，默认 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 日志格式
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"


class InterceptHandler(logging.Handler):
    """
    将标准logging模块的日志重定向到loguru

    这个处理器拦截所有logging模块的日志，并将它们转发给loguru处理
    """

    def emit(self, record):
        # 获取对应的loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到记录的调用者
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 将日志转发给loguru
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(debug: bool = False):
    """
    设置统一的日志配置

    Args:
        debug: 是否开启调试模式，开启后显示更多日志

    - 配置loguru记录器
    - 将标准logging模块的日志重定向到loguru
    """
    # 移除所有默认处理器
    logger.remove()

    # 确定日志级别
    level = "DEBUG" if debug or LOG_LEVEL == "DEBUG" else LOG_LEVEL

    # 添加控制台处理器
    logger.add(sys.stdout, format=LOG_FORMAT, level=level, colorize=True)

    # 添加文件处理器 (DEBUG 级别，记录所有日志)
    logger.add(
        LOG_PATH / "app.log",
        rotation="10 MB",
        retention="1 week",
        format=LOG_FORMAT,
        level="DEBUG",  # 文件记录所有级别
        compression="zip",
    )

    # 禁用SQLAlchemy的SQL日志输出
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

    # 将标准logging模块的日志重定向到loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 设置第三方库的日志级别
    for logger_name in logging.root.manager.loggerDict:
        if not logger_name.startswith("sqlalchemy"):
            logging.getLogger(logger_name).handlers = []
            logging.getLogger(logger_name).propagate = True
            logging.getLogger(logger_name).setLevel(logging.INFO)

    # 减少 uvicorn 启动日志
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    # 减少 httpx 日志 (OpenRouter HTTP 请求)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger.info(f"日志系统初始化完成, 级别: {level}")


# 导出logger实例，可以在其他模块中直接使用
__all__ = ["logger", "setup_logging"]
