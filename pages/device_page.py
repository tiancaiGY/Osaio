"""设备控制页面"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
import re


class DevicePage(BasePage):
    # 元素定位 - 需要用 Appium Inspector 确认实际 ID
    DEVICE_NAME = (AppiumBy.ID, "com.osaio.app:id/tv_device_name")
    LIVE_VIEW_BTN = (AppiumBy.ID, "com.osaio.app:id/btn_live_view")
    LIVE_LOG = (AppiumBy.ID, "com.afar.osaio:id/xp_live_player_stream_tag")
    LIVE_BIT = (AppiumBy.ID, "com.afar.osaio:id/xp_live_player_bit_rate")
    LIVE_VIEW = (AppiumBy.ID, "com.afar.osaio:id/player_render_view")
    SETTINGS_BTN = (AppiumBy.ID, "com.osaio.app:id/btn_settings")
    WAVEOUT_BTN = (AppiumBy.ID, "com.afar.osaio:id/xp_player_control_panel_waveout")

    def get_device_name(self):
        return self.find(*self.DEVICE_NAME).text

    def open_live_view(self):
        self.click(*self.LIVE_VIEW_BTN)

    def open_settings(self):
        self.click(*self.SETTINGS_BTN)

    def toggle_mute(self):
        self.click(*self.MUTE_BTN)

    def _is_likely_device_name(self, text: str) -> bool:
        """基于文本规则判断该文本是否可能为设备名称，过滤权限/通知文案。"""
        if not text:
            return False
        t = text.strip()
        if len(t) < 2 or len(t) > 60:
            return False

        # 黑名单关键词，包含常见权限/通知提示词
        blacklist = [
            "allow", "notification", "notifications", "允许", "不允许",
            "permission", "权限", "allow osaio", "send you notifications"
        ]
        low = t.lower()
        for b in blacklist:
            if b in low:
                return False

        # 设备名通常包含字母或数字
        if re.search(r"[A-Za-z0-9]+", t):
            return True
        return False

    def find_device_elements(self):
        """尝试多策略定位设备列表的元素，返回可能的设备元素列表（可能为空）。"""
        driver = self.driver

        # 1) 优先尝试通过已知 resource-id 或定位器
        try:
            els = driver.find_elements(*self.DEVICE_NAME)
            filtered = [e for e in els if self._is_likely_device_name(getattr(e, 'text', '') or e.text)]
            if filtered:
                return filtered
        except Exception:
            pass

        # 2) 尝试 RecyclerView 下的 TextView（常见设备列表容器）
        try:
            els = driver.find_elements("xpath", "//androidx.recyclerview.widget.RecyclerView//android.widget.TextView")
            filtered = [e for e in els if self._is_likely_device_name(getattr(e, 'text', '') or e.text)]
            if filtered:
                return filtered
        except Exception:
            pass

        # 3) 最后退化为页面上所有 TextView 的筛选，但会过滤掉黑名单文本
        try:
            els = driver.find_elements("xpath", "//android.widget.TextView")
            filtered = [e for e in els if self._is_likely_device_name(getattr(e, 'text', '') or e.text)]
            return filtered
        except Exception:
            return []
