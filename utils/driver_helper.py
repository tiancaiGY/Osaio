"""Appium Driver 管理工具"""
import yaml
from pathlib import Path
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "caps.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_driver(platform="android"):
    """创建 Appium driver 实例"""
    config = load_config()
    server = config["appium_server"]
    caps = config[platform]

    url = f"http://{server['host']}:{server['port']}/wd/hub"

    # 根据平台创建 options
    if platform == "android":
        options = UiAutomator2Options().load_capabilities(caps)
    else:
        options = XCUITestOptions().load_capabilities(caps)
    
    driver = webdriver.Remote(url, options=options)
    driver.implicitly_wait(10)

    # 确保被测 App 在前台：无线调试/复用会话时，建会话后有时会停在系统桌面
    # （launcher），导致后续页面操作都作用在错误界面上。这里显式把 App 激活到前台。
    if platform == "android":
        pkg = caps.get("appPackage") or caps.get("appium:appPackage")
        if pkg:
            try:
                import time
                if driver.query_app_state(pkg) < 4:  # 4 = 前台运行
                    driver.activate_app(pkg)
                    time.sleep(3)
            except Exception:
                pass
    return driver
