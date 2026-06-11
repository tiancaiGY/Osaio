"""首页"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class HomePage(BasePage):
    # 元素定位 - 需要用 Appium Inspector 确认实际 ID
    ADD_DEVICE_BTN = (AppiumBy.ACCESSIBILITY_ID, "new UiSelector().className(\"android.view.ViewGroup\").instance(39)")
    DEVICE_LIST = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"All Types\")")
    TAB_HOME = (AppiumBy.ACCESSIBILITY_ID, "Home, tab, 1 of 3")
    TAB_MESSAGE = (AppiumBy.ACCESSIBILITY_ID, "Event, tab, 2 of 3")
    TAB_MINE = (AppiumBy.ID, "com.osaio.app:id/tab_mine")


    def is_home_displayed(self):
        return self.is_displayed(*self.TAB_HOME)

    def click_add_device(self):
        self.click(*self.ADD_DEVICE_BTN)

    def go_account(self):
        from pages.account_page import AccountPage
        account_page = AccountPage(self.driver)
        account_page.go_to_account_tab()
        return account_page

    def go_message(self):
        self.click(*self.TAB_MESSAGE)

    def go_mine(self):
        self.click(*self.TAB_MINE)

    def dismiss_permission_dialogs(self):
        """尝试关闭进入首页后可能弹出的权限或通知弹窗。"""
        # 常见的按钮文本
        candidates = ["不允许", "Deny", "取消", "Cancel", "拒绝"]
        for txt in candidates:
            try:
                if self.tap_text(txt):
                    # small pause
                    from time import sleep
                    sleep(1)
                    return True
            except Exception:
                continue
        return False
