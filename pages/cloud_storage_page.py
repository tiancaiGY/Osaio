"""云存购买（Cloud Storage 订阅）页面对象。

覆盖用户定义的完整购买流程（测试者账号 ab3@bccto.cc 才有权限）：
  账户 tab → 订阅 "Subscription" → 选 "Cloud Storage" → 订阅页点 "Subscribe" 按钮
    → 套餐列表点 "Annual subscription" → （原生 WebView 渲染的）付款页
    → 选已存在支付源卡号 ************4242 → 下方 "Subscribe" 亮起后点击
    → 等待"支付成功"提示。

真机确认要点（逐页探查）：
- 订阅页/套餐页/付款页很多 CTA 是**不可点击的 TextView**（外层容器才可点），
  故对 "Subscribe" 按钮、套餐项、卡号行统一用**坐标点击元素中心**（复用配网页技法）。
- 付款页虽来自浏览器支付，但以 NATIVE_APP 内 WebView 渲染，text 定位可直接命中，
  无需切 WEBVIEW context。
- 付款页已有支付源显示为 "************4242"；选中后底部 "Subscribe" 才可用。
- "Add Credit or Debit Card"（新增卡）分支：后续补充。
"""
import os
import re
import time

from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage
from pages.account_page import AccountPage


def _tc(sub):
    """textContains 定位器。"""
    return (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("%s")' % sub)


class CloudStoragePage(BasePage):
    # 账户页“订阅”入口
    SUBSCRIPTION_ENTRY = _tc("Subscription")
    # 订阅二级页两个选项之一
    CLOUD_STORAGE_OPTION = _tc("Cloud Storage")
    # 订阅页/套餐页/付款页的 "Subscribe" 文案（多处出现，用坐标点具体那一个）
    SUBSCRIBE_TEXT = _tc("Subscribe")
    # 套餐列表里的“年度订阅”CTA
    ANNUAL_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR,
                   'new UiSelector().textMatches("(?i).*(Annual subscription|年度订阅|年付).*")')
    # 付款页已存在支付源卡号（默认测试卡 4242）
    SAVED_CARD_4242 = _tc("4242")
    # 付款页底部“Subscribe”按钮（Chrome WebView，resource-id=subscribe-button）；
    # 仅在选中支付源后才变蓝可点，未选中时点它无效（会触发文本选择/搜索弹窗）。
    SUBSCRIBE_BTN = (AppiumBy.ID, "subscribe-button")
    # 付款成功提示（中英兼容，尽量宽松）
    PAY_SUCCESS = (AppiumBy.ANDROID_UIAUTOMATOR,
                   'new UiSelector().textMatches("(?i).*(success|succeeded|paid|payment complete|订阅成功|支付成功|购买成功).*")')
    # 支付成功页“Done”按钮：点击后跳回 App。
    DONE_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("(?i)(Done|完成|返回|Back to App|好的|OK)")')

    # 币种选择弹窗（**不总出现**）：真机确认 title="Select Currency"，选项 USD / CAD，可"Not now"。
    # 出现时会盖住套餐/付款流程，必须先选币种（用户要求选 USD）才能继续到付款页。
    CURRENCY_DIALOG = (AppiumBy.ANDROID_UIAUTOMATOR,
                       'new UiSelector().textMatches("(?i).*(Select Currency|选择货币|选择币种|币种|currency).*")')
    CURRENCY_USD = (AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textMatches("(?i).*(USD|US Dollar|美元|美金).*")')

    def __init__(self, driver):
        super().__init__(driver)
        self._account = AccountPage(driver)

    # -------------------------------------------------- 通用助手
    def _coord_tap(self, el):
        r = el.rect
        self.driver.tap([(int(r["x"] + r["width"] / 2), int(r["y"] + r["height"] / 2))])

    def _tap_text_coord(self, locator, timeout=8):
        """等待某文案出现后**坐标点击**其元素中心（应对不可点击的 TextView）。"""
        if not self.is_displayed(*locator, timeout=timeout):
            return False
        els = self.driver.find_elements(*locator)
        if not els:
            return False
        self._coord_tap(els[0])
        return True

    def select_currency_if_present(self, timeout=2):
        """若出现“Select Currency”弹窗（不总出现），选择 USD 继续。返回是否处理了弹窗。

        真机确认：该弹窗盖住套餐/付款流程，选项 USD / CAD，用户要求选 USD。选中后价格以
        USD 展示并保存偏好，方能继续到付款页。用坐标点击（选项常为不可点击 TextView）。
        """
        if not self._present(self.CURRENCY_DIALOG, timeout=timeout):
            return False
        print("检测到币种选择弹窗，选择 USD")
        if not self._tap_text_coord(self.CURRENCY_USD, timeout=5):
            # 退化：扫描含 USD 的元素坐标点击
            els = self.driver.find_elements(*self.CURRENCY_USD)
            if els:
                self._coord_tap(els[0])
            else:
                self._save_diag("currency_no_usd_option")
                return False
        time.sleep(2)
        return True

    def _present(self, locator, timeout=1):
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

    def _save_diag(self, reason):
        try:
            os.makedirs("reports", exist_ok=True)
            ts = int(time.time())
            with open(f"reports/page_source_cloud_{reason}_{ts}.xml", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.driver.save_screenshot(f"reports/screenshot_cloud_{reason}_{ts}.png")
            print(f"已保存云存诊断: reports/*cloud_{reason}_{ts}.*")
        except Exception as e:
            print(f"保存云存诊断失败: {e}")

    # -------------------------------------------------- 流程步骤
    def open_subscription(self):
        """账户 tab → 点击“Subscription”进入订阅二级页。"""
        if not self._account._tap_account_tab():
            self._save_diag("account_tab_failed")
            return False
        time.sleep(2)
        if not self._tap_text_coord(self.SUBSCRIPTION_ENTRY, timeout=8):
            self._save_diag("no_subscription_entry")
            return False
        time.sleep(3)
        return self._present(self.CLOUD_STORAGE_OPTION, timeout=5)

    def choose_cloud_storage(self):
        """在订阅二级页选择第一个选项“Cloud Storage”，进入订阅页。"""
        if not self._tap_text_coord(self.CLOUD_STORAGE_OPTION, timeout=8):
            self._save_diag("no_cloud_storage_option")
            return False
        time.sleep(4)
        # 进入订阅页时可能弹“Select Currency”（不总出现）→ 选 USD
        self.select_currency_if_present(timeout=2)
        return self._present(self.SUBSCRIBE_TEXT, timeout=6)

    def tap_subscribe_on_plan_entry(self):
        """订阅页点击“Subscribe”按钮，进入套餐列表。

        该 Subscribe 是不可点击 TextView，需坐标点其外层按钮。取最上方的 Subscribe。
        """
        # 点 Subscribe 前后都可能弹币种选择 → 选 USD
        self.select_currency_if_present(timeout=1)
        els = self.driver.find_elements(*self.SUBSCRIBE_TEXT)
        if not els:
            self._save_diag("no_subscribe_button")
            return False
        # 取 y 最小（页面上方的订阅入口按钮）
        target = min(els, key=lambda e: (e.location or {}).get("y", 0))
        self._coord_tap(target)
        time.sleep(6)
        self.select_currency_if_present(timeout=2)
        # 进入套餐列表：出现 Annual / Monthly / Yearly
        return self._present(self.ANNUAL_TEXT, timeout=8) or self._present(_tc("Yearly"), timeout=2)

    def choose_annual_plan(self):
        """套餐列表点击“Annual subscription”，跳转到（WebView 渲染的）付款页。"""
        # 套餐页/点击后都可能弹币种选择 → 选 USD
        self.select_currency_if_present(timeout=1)
        if not self._tap_text_coord(self.ANNUAL_TEXT, timeout=8):
            self._save_diag("no_annual_plan")
            return False
        # 付款页加载较慢，轮询等待卡号/付款方式出现；期间若弹币种则选 USD
        for _ in range(10):
            time.sleep(2)
            self.select_currency_if_present(timeout=1)
            if self._present(self.SAVED_CARD_4242, timeout=1) or self._present(_tc("Payment Method"), timeout=1):
                return True
        self._save_diag("no_payment_page")
        return False

    def pay_with_saved_card(self, timeout=60):
        """付款页：选中已存在支付源 ************4242 → 点亮的“Subscribe”→ 等待支付成功。

        关键（真机+用户确认）：付款页是 Chrome WebView 的单选支付列表，**单选圆点在卡号行最左**，
        网页 label 不整体可点——只点卡号文本（行右侧）**不会选中**支付源，Subscribe 会一直是
        灰色不可点（此时去点它只会触发 Android 文本选择/“Tap to see search results”弹窗）。
        故这里按卡号行的 y、行首的 x 坐标去**点单选圆点**选中支付源，选中后 Subscribe 才变蓝可点。

        :return: True 表示检测到支付成功提示
        """
        # 1) 等待已保存卡号 4242 出现，取其所在行的坐标
        if not self.is_displayed(*self.SAVED_CARD_4242, timeout=10):
            self._save_diag("no_saved_card_4242")
            return False
        els = self.driver.find_elements(*self.SAVED_CARD_4242)
        if not els:
            self._save_diag("no_saved_card_4242")
            return False
        row = els[0].rect
        cy = int(row["y"] + row["height"] / 2)
        try:
            w = int(self.driver.get_window_size()["width"])
        except Exception:
            w = 1440
        # 2) 选中支付源：点行首的单选圆点（约屏宽 10% 处，与卡号同一行 y），兜底再点整行
        self.driver.tap([(int(w * 0.10), cy)])
        time.sleep(1)
        self._coord_tap(els[0])
        time.sleep(2)
        # 3) 点亮后的 Subscribe（优先 resource-id=subscribe-button，退化取底部 Subscribe 文案）
        if not self._tap_subscribe_button():
            self._save_diag("no_pay_subscribe")
            return False
        print("已点击付款页 Subscribe，等待支付结果…")
        # 4) 等待支付成功提示
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._present(self.PAY_SUCCESS, timeout=1):
                # 支付成功后点击“Done”跳回 App（best-effort，点不到也算成功）
                if self._tap_text_coord(self.DONE_BTN, timeout=5):
                    print("已点击 Done，返回 App")
                    time.sleep(3)
                else:
                    print("未找到 Done 按钮（支付已成功，跳过返回步骤）")
                return True
            time.sleep(2)
        self._save_diag("no_pay_success")
        return False

    def _tap_subscribe_button(self):
        """坐标点击付款页底部 Subscribe（选中支付源后才可点）。

        优先 resource-id=subscribe-button；退化取所有“Subscribe”文案里 y 最大（最底部）的那个。
        """
        els = self.driver.find_elements(*self.SUBSCRIBE_BTN)
        if not els:
            els = self.driver.find_elements(*self.SUBSCRIBE_TEXT)
        if not els:
            return False
        target = max(els, key=lambda e: (e.location or {}).get("y", 0))
        self._coord_tap(target)
        return True

    def purchase_cloud_storage_annual(self):
        """一站式：从账户页走完“云存年度订阅 + 已存卡支付成功”。返回是否成功。"""
        assert self.open_subscription(), "进入订阅页失败"
        assert self.choose_cloud_storage(), "选择 Cloud Storage 失败"
        assert self.tap_subscribe_on_plan_entry(), "点击 Subscribe 进入套餐列表失败"
        assert self.choose_annual_plan(), "选择 Annual subscription / 进入付款页失败"
        assert self.pay_with_saved_card(), "已存卡支付未成功"
        return True
