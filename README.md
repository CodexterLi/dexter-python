# Drexor Backend

Drexor 后端 — 用户认证 + 数据库 + Redis + WebSocket 基础设施。

纯基础设施核心后端（无 AI/Agent 运行时）。前端为独立仓库。

## 功能特性

- **用户认证**: 密码登录、钱包登录 (EVM)、JWT、HTTP-Only Cookie、TOTP 两步验证、API Key
- **数据库**: PostgreSQL 异步连接、SQLAlchemy ORM
- **缓存**: Redis 异步连接、Session 缓存、统一 Key 命名规范
- **定时任务**: APScheduler 异步调度
- **队列**: 基于 Redis Streams 的消费者框架（含重试 / DLQ）
- **WebSocket**: 基础连接、消息广播、心跳检测
- **其他**: Loguru 日志、统一异常处理、Google 风格 API 响应、CORS

## 快速开始

### 环境要求

- Python >= 3.14
- PostgreSQL
- Redis

### 安装与运行

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入数据库 / Redis / 密钥等

# 初始化数据库
psql -U postgres -d drexor -f migrations/001_init.sql

# 运行服务
make dev
```

### API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
app/
├── main.py                # 应用入口
├── config/                # 配置管理 (pydantic-settings)
├── core/                  # 核心模块 (异常、日志、安全、响应)
│   └── security/          # 密码、JWT、Cookie、TOTP、钱包验证、API Key
├── db/                    # 数据库连接 (PostgreSQL + Redis) + redis_keys 命名规范
├── models/                # ORM 模型 (User, ApiKey)
├── repositories/          # 数据访问层
├── schemas/               # 请求/响应 Schema
├── services/              # 业务逻辑层 (auth, api_key)
├── scheduler/             # APScheduler 定时任务
├── queue/                 # Redis Streams 消费者框架
├── api/                   # API 路由层 (auth / common / websocket)
└── utils/                 # 工具 (snowflake, timezone)
```

## 主要 API

### Auth (`/api/auth`)

| Method | Path | 说明 |
|--------|------|------|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 密码登录 |
| POST | /api/auth/refresh | 刷新 token |
| POST | /api/auth/logout | 登出 |
| GET  | /api/auth/me | 当前用户 |
| POST | /api/auth/wallet/nonce | 获取钱包签名 nonce |
| POST | /api/auth/wallet/login | 钱包登录 |
| POST | /api/auth/totp/setup | TOTP 初始化 |
| POST | /api/auth/totp/verify | TOTP 校验 |
| POST | /api/auth/totp/disable | 关闭 TOTP |
| POST | /api/auth/api-keys | 创建 API Key |
| GET  | /api/auth/api-keys | 列出 API Key |
| PUT  | /api/auth/api-keys/{id}/revoke | 撤销 API Key |
| DELETE | /api/auth/api-keys/{id} | 删除 API Key |

### Common (`/api/docs`)

| Method | Path | 说明 |
|--------|------|------|
| GET | /api/docs/health | 健康检查 |
| GET | /api/docs/info | 服务信息 |

### WebSocket

| Path | 说明 |
|------|------|
| /ws | WebSocket 连接 |
| /ws/broadcast | 消息广播 |
