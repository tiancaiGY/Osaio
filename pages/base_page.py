"""页面基类 - 封装通用操作"""
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        # Allow shorter waits for quicker test iterations when SHORT_WAIT=1
        wait_time = 5 if os.environ.get("SHORT_WAIT") == "1" else 15
        self.wait = WebDriverWait(driver, wait_time)

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

    def app_package(self):
        """获取被测应用包名（优先取会话 capabilities，失败则取当前前台包名）。"""
        pkg = None
        try:
            caps = self.driver.capabilities or {}
            pkg = caps.get("appPackage") or caps.get("appium:appPackage")
        except Exception:
            pkg = None
        if not pkg:
            pkg = getattr(self.driver, "current_package", None)
        return pkg

    def restart_app(self, wait=3):
        """终止并重新启动被测应用，把 App 复位到初始界面。

        用于登录流程中把不确定的界面状态（子页/弹窗/半渲染的 RN 页面）复位，
        比连续 back() 更确定。返回是否成功重新拉起。
        """
        import time

        pkg = self.app_package()
        if not pkg:
            print("无法获取 appPackage，跳过重启 App")
            return False
        try:
            self.driver.terminate_app(pkg)
        except Exception as e:
            print(f"终止 App 失败（忽略并继续）: {e}")
        try:
            self.driver.activate_app(pkg)
        except Exception as e:
            print(f"重新启动 App 失败: {e}")
            return False
        time.sleep(wait)
        print(f"已重启 App: {pkg}")
        return True
