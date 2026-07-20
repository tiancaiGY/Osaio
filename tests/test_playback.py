"""云卡回放测试（独立用例，使用账号 ocn03@bccto.cc）。

前置：真机、Appium(4723)、账号 ocn03@bccto.cc 下存在**在线设备**（GP5B）且直播正常、
      有云/卡录像与事件。

验证流程（出图统一以 xp_live_player_bit_rate 出现判定）：
  1. 登录 → 进入设备直播页（出图正常）
  2. 点直播页下方事件列表第一条事件 → 播放云回放，出图正常
  3. 点时间轴切换按钮 → 滑动时间轴 → 出图正常
  4. 切卡回放(SD) → 出图正常
  5. 切云回放(Cloud) → 出图正常
  6. 回到直播 → 出图正常

运行：
  pytest tests/test_playback.py -m playback -s --report-title "OSAIO 云卡回放测试报告"
"""
import time

import pytest

from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.playback_page import PlaybackPage


@pytest.mark.playback
class TestPlayback:
    """云/卡回放出图验证。"""

    def test_cloud_and_sd_playback(self, driver, account, report_step):
        cloud_acc = account("secondary")  # ocn03@bccto.cc / 123456（存在在线设备 GP5B）

        def step(name, fn):
            print(f"\n===== 步骤: {name} =====")
            s = time.time()
            try:
                fn()
            except pytest.skip.Exception as e:
                report_step(name, "skipped", time.time() - s, str(e)); raise
            except Exception as e:
                report_step(name, "failed", time.time() - s, str(e))
                print(f"✗ 失败: {name} -> {e}"); raise
            else:
                report_step(name, "passed", time.time() - s)
                print(f"✓ 通过: {name}")

        login_page = LoginPage(driver)
        pb = PlaybackPage(driver)

        def _login_and_live():
            try:
                login_page.skip_onboarding()
            except Exception:
                pass
            home = login_page.smart_login(
                account=cloud_acc.account, password=cloud_acc.password, force_login=True)
            HomePage(driver).dismiss_permission_dialogs()
            assert home.is_home_displayed(), "登录后首页未显示"
            assert pb.enter_live_view(), "未能进入设备直播页（出图）"

        step("1. 登录并进入直播页（出图）", _login_and_live)
        step("2. 点事件播放云回放（出图）", lambda: _assert(pb.play_first_event(), "点击事件后云回放未出图"))
        step("3. 时间轴切换+滑动（出图）", lambda: _assert(pb.switch_timeline_and_swipe(), "时间轴回放未出图"))
        step("4. 切卡回放 SD（出图）", lambda: _assert(pb.switch_to_sd(), "卡回放未出图"))
        step("5. 切云回放 Cloud（出图）", lambda: _assert(pb.switch_to_cloud(), "云回放未出图"))
        step("6. 回到直播（出图）", lambda: _assert(pb.back_to_live(), "回到直播未出图"))

        print("\n===== 云卡回放验证完成 =====")


def _assert(ok, msg):
    assert ok, msg
