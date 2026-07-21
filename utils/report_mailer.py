"""测试报告邮件发送工具。

把生成的 HTML 报告作为附件发到指定邮箱。所有配置走**环境变量**，不硬编码任何密码。
默认收件人 mark.guo@apemans.com，可配置。发件通道用企业邮箱 apemans.com 的 SMTP。

环境变量（发送前设置）：
  OSAIO_MAIL_SEND=1                     总开关：为 1 才真正发送（conftest 会话结束时据此判断）
  OSAIO_MAIL_TO=a@x.com,b@y.com         收件人（逗号分隔；默认 mark.guo@apemans.com）
  OSAIO_SMTP_HOST=smtp.feishu.cn        SMTP 服务器（默认飞书企业邮箱）
  OSAIO_SMTP_PORT=465                   端口（465=SSL，587=STARTTLS；默认 465）
  OSAIO_SMTP_USER=mark.guo@apemans.com  发件账号（同时作为 From）
  OSAIO_SMTP_PASSWORD=***               发件账号密码/授权码（飞书为"专用密码"）
  OSAIO_SMTP_FROM=robot@apemans.com     可选：自定义 From（默认取 USER）
  OSAIO_SMTP_SSL=1                       可选：1=SSL 直连(默认，端口465)，0=STARTTLS(端口587)

命令行用法（手动发送指定报告）：
  python -m utils.report_mailer reports/test_report_YYYYmmdd_HHMMSS.html
  # 不带参数则自动取 reports/ 下最新的 test_report_*.html
"""
import os
import glob
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime

DEFAULT_TO = "mark.guo@apemans.com"
DEFAULT_HOST = "smtp.feishu.cn"   # apemans.com 使用飞书企业邮箱
DEFAULT_PORT = 465


def _recipients():
    raw = os.environ.get("OSAIO_MAIL_TO", DEFAULT_TO)
    return [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]


def latest_report(report_dir="reports"):
    """返回 report_dir 下最新的 test_report_*.html；无则 None。"""
    files = sorted(glob.glob(os.path.join(report_dir, "test_report_*.html")),
                   key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def send_report(report_path=None, report_dir="reports", subject=None):
    """发送 HTML 报告到收件人。返回 (ok, message)。

    缺少 SMTP 账号/密码时**不报错**，返回 (False, 原因)，由调用方决定是否忽略——
    避免未配置邮箱时阻断测试流程。
    """
    report_path = report_path or latest_report(report_dir)
    if not report_path or not os.path.exists(report_path):
        return False, f"未找到报告文件: {report_path}"

    host = os.environ.get("OSAIO_SMTP_HOST", DEFAULT_HOST)
    port = int(os.environ.get("OSAIO_SMTP_PORT", str(DEFAULT_PORT)))
    user = os.environ.get("OSAIO_SMTP_USER")
    password = os.environ.get("OSAIO_SMTP_PASSWORD")
    sender = os.environ.get("OSAIO_SMTP_FROM", user or "")
    use_ssl = os.environ.get("OSAIO_SMTP_SSL", "1" if port == 465 else "0") == "1"
    to_list = _recipients()

    if not user or not password:
        return False, ("未配置 SMTP 账号/密码（OSAIO_SMTP_USER / OSAIO_SMTP_PASSWORD），跳过发送。"
                       "配置后重试即可。")
    if not to_list:
        return False, "未配置收件人（OSAIO_MAIL_TO）"

    # 组装邮件
    msg = EmailMessage()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg["Subject"] = subject or f"OSAIO 主功能测试报告 {ts}"
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)
    msg.set_content(
        f"OSAIO 主功能自动化测试报告\n生成时间: {ts}\n报告文件: {os.path.basename(report_path)}\n\n"
        f"（本邮件由自动化测试在 OSAIO_MAIL_SEND=1 时自动发送，报告见附件 HTML）")
    with open(report_path, "rb") as f:
        data = f.read()
    msg.add_attachment(data, maintype="text", subtype="html",
                       filename=os.path.basename(report_path))

    try:
        if use_ssl:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
                s.login(user, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.ehlo()
                s.starttls(context=ssl.create_default_context())
                s.login(user, password)
                s.send_message(msg)
        return True, f"报告已发送到 {', '.join(to_list)}"
    except Exception as e:
        return False, f"发送失败: {e}"


def send_report_if_enabled(report_path=None, report_dir="reports"):
    """仅当 OSAIO_MAIL_SEND=1 时发送（供 conftest 会话结束调用）。返回 (attempted, ok, message)。"""
    if os.environ.get("OSAIO_MAIL_SEND") != "1":
        return False, False, "OSAIO_MAIL_SEND != 1，未开启自动发送"
    ok, message = send_report(report_path=report_path, report_dir=report_dir)
    return True, ok, message


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    ok, message = send_report(report_path=path)
    print(("[OK] " if ok else "[FAIL] ") + message)
    sys.exit(0 if ok else 1)
