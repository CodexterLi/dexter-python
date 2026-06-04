-- =====================================================
-- 001: 初始化 - 用户表 + API Key 表
-- =====================================================

-- =====================================================
-- 用户表 (密码登录 + 钱包登录)
-- =====================================================

CREATE TABLE IF NOT EXISTS "public"."users" (
    "id" BIGSERIAL PRIMARY KEY,                             -- 自增主键
    "username" VARCHAR(50) NOT NULL UNIQUE,                  -- 用户名
    "email" VARCHAR(255) NOT NULL UNIQUE,                    -- 邮箱
    "wallet_address" VARCHAR(42) UNIQUE,                     -- 钱包地址 (EVM, 小写, 可为空)
    "hashed_password" VARCHAR(255),                          -- 密码哈希 (钱包用户可为空)
    "is_active" BOOLEAN NOT NULL DEFAULT true,               -- 是否激活
    "is_superuser" BOOLEAN NOT NULL DEFAULT false,           -- 是否超级管理员
    "totp_secret" VARCHAR(255),                              -- TOTP 密钥 (加密存储)
    "totp_enabled" BOOLEAN NOT NULL DEFAULT false,           -- 是否启用两步验证
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "last_login_at" TIMESTAMPTZ
);

-- 索引
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email ON users (email);
CREATE UNIQUE INDEX idx_users_wallet_address ON users (wallet_address) WHERE wallet_address IS NOT NULL;

-- 触发器: 自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 注释
COMMENT ON TABLE public.users IS '用户核心表 - 密码登录 + 钱包登录';
COMMENT ON COLUMN public.users.id IS '主键 (自增)';
COMMENT ON COLUMN public.users.username IS '用户名';
COMMENT ON COLUMN public.users.email IS '邮箱';
COMMENT ON COLUMN public.users.wallet_address IS '钱包地址 (EVM, 小写)';
COMMENT ON COLUMN public.users.hashed_password IS '密码哈希 (钱包用户可为空)';
COMMENT ON COLUMN public.users.is_active IS '是否激活';
COMMENT ON COLUMN public.users.is_superuser IS '是否超级管理员';
COMMENT ON COLUMN public.users.totp_secret IS 'TOTP 密钥 (加密存储)';
COMMENT ON COLUMN public.users.totp_enabled IS '是否启用两步验证';

-- =====================================================
-- API Key 表
-- =====================================================

CREATE TABLE IF NOT EXISTS "public"."api_keys" (
    "id" BIGSERIAL PRIMARY KEY,                                               -- 自增主键
    "user_id" BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,         -- 所属用户
    "name" VARCHAR(50) NOT NULL,                                              -- 密钥名称
    "key" VARCHAR(64) NOT NULL UNIQUE,                                        -- API Key (dk_ 前缀)
    "secret_hash" VARCHAR(255) NOT NULL,                                      -- API Secret bcrypt 哈希
    "is_active" BOOLEAN NOT NULL DEFAULT true,                                -- 是否启用
    "expires_at" TIMESTAMPTZ,                                                 -- 过期时间, NULL=永不过期
    "last_used_at" TIMESTAMPTZ,                                               -- 最后使用时间
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_api_keys_key ON api_keys (key) WHERE is_active = true;
CREATE INDEX idx_api_keys_user_id ON api_keys (user_id);

-- 触发器
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 注释
COMMENT ON TABLE public.api_keys IS 'API Key 表 - 程序化 API 访问凭据';
COMMENT ON COLUMN public.api_keys.id IS '主键 (自增)';
COMMENT ON COLUMN public.api_keys.user_id IS '所属用户';
COMMENT ON COLUMN public.api_keys.name IS '密钥名称 (用户自定义)';
COMMENT ON COLUMN public.api_keys.key IS 'API Key (dk_ 前缀)';
COMMENT ON COLUMN public.api_keys.secret_hash IS 'API Secret 的 bcrypt 哈希';
COMMENT ON COLUMN public.api_keys.is_active IS '是否启用';
COMMENT ON COLUMN public.api_keys.expires_at IS '过期时间';
COMMENT ON COLUMN public.api_keys.last_used_at IS '最后使用时间';
