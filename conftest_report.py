"""[已弃用] 报告钩子已合并进根目录 conftest.py（pytest 只自动加载 conftest.py，
不会加载本文件）。保留仅作历史参考，请勿再启用本文件——否则会与 conftest.py 里的
pytest_configure / pytest_runtest_makereport / pytest_sessionfinish 钩子重复注册。

可视化报告现由 conftest.py + utils/report_generator.py 提供，运行任意 pytest 命令
即自动在 --report-dir（默认 reports/）生成 test_report_<时间戳>.html 与 .json。
"""
"""Pytest配置文件 - 自动生成可视化测试报告"""
import pytest
import time
import os
from utils.report_generator import TestReportGenerator, TestReportHook


# 全局报告生成器
report_generator = None
report_hook = None


def pytest_configure(config):
    """pytest配置初始化"""
    global report_generator, report_hook
    
    # 创建报告生成器
    report_generator = TestReportGenerator(
        report_dir="reports",
        report_title="Osaio UI 自动化测试报告"
    )
    
    # 创建报告钩子
    report_hook = TestReportHook(report_generator)
    
    # 开始报告
    report_generator.start_report()
    
    print("\n" + "="*60)
    print("测试报告系统已启动")
    print(f"报告目录: {report_generator.report_dir}")
    print("="*60 + "\n")


def pytest_unconfigure(config):
    """pytest清理"""
    global report_generator, report_hook
    
    if report_generator:
        # 结束报告
        report_generator.end_report()
        
        # 生成HTML报告
        html_path = report_generator.generate_html_report()
        
        # 生成JSON报告
        json_path = report_generator.generate_json_report()
        
        print("\n" + "="*60)
        print("测试报告已生成")
        print(f"HTML报告: {html_path}")
        print(f"JSON报告: {json_path}")
        print("="*60 + "\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """钩子：测试执行后生成报告"""
    outcome = yield
    report = outcome.get_result()
    
    global report_generator, report_hook
    
    if report_generator and report_hook:
        # 只在测试调用阶段处理
        if call.when == "call":
            # 获取测试名称
            test_name = item.nodeid
            
            # 确定测试状态
            if report.passed:
                status = "passed"
            elif report.failed:
                status = "failed"
            elif report.skipped:
                status = "skipped"
            else:
                status = "error"
            
            # 获取测试耗时
            duration = call.duration if hasattr(call, 'duration') else 0
            
            # 获取错误消息
            error_message = None
            if report.failed:
                error_message = str(call.excinfo.value) if call.excinfo else None
            
            # 尝试获取截图
            screenshot_path = None
            if report.failed and "driver" in item.funcargs:
                try:
                    driver = item.funcargs["driver"]
                    screenshot_path = report_generator.save_screenshot(
                        driver=driver,
                        test_name=test_name.replace("::", "_").replace("/", "_"),
                        step_name="failure"
                    )
                except Exception as e:
                    print(f"保存失败截图时出错: {e}")
            
            # 添加测试结果
            report_generator.add_test_result(
                test_name=test_name,
                status=status,
                duration=duration,
                error_message=error_message,
                screenshot_path=screenshot_path
            )


# 可选：添加命令行参数
def pytest_addoption(parser):
    """添加命令行参数"""
    parser.addoption(
        "--report-dir",
        action="store",
        default="reports",
        help="测试报告目录"
    )
    
    parser.addoption(
        "--report-title",
        action="store",
        default="Osaio UI 测试报告",
        help="测试报告标题"
    )


# 可选：自动打开报告
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束"""
    global report_generator
    
    if report_generator:
        # 获取统计信息
        statistics = report_generator.generate_statistics()
        
        print("\n" + "="*60)
        print("测试统计:")
        print(f"  总测试数: {statistics['total_tests']}")
        print(f"  通过: {statistics['passed_tests']}")
        print(f"  失败: {statistics['failed_tests']}")
        print(f"  跳过: {statistics['skipped_tests']}")
        print(f"  错误: {statistics['error_tests']}")
        print(f"  通过率: {statistics['pass_rate']}%")
        print(f"  总耗时: {statistics['total_duration']}s")
        print("="*60 + "\n")