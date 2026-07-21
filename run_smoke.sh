#!/usr/bin/env bash
# ============================================================
#  一键运行「主功能测试」并生成报告（git-bash / Linux / macOS / CI 通用）
#  用法：  ./run_smoke.sh
#  前置：真机已连（adb devices 可见）、Appium 已在 127.0.0.1:4723 运行。
#
#  可选环境变量：
#    OSAIO_IOT_PUSH_TIMEOUT=90   IoT 推送监听秒数（默认 150）
#    OSAIO_SKIP_IOT_PUSH=1       跳过 IoT 推送验证
#    SMOKE_NO_RESET=1            跳过 pm clear（沿用现状调试）
#
#  参数：
#    --mail   测试结束后把报告邮件发到收件人（等价 OSAIO_MAIL_SEND=1）
#             收件人默认 mark.guo@apemans.com，可用 OSAIO_MAIL_TO 覆盖；
#             SMTP 需先配好 OSAIO_SMTP_USER / OSAIO_SMTP_PASSWORD（见 utils/report_mailer.py）。
# ============================================================
set -u
cd "$(dirname "$0")"

# 解析参数：--mail 开启报告邮件发送
if [ "${1:-}" = "--mail" ]; then export OSAIO_MAIL_SEND=1; fi
[ "${OSAIO_MAIL_SEND:-}" = "1" ] && echo "[run_smoke] 报告邮件发送已开启（OSAIO_MAIL_SEND=1）"

# 优先用项目内 venv 的 python
if [ -x "venv/Scripts/python.exe" ]; then PY="venv/Scripts/python.exe"      # Windows venv
elif [ -x "venv/bin/python" ]; then PY="venv/bin/python"                    # *nix venv
else PY="python"; fi

echo "[run_smoke] 使用解释器: $PY"
echo "[run_smoke] 开始运行主功能 smoke 测试..."
"$PY" -m pytest tests/test_smoke_main_flow.py -m smoke -s \
    --report-title "OSAIO 主功能测试报告" \
    --report-dir reports
RC=$?

echo
echo "[run_smoke] 测试结束（退出码 $RC）。报告在 reports/ 目录下最新的 test_report_*.html"
# 尽力自动打开最新报告（有 xdg-open / open 时）
latest="$(ls -t reports/test_report_*.html 2>/dev/null | head -1)"
if [ -n "${latest:-}" ]; then
    echo "[run_smoke] 最新报告: $latest"
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$latest" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1; then open "$latest" >/dev/null 2>&1 || true
    fi
fi
exit $RC
