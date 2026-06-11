"""页面基类 - 封装通用操作"""
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    def find(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def find_visible(self, by, value):
        return self.wait.until(EC.visibility_of_element_located((by, value)))

    def click(self, by, value):
        self.find_visible(by, value).click()

    def tap_text(self, text, exact=False):
        """点击文本元素，按包含文本查找，返回是否成功。"""
        selector = f'new UiSelector().text("{text}")' if exact else f'new UiSelector().textContains("{text}")'
        try:
            self.click(AppiumBy.ANDROID_UIAUTOMATOR, selector)
            return True
        except Exception:
            return False

    def input_text(self, by, value, text):
        el = self.find(by, value)
        el.clear()
        el.send_keys(text)

    def is_displayed(self, by, value, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except Exception:
            return False

    def swipe_up(self):
        size = self.driver.get_window_size()
        x = size["width"] // 2
        self.driver.swipe(x, size["height"] * 0.8, x, size["height"] * 0.2, 800)

    def back(self):
        self.driver.back()

    def screenshot(self, name="screenshot"):
        self.driver.save_screenshot(f"reports/{name}.png")
