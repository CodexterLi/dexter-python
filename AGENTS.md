# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Drexor Backend is a FastAPI-based **infrastructure-core** backend with Web3 authentication.
It provides user auth (JWT + wallet + TOTP), API keys, PostgreSQL + Redis, scheduled tasks,
a Redis-Streams queue framework, and real-time WebSocket communication.

There is **no AI/Agent runtime** in this repository — it was removed during the front/back split.
The frontend lives in a separate repository.

**Stack**: Python 3.14, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Redis, APScheduler, uv

## Commands

| Command         | Purpose                                            |
| --------------- | -------------------------------------------------- |
| `make install`  | Install dependencies via `uv sync`                 |
| `make dev`      | Dev server with hot-reload (http://localhost:8000) |
| `make lint`     | Ruff check + format check (uses `uvx`)             |
| `make format`   | Auto-fix + format code (uses `uvx`)                |
| `make test`     | Run pytest                                         |
| `make upgrade`  | Upgrade all dependencies                           |

Linting and formatting use `uvx ruff` (not `uv run ruff`) — ruff is not a project dependency.

## Architecture

```
Client ──▶ FastAPI (uvicorn :8000)
               ├── Auth (JWT / Wallet / TOTP / API Key)
               ├── Scheduler (APScheduler cron/interval jobs)
               ├── Queue (Redis Streams consumers)
               └── WebSocket (broadcast / personal)
```

Single layer: all code lives under `app/` with the `app.*` import prefix.

### Source Layout — App (`app/`)

- **`main.py`** — Entry point. Lifespan manages DB + Redis init/shutdown. Registers CORS, exception handlers.
- **`config/`** — Pydantic Settings loading from local `.env`.
- **`core/`** — Cross-cutting concerns:
  - `security/` — JWT, bcrypt, TOTP (encrypted), wallet verification, API key validation
  - `responses.py` — Google JSON style responses (`{ items, totalCount }` / `{ error: { code, message } }`)
  - `exceptions.py` — Exception hierarchy (`APIException` → `BadRequestException`, `UnauthorizedException`, etc.)
  - `logging.py` — Loguru setup, bridges stdlib logging, file rotation
- **`db/`** — Database layer:
  - `postgres.py` — Async SQLAlchemy engine + session factory, lazy init, `get_db()` dependency
  - `redis.py` — Async Redis client with connection pool, SSL/ACL support
  - `redis_keys/` — Key namespace conventions (`CacheKeys`, `UserKeys`, `RateLimitKeys`, `QueueKeys`)
- **`models/`** — SQLAlchemy ORM models: `User`, `ApiKey`. Base provides UTC `utc_now()`.
- **`api/`** — Route handlers:
  - `auth/` — Login, register, wallet login, TOTP, API keys, profile
  - `websocket/` — WebSocket with ConnectionManager (broadcast/personal)
  - `common/` — Health check, docs
- **`services/`** — Business logic (`AuthService`, `ApiKeyService`).
- **`repositories/`** — Database queries (`UserRepository`, `ApiKeyRepository`).
- **`scheduler/`** — APScheduler integration. `BaseJob` abstract with cron/interval triggers.
- **`queue/`** — Redis Streams consumers with XREADGROUP, auto-retry, dead-letter queue.
- **`schemas/`** — Pydantic request/response models.
- **`utils/`** — Snowflake ID generator, timezone helpers.
- **`migrations/`** — Raw SQL migration files (`001_init.sql`: users + api_keys).

### Key Patterns

- **Async-first**: All I/O (database, Redis) is async.
- **Dependency injection**: FastAPI `Depends()` for DB sessions, auth, services.
- **Google JSON response style**: Success returns data directly; errors return `{ error: { code, message } }`.
- **Flexible auth**: Routes accept JWT cookie OR API key header via `get_current_user` dependency.
- **Multi-tenancy**: All models scoped by `user_id`.

## Code Style

- **Ruff config** lives in `ruff.toml`. Line length 120. Interpreter is 3.14; ruff `target-version` is pinned to `py313` (see comment in `ruff.toml`) to avoid PEP 649 false positives that conflict with FastAPI runtime annotations.
- **Lint rules**: E, W, F, I, B, C4, UP, SIM, TCH, RUF. `B008` ignored for FastAPI `Depends()`.
- **Imports**: isort with `app` as known first-party.
- **Models**: `TC003` ignored in `app/models/` for SQLAlchemy `Mapped[]` type hints.

## Environment

The `.env` file lives in the repo root. See `.env.example`. Key variables:

```
SECRET_KEY      — JWT signing
DB_*            — PostgreSQL (asyncpg)
REDIS_*         — Redis connection
TOTP_*          — TOTP encryption
CORS_ORIGINS    — allowed origins
```

Requires Python 3.14+ and uv.
