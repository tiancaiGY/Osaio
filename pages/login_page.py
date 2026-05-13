"""登录页面"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class LoginPage(BasePage):
    # 元素定位 - 根据实际页面调整
    # 从测试输出看，元素没有ID，需要用文本或其他方式定位

    # 登录页面元素 - 使用更可靠的定位方式
    # 账号输入框：使用resource-id或class name + 索引
    ACCOUNT_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(0)")
    # 或者使用：ACCOUNT_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@text, '@') or @hint='Email']")
    
    # 密码输入框
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(1)")
    # 或者使用：PASSWORD_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[@password='true' or @hint='Password']")
    
    LOGIN_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Sign In\").instance(1)")
    REGISTER_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Sign Up\")")
    FORGOT_PWD_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Keep me signed in\")")
    
    # 清除按钮（通常在输入框右侧）
    ACCOUNT_CLEAR_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.view.ViewGroup\").instance(16)")
    # 密码可见按钮
    PASSWORD_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.view.ViewGroup\").instance(19)")
    
    # 首页元素（用于检查是否已登录）
    TAB_HOME = (AppiumBy.ACCESSIBILITY_ID, "Home, tab, 1 of 3")
    TAB_Event = (AppiumBy.ACCESSIBILITY_ID, "Home, tab, 2 of 3")
    TAB_Account = (AppiumBy.ACCESSIBILITY_ID, "Home, tab, 3 of 3")

    # 错误提示元素
    ERROR_MESSAGE = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"error\").textContains(\"Error\").textContains(\"incorrect\").textContains(\"Invalid\")")
    EMPTY_ACCOUNT_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"The mailbox is not registered\")")
    EMPTY_PASSWORD_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Incorrect password\")")

    # 注册元素（用于检查是否在注册页）


    def is_already_logged_in(self):
        """检查是否已经登录"""
        from pages.home_page import HomePage
        home_page = HomePage(self.driver)
        
        # 检查是否在登录页面（通过登录按钮是否存在）
        try:
            is_on_login_page = self.is_displayed(*self.LOGIN_BTN, timeout=3)
        except Exception:
            is_on_login_page = False
        
        # 如果登录按钮可见，说明在登录页面，用户未登录
        if is_on_login_page:
            return False
        
        # 检查是否在首页或其他已登录页面
        try:
            # 检查首页元素是否可见
            return home_page.is_home_displayed()
        except Exception:
            # 检查其他已登录状态的元素
            return self.is_displayed(*self.TAB_Event) or \
                   self.is_displayed(*self.TAB_Account) or \
                   self.is_displayed(*self.TAB_HOME)

    def login(self, account, password, expect_success=True):
        """
        登录方法
        :param account: 账号
        :param password: 密码
        :param expect_success: 是否期望登录成功，默认为True
        :return: 如果expect_success为True，返回HomePage对象；如果为False，返回错误消息文本
        """
        # 先检查是否已经登录
        if self.is_already_logged_in():
            print("用户已登录，直接返回首页")
            from pages.home_page import HomePage
            return HomePage(self.driver)
        
        # 如果未登录，执行正常登录流程（使用智能输入方法）
        self.smart_input_account(account)
        self.smart_input_password(password)
        self.click(*self.LOGIN_BTN)
        
        if expect_success:
            # 等待登录完成，返回首页对象
            from pages.home_page import HomePage
            home_page = HomePage(self.driver)
            # 等待首页元素出现
            home_page.wait.until(lambda d: home_page.is_home_displayed())
            return home_page
        else:
            # 等待错误提示出现
            self.wait.until(lambda d: self.is_error_displayed())
            return self.get_error_message()

    def is_error_displayed(self):
        """检查是否有错误提示"""
        return self.is_displayed(*self.ERROR_MESSAGE) or \
               self.is_displayed(*self.EMPTY_ACCOUNT_ERROR) or \
               self.is_displayed(*self.EMPTY_PASSWORD_ERROR)

    def get_error_message(self):
        """获取错误提示文本"""
        # 尝试获取不同类型的错误提示
        if self.is_displayed(*self.ERROR_MESSAGE, timeout=2):
            return self.find(*self.ERROR_MESSAGE).text
        elif self.is_displayed(*self.EMPTY_ACCOUNT_ERROR, timeout=2):
            return self.find(*self.EMPTY_ACCOUNT_ERROR).text
        elif self.is_displayed(*self.EMPTY_PASSWORD_ERROR, timeout=2):
            return self.find(*self.EMPTY_PASSWORD_ERROR).text
        return "未知错误"

    def go_register(self):
        """跳转到注册页面并返回注册页面对象"""
        self.click(*self.REGISTER_LINK)
        
        # 等待注册页面加载
        from pages.register_page import RegisterPage
        register_page = RegisterPage(self.driver)
        register_page.wait.until(lambda d: register_page.is_displayed(*register_page.REGISTER_BTN))
        return register_page

    def go_forgot_password(self):
        self.click(*self.FORGOT_PWD_LINK)

    def find_input_field(self, field_type="account"):
        """
        通用方法查找输入框，无论是否有文本
        :param field_type: "account" 或 "password"
        :return: 找到的元素
        """
        from appium.webdriver.common.appiumby import AppiumBy
        
        if field_type == "account":
            # 尝试多种方式定位账号输入框
            selectors = [
                # 方式1: 通过类名和索引
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(0)"),
                # 方式2: 通过提示文本
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Email\")"),
                # 方式3: 通过XPath查找包含@或提示为Email
                (AppiumBy.XPATH, "//android.widget.EditText[contains(@text, '@') or @hint='Email' or @text='Email']"),
                # 方式4: 通过resource-id（如果有）
                # (AppiumBy.ID, "com.osaio.app:id/et_email"),
            ]
        else:  # password
            # 尝试多种方式定位密码输入框
            selectors = [
                # 方式1: 通过类名和索引
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(1)"),
                # 方式2: 通过提示文本
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Password\")"),
                # 方式3: 通过XPath查找密码框
                (AppiumBy.XPATH, "//android.widget.EditText[@password='true' or @hint='Password' or @text='Password']"),
                # 方式4: 通过resource-id（如果有）
                # (AppiumBy.ID, "com.osaio.app:id/et_password"),
            ]
        
        # 尝试每种选择器
        for by, value in selectors:
            try:
                element = self.find(by, value)
                print(f"使用 {by} = {value} 成功找到{field_type}输入框")
                return element
            except Exception as e:
                print(f"使用 {by} = {value} 查找{field_type}输入框失败: {e}")
                continue
        
        raise Exception(f"无法找到{field_type}输入框")

    def smart_input_account(self, account):
        """智能输入账号，处理输入框已有文本的情况"""
        try:
            # 使用通用方法查找输入框
            element = self.find_input_field("account")
            element.clear()
            element.send_keys(account)
        except Exception as e:
            print(f"智能输入账号失败: {e}")
            raise Exception(f"无法输入账号: {e}")

    def smart_input_password(self, password):
        """智能输入密码，处理输入框已有文本的情况"""
        try:
            # 使用通用方法查找输入框
            element = self.find_input_field("password")
            element.clear()
            element.send_keys(password)
        except Exception as e:
            print(f"智能输入密码失败: {e}")
            raise Exception(f"无法输入密码: {e}")

    def smart_login(self, account=None, password=None, force_login=False):
        """
        智能登录方法
        :param account: 账号（可选，如果已登录则不需要）
        :param password: 密码（可选，如果已登录则不需要）
        :param force_login: 是否强制重新登录，默认为False
        :return: HomePage对象
        """
        # 检查是否已经登录
        if not force_login and self.is_already_logged_in():
            print("用户已登录，直接返回首页")
            from pages.home_page import HomePage
            return HomePage(self.driver)
        
        # 如果需要强制重新登录或未登录，执行登录
        if not account or not password:
            raise ValueError("未提供账号或密码，无法登录")
        
        # 检查是否在登录页面
        if not self.is_displayed(*self.LOGIN_BTN, timeout=5):
            # 如果不在登录页面，可能需要先退出或导航到登录页面
            print("不在登录页面，可能需要先退出登录")
            # 这里可以添加退出登录的逻辑
            # 暂时先返回错误
            raise Exception("当前不在登录页面，无法执行登录操作")
        
        # 使用智能输入方法
        self.smart_input_account(account)
        self.smart_input_password(password)
        self.click(*self.LOGIN_BTN)
        
        # 等待登录完成，返回首页对象
        from pages.home_page import HomePage
        home_page = HomePage(self.driver)
        home_page.wait.until(lambda d: home_page.is_home_displayed())
        return home_page
