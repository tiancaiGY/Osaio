import json
import re
import time
from urllib import parse, request
from urllib.error import HTTPError, URLError

API_BASE = "https://tempmail.plus/api"


def _http_get(url, timeout=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def _build_email_parts(email):
    if "@" not in email:
        raise ValueError("邮箱地址必须包含 '@'")
    return email.split("@", 1)


def get_mail_list(email, limit=5, timeout=10):
    """获取临时邮箱列表中的邮件摘要。"""
    username, domain = _build_email_parts(email)
    url = f"{API_BASE}/mails?email={parse.quote(username)}@{parse.quote(domain)}&epin=&limit={limit}"
    try:
        data = _http_get(url, timeout=timeout)
    except (HTTPError, URLError, ValueError):
        return []

    if data.get("result"):
        return data.get("mail_list", [])
    return []


def get_mail_detail(mail_id, email, timeout=10):
    """获取邮件详情内容。"""
    username, domain = _build_email_parts(email)
    url = f"{API_BASE}/mails/{parse.quote(str(mail_id))}?email={parse.quote(username)}@{parse.quote(domain)}&epin="
    try:
        data = _http_get(url, timeout=timeout)
    except (HTTPError, URLError, ValueError):
        return None
    return data if data.get("result") else None


def extract_verification_code(mail_data):
    """从邮件正文或 HTML 中提取 6 位验证码。"""
    if not mail_data:
        return None

    text = mail_data.get("text", "") or ""
    html = mail_data.get("html", "") or ""
    body = text + "\n" + html

    patterns = [
        r"验证码[是:：\s]*(\d{6})",
        r"code[\s:：]*(\d{6})",
        r"verification[\s:：]*(\d{6})",
        r"token[\s:：]*(\d{6})",
        r"([0-9]{6})",
    ]

    for pat in patterns:
        match = re.search(pat, body, re.IGNORECASE)
        if match:
            code = match.group(1)
            if code not in {"000000", "010201"}:
                return code
    return None


def wait_for_verification_code(email, timeout=120, check_interval=3, sender_hint=None):
    """轮询临时邮箱，直到收到验证码邮件或超时。"""
    sender_hint = sender_hint or "osaio"
    username, domain = _build_email_parts(email)
    known_ids = set()
    start_time = time.time()

    while time.time() - start_time < timeout:
        mail_list = get_mail_list(email, limit=10, timeout=10)
        for mail in mail_list:
            mid = mail.get("mail_id")
            if not mid or mid in known_ids:
                continue
            known_ids.add(mid)

            sender = mail.get("from_mail", "") or ""
            subject = mail.get("subject", "") or ""
            if sender_hint.lower() in sender.lower() or "验证" in subject or "code" in subject.lower():
                detail = get_mail_detail(mid, email, timeout=10)
                if detail:
                    code = extract_verification_code(detail)
                    if code:
                        return code, mid
        time.sleep(check_interval)
    return None, None
