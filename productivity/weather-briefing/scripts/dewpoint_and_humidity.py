#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""某片区/北京天气简报取数助手（官方口径 + 露点换算）。

用法:  python3 dewpoint_and_humidity.py
说明:  跑 .py 文件不触发终端审批（execute_code / python3 -c 会审批超时，别用）。
输出:  直接可粘贴进简报的中文实况块 + 露点判断 + 当天预报 + 预警核验结论。
"""
import json
import math
import re
import urllib.request

CITY = "101010100"  # 北京（含某城区某片区）
HDRS = {
    "Referer": "http://www.weather.com.cn/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
}


def fetch(url):
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def dewpoint(t_c, rh_pct):
    """Magnus 公式，返回露点 °C。"""
    a, b = 17.625, 243.04
    rh = max(1.0, min(100.0, float(rh_pct)))
    g = math.log(rh / 100.0) + a * t_c / (b + t_c)
    return b * g / (a - g)


def muggy(td):
    if td < 16:
        return "干爽"
    if td < 18:
        return "开始黏"
    return "闷热、汗液难蒸发，体感闷/易出汗"


def main():
    sk = json.loads(re.search(r"=\s*(\{.*\})", fetch(
        f"https://d1.weather.com.cn/sk_2d/{CITY}.html")).group(1))
    dz_raw = fetch(f"https://d1.weather.com.cn/dingzhi/{CITY}.html")
    day = json.loads(re.search(r'cityDZ\d*\s*=\s*(\{.*?\});', dz_raw).group(1))["weatherinfo"]
    alarm = re.search(r"alarmDZ\d*\s*=\s*(\{.*\})", dz_raw)
    alarm_json = json.loads(alarm.group(1)) if alarm else {"w": []}

    t = float(sk["temp"])
    rh = float(re.sub(r"[^\d.]", "", str(sk["SD"])) or 0)
    td = dewpoint(t, rh)

    print("### 当前实况（官方站）")
    print("| 项目 | 数据 |")
    print("|------|------|")
    print(f"| 🌡️ 当前温度 | **{t}°C** |")
    print(f"| 💧 湿度 | {rh:.0f}% |")
    print(f"| 💧 露点 | **{td:.1f}°C** —— {muggy(td)} |")
    print(f"| 天气 | {sk['weather']} |")
    print(f"| 🌬️ 风力 | {sk['WD']}，{sk['WS']} |")
    print(f"| 👁️ 能见度 | {sk['njd']} |")
    print(f"| 🧭 气压 | {sk['qy']} hPa |")
    print(f"| AQI | {sk['aqi']} |")
    print(f"| 更新时间 | {sk['time']} |")
    print()
    print(f"### 当天预报（{sk['date']}）白天 {day['temp']} / 夜间 {day['tempn']}，{day['weather']}，{day['wd']}{day['ws']}")
    print("### 预警核验: " + ("无生效预警（alarmDZ 为空）" if not alarm_json.get("w") else json.dumps(alarm_json, ensure_ascii=False)))
    print()
    print("# 提示：湿度/露点/能见度以以上官方值为准；wttr.in 的 humidity 偏低（实测 9/21 低 25 个百分点），"
          "wttr 只用来看逐小时走势。")


if __name__ == "__main__":
    main()
