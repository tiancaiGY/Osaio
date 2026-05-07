"""登录页面"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class LoginPage(BasePage):
    # 元素定位 - 需要用 Appium Inspector 确认实际 ID
    ACCOUNT_INPUT = (AppiumBy.ID, "fda2ab72-e362-4002-9ae2-6b3dc8f43fb2")
    PASSWORD_INPUT = (AppiumBy.ID, "0d096194-a5bb-4b14-a115-a8256b3218bc")
    LOGIN_BTN = (AppiumBy.ID, "20085f8e-a727-420d-bc99-4fa489be14de")
    REGISTER_LINK = (AppiumBy.ID, "192a682b-c5e4-47e2-80de-7c1fb9e901ca")
    FORGOT_PWD_LINK = (AppiumBy.ID, "c0fb6bff-6133-4059-9c9e-e8b26911d098")

    def login(self, account, password):
        self.input_text(*self.ACCOUNT_INPUT, account)
        self.input_text(*self.PASSWORD_INPUT, password)
        self.click(*self.LOGIN_BTN)
    
    def go_register(self):
        self.click(*self.REGISTER_LINK)

    def go_forgot_password(self):
        self.click(*self.FORGOT_PWD_LINK)
