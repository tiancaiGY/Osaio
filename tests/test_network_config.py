"""蓝牙配网流程测试

前提：已获取蓝牙权限、已登录、在首页；待配网 IoT 设备处于配对模式并在蓝牙范围内；
     目标 WiFi（mmm_test / mmmmmmmm，2.4GHz）在附近。

覆盖两种配网入口，均走同一套后续流程直到直播出图：
  入口 A：首次进首页 → 配网弹窗 → 「添加设备」
  入口 B：右上角「+」→ 配网页

设计：
- 每个测试前先 unbind_device_if_present，把上次配网的设备解绑，保证设备可被重新搜到，
  两个测试互不干扰（配网成功会把设备绑定到账号）。
- 连接失败 / 配对 120s 超时 → 页对象内已存诊断，测试层 assert 失败。
- 文本定位中英双语兼容（系统语言中/英均可跑）。
"""
import pytest

from pages.login_page import LoginPage
from pages.network_config_page import NetworkConfigPage

WIFI_NAME = "mmm_test"
WIFI_PWD = "mmmmmmmm"


@pytest.mark.network
class TestNetworkConfig:
    """蓝牙配网主流程测试。"""

    def _login_home_and_reset(self, driver, account):
        """前置：登录进首页，并解绑已配网设备（恢复可搜到状态）。"""
        primary = account("primary")
        login_page = LoginPage(driver)
        try:
            login_page.skip_onboarding()
        except Exception:
            pass
        home = login_page.smart_login(
            account=primary.account,
            password=primary.password,
            force_login=False,
        )
        assert home.is_home_displayed(), "登录后未进入首页"

        # 解绑上次配网的设备，确保本次能重新搜到并配网
        ncp = NetworkConfigPage(driver)
        assert ncp.unbind_device_if_present(), "前置解绑设备失败：设备可能仍绑定，导致搜不到待配网设备"
        return home, ncp

    def _run_provision_flow(self, ncp):
        """两种入口共用的配网后续流程：选设备→连接→选WiFi→填密码→配对→命名→出图。"""
        assert ncp.select_first_found_device(), "未能在“设备已找到”列表中选择第一个设备"
        assert ncp.wait_connecting_result(), "连接设备失败（进入“连接失败”页或连接超时）"
        assert ncp.select_wifi(WIFI_NAME), f"未能在WiFi列表中选择 {WIFI_NAME}"
        assert ncp.input_wifi_password(WIFI_PWD), "填写WiFi密码（密码+确认密码）或点击下一步失败"
        assert ncp.wait_pairing_result(timeout=120), "配对超时（120秒内未进入设备命名页）"
        assert ncp.set_random_nickname(), "设置设备随机名称并点击“下一步”失败"
        assert ncp.verify_live_view(), "直播页出图异常（未检测到视频渲染/码率/控制按钮）"
        print(f"✓ 配网成功，设备昵称: {ncp.last_nickname}")

    def test_network_config_via_home_popup(self, driver, account):
        """入口 A：首页配网弹窗 → 添加设备 → 完成配网出图。"""
        print("=== 配网入口A：首页弹窗“添加设备” ===")
        _, ncp = self._login_home_and_reset(driver, account)

        # 重启 App 复现“首次进首页”，触发配网弹窗（弹窗延迟出现）
        ncp.restart_app()

        assert ncp.enter_via_home_popup(), "入口A：未等到配网弹窗或未能点击“添加设备”"
        self._run_provision_flow(ncp)
        print("=== 入口A 配网流程完成 ===")

    def test_network_config_via_plus_button(self, driver, account):
        """入口 B：右上角“+” → 配网页 → 完成配网出图。"""
        print("=== 配网入口B：右上角“+” ===")
        home, ncp = self._login_home_and_reset(driver, account)

        # 关闭可能的权限/通知弹窗，避免遮挡“+”
        try:
            home.dismiss_permission_dialogs()
        except Exception:
            pass

        assert ncp.enter_via_plus(), "入口B：点击右上角“+”未进入配网页"
        self._run_provision_flow(ncp)
        print("=== 入口B 配网流程完成 ===")
