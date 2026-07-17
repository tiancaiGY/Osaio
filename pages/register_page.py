"""注册页面 - 分步注册流程"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
import time
import os


class RegisterPage(BasePage):
    # 重要：同一个 UiSelector 里链式写多个 textContains 是“相与”，一个元素不可能同时包含
    # 两种语言文案，会导致定位器永不命中（历史 bug）。凡是中/英双语匹配一律用
    # textMatches("a|b")（相或）；“包含”语义写成 .*(a|b).*。
    #
    # 第一步：注册（Sign Up）页面元素（RN 页面，实测结构见下）
    # 页面结构：顶部 Sign In/Sign Up tab → 国家行(含"China") → Email 输入框 →
    #           "I confirm ... Terms ... Privacy" 同意行(左侧有勾选框，行内含可点的政策链接) →
    #           底部 Sign Up 按钮。
    COUNTRY_SELECTOR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("China|中国")')
    EMAIL_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(0)")
    # 同意条款一整行（可点的 ViewGroup 包裹这段文本）。勾选框在该行最左侧留白处，
    # 行内的 Terms/Privacy 是可点链接——所以切勿点文字，要点最左侧勾选框。见 _toggle_agreement。
    AGREEMENT_ROW = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*(I confirm that I am|我确认|同意).*")')
    # 底部“Sign Up”按钮为 instance(1)（顶部 tab 是 instance(0)）。
    REGISTER_BTN_STEP1 = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("注册|Sign Up").instance(1)')
    BACK_TO_LOGIN_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("登录|Sign In")')
    # 兼容老测试中使用的 REGISTER_BTN 名称
    REGISTER_BTN = REGISTER_BTN_STEP1

    # 第二步：验证码页面元素。实测页面标题为“Verify Your Account”、
    # 副标题“Enter the verification code to continue”，含重发倒计时“NNs”。
    VERIFICATION_CODE_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\")")
    VERIFICATION_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*(Verify Your Account|Enter the verification code|Verification|验证码|验证你的|输入验证码).*")')
    RESEND_CODE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*(Resend|重发|重新发送).*")')
    VERIFY_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*(Verify|Continue|Next|验证|继续|下一步).*")')

    # 第三步：设置密码页面元素
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(0)")
    CONFIRM_PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\").instance(1)")
    PASSWORD_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*(Set password|设置密码|Password|密码).*")')
    # 设密页提交按钮实测文案为“Submit”（非 Confirm）；中英双语兼容。
    CONFIRM_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("Submit|提交|Confirm|确认|完成|Done")')

    # 国家选择页面元素（实测标题为“Country List”，含“Search”搜索框，条目如“China”“Afghanistan (+93)”）
    COUNTRY_SEARCH_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.EditText\")")
    COUNTRY_LIST = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().className(\"android.widget.TextView\")")
    COUNTRY_ITEM = (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'China') or contains(@text, '美国') or contains(@text, 'United')]")
    COUNTRY_PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*(Country List|Country|国家).*")')

    # 错误提示（大小写无关，中英双语；用 textMatches 相或）
    ERROR_MESSAGE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i).*(error|错误|失败|invalid|incorrect).*")')
    EMAIL_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i).*(email|邮箱).*(invalid|incorrect|错误|已注册|registered).*")')
    PASSWORD_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i).*(password|密码).*(invalid|incorrect|错误|不一致|mismatch|length|长度).*")')
    CODE_ERROR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i).*(code|验证码).*(invalid|incorrect|error|错误|expired).*")')
    
    def select_country(self, country_name="China"):
        """选择国家。

        实测：Sign Up 页的国家行显示当前国家（默认“China”），点击进入“Country List”页
        （含 Search 搜索框，条目如“China”“Afghanistan (+93)”）。若默认已是目标国家，
        点开后可直接在列表里点选；也可先用搜索框过滤。
        :return: 选择的国家名称（失败返回 None）
        """
        # 若当前页已显示目标国家且无需切换，直接返回（避免不必要的进出）
        # 点击国家行进入国家列表页
        try:
            self.click(*self.COUNTRY_SELECTOR)
            self.wait.until(lambda d: self.is_displayed(*self.COUNTRY_PAGE_TITLE, timeout=2))
            print("已进入国家选择页面（Country List）")
        except Exception:
            print("未能进入国家选择页（可能已在注册页且默认国家即为目标），继续")
            return country_name

        # 优先用搜索框过滤
        try:
            if self.is_displayed(*self.COUNTRY_SEARCH_INPUT, timeout=3):
                self.input_text(*self.COUNTRY_SEARCH_INPUT, country_name)
                print(f"搜索国家: {country_name}")
                import time
                time.sleep(1)
        except Exception:
            print("搜索框不可用，直接在列表中查找")

        # 在列表中点选匹配项
        try:
            item = (AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{country_name}")')
            if self.is_displayed(*item, timeout=3):
                self.click(*item)
                print(f"选择国家: {country_name}")
                return country_name
        except Exception:
            pass

        # 降级：扫描列表取第一个包含关键词的条目
        try:
            countries = self.driver.find_elements(*self.COUNTRY_LIST)
            for c in countries:
                try:
                    if country_name.lower() in (c.text or "").lower():
                        c.click()
                        print(f"通过列表选择国家: {c.text}")
                        return c.text
                except Exception:
                    continue
        except Exception as e:
            print(f"选择国家失败: {e}")

        # 仍未选中：返回上一页，交由调用方处理
        try:
            self.back()
        except Exception:
            pass
        return None

    def _toggle_agreement(self, agree=True):
        """切换“I confirm ... Terms ... Privacy”同意勾选框。

        关键：这一行里的 Terms/Privacy 是**行内可点链接**，点文字会跳到条款/隐私政策页；
        勾选框在该行**最左侧留白**处。因此对同意行左侧留白坐标做 tap，避开链接。
        :param agree: True=尝试勾选（点一次）。当前 App 无法读取勾选态，故只做一次点击尝试。
        :return: 是否找到并点击了同意行
        """
        els = self.driver.find_elements(*self.AGREEMENT_ROW)
        if not els:
            print("未找到同意条款行")
            return False
        try:
            # 取包裹该文本的可点父行 rect；勾选框在行最左侧，点 (left+40, 垂直中点)
            r = els[0].rect
            cx = int(r["x"] + 40)
            cy = int(r["y"] + r["height"] / 2)
            self.driver.tap([(cx, cy)])
            print(f"已点击同意条款勾选框: ({cx},{cy})")
            return True
        except Exception as e:
            print(f"点击同意条款勾选框失败: {e}")
            return False

    def register(self, email, password="", confirm_password="", agree_terms=True):
        """一步式注册入口（服务于负向/校验用例）。

        真机上注册是分步流程：Sign Up 页只输入**邮箱**并勾选同意，密码在后续页。
        因此本方法只完成 Sign Up 页的操作（输入邮箱、按需勾选同意、点 Sign Up），
        用于验证“空/非法邮箱、不同意条款”等 App 的即时校验行为。
        password/confirm_password 保留为兼容旧用例签名，Sign Up 页不使用。

        :return: 进入验证码页 -> RegisterPage(self)；否则返回错误消息字符串
                 （App 静默校验、无错误文案时返回描述性字符串）。
        """
        print(f"=== register(): 邮箱={email!r} agree_terms={agree_terms} ===")
        # 输入邮箱（空字符串则清空即可）
        try:
            el = self.find(*self.EMAIL_INPUT)
            el.clear()
            if email:
                el.send_keys(email)
        except Exception as e:
            return f"无法输入邮箱: {e}"

        if agree_terms:
            self._toggle_agreement(agree=True)

        # 点击底部 Sign Up
        try:
            self.click(*self.REGISTER_BTN_STEP1)
            print("点击 Sign Up")
        except Exception as e:
            return f"点击 Sign Up 失败: {e}"

        # 进入验证码页则算成功；否则读取错误提示或返回“无错误提示”描述
        if self.is_displayed(*self.VERIFICATION_TITLE, timeout=6):
            print("已进入验证码页面")
            return self
        if self.is_error_displayed():
            return self.get_error_message()
        return "未进入验证码页面且无明确错误提示（App 可能静默校验）"
    
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

        # 同意条款（隐私与条款为同一行的同意勾选框；agree_privacy/agree_terms 任一为真即勾选）
        if agree_privacy or agree_terms:
            self._toggle_agreement(agree=True)
        
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
    
    def _find_otp_input(self):
        """定位验证码页真正的 OTP 输入框。

        真机实测：验证码页是 RN 覆盖层，DOM 里同时存在底层注册页的邮箱 EditText
        （可见、y≈1161、text 为邮箱）和验证码页的**隐藏 OTP EditText**
        （很窄、位于 6 个数字框上方、y<900）。className 取 instance(0) 会误命中邮箱框。
        这里排除“含 @ 的邮箱框”，优先取位置最靠上的那个 EditText 作为 OTP 输入。
        返回元素或 None。
        """
        eds = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        cands = []
        for e in eds:
            try:
                txt = e.text or ""
                r = e.rect
            except Exception:
                continue
            if "@" in txt:  # 邮箱框，跳过
                continue
            cands.append((r.get("y", 99999), e))
        if not cands:
            return None
        cands.sort()  # y 最小（最靠上）的即 OTP 隐藏输入框
        return cands[0][1]

    def register_step2_input_verification_code(self, verification_code):
        """
        注册第二步：输入验证码
        :param verification_code: 验证码
        :return: 密码设置页面对象或错误消息

        真机实测：验证码页为 6 位数字框 + 隐藏 OTP 输入框，**无显式“验证/下一步”按钮**，
        输满 6 位后自动跳转到设密页。故本方法输入到 OTP 框后，直接等待设密页出现，
        仅在存在 VERIFY_BTN 时才点击（兼容其它版本）。
        """
        print("=== 注册第二步：输入验证码 ===")

        # 确保在验证码页面
        if not self.is_displayed(*self.VERIFICATION_TITLE, timeout=5):
            return "不在验证码页面"

        # 输入验证码到正确的隐藏 OTP 框（不是邮箱框）
        otp = self._find_otp_input()
        if otp is None:
            self._save_step_diag("verif_no_otp_input")
            return "未找到验证码输入框"
        try:
            otp.click()
            otp.clear()
        except Exception:
            pass
        otp.send_keys(verification_code)
        print(f"输入验证码: {verification_code}")

        # 若存在显式“验证/下一步”按钮则点击；否则依赖输满自动跳转
        if self.is_displayed(*self.VERIFY_BTN, timeout=2):
            try:
                self.click(*self.VERIFY_BTN)
                print("点击验证按钮")
            except Exception:
                pass

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

            self._save_step_diag("verif_no_password_page")
            return "验证失败，未进入密码设置页面"

    def _save_step_diag(self, reason):
        """保存注册步骤诊断（page_source + 截图）到 reports/。"""
        try:
            os.makedirs("reports", exist_ok=True)
            ts = time.strftime('%Y%m%d_%H%M%S')
            with open(f"reports/register_{reason}_{ts}.xml", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.driver.get_screenshot_as_file(f"reports/register_{reason}_{ts}.png")
            print(f"已保存注册诊断: reports/register_{reason}_{ts}.*")
        except Exception as e:
            print(f"保存注册诊断失败: {e}")
    
    def _find_password_fields(self):
        """定位设密页的“密码/确认密码”两个输入框（排除残留邮箱框）。

        与 _find_otp_input 同理：设密页 DOM 残留底层注册页含 @ 的邮箱 EditText。
        排除邮箱框后按 y 升序返回其余 EditText（前两个即 密码、确认密码）。
        """
        eds = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        cands = []
        for e in eds:
            try:
                if "@" in (e.text or ""):
                    continue
                cands.append((e.rect.get("y", 99999), e))
            except Exception:
                continue
        cands.sort()
        return [e for _, e in cands]

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
        
        # 输入密码 + 确认密码。
        # 真机实测：设密页仍是 RN 覆盖层，DOM 里残留底层注册页的邮箱 EditText（含 @）。
        # className instance(0)/(1) 会把邮箱框算进去，导致错位。这里排除邮箱框后，
        # 取按 y 排序的前两个 EditText 作为“密码/确认密码”。
        pwd_fields = self._find_password_fields()
        if len(pwd_fields) < 2:
            self._save_step_diag("password_fields_lt2")
            return "设密页未找到两个密码输入框"
        try:
            pwd_fields[0].click(); pwd_fields[0].clear(); pwd_fields[0].send_keys(password)
            print(f"输入密码: {'*' * len(password)}")
            pwd_fields[1].click(); pwd_fields[1].clear(); pwd_fields[1].send_keys(confirm_password)
            print(f"输入确认密码: {'*' * len(confirm_password)}")
        except Exception as e:
            self._save_step_diag("password_input_failed")
            return f"输入密码失败: {e}"
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass

        # 点击提交按钮（Submit）
        if not self.is_displayed(*self.CONFIRM_BTN, timeout=3):
            self._save_step_diag("password_no_submit_btn")
            return "设密页未找到提交按钮"
        self.click(*self.CONFIRM_BTN)
        print("点击提交按钮")
        
        # 等待注册完成，跳转到首页。
        # 注册成功后 App 自动登录并落到首页，但常伴“添加新设备/Add Device”全屏弹窗
        # 盖住底部 tab，使 is_home_displayed()（检 TAB_HOME）超时。故先轮询关闭该弹窗，
        # 再判定首页；给足时间（注册落地较慢）。
        from pages.home_page import HomePage
        from pages.account_page import AccountPage
        home_page = HomePage(self.driver)
        account_page = AccountPage(self.driver)
        deadline = time.time() + 25
        while time.time() < deadline:
            try:
                home_page.dismiss_permission_dialogs()   # 关掉“允许通知/定位”等系统弹窗
            except Exception:
                pass
            try:
                account_page._dismiss_bluetooth_popup()  # 关掉“添加新设备”全屏弹窗
            except Exception:
                pass
            if home_page.is_home_displayed():
                print("注册成功，已跳转到首页")
                return home_page
            time.sleep(1.5)

        print("注册完成但未检测到首页（可能弹窗持续遮挡）")
        # 检查密码错误
        if self.is_displayed(*self.PASSWORD_ERROR, timeout=3):
            error_msg = self.find(*self.PASSWORD_ERROR).text
            print(f"密码设置错误: {error_msg}")
            return error_msg

        self._save_step_diag("register_no_home_after_submit")
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