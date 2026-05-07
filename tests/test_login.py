"""登录模块测试用例"""
import pytest
from pages.login_page import LoginPage
from pages.home_page import HomePage


class TestLogin:
    """登录功能测试"""

    def test_login_success(self, driver):
        """正常登录 - 正确账号密码"""
        login_page = LoginPage(driver)
        home_page = HomePage(driver)

        login_page.login("kyg01@bccto.cc", "123456")
        assert home_page.is_home_displayed(), "登录后应跳转到首页"

    def test_login_empty_account(self, driver):
        """异常登录 - 账号为空"""
        login_page = LoginPage(driver)
        login_page.login("", "123456")
        # TODO: 验证错误提示

    def test_login_wrong_password(self, driver):
        """异常登录 - 密码错误"""
        login_page = LoginPage(driver)
        login_page.login("kyg01@bccto.cc", "1111111")
        # TODO: 验证错误提示

    def test_go_register(self, driver):
        """跳转注册页面"""
        login_page = LoginPage(driver)
        login_page.go_register()
        # TODO: 验证跳转到注册页
