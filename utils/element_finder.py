"""快速获取 App 元素信息的工具"""
from appium import webdriver
import time


def get_page_source():
    """获取当前页面的 XML 结构"""
    caps = {
        "platformName": "Android",
        "automationName": "UiAutomator",
        "appPackage": "com.afar.osaio",
        "appActivity": "com.yrcx.xuser.ui.activity.YRSplashActivity",
        "noReset": True,
        "deviceName": "2C011FDH3003AC",
        "newCommandTimeout": 300
    }

    driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", caps)
    
    # 等待 App 启动
    time.sleep(5)
    
    # 获取页面源码
    page_source = driver.page_source
    
    # 保存到文件
    with open("page_source.xml", "w", encoding="utf-8") as f:
        f.write(page_source)
    
    print("页面源码已保存到 page_source.xml")
    
    # 查找常见元素
    print("\n尝试查找常见元素...")
    
    # 尝试查找输入框
    try:
        inputs = driver.find_elements("class name", "android.widget.EditText")
        print(f"找到 {len(inputs)} 个输入框:")
        for i, el in enumerate(inputs):
            resource_id = el.get_attribute("resource-id") or "无ID"
            text = el.get_attribute("text") or "无文本"
            print(f"  {i+1}. ID: {resource_id}, 文本: {text}")
    except Exception as e:
        print(f"查找输入框失败: {e}")
    
    # 尝试查找按钮
    try:
        buttons = driver.find_elements("class name", "android.widget.Button")
        print(f"\n找到 {len(buttons)} 个按钮:")
        for i, el in enumerate(buttons):
            resource_id = el.get_attribute("resource-id") or "无ID"
            text = el.get_attribute("text") or "无文本"
            print(f"  {i+1}. ID: {resource_id}, 文本: {text}")
    except Exception as e:
        print(f"查找按钮失败: {e}")
    
    driver.quit()
    return page_source


if __name__ == "__main__":
    get_page_source()