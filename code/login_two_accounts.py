import sys, time, yaml, uiautomator2 as u2
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

# 复用项目根目录的账号加载器（集中管理账号密码，支持环境变量覆盖）
sys.path.insert(0, str(BASE_DIR.parent))
from utils.accounts import get_account

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def find_elem(d, selectors):
    for s in selectors:
        e = d(**s)
        if e.exists(timeout=1):
            return e
    return None

def skip_onboarding(d):
    for _ in range(5):
        if (d(text="Forgot Password").exists(timeout=1) or
            d(text="忘记密码").exists(timeout=1) or
            d(className="android.widget.EditText").exists(timeout=1)):
            return True
        for txt in ["同意", "Agree"]:
            btn = d(text=txt)
            if btn.exists(timeout=1):
                btn.click()
                time.sleep(1.5)
                break
        else:
            btn = d(className="android.widget.Button")
            if btn.exists(timeout=1):
                btn.click()
                time.sleep(1.5)
        for txt in ["开始", "Start", "Get Started"]:
            btn = d(textContains=txt)
            if btn.exists(timeout=1):
                btn.click()
                time.sleep(1.5)
                break
        time.sleep(1.5)
    return False

def login(d, email, password):
    email_elem = find_elem(d, [
        {"className": "android.widget.EditText", "instance": 0},
        {"resourceId": "email_input"},
    ])
    if not email_elem or not email_elem.exists(timeout=2):
        return False
    email_elem.click()
    time.sleep(0.3)
    email_elem.clear_text()
    email_elem.send_keys(email)
    time.sleep(0.5)

    pwd = find_elem(d, [
        {"className": "android.widget.EditText", "instance": 1},
        {"resourceId": "password_input"},
    ])
    if not pwd or not pwd.exists(timeout=2):
        return False
    pwd.click()
    time.sleep(0.3)
    pwd.clear_text()
    pwd.set_text(password)
    time.sleep(0.3)

    btn = find_elem(d, [
        {"className": "android.widget.Button", "instance": 0},
        {"resourceId": "login_button"},
        {"text": "Sign In"}, {"text": "Log In"}, {"text": "登录"},
    ])
    if not btn or not btn.exists(timeout=2):
        btn = d(className="android.widget.Button", instance=0)
    if not btn.exists(timeout=2):
        return False
    btn.click()
    return True

def wait_login_success(d, screenshots_dir, email):
    for s in range(15):
        on_login = (d(text="Forgot Password").exists(timeout=0.3) or
                    d(text="忘记密码").exists(timeout=0.3) or
                    d(className="android.widget.EditText").exists(timeout=0.3))
        if not on_login:
            name = email.split('@')[0]
            d.screenshot(str(screenshots_dir / f"{name}_success.png"))
            return True
        time.sleep(1)
    return False

def dismiss_system_dialogs(d):
    """关闭登录后可能弹出的系统对话框"""
    for _ in range(5):
        all_texts = get_all_texts(d)
        page_str = " ".join(all_texts)

        if any(kw in page_str for kw in ["通知", "notification", "权限", "permission"]):
            print(f"  检测到弹窗")
            # "不允许" Button 坐标 [130,1998][949,2132] → 中心 (539, 2065)
            click_xy(d, 539, 2065)
            time.sleep(1)
            print(f"  已点击: 不允许")
            return True
        break
    return False

def click_text(d, target_text, y_min=0):
    """通过 dump XML 按坐标点击指定文本"""
    try:
        raw = d.dump_hierarchy()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw.encode("utf-8"))
        for node in root.iter("node"):
            txt = node.get("text", "")
            bounds = node.get("bounds", "")
            if target_text in txt and "[" in bounds:
                parts = bounds.strip("[]").split("][")
                if len(parts) == 2:
                    c1 = [int(x) for x in parts[0].split(",")]
                    c2 = [int(x) for x in parts[1].split(",")]
                    cx = (c1[0] + c2[0]) // 2
                    cy = (c1[1] + c2[1]) // 2
                    if cy >= y_min:
                        d.click(cx, cy)
                        print(f"  点击: {txt} (坐标 {cx},{cy})")
                        return True, cx, cy
    except:
        pass
    return False, None, None

def click_parent_button(d, target_text):
    """找到包含指定文本的可点击 Button 并点击（通过 XML dump）"""
    try:
        raw = d.dump_hierarchy()
        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw.encode("utf-8"))
        # 找到所有 Button
        for btn in root.iter("node"):
            if btn.get("class") == "android.widget.Button" and btn.get("clickable") == "true":
                bounds = btn.get("bounds", "")
                if "[" not in bounds:
                    continue
                # 检查 Button 内是否包含目标文本
                inner_text = _find_text_in_children(btn, target_text)
                if inner_text:
                    parts = bounds.strip("[]").split("][")
                    c1 = [int(x) for x in parts[0].split(",")]
                    c2 = [int(x) for x in parts[1].split(",")]
                    cx = (c1[0] + c2[0]) // 2
                    cy = (c1[1] + c2[1]) // 2
                    d.click(cx, cy)
                    print(f"  点击Button: '{target_text}' (坐标 {cx},{cy})")
                    return True
    except:
        pass
    return False

def _find_text_in_children(node, target):
    """递归查找节点内是否包含指定文本"""
    if target in node.get("text", ""):
        return True
    for child in node:
        if _find_text_in_children(child, target):
            return True
    return False

def get_all_texts(d):
    """获取当前页面所有文本"""
    texts = []
    try:
        raw = d.dump_hierarchy()
        import xml.etree.ElementTree as ET
        for node in ET.fromstring(raw.encode("utf-8")).iter("node"):
            t = node.get("text", "")
            bounds = node.get("bounds", "")
            if t and "[" in bounds:
                texts.append(t)
    except:
        pass
    return texts

def click_xy(d, x, y):
    """直接 tap 坐标"""
    d.click(x, y)

def logout(d):
    """登录成功后退出登录：首页 → 账户 tab → 点击头像 → 退出登录 → 确认"""
    time.sleep(2)

    # 1. 关闭通知弹窗
    dismiss_system_dialogs(d)
    time.sleep(1)

    # 2. 点击底部"账户"tab（desc="账户, tab, 3 of 3"）
    print(f"  点击账户tab...")
    d(descriptionContains="3 of 3").click()
    time.sleep(2)
    print(f"  已进入账户页")

    # 3. 点击头像区域 ViewGroup [432,257][648,472] → 中心 (540, 364)
    print(f"  点击头像...")
    click_xy(d, 540, 364)
    time.sleep(3)
    print(f"  已进入个人资料页")

    # 3.5 关闭可能出现的通知弹窗
    dismiss_system_dialogs(d)
    time.sleep(1)

    # 4. 点击"退出登录" Button [267,1886][814,2070] → 中心 (540, 1978)
    print(f"  点击退出登录...")
    click_xy(d, 540, 1978)
    time.sleep(3)

    # 5. 确认退出弹窗 - 对话框的确认按钮也是"退出登录" at (555, 1133)
    all_texts = get_all_texts(d)
    print(f"  弹窗文本: {all_texts[:10]}")
    if "确定" in " ".join(all_texts) or "退出" in " ".join(all_texts):
        print(f"  点击对话框中'退出登录'...")
        click_xy(d, 555, 1133)
        time.sleep(3)
        print(f"  已确认退出")
    else:
        print(f"  无弹窗，继续")

    # 6. 等待回到登录页（需要再跳过引导页，因为退出后可能回到首次启动）
    for _ in range(10):
        if (d(text="Forgot Password").exists(timeout=1) or
            d(text="忘记密码").exists(timeout=1) or
            d(className="android.widget.EditText").exists(timeout=1)):
            print(f"  已退出登录，回到登录页")
            return True
        time.sleep(2)

    # 可能回到了引导页，再跳一次
    print(f"  未检测到登录页，可能回到引导页...")
    if skip_onboarding(d):
        print(f"  跳过引导页后到达登录页")
        return True

    print(f"  WARNING: 退出后未检测到登录页")
    return False

def debug_screenshot(d, tag, screenshots_dir=None):
    try:
        if screenshots_dir:
            d.screenshot(str(screenshots_dir / f"debug_{tag}.png"))
        else:
            d.screenshot(f"screenshots/debug_{tag}.png")
    except:
        pass

def main():
    config = load_config()
    serial = config["device"]["serial"]
    package = config["app"]["package_name"]
    screenshots_dir = BASE_DIR / "_internal" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    accounts = [
        tuple(get_account("switch_a")),
        tuple(get_account("switch_b")),
    ]

    print(f"连接设备: {serial}")
    d = u2.connect(serial)
    d.implicitly_wait(config.get("timeout", 10))
    print(f"设备已连接: {d.info.get('productName', 'unknown')}")

    # ---- 账号1：从登录到退出 ----
    email1, pwd1 = accounts[0]
    print(f"\n{'='*50}")
    print(f"[1/2] {email1} → 登录 → 退出")
    print(f"{'='*50}")

    d.app_stop(package)
    d.app_clear(package)
    time.sleep(1)
    d.app_start(package)
    time.sleep(4)
    skip_onboarding(d)
    time.sleep(1)

    if not login(d, email1, pwd1):
        print(f"  RESULT: FAIL (登录失败)")
        return
    print(f"  已点击登录按钮")

    if wait_login_success(d, screenshots_dir, email1):
        print(f"  登录成功!")
        debug_screenshot(d, "logged_in_home", screenshots_dir)

        # 退出登录
        print(f"  执行退出登录...")
        logout(d)
    else:
        print(f"  RESULT: FAIL (登录超时)")
        return

    # ---- 账号2：直接登录（不清数据） ----
    email2, pwd2 = accounts[1]
    print(f"\n{'='*50}")
    print(f"[2/2] {email2} → 登录")
    print(f"{'='*50}")

    # 等待一下确保在登录页
    time.sleep(2)

    if not login(d, email2, pwd2):
        print(f"  RESULT: FAIL (登录失败)")
        return
    print(f"  已点击登录按钮")

    if wait_login_success(d, screenshots_dir, email2):
        print(f"  登录成功!")
    else:
        print(f"  RESULT: FAIL (登录超时)")

    print(f"\n{'='*50}")
    print(f"完成! APP 保留在登录成功状态")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
