"""登录模块测试用例"""
import pytest
from pages.login_page import LoginPage
from pages.home_page import HomePage


class TestLogin:
    """登录功能测试"""

    def test_login_empty_account(self, driver):
        """异常登录 - 账号为空"""
        login_page = LoginPage(driver)
        error_message = login_page.login("", "123456", expect_success=False)
        assert error_message, "空账号登录应有错误提示"
        # 可以根据实际错误消息进行更具体的断言
        # assert "required" in error_message.lower() or "empty" in error_message.lower()

    def test_login_wrong_password(self, driver):
        """异常登录 - 密码错误"""
        login_page = LoginPage(driver)
        error_message = login_page.login("kyg01@bccto.cc", "123456", expect_success=False)
        assert error_message, "错误密码登录应有错误提示"
        # 可以根据实际错误消息进行更具体的断言
        # assert "incorrect" in error_message.lower() or "invalid" in error_message.lower()

    def test_go_register(self, driver):
        """跳转注册页面"""
        login_page = LoginPage(driver)
        login_page.go_register()
        # TODO: 验证跳转到注册页
    def test_login_success(self, driver):
        """正常登录 - 正确账号密码"""
        login_page = LoginPage(driver)
        
        # 登录并获取首页对象
        home_page = login_page.login("kyg01@bccto.cc", "111111")
        assert home_page.is_home_displayed(), "登录后应跳转到首页"

    def test_smart_login_already_logged_in(self, driver):
        """智能登录 - 已登录状态"""
        login_page = LoginPage(driver)
        
        # 先确保用户已登录
        home_page = login_page.login("kyg01@bccto.cc", "111111")
        assert home_page.is_home_displayed(), "首次登录后应跳转到首页"
        
        # 再次调用smart_login，应该直接返回首页（不重新登录）
        home_page2 = login_page.smart_login("kyg01@bccto.cc", "111111")
        assert home_page2.is_home_displayed(), "已登录状态下应直接返回首页"




