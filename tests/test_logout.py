import pytest
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.account_page import AccountPage


def test_logout_flow(driver):
    """从首页进入账户并退出登录，验证回到登录页"""
    print("开始 logout 流程")
    home = HomePage(driver)
    # 确认在首页
    print("检查是否在首页")
    if not home.is_home_displayed():
        print("检测不到首页元素，仍尝试跳转到账户页")

    print("开始执行 logout()")
    account = AccountPage(driver)
    ok = account.logout()
    print(f"logout() 返回: {ok}")
    assert ok, "logout() 方法应返回 True 表示已登出"

    # 验证回到登录页
    login = LoginPage(driver)
    print("等待登录页面出现")
    assert login.is_displayed(*login.LOGIN_BTN, timeout=10), "应回到登录页面（登录按钮可见）"
    print("已返回登录页")