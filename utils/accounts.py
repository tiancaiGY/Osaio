"""测试账号加载器

集中管理所有测试/脚本用到的账号密码，代码里不再硬编码。

来源优先级（从低到高）：
1. config/accounts.yaml 中的默认值；
2. 环境变量覆盖：
   - OSAIO_<KEY>_ACCOUNT / OSAIO_<KEY>_PASSWORD   覆盖具名账号（KEY 形如 PRIMARY、SWITCH_A）
   - OSAIO_WRONG_PASSWORD                          覆盖错误密码
   - OSAIO_REGISTER_DEFAULT_PASSWORD              覆盖注册脚本默认密码

用法：
    from utils.accounts import get_account, get_wrong_password
    acc = get_account("primary")        # -> Account(account=..., password=...)
    login_page.login(acc.account, acc.password)
"""
import os
from pathlib import Path
from collections import namedtuple

import yaml

Account = namedtuple("Account", ["account", "password"])

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "accounts.yaml"
_cache = None


def _load_yaml():
    global _cache
    if _cache is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _cache = yaml.safe_load(f) or {}
    return _cache


def get_account(key):
    """按名字获取账号（primary / secondary / switch_a / switch_b ...）。

    环境变量 OSAIO_<KEY>_ACCOUNT / OSAIO_<KEY>_PASSWORD 优先。
    """
    data = _load_yaml().get("accounts", {})
    entry = data.get(key, {}) or {}
    env_key = key.upper()
    account = os.environ.get(f"OSAIO_{env_key}_ACCOUNT", entry.get("account", ""))
    password = os.environ.get(f"OSAIO_{env_key}_PASSWORD", entry.get("password", ""))
    return Account(account=account, password=password)


def get_all_accounts():
    """返回所有具名账号 {key: Account}（含环境变量覆盖）。"""
    data = _load_yaml().get("accounts", {})
    return {key: get_account(key) for key in data}


def get_wrong_password():
    """错误密码用例使用的密码。"""
    return os.environ.get("OSAIO_WRONG_PASSWORD", _load_yaml().get("wrong_password", "wrongpassword"))


def get_register_default_password():
    """注册脚本默认密码。"""
    return os.environ.get(
        "OSAIO_REGISTER_DEFAULT_PASSWORD",
        _load_yaml().get("register_default_password", "123456"),
    )
