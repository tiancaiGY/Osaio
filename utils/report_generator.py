"""可视化测试报告生成工具"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import base64


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, report_dir: str = "reports", report_title: str = "Osaio UI 测试报告"):
        """
        初始化报告生成器
        :param report_dir: 报告目录
        :param report_title: 报告标题
        """
        self.report_dir = report_dir
        self.report_title = report_title
        self.test_results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
        
        # 创建报告目录
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(os.path.join(self.report_dir, "screenshots"), exist_ok=True)
    
    def start_report(self):
        """开始生成报告"""
        self.start_time = datetime.now()
        print(f"开始生成测试报告: {self.start_time}")
    
    def end_report(self):
        """结束报告生成"""
        self.end_time = datetime.now()
        print(f"结束生成测试报告: {self.end_time}")
    
    def add_test_result(self, test_name: str, status: str, duration: float = 0,
                       error_message: str = None, screenshot_path: str = None,
                       steps: List[Dict[str, Any]] = None):
        """
        添加测试结果
        :param test_name: 测试名称
        :param status: 测试状态 (passed, failed, skipped, error)
        :param duration: 测试耗时（秒）
        :param error_message: 错误消息
        :param screenshot_path: 截图路径
        :param steps: 测试步骤列表
        """
        test_result = {
            "test_name": test_name,
            "status": status,
            "duration": duration,
            "error_message": error_message,
            "screenshot_path": screenshot_path,
            "steps": steps or [],
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(test_result)
    
    def add_test_step(self, step_name: str, status: str, duration: float = 0,
                     message: str = None, screenshot: str = None):
        """
        添加测试步骤
        :param step_name: 步骤名称
        :param status: 步骤状态
        :param duration: 步骤耗时
        :param message: 步骤消息
        :param screenshot: 截图路径
        """
        step = {
            "step_name": step_name,
            "status": status,
            "duration": duration,
            "message": message,
            "screenshot": screenshot,
            "timestamp": datetime.now().isoformat()
        }
        
        return step
    
    def save_screenshot(self, driver, test_name: str, step_name: str = None) -> str:
        """
        保存截图
        :param driver: Appium driver
        :param test_name: 测试名称
        :param step_name: 步骤名称
        :return: 截图路径
        """
        try:
            # 生成截图文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if step_name:
                filename = f"{test_name}_{step_name}_{timestamp}.png"
            else:
                filename = f"{test_name}_{timestamp}.png"
            
            # 清理文件名中的特殊字符
            filename = "".join(c if c.isalnum() or c in ('_', '-', '.') else '_' for c in filename)
            
            screenshot_path = os.path.join(self.report_dir, "screenshots", filename)
            
            # 保存截图
            driver.save_screenshot(screenshot_path)
            
            print(f"截图已保存: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            print(f"保存截图失败: {e}")
            return None
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        生成测试统计信息
        :return: 统计信息字典
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "passed")
        failed_tests = sum(1 for result in self.test_results if result["status"] == "failed")
        skipped_tests = sum(1 for result in self.test_results if result["status"] == "skipped")
        error_tests = sum(1 for result in self.test_results if result["status"] == "error")
        
        # 计算总耗时
        total_duration = sum(result["duration"] for result in self.test_results)
        
        # 计算通过率
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        statistics = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "error_tests": error_tests,
            "pass_rate": round(pass_rate, 2),
            "total_duration": round(total_duration, 2),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
        
        return statistics
    
    def generate_html_report(self, report_filename: str = None) -> str:
        """
        生成HTML格式的测试报告
        :param report_filename: 报告文件名
        :return: 报告文件路径
        """
        if report_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"test_report_{timestamp}.html"
        
        report_path = os.path.join(self.report_dir, report_filename)
        
        # 生成统计信息
        statistics = self.generate_statistics()
        
        # 生成HTML内容
        html_content = self._generate_html_template(statistics)
        
        # 保存HTML文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"测试报告已生成: {report_path}")
        return report_path
    
    def _generate_html_template(self, statistics: Dict[str, Any]) -> str:
        """
        生成HTML模板
        :param statistics: 统计信息
        :return: HTML内容
        """
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .statistics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card h3 {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-card.total .value {{ color: #3498db; }}
        .stat-card.passed .value {{ color: #27ae60; }}
        .stat-card.failed .value {{ color: #e74c3c; }}
        .stat-card.skipped .value {{ color: #f39c12; }}
        .stat-card.error .value {{ color: #e67e22; }}
        .stat-card.rate .value {{ color: #9b59b6; }}
        .stat-card.duration .value {{ color: #1abc9c; }}
        
        .progress-bar {{
            width: 100%;
            height: 8px;
            background-color: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 15px;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        
        .progress-fill.passed {{ background-color: #27ae60; }}
        .progress-fill.failed {{ background-color: #e74c3c; }}
        .progress-fill.skipped {{ background-color: #f39c12; }}
        
        .test-results {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 30px;
        }}
        
        .test-results-header {{
            background-color: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .test-results-header h2 {{
            color: #333;
            font-size: 1.5em;
        }}
        
        .test-item {{
            border-bottom: 1px solid #e9ecef;
            padding: 20px;
            transition: background-color 0.3s ease;
        }}
        
        .test-item:hover {{
            background-color: #f8f9fa;
        }}
        
        .test-item:last-child {{
            border-bottom: none;
        }}
        
        .test-item-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .test-name {{
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
        }}
        
        .test-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .test-status.passed {{
            background-color: #d4edda;
            color: #155724;
        }}
        
        .test-status.failed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        
        .test-status.skipped {{
            background-color: #fff3cd;
            color: #856404;
        }}
        
        .test-status.error {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        
        .test-meta {{
            display: flex;
            gap: 20px;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }}
        
        .test-meta span {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .test-error {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .test-steps {{
            margin-top: 15px;
            padding-left: 20px;
        }}
        
        .test-step {{
            padding: 10px;
            margin-bottom: 5px;
            background-color: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #ddd;
        }}
        
        .test-step.passed {{
            border-left-color: #27ae60;
        }}
        
        .test-step.failed {{
            border-left-color: #e74c3c;
        }}
        
        .test-step.skipped {{
            border-left-color: #f39c12;
        }}
        
        .screenshot {{
            margin-top: 15px;
            max-width: 100%;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .screenshot img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        
        .no-tests {{
            text-align: center;
            padding: 50px;
            color: #666;
        }}
        
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .chart {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 30px;
            flex-wrap: wrap;
        }}
        
        .pie-chart {{
            width: 200px;
            height: 200px;
            border-radius: 50%;
            position: relative;
        }}
        
        .chart-legend {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
        }}
        
        @media (max-width: 768px) {{
            .statistics {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .test-item-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{self.report_title}</h1>
        <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="container">
        <div class="statistics">
            <div class="stat-card total">
                <h3>总测试数</h3>
                <div class="value">{statistics['total_tests']}</div>
            </div>
            <div class="stat-card passed">
                <h3>通过</h3>
                <div class="value">{statistics['passed_tests']}</div>
            </div>
            <div class="stat-card failed">
                <h3>失败</h3>
                <div class="value">{statistics['failed_tests']}</div>
            </div>
            <div class="stat-card skipped">
                <h3>跳过</h3>
                <div class="value">{statistics['skipped_tests']}</div>
            </div>
            <div class="stat-card error">
                <h3>错误</h3>
                <div class="value">{statistics['error_tests']}</div>
            </div>
            <div class="stat-card rate">
                <h3>通过率</h3>
                <div class="value">{statistics['pass_rate']}%</div>
                <div class="progress-bar">
                    <div class="progress-fill passed" style="width: {statistics['pass_rate']}%"></div>
                </div>
            </div>
            <div class="stat-card duration">
                <h3>总耗时</h3>
                <div class="value">{statistics['total_duration']}s</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 style="text-align: center; margin-bottom: 20px;">测试结果分布</h2>
            <div class="chart">
                <div class="pie-chart" style="background: conic-gradient(
                    #27ae60 0deg {statistics['passed_tests'] / max(statistics['total_tests'], 1) * 360}deg,
                    #e74c3c {statistics['passed_tests'] / max(statistics['total_tests'], 1) * 360}deg {(statistics['passed_tests'] + statistics['failed_tests']) / max(statistics['total_tests'], 1) * 360}deg,
                    #f39c12 {(statistics['passed_tests'] + statistics['failed_tests']) / max(statistics['total_tests'], 1) * 360}deg {(statistics['passed_tests'] + statistics['failed_tests'] + statistics['skipped_tests']) / max(statistics['total_tests'], 1) * 360}deg,
                    #e67e22 {(statistics['passed_tests'] + statistics['failed_tests'] + statistics['skipped_tests']) / max(statistics['total_tests'], 1) * 360}deg 360deg
                )"></div>
                <div class="chart-legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #27ae60;"></div>
                        <span>通过 ({statistics['passed_tests']})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #e74c3c;"></div>
                        <span>失败 ({statistics['failed_tests']})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #f39c12;"></div>
                        <span>跳过 ({statistics['skipped_tests']})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #e67e22;"></div>
                        <span>错误 ({statistics['error_tests']})</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="test-results">
            <div class="test-results-header">
                <h2>测试详情</h2>
            </div>
            {self._generate_test_results_html()}
        </div>
    </div>
    
    <div class="footer">
        <p>© 2024 Osaio UI 测试报告 | 自动化测试框架</p>
    </div>
</body>
</html>
        """
        
        return html
    
    def _generate_test_results_html(self) -> str:
        """
        生成测试结果HTML
        :return: 测试结果HTML内容
        """
        if not self.test_results:
            return '<div class="no-tests"><p>暂无测试结果</p></div>'
        
        html_parts = []
        
        for result in self.test_results:
            # 状态样式
            status_class = result['status'].lower()
            
            # 测试项HTML
            test_html = f"""
            <div class="test-item">
                <div class="test-item-header">
                    <div class="test-name">{result['test_name']}</div>
                    <div class="test-status {status_class}">{result['status']}</div>
                </div>
                <div class="test-meta">
                    <span>⏱️ 耗时: {result['duration']:.2f}s</span>
                    <span>🕐 时间: {result['timestamp']}</span>
                </div>
            """
            
            # 添加错误消息
            if result['error_message']:
                test_html += f"""
                <div class="test-error">{result['error_message']}</div>
                """
            
            # 添加测试步骤
            if result['steps']:
                test_html += '<div class="test-steps">'
                for step in result['steps']:
                    step_class = step['status'].lower()
                    test_html += f"""
                    <div class="test-step {step_class}">
                        <strong>{step['step_name']}</strong>
                        <span style="margin-left: 10px; color: #666;">{step['status']}</span>
                        {f'<span style="margin-left: 10px; color: #999;">{step["duration"]:.2f}s</span>' if step['duration'] > 0 else ''}
                        {f'<div style="margin-top: 5px; color: #666;">{step["message"]}</div>' if step.get('message') else ''}
                    </div>
                    """
                test_html += '</div>'
            
            # 添加截图
            if result['screenshot_path'] and os.path.exists(result['screenshot_path']):
                # 使用相对路径（统一用正斜杠，保证 HTML 在任意平台/浏览器都能加载）
                relative_path = os.path.relpath(result['screenshot_path'], self.report_dir).replace(os.sep, "/")
                test_html += f"""
                <div class="screenshot">
                    <img src="{relative_path}" alt="Test Screenshot" />
                </div>
                """
            
            test_html += '</div>'
            html_parts.append(test_html)
        
        return '\n'.join(html_parts)
    
    def generate_json_report(self, report_filename: str = None) -> str:
        """
        生成JSON格式的测试报告
        :param report_filename: 报告文件名
        :return: 报告文件路径
        """
        if report_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"test_report_{timestamp}.json"
        
        report_path = os.path.join(self.report_dir, report_filename)
        
        # 准备报告数据
        report_data = {
            "title": self.report_title,
            "generated_at": datetime.now().isoformat(),
            "statistics": self.generate_statistics(),
            "test_results": self.test_results
        }
        
        # 保存JSON文件
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON报告已生成: {report_path}")
        return report_path


class TestReportHook:
    """测试报告钩子 - 与pytest集成"""
    
    def __init__(self, report_generator: TestReportGenerator):
        self.report_generator = report_generator
        self.current_test = None
        self.current_steps = []
    
    def start_test(self, test_name: str):
        """开始测试"""
        self.current_test = test_name
        self.current_steps = []
    
    def end_test(self, status: str, duration: float = 0, error_message: str = None, screenshot_path: str = None):
        """结束测试"""
        if self.current_test:
            self.report_generator.add_test_result(
                test_name=self.current_test,
                status=status,
                duration=duration,
                error_message=error_message,
                screenshot_path=screenshot_path,
                steps=self.current_steps
            )
        
        self.current_test = None
        self.current_steps = []
    
    def add_step(self, step_name: str, status: str, duration: float = 0, message: str = None, screenshot: str = None):
        """添加测试步骤"""
        step = self.report_generator.add_test_step(
            step_name=step_name,
            status=status,
            duration=duration,
            message=message,
            screenshot=screenshot
        )
        self.current_steps.append(step)


# 使用示例
if __name__ == "__main__":
    # 创建报告生成器
    report = TestReportGenerator(report_title="Osaio UI 测试报告")
    
    # 开始报告
    report.start_report()
    
    # 添加测试结果示例
    report.add_test_result(
        test_name="test_login_success",
        status="passed",
        duration=3.5,
        steps=[
            report.add_test_step("打开登录页面", "passed", 1.0),
            report.add_test_step("输入账号密码", "passed", 1.5),
            report.add_test_step("点击登录按钮", "passed", 0.5),
            report.add_test_step("验证首页显示", "passed", 0.5)
        ]
    )
    
    report.add_test_result(
        test_name="test_login_failed",
        status="failed",
        duration=2.0,
        error_message="AssertionError: Expected home page but still on login page",
        steps=[
            report.add_test_step("打开登录页面", "passed", 1.0),
            report.add_test_step("输入错误密码", "passed", 0.5),
            report.add_test_step("点击登录按钮", "passed", 0.5),
            report.add_test_step("验证错误提示", "failed", 0.0, message="未找到错误提示元素")
        ]
    )
    
    report.add_test_result(
        test_name="test_register",
        status="skipped",
        duration=0.1,
        error_message="需要真实验证码才能测试"
    )
    
    # 结束报告
    report.end_report()
    
    # 生成HTML报告
    html_path = report.generate_html_report()
    print(f"\nHTML报告: {html_path}")
    
    # 生成JSON报告
    json_path = report.generate_json_report()
    print(f"JSON报告: {json_path}")
    
    print("\n测试报告生成完成！")