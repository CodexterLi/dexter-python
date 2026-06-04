"""
钱包签名验证模块

支持 EVM 兼容钱包 (MetaMask 等) 的签名验证。
使用 eth_account 进行 EIP-191 签名恢复。
"""

import secrets

from eth_account.messages import encode_defunct
from web3 import Web3


def generate_nonce() -> str:
    """生成 32 字节随机 nonce"""
    return secrets.token_hex(32)


def build_sign_message(nonce: str) -> str:
    """构造待签名消息"""
    return f"Sign this message to login: {nonce}"


def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """
    验证钱包签名

    Args:
        wallet_address: 期望的钱包地址
        message: 签名的原始消息
        signature: 签名的十六进制字符串

    Returns:
        签名是否有效
    """
    try:
        w3 = Web3()
        msg = encode_defunct(text=message)
        recovered = w3.eth.account.recover_message(msg, signature=signature)
        return recovered.lower() == wallet_address.lower()
    except Exception:
        return False
