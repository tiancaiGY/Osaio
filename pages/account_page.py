from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
import time
import os


class AccountPage(BasePage):
    # 中文界面 content-desc 为“帐户, tab, 3 of 3”，用 descriptionContains 做语言无关匹配。
    ACCOUNT_TAB = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("tab, 3 of 3")')
    # 帐户 tab 落地页的“资料头部”（含头像/邮箱），点击后进入“账户设置”页。无 id，用 viewgroup 索引兜底。
    ACCOUNT_SETTINGS = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.view.ViewGroup").instance(14)')
    # 已进入“账户设置”页的标识（中文实际文案为“账户设置”）。
    ACCOUNT_SETTINGS_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("账户设置")')
    PROFILE_AREA = ACCOUNT_SETTINGS_TITLE
    # 退出登录按钮（设置页底部）。中文文案“退出登录”。
    LOGOUT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("退出登录")')
    # 退出确认弹窗标题（“立即退出 OSAIO？”），用于判断弹窗已出现。
    LOGOUT_CONFIRM_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("立即退出")')
    # 邮箱文本（资料头部内），作为进入账户设置的兜底点击目标。
    PROFILE_EMAIL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("@")')
    DENY_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("不允许|Deny|Cancel")')
    BLUETOOTH_CLOSE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.view.ViewGroup").instance(84)')

    def go_to_account_tab(self):
        """跳转到账户标签页（进入账户 landing，并尽量进入“账户设置”页）。

        使用可靠原语：先退出遮挡的“添加新设备”页，再用坐标点击切到帐户 tab
        （element.click() 对该 RN tab 无效），最后点击资料头部进入账户设置。
        """
        self._dismiss_bluetooth_popup()
        if not self._tap_account_tab():
            self._dismiss_bluetooth_popup()
            if not self._tap_account_tab():
                self._save_diagnostics("account_tab_click_failed")
                return self
        # 进入账户设置页（best-effort，失败不抛出以兼容旧调用方）
        self._open_account_settings()
        return self

    def dismiss_system_dialogs(self):
        """尝试关闭常见系统权限弹窗（用快速存在性探测，避免逐个 15s+10s 空等）。"""
        try:
            self.driver.implicitly_wait(1)
        except Exception:
            pass
        try:
            for text in ["不允许", "Deny", "Cancel"]:
                els = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{text}")')
                if els:
                    try:
                        els[0].click()
                        return True
                    except Exception:
                        continue
            return False
        finally:
            try:
                self.driver.implicitly_wait(10)
            except Exception:
                pass

    # open_profile 已移除：不再通过点击头像进入设置，使用 ACCOUNT_SETTINGS 直接进入

    def logout(self):
        """执行退出登录：帐户 tab → 账户设置 → 退出登录 → 确认弹窗 → 回到登录页。

        自包含流程（不依赖 go_to_account_tab），使用中文实际文案定位。返回是否成功。
        """
        try:
            # 1) 先退出可能覆盖首页、拦截 tab 的“添加新设备”全屏页，再进入帐户 tab。
            #    帐户 tab 必须用坐标点击（element.click() 对该 RN tab 无效）。
            self._dismiss_bluetooth_popup()
            if not self._tap_account_tab():
                # 可能是“添加新设备”页延迟渲染挡住了 tab，退出后重试一次
                self._dismiss_bluetooth_popup()
                self._tap_account_tab()
            self.dismiss_system_dialogs()

            # 2) 进入“账户设置”页（点击资料头部/邮箱）
            if not self._open_account_settings():
                self._save_diagnostics("account_settings_enter_failed")
                return False

            # 3) 点击“退出登录”（设置页底部，必要时上滑露出）
            if not self._tap_logout_entry():
                self._save_diagnostics("logout_no_button")
                return False

            # 4) 确认弹窗（“立即退出 OSAIO？”）
            try:
                self.wait.until(lambda d: self.is_displayed(*self.LOGOUT_CONFIRM_TITLE, timeout=2))
            except Exception:
                pass
            if not self._confirm_logout():
                self._save_diagnostics("logout_confirm_failed")
                return False

            # 5) 等待回到登录页
            from pages.login_page import LoginPage
            ok = LoginPage(self.driver).wait_for_login_page(timeout=10)
            if not ok:
                self._save_diagnostics("logout_not_back_to_login")
            return ok
        except Exception:
            self._save_diagnostics("logout_exception")
            return False

    # 会遮挡首页/底部 tab、拦截“帐户”tab 点击的两类干扰界面（BLE 自动发现附近设备触发）：
    #  1) 全屏“添加新设备/正在搜索附近的设备”页（App 重启后 RN 可能恢复到此页）；
    #  2) “发现设备”底部弹窗（含“所有设备/添加设备”，会盖住底部 tab 栏）。
    # 关键：底部弹窗在重启后会“延迟数秒”才弹出，所以必须在每次点击 tab 前重新检测并关闭；
    # 两类界面都可用系统返回键关闭（实测有效）。它们的 tab 仍在无障碍树中，
    # 会导致 is_home_displayed() 误判为“在首页”。
    ADD_DEVICE_POPUP_MARKERS = [
        'new UiSelector().textContains("添加新设备")',
        'new UiSelector().textContains("正在搜索附近的设备")',
        'new UiSelector().textContains("所有设备")',
        'new UiSelector().descriptionContains("add-device")',
    ]

    def _add_device_page_present(self):
        for sel in self.ADD_DEVICE_POPUP_MARKERS:
            if self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, sel):
                return True
        return False

    def _on_account_page(self):
        """是否已在“帐户”landing/设置页（出现邮箱/退出登录/账户设置即判定为是）。"""
        try:
            self.driver.implicitly_wait(1)
        except Exception:
            pass
        try:
            return bool(self.driver.find_elements(*self.PROFILE_EMAIL)
                        or self.driver.find_elements(*self.LOGOUT_BUTTON)
                        or self.driver.find_elements(*self.ACCOUNT_SETTINGS_TITLE))
        finally:
            try:
                self.driver.implicitly_wait(10)
            except Exception:
                pass

    def _tap_account_tab(self, max_tries=6):
        """切换到“帐户”tab。

        关键：该 RN 底部 tab 的无障碍节点不是触摸目标，element.click() 实测无效（不切换），
        必须对 tab 中心做坐标点击。点击后校验是否已进入账户页，最多重试 max_tries 次。
        """
        import time
        for i in range(max_tries):
            # 每次点击前重新关闭可能盖住 tab 栏的“发现设备”弹窗/添加设备页
            # （该弹窗在重启后会延迟弹出，故必须每轮重检，不能只在最开始关一次）
            self._dismiss_bluetooth_popup()
            els = self.driver.find_elements(*self.ACCOUNT_TAB)
            if not els:
                time.sleep(1.5)
                continue
            try:
                r = els[0].rect
                cx = int(r["x"] + r["width"] / 2)
                cy = int(r["y"] + r["height"] / 2)
                self.driver.tap([(cx, cy)])
            except Exception:
                try:
                    els[0].click()  # 兜底（该 RN tab 上通常无效，仅作保险）
                except Exception:
                    pass
            time.sleep(2.5)
            if self._on_account_page():
                print(f"已切换到帐户页（第 {i + 1} 次点击）")
                return True
        return self._on_account_page()

    def _dismiss_bluetooth_popup(self, max_tries=6):
        """退出会覆盖首页、拦截 tab 点击的“添加新设备/蓝牙搜索”全屏页。

        这是 logout 卡在“进入账户设置失败”的主因。用系统返回键逐次退出，直到该页消失。

        隐式等待临时压到 1s（不是 0/10）：既能探到已渲染的干扰界面，
        又不会在界面不存在时与 10s 隐式等待叠加造成空转。延迟弹出的情况由
        调用方（_tap_account_tab 每轮重检）覆盖。
        """
        import time
        try:
            self.driver.implicitly_wait(1)
        except Exception:
            pass
        try:
            for _ in range(max_tries):
                if not self._add_device_page_present():
                    return True
                try:
                    self.driver.back()
                    print("已用返回键退出“添加新设备”页")
                    time.sleep(1.5)
                except Exception:
                    break

            # 兜底：坐标点击原蓝牙关闭控件（若仍残留）
            elems = self.driver.find_elements(*self.BLUETOOTH_CLOSE)
            if elems:
                el = elems[0]
                loc, size = el.location, el.size
                cx = int(loc["x"] + size["width"] / 2)
                cy = int(loc["y"] + size["height"] / 2)
                try:
                    self.driver.tap([(cx, cy)])
                    time.sleep(1.5)
                    print(f"已尝试坐标点击关闭蓝牙弹窗: ({cx},{cy})")
                except Exception:
                    pass
            return not self._add_device_page_present()
        except Exception:
            return False
        finally:
            try:
                self.driver.implicitly_wait(10)
            except Exception:
                pass

    def _open_account_settings(self):
        """点击资料头部进入“账户设置”页；实测点击邮箱文本最稳，vg14 索引为兜底。返回是否成功。"""
        for by, val in [self.PROFILE_EMAIL, self.ACCOUNT_SETTINGS]:
            try:
                self.click(by, val)
            except Exception:
                continue
            if self.is_displayed(*self.ACCOUNT_SETTINGS_TITLE, timeout=5):
                return True
        return self.is_displayed(*self.ACCOUNT_SETTINGS_TITLE, timeout=1)

    def _tap_logout_entry(self):
        """在账户设置页点击“退出登录”（必要时上滑露出）。返回是否点击成功。"""
        for _ in range(3):
            if self.is_displayed(*self.LOGOUT_BUTTON, timeout=2):
                try:
                    self.click(*self.LOGOUT_BUTTON)
                    return True
                except Exception:
                    pass
            self.swipe_up()
        return False

    def _confirm_logout(self):
        """点击确认弹窗中的“退出登录”。

        弹窗确认按钮在上方(y 更小)，设置页按钮在下方；取最上面一个即确认按钮，
        避免误点背景里的设置页按钮。
        """
        try:
            els = self.driver.find_elements(*self.LOGOUT_BUTTON)
        except Exception:
            els = []
        if not els:
            return False
        target = min(els, key=lambda e: (e.location or {}).get("y", 0)) if len(els) > 1 else els[0]
        try:
            target.click()
            return True
        except Exception:
            return False

    def _save_diagnostics(self, reason="diag"):
        """保存 page_source 与截图到 reports/ 目录，便于排查（不使用 adb 回退）。"""
        os.makedirs("reports", exist_ok=True)
        ts = int(time.time())
        src_path = f"reports/page_source_{reason}_{ts}.xml"
        img_path = f"reports/screenshot_{reason}_{ts}.png"
        try:
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        except Exception as e:
            print(f"保存 page_source 失败: {e}")
        try:
            self.driver.save_screenshot(img_path)
        except Exception as e:
            print(f"保存截图失败: {e}")
        print(f"已保存诊断文件（若可用）: {src_path}, {img_path}")

    # 已移除 adb 回退与 driver 重建等恢复逻辑，保留简洁的诊断保存
