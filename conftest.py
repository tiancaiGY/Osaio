"""pytest 全局 fixture 配置"""
import sys


def _force_utf8_output():
    """修复 Windows 控制台 / 重定向日志中的中文乱码：强制 stdout/stderr 使用 UTF-8。

    - reconfigure：让 Python 以 UTF-8 编码写出（覆盖 GBK/cp936 默认值）。
    - SetConsoleOutputCP(65001)：把 Windows 控制台代码页切到 UTF-8。
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass


_force_utf8_output()

import pytest
from utils.driver_helper import create_driver
from utils.accounts import (
    get_account,
    get_all_accounts,
    get_wrong_password,
    get_register_default_password,
)


def pytest_addoption(parser):
    parser.addoption(
        "--platform", action="store", default="android",
        help="测试平台: android 或 ios"
    )
    # 可视化 HTML/JSON 报告选项（由本文件底部的报告钩子使用）
    parser.addoption(
        "--report-dir", action="store", default="reports",
        help="测试报告输出目录"
    )
    parser.addoption(
        "--report-title", action="store", default="Osaio UI 自动化测试报告",
        help="测试报告标题"
    )


@pytest.fixture(scope="session")
def accounts():
    """所有具名测试账号 {key: Account(account, password)}（支持环境变量覆盖）。"""
    return get_all_accounts()


@pytest.fixture(scope="session")
def account():
    """按名字取账号的工厂：account("primary") -> Account(account, password)。"""
    return get_account


@pytest.fixture(scope="session")
def wrong_password():
    """错误密码用例使用的密码。"""
    return get_wrong_password()


@pytest.fixture(scope="session")
def register_default_password():
    """注册脚本/用例默认密码。"""
    return get_register_default_password()


@pytest.fixture(scope="session")
def driver(request):
    """创建并管理 Appium driver 生命周期"""
    platform = request.config.getoption("--platform")
    d = create_driver(platform)
    yield d
    d.quit()


@pytest.fixture(autouse=True)
def test_setup(driver):
    """每个测试用例前后的处理"""
    yield
    # 测试结束后可以做清理，比如回到首页


# ---------------------------------------------------------------------------
# 可视化测试报告（HTML + JSON）
#
# 复用 utils/report_generator.py，在测试会话中收集每个用例的结果/耗时/失败截图，
# 会话结束后生成品牌化 HTML 报告与 JSON 报告到 --report-dir（默认 reports/）。
# 报告系统的任何异常都被吞掉，绝不影响测试本身的通过/失败。
# ---------------------------------------------------------------------------
from utils.report_generator import TestReportGenerator

_report_generator = None
# 当前用例的步骤缓冲（供 smoke 等"分步骤"用例填充；makereport 钩子取用后清空）。
_current_test_steps = []


def _record_step(step_name, status, duration=0, message=None):
    """把一个步骤结果追加到当前用例的步骤缓冲（报告里会展开显示）。

    任何异常都吞掉——报告记录绝不能影响用例本身的通过/失败。
    """
    global _report_generator, _current_test_steps
    try:
        if _report_generator is not None:
            _current_test_steps.append(
                _report_generator.add_test_step(step_name, status, duration, message)
            )
    except Exception:
        pass


@pytest.fixture
def report_step():
    """给用例记录步骤级结果的辅助：report_step("步骤名", "passed", 1.2, "备注")。

    步骤会在报告的该用例条目下展开显示（passed/failed/skipped）。
    """
    return _record_step


def _set_report_env(**info):
    """向报告注入测试环境信息（设备/邮箱/国家等），显示在报告“测试环境”表。异常吞掉。"""
    global _report_generator
    try:
        if _report_generator is not None:
            _report_generator.set_environment(**info)
    except Exception:
        pass


@pytest.fixture
def report_env():
    """用例注入“测试环境”信息：report_env(测试邮箱=..., 注册国家=...)。"""
    return _set_report_env


def pytest_configure(config):
    """会话开始：初始化报告生成器。"""
    global _report_generator
    try:
        _report_generator = TestReportGenerator(
            report_dir=config.getoption("--report-dir"),
            report_title=config.getoption("--report-title"),
        )
        _report_generator.start_report()
    except Exception as e:
        _report_generator = None
        print(f"报告系统初始化失败（不影响测试执行）: {e}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """收集每个用例 call 阶段的结果；失败时保存截图。"""
    outcome = yield
    report = outcome.get_result()

    if _report_generator is None or call.when != "call":
        return

    try:
        if report.passed:
            status = "passed"
        elif report.failed:
            status = "failed"
        elif report.skipped:
            status = "skipped"
        else:
            status = "error"

        duration = getattr(call, "duration", 0) or 0
        error_message = None
        if report.failed and call.excinfo:
            error_message = str(call.excinfo.value)

        # 失败时尝试保存截图（用例需注入了 driver fixture）
        screenshot_path = None
        if report.failed and "driver" in getattr(item, "funcargs", {}):
            try:
                screenshot_path = _report_generator.save_screenshot(
                    driver=item.funcargs["driver"],
                    test_name=item.nodeid.replace("::", "_").replace("/", "_"),
                    step_name="failure",
                )
            except Exception as e:
                print(f"保存失败截图时出错: {e}")

        _report_generator.add_test_result(
            test_name=item.nodeid,
            status=status,
            duration=duration,
            error_message=error_message,
            screenshot_path=screenshot_path,
            steps=list(_current_test_steps),
        )
    except Exception as e:
        print(f"记录测试结果失败（不影响测试执行）: {e}")
    finally:
        # 无论成功与否都清空步骤缓冲，避免串到下一个用例
        _current_test_steps.clear()


def pytest_sessionfinish(session, exitstatus):
    """会话结束：打印统计、生成 HTML/JSON 报告。"""
    global _report_generator
    if _report_generator is None:
        return
    try:
        _report_generator.end_report()
        stats = _report_generator.generate_statistics()
        html_path = _report_generator.generate_html_report()
        json_path = _report_generator.generate_json_report()

        print("\n" + "=" * 60)
        print("测试统计:")
        print(f"  总测试数: {stats['total_tests']}  通过: {stats['passed_tests']}  "
              f"失败: {stats['failed_tests']}  跳过: {stats['skipped_tests']}  "
              f"错误: {stats['error_tests']}")
        print(f"  通过率: {stats['pass_rate']}%   总耗时: {stats['total_duration']}s")
        print(f"  HTML 报告: {html_path}")
        print(f"  JSON 报告: {json_path}")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"生成报告失败（不影响测试执行）: {e}")
        html_path = None

    # 可选：把报告邮件发到收件人（仅当 OSAIO_MAIL_SEND=1）。任何异常都吞掉，绝不影响测试结果。
    try:
        from utils.report_mailer import send_report_if_enabled
        attempted, ok, message = send_report_if_enabled(report_path=html_path)
        if attempted:
            print(f"[报告邮件] {'成功' if ok else '未发送'}: {message}")
    except Exception as e:
        print(f"发送报告邮件失败（不影响测试执行）: {e}")
