# Osaio App UI 自动化测试

## 环境准备

```bash
# 1. 安装 Appium
npm install -g appium
appium driver install uiautomator2   # Android
appium driver install xcuitest        # iOS

# 2. 安装 Python 依赖
cd osaio-ui-test
pip install -r requirements.txt

# 3. 启动 Appium Server
appium
```

## 运行测试

```bash
# 运行全部测试 (默认 Android)
pytest

# 指定 iOS 平台
pytest --platform=ios

# 运行指定模块
pytest tests/test_login.py

# 生成 HTML 报告
pytest --html=reports/report.html
```

## 项目结构

```
osaio-ui-test/
├── config/caps.yaml        # 设备能力配置
├── pages/                  # Page Object 页面对象
│   ├── base_page.py        # 页面基类
│   ├── login_page.py       # 登录页
│   ├── home_page.py        # 首页
│   └── device_page.py      # 设备页
├── tests/                  # 测试用例
│   ├── test_login.py       # 登录测试
│   └── test_home.py        # 首页测试
├── utils/                  # 工具类
│   └── driver_helper.py    # Driver 管理
├── conftest.py             # pytest 全局配置
└── pytest.ini              # pytest 运行配置
```

## 注意事项

1. 运行前需用 Appium Inspector 确认元素的实际定位信息
2. 修改 `config/caps.yaml` 中的包名和 Activity 为实际值
3. 测试账号密码请替换为实际测试数据
