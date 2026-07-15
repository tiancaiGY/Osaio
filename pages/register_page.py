"""注册页面 - 分步注册流程"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
import time
import os


class RegisterPage(BasePage):
    # 第一步：注册页面元素（输入邮箱和国家）
    COUNTRY_SELECTOR = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"Country\").textContains(\"国家\")")
    EMAIL_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(0)")
    PRIVACY_CHECKBOX = (AppiumBy.XPATH, "//*[contains(@text, 'Privacy') or contains(@text, '隐私')]")
    TERMS_CHECKBOX = (AppiumBy.XPATH, "//*[contains(@text, 'Terms') or contains(@text, '条款')]")
    REGISTER_BTN_STEP1 = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Sign Up\").instance(1)")
    BACK_TO_LOGIN_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Sign In\")")
    # 兼容老测试中使用的 REGISTER_BTN 名称
    REGISTER_BTN = REGISTER_BTN_STEP1
    
    # 第二步：验证码页面元素
    VERIFICATION_CODE_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\")")
    VERIFICATION_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"Verification\").textContains(\"Resend Code\")")
    RESEND_CODE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"Resend\").textContains(\"重发\")")
    VERIFY_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Verify\").textContains(\"验证\")")
    
    # 第三步：设置密码页面元素
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(0)")
    CONFIRM_PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(1)")
    PASSWORD_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"Password\").textContains(\"密码\")")
    CONFIRM_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Confirm\").textContains(\"确认\")")
    
    # 国家选择页面元素
    COUNTRY_SEARCH_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\")")
    COUNTRY_LIST = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.TextView\")")
    COUNTRY_ITEM = (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'China') or contains(@text, '美国') or contains(@text, 'United')]")
    COUNTRY_PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"Country\").textContains(\"国家\")")
    
    # 错误提示
    ERROR_MESSAGE = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"error\").textContains(\"Error\")")
    EMAIL_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"email\").textContains(\"Email\")")
    PASSWORD_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"password\").textContains(\"Password\")")
    CODE_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains(\"code\").textContains(\"Code\").textContains(\"验证码\")")
    
    def select_country(self, country_name="China"):
        """
        选择国家
        :param country_name: 国家名称，如 "China", "United States"
        :return: 选择的国家名称
        """
        # 尝试点击国家选择器，如果找不到则降级处理
        try:
            self.click(*self.COUNTRY_SELECTOR)
            # 等待国家选择页面加载
            self.wait.until(lambda d: self.is_displayed(*self.COUNTRY_PAGE_TITLE))
            print("已进入国家选择页面")
        except Exception:
            print("未找到国家选择器，尝试在当前页面查找国家列表或搜索框")
        
        # 如果需要搜索国家
        try:
            # 输入搜索关键词（如果存在搜索框）
            self.input_text(*self.COUNTRY_SEARCH_INPUT, country_name)
            print(f"搜索国家: {country_name}")
        except Exception:
            print("搜索框未找到，直接在国家列表中查找或使用页面上的国家文本")
        
        # 选择国家
        # 尝试通过文本选择国家
        try:
            country_selector = (AppiumBy.ANDROID_UIAUTOMATOR, f"new UiSelector().text(\"{country_name}\")")
            self.click(*country_selector)
            print(f"选择国家: {country_name}")
            return country_name
        except Exception:
            # 如果找不到，尝试在列表中选择或直接匹配页面文本
            try:
                countries = self.driver.find_elements(*self.COUNTRY_LIST)
                if countries:
                    # 尝试找到与 country_name 匹配的条目
                    for c in countries:
                        try:
                            if country_name.lower() in c.text.lower():
                                c.click()
                                print(f"通过列表选择国家: {c.text}")
                                return c.text
                        except Exception:
                            continue
                    # 否则选择第一个国家作为降级
                    countries[0].click()
                    selected_country = countries[0].text
                    print(f"选择第一个国家: {selected_country}")
                    return selected_country
            except Exception as e:
                print(f"选择国家失败: {e}")
                # 返回上一页
                try:
                    self.back()
                except Exception:
                    pass
                return None
        
        # 返回注册页面
        return country_name
    
    def register_step1_input_email(self, email, country="China", agree_privacy=True, agree_terms=True):
        """
        注册第一步：输入邮箱、选择国家、同意条款
        :param email: 邮箱
        :param country: 国家名称
        :param agree_privacy: 是否同意隐私政策
        :param agree_terms: 是否同意条款
        :return: 验证码页面对象或错误消息
        """
        print("=== 注册第一步：输入邮箱和国家 ===")
        
        # 选择国家
        if country:
            selected_country = self.select_country(country)
            if not selected_country:
                return "选择国家失败"
        
        # 输入邮箱
        self.input_text(*self.EMAIL_INPUT, email)
        print(f"输入邮箱: {email}")
        
        # 同意隐私政策
        if agree_privacy:
            try:
                self.click(*self.PRIVACY_CHECKBOX)
                print("已同意隐私政策")
            except Exception:
                print("隐私政策复选框未找到或已默认选中")
        
        # 同意条款
        if agree_terms:
            try:
                self.click(*self.TERMS_CHECKBOX)
                print("已同意条款")
            except Exception:
                print("条款复选框未找到或已默认选中")
        
        # 点击注册按钮进入下一步（失败时保存诊断信息）
        try:
            self.click(*self.REGISTER_BTN_STEP1)
            print("点击注册按钮，进入验证码页面")
        except Exception as e_click:
            print(f"点击注册按钮失败: {e_click}")
            try:
                ts = time.strftime('%Y%m%d_%H%M%S')
                report_dir = os.path.join(os.getcwd(), 'report')
                os.makedirs(report_dir, exist_ok=True)
                page_src_path = os.path.join(report_dir, f'register_step1_click_pagesource_{ts}.xml')
                screenshot_path = os.path.join(report_dir, f'register_step1_click_screenshot_{ts}.png')
                try:
                    with open(page_src_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print(f"已保存页面源: {page_src_path}")
                except Exception as ex_src:
                    print(f"保存页面源失败: {ex_src}")
                try:
                    self.driver.get_screenshot_as_file(screenshot_path)
                    print(f"已保存截图: {screenshot_path}")
                except Exception as ex_sh:
                    print(f"保存截图失败: {ex_sh}")
            except Exception as ex_cap:
                print(f"诊断信息保存失败: {ex_cap}")

            return "点击注册按钮失败"
        
        # 等待验证码页面加载
        try:
            self.wait.until(lambda d: self.is_displayed(*self.VERIFICATION_TITLE))
            print("已进入验证码页面")
            return self  # 返回当前页面对象，现在在验证码页面
        except Exception as e:
            print(f"未进入验证码页面: {e}")

            # 捕获页面源与截图以便诊断
            try:
                ts = time.strftime('%Y%m%d_%H%M%S')
                report_dir = os.path.join(os.getcwd(), 'report')
                os.makedirs(report_dir, exist_ok=True)
                page_src_path = os.path.join(report_dir, f'register_step1_pagesource_{ts}.xml')
                screenshot_path = os.path.join(report_dir, f'register_step1_screenshot_{ts}.png')
                try:
                    src = self.driver.page_source
                    with open(page_src_path, 'w', encoding='utf-8') as f:
                        f.write(src)
                    print(f"已保存页面源: {page_src_path}")
                except Exception as ex_src:
                    print(f"保存页面源失败: {ex_src}")

                try:
                    self.driver.get_screenshot_as_file(screenshot_path)
                    print(f"已保存截图: {screenshot_path}")
                except Exception as ex_sh:
                    print(f"保存截图失败: {ex_sh}")
            except Exception as ex_capture:
                print(f"诊断信息保存失败: {ex_capture}")

            # 检查是否有错误消息
            if self.is_error_displayed():
                error_msg = self.get_error_message()
                print(f"注册第一步失败: {error_msg}")
                return error_msg

            return "未知错误，未进入验证码页面"
    
    def register_step2_input_verification_code(self, verification_code):
        """
        注册第二步：输入验证码
        :param verification_code: 验证码
        :return: 密码设置页面对象或错误消息
        """
        print("=== 注册第二步：输入验证码 ===")
        
        # 确保在验证码页面
        if not self.is_displayed(*self.VERIFICATION_TITLE, timeout=5):
            return "不在验证码页面"
        
        # 输入验证码
        self.input_text(*self.VERIFICATION_CODE_INPUT, verification_code)
        print(f"输入验证码: {verification_code}")
        
        # 点击验证按钮
        self.click(*self.VERIFY_BTN)
        print("点击验证按钮")
        
        # 等待密码设置页面加载
        try:
            self.wait.until(lambda d: self.is_displayed(*self.PASSWORD_TITLE))
            print("已进入密码设置页面")
            return self  # 返回当前页面对象，现在在密码设置页面
        except Exception as e:
            print(f"未进入密码设置页面: {e}")
            
            # 检查验证码错误
            if self.is_displayed(*self.CODE_ERROR, timeout=3):
                error_msg = self.find(*self.CODE_ERROR).text
                print(f"验证码错误: {error_msg}")
                return error_msg
            
            return "验证失败，未进入密码设置页面"
    
    def register_step3_set_password(self, password, confirm_password=None):
        """
        注册第三步：设置密码
        :param password: 密码（6-28位）
        :param confirm_password: 确认密码（默认为与密码相同）
        :return: 首页对象或错误消息
        """
        print("=== 注册第三步：设置密码 ===")
        
        if confirm_password is None:
            confirm_password = password
        
        # 确保在密码设置页面
        if not self.is_displayed(*self.PASSWORD_TITLE, timeout=5):
            return "不在密码设置页面"
        
        # 检查密码长度
        if len(password) < 6 or len(password) > 28:
            return f"密码长度必须在6-28位之间，当前长度: {len(password)}"
        
        # 输入密码
        self.input_text(*self.PASSWORD_INPUT, password)
        print(f"输入密码: {'*' * len(password)}")
        
        # 输入确认密码
        self.input_text(*self.CONFIRM_PASSWORD_INPUT, confirm_password)
        print(f"输入确认密码: {'*' * len(confirm_password)}")
        
        # 点击确认按钮
        self.click(*self.CONFIRM_BTN)
        print("点击确认按钮")
        
        # 等待注册完成，跳转到首页
        try:
            from pages.home_page import HomePage
            home_page = HomePage(self.driver)
            home_page.wait.until(lambda d: home_page.is_home_displayed())
            print("注册成功，已跳转到首页")
            return home_page
        except Exception as e:
            print(f"注册完成但未跳转到首页: {e}")
            
            # 检查密码错误
            if self.is_displayed(*self.PASSWORD_ERROR, timeout=3):
                error_msg = self.find(*self.PASSWORD_ERROR).text
                print(f"密码设置错误: {error_msg}")
                return error_msg
            
            return "密码设置完成，但未跳转到首页"
    
    def register_complete_flow(self, email, verification_code, password, country="China", 
                              agree_privacy=True, agree_terms=True, confirm_password=None):
        """
        完整注册流程
        :param email: 邮箱
        :param verification_code: 验证码
        :param password: 密码（6-28位）
        :param country: 国家名称
        :param agree_privacy: 是否同意隐私政策
        :param agree_terms: 是否同意条款
        :param confirm_password: 确认密码（默认为与密码相同）
        :return: 首页对象或错误消息
        """
        print("=== 开始完整注册流程 ===")
        
        # 第一步：输入邮箱和国家
        step1_result = self.register_step1_input_email(
            email=email,
            country=country,
            agree_privacy=agree_privacy,
            agree_terms=agree_terms
        )
        
        if isinstance(step1_result, str):
            return step1_result  # 返回错误消息
        
        # 第二步：输入验证码
        step2_result = self.register_step2_input_verification_code(verification_code)
        
        if isinstance(step2_result, str):
            return step2_result  # 返回错误消息
        
        # 第三步：设置密码
        step3_result = self.register_step3_set_password(
            password=password,
            confirm_password=confirm_password
        )
        
        return step3_result
    
    def is_error_displayed(self):
        """检查是否有错误提示"""
        return (self.is_displayed(*self.ERROR_MESSAGE) or 
                self.is_displayed(*self.EMAIL_ERROR) or 
                self.is_displayed(*self.PASSWORD_ERROR) or
                self.is_displayed(*self.CODE_ERROR))
    
    def get_error_message(self):
        """获取错误提示文本"""
        # 尝试获取不同类型的错误提示
        if self.is_displayed(*self.ERROR_MESSAGE, timeout=2):
            return self.find(*self.ERROR_MESSAGE).text
        elif self.is_displayed(*self.EMAIL_ERROR, timeout=2):
            return self.find(*self.EMAIL_ERROR).text
        elif self.is_displayed(*self.PASSWORD_ERROR, timeout=2):
            return self.find(*self.PASSWORD_ERROR).text
        elif self.is_displayed(*self.CODE_ERROR, timeout=2):
            return self.find(*self.CODE_ERROR).text
        return "未知错误"
    
    def go_back_to_login(self):
        """返回登录页面"""
        self.click(*self.BACK_TO_LOGIN_LINK)
        from pages.login_page import LoginPage
        return LoginPage(self.driver)
    
    def find_input_field(self, field_type="email"):
        """
        通用方法查找输入框，无论是否有文本
        :param field_type: "email", "password", "confirm_password", "first_name", "last_name", "phone"
        :return: 找到的元素
        """
        from appium.webdriver.common.appiumby import AppiumBy
        
        if field_type == "email":
            selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(0)"),
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Email\")"),
                (AppiumBy.XPATH, "//android.widget.EditText[contains(@text, '@') or @hint='Email' or @text='Email']"),
            ]
        elif field_type == "password":
            selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(1)"),
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Password\")"),
                (AppiumBy.XPATH, "//android.widget.EditText[@password='true' or @hint='Password' or @text='Password']"),
            ]
        elif field_type == "confirm_password":
            selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(2)"),
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Confirm Password\")"),
                (AppiumBy.XPATH, "//android.widget.EditText[@password='true' or @hint='Confirm Password' or @text='Confirm Password']"),
            ]
        elif field_type == "first_name":
            selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"First Name\")"),
                (AppiumBy.XPATH, "//android.widget.EditText[@hint='First Name' or @text='First Name']"),
            ]
        elif field_type == "last_name":
            selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Last Name\")"),
                (AppiumBy.XPATH, "//android.widget.EditText[@hint='Last Name' or @text='Last Name']"),
            ]
        elif field_type == "phone":
            selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"Phone Number\")"),
                (AppiumBy.XPATH, "//android.widget.EditText[@hint='Phone Number' or @text='Phone Number']"),
            ]
        else:
            raise ValueError(f"不支持的字段类型: {field_type}")
        
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
    
    def smart_input_email(self, email):
        """智能输入邮箱"""
        try:
            element = self.find_input_field("email")
            element.clear()
            element.send_keys(email)
        except Exception as e:
            print(f"智能输入邮箱失败: {e}")
            raise Exception(f"无法输入邮箱: {e}")
    
    def smart_input_password(self, password):
        """智能输入密码"""
        try:
            element = self.find_input_field("password")
            element.clear()
            element.send_keys(password)
        except Exception as e:
            print(f"智能输入密码失败: {e}")
            raise Exception(f"无法输入密码: {e}")
    
    def smart_input_confirm_password(self, confirm_password):
        """智能输入确认密码"""
        try:
            element = self.find_input_field("confirm_password")
            element.clear()
            element.send_keys(confirm_password)
        except Exception as e:
            print(f"智能输入确认密码失败: {e}")
            raise Exception(f"无法输入确认密码: {e}")