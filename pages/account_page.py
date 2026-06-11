from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class AccountPage(BasePage):
    ACCOUNT_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("3 of 3")')
    PROFILE_AREA = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("账户").textContains("Account")')
    LOGOUT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("退出登录").textContains("Log Out").textContains("Logout")')
    CONFIRM_LOGOUT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("确定").textContains("Logout").textContains("Exit")')
    DENY_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("不允许").textContains("Deny").textContains("Cancel")')

    def go_to_account_tab(self):
        """跳转到账户标签页。"""
        self.click(*self.ACCOUNT_TAB)
        return self

    def dismiss_system_dialogs(self):
        """尝试关闭常见系统权限弹窗。"""
        for text in ["不允许", "Deny", "Cancel"]:
            if self.tap_text(text):
                return True
        return False

    def open_profile(self):
        """尝试打开个人资料区域。"""
        if self.tap_text("账户") or self.tap_text("Account"):
            return True
        try:
            self.click(*self.PROFILE_AREA)
            return True
        except Exception:
            return False

    def logout(self):
        """执行退出登录操作。"""
        self.go_to_account_tab()
        self.dismiss_system_dialogs()

        # 尝试先打开个人资料区域，再执行退出
        if not self.open_profile():
            # 失败时继续查找退出按钮
            pass

        if self.tap_text("退出登录") or self.tap_text("Log Out") or self.tap_text("Logout"):
            self.wait.until(lambda d: self.is_displayed(*self.CONFIRM_LOGOUT_BUTTON))
            self.tap_text("确定")
            self.tap_text("Logout")
            self.tap_text("Exit")
            return True

        return False
