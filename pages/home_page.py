"""首页"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class HomePage(BasePage):
    # 元素定位 - 需要用 Appium Inspector 确认实际 ID
    ADD_DEVICE_BTN = (AppiumBy.ID, "com.osaio.app:id/btn_add_device")
    DEVICE_LIST = (AppiumBy.ID, "com.osaio.app:id/rv_device_list")
    TAB_HOME = (AppiumBy.ID, "com.osaio.app:id/tab_home")
    TAB_MESSAGE = (AppiumBy.ID, "com.osaio.app:id/tab_message")
    TAB_MINE = (AppiumBy.ID, "com.osaio.app:id/tab_mine")

    def is_home_displayed(self):
        return self.is_displayed(*self.TAB_HOME)

    def click_add_device(self):
        self.click(*self.ADD_DEVICE_BTN)

    def go_message(self):
        self.click(*self.TAB_MESSAGE)

    def go_mine(self):
        self.click(*self.TAB_MINE)
