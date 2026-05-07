"""首页模块测试用例"""
import pytest
from pages.home_page import HomePage


class TestHome:
    """首页功能测试"""

    def test_home_display(self, driver):
        """首页正常展示"""
        home_page = HomePage(driver)
        assert home_page.is_home_displayed(), "首页应正常展示"

    def test_add_device_entry(self, driver):
        """添加设备入口"""
        home_page = HomePage(driver)
        home_page.click_add_device()
        # TODO: 验证跳转到配网页面

    def test_switch_to_message(self, driver):
        """切换到消息Tab"""
        home_page = HomePage(driver)
        home_page.go_message()
        # TODO: 验证消息页面展示

    def test_switch_to_mine(self, driver):
        """切换到我的Tab"""
        home_page = HomePage(driver)
        home_page.go_mine()
        # TODO: 验证我的页面展示
