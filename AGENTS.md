# AGENTS.md

本文件用于指导 Codex（Codex.ai/code）在本仓库中工作。

## 项目概览

drexor-python 是 Drexor 的 Python 后端服务，基于 FastAPI 构建，定位为 **基础设施核心后端**，包含 Web3 认证能力。

当前仓库提供：

- 用户认证：JWT、钱包登录、TOTP
- API Key 管理
- PostgreSQL + Redis 基础设施
- APScheduler 定时任务
- Redis Streams 队列框架
- WebSocket 实时通信

本仓库 **不包含 AI/Agent 运行时**。相关能力已在前后端拆分过程中移除；前端位于独立仓库。

技术栈：Python 3.14、FastAPI、SQLAlchemy 2.0 async、asyncpg、Redis、APScheduler、uv。

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `make install` | 使用 `uv sync` 安装依赖 |
| `make dev` | 启动热重载开发服务（http://localhost:8000） |
| `make worker` | 按 `.env` 配置启动后台 worker（scheduler / queue） |
| `make docker-build` | 构建统一运行镜像 |
| `make docker-run-api` | 使用统一镜像运行 API 容器 |
| `make docker-run-worker` | 使用统一镜像运行 worker 容器 |
| `make lint` | Ruff 检查 + 格式检查 |
| `make format` | Ruff 自动修复 + 格式化 |
| `make test` | 运行 pytest |
| `make upgrade` | 升级依赖 |

Lint 和格式化使用 `uvx ruff`，不是 `uv run ruff`；ruff 不是项目运行依赖。

## 架构

```text
Client ──▶ FastAPI API (uvicorn :8000)
               ├── Auth (JWT / Wallet / TOTP / API Key)
               └── WebSocket (broadcast / personal)

Background Worker (`make worker`)
               ├── Scheduler (APScheduler cron/interval jobs)
               └── Queue (Redis Streams consumers, disabled by default)
```

当前主应用采用模块化单体架构：业务代码位于 `app/`，导入前缀为 `app.*`。

仓库已经预留轻量共享包：

- `packages/common`：跨未来服务复用的纯基础设施工具，例如 Snowflake ID、时间工具。
- 未来如需拆独立服务，可新增 `services/<service_name>`，并通过 HTTP/Redis Streams 通信。
- 跨服务契约可放在 `contracts/`，只放 schema、事件 payload、错误码和常量，不放业务逻辑。

## 目录结构

### 主应用：`app/`

- `main.py`：FastAPI 入口。生命周期中初始化/关闭 DB 与 Redis，注册 CORS 和异常处理器。
- `api/`：HTTP/WebSocket 路由。
  - `router.py`：主路由聚合入口。
  - `dependencies.py`：API 层通用依赖，例如当前用户、认证 service、DB session。
  - `auth/`：登录、注册、钱包登录、TOTP、API Key、用户资料。
  - `websocket/`：WebSocket 路由和连接管理。
  - `common/`：健康检查、文档等公共路由。
- `config/`：基于 Pydantic Settings 的配置加载，读取根目录 `.env`。
- `core/`：横切基础能力。
  - `security/`：JWT、bcrypt、TOTP 加密、钱包签名验证、API Key 校验。
  - `responses.py`：Google JSON 风格响应。
  - `exceptions.py`：统一异常层级和异常处理器。
  - `logging.py`：Loguru 日志配置、标准库 logging 桥接、日志轮转。
- `db/`：数据库层。
  - `postgres.py`：异步 SQLAlchemy engine、session factory、`get_db()` 依赖。
  - `redis.py`：异步 Redis 客户端，支持连接池、SSL、ACL。
  - `redis_keys/`：Redis key 命名空间约定。
- `models/`：SQLAlchemy ORM 模型，例如 `User`、`ApiKey`。
- `repositories/`：数据库查询封装。
- `services/`：业务逻辑，例如 `AuthService`、`ApiKeyService`。
- `schemas/`：Pydantic 请求/响应模型。
- `scheduler/`：APScheduler 集成，`BaseJob` 支持 cron/interval trigger。
- `queue/`：Redis Streams 消费框架，支持 XREADGROUP、自动重试、死信队列。
- `utils/`：兼容层。新共享工具应优先放到 `packages/common`。

### 共享包：`packages/`

- `packages/common/snowflake.py`：Snowflake ID 生成器。
- `packages/common/time.py`：UTC 和 UTC+8 时间工具。

`packages/common` 只能放无 FastAPI、无数据库 session、无业务状态的纯工具。不要把业务 service、repository、model 放进去。

### 测试：`tests/`

测试目录统一使用 `tests/`，不要再新增 `test/`。

### 迁移：`migrations/`

当前使用 raw SQL migration 文件，例如 `001_init.sql`。

### 文档库

- `docs/product/`：产品 / 功能文档。
- `docs/architecture/`：系统架构文档。
- `docs/api/`：API 文档。
- `docs/dev-phase/`：开发进度文档。

接口、配置、数据结构、服务边界或模块行为发生变化时，必须同步更新对应文档。

## 关键模式

- **异步优先**：数据库、Redis、HTTP 等 I/O 均使用 async。
- **依赖注入**：FastAPI `Depends()` 用于 DB session、认证和 service 注入。
- **分层边界**：API 层处理 HTTP；Service 层编排业务；Repository 层处理查询。
- **响应风格**：成功直接返回数据；错误返回 `{ "error": { "code", "message" } }`。
- **认证方式**：路由可通过 JWT cookie 或 API key header 获取当前用户。
- **用户隔离**：当前模型主要通过 `user_id` 进行数据归属。

## 分层架构

编写业务代码、创建新文件、重构代码时遵循以下依赖方向：

```text
API / Router          HTTP 参数解析、依赖注入、响应返回
    ↓
Application / UseCase 跨 service、跨领域或多步骤业务编排
    ↓
Service               单领域业务规则
    ↓
Repository            数据访问接口和查询封装
    ↓
Model / Infrastructure SQLAlchemy 模型、DB、Redis、外部服务实现
```

当前简单业务可以保持 `API -> Service -> Repository`。当一个业务流程需要组合 2 个以上 service、外部系统、事务边界、Redis 事件或状态流转时，应新增明确的 Application/UseCase 编排层，例如 `app/services/<domain>/usecase.py` 或 `app/application/<domain>.py`。

| 层 | 允许依赖 | 禁止依赖 |
| --- | --- | --- |
| API / Router | Service、UseCase、Schema、Depends | Repository、SQLAlchemy 查询、Redis 细节 |
| Application / UseCase | 多个 Service、事务管理、事件发布接口 | FastAPI Request/Response、具体 HTTP 细节 |
| Service | Repository、Domain helper、基础组件 | FastAPI DTO、其他领域的 Repository |
| Repository | SQLAlchemy session、Model | HTTP、WebSocket、Redis Streams 副作用 |
| Model / Schema | 类型、字段、校验 | 业务流程、外部 I/O |

禁止事项：

- 不要在 API 路由中直接写 SQLAlchemy 查询。
- 不要在 API 路由中直接串联多个 repository 或外部服务。
- 不要让 service 依赖 FastAPI `Request`、`Response` 或 HTTP-only schema。
- 不要让 repository 发布消息、写缓存、调用 HTTP 或处理 WebSocket。

## Application / UseCase 编排

复杂业务流程必须有清晰编排层，避免 Handler/Router 变成流程脚本。

| 场景 | 推荐处理 |
| --- | --- |
| 单个 service 可完成 | `API -> Service` |
| 需要 2 个以上 service 协作 | `API -> UseCase -> Services` |
| 需要事务保证 | `API -> UseCase + transaction boundary -> Services` |
| 需要聚合多个 I/O 数据源 | `API -> UseCase`，可并发聚合 |
| 需要最终一致性 | `API -> UseCase -> Redis Streams / Domain Event` |

UseCase 命名建议：

- 文件：`<business>_usecase.py`
- 类：`<Business>UseCase`
- 方法：动词开头，描述完整业务动作，例如 `create_order_with_payment`

UseCase 只负责编排，不堆领域规则；领域规则仍放在对应 service 或 domain helper。

## API 和响应规范

HTTP API 优先使用资源导向 URL：

```text
GET    /api/v1/resources
GET    /api/v1/resources/{id}
POST   /api/v1/resources
PUT    /api/v1/resources/{id}
PATCH  /api/v1/resources/{id}
DELETE /api/v1/resources/{id}
```

过滤、排序、分页使用查询参数：

```text
GET /api/v1/resources?status=active&sort=created_at&limit=20&offset=0
```

编写或修改路由时：

- 统一使用 `app.core.responses` 中的响应工具。
- 成功响应直接返回数据对象，不额外包一层 `data`。
- 列表响应使用 `{ "items": [...], "totalCount": n }`。
- 错误响应使用统一格式 `{ "error": { "code", "message" } }`。
- 不要在路由里临时定义自定义响应格式。

## 数据库、缓存和并发

数据库访问：

- 查询逻辑集中在 repository，不要散落在 service 或 API 层。
- 只查询需要的列和关系，避免无意的全量加载。
- 避免 N+1 查询；需要关联数据时优先批量查询并在内存中组装。
- 事务边界应由 UseCase 或明确的 service 方法控制，不要散落在 API 层。
- 数据库错误应映射为稳定业务异常，不要向上泄露底层驱动错误文本。

Redis 和缓存：

- Redis key 前缀集中定义在 `app/db/redis_keys/`。
- 使用 Cache-Aside 时，读取顺序为缓存 -> 数据库 -> 写回缓存；更新数据后删除或刷新缓存。
- 缓存写入失败通常不应阻断主流程，但必须有可观测日志。
- 不要缓存密钥、完整 token、私钥、完整 API key 等敏感明文。

并发与后台任务：

- 并发聚合多个 I/O 结果时使用 `asyncio.TaskGroup` 或等价结构，保证失败时有明确取消和错误处理。
- 后台任务、scheduler job、queue consumer 必须有明确启动、关闭和失败处理路径。
- 不要静默吞掉 task 内异常；至少记录日志或返回到调用方。
- 外部 HTTP、Redis、数据库调用应设置合理超时。

日志和配置：

- 日志字段使用稳定 key，例如 `request_id`、`user_id`、`method`、`path`、`status`、`latency_ms`。
- 对外返回通用错误消息时，内部日志可以记录更详细错误链，但不能泄露敏感信息。
- 新增配置时同步更新 `app/config/settings.py`、`.env.example` 和相关文档。

## 代码风格

- Ruff 配置位于 `ruff.toml`，行宽 120。
- Python 运行版本为 3.14；Ruff `target-version` 固定为 `py313`，避免 PEP 649 相关误判影响 FastAPI 运行时注解。
- 启用规则：E、W、F、I、B、C4、UP、SIM、TCH、RUF。
- 忽略 `B008`，用于兼容 FastAPI `Depends()`。
- isort first-party 包含 `app` 和 `packages`。
- SQLAlchemy 模型中的 `Mapped[]` 需要运行时类型导入，`app/models/` 对 `TC003` 有例外。

| 项目 | 建议限制 | 超出时 |
| --- | --- | --- |
| 函数/方法 | 尽量不超过 50 行 | 拆分私有 helper、service 方法或独立对象 |
| 文件 | 尽量不超过 500 行 | 按职责拆分模块 |
| 行宽 | 120 字符 | 换行或拆分表达式 |
| 参数 | 尽量不超过 5 个 | 使用 Pydantic model、dataclass 或参数对象 |
| 嵌套 | 尽量不超过 4 层 | 早返回、拆 helper |

命名规范：

- 模块和函数使用 `snake_case`。
- 类使用 `PascalCase`。
- 常量使用 `UPPER_SNAKE_CASE`。
- 私有 helper 使用 `_` 前缀。
- 异常类使用明确业务语义，例如 `InvalidApiKeyException`。
- 布尔变量使用 `is_`、`has_`、`can_` 前缀。

## 编码约束

- 每次修改代码后必须运行 `make format` 和 `make lint`；通常先 `make format`，再 `make lint`。如果因为环境问题无法运行，需要在回复中明确说明原因。
- 涉及业务逻辑、接口行为、数据模型、队列、调度或安全认证的改动，必须运行 `make test`；如果测试覆盖不足，应补充针对性测试。
- 单个函数/方法尽量控制在 50 行以内。超过 50 行时，应优先拆分为私有 helper、service 方法或独立对象；只有在事务流程必须连续表达时才允许例外，并保持清晰注释。
- 单个模块不应混合多个层级职责。API 文件不要写数据库查询；repository 不要写 HTTP/Redis 副作用；schema 不要包含业务流程。
- API 层只负责参数解析、依赖注入和响应返回；业务规则放在 service；SQLAlchemy 查询放在 repository。
- 新增公共逻辑前先查现有实现，优先复用本仓库已有模式，不要引入重复工具函数。
- 不为了“未来可能需要”提前创建抽象。只有出现实际复用、边界隔离或复杂度下降时才抽象。
- 复杂业务涉及多个 service、外部系统、状态流转或多步骤事务时，可以引入合适的设计模式提升健壮性，例如 Facade、Strategy、Factory、State Machine、Unit of Work、Domain Event、Saga/Process Manager。
- 使用设计模式必须服务当前复杂度：需要能说明它解决了什么问题，例如隔离变化、减少分支、统一事务边界、降低耦合或提升可测试性。不要为了“看起来架构化”而套模式。
- 跨多个 service 的业务流程应有明确编排层；不要让 API 路由直接串联多个 repository 或外部调用。
- 不要在代码中硬编码环境相关配置、密钥、token、服务地址、数据库/Redis 地址、链 RPC、外部 API endpoint、管理员账号或业务可调参数；应放入 `app/config/settings.py` 并通过 `.env` 注入。
- 对固定协议值、错误码、Redis key 前缀、权限名等确实稳定的常量，应集中定义在对应模块，不要散落在业务流程中。
- 异步代码中不要调用阻塞 I/O；需要外部 HTTP 调用时使用 `httpx.AsyncClient`。
- 错误处理优先使用 `app.core.exceptions` 中的统一异常，不要在业务层随意返回裸 dict 表示错误。
- 日志不得包含密码、JWT、API secret、TOTP secret、私钥、完整 API key 等敏感信息。
- 代码风格要服务可读性：命名清晰、分支扁平、避免深层嵌套，优先早返回；不要为了压行数牺牲语义。

## 注释与文档

注释精简为主，仅在关键位置添加中文注释。

必须注释：

- 复杂业务流程的步骤标注。
- 非显而易见的业务规则。
- 事务边界、重试策略、幂等策略和最终一致性处理。
- 临时方案或技术债务，例如 `TODO:`、`FIXME:`。

禁止注释：

- 不要解释显而易见的代码。
- 不要重复代码本身的描述。
- 不要每行都加注释。

复杂业务可以用步骤编号标注关键节点：

```python
async def create_order_with_payment(self, command: CreateOrderCommand) -> Order:
    # 1. 校验用户和余额
    await self._validate_user(command.user_id)

    # 2. 创建订单并锁定库存
    order = await self._create_order(command)

    # 3. 发起支付流程
    await self._start_payment(order)
    return order
```

## 测试要求

- 测试统一放在 `tests/`，文件命名为 `test_*.py`。
- 对 service 和 repository 的核心分支补测试；API 行为变化至少覆盖成功路径和关键失败路径。
- 修复 bug 时，优先先补一个能复现问题的测试，再修复实现。
- 不要依赖测试执行顺序；涉及时间、ID、Redis、数据库的测试应显式隔离状态。
- 测试命名建议：`test_<function>_<scenario>`，例如 `test_get_by_id_not_found`。
- 测试结构遵循 AAA：Arrange、Act、Assert。
- 不要进行真实外部调用；外部 HTTP、链 RPC、邮件、支付等必须 mock、fake 或通过本地测试替身。
- 不要使用 `time.sleep()` 等待异步流程；应使用可控事件、mock 时间或轮询带超时。

## 环境变量

`.env` 位于仓库根目录，参考 `.env.example`。

关键配置：

```text
SECRET_KEY      — JWT 签名密钥
DB_*            — PostgreSQL asyncpg 连接配置
REDIS_*         — Redis 连接配置
TOTP_*          — TOTP 加密配置
CORS_ORIGINS    — 允许的跨域来源
```

要求 Python 3.14+ 和 uv。

## 开发约定

- 新增共享工具时优先放入 `packages/common`，并视情况在 `app/utils` 保留兼容 wrapper。
- 新增测试放入 `tests/`。
- 不要把未来独立 service 的代码直接 import 到 `app` 中；服务间同步调用优先 HTTP，异步事件优先 Redis Streams。
- 不要使用共享数据库作为服务间通信方式；独立服务应有明确表权限和边界。
- 修改架构说明、命令、目录或服务边界时，同步更新 `AGENTS.md` 和 `CLAUDE.md`。
