# UI 自动化高复用框架方案

## 1. 目标

本方案面向当前 `osaio-ui-test` 项目，目标不是推倒重来，而是在现有 `pytest + Appium + Page Object` 基础上，逐步演进出一套：

- 稳定性更高
- 业务流程可复用
- 数据与环境可切换
- 用例维护成本更低
- 报告与排障更清晰

的 App UI 自动化框架。


## 2. 当前项目现状

当前仓库已经具备基础自动化能力：

- `conftest.py` 负责 driver 生命周期
- `pages/` 已有页面对象雏形
- `utils/driver_helper.py` 已封装 Appium driver 创建
- `config/caps.yaml` 已管理基础能力配置
- `conftest_report.py` 和 `utils/report_generator.py` 已开始做报告能力

这说明框架已经有基础，但从“可跑”到“高复用、可维护”之间，还差关键的一层：业务流程层和统一公共能力层。


## 3. 当前主要问题

结合现有代码，复用率不高的根因主要有这些。

### 3.1 页面对象承担了太多职责

例如 [pages/login_page.py](C:\Users\Administrator\Desktop\New folder\osaio-ui-test\pages\login_page.py) 里同时包含：

- 元素定位
- 页面输入与点击
- 登录成功/失败判断
- 已登录态识别
- 页面恢复
- 引导页跳过
- 部分业务兜底逻辑

问题在于：页面类既像 Page Object，又像业务流程类，还兼做异常恢复器，后续会越来越难复用。

### 3.2 业务流程没有独立抽层

当前“登录”“智能登录”“退出登录”“跳过引导”“关闭权限弹窗”这些能力分散在不同页面里，导致：

- 相同流程在不同测试里重复调用页面细节
- 测试用例依赖页面实现，而不是依赖稳定业务动作
- 页面改动会牵连大量测试

### 3.3 通用弹窗与恢复机制没有统一入口

例如：

- 登录页有 `skip_onboarding`
- 首页有 `dismiss_permission_dialogs`
- 账户页有 `dismiss_system_dialogs`

这些都属于跨页面公共能力，不应该散在页面类里。

### 3.4 数据与断言耦合在测试里

例如 [tests/test_login.py](C:\Users\Administrator\Desktop\New folder\osaio-ui-test\tests\test_login.py) 中直接写死：

- 测试账号
- 密码
- 期望行为

这会导致：

- 场景扩展困难
- 账号切换成本高
- 测试环境切换不方便

### 3.5 测试层仍然依赖页面细节

理想状态下，用例应该更像：

- “以有效账号登录”
- “登录失败时应提示错误”
- “已登录用户再次进入应保持首页态”

而不是频繁关心输入框、按钮、恢复逻辑这些实现细节。


## 4. 目标分层设计

建议把框架稳定为 5 层。

### 4.1 基础层 `core/`

负责最底层能力，不包含业务语义。

- driver 创建与销毁
- 显式等待
- 元素查找
- 点击/输入/滑动
- 截图
- 日志
- 重试
- 统一异常

这一层的目标是“稳定操作 UI”。

### 4.2 页面层 `pages/`

只负责页面结构与页面行为，不写跨页面业务流程。

例如登录页只保留：

- 输入账号
- 输入密码
- 点击登录
- 读取错误文案
- 判断登录页是否展示

不要在页面层里写：

- 智能登录
- 强制退出后重登
- 引导页跳过
- 全局弹窗恢复

### 4.3 业务流程层 `flows/`

这是复用率提升的核心层。

把多个页面动作组合成稳定业务动作，例如：

- `LoginFlow.login_with_password()`
- `LoginFlow.ensure_logged_in()`
- `LoginFlow.ensure_logged_out()`
- `OnboardingFlow.skip_if_present()`
- `PermissionFlow.dismiss_if_present()`
- `AccountFlow.logout()`

测试只依赖 flow，不直接依赖复杂页面实现。

### 4.4 数据层 `data/`

把测试账号、环境参数、输入数据、预期数据抽离出来。

例如：

- `data/accounts.yaml`
- `data/login_cases.yaml`
- `data/devices.yaml`

这样同一个流程可以服务多组测试。

### 4.5 用例层 `tests/`

用例层只做三件事：

- 调用 flow
- 校验结果
- 标记用例意图

不要在用例层处理复杂 UI 细节。


## 5. 推荐目录结构

建议在现有项目基础上逐步演进到下面结构：

```text
osaio-ui-test/
├─ config/
│  ├─ caps.yaml
│  ├─ env.yaml
│  └─ accounts.yaml
├─ core/
│  ├─ driver_factory.py
│  ├─ base_page.py
│  ├─ locator.py
│  ├─ waiter.py
│  ├─ exceptions.py
│  ├─ logger.py
│  └─ screenshot.py
├─ pages/
│  ├─ login_page.py
│  ├─ home_page.py
│  ├─ account_page.py
│  ├─ register_page.py
│  └─ device_page.py
├─ flows/
│  ├─ login_flow.py
│  ├─ account_flow.py
│  ├─ onboarding_flow.py
│  ├─ permission_flow.py
│  └─ app_flow.py
├─ data/
│  ├─ login_cases.yaml
│  ├─ register_cases.yaml
│  └─ test_users.yaml
├─ fixtures/
│  ├─ app_fixture.py
│  └─ data_fixture.py
├─ tests/
│  ├─ smoke/
│  ├─ regression/
│  └─ login/
├─ reports/
├─ utils/
└─ conftest.py
```

如果不想一次性改太多，也可以先只新增 `flows/` 和 `data/`，这是收益最高的第一步。


## 6. 各层职责边界

职责边界清晰，复用率才会高。

### 页面层应该做什么

- 提供元素定位
- 封装单页面动作
- 返回页面状态

示例：

- `LoginPage.enter_account(account)`
- `LoginPage.enter_password(password)`
- `LoginPage.tap_login()`
- `LoginPage.get_error_message()`

### 页面层不应该做什么

- 判断是否需要重登并自动恢复
- 负责全局权限弹窗处理
- 写完整登录业务
- 写跨页面跳转后的兜底流程

### 业务流程层应该做什么

- 编排多个页面动作
- 处理跨页面流程
- 处理公共恢复动作
- 统一日志与步骤记录

示例：

- `LoginFlow.ensure_login(account_type="valid_user")`
- `AppFlow.launch_and_prepare()`
- `AccountFlow.logout_if_needed()`


## 7. 建议优先沉淀的复用能力

这几类能力最值得先抽。

### 7.1 登录流程复用

把现有 `login`、`smart_login`、`is_already_logged_in`、部分恢复逻辑，从页面层迁到 `flows/login_flow.py`。

目标接口示例：

```python
home_page = login_flow.login_success("default_user")
error_text = login_flow.login_expect_error("", "123456")
login_flow.ensure_logged_out()
login_flow.ensure_logged_in("default_user")
```

### 7.2 全局弹窗处理

建立统一弹窗处理器，例如：

```python
permission_flow.dismiss_if_present()
system_dialog_flow.dismiss_common_dialogs()
```

不要在每个页面里各写一套 `dismiss_xxx`。

### 7.3 应用启动准备流程

把“启动 App -> 跳过引导 -> 关闭权限框 -> 进入可测态”做成统一入口。

例如：

```python
app_flow.launch_to_ready_state()
```

所有测试都从“可测态”开始，而不是每条用例自己恢复。

### 7.4 测试数据工厂

统一提供测试账号和场景数据，例如：

```python
user = account_data.get("valid_user")
invalid_user = account_data.get("wrong_password_user")
```

这样可以避免测试里写死邮箱和密码。

### 7.5 统一失败取证

你们已有报告能力，建议再统一挂接：

- 失败截图
- 当前页面 source
- 当前 activity 或页面标识
- 关键步骤日志

这样 flaky 问题更容易定位。


## 8. 推荐的编码模式

### 8.1 测试只调用 flow

推荐：

```python
def test_login_success(login_flow):
    home = login_flow.login_success("default_user")
    assert home.is_home_displayed()
```

不推荐：

```python
def test_login_success(driver):
    page = LoginPage(driver)
    page.smart_input_account("xxx")
    page.smart_input_password("xxx")
    page.click(...)
```

### 8.2 定位器统一管理

页面内定位器保持静态、集中、可读。

优先级建议：

1. `resource-id`
2. `accessibility id`
3. 稳定文本
4. 短 XPath
5. 坐标和长链 XPath

尽量减少这类高脆弱定位：

- `instance(16)`
- `instance(19)`
- 很长的绝对 XPath

这类定位短期能跑，长期维护成本会很高。

### 8.3 单一方法单一语义

例如：

- `enter_account()` 只输入账号
- `tap_login()` 只点击登录
- `login_success()` 才表示完整业务动作

这样页面层和流程层不会混乱。


## 9. 基于当前项目的落地改造建议

建议分 4 步走，不要一次性大改。

### 第一步：保留现有 pages，新增 flows

先不重写页面类，只新增：

- `flows/login_flow.py`
- `flows/account_flow.py`
- `flows/app_flow.py`
- `flows/permission_flow.py`

先把业务编排抽出来，马上就能提升复用率。

### 第二步：把恢复逻辑从 page 中迁出

优先迁出这些逻辑：

- `smart_login`
- `skip_onboarding`
- `dismiss_permission_dialogs`
- `dismiss_system_dialogs`
- “不在登录页时的恢复逻辑”

页面类只保留页面操作。

### 第三步：把测试数据配置化

新增：

- `config/accounts.yaml`
- `data/login_cases.yaml`

测试不再写死账号密码。

### 第四步：整理 fixture 与报告

让 fixture 直接产出 flow，而不是只产出 driver。

例如：

- `driver`
- `login_flow`
- `app_flow`
- `test_user`

这样测试代码会更干净。


## 10. 推荐的 fixture 设计

建议在 `conftest.py` 中逐渐提供更高层 fixture。

示例思路：

```python
@pytest.fixture
def login_flow(driver):
    return LoginFlow(driver)


@pytest.fixture
def app_flow(driver):
    return AppFlow(driver)
```

然后测试里直接使用：

```python
def test_user_can_login(app_flow, login_flow):
    app_flow.launch_to_ready_state()
    home = login_flow.login_success("default_user")
    assert home.is_home_displayed()
```


## 11. 推荐的测试分层策略

不要把所有验证都压到 UI 层。

建议按价值拆分：

### UI 自动化保留

- 核心主链路冒烟
- 关键跨页面流程
- 登录/注册/设备绑定等高价值场景
- 真实交互验证

### 不建议全部放在 UI 层

- 纯字段校验逻辑
- 大量边界条件
- 数据组合爆炸场景
- 复杂业务规则穷举

这些更适合接口测试或单元测试承接。


## 12. 对当前仓库的直接建议

基于现有代码，建议优先做下面几件事。

### 建议一

把 [pages/base_page.py](C:\Users\Administrator\Desktop\New folder\osaio-ui-test\pages\base_page.py) 移到 `core/`，作为真正基础层。

### 建议二

把 [utils/driver_helper.py](C:\Users\Administrator\Desktop\New folder\osaio-ui-test\utils\driver_helper.py) 演进为 `core/driver_factory.py`，并支持：

- 多环境
- 多设备
- 平台差异化配置

### 建议三

把 [tests/test_login.py](C:\Users\Administrator\Desktop\New folder\osaio-ui-test\tests\test_login.py) 改成“调用 flow 的测试样板”，作为后续测试规范模板。

### 建议四

把 [pages/login_page.py](C:\Users\Administrator\Desktop\New folder\osaio-ui-test\pages\login_page.py) 拆成：

- 登录页操作
- 登录流程编排

这是当前收益最大的重构点。


## 13. 一个更合理的目标示例

理想状态下，一条登录测试应该长这样：

```python
def test_login_success(app_flow, login_flow):
    app_flow.launch_to_ready_state()
    home_page = login_flow.login_success("default_user")
    assert home_page.is_home_displayed()
```

而不是让测试关心：

- 是否有引导页
- 是否已登录
- 是否要退出重登
- 当前是不是登录页
- 要不要手动关闭弹窗

这些都应该由 flow 层兜住。


## 14. 实施优先级

如果只做最小投入，建议按这个顺序推进：

1. 新增 `flows/`，抽登录与启动流程
2. 抽全局弹窗处理
3. 配置化测试账号和场景数据
4. 让测试通过 fixture 直接使用 flow
5. 再逐步重构 page 和报告能力


## 15. 总结

当前项目的问题不是没有 Page Object，而是 Page Object 承担了太多不该承担的职责。

要提高 UI 自动化复用率，关键不是继续在测试里堆脚本，而是补齐下面三层：

- 公共基础层
- 业务流程层
- 数据配置层

对你们当前仓库来说，最值得先落地的是新增 `flows/`，把登录、启动准备、弹窗处理、退出登录这几块抽出来。只要这一步完成，后续大部分测试的可读性、稳定性和复用率都会明显提升。
