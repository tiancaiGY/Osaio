"""首页模块测试用例"""
import pytest
from pages.home_page import HomePage


class TestHome:
    """首页功能测试"""

    def test_home_display(self, driver):
        """首页正常展示"""
        import time
        home_page = HomePage(driver)
        
        # 等待启动页跳转（最多10秒）
        print("等待启动页跳转到首页...")
        for i in range(10):
            current_activity = driver.current_activity
            print(f"等待 {i+1}s, 当前 Activity: {current_activity}")
            
            # 检查是否还在启动页
            if "SplashActivity" in current_activity:
                time.sleep(1)
            else:
                print(f"已跳转到新页面: {current_activity}")
                break
        
        # 等待页面加载
        time.sleep(3)
        
        # 再次检查当前 Activity
        current_activity = driver.current_activity
        print(f"最终 Activity: {current_activity}")
        
        # 获取页面源码（调试用）
        page_source = driver.page_source[:1000]  # 只取前1000字符
        print(f"页面源码片段: {page_source}")
        
        # 尝试查找任意元素
        try:
            elements = driver.find_elements("class name", "android.widget.TextView")
            print(f"找到 {len(elements)} 个 TextView 元素")
            for i, el in enumerate(elements[:10]):  # 只显示前10个
                text = el.get_attribute("text") or "无文本"
                resource_id = el.get_attribute("resource-id") or "无ID"
                print(f"  元素 {i+1}: 文本='{text}', ID='{resource_id}'")
        except Exception as e:
            print(f"查找元素失败: {e}")
        
        # 原来的断言
        assert home_page.is_home_displayed(), "首页应正常展示"

    def test_add_device_entry(self, driver):
        """添加设备入口"""
        home_page = HomePage(driver)
        home_page.click_add_device()
        # TODO: 验证跳转到配网页面

    def test_switch_to_message(self, driver):
        """切换到消息Tab"""
        home_page = HomePage(driver)
        home_page.go_message()
        # TODO: 验证消息页面展示

    def test_switch_to_mine(self, driver):
        """切换到我的Tab"""
        home_page = HomePage(driver)
        home_page.go_mine()
        # TODO: 验证我的页面展示
