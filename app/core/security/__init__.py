"""
安全模块

提供密码哈希、JWT令牌、Cookie管理、TOTP两步验证、钱包验证和API Key功能。
"""

from app.core.security.apikey import (
    generate_api_key,
    generate_api_secret,
    hash_secret,
    verify_secret,
)
from app.core.security.cookie import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    clear_auth_cookies,
    set_access_token_cookie,
    set_refresh_token_cookie,
)
from app.core.security.jwt import (
    TokenData,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.security.password import get_password_hash, verify_password
from app.core.security.totp import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
)
from app.core.security.wallet import (
    build_sign_message,
    generate_nonce,
    verify_wallet_signature,
)

__all__ = [
    "ACCESS_TOKEN_COOKIE_NAME",
    "REFRESH_TOKEN_COOKIE_NAME",
    "TokenData",
    "build_sign_message",
    "clear_auth_cookies",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "decrypt_totp_secret",
    "encrypt_totp_secret",
    "generate_api_key",
    "generate_api_secret",
    "generate_nonce",
    "generate_totp_secret",
    "get_password_hash",
    "get_totp_uri",
    "hash_secret",
    "set_access_token_cookie",
    "set_refresh_token_cookie",
    "verify_password",
    "verify_secret",
    "verify_totp",
    "verify_wallet_signature",
]
