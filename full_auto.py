import uiautomator2 as u2
import requests, re, time

d = u2.connect_usb('R5CT34HNGTN')

def get_code(email, timeout=90):
    username, domain = email.split('@')
    known_ids = set()
    start = time.time()
    while time.time() - start < timeout:
        url = 'https://tempmail.plus/api/mails?email=%s@%s&epin=&limit=5' % (username, domain)
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for mail in data.get('mail_list', []):
            mid = mail.get('mail_id')
            if mid in known_ids:
                continue
            known_ids.add(mid)
            if 'osaio' in mail.get('from_mail', '').lower():
                detail_url = 'https://tempmail.plus/api/mails/%s?email=%s@%s&epin=' % (mid, username, domain)
                detail = requests.get(detail_url, timeout=10).json()
                body = (detail.get('text','') or '') + (detail.get('html','') or '')
                m = re.search(r'验证码[是:：\s]*(\d{6})', body)
                if m:
                    return m.group(1)
        time.sleep(3)
    return None

# ===== REGISTER =====
print("=== REGISTER ===")
d.app_stop('com.afar.osaio')
d.app_clear('com.afar.osaio')
d.app_start('com.afar.osaio')
time.sleep(4)

for t in ["Agree", "同意"]:
    btn = d(text=t)
    if btn.exists(timeout=3): btn.click(); time.sleep(2); break
for t in ["让我们开始", "开始", "Start", "Get Started"]:
    btn = d(text=t)
    if btn.exists(timeout=3): btn.click(); time.sleep(2); break

d.click(781, 483)
time.sleep(2)

email = "testb11@mailto.plus"
e = d(className="android.widget.EditText", instance=0)
e.clear_text(); time.sleep(0.3)
e.set_text(email); time.sleep(2)
print("Email:", email)

d.touch.down(509, 1214); time.sleep(0.1)
d.touch.up(509, 1214); time.sleep(1)
print("Checkbox clicked")

btns = d(className="android.widget.Button")
for i in range(btns.count):
    top = btns[i].info.get('bounds', {}).get('top', 0)
    if 1250 < top < 1400:
        btns[i].click(); break
print("Send code clicked")

print("Waiting for verification code...")
code = get_code(email, timeout=90)
if not code: print("FAILED"); exit(1)
print("Got code:", code)

time.sleep(5)
d.click(10, 680); time.sleep(0.5)
d.send_keys(code); time.sleep(2)
print("Code entered")

time.sleep(3)
pw1 = d(className="android.widget.EditText", instance=1)
if pw1.exists(timeout=3): pw1.set_text("123456"); time.sleep(1)
pw2 = d(className="android.widget.EditText", instance=2)
if pw2.exists(timeout=3): pw2.set_text("123456"); time.sleep(1)
print("Password set")

for t in ['提交', 'Submit', 'Confirm']:
    btn = d(text=t)
    if btn.exists(timeout=2): btn.click(); print("Submitted"); break

time.sleep(10)
d.click(539, 2065); time.sleep(2)
print("Notification dismissed")

if '3 of 3' in d.dump_hierarchy():
    print("REGISTRATION SUCCESSFUL!")

# ===== LOGOUT =====
print("\n=== LOGOUT ===")
d(descriptionContains='3 of 3').click(); time.sleep(3)
d.click(540, 550); time.sleep(3)
d.click(555, 1978); time.sleep(2)
d.click(555, 1133); time.sleep(3)

if '欢迎来到OSAIO' in d.dump_hierarchy():
    print("LOGOUT SUCCESSFUL!")

# ===== LOGIN =====
print("\n=== LOGIN ===")
e = d(className="android.widget.EditText", instance=0)
e.clear_text(); time.sleep(0.3)
e.set_text(email); time.sleep(2)
print("Email filled")

p = d(className="android.widget.EditText", instance=1)
p.clear_text(); time.sleep(0.3)
p.set_text("123456"); time.sleep(2)
print("Password filled")

d.click(589, 1394); time.sleep(3)
dump = d.dump_hierarchy()
if '通知' in dump:
    d.click(539, 2065); time.sleep(2)

if '3 of 3' in d.dump_hierarchy():
    print("LOGIN SUCCESSFUL!")
else:
    print("Login result unknown, checking...")
    import xml.etree.ElementTree as ET
    root = ET.fromstring(d.dump_hierarchy().encode('utf-8'))
    for node in root.iter('node'):
        txt = node.get('text', '')
        if txt and len(txt) > 2:
            print('  text=%s' % txt.replace(chr(8226),'.'))

print("\n=== DONE ===")
