# AI HOT 独立脚本

独立可运行的 Python 脚本，不依赖 Hermes Agent，可直接被 cron 调用。

## 位置

`~/quant-lab/ai_daily.py`

## 用法

```bash
python3 ~/quant-lab/ai_daily.py              # 最新日报
python3 ~/quant-lab/ai_daily.py 2026-07-14   # 指定日期
python3 ~/quant-lab/ai_daily.py --open       # 生成后自动打开浏览器
```

## 依赖

仅 Python 标准库（`urllib.request`, `json`, `ssl`, `os`, `datetime`），零第三方依赖。

## 特性

- 浏览器 UA 自动带（避免 403）
- SSL 跳过验证（Mac 证书链兼容）
- 智能截断（句子边界，软上限 150 字）
- 响应式 CSS（768px / 400px 两级断点）
- 输出路径：`~/Documents/本地/ai探索/AI日报/AI日报_{date}.html`

## 集成到 Cron

```bash
crontab -e
# 每天 08:05 生成昨日日报（日报 UTC 00:00 生成，北京时间 08:00 后可用）
5 8 * * * /usr/bin/python3 /Users/you/quant-lab/ai_daily.py
```
