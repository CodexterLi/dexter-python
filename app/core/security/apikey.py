"""
API Key 生成与验证模块
"""

import secrets

import bcrypt

KEY_PREFIX = "dk_"  # dexter key
KEY_BYTES = 20  # 40 字符 hex
SECRET_BYTES = 32  # 64 字符 hex


def generate_api_key() -> str:
    """生成 API Key (前缀 + 随机 hex)"""
    return KEY_PREFIX + secrets.token_hex(KEY_BYTES)


def generate_api_secret() -> str:
    """生成 API Secret (随机 hex)"""
    return secrets.token_hex(SECRET_BYTES)


def hash_secret(secret: str) -> str:
    """哈希 API Secret"""
    return bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    """验证 API Secret"""
    try:
        return bcrypt.checkpw(plain_secret.encode(), hashed_secret.encode())
    except Exception:
        return False
