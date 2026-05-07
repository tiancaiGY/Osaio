"""pytest 全局 fixture 配置"""
import pytest
from utils.driver_helper import create_driver


def pytest_addoption(parser):
    parser.addoption(
        "--platform", action="store", default="android",
        help="测试平台: android 或 ios"
    )


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
