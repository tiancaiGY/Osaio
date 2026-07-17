"""云存购买流程测试（独立用例，使用测试者账号 ab3@bccto.cc）。

为什么独立：云存购买需要“测试者账号”权限（新注册账号暂无权限），且流程会切换账号，
放进主 smoke 会弄脏主流程。故单列一个文件，用 conftest 的 account("cloud") 注入账号。

前置：真机、Appium(4723)、账号 ab3@bccto.cc 已配置为测试者账号且已有支付源
      ************4242。付款成功后订阅生效（真实扣费/测试卡，请在测试环境使用）。

运行：
  pytest tests/test_cloud_storage.py -m subscription -s \
      --report-title "OSAIO 云存购买测试报告"
"""
import time

import pytest

from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.cloud_storage_page import CloudStoragePage


@pytest.mark.subscription
class TestCloudStorage:
    """云存年度订阅购买（已存卡支付）。"""

    def test_purchase_cloud_storage_annual(self, driver, account, report_step):
        """登录测试者账号 → 云存 → 年度订阅 → 已存卡 4242 支付成功。"""
        cloud = account("cloud")  # ab3@bccto.cc / 111111

        def step(name, fn):
            """执行一步：计时 + 记录报告步骤 + 失败即 fail。"""
            print(f"\n===== 步骤: {name} =====")
            s = time.time()
            try:
                fn()
            except pytest.skip.Exception as e:
                report_step(name, "skipped", time.time() - s, str(e))
                raise
            except Exception as e:
                report_step(name, "failed", time.time() - s, str(e))
                print(f"✗ 失败: {name} -> {e}")
                raise
            else:
                report_step(name, "passed", time.time() - s)
                print(f"✓ 通过: {name}")

        login_page = LoginPage(driver)
        csp = CloudStoragePage(driver)

        def _login():
            try:
                login_page.skip_onboarding()
            except Exception:
                pass
            home = login_page.smart_login(
                account=cloud.account, password=cloud.password, force_login=True)
            HomePage(driver).dismiss_permission_dialogs()
            assert home.is_home_displayed(), "登录测试者账号后首页未显示"

        step("1. 登录测试者账号 ab3", _login)
        step("2. 进入订阅页", lambda: _assert(csp.open_subscription(), "进入订阅页失败"))
        step("3. 选择 Cloud Storage", lambda: _assert(csp.choose_cloud_storage(), "选择 Cloud Storage 失败"))
        step("4. 点击 Subscribe 进入套餐列表", lambda: _assert(csp.tap_subscribe_on_plan_entry(), "进入套餐列表失败"))
        step("5. 选择 Annual subscription 进入付款页", lambda: _assert(csp.choose_annual_plan(), "进入付款页失败"))
        step("6. 已存卡 4242 支付成功", lambda: _assert(csp.pay_with_saved_card(), "已存卡支付未成功"))

        print("\n===== 云存年度订阅购买流程完成 =====")


def _assert(ok, msg):
    assert ok, msg
