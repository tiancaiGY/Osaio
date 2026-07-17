"""蓝牙配网页面对象

覆盖从「进入配网」到「直播出图」的完整流程，以及测试前置的「解绑设备」。

设计要点（均源自真机逐页探查 + 现有代码约定）：
- 文本标记一律**中英双语**匹配（textMatches 正则），系统语言中/英均可跑。
- RN 元素 element.click() 常无效，统一用坐标点击 el.rect 中心（复用 AccountPage 技法）。
- 否定探测临时把隐式等待压到 1s、finally 恢复 10s，避免与 10s 隐式等待叠加空转。
- 失败自存诊断（reports/page_source_*.xml + 截图），测试层只需 assert。
- 直播出图定位只用正确包名 com.afar.osaio 的 id（复用 DevicePage）。

真机确认的流程：
  首页弹窗「添加设备/Add Device」或右上「+」
    → 连接中「正在连接/Connecting」（自动，成功→网络选择，失败→连接失败页）
    → 网络选择「选择网络/Select Network」→ 选中 WiFi(mmm_test)
    → 「连接到Wi-Fi/Connect to Wi-Fi」：3 个 EditText（[0]名称已填、[1]密码、[2]确认密码）→ 下一步/Next
    → 配对「配对/Pairing」（~120s，成功→命名页）
    → 「设备昵称/Device Nickname」：EditText[0] 昵称 → 下一步/Next
    → 直播页「Live」出图（player_render_view / xp_live_player_stream_tag）
解绑：设备卡 → 直播页齿轮(xp_header_bar_nav_right) → 设置上滑到底「移除/Remove」→ 确认弹窗「移除/Remove」
"""
import os
import re
import time
import random
import string

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
from pages.account_page import AccountPage
from pages.device_page import DevicePage


def _tm(pattern):
    """构造中英双语 textMatches 定位器（忽略大小写，包含匹配）。"""
    return (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i).*(%s).*")' % pattern)


class NetworkConfigPage(BasePage):
    # ---- 里程碑文本标记（中英双语，用于判定“已到达某页”）----
    ADD_DEVICE_BTN = _tm("添加设备|Add Device")
    DEVICE_FOUND = _tm("设备已找到|点击继续|Device found|tap to continue")
    CONNECTING = _tm("正在连接|Connecting")
    CONNECT_FAILED = _tm("连接失败|Connect failed|Connection failed|failed to connect")
    SELECT_NETWORK = _tm("选择网络|Select Network")
    WIFI_PWD_PAGE = _tm("连接到\\s*Wi-?Fi|Connect to\\s*Wi-?Fi|Selected Network|已选网络")
    PAIRING = _tm("配对|Pairing")
    NICKNAME_PAGE = _tm("设备昵称|设备名称|命名|Device Nickname|nickname")
    NEXT_BTN = _tm("下一步|Next|连接|确定|Done|完成")

    # ---- 直播出图（正确包名 id，复用 DevicePage）----
    LIVE_VIEW = DevicePage.LIVE_VIEW          # com.afar.osaio:id/player_render_view
    LIVE_LOG = DevicePage.LIVE_LOG            # com.afar.osaio:id/xp_live_player_stream_tag
    LIVE_BIT = DevicePage.LIVE_BIT            # com.afar.osaio:id/xp_live_player_bit_rate
    WAVEOUT_BTN = DevicePage.WAVEOUT_BTN      # com.afar.osaio:id/xp_player_control_panel_waveout

    # ---- 解绑设备相关 ----
    DEVICE_SETTINGS_GEAR = (AppiumBy.ID, "com.afar.osaio:id/xp_header_bar_nav_right")
    SETTINGS_TITLE = _tm("^设置$|^Settings$|设备设置")
    REMOVE_ENTRY = _tm("移除|删除设备|删除|Remove|Delete")
    REMOVE_CONFIRM_TITLE = _tm("确定.*移除|确定.*删除|sure.*remove|sure.*delete|remove the device")
    WIFI_NAME_DEFAULT = "mmm_test"
    WIFI_PWD_DEFAULT = "mmmmmmmm"

    def __init__(self, driver):
        super().__init__(driver)
        self.last_nickname = None
        self._account = AccountPage(driver)  # 复用弹窗关闭

    # ======================= 通用助手 =======================

    def _coordinate_tap(self, el):
        """坐标点击元素中心（RN 元素 element.click() 常无效）。"""
        r = el.rect
        cx = int(r["x"] + r["width"] / 2)
        cy = int(r["y"] + r["height"] / 2)
        self.driver.tap([(cx, cy)])

    def _present(self, locator, timeout=1):
        """否定探测：压低隐式等待，find_elements 找不到即刻返回 False。"""
        try:
            self.driver.implicitly_wait(timeout)
        except Exception:
            pass
        try:
            return bool(self.driver.find_elements(*locator))
        finally:
            try:
                self.driver.implicitly_wait(10)
            except Exception:
                pass

    def _wait_present(self, locator, timeout=15, interval=1.0):
        """轮询等待某定位器出现，返回 bool。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._present(locator, timeout=1):
                return True
            time.sleep(interval)
        return False

    def _wait_any(self, locators, timeout=30, interval=1.0):
        """轮询等待多个定位器中任一出现，返回命中的下标；超时返回 None。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            for i, loc in enumerate(locators):
                if self._present(loc, timeout=1):
                    return i
            time.sleep(interval)
        return None

    def _tap_locator(self, locator, timeout=10):
        """等待并坐标点击某定位器的第一个元素，返回 bool。"""
        if not self._wait_present(locator, timeout=timeout):
            return False
        els = self.driver.find_elements(*locator)
        if not els:
            return False
        self._coordinate_tap(els[0])
        return True

    def _save_diagnostics(self, reason="netcfg"):
        """保存 page_source 与截图到 reports/（复用 AccountPage 约定）。"""
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
        print(f"已保存诊断文件: {src_path}, {img_path}")

    def _dismiss_popup(self):
        """关闭首页“发现设备/添加设备”弹窗（复用 AccountPage 逻辑）。"""
        try:
            self._account._dismiss_bluetooth_popup()
        except Exception:
            pass

    def _tap_top_right_plus(self):
        """点击首页右上角“+”（最右上的小方块 ViewGroup），坐标点击。"""
        vgs = self.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.view.ViewGroup").clickable(true)')
        cand = []
        for e in vgs:
            try:
                r = e.rect
            except Exception:
                continue
            if r["y"] < 300 and r["width"] < 200 and r["height"] < 200:
                cand.append((r["x"], e))
        if not cand:
            return False
        cand.sort()
        self._coordinate_tap(cand[-1][1])  # 最右 = +（左边是铃铛）
        return True

    # ======================= 入口 =======================

    def enter_via_home_popup(self, timeout=30):
        """入口 A：等待首页配网弹窗出现，点击“添加设备/Add Device”。

        弹窗延迟出现（调用方应已先 restart_app 复现首次进首页）。
        点击后设备会自动进入“正在连接”，无需再选设备列表。
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._present(self.ADD_DEVICE_BTN, timeout=1):
                if self._tap_locator(self.ADD_DEVICE_BTN, timeout=3):
                    # 进入连接中或直接网络选择均算成功进入配网
                    if self._wait_any([self.CONNECTING, self.SELECT_NETWORK,
                                       self.CONNECT_FAILED], timeout=15) is not None:
                        return True
            time.sleep(2)
        self._save_diagnostics("entryA_popup_not_found")
        return False

    def enter_via_plus(self, timeout=15):
        """入口 B：点右上角“+”进入配网。"""
        self._dismiss_popup()  # 先关掉可能抢焦点的弹窗
        if not self._tap_top_right_plus():
            self._save_diagnostics("entryB_plus_not_found")
            return False
        time.sleep(3)
        # “+”可能进入“设备已找到”列表页，或直接连接
        if self._wait_any([self.DEVICE_FOUND, self.CONNECTING,
                           self.SELECT_NETWORK], timeout=timeout) is not None:
            return True
        self._save_diagnostics("entryB_no_provision_page")
        return False

    # ======================= 后续流程 =======================

    def select_first_found_device(self, timeout=20):
        """“设备已找到”页选中列表第一个设备（自动进入连接中）。

        入口 A（弹窗点添加设备）通常已直接连接、跳过此页；此时若已在连接中/网络选择页
        则视为已通过，直接返回 True。
        """
        # 已越过设备列表（已在连接中/网络选择）→ 通过
        if self._present(self.CONNECTING, timeout=1) or self._present(self.SELECT_NETWORK, timeout=1):
            return True
        if not self._wait_present(self.DEVICE_FOUND, timeout=timeout):
            # 没有独立的设备列表页也可能正常（弹窗已选定设备）
            if self._present(self.CONNECTING, timeout=2) or self._present(self.SELECT_NETWORK, timeout=2):
                return True
            self._save_diagnostics("device_found_missing")
            return False
        # 取页面中部第一个较大的可点击项作为设备行
        rows = self.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().clickable(true)')
        rows = [e for e in rows if _row_is_device_candidate(e)]
        if not rows:
            self._save_diagnostics("no_device_rows")
            return False
        rows.sort(key=lambda e: (e.rect or {}).get("y", 0))
        self._coordinate_tap(rows[0])
        time.sleep(3)
        return True

    def wait_connecting_result(self, timeout=40):
        """等待连接结果：成功进入网络选择页，失败进入“连接失败”页（视为失败）。"""
        idx = self._wait_any([self.SELECT_NETWORK, self.WIFI_PWD_PAGE, self.CONNECT_FAILED],
                             timeout=timeout)
        if idx is None:
            self._save_diagnostics("connecting_no_result")
            return False
        if idx == 2:  # 连接失败
            self._save_diagnostics("connect_failed")
            return False
        return True

    def select_wifi(self, name=None, timeout=25):
        """网络选择页选中目标 WiFi（默认 mmm_test），滚动查找。"""
        name = name or self.WIFI_NAME_DEFAULT
        sel = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("%s")' % name)
        deadline = time.time() + timeout
        while time.time() < deadline:
            els = self.driver.find_elements(*sel)
            if els:
                self._coordinate_tap(els[0])
                if self._wait_present(self.WIFI_PWD_PAGE, timeout=10):
                    return True
                # 点击后未进入密码页，重试
            self.swipe_up()
            time.sleep(1)
        self._save_diagnostics("wifi_not_found_%s" % name)
        return False

    def input_wifi_password(self, pwd=None):
        """“连接到Wi-Fi”页填写密码。

        真机实测该页有 3 个 EditText：[0]=WiFi名称(已自动填充)、[1]=密码、[2]=确认密码。
        故对索引 >=1 的输入框都填入密码；若只有 2 个则填 [0]、[1]（兼容不同版本）。
        """
        pwd = pwd or self.WIFI_PWD_DEFAULT
        if not self._wait_present(self.WIFI_PWD_PAGE, timeout=10):
            self._save_diagnostics("wifi_pwd_page_missing")
            return False
        eds = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        if len(eds) < 2:
            self._save_diagnostics("pwd_fields_lt2")
            return False
        # 3 个：跳过名称框，填 [1]、[2]；2 个：填 [0]、[1]
        targets = eds[1:] if len(eds) >= 3 else eds[:2]
        for e in targets:
            try:
                e.clear()
                e.send_keys(pwd)
            except Exception as ex:
                print(f"填写密码框失败: {ex}")
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass
        time.sleep(1)
        if not self._tap_locator(self.NEXT_BTN, timeout=5):
            self._save_diagnostics("pwd_next_missing")
            return False
        return True

    def wait_pairing_result(self, timeout=120):
        """配对页（~120s）：成功进入设备命名页；超时视为失败。"""
        # best-effort 确认进入配对页
        self._present(self.PAIRING, timeout=3)
        idx = self._wait_any([self.NICKNAME_PAGE], timeout=timeout, interval=2.0)
        if idx is None:
            self._save_diagnostics("pairing_timeout")
            return False
        return True

    def set_random_nickname(self):
        """设备命名页：随机命名 → 下一步。"""
        if not self._wait_present(self.NICKNAME_PAGE, timeout=10):
            self._save_diagnostics("nickname_page_missing")
            return False
        eds = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        if not eds:
            self._save_diagnostics("nickname_field_missing")
            return False
        name = "T" + "".join(random.choices(string.ascii_letters + string.digits, k=6))
        try:
            eds[0].clear()
            eds[0].send_keys(name)
        except Exception as ex:
            print(f"填写昵称失败: {ex}")
            self._save_diagnostics("nickname_input_failed")
            return False
        self.last_nickname = name
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass
        time.sleep(1)
        if not self._tap_locator(self.NEXT_BTN, timeout=5):
            self._save_diagnostics("nickname_next_missing")
            return False
        return True

    def verify_live_view(self, timeout=30):
        """直播页出图验证：检测视频渲染/码率/控制按钮（正确包名 id）。"""
        ok = (self.is_displayed(*self.LIVE_VIEW, timeout=timeout)
              or self.is_displayed(*self.LIVE_LOG, timeout=5)
              or self.is_displayed(*self.LIVE_BIT, timeout=5)
              or self.is_displayed(*self.WAVEOUT_BTN, timeout=5))
        if not ok:
            self._save_diagnostics("live_view_no_stream")
        return ok

    # ======================= 解绑（测试前置） =======================

    # 首页“无设备”空状态标记（新注册账号）：出现即表示无可解绑设备，直接通过。
    NO_DEVICE_MARKERS = _tm("Add your first device|No devices|无设备|暂无设备|添加第一个设备")

    def unbind_device_if_present(self, timeout=8):
        """若首页存在已配网设备卡片，进入设备设置删除它，恢复未配网可搜到状态。

        无已配网设备则直接返回 True。用于两个测试互不干扰。
        """
        self._dismiss_popup()
        # 空状态（新注册账号“Add your first device / No devices”）→ 无设备可解绑，直接通过。
        # 否则订阅横幅/空态卡片会被 _find_device_card 误判为设备卡而进入失败。
        if self._present(self.NO_DEVICE_MARKERS, timeout=2):
            print("首页为无设备空状态，跳过解绑")
            return True
        card = self._find_device_card()
        if not card:
            return True  # 无已配网设备
        self._coordinate_tap(card)
        time.sleep(4)
        # 进入设备设置（齿轮）
        gear = self.driver.find_elements(*self.DEVICE_SETTINGS_GEAR)
        if not gear:
            self._save_diagnostics("unbind_no_gear")
            self.driver.back()
            return False
        self._coordinate_tap(gear[0])
        if not self._wait_present(self.SETTINGS_TITLE, timeout=8):
            self._save_diagnostics("unbind_no_settings")
            return False
        # 上滑到底找到“移除/Remove”
        for _ in range(6):
            if self._present(self.REMOVE_ENTRY, timeout=1):
                break
            self.swipe_up()
            time.sleep(0.5)
        if not self._tap_locator(self.REMOVE_ENTRY, timeout=3):
            self._save_diagnostics("unbind_no_remove_entry")
            return False
        # 确认弹窗：点最上方的“移除/Remove”（弹窗按钮在设置页按钮之上）
        self._wait_present(self.REMOVE_CONFIRM_TITLE, timeout=5)
        confirm = self.driver.find_elements(*self.REMOVE_ENTRY)
        if confirm:
            target = min(confirm, key=lambda e: (e.location or {}).get("y", 0)) \
                if len(confirm) > 1 else confirm[0]
            self._coordinate_tap(target)
            time.sleep(4)
        # 验证回到首页且设备已移除（弹窗关闭后再确认）
        self._dismiss_popup()
        return not bool(self._find_device_card())

    def _find_device_card(self):
        """定位首页已配网设备卡片（中部较大的可点击 ViewGroup，排除弹窗）。返回元素或 None。"""
        # 弹窗存在时先不判定（避免误点弹窗里的设备）
        if self._account._add_device_page_present():
            self._dismiss_popup()
        vgs = self.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.view.ViewGroup").clickable(true)')
        cards = []
        for e in vgs:
            try:
                r = e.rect
            except Exception:
                continue
            # 设备卡片：宽度大、位于列表区域（y 500~2400）
            if r["width"] > 1000 and 500 < r["y"] < 2400 and r["height"] > 300:
                cards.append((r["y"], e))
        if not cards:
            return None
        cards.sort()
        return cards[0][1]


def _row_is_device_candidate(el):
    """判断某可点击元素是否像“设备列表行”（中部、较宽）。"""
    try:
        r = el.rect
    except Exception:
        return False
    return 500 < r["y"] < 2300 and r["width"] > 200
