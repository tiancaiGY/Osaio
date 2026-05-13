"""设备控制页面"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


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
