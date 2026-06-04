"""
TOTP 两步验证模块
"""

import base64

import pyotp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config.settings import settings
from app.core.logging import logger


def _get_encryption_key() -> bytes:
    """从 SECRET_KEY 派生 Fernet 加密密钥"""
    salt = settings.TOTP_ENCRYPTION_SALT.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))


def encrypt_totp_secret(secret: str) -> str:
    """加密 TOTP secret"""
    try:
        f = Fernet(_get_encryption_key())
        encrypted = f.encrypt(secret.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"加密 TOTP secret 失败: {e}")
        raise


def decrypt_totp_secret(encrypted_secret: str) -> str:
    """解密 TOTP secret"""
    try:
        f = Fernet(_get_encryption_key())
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_secret.encode())
        return f.decrypt(encrypted_bytes).decode()
    except Exception as e:
        logger.error(f"解密 TOTP secret 失败: {e}")
        raise


def generate_totp_secret() -> str:
    """生成 TOTP 密钥"""
    return pyotp.random_base32()


def verify_totp(secret: str, token: str) -> bool:
    """验证 TOTP 令牌"""
    try:
        # 尝试解密，失败则视为明文（向后兼容）
        try:
            decrypted = decrypt_totp_secret(secret)
        except Exception:
            decrypted = secret

        return pyotp.TOTP(decrypted).verify(token)
    except Exception as e:
        logger.error(f"验证 TOTP 失败: {e}")
        return False


def get_totp_uri(secret: str, username: str) -> str:
    """获取 TOTP URI (用于生成二维码)"""
    return pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name=settings.TOTP_ISSUER)
