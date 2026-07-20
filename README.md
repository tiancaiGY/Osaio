# OSAIO App UI 自动化测试

基于 **Appium + pytest + Page Object Model** 的 OSAIO 摄像头 App（Android 包名
`com.afar.osaio`）UI 自动化测试工程。覆盖注册 / 登录 / 配网 / 直播出图 / 云存订阅 /
云卡回放等主功能，并以一条端到端 **Smoke 主流程**作为每轮测试前的健康门禁。

> App 界面语言可能为**中文或英文**，所有定位器均使用 `textMatches` / `descriptionMatches`
> 做双语（zh/en）语言无关匹配，勿写死单语言文案或固定 tab 序号（tab 数量随账号为 3 或 4 个）。

---

## 1. 环境准备

```bash
# 1. 安装 Appium 2 及 UiAutomator2 驱动
npm install -g appium
appium driver install uiautomator2   # Android（本工程主用）
appium driver install xcuitest        # iOS（可选）

# 2. 安装 Python 依赖（Python 3.12）
cd osaio-ui-test
pip install -r requirements.txt

# 3. 启动 Appium Server（默认 127.0.0.1:4723）
appium
```

**真机前置**（本工程针对真机运行，非模拟器）：

- 一台已开启 USB/无线调试的 Android 真机，`adb devices` 可见。
- `config/caps.yaml` 里 `deviceName` 为无线调试地址（形如 `192.168.71.116:44713`）；
  用有线设备时改成 `adb devices` 显示的序列号。
- 配网 / 直播 / 回放类用例需要现场真实条件：待配网 IoT 设备、`mmm_test`（2.4GHz，密码
  `mmmmmmmm`）WiFi、以及在线的已配网设备等（见下文各用例前置）。

> `noReset: true`：会话之间**不清除** App 数据，登录态会被保留（“记住我”）。因此需要
> “从登录页开始”的用例会先走一次 UI 登出（`ensure_logged_out`），而 Smoke 主流程用
> `adb shell pm clear` 重现首装。

---

## 2. 账号配置

所有测试账号集中在 [config/accounts.yaml](config/accounts.yaml)，加载逻辑见
[utils/accounts.py](utils/accounts.py)，**代码里不再硬编码账号**。

| 名字 | 默认账号 | 用途 |
| --- | --- | --- |
| `primary` | `kyg01@bccto.cc` | 主流程 / 登录用例 |
| `secondary` | `ocn03@bccto.cc` | 设备操作 / 错误处理 / 性能用例，**且满足云卡回放前置**（在线设备 GP5B） |
| `switch_a` / `switch_b` | `testa31@mailto.plus` / `testa32@mailto.plus` | 账号切换用例 |
| `cloud` | `ab1@bccto.cc` | 云存购买用例（需“测试者账号”权限，普通新注册账号无权限） |

可用**环境变量覆盖**任意字段（便于 CI / 本地私密账号，避免真实账号入库）：

```bash
# 覆盖具名账号（KEY 形如 PRIMARY / SECONDARY / SWITCH_A / CLOUD）
OSAIO_PRIMARY_ACCOUNT=foo@bar.cc OSAIO_PRIMARY_PASSWORD=secret pytest ...
# 覆盖错误密码用例值 / 注册脚本默认密码
OSAIO_WRONG_PASSWORD=xxx  OSAIO_REGISTER_DEFAULT_PASSWORD=123456
```

---

## 3. 运行测试

```bash
# 全部用例（默认 Android）
pytest

# 按标记（marker）跑某个模块，见 pytest.ini
pytest -m smoke -s          # Smoke 主流程（端到端门禁，见第 5 节）
pytest -m subscription -s   # 云存购买
pytest -m playback -s       # 云卡回放
pytest -m network -s        # 蓝牙配网

# 指定单个文件 / iOS 平台
pytest tests/test_login.py
pytest --platform=ios

# 自定义报告标题 / 目录（默认输出到 reports/）
pytest -m smoke -s --report-title "OSAIO 主功能测试报告" --report-dir reports
```

### 常用环境变量

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `FRESH_INSTALL` | 未设 | `=1` 时 Smoke 步骤 1 断言确实经过首装引导页（配合 `pm clear`） |
| `SMOKE_NO_RESET` | 未设 | `=1` 时 Smoke 跳过 `pm clear`（沿用现状，供调试） |
| `OSAIO_COUNTRY` | `CN` | 注册国家，可选 `CN` / `US` / `UK`（见 [utils/countries.py](utils/countries.py)） |
| `TEMP_EMAIL_DOMAIN` | `mailto.plus` | 注册用临时邮箱域名（`@mailto.plus` 实测可收到 OSAIO 验证码） |
| `OSAIO_CODE_TIMEOUT` | `180` | 注册验证码等待秒数 |
| `SHORT_WAIT` | 未设 | `=1` 时页面基类显式等待由 15s 缩短到 5s（快速本地迭代） |

---

## 4. Pytest 标记（markers）

定义于 [pytest.ini](pytest.ini)：

| marker | 含义 | 当前应用于 |
| --- | --- | --- |
| `smoke` | 冒烟 / 主流程门禁 | `test_smoke_main_flow.py` |
| `subscription` | 订阅 / 云存购买 | `test_cloud_storage.py` |
| `playback` | 云卡回放 | `test_playback.py` |
| `network` | 蓝牙配网 | `test_network_config.py` |

> `login` / `home` / `device` 三个 marker 已在 `pytest.ini` 声明，但**当前尚未**标注到任何用例，
> 故 `pytest -m login|home|device` 会收集到 0 条用例。对应的 `test_login.py` / `test_home.py` 等
> 目前不带 marker，直接按文件名运行（见第 6 节）。

---

## 5. Smoke 主功能流程

[tests/test_smoke_main_flow.py](tests/test_smoke_main_flow.py) 是一条端到端用例，作为每轮
测试前的**健康门禁**：任一必需步骤失败即整条 fail。步骤在报告里逐条展开
（passed / failed / skipped）。

```bash
pytest tests/test_smoke_main_flow.py -m smoke -s --report-title "OSAIO 主功能测试报告"
# 重现首次安装引导页：
FRESH_INSTALL=1 pytest tests/test_smoke_main_flow.py -m smoke -s
```

流程步骤：

| # | 步骤 | 说明 |
| --- | --- | --- |
| 0 | 首次安装重置 | `adb shell pm clear`，从干净首装态开始（`SMOKE_NO_RESET=1` 可跳过） |
| 1 | 打开 App → 引导页 | 同意条款 / 进入登录表单（`FRESH_INSTALL=1` 断言确有引导页） |
| 2 | 注册新用户（自动登录） | 临时邮箱取码注册，密码固定 `111111`，成功落盘 CSV |
| 3 | 退出 → 重新登录 | 用新注册账号重登 |
| 4 | 配网成功 | 蓝牙配网（需真实待配网设备 + `mmm_test` WiFi） |
| 5 | 出图成功（直播） | 直播页 `bit_rate` 出现即判定出图 |
| 6 | 订阅云存成功 | **占位 skip**（记为 skipped，不中断后续步骤） |
| 7 | **云卡回放成功** | **切到 `secondary` 账号**，依次验证 事件云回放 → 时间轴切换+滑动 → 卡回放(SD) → 云回放(Cloud) → 回到直播，每步以出图判定 |
| 8 | IOT 推送消息 | **占位 skip** |
| 9 | 消息列表显示历史消息 | 进入消息/事件 tab，验证列表出现 |
| 10 | 退出登录成功 | 回到登录页 |

> **步骤 7 为什么切账号**：云/卡回放需要“存在在线设备 + 云存订阅 + 历史录像/事件”的账号，
> 主流程新注册账号刚配网、无历史数据，不满足前置；`secondary`（ocn03）经确认已满足条件。
> `smart_login(force_login=True)` 会先登出当前会话再登入 `secondary`，此步之后 App 处于
> `secondary` 会话（后续步骤 9/10 照常在该会话执行）。该步复用与独立用例
> `test_playback.py` **同一套** [pages/playback_page.py](pages/playback_page.py)。
>
> **占位 skip 语义**：占位步骤（步骤 6/8）用 `pytest.skip` 标记，记为 skipped 但**不中断**
> 整条流程；只有真正的失败才会中止并 fail 整条 smoke。

---

## 6. 独立专项用例

| 文件 | marker | 账号 | 说明 |
| --- | --- | --- | --- |
| [tests/test_cloud_storage.py](tests/test_cloud_storage.py) | `subscription` | `cloud` | 云存年度订阅：订阅页 → Cloud Storage → Annual → 已存卡 `4242` 支付成功。需测试者账号权限；会切账号，故独立于 smoke |
| [tests/test_playback.py](tests/test_playback.py) | `playback` | `secondary` | 云/卡回放独立验证（与 smoke 步骤 7 同一套页面对象），需在线设备 GP5B、有云/卡录像与事件 |
| [tests/test_network_config.py](tests/test_network_config.py) | `network` | `primary` | 蓝牙配网两种入口（首页弹窗 / 右上角 `+`）直到直播出图 |
| [tests/test_register.py](tests/test_register.py) | — | 临时邮箱 | 注册模块（国家可配、临时邮箱取码） |
| [tests/test_login.py](tests/test_login.py) | — | — | 登录（含空账号/空密码/错误密码异常用例） |
| [tests/test_login_two_accounts.py](tests/test_login_two_accounts.py) | — | `switch_a/b` | 登录 A → 退出 → 登录 B 切换 |
| [tests/test_home.py](tests/test_home.py) | — | — | 首页展示 |
| [tests/test_logout.py](tests/test_logout.py) | — | — | 退出登录流程 |
| [tests/test_main.py](tests/test_main.py) | — | `account` | 早期主流程用例（登录 + 设备直播） |

---

## 7. 项目结构

```
osaio-ui-test/
├── config/
│   ├── caps.yaml           # Appium 能力（包名/Activity/deviceName/noReset/Appium地址）
│   └── accounts.yaml       # 集中账号配置（支持环境变量覆盖）
├── pages/                  # Page Object 页面对象
│   ├── base_page.py        # 页面基类（等待/点击/滑动/存在性等原语）
│   ├── login_page.py       # 登录页（smart_login / ensure_logged_out / 引导跳过）
│   ├── register_page.py    # 注册页（三步注册 + 国家选择）
│   ├── home_page.py        # 首页（底部 tab / 关权限弹窗）
│   ├── account_page.py     # 账户页（进入设置 / 退出登录，含关“添加设备”页干扰）
│   ├── device_page.py      # 设备/直播页（出图标志 bit_rate 等 id）
│   ├── network_config_page.py  # 蓝牙配网页
│   ├── cloud_storage_page.py   # 云存订阅购买页
│   └── playback_page.py    # 云卡回放页
├── tests/                  # 测试用例（见第 5、6 节）
├── utils/                  # 工具
│   ├── driver_helper.py    # Appium driver 创建/管理
│   ├── accounts.py         # 账号加载器（yaml + 环境变量覆盖）
│   ├── countries.py        # 注册国家配置（OSAIO_COUNTRY）
│   ├── temp_mail.py        # tempmail.plus 临时邮箱取验证码
│   ├── account_recorder.py # 注册账号落盘 CSV
│   └── report_generator.py # 品牌化 HTML/JSON 报告生成
├── code/                   # 独立脚本（uiautomator2 直驱，非 pytest）：注册/切换账号/取码
├── docs/                   # 设计文档（高复用框架方案 / 报告使用指南）
├── capture_state.py        # 手动抓取当前屏幕：截图 + page_source + id/text 列表
├── conftest.py             # pytest 全局 fixture + 报告钩子
├── pytest.ini              # pytest 配置与 markers
└── requirements.txt        # Python 依赖
```

---

## 8. 测试报告

会话结束后由 [utils/report_generator.py](utils/report_generator.py) 生成品牌化报告到
`--report-dir`（默认 `reports/`）：

- `reports/test_report_<时间戳>.html` — 可视化 HTML 报告（Smoke 会展开每个步骤）。
- `reports/test_report_<时间戳>.json` — 同数据的 JSON。
- `reports/registered_accounts.csv` — 注册用例产生的账号台账（**长期保留**）。
- 失败用例自动保存截图；页面对象排障时会另存 `page_source_*.xml` / `screenshot_*.png`。

> 报告系统的任何异常都被吞掉，**绝不影响**用例本身的通过/失败。
> 运行中间产物（`page_source_*` / `screenshot_*` / 时间戳报告）已在 `.gitignore` 忽略。

---

## 9. 辅助工具

- **手动抓屏**：`python capture_state.py <tag>` —— 复用当前 App 状态（不重启/不清数据），
  抓截图 + page_source，并打印 `com.afar.osaio` 的 resource-id 与前 30 条 text，便于定位新元素。
- **`code/` 脚本**：基于 `uiautomator2` 的独立自动化脚本（注册 / 双账号切换 / 取码），
  不依赖 Appium 会话，可单独运行辅助造数据。

---

## 10. 常见踩坑（务必知悉）

1. **语言无关定位**：界面中英不定，用 `textMatches` / `descriptionMatches`；tab 数量随账号
   为 3 或 4 个，按角色名（Home/Events/Account）匹配 content-desc，勿写死 `of 3`。
2. **“添加新设备 / 蓝牙搜索”干扰页**：BLE 自动发现会反复弹出全屏页/底部弹窗，遮住首页与底部
   tab，且重启后**延迟数秒**才出现，导致 `is_home_displayed()` 误判——每次点击 tab 前都要重检并关闭。
3. **RN 底部 tab 点击**：`element.click()` 对底部 tab 常无效，需对 tab 中心做**坐标点击**。
4. **noReset 登录态**：`noReset=true` + “记住我” 使重启仍保持登录，需 UI 走一次登出才回登录页。
5. **注册取码域名**：`@mailto.plus` 实测可收到验证码（`@tempmail.plus` 本身不收信）。
