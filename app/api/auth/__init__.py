"""
认证模块

按功能拆分：
- login.py: 登录、登出、刷新令牌
- register.py: 用户注册
- totp.py: TOTP 两步验证
- profile.py: 用户信息
- wallet.py: 钱包登录
- api_keys.py: API Key 管理
- dependencies.py: 依赖注入
"""

from fastapi import APIRouter

from . import api_keys, login, profile, register, totp, wallet

# 创建认证路由器
router = APIRouter()

# 包含所有子路由
router.include_router(login.router)
router.include_router(register.router)
router.include_router(totp.router)
router.include_router(profile.router)
router.include_router(wallet.router)
router.include_router(api_keys.router)
