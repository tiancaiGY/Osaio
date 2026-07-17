"""首页"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class HomePage(BasePage):
    # 元素定位 - 需要用 Appium Inspector 确认实际 ID
    ADD_DEVICE_BTN = (AppiumBy.ACCESSIBILITY_ID, "new UiSelector().className(\"android.view.ViewGroup\").instance(39)")
    DEVICE_LIST = (AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().text(\"All Types\")")
    # 底部 tab 用 content-desc 定位。tab 数量随账号变化（部分账号 3 个 Home/Events/Account，
    # 部分 4 个含 Alarm），故 **不能**写死 "of 3"。改用角色名前缀（Home/Events/Account）匹配，
    # 与 tab 总数无关；这些角色名在 content-desc 里稳定出现（形如 "Home, tab, 1 of 4"）。
    # 注：Account tab 始终是最后一个（3 of 3 或 4 of 4）。
    TAB_HOME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*(Home|首页).*tab.*")')
    TAB_MESSAGE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*(Events|Message|事件|消息).*tab.*")')
    TAB_MINE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionMatches("(?i).*(Account|帐户|账户).*tab.*")')


    def is_home_displayed(self):
        return self.is_displayed(*self.TAB_HOME)

    def click_add_device(self):
        self.click(*self.ADD_DEVICE_BTN)

    def go_account(self):
        from pages.account_page import AccountPage
        account_page = AccountPage(self.driver)
        account_page.go_to_account_tab()
        return account_page

    def go_message(self):
        self.click(*self.TAB_MESSAGE)

    def go_mine(self):
        self.click(*self.TAB_MINE)

    def dismiss_permission_dialogs(self, max_rounds=4):
        """关闭进入首页后可能连续弹出的系统权限/通知弹窗。

        真机实测注册/登录后会弹“Allow OSAIO to send you notifications?”等系统弹窗，
        按钮为 Allow / Don't allow（还可能有定位、蓝牙等多个连续弹窗）。
        这里优先点“允许/Allow/While using…/OK”让流程继续，其次点拒绝类按钮；
        用 textMatches 双语匹配，循环多轮直到无弹窗。返回是否点掉过至少一个。
        """
        from appium.webdriver.common.appiumby import AppiumBy
        from time import sleep
        # 优先“允许/继续/跳过”，其次“拒绝/取消”，兼顾中英与带撇号写法。
        # 含首装后的“New Subscription Plans”订阅推广页（Skip for Now）等一次性插屏。
        patterns = [
            "允许|Allow|While using the app|Only this time|OK|好|确定|Skip for Now|Skip|跳过|Maybe Later|稍后|Got it|知道了|I Got It",
            "不允许|Don.t allow|Deny|取消|Cancel|拒绝|Close|关闭",
        ]
        dismissed = False
        for _ in range(max_rounds):
            hit = False
            for pat in patterns:
                loc = (AppiumBy.ANDROID_UIAUTOMATOR,
                       'new UiSelector().textMatches("(?i)(%s)")' % pat)
                if self.is_displayed(*loc, timeout=1):
                    try:
                        self.click(*loc)
                        dismissed = True
                        hit = True
                        sleep(1)
                        break
                    except Exception:
                        continue
            if not hit:
                break
        return dismissed
