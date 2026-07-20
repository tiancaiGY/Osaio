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

    # 首次进直播的“设备升级弹窗”（New Device Firmware Found）——通用自定义弹窗框架，
    # 结构 id 真机确认（reports/probe_seq_0）：root_remind/checkbox_remind/txt_reminds、
    # ll_negative(txt_negative=Not Now) / ll_positive(txt_positive=Upgrade Firmware)。
    # 处理原则：勾选“Don't remind me again”→ 点“Not Now”；**切勿**点“Upgrade Firmware”（会触发真实升级）。
    FW_TITLE = (AppiumBy.ID, "com.afar.osaio:id/txt_title")            # "New Device Firmware Found"
    FW_CHECKBOX = (AppiumBy.ID, "com.afar.osaio:id/checkbox_remind")   # "Don't remind me again"
    FW_NOT_NOW = (AppiumBy.ID, "com.afar.osaio:id/ll_negative")        # 负按钮容器（Not Now）
    FW_NOT_NOW_TXT = (AppiumBy.ID, "com.afar.osaio:id/txt_negative")
    # 首次进直播的“引导流程”（引导图）——逐步点“下一步/Next…”关闭。用户口述流程，故用语言无关
    # 的引导专属文案（不含 OK/好的/Start 等过泛词，避免误点直播控制项）。
    INTRO_NEXT = (AppiumBy.ANDROID_UIAUTOMATOR,
                  'new UiSelector().textMatches("(?i).*(下一步|下一个|我知道了|知道了|知道啦|Next|Skip|跳过|开始体验|立即体验|开始使用|I Got It|Got it).*")')


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
        # 含首装后的“New Subscription Plans”订阅推广页（Skip for Now）等一次性插屏；
        # 以及登录后设备端弹出的“New Device Firmware Found”固件升级弹窗——点“Not Now”跳过
        # （切勿点“Upgrade Firmware”），否则该弹窗会盖住设备卡，导致进不去直播/回放（真机实测）。
        patterns = [
            "允许|Allow|While using the app|Only this time|OK|好|确定|Skip for Now|Skip|跳过|Maybe Later|稍后|Not Now|暂不升级|暂不|以后再说|稍后再说|下次再说|Got it|知道了|I Got It",
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

    # ---------------------------------------------------------------- 直播前置
    def _tap_element(self, el):
        """点击元素：优先 element.click()，失败退坐标点中心。"""
        try:
            el.click()
            return True
        except Exception:
            try:
                r = el.rect
                self.driver.tap([(int(r["x"] + r["width"] / 2), int(r["y"] + r["height"] / 2))])
                return True
            except Exception:
                return False

    def dismiss_firmware_upgrade_dialog(self, check_dont_remind=True):
        """第一步：关“New Device Firmware Found”设备升级弹窗。

        勾选“Don't remind me again”（减少后续复现）→ 点“Not Now”。**切勿**点“Upgrade Firmware”。
        仅当确为该弹窗时才处理（标题含 Firmware/固件 或存在 Don't remind 勾选项），以免误关其它
        复用同一套 ll_negative/ll_positive id 的对话框。返回是否处理了弹窗。
        """
        from time import sleep
        # 关键：把隐式等待临时压到 1s。否则弹窗不在场时，对 txt_title/checkbox 的 find_elements
        # 会各自空等满 10s（隐式等待），本方法每轮被 enter_live_view 调用一次 → 单轮就吃掉
        # ~20s，直接耗尽进直播的 40s 预算，导致真弹窗出现后再没机会被关闭（真机实测踩坑）。
        try:
            self.driver.implicitly_wait(1)
        except Exception:
            pass
        try:
            title_els = self.driver.find_elements(*self.FW_TITLE)
            is_fw = any(("firmware" in (e.text or "").lower() or "固件" in (e.text or ""))
                        for e in title_els)
            cb_els = self.driver.find_elements(*self.FW_CHECKBOX)
            if not (is_fw or cb_els):
                return False
            print(f"检测到设备升级弹窗（is_fw={is_fw}, checkbox={bool(cb_els)}），准备关闭")
            # 勾选“Don't remind me again”
            if check_dont_remind and cb_els:
                print(f"  勾选 Don't remind me again -> {self._tap_element(cb_els[0])}")
                sleep(0.5)
            # 点“Not Now”（负按钮容器优先，退化到文本）
            for loc in (self.FW_NOT_NOW, self.FW_NOT_NOW_TXT):
                els = self.driver.find_elements(*loc)
                if els:
                    ok = self._tap_element(els[0])
                    print(f"  点 Not Now（{loc[1]}）-> {ok}")
                    sleep(1.5)
                    return True
            print("  未找到 Not Now 按钮（ll_negative/txt_negative 均缺失）")
            return False
        finally:
            try:
                self.driver.implicitly_wait(10)
            except Exception:
                pass

    def dismiss_intro_guide(self, max_steps=8):
        """第二步：关首次进直播的“引导流程”——反复点“下一步/Next…”直至无该类按钮。

        返回点击次数（0 表示无引导）。用短隐式等待做快速探测，无引导时立即返回、不空等。
        """
        from time import sleep
        steps = 0
        try:
            self.driver.implicitly_wait(1)
        except Exception:
            pass
        try:
            for _ in range(max_steps):
                els = self.driver.find_elements(*self.INTRO_NEXT)
                if not els:
                    break
                txt = (els[0].text or "").strip()
                if not self._tap_element(els[0]):
                    break
                steps += 1
                print(f"  引导流程点“下一步/{txt}”（第 {steps} 次）")
                sleep(1.5)
            return steps
        finally:
            try:
                self.driver.implicitly_wait(10)
            except Exception:
                pass

    def dismiss_live_view_intro(self):
        """直播前置组合：先关设备升级弹窗，再关引导流程（best-effort，不抛异常）。

        首次进直播会依次出现“设备升级弹窗 + 引导图流程”，二者都会盖住直播画面/设备卡，
        不清理则进不去直播或后续控件点击落空。返回是否处理了其中任意一项。
        """
        try:
            handled_fw = self.dismiss_firmware_upgrade_dialog()
        except Exception:
            handled_fw = False
        try:
            guide_steps = self.dismiss_intro_guide()
        except Exception:
            guide_steps = 0
        return bool(handled_fw or guide_steps)
