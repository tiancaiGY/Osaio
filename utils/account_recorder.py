"""注册账号落盘工具：把每次成功注册的账号追加保存到 CSV，便于回溯/复用。

文件：reports/registered_accounts.csv（表头：timestamp,email,password,country）。
追加写入，保留历史；首次创建时写表头。
"""
import csv
import os
from datetime import datetime

_CSV_PATH = os.path.join("reports", "registered_accounts.csv")
_HEADER = ["timestamp", "email", "password", "country"]


def save_registered_account(email, password, country="", path=_CSV_PATH):
    """追加一条注册账号记录到 CSV。异常不抛出（记录失败不应影响测试）。返回是否写入成功。"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        new_file = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(_HEADER)
            w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), email, password, country])
        print(f"已保存注册账号到 {path}: {email} / {password} ({country})")
        return True
    except Exception as e:
        print(f"保存注册账号失败（忽略）: {e}")
        return False
