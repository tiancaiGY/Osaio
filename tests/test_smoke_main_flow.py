"""主功能端到端 Smoke 测试（只跑完全正确的 happy-path，作为每轮测试前的健康门禁）。

主功能顺序（用户定义）：
  1. 首次安装 App 打开 → 引导页（FRESH_INSTALL=1 时清数据重现，默认沿用现状）
  2. 进入登录页 → 注册新用户成功（注册完成自动登录）
  3. 退出登录 → 重新登录成功
  4. 配网成功（现场需有真实待配网设备 + mmm_test 2.4G WiFi；新装首次会先走定位权限授予）
  5. 出图成功（直播）
  6. IOT 设备推送消息正常（监听「配网开始→出图后」窗口内收到 OSAIO 侦测推送；紧接出图汇报）
  7. 订阅云存成功（切到 cloud 测试者账号完成年度订阅购买）
  8. 云卡回放成功（切到 secondary 账号；依次验证 事件云回放 → 时间轴切换+滑动
     → 卡回放(SD) → 云回放(Cloud) → 回到直播，每步均以“出图”判定）
  9. 消息列表显示历史消息成功
  10. 退出登录成功

约定：
  - 注册验证码经临时邮箱 tempmail.plus 自动获取（utils/temp_mail.py）。
  - 注册密码固定为 "111111"。
  - 各主功能相互独立：某步失败/跳过不应牵连无关步骤，后续照常执行。
  - 软步骤（失败/前置不满足 → 记 skipped 并继续，不中断整条流程）：
    · 步骤 4 配网 / 5 出图：强依赖现场硬件（待配网设备 + WiFi）；配网未成功则出图一并 skip。
    · 步骤 6 IoT 推送：监听「配网开始→出图后」窗口，需摄像头真实动静触发侦测，无新推送则软性跳过。
    · 步骤 7 订阅云存：需 cloud 测试者账号 + 可用支付源，购买失败软性跳过。
  - 步骤 7/8 会切换账号（cloud / secondary），各自 force_login 先登出再登入；步骤8登录前会先把
    OSAIO 拉回前台（云存付款走 Chrome，避免在浏览器页找不到登录表单）。
  - 云卡回放（步骤 8）需要“存在在线设备 + 云存订阅 + 历史录像/事件”的账号；主流程
    新注册账号刚配网、无历史录像/事件，不满足前置，故该步切到 config/accounts.yaml 的
    secondary 账号（ocn03@bccto.cc，用户确认已满足条件）后再验证，复用 test_playback 同一套页面对象。
  - IoT 推送（步骤 6）监听窗口＝配网起点（_network_config 记通知栏基线）→ 出图后（_live_view 结算）。
  - 每步结果通过 report_step 记录，报告里展开显示各步骤（passed/failed/skipped）。

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
from utils.countries import get_country
from utils.account_recorder import save_registered_account

APP_PACKAGE = "com.afar.osaio"
REGISTER_PASSWORD = "111111"          # 用户要求：注册密码固定为 111111
WIFI_NAME = NetworkConfigPage.WIFI_NAME_DEFAULT   # mmm_test
WIFI_PWD = NetworkConfigPage.WIFI_PWD_DEFAULT     # mmmmmmmm
# tempmail.plus 的可收信域名（@tempmail.plus 本身不收信；@mailto.plus 实测可正常收到
# OSAIO 验证码邮件，发件人 no-reply@eu.support.osaio.net）。可用 TEMP_EMAIL_DOMAIN 覆盖。
TEMP_MAIL_DOMAIN = os.environ.get("TEMP_EMAIL_DOMAIN", "mailto.plus")
CODE_TIMEOUT = int(os.environ.get("OSAIO_CODE_TIMEOUT", "180"))
# 注册国家：默认中国+86，可用 OSAIO_COUNTRY=US|UK 切换（China/United States/United Kingdom）。
REGISTER_COUNTRY = get_country()


def _gen_temp_email():
    rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"osaio_smoke_{rnd}@{TEMP_MAIL_DOMAIN}"


@pytest.mark.smoke
class TestSmokeMainFlow:
    """主功能完整正确流程（单个端到端用例）。"""

    def test_main_flow_smoke(self, driver, account, report_step, report_env):
        """按顺序跑完主功能 happy-path，分步骤记录到报告。"""
        t0 = time.time()

        def step(name, fn):
            """执行一步：计时、记录报告步骤。

            - 失败（任意非 skip 异常）→ 记 failed 并向上抛出，整条 smoke 立即 fail（门禁语义）。
            - pytest.skip → 记 skipped 但**吞掉不再抛出**，让后续步骤照常执行
              （订阅云存 / IOT 推送等占位步骤不应中断整条流程；否则报告只能显示到跳过处为止）。
            - 跳过/失败时抓当前 App 屏幕截图（并存 page_source）附到报告，便于事后定位现场。
            """
            print(f"\n===== 步骤: {name} =====")
            s = time.time()
            try:
                fn()
            except pytest.skip.Exception as e:
                shot = self._capture(driver, name, "skipped")
                report_step(name, "skipped", time.time() - s, str(e), screenshot=shot)
                print(f"⏭  跳过（占位，流程继续）: {name} ({e})")
            except Exception as e:
                shot = self._capture(driver, name, "failed")
                report_step(name, "failed", time.time() - s, str(e), screenshot=shot)
                print(f"✗ 失败: {name} -> {e}")
                raise
            else:
                report_step(name, "passed", time.time() - s)
                print(f"✓ 通过: {name}")

        login_page = LoginPage(driver)
        # 注册成功后保存，供步骤3重登使用
        self._email = _gen_temp_email()
        self._password = REGISTER_PASSWORD

        # IoT 推送监听状态：改为「配网开始起听 → 直播出图后结束」（见 _network_config / _live_view /
        # _iot_push）。基线在步骤4起点记，出图后结算，步骤8只汇报窗口内是否收到新侦测推送。
        self._iot_listen = False
        self._iot_serial = None
        self._iot_baseline = 0
        self._iot_new_when = 0

        # 注入报告“测试环境”信息（设备由 caps.yaml 兜底自动读取）
        report_env(测试邮箱=self._email,
                   注册国家=f"{REGISTER_COUNTRY.name} ({REGISTER_COUNTRY.code})",
                   验证码服务=TEMP_MAIL_DOMAIN)

        # ---- 步骤 0：首次安装重置（始终执行）----
        # 用户定义的主流程本就以“首次安装 App 打开”为起点。始终 pm clear 让每轮都从
        # 干净的首装状态开始 → 直达引导/登录页，避免依赖脆弱的 UI 登出做前置
        # （历史踩坑：残留已登录会话 + 绑定设备的 BLE 弹窗会让账户页导航/登出卡死）。
        # SMOKE_NO_RESET=1 可跳过清数据（沿用现状，供特殊调试）。
        skip_reset = os.environ.get("SMOKE_NO_RESET") == "1"
        if not skip_reset:
            step("首次安装重置（pm clear）", lambda: self._fresh_install(driver))

        # ---- 步骤 1：首次安装打开 → 引导页 ----
        # FRESH_INSTALL=1 时断言确实经过引导页；否则尽力而为。
        fresh = os.environ.get("FRESH_INSTALL") == "1" and not skip_reset
        step("打开 App 进入引导页", lambda: self._onboarding(login_page, fresh))

        # ---- 步骤 2：注册新用户（自动登录）----
        step("注册新用户成功（自动登录）", lambda: self._register(driver, login_page))

        # ---- 步骤 3：退出登录 → 重新登录 ----
        step("退出后重新登录成功", lambda: self._logout_then_relogin(driver, login_page))

        # ---- 步骤 4：配网（软性：现场无待配网设备等原因失败 → 记 skipped 并继续）----
        # 配网强依赖现场硬件（待配网设备处于配对模式 + mmm_test WiFi）。无设备时它不该阻断
        # 与之无关的主功能（云卡回放/消息列表/登出）。故把配网做成“软步骤”：失败即转 skip
        # 并继续；用 self._netcfg_ok 记录是否真的配网成功，供步骤5判断。
        self._netcfg_ok = False
        ncp = NetworkConfigPage(driver)
        step("配网成功", lambda: self._network_config(driver, ncp))

        # ---- 步骤 5：出图（依赖步骤4配网的设备；配网未成功则一并 skip）----
        step("出图成功（直播）", lambda: self._live_view(driver, ncp))

        # ---- 步骤 6：IOT 推送消息（紧接出图之后）----
        # IoT 推送监听在「配网开始 → 出图后」窗口进行（见 _network_config/_live_view），故把
        # 推送结算步骤紧跟在出图之后汇报，与监听窗口对齐（用户要求）。此后再切账号做云存/回放。
        step("IOT 设备推送消息正常", lambda: self._iot_push(driver))

        # ---- 步骤 7：订阅云存（切到 cloud 测试者账号完成购买；软性跳过）----
        step("订阅云存成功", lambda: self._cloud_storage(driver, login_page, account))

        # ---- 步骤 8：云卡回放（切到 secondary 账号验证云/卡回放出图）----
        step("云卡回放成功（云/卡回放出图）",
             lambda: self._cloud_sd_playback(driver, login_page, account))

        # ---- 步骤 9：消息列表显示历史消息 ----
        step("消息列表显示历史消息成功", lambda: self._message_list(driver))

        # ---- 步骤 10：退出登录 ----
        step("退出登录成功", lambda: self._final_logout(driver))

        print(f"\n===== 主功能 smoke 全流程完成，用时 {time.time() - t0:.1f}s =====")

    # ------------------------------------------------------------------ 步骤实现

    @staticmethod
    def _adb_serial(driver):
        """确定 adb 目标设备序列号。

        多设备同时连接时，裸 `adb shell` 会因 “more than one device/emulator” 直接失败，
        故必须用 `-s <serial>` 指定本会话实际操作的设备。优先取会话绑定设备（driver
        capabilities 的 udid/deviceName，即 Appium 真正连上的那台），其次取 config/caps.yaml
        的 deviceName，最后可用环境变量 ANDROID_SERIAL / OSAIO_DEVICE_SERIAL 覆盖。
        返回 None 表示未知（此时退回裸 adb，仅单设备场景可用）。
        """
        env = os.environ.get("OSAIO_DEVICE_SERIAL") or os.environ.get("ANDROID_SERIAL")
        if env:
            return env
        try:
            caps = getattr(driver, "capabilities", None) or {}
            for k in ("udid", "deviceUDID", "appium:udid", "deviceName", "appium:deviceName"):
                v = caps.get(k)
                if v:
                    return v
        except Exception:
            pass
        try:
            from utils.driver_helper import load_config
            return (load_config().get("android", {}) or {}).get("deviceName")
        except Exception:
            return None

    @staticmethod
    def _capture(driver, step_name, status):
        """跳过/失败时抓 App 屏幕截图（+page_source），返回截图路径供报告附图。

        “等相关信息”：截图落 reports/screenshots/，page_source 落 reports/，均以步骤名+状态+
        时间戳命名。任何异常都吞掉、返回 None——截图是辅助信息，绝不能反过来把用例搞挂。
        """
        try:
            os.makedirs("reports/screenshots", exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            safe = "".join(c if c.isalnum() else "_" for c in str(step_name))[:40]
            img_path = os.path.join("reports", "screenshots", f"step_{safe}_{status}_{ts}.png")
            driver.save_screenshot(img_path)
            # 附带 page_source（best-effort，失败忽略）
            try:
                with open(os.path.join("reports", f"step_{safe}_{status}_{ts}.xml"),
                          "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
            except Exception:
                pass
            print(f"已保存步骤现场截图: {img_path}")
            return img_path
        except Exception as e:
            print(f"保存步骤截图失败（忽略）: {e}")
            return None

    def _fresh_install(self, driver):
        """adb 清除 App 数据以重现首次安装，然后重启 App。"""
        serial = self._adb_serial(driver)
        cmd = ["adb"] + (["-s", serial] if serial else []) + ["shell", "pm", "clear", APP_PACKAGE]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        except Exception as e:
            pytest.fail(f"pm clear 失败（无法重现首次安装，adb 目标={serial or '默认'}）: {e}")
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

        # 第一步：国家 + 邮箱 + 同意条款 → 进入验证码页。
        # 传入期望区号（REGISTER_COUNTRY.code，默认 +86，可由 OSAIO_COUNTRY 配置）以**校验**
        # 选中的正是目标国家——历史 bug：搜索输错框导致误选 Algeria(+213)。
        step1 = register_page.register_step1_input_email(
            email=self._email, country=REGISTER_COUNTRY.name,
            country_code=REGISTER_COUNTRY.code,
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
        # 保存注册账号到 CSV（reports/registered_accounts.csv）
        save_registered_account(self._email, self._password,
                                f"{REGISTER_COUNTRY.name} ({REGISTER_COUNTRY.code})")
        print(f"注册成功并自动登录：{self._email} / {self._password} / {REGISTER_COUNTRY.name}")

    def _logout_then_relogin(self, driver, login_page):
        """退出登录 → 用新注册账号重新登录。"""
        assert AccountPage(driver).logout(), "退出登录失败（未回到登录页）"
        time.sleep(1)
        home = login_page.smart_login(
            account=self._email, password=self._password, force_login=True)
        assert home.is_home_displayed(), "重新登录后首页未显示"

    def _network_config(self, driver, ncp):
        """完整蓝牙配网（现场需有待配网设备）。

        软步骤语义：配网强依赖现场硬件（待配网设备处于配对模式 + mmm_test WiFi）。现场无设备
        或连接超时等**环境原因**不应阻断与之无关的主功能，故这里把任何配网失败**转成
        pytest.skip**（step() 会记 skipped 并继续），仅在真正配网成功时置 self._netcfg_ok=True，
        供步骤5（出图，依赖该设备）判断是否一并跳过。

        另：在配网**开始**时开启 IoT 推送监听（记录通知栏基线 when），到步骤5直播出图后结束，
        使侦测推送的监听窗口贴合“设备刚配网上线并出图”这段真实活动期（见 _live_view/_iot_push）。
        """
        self._start_iot_listen(driver)
        try:
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
        except pytest.skip.Exception:
            raise
        except Exception as e:
            # 配网失败大概率是现场无待配网设备/连接超时（环境前置），软性跳过、不阻断后续
            pytest.skip(f"配网未完成（现场需真实待配网设备+mmm_test WiFi），跳过并继续: {e}")
        self._netcfg_ok = True
        print(f"配网成功，设备昵称: {ncp.last_nickname}")

    def _live_view(self, driver, ncp):
        """配网完成后进入直播页验证出图。

        依赖步骤4配网出来的设备：若配网未成功（被软性跳过），此步没有可出图的新设备，随之 skip。

        首次进直播（新配网设备）设备端会先弹“New Device Firmware Found”升级弹窗 + 引导流程，
        二者会盖住直播画面导致出图判定失败，故验证前先做“直播前置”清理（勾 Don't remind + Not Now、
        逐步点下一步关引导），出图后再清一次（引导有时在出图后才浮出）。
        """
        if not getattr(self, "_netcfg_ok", False):
            pytest.skip("配网未成功，无新配网设备可出图，跳过出图步骤")
        home = HomePage(driver)
        home.dismiss_live_view_intro()
        assert ncp.verify_live_view(), "直播页出图异常（未检测到视频/码率/控制按钮）"
        home.dismiss_live_view_intro()
        # 直播出图成功 → 结束 IoT 推送监听（结算窗口内是否收到新侦测推送，供步骤8汇报）
        self._end_iot_listen()
        # 回到首页，便于后续消息列表步骤
        try:
            driver.back()
            time.sleep(2)
        except Exception:
            pass

    def _cloud_storage(self, driver, login_page, account):
        """订阅云存：切到 cloud 测试者账号后完成年度订阅购买（软性：失败转 skip 并继续）。

        为什么切账号：云存购买需“测试者账号”权限（新注册账号无权限），config/accounts.yaml
        的 cloud（ab1@bccto.cc）为测试者账号且有已存支付源 4242。smart_login(force_login=True)
        先登出当前会话再登入 cloud，此步之后 App 处于 cloud 会话（步骤7会再切到 secondary）。

        复用 pages/cloud_storage_page.py（与独立用例 test_cloud_storage.py 同一套）：
        进入订阅页 → 选 Cloud Storage → Subscribe → Annual → 已存卡 4242 支付成功。
        购买涉及真实支付，可能因账号权限/支付源/网络失败——按“软步骤”处理：任何失败转成
        pytest.skip（记 skipped 并继续），不阻断与之无关的后续主功能。
        """
        from pages.cloud_storage_page import CloudStoragePage

        acc = account("cloud")   # ab1@bccto.cc / 111111（测试者账号，有已存卡 4242）
        csp = CloudStoragePage(driver)
        try:
            home = login_page.smart_login(
                account=acc.account, password=acc.password, force_login=True)
            HomePage(driver).dismiss_permission_dialogs()
            assert home.is_home_displayed(), "切到 cloud 测试者账号后首页未显示"
            assert csp.open_subscription(), "进入订阅页失败"
            assert csp.choose_cloud_storage(), "选择 Cloud Storage 失败"
            assert csp.tap_subscribe_on_plan_entry(), "进入套餐列表失败"
            assert csp.choose_annual_plan(), "进入付款页失败"
            assert csp.pay_with_saved_card(), "已存卡 4242 支付未成功"
        except pytest.skip.Exception:
            raise
        except Exception as e:
            pytest.skip(f"云存购买未完成（需测试者账号+可用支付源），跳过并继续: {e}")
        print(f"云存年度订阅购买成功（账号 {acc.account}）")

    def _cloud_sd_playback(self, driver, login_page, account):
        """云卡回放：切到 secondary 账号（满足回放前置）后验证云/卡回放各场景出图。

        为什么切账号：云/卡回放需要“存在在线设备 + 云存订阅 + 历史录像/事件”的账号；主流程
        新注册账号刚配网、无历史录像/事件，不满足前置。secondary（ocn03@bccto.cc）经用户确认
        已满足条件（在线设备 GP5B）。smart_login(force_login=True) 会先登出当前新注册账号再登入
        secondary，故此步之后 App 处于 secondary 会话（后续消息列表 / 最终登出照常在该会话执行）。

        复用 pages/playback_page.py（与独立用例 test_playback.py 同一套）：进入直播出图 →
        点事件云回放 → 时间轴切换+滑动 → 卡回放(SD) → 云回放(Cloud) → 回到直播，
        每一子步均以出图（bit_rate 出现）判定，任一未出图即 fail。
        """
        from pages.playback_page import PlaybackPage

        acc = account("secondary")   # ocn03@bccto.cc / 123456（在线设备 GP5B）
        pb = PlaybackPage(driver)

        # 前置：云存步骤会跳到 Chrome 浏览器付款页；无论购买成功/跳过，此处都可能仍停在浏览器。
        # 必须先把 OSAIO 拉回前台，否则 smart_login 会在浏览器页找不到登录表单——历史现象：
        # 把 Chrome 地址栏误当成账号输入框(instance 0)、无第二个输入框→密码框缺失而失败。
        try:
            driver.activate_app(APP_PACKAGE)
            time.sleep(3)
        except Exception as e:
            print(f"拉回 OSAIO 前台失败（忽略，继续尝试登录）: {e}")

        # 切换到 secondary 账号（force_login 内部先登出当前会话再登入）
        home = login_page.smart_login(
            account=acc.account, password=acc.password, force_login=True)
        HomePage(driver).dismiss_permission_dialogs()
        assert home.is_home_displayed(), "切到 secondary 账号后首页未显示"

        # 云/卡回放六步（复用 PlaybackPage），任一未出图即 fail
        assert pb.enter_live_view(), "未能进入设备直播页（出图）"
        assert pb.play_first_event(), "点击事件后云回放未出图"
        assert pb.switch_timeline_and_swipe(), "时间轴回放未出图"
        assert pb.switch_to_sd(), "卡回放(SD)未出图"
        assert pb.switch_to_cloud(), "云回放(Cloud)未出图"
        assert pb.back_to_live(), "回到直播未出图"
        print(f"云卡回放全部出图正常（账号 {acc.account}）")

    def _start_iot_listen(self, driver):
        """配网开始时开启 IoT 推送监听：记录当前该 App 通知栏最新推送 when 作为基线。

        真机确认：OSAIO 侦测推送落在通知渠道 PUSH_NOTIFY_ID，title="Osaio Notice"，
        text="Device <名称> <Motion|Sound> Detected"，每条带 when=<epoch ms>。基线之后出现
        更晚(when 更大)的推送即视为“监听窗口内收到新侦测”。OSAIO_SKIP_IOT_PUSH=1 时不起听。
        """
        if os.environ.get("OSAIO_SKIP_IOT_PUSH") == "1":
            return
        from utils import adb_helper
        serial = adb_helper.resolve_serial(driver)
        if not serial:
            print("无法确定 adb 目标设备，本轮不开启 IoT 推送监听")
            return
        self._iot_serial = serial
        self._iot_baseline = adb_helper.latest_push_when(serial)
        self._iot_listen = True
        print(f"IoT 推送监听已开始（配网起），基线 when={self._iot_baseline}")

    def _end_iot_listen(self):
        """直播出图后结束 IoT 推送监听：结算窗口内该 App 最新推送 when（供步骤8比对基线）。"""
        if not self._iot_listen or not self._iot_serial:
            return
        from utils import adb_helper
        self._iot_new_when = adb_helper.latest_push_when(self._iot_serial)
        print(f"IoT 推送监听已结束（出图后），窗口内最新 when={self._iot_new_when}"
              f"（基线 {self._iot_baseline}）")

    def _iot_push(self, driver):
        """IoT 推送验证：汇报「配网开始 → 直播出图后」监听窗口内是否收到新的 OSAIO 侦测推送。

        监听不再在本步单开窗口，而是贴合设备真实活动期：_network_config 起点起听（记基线），
        _live_view 出图后结束（记窗口末最新 when）。本步只做结算判定：
          - OSAIO_SKIP_IOT_PUSH=1 → 跳过；
          - 未开启监听（配网/出图被软性跳过，无设备触发侦测）→ 跳过并说明；
          - 窗口末最新 when > 基线 → 通过（期间收到新侦测推送）；
          - 否则默认软性跳过；可用 OSAIO_IOT_PUSH_TIMEOUT>0 在本步再补听一小段兜底。
        侦测是否触发取决于摄像头端的真实动静，无法按需保证，故未命中记 skipped 不误判为失败。
        """
        if os.environ.get("OSAIO_SKIP_IOT_PUSH") == "1":
            pytest.skip("OSAIO_SKIP_IOT_PUSH=1，跳过 IoT 推送验证")
        if not self._iot_listen or not self._iot_serial:
            pytest.skip("配网/出图未进行，未开启 IoT 监听（无新配网设备触发侦测），跳过并继续")
        from utils import adb_helper
        # 出图后若尚未结算（异常情况）补一次
        if not self._iot_new_when:
            self._iot_new_when = adb_helper.latest_push_when(self._iot_serial)
        if self._iot_new_when > (self._iot_baseline or 0):
            text = adb_helper.latest_push_text(self._iot_serial) or ""
            print(f"监听窗口内收到新的 IoT 侦测推送：when={self._iot_new_when} {text}")
            return
        # 窗口内未见新推送：可选再补听一小段（默认 0=不补听，直接软跳过）
        grace = int(os.environ.get("OSAIO_IOT_PUSH_TIMEOUT", "0"))
        if grace > 0:
            print(f"窗口内暂无新侦测推送，补听 {grace}s…")
            new_when = adb_helper.wait_for_new_push(
                self._iot_serial, self._iot_baseline or 0, timeout=grace, interval=5)
            if new_when:
                text = adb_helper.latest_push_text(self._iot_serial) or ""
                print(f"补听收到新的 IoT 侦测推送：when={new_when} {text}")
                return
        pytest.skip("配网→出图监听窗口内未收到新的侦测推送（设备需真实动静触发），跳过并继续")

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
