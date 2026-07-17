"""注册国家配置。

集中管理"可选择国家"及其在注册页国家列表里的匹配文案。当前支持三个：
  - China          (+86)
  - United States  (+1)
  - United Kingdom (+44)

用法：
    from utils.countries import get_country, DEFAULT_COUNTRY
    c = get_country("US")          # -> Country(key='US', name='United States', code='+86'...)
    register_page.select_country(c.name)

可用环境变量 OSAIO_COUNTRY 覆盖默认（值可为 key 或名称，大小写不敏感）：
    OSAIO_COUNTRY=UK pytest ...
"""
import os
from collections import namedtuple

Country = namedtuple("Country", ["key", "name", "code"])

# key（简称/别名）-> Country。注册页国家列表条目形如 "China"、"United States (+1)"，
# 故 name 用于在列表中 textContains 匹配。
_COUNTRIES = {
    "CN": Country("CN", "China", "+86"),
    "US": Country("US", "United States", "+1"),
    "UK": Country("UK", "United Kingdom", "+44"),
}

# 常见别名 -> 规范 key
_ALIASES = {
    "CHINA": "CN", "中国": "CN", "+86": "CN", "86": "CN",
    "USA": "US", "UNITED STATES": "US", "AMERICA": "US", "美国": "US", "+1": "US", "1": "US",
    "GB": "UK", "UNITED KINGDOM": "UK", "ENGLAND": "UK", "BRITAIN": "UK", "英国": "UK", "+44": "UK", "44": "UK",
}

DEFAULT_COUNTRY_KEY = "CN"


def _normalize(value):
    if not value:
        return DEFAULT_COUNTRY_KEY
    v = str(value).strip().upper()
    if v in _COUNTRIES:
        return v
    return _ALIASES.get(v, DEFAULT_COUNTRY_KEY)


def get_country(value=None):
    """按 key/别名/名称取国家；None 时取默认（可被环境变量 OSAIO_COUNTRY 覆盖）。"""
    if value is None:
        value = os.environ.get("OSAIO_COUNTRY", DEFAULT_COUNTRY_KEY)
    return _COUNTRIES[_normalize(value)]


def all_countries():
    """返回全部可选国家 {key: Country}。"""
    return dict(_COUNTRIES)


DEFAULT_COUNTRY = get_country()
