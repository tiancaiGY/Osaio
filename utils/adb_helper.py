"""adb 辅助工具：解析目标设备序列号 + 读取手机系统/机型/目标 App 版本。

集中管理 adb 调用，供报告（测试环境采集）与用例（pm clear / 通知监听）复用。
所有函数尽力而为：拿不到就返回 None，绝不抛出。
"""
import os
import re
import subprocess
import time

APP_PACKAGE = "com.afar.osaio"


def resolve_serial(driver=None):
    """确定 adb 目标设备序列号。

    优先级：环境变量 OSAIO_DEVICE_SERIAL / ANDROID_SERIAL → driver 会话 caps
    (udid/deviceName) → config/caps.yaml 的 deviceName → `adb devices` 唯一设备。
    多设备且无法判定时返回 None（调用方应退回裸 adb，仅单设备可用）。
    """
    env = os.environ.get("OSAIO_DEVICE_SERIAL") or os.environ.get("ANDROID_SERIAL")
    if env:
        return env
    if driver is not None:
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
        dev = (load_config().get("android", {}) or {}).get("deviceName")
        if dev:
            return dev
    except Exception:
        pass
    # 兜底：adb devices 只有一台时用它
    try:
        r = subprocess.run(["adb", "devices"], capture_output=True, timeout=10)
        out = (r.stdout or b"").decode("utf-8", errors="replace")
        devs = [ln.split("\t")[0] for ln in out.splitlines()[1:]
                if ln.strip() and ln.strip().endswith("device")]
        if len(devs) == 1:
            return devs[0]
    except Exception:
        pass
    return None


def adb_args(serial):
    """构造 `adb [-s serial]` 前缀参数列表。"""
    return ["adb"] + (["-s", serial] if serial else [])


def _sh(serial, *args, timeout=15):
    """在目标设备上执行 `adb -s <serial> <args...>`，返回 stdout（失败返回 ""）。

    用 bytes + errors='replace' 显式 UTF-8 解码：dumpsys 输出常含非 GBK 字节，
    Windows 默认 locale(GBK) 解码会抛 UnicodeDecodeError（曾导致通知解析全崩）。
    """
    try:
        r = subprocess.run(adb_args(serial) + list(args),
                           capture_output=True, timeout=timeout)
        return (r.stdout or b"").decode("utf-8", errors="replace")
    except Exception:
        return ""


def getprop(serial, name):
    """读取单个系统属性，失败返回 None。"""
    v = _sh(serial, "shell", "getprop", name).strip()
    return v or None


def device_info(serial):
    """返回手机系统/机型信息 dict：{系统, 型号}（尽力而为）。"""
    info = {}
    rel = getprop(serial, "ro.build.version.release")
    sdk = getprop(serial, "ro.build.version.sdk")
    if rel:
        info["系统"] = f"Android {rel}" + (f" (SDK {sdk})" if sdk else "")
    brand = getprop(serial, "ro.product.manufacturer")
    model = getprop(serial, "ro.product.model")
    if brand or model:
        info["型号"] = " ".join(x for x in (brand, model) if x)
    return info


def app_version(serial, package=APP_PACKAGE):
    """读取目标 App 的 versionName(+versionCode)，失败返回 None。"""
    out = _sh(serial, "shell", "dumpsys", "package", package)
    if not out:
        return None
    name = re.search(r"versionName=(\S+)", out)
    code = re.search(r"versionCode=(\d+)", out)
    if not name:
        return None
    return f"{name.group(1)}" + (f" ({code.group(1)})" if code else "")


# ---- IoT 推送侦测消息（通知栏）监听 ----
# 真机确认：OSAIO 侦测推送落在通知渠道 PUSH_NOTIFY_ID（importance=4），
# title="Osaio Notice"，text="Device <名称> <Motion|Sound> Detected"，每条带 when=<epoch ms>。
# 判定“收到新推送”= 出现比基线更晚(when 更大)的 PUSH_NOTIFY_ID 记录。
PUSH_CHANNEL = "PUSH_NOTIFY_ID"


def latest_push_when(serial, package=APP_PACKAGE, channel=PUSH_CHANNEL):
    """返回目标 App 在指定通知渠道上最新一条推送的 when 时间戳(int, epoch ms)；无则 0。

    解析 `dumpsys notification --noredact`：定位到属于本 App 且 channel 匹配的通知块，
    取其中所有 when=<num> 的最大值。any 解析失败一律返回 0（视为无基线）。
    """
    out = _sh(serial, "shell", "dumpsys", "notification", "--noredact", timeout=20)
    if not out:
        return 0
    whens = []
    # 简化稳健：只要该行属于本 App 的 PUSH 渠道上下文，就收集其后出现的 when
    # 直接全局扫描 when=<num>，并要求全文包含本 App 的 PUSH 渠道（避免误统计其它 App）。
    if package not in out or channel not in out:
        return 0
    for m in re.finditer(r"when=(\d{10,})", out):
        try:
            whens.append(int(m.group(1)))
        except Exception:
            pass
    return max(whens) if whens else 0


def latest_push_text(serial, package=APP_PACKAGE):
    """返回最近一条推送的 title/text（best-effort），用于日志/报告说明。"""
    out = _sh(serial, "shell", "dumpsys", "notification", "--noredact", timeout=20)
    if not out or package not in out:
        return None
    texts = re.findall(r"android\.text=String \(([^)]+)\)", out)
    return texts[0] if texts else None


def wait_for_new_push(serial, baseline_when, timeout=180, interval=5,
                      package=APP_PACKAGE, channel=PUSH_CHANNEL):
    """轮询等待出现比 baseline_when 更新的 App 推送；命中返回其 when，否则超时返回 0。

    用于 IoT 侦测消息验证：设备每分钟触发一次侦测推送，可持续监听。
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        latest = latest_push_when(serial, package=package, channel=channel)
        if latest > baseline_when:
            return latest
        time.sleep(interval)
    return 0

