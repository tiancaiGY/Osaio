"""调试登录页面元素定位"""
from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

caps = {
    "platformName": "Android",
    "automationName": "UiAutomator2",
    "appPackage": "com.afar.osaio",
    "appActivity": "com.yrcx.xuser.ui.activity.YRSplashActivity",
    "noReset": True,
    "deviceName": "2C011FDH3003AC",
    "newCommandTimeout": 300
}

options = UiAutomator2Options().load_capabilities(caps)
driver = webdriver.Remote("http://127.0.0.1:4725/wd/hub", options=options)

# 等待启动页跳转
print("等待启动页跳转...")
time.sleep(5)

# 检查当前页面
current_activity = driver.current_activity
print(f"当前 Activity: {current_activity}")

# 保存页面源码
page_source = driver.page_source
with open("debug_page_source.xml", "w", encoding="utf-8") as f:
    f.write(page_source)
print("页面源码已保存到 debug_page_source.xml")

# 查找所有元素类型
print("\n=== 查找所有 EditText (输入框) ===")
edit_texts = driver.find_elements("class name", "android.widget.EditText")
print(f"找到 {len(edit_texts)} 个 EditText:")
for i, el in enumerate(edit_texts):
    resource_id = el.get_attribute("resource-id") or "无ID"
    text = el.get_attribute("text") or "无文本"
    hint = el.get_attribute("hint") or "无提示"
    bounds = el.get_attribute("bounds")
    print(f"  {i+1}. ID: {resource_id}, 文本: '{text}', 提示: '{hint}', 位置: {bounds}")

print("\n=== 查找所有 Button (按钮) ===")
buttons = driver.find_elements("class name", "android.widget.Button")
print(f"找到 {len(buttons)} 个 Button:")
for i, el in enumerate(buttons):
    resource_id = el.get_attribute("resource-id") or "无ID"
    text = el.get_attribute("text") or "无文本"
    bounds = el.get_attribute("bounds")
    print(f"  {i+1}. ID: {resource_id}, 文本: '{text}', 位置: {bounds}")

print("\n=== 查找所有 TextView (文本) ===")
text_views = driver.find_elements("class name", "android.widget.TextView")
print(f"找到 {len(text_views)} 个 TextView (显示前20个):")
for i, el in enumerate(text_views[:20]):
    resource_id = el.get_attribute("resource-id") or "无ID"
    text = el.get_attribute("text") or "无文本"
    bounds = el.get_attribute("bounds")
    print(f"  {i+1}. ID: {resource_id}, 文本: '{text}', 位置: {bounds}")

print("\n=== 尝试点击 'Sign In' 按钮 ===")
try:
    sign_in_btn = driver.find_element("xpath", "//*[@text='Sign In']")
    print(f"找到 'Sign In' 按钮: {sign_in_btn.get_attribute('bounds')}")
    sign_in_btn.click()
    print("点击成功")
except Exception as e:
    print(f"找不到 'Sign In' 按钮: {e}")

driver.quit()