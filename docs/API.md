# Drexor API 文档

**Base URL**: `http://localhost:8000`

**在线文档**: 
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 认证方式

所有需要认证的接口支持两种方式：

1. **Cookie** (推荐浏览器使用) - 登录后自动设置 HTTP-Only Cookie
2. **Bearer Token** - `Authorization: Bearer <token>`

---

## 认证接口

### 登录

```
POST /api/auth/login
```

**请求体**

```json
{
  "username": "admin",
  "password": "password123",
  "totpCode": "123456"  // 可选，启用两步验证时必填
}
```

**成功响应** `200 OK`

```json
{
  "tokenType": "bearer",
  "expiresIn": 1800
}
```

> 登录成功后会自动设置 `access_token` 和 `refresh_token` Cookie

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 400 | 需要 TOTP 验证码 |
| 401 | 用户名或密码错误 |

---

### 刷新令牌

```
POST /api/auth/refresh
```

**认证**: 需要有效的 `refresh_token` Cookie

**成功响应** `200 OK`

```json
{
  "tokenType": "bearer",
  "expiresIn": 1800
}
```

---

### 登出

```
POST /api/auth/logout
```

**认证**: 🔒 需要登录

**成功响应** `204 No Content`

---

### 注册用户

```
POST /api/auth/register
```

**认证**: 🔒 需要管理员权限

**请求体**

```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123"
}
```

**字段验证**

| 字段 | 规则 |
|------|------|
| username | 3-50 字符 |
| email | 有效邮箱格式 |
| password | 至少 8 字符 |

**成功响应** `201 Created`

```json
{
  "id": 2,
  "username": "newuser",
  "email": "user@example.com",
  "isActive": true,
  "isSuperuser": false,
  "totpEnabled": false,
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 400 | 用户名或邮箱已存在 |
| 403 | 权限不足 |

---

### 获取当前用户

```
GET /api/auth/me
```

**认证**: 🔒 需要登录

**成功响应** `200 OK`

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "isActive": true,
  "isSuperuser": true,
  "totpEnabled": false,
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```

---

## TOTP 两步验证

### 设置 TOTP

```
POST /api/auth/totp/setup
```

**认证**: 🔒 需要登录

**成功响应** `200 OK`

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "uri": "otpauth://totp/Drexor:admin?secret=JBSWY3DPEHPK3PXP&issuer=Drexor"
}
```

> `uri` 可用于生成二维码，使用 Google Authenticator 扫描

---

### 验证并启用 TOTP

```
POST /api/auth/totp/verify
```

**认证**: 🔒 需要登录

**请求体**

```json
{
  "totpCode": "123456"
}
```

**成功响应** `200 OK`

```json
{
  "id": 1,
  "username": "admin",
  "totpEnabled": true,
  ...
}
```

---

### 禁用 TOTP

```
POST /api/auth/totp/disable
```

**认证**: 🔒 需要登录

**成功响应** `200 OK`

```json
{
  "id": 1,
  "username": "admin",
  "totpEnabled": false,
  ...
}
```

---

## WebSocket

### 基础连接

```
WS /ws
```

**连接成功消息**

```json
{
  "type": "welcome",
  "message": "欢迎连接 WebSocket 服务！",
  "connectionCount": 1
}
```

**消息类型**

| 发送 | 接收 | 说明 |
|------|------|------|
| `{"type": "ping"}` | `{"type": "pong"}` | 心跳检测 |
| `{"type": "message", "content": "hello"}` | `{"type": "echo", "content": "hello"}` | 消息回显 |

---

### 广播连接

```
WS /ws/broadcast
```

**消息类型**

| 发送 | 接收 | 说明 |
|------|------|------|
| `{"type": "ping"}` | `{"type": "pong"}` | 心跳检测 |
| `{"type": "message", "content": "hello"}` | `{"type": "broadcast", "content": "hello"}` | 广播给所有连接 |

---

## 错误响应格式

所有错误返回统一格式：

```json
{
  "error": {
    "code": 400,
    "message": "错误描述",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

---

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 成功，无返回内容 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

