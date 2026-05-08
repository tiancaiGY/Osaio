"""登录页面"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class LoginPage(BasePage):
    # 元素定位 - 根据实际页面调整
    # 从测试输出看，元素没有ID，需要用文本或其他方式定位

    ACCOUNT_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Email\")")
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Password\")")
    LOGIN_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Sign In\").instance(1)")
    REGISTER_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Sign Up\")")
    FORGOT_PWD_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Keep me signed in\")")
    ACCOUNT_CLEAR = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.view.ViewGroup\").instance(16)")

    def login(self, account, password):
        self.input_text(*self.ACCOUNT_INPUT, account)
        self.input_text(*self.PASSWORD_INPUT, password)
        self.click(*self.LOGIN_BTN)
    
    def go_register(self):
        self.click(*self.REGISTER_LINK)

    def go_forgot_password(self):
        self.click(*self.FORGOT_PWD_LINK)
