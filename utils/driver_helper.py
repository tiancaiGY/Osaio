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

    if platform == "android":
        options = UiAutomator2Options().load_capabilities(caps)
    else:
        options = XCUITestOptions().load_capabilities(caps)

    driver = webdriver.Remote(url, options=options)
    driver.implicitly_wait(10)
    return driver
