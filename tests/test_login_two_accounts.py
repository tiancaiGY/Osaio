"""两个账号登录/退出切换流程测试。"""

from pages.login_page import LoginPage


class TestLoginTwoAccounts:
    def test_switch_accounts(self, driver):
        """登录账号 A，退出，再登录账号 B。"""
        login_page = LoginPage(driver)

        email_a = "testa31@mailto.plus"
        email_b = "testa32@mailto.plus"
        password = "123456"

        home_page_a = login_page.login(email_a, password)
        assert home_page_a.is_home_displayed(), "账号 A 登录后应进入首页"

        account_page = home_page_a.go_account()
        assert account_page.logout(), "退出登录操作应成功"

        assert login_page.is_displayed(*login_page.LOGIN_BTN), "退出后应返回登录页"

        home_page_b = login_page.login(email_b, password)
        assert home_page_b.is_home_displayed(), "账号 B 登录后应进入首页"
