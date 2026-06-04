# OSAIO Auto Test

独立脚本，无需原项目框架，只需安装：

```
pip install uiautomator2 requests
```

## 脚本说明

- `full_auto.py` — 注册→退出→重新登录完整流程
  - 自动获取邮箱验证码（tempmail.plus）
  - 处理通知权限弹窗（等2秒关闭）
  - 用新邮箱：改第46行 `email = "testbXX@mailto.plus"`
- `get_code.py` — 独立获取验证码：`python get_code.py testbXX@mailto.plus`
- `login_two_accounts.py` — 两个账号切换登录
- `register_only.py` — 纯注册脚本

## 设备信息

- 序列号: `R5CT34HNGTN`
- 屏幕: 1080×2340, Samsung S22

## 关键坐标

- 账户标签: (842, 2277)
- 用户信息行: (540, 550)
- 退出登录: (555, 1978)
- 确认退出: (555, 1133)
- 通知"不允许": (539, 2065)
- 登录按钮: (589, 1394)
