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

    def go_message(self):
        self.click(*self.TAB_MESSAGE)

    def go_mine(self):
        self.click(*self.TAB_MINE)
