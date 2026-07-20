"""云卡回放（Cloud / SD Playback）页面对象。

场景（用户定义，账号 ocn03@bccto.cc，存在在线设备且直播正常）：
  首页设备卡 → 进入直播页（出图：xp_live_player_bit_rate）
  → 直播页下方**事件列表**（yr_xplayer_playback_video_list_rv，条目 yr_xplayer_event_item_bg）
  → 点第一条事件 → 播放**云回放**，出图正常（bit_rate 出现）即通过
  → 点**时间轴切换**按钮（xp_playback_header_bar_nav_play_mode）→ 滑动下方时间轴 → 出图正常
  → 切**卡回放**（xp_playback_header_bar_nav_sd）/ **云回放**（xp_playback_header_bar_nav_cloud）→ 各自出图正常
  → **回到直播**（xp_player_control_panel_go_live）→ 出图正常

真机确认（cap_live_view）：直播页会完整暴露上述 id；出图统一以 bit_rate(LIVE_BIT) 是否出现判定。
注意：睡眠中的设备卡“播放按钮”对程序化点击不敏感，进入直播需先唤醒/重试（见 enter_live_view）。
"""
import os
import time

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
from pages.device_page import DevicePage
from pages.home_page import HomePage


class PlaybackPage(BasePage):
    # 出图判定（复用 DevicePage 的正确包名 id）
    LIVE_BIT = DevicePage.LIVE_BIT          # xp_live_player_bit_rate —— 出图标志
    LIVE_VIEW = DevicePage.LIVE_VIEW        # player_render_view
    LIVE_LOG = DevicePage.LIVE_LOG          # xp_live_player_stream_tag

    # 事件列表 & 事件条目
    EVENT_LIST = (AppiumBy.ID, "com.afar.osaio:id/yr_xplayer_playback_video_list_rv")
    EVENT_ITEM = (AppiumBy.ID, "com.afar.osaio:id/yr_xplayer_event_item_bg")

    # 回放头部导航按钮（用户提供的 id）
    NAV_PLAY_MODE = (AppiumBy.ID, "com.afar.osaio:id/xp_playback_header_bar_nav_play_mode")  # 时间轴切换
    NAV_SD = (AppiumBy.ID, "com.afar.osaio:id/xp_playback_header_bar_nav_sd")                # 卡回放
    NAV_CLOUD = (AppiumBy.ID, "com.afar.osaio:id/xp_playback_header_bar_nav_cloud")          # 云回放
    GO_LIVE = (AppiumBy.ID, "com.afar.osaio:id/xp_player_control_panel_go_live")             # 回到直播

    def __init__(self, driver):
        super().__init__(driver)
        self._home = HomePage(driver)

    # -------------------------------------------------- 通用助手
    def _coord_tap(self, el):
        r = el.rect
        self.driver.tap([(int(r["x"] + r["width"] / 2), int(r["y"] + r["height"] / 2))])

    def _tap_id(self, locator, timeout=8):
        """等待某 id 出现后点击（优先 element.click，失败退坐标点击）。"""
        if not self.is_displayed(*locator, timeout=timeout):
            return False
        els = self.driver.find_elements(*locator)
        if not els:
            return False
        try:
            els[0].click()
        except Exception:
            self._coord_tap(els[0])
        return True

    def _save_diag(self, reason):
        try:
            os.makedirs("reports", exist_ok=True)
            ts = int(time.time())
            with open(f"reports/page_source_playback_{reason}_{ts}.xml", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.driver.save_screenshot(f"reports/screenshot_playback_{reason}_{ts}.png")
            print(f"已保存回放诊断: reports/*playback_{reason}_{ts}.*")
        except Exception as e:
            print(f"保存回放诊断失败: {e}")

    def verify_stream(self, timeout=25):
        """出图判定：检测到 bit_rate（或视频渲染/日志）即视为出图正常。"""
        ok = (self.is_displayed(*self.LIVE_BIT, timeout=timeout)
              or self.is_displayed(*self.LIVE_VIEW, timeout=5)
              or self.is_displayed(*self.LIVE_LOG, timeout=5))
        return ok

    # -------------------------------------------------- 进入直播
    def enter_live_view(self, timeout=60):
        """从首页设备卡进入直播页。

        真机要点（用户确认）：
        - 首页会**反复弹出“发现蓝牙设备”弹窗**遮住中间的播放键，必须在每次点击**前**关闭；
        - 进入直播后**默认自动播放**直播内容（出图即 bit_rate 出现），无需再手动播放。
        睡眠设备的卡播放键对程序化点击不敏感，故多策略重试：关弹窗 → 点缩略图中心(播放键)
        → 退化点卡可点区域 → 直到出现 bit_rate。
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.is_displayed(*self.LIVE_BIT, timeout=2):
                # 出图后再清一次“直播前置”：首次进直播的升级弹窗/引导可能浮在直播画面上，
                # 不清掉会挡住后续事件列表/回放控件的点击。
                self._home.dismiss_live_view_intro()
                return True
            # 每轮先关“直播前置”（设备升级弹窗 + 引导流程）与“发现蓝牙设备”权限弹窗
            # （都会反复出现、遮挡设备卡/播放键）
            self._home.dismiss_live_view_intro()
            self._home.dismiss_permission_dialogs()
            # 找首页设备卡（列表区较宽的可点 ViewGroup），点其中心（缩略图/播放键）
            vgs = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().className("android.view.ViewGroup").clickable(true)')
            cards = []
            for e in vgs:
                try:
                    r = e.rect
                except Exception:
                    continue
                if r["width"] > 800 and 300 < r["y"] < 2200 and r["height"] > 200:
                    cards.append((r["y"], e, r))
            if cards:
                cards.sort()
                _, el, r = cards[0]
                # 先点缩略图中心（播放键），再退化点元素
                self.driver.tap([(int(r["x"] + r["width"] / 2), int(r["y"] + r["height"] / 2))])
                time.sleep(6)
                # 点进设备后，首次进直播会弹“设备升级弹窗 + 引导流程”，必须**在本轮**就地清理，
                # 否则它们盖住直播画面 → 下面出图判定永远为 False（等到下一轮再清则预算已耗尽）。
                self._home.dismiss_live_view_intro()
                if self.is_displayed(*self.LIVE_BIT, timeout=3):
                    return True
                try:
                    el.click()
                    time.sleep(6)
                    self._home.dismiss_live_view_intro()
                except Exception:
                    pass
            time.sleep(2)
        self._save_diag("enter_live_failed")
        return False

    # -------------------------------------------------- 回放各场景
    def play_first_event(self):
        """点击事件列表第一条事件 → 播放云回放；出图即通过。"""
        if not self.is_displayed(*self.EVENT_LIST, timeout=10):
            self._save_diag("no_event_list")
            return False
        items = self.driver.find_elements(*self.EVENT_ITEM)
        if not items:
            self._save_diag("no_event_items")
            return False
        # 取列表内第一条（y 最小）
        items.sort(key=lambda e: (e.location or {}).get("y", 0))
        self._coord_tap(items[0])
        time.sleep(5)
        if not self.verify_stream():
            self._save_diag("event_play_no_stream")
            return False
        return True

    def switch_timeline_and_swipe(self):
        """点时间轴切换按钮 → 滑动下方时间轴 → 出图正常。"""
        if not self._tap_id(self.NAV_PLAY_MODE, timeout=8):
            self._save_diag("no_play_mode_btn")
            return False
        time.sleep(3)
        # 滑动下方时间轴（屏幕下半部水平滑动）
        size = self.driver.get_window_size()
        y = int(size["height"] * 0.8)
        x1, x2 = int(size["width"] * 0.7), int(size["width"] * 0.3)
        try:
            self.driver.swipe(x1, y, x2, y, 800)
        except Exception:
            pass
        time.sleep(4)
        if not self.verify_stream():
            self._save_diag("timeline_no_stream")
            return False
        return True

    def switch_to_sd(self):
        """切换到卡回放（SD）→ 出图正常。"""
        if not self._tap_id(self.NAV_SD, timeout=8):
            self._save_diag("no_sd_btn")
            return False
        time.sleep(5)
        if not self.verify_stream():
            self._save_diag("sd_no_stream")
            return False
        return True

    def switch_to_cloud(self):
        """切换到云回放（Cloud）→ 出图正常。"""
        if not self._tap_id(self.NAV_CLOUD, timeout=8):
            self._save_diag("no_cloud_btn")
            return False
        time.sleep(5)
        if not self.verify_stream():
            self._save_diag("cloud_no_stream")
            return False
        return True

    def back_to_live(self):
        """点“回到直播”→ 出图正常。"""
        if not self._tap_id(self.GO_LIVE, timeout=8):
            self._save_diag("no_go_live_btn")
            return False
        time.sleep(5)
        if not self.verify_stream():
            self._save_diag("golive_no_stream")
            return False
        return True
