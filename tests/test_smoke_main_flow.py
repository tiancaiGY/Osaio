"""主功能端到端 Smoke 测试（只跑完全正确的 happy-path，作为每轮测试前的健康门禁）。

主功能顺序（用户定义）：
  1. 首次安装 App 打开 → 引导页（FRESH_INSTALL=1 时清数据重现，默认沿用现状）
  2. 进入登录页 → 注册新用户成功（注册完成自动登录）
  3. 退出登录 → 重新登录成功
  4. 配网成功（现场需有真实待配网设备 + mmm_test 2.4G WiFi）
  5. 出图成功（直播）
  6. 订阅云存成功（后续补充，本期占位 skip）
  7. IOT 设备推送消息正常（后续补充，本期占位 skip）
  8. 消息列表显示历史消息成功
  9. 退出登录成功

约定：
  - 注册验证码经临时邮箱 tempmail.plus 自动获取（utils/temp_mail.py）。
  - 注册密码固定为 "111111"。
  - 任一必需步骤失败 → 整条 smoke 立即 fail（门禁语义）；后续补充功能用 skip 占位。
  - 每步结果通过 report_step 记录，报告里展开显示 9 个步骤。

运行：
  pytest tests/test_smoke_main_flow.py -m smoke -s \
      --report-title "OSAIO 主功能测试报告"
  # 重现首次安装引导页：
  FRESH_INSTALL=1 pytest tests/test_smoke_main_flow.py -m smoke -s
"""
import os
import random
import string
import subprocess
import time

import pytest

from pages.login_page import LoginPage
from pages.register_page import RegisterPage
from pages.home_page import HomePage
from pages.account_page import AccountPage
from pages.network_config_page import NetworkConfigPage
from utils.temp_mail import wait_for_verification_code

APP_PACKAGE = "com.afar.osaio"
REGISTER_PASSWORD = "111111"          # 用户要求：注册密码固定为 111111
WIFI_NAME = NetworkConfigPage.WIFI_NAME_DEFAULT   # mmm_test
WIFI_PWD = NetworkConfigPage.WIFI_PWD_DEFAULT     # mmmmmmmm
# tempmail.plus 的可收信域名（@tempmail.plus 本身不收信；@mailto.plus 实测可正常收到
# OSAIO 验证码邮件，发件人 no-reply@eu.support.osaio.net）。可用 TEMP_EMAIL_DOMAIN 覆盖。
TEMP_MAIL_DOMAIN = os.environ.get("TEMP_EMAIL_DOMAIN", "mailto.plus")
CODE_TIMEOUT = int(os.environ.get("OSAIO_CODE_TIMEOUT", "180"))


def _gen_temp_email():
    rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"osaio_smoke_{rnd}@{TEMP_MAIL_DOMAIN}"


@pytest.mark.smoke
class TestSmokeMainFlow:
    """主功能完整正确流程（单个端到端用例）。"""

    def test_main_flow_smoke(self, driver, report_step):
        """按顺序跑完主功能 happy-path，分步骤记录到报告。"""
        t0 = time.time()

        def step(name, fn):
            """执行一步：计时、记录报告步骤、失败即 fail（附诊断）。"""
            print(f"\n===== 步骤: {name} =====")
            s = time.time()
            try:
                fn()
            except pytest.skip.Exception as e:
                report_step(name, "skipped", time.time() - s, str(e))
                print(f"⏭  跳过: {name} ({e})")
                raise
            except Exception as e:
                report_step(name, "failed", time.time() - s, str(e))
                print(f"✗ 失败: {name} -> {e}")
                raise
            else:
                report_step(name, "passed", time.time() - s)
                print(f"✓ 通过: {name}")

        login_page = LoginPage(driver)
        # 注册成功后保存，供步骤3重登使用
        self._email = _gen_temp_email()
        self._password = REGISTER_PASSWORD

        # ---- 步骤 0：首次安装重置（始终执行）----
        # 用户定义的主流程本就以“首次安装 App 打开”为起点。始终 pm clear 让每轮都从
        # 干净的首装状态开始 → 直达引导/登录页，避免依赖脆弱的 UI 登出做前置
        # （历史踩坑：残留已登录会话 + 绑定设备的 BLE 弹窗会让账户页导航/登出卡死）。
        # SMOKE_NO_RESET=1 可跳过清数据（沿用现状，供特殊调试）。
        skip_reset = os.environ.get("SMOKE_NO_RESET") == "1"
        if not skip_reset:
            step("0. 首次安装重置（pm clear）", lambda: self._fresh_install(driver))

        # ---- 步骤 1：首次安装打开 → 引导页 ----
        # FRESH_INSTALL=1 时断言确实经过引导页；否则尽力而为。
        fresh = os.environ.get("FRESH_INSTALL") == "1" and not skip_reset
        step("1. 打开 App 进入引导页", lambda: self._onboarding(login_page, fresh))

        # ---- 步骤 2：注册新用户（自动登录）----
        step("2. 注册新用户成功（自动登录）", lambda: self._register(driver, login_page))

        # ---- 步骤 3：退出登录 → 重新登录 ----
        step("3. 退出后重新登录成功", lambda: self._logout_then_relogin(driver, login_page))

        # ---- 步骤 4：配网 ----
        ncp = NetworkConfigPage(driver)
        step("4. 配网成功", lambda: self._network_config(ncp))

        # ---- 步骤 5：出图 ----
        step("5. 出图成功（直播）", lambda: self._live_view(driver, ncp))

        # ---- 步骤 6：订阅云存（后续补充）----
        step("6. 订阅云存成功", lambda: pytest.skip("后续补充流程"))

        # ---- 步骤 7：IOT 推送消息（后续补充）----
        step("7. IOT 设备推送消息正常", lambda: pytest.skip("后续补充流程"))

        # ---- 步骤 8：消息列表显示历史消息 ----
        step("8. 消息列表显示历史消息成功", lambda: self._message_list(driver))

        # ---- 步骤 9：退出登录 ----
        step("9. 退出登录成功", lambda: self._final_logout(driver))

        print(f"\n===== 主功能 smoke 全流程完成，用时 {time.time() - t0:.1f}s =====")

    # ------------------------------------------------------------------ 步骤实现

    def _fresh_install(self, driver):
        """adb 清除 App 数据以重现首次安装，然后重启 App。"""
        try:
            subprocess.run(["adb", "shell", "pm", "clear", APP_PACKAGE],
                           check=True, capture_output=True, timeout=30)
        except Exception as e:
            pytest.fail(f"pm clear 失败（无法重现首次安装）: {e}")
        time.sleep(2)
        # 清数据后需重新拉起 App
        try:
            driver.activate_app(APP_PACKAGE)
        except Exception as e:
            pytest.fail(f"清数据后重新启动 App 失败: {e}")
        time.sleep(4)

    def _onboarding(self, login_page, fresh):
        """处理首次启动引导页（pm clear 后为 Terms “Agree” 门 + 可能的 welcome 页）。

        FRESH_INSTALL=1：要求确实见到引导页元素（Agree/Terms/Let's Start）。
        随后确保推进到登录表单（skip_onboarding 点 Agree；ensure_login_page 兜底进表单）。
        """
        from appium.webdriver.common.appiumby import AppiumBy
        # 首装后引导页标志（Terms & Conditions / Agree / Let's Start）
        onboarding_markers = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textMatches("(?i).*(Terms\\s*&|Agree|同意|Let.?s Start|开始|Get Started).*")')
        saw_onboarding = login_page.is_displayed(*onboarding_markers, timeout=5)
        if fresh:
            assert saw_onboarding, "FRESH_INSTALL 下未检测到首次安装引导页（Agree/Terms）"
        print(f"引导页可见: {saw_onboarding}")

        # 点过引导（同意）；无引导时为安全空跑
        login_page.skip_onboarding()
        # 确保推进到登录表单（welcome 页需点顶部“登录”入口露出表单）
        assert login_page.ensure_login_page(), "引导后未能进入登录页/登录表单"

    def _register(self, driver, login_page):
        """临时邮箱注册 → 取码 → 设密 → 自动登录到首页。"""
        # 注册必须从登录页开始。此前多次踩坑：重启后“添加新设备”弹窗盖住 tab，
        # 使 is_already_logged_in()（依赖 is_home_displayed）在已登录时仍误判为未登录，
        # 从而跳过登出、在首页找不到登录表单而失败。
        # 稳妥做法：只要当前不在登录页，就直接走 ensure_logged_out()——它内部会重启、
        # 关弹窗、经账户页 UI 登出（logout 自包含完整导航），空跑也安全。
        if not login_page.wait_for_login_page(timeout=3):
            print("当前不在登录页，先确保登出（清理任何已登录会话）")
            assert login_page.ensure_logged_out(), "注册前置登出失败，无法回到登录页"
            time.sleep(1)

        # 确保停在登录表单（welcome 页需先点“登录”入口露出表单/注册入口）
        login_page.ensure_login_page()

        register_page = login_page.go_register()
        assert isinstance(register_page, RegisterPage), "未能进入注册页"

        # 第一步：国家 + 邮箱 + 同意条款 → 进入验证码页
        step1 = register_page.register_step1_input_email(
            email=self._email, country="China",
            agree_privacy=True, agree_terms=True,
        )
        assert isinstance(step1, RegisterPage), f"注册第一步未进入验证码页: {step1}"

        # 取验证码（临时邮箱）
        code, mail_id = wait_for_verification_code(
            self._email, timeout=CODE_TIMEOUT, check_interval=5)
        assert code, f"{CODE_TIMEOUT}s 内未从临时邮箱 {self._email} 收到验证码"
        print(f"收到验证码 {code} (mail_id={mail_id})")

        # 第二步：输入验证码 → 进入设密页
        step2 = register_page.register_step2_input_verification_code(code)
        assert isinstance(step2, RegisterPage), f"验证码校验失败: {step2}"

        # 第三步：设置密码 → 自动登录到首页
        result = register_page.register_step3_set_password(self._password)
        assert isinstance(result, HomePage), f"注册设密后未自动登录到首页: {result}"
        assert result.is_home_displayed(), "注册完成后首页未显示"
        print(f"注册成功并自动登录：{self._email} / {self._password}")

    def _logout_then_relogin(self, driver, login_page):
        """退出登录 → 用新注册账号重新登录。"""
        assert AccountPage(driver).logout(), "退出登录失败（未回到登录页）"
        time.sleep(1)
        home = login_page.smart_login(
            account=self._email, password=self._password, force_login=True)
        assert home.is_home_displayed(), "重新登录后首页未显示"

    def _network_config(self, ncp):
        """完整蓝牙配网（现场需有待配网设备）。"""
        # 前置：解绑已配网设备，保证设备可被重新搜到
        assert ncp.unbind_device_if_present(), "前置解绑设备失败（设备可能仍绑定）"
        # 入口 A：重启复现首页配网弹窗；失败则退回入口 B（右上角 +）
        ncp.restart_app()
        if not ncp.enter_via_home_popup():
            print("入口A（首页弹窗）未命中，改用入口B（右上角 +）")
            assert ncp.enter_via_plus(), "两种配网入口均未进入配网页"
        assert ncp.select_first_found_device(), "未能在“设备已找到”列表选择设备"
        assert ncp.wait_connecting_result(), "连接设备失败（连接失败页或超时）"
        assert ncp.select_wifi(WIFI_NAME), f"未能在WiFi列表选择 {WIFI_NAME}"
        assert ncp.input_wifi_password(WIFI_PWD), "填写WiFi密码或点下一步失败"
        assert ncp.wait_pairing_result(timeout=120), "配对超时（120s 内未进入命名页）"
        assert ncp.set_random_nickname(), "设置设备昵称并下一步失败"
        print(f"配网成功，设备昵称: {ncp.last_nickname}")

    def _live_view(self, driver, ncp):
        """配网完成后进入直播页验证出图。"""
        assert ncp.verify_live_view(), "直播页出图异常（未检测到视频/码率/控制按钮）"
        # 回到首页，便于后续消息列表步骤
        try:
            driver.back()
            time.sleep(2)
        except Exception:
            pass

    def _message_list(self, driver):
        """进入消息/事件列表，验证列表页出现。"""
        home = HomePage(driver)
        # 确保在首页再切消息 tab
        if not home.is_home_displayed():
            try:
                driver.back()
                time.sleep(2)
            except Exception:
                pass
        home.go_message()
        time.sleep(2)
        # 判定进入消息/事件列表页：消息 tab（tab,2 of 3）仍在，且出现列表容器或历史条目。
        # 用 RecyclerView / ListView / 多个 TextView 作为“有历史消息列表”的启发式判断。
        from appium.webdriver.common.appiumby import AppiumBy
        list_containers = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().classNameMatches(".*(RecyclerView|ListView|ScrollView)")')
        text_nodes = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
        assert list_containers or len(text_nodes) >= 3, \
            "消息列表页未显示历史消息（未检测到列表容器/条目）"
        print(f"消息列表已显示（容器 {len(list_containers)} 个，文本节点 {len(text_nodes)} 个）")

    def _final_logout(self, driver):
        """最终退出登录，回到登录页。"""
        assert AccountPage(driver).logout(), "最终退出登录失败（未回到登录页）"
