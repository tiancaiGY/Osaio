import sys, time, yaml, uiautomator2 as u2, random
from pathlib import Path
from xml.etree import ElementTree as ET

BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "config" / "config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 复用项目根目录的账号加载器（集中管理账号密码，支持环境变量覆盖）
sys.path.insert(0, str(BASE_DIR.parent))
from utils.accounts import get_register_default_password

serial = config["device"]["serial"]
package = config["app"]["package_name"]
UID = random.randint(10000, 99999)
EMAIL = f"autotest{UID}@mailto.plus"
PASSWORD = get_register_default_password()

d = u2.connect(serial)
d.implicitly_wait(10)

def skip_onboarding():
    for _ in range(10):
        raw = d.dump_hierarchy()
        if 'EditText' in raw:
            time.sleep(2)
            return True
        if '如果您不想继续' in raw:
            e = d(text="同意")
            if e.exists(timeout=0.5):
                e.click()
                time.sleep(2)
        for t in ["开始", "Start", "Get Started"]:
            if t in raw:
                d(textContains=t).click()
                time.sleep(2)
                break
        time.sleep(2)
    return False

print("=" * 50)
print("注册:", EMAIL)
print("=" * 50)

print("\n1. 启动APP...")
d.app_stop(package)
d.app_clear(package)
time.sleep(1)
d.app_start(package)
time.sleep(5)
skip_onboarding()

print("\n2. 进入注册页...")
d(text="注册").click()
time.sleep(3)

print("   输入邮箱:", EMAIL)
elem = d(className="android.widget.EditText", instance=0)
elem.click()
time.sleep(0.5)
elem.clear_text()
time.sleep(0.3)
elem.send_keys(EMAIL)
time.sleep(0.5)
# 原版方式: click blank area to blur
d.click(540, 150)
time.sleep(2)

print("   勾选协议...")
# 原版方式: 点击文本元素
d(textContains="我确认我至少13岁").click()
time.sleep(2)

raw = d.dump_hierarchy()
if "EditText" not in raw:
    print("   => 触发链接，返回")
    d.press("back")
    time.sleep(3)

for attempt in range(3):
    raw = d.dump_hierarchy()
    if "EditText" in raw:
        break
    d.press("back")
    time.sleep(2)

# 提交
print("   点击注册...")
raw = d.dump_hierarchy()
root = ET.fromstring(raw.encode("utf-8"))
hit = False
for n in root.iter("node"):
    if n.get("class") == "android.widget.Button" and n.get("clickable") == "true":
        b = n.get("bounds", "")
        parts = b.replace("][", "|").replace("[", "").replace("]", "").split("|")
        if len(parts) == 2:
            y1 = int(parts[0].split(",")[1])
            y2 = int(parts[1].split(",")[1])
            if 1250 <= y1 <= 1400:
                x1, x2 = int(parts[0].split(",")[0]), int(parts[1].split(",")[0])
                d.click((x1 + x2) // 2, (y1 + y2) // 2)
                hit = True
                break
if not hit:
    d.click(540, 1427)

print("\n3. 等待结果...")
for _ in range(15):
    raw = d.dump_hierarchy()
    texts = [n.get("text", "") for n in ET.fromstring(raw.encode("utf-8")).iter("node") if n.get("text", "")]
    edits = [n for n in ET.fromstring(raw.encode("utf-8")).iter("node") if n.get("class") == "android.widget.EditText"]
    ec = len(edits)
    
    if ec >= 4:
        print("\n   ✓ 验证码页！")
        code = input("   验证码: ").strip()
        d.click(300, 750)
        time.sleep(1)
        d.send_keys(code)
        time.sleep(3)
        break
    elif ec >= 2 and ec <= 3:
        print("\n   ✓ 密码页！")
        d(className="android.widget.EditText", instance=1).click()
        d(className="android.widget.EditText", instance=1).set_text(PASSWORD)
        time.sleep(1)
        d(className="android.widget.EditText", instance=2).click()
        d(className="android.widget.EditText", instance=2).set_text(PASSWORD)
        time.sleep(1)
        d(text="提交").click()
        time.sleep(5)
        break
    elif "3 of 3" in raw:
        break
    time.sleep(2)
else:
    print("\n   × 未到下一步")
    print("   texts:", [t for t in texts if t][:10])

for _ in range(3):
    raw = d.dump_hierarchy()
    if "3 of 3" in raw:
        print("\n✓✓✓ 注册成功！")
        break
    if "通知" in raw:
        for t in ["不允许", "Don't Allow"]:
            btn = d(text=t)
            if btn.exists(timeout=1):
                btn.click()
                time.sleep(2)
                break
        else:
            d.click(539, 2065)
    time.sleep(3)

print("=" * 50)
print("完成！")
print("=" * 50)
