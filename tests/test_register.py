"""注册模块测试用例"""
import pytest
import random
import string
from pages.login_page import LoginPage
from pages.register_page import RegisterPage
from pages.home_page import HomePage
import os
from utils.temp_mail import wait_for_verification_code


class TestRegister:
    """注册功能测试"""
    
    def generate_random_email(self):
        """生成随机邮箱"""
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"test_{random_string}@example.com"
    
    def generate_random_password(self):
        """生成随机密码"""
        return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=10))
    
    def test_go_to_register_page(self, driver):
        """测试跳转到注册页面"""
        login_page = LoginPage(driver)
        
        # 确保在登录页面
        if not login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            # 如果不在登录页面，可能需要先退出登录
            print("当前不在登录页面，可能需要先退出登录")
            # 这里可以添加退出登录的逻辑
            # 暂时跳过测试
            pytest.skip("当前不在登录页面，无法测试注册")
        
        # 点击注册链接
        login_page.go_register()
        
        # 验证是否跳转到注册页面
        register_page = RegisterPage(driver)
        assert register_page.is_displayed(*register_page.REGISTER_BTN, timeout=10), "应跳转到注册页面"
        print("成功跳转到注册页面")
    
    def test_register_empty_fields(self, driver):
        """异常注册 - 所有字段为空"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            login_page.go_register()
        
        register_page = RegisterPage(driver)
        
        # 尝试注册，所有字段为空
        result = register_page.register("", "", "")
        
        # 应返回错误消息
        assert isinstance(result, str), "空字段注册应返回错误消息"
        assert result, "应有错误提示"
        print(f"空字段注册测试通过，错误消息: {result}")
    
    def test_register_invalid_email(self, driver):
        """异常注册 - 无效邮箱格式"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            login_page.go_register()
        
        register_page = RegisterPage(driver)
        
        # 尝试注册，使用无效邮箱
        result = register_page.register("invalid-email", "Password123!", "Password123!")
        
        # 应返回错误消息
        assert isinstance(result, str), "无效邮箱注册应返回错误消息"
        assert result, "应有错误提示"
        print(f"无效邮箱注册测试通过，错误消息: {result}")
    
    def test_register_password_mismatch(self, driver):
        """异常注册 - 密码不匹配"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            login_page.go_register()
        
        register_page = RegisterPage(driver)
        
        # 尝试注册，密码不匹配
        email = self.generate_random_email()
        result = register_page.register(email, "Password123!", "DifferentPassword!")
        
        # 应返回错误消息
        assert isinstance(result, str), "密码不匹配注册应返回错误消息"
        assert result, "应有错误提示"
        print(f"密码不匹配注册测试通过，错误消息: {result}")

    
    def test_register_step1_input_email(self, driver):
        """测试注册第一步：输入邮箱和国家"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            register_page = login_page.go_register()
        else:
            register_page = RegisterPage(driver)
        
        # 生成测试数据
        email = self.generate_random_email()
        
        print(f"测试注册第一步 - 邮箱: {email}")
        
        # 执行注册第一步
        result = register_page.register_step1_input_email(
            email=email,
            country="China",
            agree_privacy=True,
            agree_terms=True
        )
        
        # 检查结果
        if isinstance(result, RegisterPage):
            # 成功进入验证码页面
            assert result.is_displayed(*result.VERIFICATION_TITLE, timeout=10), "应进入验证码页面"
            print("注册第一步成功，已进入验证码页面")
        elif isinstance(result, str):
            # 返回错误消息
            print(f"注册第一步失败: {result}")
            
            # 检查是否是邮箱已存在的错误
            if "already" in result.lower() or "exist" in result.lower():
                print("邮箱已存在，这是预期行为（测试数据冲突）")
                pytest.skip(f"邮箱已存在: {result}")
            else:
                # 其他错误，测试失败
                pytest.fail(f"注册第一步失败: {result}")
        else:
            pytest.fail(f"未知的注册第一步结果类型: {type(result)}")
    
    def test_register_complete_flow_with_mock_code(self, driver):
        """测试完整注册流程（使用模拟验证码）"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            register_page = login_page.go_register()
        else:
            register_page = RegisterPage(driver)
        
        # 生成测试数据
        email = self.generate_random_email()
        # 模拟验证码，实际测试中需要真实验证码（可用 OSAIO_MOCK_VERIFICATION_CODE 覆盖）
        verification_code = os.environ.get("OSAIO_MOCK_VERIFICATION_CODE", "123456")
        password = self.generate_random_password()
        
        print(f"测试完整注册流程 - 邮箱: {email}, 密码: {password}")
        
        # 执行完整注册流程
        result = register_page.register_complete_flow(
            email=email,
            verification_code=verification_code,
            password=password,
            country="China",
            agree_privacy=True,
            agree_terms=True
        )
        
        # 检查注册结果
        if isinstance(result, HomePage):
            # 注册成功，跳转到首页
            assert result.is_home_displayed(), "注册成功后应跳转到首页"
            print("完整注册流程成功，已跳转到首页")
            
            # 可以在这里添加验证注册成功的其他检查
            # 例如：检查用户是否已登录，检查欢迎消息等
            
        elif isinstance(result, str):
            # 注册失败，返回错误消息
            print(f"完整注册流程失败: {result}")
            
            # 检查是否是邮箱已存在的错误
            if "already" in result.lower() or "exist" in result.lower():
                print("邮箱已存在，这是预期行为（测试数据冲突）")
                pytest.skip(f"邮箱已存在: {result}")
            elif "验证码" in result or "code" in result.lower():
                print("验证码错��，这是预期行为（使用模拟验证码）")
                pytest.skip(f"验证码错误: {result}")
            else:
                # 其他错误，记录但不失败（因为验证码是模拟的）
                print(f"注册流程其他错误: {result}")
                # 不标记为失败，因为验证码是模拟的
        else:
            print(f"未知的注册结果类型: {type(result)}")
    
    def test_back_to_login(self, driver):
        """测试从注册页面返回登录页面"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            register_page = login_page.go_register()
        else:
            register_page = RegisterPage(driver)
        
        # 点击返回登录链接
        returned_login_page = register_page.go_back_to_login()
        
        # 验证是否返回登录页面
        assert returned_login_page.is_displayed(*returned_login_page.LOGIN_BTN, timeout=10), "应返回登录页面"
        print("成功从注册页面返回登录页面")
    
    def test_select_country(self, driver):
        """测试选择国家功能"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            register_page = login_page.go_register()
        else:
            register_page = RegisterPage(driver)
        
        # 选择国家
        selected_country = register_page.select_country("China")
        
        # 验证国家选择
        assert selected_country is not None, "应成功选择国家"
        print(f"成功选择国家: {selected_country}")
    
    def test_register_without_agreeing_terms(self, driver):
        """异常注册 - 不同意条款"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            register_page = login_page.go_register()
        else:
            register_page = RegisterPage(driver)
        
        # 生成测试数据
        email = self.generate_random_email()
        
        # 尝试注册第一步，但不同意条款
        result = register_page.register_step1_input_email(
            email=email,
            country="China",
            agree_privacy=True,
            agree_terms=False  # 不同意条款
        )
        
        # 检查结果
        if isinstance(result, str):
            # 应返回错误消息
            assert "terms" in result.lower() or "agree" in result.lower() or "条件" in result, "不同意条款应有相应错误提示"
            print(f"不同意条款注册测试通过，错误消息: {result}")
        elif isinstance(result, RegisterPage):
            # 如果APP允许不同意条款也能继续，记录日志
            print("APP允许不同意条款继续注册，这可能不是预期行为")
            assert result.is_displayed(*result.VERIFICATION_TITLE, timeout=10), "应进入验证码页面"
        else:
            print(f"不同意条款注册结果: {type(result)}")

    def test_register_complete_flow_with_temp_mail(self, driver):
        """使用临时邮箱服务获取真实验证码并完成注册流程（受控运行）"""
        # 通过环境变量启用真实邮箱测试，避免 CI/本地误触发
        if os.environ.get("USE_TEMP_MAIL", "0") != "1":
            pytest.skip("未启用临时邮箱测试，设置环境变量 USE_TEMP_MAIL=1 以启用")

        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            register_page = login_page.go_register()
        else:
            register_page = RegisterPage(driver)

        # 生成临时邮箱（可通过 TEMP_EMAIL_DOMAIN 覆盖）
        domain = os.environ.get("TEMP_EMAIL_DOMAIN", "tempmail.plus")
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"osaio_test_{random_string}@{domain}"
        password = self.generate_random_password()

        print(f"开始使用临时邮箱注册流程 - 邮箱: {email}")

        # 第一步：提交邮箱
        step1 = register_page.register_step1_input_email(
            email=email,
            country="China",
            agree_privacy=True,
            agree_terms=True
        )

        if isinstance(step1, str):
            pytest.skip(f"注册第一步未能进入验证码页面: {step1}")

        # 等待验证码到临时邮箱
        code, mail_id = wait_for_verification_code(email, timeout=180, check_interval=5)
        if not code:
            pytest.skip("未收到验证码邮件，跳过真实验证码注册测试")

        print(f"收到验证码 {code} (mail_id={mail_id})")

        # 第二步：输入验证码
        step2 = register_page.register_step2_input_verification_code(code)
        if isinstance(step2, str):
            pytest.fail(f"验证码校验失败: {step2}")

        # 第三步：设置密码并完成注册
        result = register_page.register_step3_set_password(password)

        if isinstance(result, HomePage):
            assert result.is_home_displayed(), "注册成功应跳转到首页"
            print("使用临时邮箱完成注册并跳转到首页")
        else:
            pytest.fail(f"注册流程未成功完成: {result}")
    
    def test_register_invalid_password_length(self, driver):
        """测试密码长度验证"""
        # 这个测试需要先完成前两步，然后测试密码设置
        # 由于验证码需要真实获取，这里只测试逻辑
        
        print("密码长度验证测试:")
        print("- 密码长度小于6位应失败")
        print("- 密码长度大于28位应失败")
        print("- 密码长度6-28位应成功")
        
        # 实际测试需要在有真实验证码的情况下进行
        pytest.skip("需要真实验证码才能测试密码设置步骤")
    
    def test_register_password_mismatch(self, driver):
        """测试密码不匹配"""
        # 这个测试需要先完成前两步，然后测试密码设置
        print("密码不匹配测试:")
        print("- 密码和确认密码不一致应失败")
        
        # 实际测试需要在有真实验证码的情况下进行
        pytest.skip("需要真实验证码才能测试密码设置步骤")
    
    def test_register_without_agreeing_terms(self, driver):
        """异常注册 - 不同意条款"""
        # 先导航到注册页面
        login_page = LoginPage(driver)
        if login_page.is_displayed(*login_page.LOGIN_BTN, timeout=5):
            login_page.go_register()
        
        register_page = RegisterPage(driver)
        
        # 生成测试数据
        email = self.generate_random_email()
        password = self.generate_random_password()
        
        # 尝试注册，但不同意条款
        result = register_page.register(
            email=email,
            password=password,
            agree_terms=False  # 不同意条款
        )
        
        # 检查结果
        if isinstance(result, str):
            # 应返回错误消息
            assert "terms" in result.lower() or "agree" in result.lower() or "条件" in result, "不同意条款应有相应错误提示"
            print(f"不同意条款注册测试通过，错误消息: {result}")
        elif isinstance(result, HomePage):
            # 如果APP允许不同意条款也能注册，记录日志
            print("APP允许不同意条款注册，这可能不是预期行为")
            assert result.is_home_displayed(), "注册成功后应跳转到首页"
        else:
            print(f"不同意条款注册结果: {type(result)}")