"""按需抓取当前屏幕：截图 + page_source + com.afar.osaio ID 列表。用法：python capture_state.py <tag>"""
import re, sys, time
from utils.driver_helper import load_config
from appium import webdriver
from appium.options.android import UiAutomator2Options

tag = sys.argv[1] if len(sys.argv) > 1 else "state"
cfg = load_config()
opts = UiAutomator2Options().load_capabilities(cfg["android"])
# 复用当前 App 状态：不重启、不清数据
opts.set_capability("appium:noReset", True)
opts.set_capability("appium:autoLaunch", False)
url = f"http://{cfg['appium_server']['host']}:{cfg['appium_server']['port']}/wd/hub"
d = webdriver.Remote(url, options=opts)
try:
    d.save_screenshot(f"reports/cap_{tag}.png")
    xml = d.page_source
    open(f"reports/cap_{tag}.xml", "w", encoding="utf-8").write(xml)
    ids = sorted(set(re.findall(r'resource-id="(com\.afar\.osaio:id/[^"]+)"', xml)))
    ts = [t for t in re.findall(r'text="([^"]+)"', xml) if t.strip()][:30]
    out = f"[{tag}] IDS: {[i.split('/')[-1] for i in ids]}\n[{tag}] TEXTS: {ts}"
    sys.stdout.buffer.write(out.encode("utf-8"))
finally:
    d.quit()
