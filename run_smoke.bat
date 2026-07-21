@echo off
REM ============================================================
REM  一键运行「主功能测试」并生成报告
REM  用法：双击本文件，或命令行执行  run_smoke.bat
REM  前置：真机已连（adb devices 可见）、Appium 已在 127.0.0.1:4723 运行。
REM
REM  可选环境变量（运行前 set）：
REM    OSAIO_IOT_PUSH_TIMEOUT=90   IoT 推送监听秒数（默认 150）
REM    OSAIO_SKIP_IOT_PUSH=1       跳过 IoT 推送验证
REM    SMOKE_NO_RESET=1            跳过 pm clear（沿用现状调试）
REM ============================================================
setlocal
cd /d "%~dp0"

REM 优先用项目内 venv 的 python，否则用 PATH 里的 python
set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

echo [run_smoke] 使用解释器: %PY%
echo [run_smoke] 开始运行主功能 smoke 测试...
"%PY%" -m pytest tests\test_smoke_main_flow.py -m smoke -s ^
    --report-title "OSAIO 主功能测试报告" ^
    --report-dir reports
set "RC=%ERRORLEVEL%"

echo.
echo [run_smoke] 测试结束（退出码 %RC%）。报告在 reports\ 目录下最新的 test_report_*.html
REM 自动打开最新生成的 HTML 报告
for /f "delims=" %%F in ('dir /b /o-d "reports\test_report_*.html" 2^>nul') do (
    echo [run_smoke] 打开报告: reports\%%F
    start "" "reports\%%F"
    goto :opened
)
:opened

endlocal & exit /b %RC%
