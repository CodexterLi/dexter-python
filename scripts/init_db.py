#!/usr/bin/env python3
"""Apply raw SQL migrations from the migrations directory."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from app.core.logging import logger, setup_logging
from app.db.postgres import close_db, get_engine

MIGRATIONS_DIR = Path("migrations")


def _migration_files() -> list[Path]:
    if not MIGRATIONS_DIR.exists():
        raise FileNotFoundError(f"迁移目录不存在: {MIGRATIONS_DIR}")

    files = sorted(path for path in MIGRATIONS_DIR.glob("*.sql") if path.is_file())
    if not files:
        raise FileNotFoundError(f"迁移目录没有 SQL 文件: {MIGRATIONS_DIR}")
    return files


async def _apply_migration(path: Path) -> None:
    sql = path.read_text(encoding="utf-8").strip()
    if not sql:
        logger.warning(f"跳过空迁移文件: {path}")
        return

    engine = get_engine()
    async with engine.begin() as conn:
        raw_conn = await conn.get_raw_connection()
        await raw_conn.driver_connection.execute(sql)

    logger.info(f"已执行迁移: {path}")


async def _run() -> None:
    setup_logging()
    try:
        for path in _migration_files():
            await _apply_migration(path)
        logger.info("数据库 SQL 初始化完成")
    finally:
        await close_db()


def main() -> None:
    """按编号顺序执行 migrations/*.sql 初始化数据库。"""
    asyncio.run(_run())


if __name__ == "__main__":
    typer.run(main)
