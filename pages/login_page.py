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
    
    # App 语言可能为中/英。登录页顶部有一个“登录/Sign In”入口(instance 0)，
    # 表单底部有“登录/Sign In”按钮(instance 1)；用 textMatches 语言无关匹配 + instance(1) 取按钮。
    LOGIN_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("登录|Sign In").instance(1)')
    REGISTER_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("注册|Sign Up")')
    FORGOT_PWD_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*(忘记密码|Forgot Password).*")')
    
    # 清除按钮（通常在输入框右侧）
    ACCOUNT_CLEAR_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.view.ViewGroup\").instance(16)")
    # 密码可见按钮
    PASSWORD_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.view.ViewGroup\").instance(19)")
    
    # 首页元素（用于检查是否已登录）。tab 数量随账号变化（3 或 4 个），故用角色名
    # （Home/Events/Account）匹配 content-desc，与 tab 总数无关。
    TAB_HOME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*(Home|首页).*tab.*")')
    TAB_Event = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*(Events|Message|事件|消息).*tab.*")')
    TAB_Account = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*(Account|帐户|账户).*tab.*")')

    # 错误提示元素。中文界面：错误密码提示为“密码不正确.”（末尾带句点，用 textContains 匹配）。
    # 注意：单个 UiSelector 里多个 textContains 是“相与”，会永不命中，故用 textMatches 做“相或”。
    ERROR_MESSAGE = (AppiumBy.ANDROID_UIAUTOMATOR,
                     'new UiSelector().textMatches("(?i).*(密码不正确|该邮箱未注册|错误|失败|incorrect|invalid|error).*")')
    EMPTY_ACCOUNT_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("该邮箱未注册")')
    EMPTY_PASSWORD_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("密码不正确")')

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
        from pages.home_page import HomePage

        if expect_success:
            # 期望成功：若已登录则直接返回首页
            if self.is_already_logged_in():
                print("用户已登录，直接返回首页")
                return HomePage(self.driver)
        else:
            # 期望失败（错误用例）：必须从登录页开始。若当前已登录，先登出，
            # 否则会走 is_already_logged_in 直接返回 HomePage，导致错误断言失败。
            if self.is_already_logged_in():
                print("错误用例前置：当前已登录，先登出以回到登录页")
                self.ensure_logged_out()

        # 确保停在登录页（必要时重启 App 复位，消除半渲染/子页状态）
        self.ensure_login_page()

        # 执行登录流程（使用智能输入方法）
        self._do_login(account, password)

        if expect_success:
            # 等待登录完成，返回首页对象
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

    def find_input_field(self, field_type="account", timeout=4):
        """
        通用方法查找输入框，无论是否有文本。
        :param field_type: "account" 或 "password"
        :param timeout: 单个定位策略的等待秒数（渲染完成后元素会立刻出现，无需长等待）
        :return: 找到的元素

        说明：实际页面（RN）中，邮箱框 hint="邮箱"、密码框 hint="密码" 且 password=true，
        均为 android.widget.EditText，无 resource-id，因此以 className+instance 为主，
        并用 hint / password 作为兜底，同时兼容英文 Email/Password。
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        if field_type == "account":
            selectors = [
                # 首选：第一个输入框
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)'),
                # 兜底：按 hint 匹配邮箱框（中/英）
                (AppiumBy.XPATH, "//android.widget.EditText[@hint='邮箱' or @hint='Email']"),
                # 兜底：已预填的邮箱通常包含 @
                (AppiumBy.XPATH, "//android.widget.EditText[contains(@text, '@')]"),
            ]
        else:  # password
            selectors = [
                # 首选：第二个输入框
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)'),
                # 兜底：密码属性
                (AppiumBy.XPATH, "//android.widget.EditText[@password='true']"),
                # 兜底：按 hint 匹配密码框（中/英）
                (AppiumBy.XPATH, "//android.widget.EditText[@hint='密码' or @hint='Password']"),
            ]

        last_err = None
        for by, value in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                print(f"已定位{field_type}输入框: {by}={value}")
                return element
            except Exception as e:
                last_err = e
                print(f"定位{field_type}输入框失败: {by}={value}")
                continue

        raise Exception(f"无法找到{field_type}输入框（最后错误: {last_err}）")

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

    def wait_for_login_page(self, timeout=10):
        """等待登录页渲染完成（登录按钮或邮箱输入框出现）。返回是否已到达登录页。"""
        from selenium.webdriver.support.ui import WebDriverWait

        def _ready(_d):
            try:
                return (self.is_displayed(*self.LOGIN_BTN, timeout=1)
                        or self.is_displayed(*self.ACCOUNT_INPUT, timeout=1))
            except Exception:
                return False

        try:
            return bool(WebDriverWait(self.driver, timeout).until(_ready))
        except Exception:
            return False

    def _reach_login_form(self):
        """确保停在“登录表单”（有邮箱/密码输入框）。

        App 冷启动/登出后可能停在“欢迎来到OSAIO”页（只有顶部的 登录/注册 入口，
        没有输入框），此时需要点顶部“登录”进入表单。返回是否已见到输入框。
        """
        import time
        for _ in range(4):
            # 已有输入框 → 在表单
            if self.driver.find_elements(*self.ACCOUNT_INPUT):
                return True
            # 尝试点顶部“登录/Sign In”入口（welcome 页的登录入口为 instance(0)）
            try:
                if self.is_displayed(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("登录|Sign In")', timeout=2):
                    self.click(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("登录|Sign In").instance(0)')
                    time.sleep(1.5)
            except Exception:
                time.sleep(1)
        return bool(self.driver.find_elements(*self.ACCOUNT_INPUT))

    def ensure_login_page(self):
        """确保当前停在登录页（能看到输入框）；若不是，则重启 App、跳过引导、进入登录表单。"""
        if self.wait_for_login_page(timeout=8) and self._reach_login_form():
            return True

        print("未检测到登录表单，尝试重启 App 复位…")
        self.restart_app()
        try:
            self.skip_onboarding()
        except Exception:
            pass

        if self.wait_for_login_page(timeout=12) and self._reach_login_form():
            return True

        raise Exception("无法进入登录页，登录中止")

    def ensure_logged_out(self):
        """确保处于已登出状态（登录页）。若已登录则通过账户页退出登录。

        主要服务于 force_login=True：由于 caps 使用 noReset=true 且勾选“记住我已登录”，
        单纯重启 App 仍会保持登录态，必须通过 UI 走一次退出登录。
        """
        # 已在登录页 → 无需处理
        if self.wait_for_login_page(timeout=3):
            return True

        # 先重启到已知的顶层界面（已登录→首页；未登录→登录页）
        self.restart_app()
        try:
            self.skip_onboarding()
        except Exception:
            pass
        if self.wait_for_login_page(timeout=6):
            return True

        # 仍不是登录页 → 处于已登录态（首页 / “添加新设备”全屏页 / 其它子页），
        # 直接走账户设置退出登录。logout() 自包含完整导航（会先关闭“添加新设备”页再进账户 tab），
        # 因此这里不再用 is_home_displayed() 做前置门槛——重启后常停在添加设备页，
        # 该门槛会误判 is_home_displayed()=False 而跳过登出，导致前置失败（真机实测的偶发点）。
        try:
            from pages.account_page import AccountPage
            if AccountPage(self.driver).logout():
                return self.wait_for_login_page(timeout=8)
            else:
                print("退出登录未成功")
        except Exception as e:
            print(f"退出登录异常: {e}")

        return self.wait_for_login_page(timeout=3)

    def click_login_button(self):
        """稳健地点击登录按钮，多策略兜底。"""
        strategies = [
            self.LOGIN_BTN,  # text "登录" instance(1)（页面顶部还有一个“登录”tab 为 instance(0)）
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.Button").instance(0)'),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("登录").instance(0)'),
        ]
        for by, value in strategies:
            if self.is_displayed(by, value, timeout=3):
                try:
                    self.click(by, value)
                    print(f"点击登录按钮: {by}={value}")
                    return True
                except Exception:
                    continue
        raise Exception("无法点击登录按钮")

    def _do_login(self, account, password):
        """在登录页输入账号密码并点击登录（调用前需确保已在登录页）。"""
        self.smart_input_account(account)
        self.smart_input_password(password)
        self.click_login_button()

    def smart_login(self, account=None, password=None, force_login=False):
        """
        智能登录方法
        :param account: 账号（可选，如果已登录则不需要）
        :param password: 密码（可选，如果已登录则不需要）
        :param force_login: 是否强制重新登录，默认为False
        :return: HomePage对象
        """
        from pages.home_page import HomePage

        if force_login:
            # 强制重新登录：先确保已登出（回到登录页）
            print("force_login=True：先确保已登出")
            self.ensure_logged_out()
        elif self.is_already_logged_in():
            # 已登录且不强制重登 → 直接返回首页
            print("用户已登录，直接返回首页")
            return HomePage(self.driver)

        # 需要登录：必须提供账号密码
        if not account or not password:
            raise ValueError("未提供账号或密码，无法登录")

        # 确保停在登录页（必要时重启 App 复位）
        self.ensure_login_page()

        # 输入并登录
        self._do_login(account, password)

        # 等待登录完成，返回首页对象。
        # 首装后**首次**登录会连续弹系统权限（通知/定位/蓝牙）与设备“升级弹窗”盖住首页，
        # 使 is_home_displayed() 迟迟不满足而超时（noReset 的非首装登录已授权、无此问题）。
        # 故边关这些弹窗边等首页出现；仍不出现时再走一次显式等待，保持原有失败语义。
        import time as _time
        home_page = HomePage(self.driver)
        deadline = _time.time() + 25
        while _time.time() < deadline:
            if home_page.is_displayed(*home_page.TAB_HOME, timeout=1):
                break
            try:
                home_page.dismiss_permission_dialogs(max_rounds=1)
                home_page.dismiss_firmware_upgrade_dialog()
            except Exception:
                pass
            _time.sleep(0.5)
        if not home_page.is_displayed(*home_page.TAB_HOME, timeout=2):
            home_page.wait.until(lambda d: home_page.is_home_displayed())
        print("登录成功，已进入首页")
        return home_page

    def skip_onboarding(self, max_tries=5):
        """尝试跳过首次启动的引导页（同意 -> 开始等）。

        性能关键：本方法会在“已登录/已在登录页/无引导”时被调用（如 ensure_logged_out
        重启 App 后）。此前用 tap_text（内部 15s 显式等待）逐个点击不存在的按钮，
        与 driver 的 10s 隐式等待叠加，单次探测可达 ~25s，空跑累计数分钟。

        改为：临时把隐式等待压到 1s，用 find_elements 做“找不到即刻返回”的快速探测，
        存在引导按钮才点击；扫描结束后恢复隐式等待。
        """
        from time import sleep

        onboarding_texts = ["同意", "Agree", "开始", "Start", "Get Started", "让我们开始"]

        def _login_form_present():
            return bool(self.driver.find_elements(*self.LOGIN_BTN)
                        or self.driver.find_elements(*self.ACCOUNT_INPUT))

        try:
            self.driver.implicitly_wait(1)
        except Exception:
            pass
        try:
            for _ in range(max_tries):
                # 已到登录页/登录表单 → 引导已跳过
                if _login_form_present():
                    return True

                progressed = False
                for txt in onboarding_texts:
                    els = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{txt}")')
                    if els:
                        try:
                            els[0].click()
                            progressed = True
                            sleep(1.5)
                            break
                        except Exception:
                            continue

                if not progressed:
                    # 没有可点击的引导按钮（已登录/已在登录页/无引导），退出
                    break
            return _login_form_present()
        finally:
            try:
                self.driver.implicitly_wait(10)
            except Exception:
                pass
