#!/usr/bin/env python3
"""
Browser站点自动化抓取 (Playwright) — 使用说明
==============================================
覆盖：金融监管总局(nfra) + 市场监管总局(samr) + 网联清算(nucc)

安装:
  pip3 install playwright && python3 -m playwright install chromium

用法:
  python3 browser_scraper.py                  # 全量
  python3 browser_scraper.py --site nfra      # 仅金监总局
  python3 browser_scraper.py --cron           # cron模式,输出JSON

数据输出: leader_data/browser_snapshots/browser_scrape_YYYYMMDD_HHMMSS.json

关键实现细节:
- nfra: wait_until='load' (非networkidle，避免超时), 然后wait_for_timeout(5000)
- samr: 从DOM提取领导链接, 逐页访问详情
- nucc: tab切换用page.evaluate执行element.click()

源代码位置: /Users/you/Documents/工作/2026创新大赛/agent/政策动态追踪/browser_scraper.py
