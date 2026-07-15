"""pytest 全局 fixture 配置"""
import sys


def _force_utf8_output():
    """修复 Windows 控制台 / 重定向日志中的中文乱码：强制 stdout/stderr 使用 UTF-8。

    - reconfigure：让 Python 以 UTF-8 编码写出（覆盖 GBK/cp936 默认值）。
    - SetConsoleOutputCP(65001)：把 Windows 控制台代码页切到 UTF-8。
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass


_force_utf8_output()

import pytest
from utils.driver_helper import create_driver
from utils.accounts import (
    get_account,
    get_all_accounts,
    get_wrong_password,
    get_register_default_password,
)


def pytest_addoption(parser):
    parser.addoption(
        "--platform", action="store", default="android",
        help="测试平台: android 或 ios"
    )


@pytest.fixture(scope="session")
def accounts():
    """所有具名测试账号 {key: Account(account, password)}（支持环境变量覆盖）。"""
    return get_all_accounts()


@pytest.fixture(scope="session")
def account():
    """按名字取账号的工厂：account("primary") -> Account(account, password)。"""
    return get_account


@pytest.fixture(scope="session")
def wrong_password():
    """错误密码用例使用的密码。"""
    return get_wrong_password()


@pytest.fixture(scope="session")
def register_default_password():
    """注册脚本/用例默认密码。"""
    return get_register_default_password()


@pytest.fixture(scope="session")
def driver(request):
    """创建并管理 Appium driver 生命周期"""
    platform = request.config.getoption("--platform")
    d = create_driver(platform)
    yield d
    d.quit()


@pytest.fixture(autouse=True)
def test_setup(driver):
    """每个测试用例前后的处理"""
    yield
    # 测试结束后可以做清理，比如回到首页
