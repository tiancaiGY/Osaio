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
    
    # ------------------------------------------------------------------ 样式化 HTML
    # 报告样式对齐 report/test_report.html（Apple 风格）：测试环境 + 编号步骤表(#/步骤/状态/说明)
    # + 4 项总结卡（总测试数/通过/失败/通过率）。用例的“步骤”是报告主体（smoke 为分步骤用例）。

    STATUS_LABEL = {"passed": "通过", "failed": "失败", "skipped": "跳过", "error": "错误"}

    @staticmethod
    def _esc(text) -> str:
        """HTML 转义，防止说明/错误文本里的 <>& 破坏结构。"""
        s = "" if text is None else str(text)
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))

    def _screenshot_cell(self, path) -> str:
        """把截图路径渲染成结果表“截图”单元格内容：缩略图链接（点击看原图）；无图返回占位。

        路径统一转成相对 report_dir 的正斜杠形式，保证 HTML 在任意平台/浏览器都能加载。
        """
        if not path or not os.path.exists(path):
            return '<span class="noshot">—</span>'
        rel = os.path.relpath(path, self.report_dir).replace(os.sep, "/")
        rel_esc = self._esc(rel)
        return (f'<a href="{rel_esc}" target="_blank">'
                f'<img src="{rel_esc}" alt="现场截图" /></a>')

    def collect_environment(self) -> Dict[str, str]:
        """收集测试环境信息（尽力而为，任何缺失都用占位符，绝不抛出）。

        操作系统展示的是**手机**系统及版本（非跑测试的桌面），并附目标 App 版本号——
        二者优先用外部注入值（set_environment，来自 driver caps），否则用 adb 兜底读取。
        """
        import platform
        env: Dict[str, str] = {}
        env["报告标题"] = self.report_title
        env["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        env["Python"] = platform.python_version()
        # 依赖版本（存在才显示；优先包元数据，回退模块 __version__）
        try:
            from importlib.metadata import version as _pkg_version
        except Exception:
            _pkg_version = None
        for dist, mod, label in (
            ("Appium-Python-Client", "appium", "Appium-Python-Client"),
            ("selenium", "selenium", "Selenium"),
            ("pytest", "pytest", "pytest"),
        ):
            ver = None
            if _pkg_version is not None:
                try:
                    ver = _pkg_version(dist)
                except Exception:
                    ver = None
            if ver is None:
                try:
                    ver = getattr(__import__(mod), "__version__", None)
                except Exception:
                    ver = None
            if ver:
                env[label] = ver
        # 设备/账号等运行期信息由外部通过 set_environment 注入（可选，优先级最高）
        extra = getattr(self, "_extra_env", {}) or {}
        env.update(extra)
        # 手机系统/机型/App 版本：外部未注入则用 adb 兜底读取
        try:
            from utils import adb_helper
            serial = adb_helper.resolve_serial()
            if serial:
                env.setdefault("设备", serial)
                dinfo = adb_helper.device_info(serial)
                if "系统" not in env and dinfo.get("系统"):
                    env["系统(手机)"] = dinfo["系统"]
                if "型号" not in env and dinfo.get("型号"):
                    env["型号"] = dinfo["型号"]
                if "App版本" not in env:
                    ver = adb_helper.app_version(serial)
                    if ver:
                        env["App版本(OSAIO)"] = ver
        except Exception:
            pass
        # 设备兜底（若 adb 也没拿到，用 caps.yaml 的 deviceName）
        if "设备" not in env:
            try:
                from utils.driver_helper import load_config
                dev = (load_config().get("android", {}) or {}).get("deviceName")
                if dev:
                    env["设备"] = dev
            except Exception:
                pass
        return env

    def set_environment(self, **info):
        """外部注入运行期环境信息（如 设备、账号、注册国家），会并入 collect_environment。"""
        self._extra_env = {**getattr(self, "_extra_env", {}), **{k: str(v) for k, v in info.items()}}

    def _all_steps(self) -> List[Dict[str, Any]]:
        """把所有用例的步骤按顺序摊平为报告主表的行；无步骤的用例回退为“用例级一行”。"""
        rows: List[Dict[str, Any]] = []
        for result in self.test_results:
            steps = result.get("steps") or []
            if steps:
                for s in steps:
                    rows.append({
                        "name": s.get("step_name") or "(未命名步骤)",
                        "status": (s.get("status") or "").lower(),
                        "message": s.get("message") or "",
                        "screenshot": s.get("screenshot"),
                    })
            else:
                # 无分步骤的用例：整条用例作为一行，错误信息作说明
                rows.append({
                    "name": result.get("test_name") or "(用例)",
                    "status": (result.get("status") or "").lower(),
                    "message": result.get("error_message") or "",
                    "screenshot": result.get("screenshot_path"),
                })
        return rows

    def _generate_html_template(self, statistics: Dict[str, Any]) -> str:
        """生成 Apple 风格 HTML 报告（对齐 report/test_report.html 样式）。"""
        rows = self._all_steps()
        total = len(rows)
        passed = sum(1 for r in rows if r["status"] == "passed")
        failed = sum(1 for r in rows if r["status"] in ("failed", "error"))
        skipped = sum(1 for r in rows if r["status"] == "skipped")
        pass_rate = round(passed / total * 100) if total else 0
        # 通过率颜色：全过绿色，否则红色（与样式表 .pct 语义一致）
        pct_color = "#30d158" if failed == 0 and total > 0 else "#ff453a"

        # 测试环境表
        env = self.collect_environment()
        env_rows = "\n".join(
            f"<tr><td>{self._esc(k)}</td><td>{self._esc(v)}</td></tr>" for k, v in env.items()
        )

        # 结果步骤表
        tag_class = {"passed": "tag-pass", "failed": "tag-fail", "error": "tag-fail",
                     "skipped": "tag-skip"}
        result_rows = []
        for i, r in enumerate(rows, 1):
            st = r["status"]
            cls = tag_class.get(st, "tag-skip")
            label = self.STATUS_LABEL.get(st, st or "?")
            # 说明只取首行：失败/跳过的原始 message 常带多行 assert 堆栈，表格里只需第一句
            msg = (r["message"] or "").strip()
            msg_first = msg.splitlines()[0] if msg else ""
            # 截图列：跳过/失败步骤附 App 现场截图缩略图（点击看原图）；无图留空
            shot_cell = self._screenshot_cell(r.get("screenshot"))
            result_rows.append(
                f'<tr><td>{i}</td><td>{self._esc(r["name"])}</td>'
                f'<td><span class="tag {cls}">{label}</span></td>'
                f'<td>{self._esc(msg_first)}</td>'
                f'<td class="shot">{shot_cell}</td></tr>'
            )
        result_rows_html = "\n".join(result_rows) or \
            '<tr><td colspan="5" style="text-align:center;color:#86868b;">暂无测试步骤</td></tr>'

        # 结论文字
        if total == 0:
            conclusion = "未采集到测试步骤"
        elif failed == 0:
            conclusion = "全部步骤执行通过"
        else:
            conclusion = f"{failed} 个步骤失败，需排查"

        duration = statistics.get("total_duration", 0)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._esc(self.report_title)}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f5f5f7; color: #1d1d1f; }}
h1 {{ text-align: center; color: #1d1d1f; margin-bottom: 6px; }}
.subtitle {{ text-align:center; color:#86868b; margin-bottom: 24px; font-size: 14px; }}
h2 {{ color: #1d1d1f; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; margin-top: 36px; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin: 16px 0; }}
th, td {{ padding: 12px 16px; text-align: left; vertical-align: top; }}
th {{ background: #1d1d1f; color: #fff; font-weight: 600; }}
tr:nth-child(even) {{ background: #f9f9f9; }}
.summary-box {{ display: flex; gap: 20px; justify-content: center; margin: 24px 0; flex-wrap: wrap; }}
.summary-item {{ background: #fff; border-radius: 12px; padding: 20px 32px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.08); flex: 1; min-width: 120px; }}
.summary-item .num {{ font-size: 36px; font-weight: 700; }}
.summary-item .label {{ font-size: 14px; color: #86868b; margin-top: 4px; }}
.pass {{ color: #30d158; }}
.fail {{ color: #ff453a; }}
.skip {{ color: #ff9f0a; }}
.tag {{ display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 13px; font-weight: 600; }}
.tag-pass {{ background: #d1fae5; color: #065f46; }}
.tag-fail {{ background: #fee2e2; color: #991b1b; }}
.tag-skip {{ background: #fef3c7; color: #92400e; }}
.pct {{ font-size: 48px; font-weight: 700; }}
td.shot {{ text-align: center; }}
td.shot img {{ max-height: 90px; max-width: 140px; border-radius: 6px; border: 1px solid #e0e0e0; }}
td.shot .noshot {{ color: #c7c7cc; }}
</style>
</head>
<body>

<h1>{self._esc(self.report_title)}</h1>
<div class="subtitle">生成时间 {env.get('生成时间', '')} · 总耗时 {duration}s</div>

<h2>测试环境</h2>
<table>
<tr><th>项目</th><th>信息</th></tr>
{env_rows}
</table>

<h2>测试结果</h2>
<table>
<thead>
<tr><th>#</th><th>步骤</th><th>状态</th><th>说明</th><th>截图</th></tr>
</thead>
<tbody>
{result_rows_html}
</tbody>
</table>

<h2>总结</h2>
<div class="summary-box">
<div class="summary-item"><div class="num">{total}</div><div class="label">总步骤数</div></div>
<div class="summary-item"><div class="num pass">{passed}</div><div class="label">通过</div></div>
<div class="summary-item"><div class="num fail">{failed}</div><div class="label">失败</div></div>
<div class="summary-item"><div class="num skip">{skipped}</div><div class="label">跳过</div></div>
<div class="summary-item"><div class="pct" style="color:{pct_color};">{pass_rate}%</div><div class="label">通过率</div></div>
</div>

<p style="text-align:center;color:#86868b;margin-top:32px;">{self._esc(conclusion)}</p>

</body>
</html>"""
    
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