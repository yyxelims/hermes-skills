# JS 反爬挑战检测与清理 — 三道防线

## 问题

国家外汇管理局 (safe.gov.cn) 等站点检测 headless Chrome/urllib，返回 JS 挑战页面而非正文。
正文列出现 `function u(o,s)` + 大量 `0x` 十六进制 = JS 混淆代码，不是真实正文。

## 防线一：HTML 关键词检测（scrape_details.py）

在 `fetch_detail()` 返回 HTML 后、`extract_from_html()` 之前执行：

```python
def is_js_challenge(html):
    if '浏览器环境检查' in html or '环境检查中' in html:
        return True
    if '请开启 JavaScript' in html or '请开启JavaScript' in html:
        return True
    if '请稍等几秒钟' in html:
        return True
    if 'Please enable JavaScript' in html:
        return True
    if 'function u(o,s)' in html[:500] and '0x' in html[:500]:
        return True
    return False
```

**关键**：检测必须在 HTMLParser 之前。HTMLParser 会把 JS 代码当正文清理掉，导致后续检测失效。

## 防线二：Playwright 共享 Browser 兜底（scrape_details.py Phase 2）

检测到 JS 挑战 → 用共享 Playwright Browser 实例渲染。不能多线程。

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for r in js_articles:
        page = browser.new_page()
        page.goto(url, wait_until='load', timeout=20000)
        page.wait_for_timeout(1500)
        html = page.content()  # 或 page.evaluate('document.body.innerText')
        page.close()
    browser.close()
```

**限制**：safe.gov.cn 仍能检测部分 headless Chrome。修复率约 33%（61/186）。
剩余无法修复的多为导航/索引页（本身无实质内容）。

## 防线三：build_final.py 双重过滤

```python
# 空正文过滤
if not body or len(body) < 50:
    continue

# JS 密度检测（正文 >50 字但全是 JS 代码）
if ('0x' in body[:500] and 'function' in body[:300] and body[:500].count('0x') > 3) \
   or '浏览器环境检查' in body \
   or 'Please enable JavaScript' in body:
    continue
```

## 正文级 JS 检测（is_js_body）

用于清理 detail_pages_llm_v2.json 中残留的 JS 正文：

```python
def is_js_body(text):
    if not text or len(text) < 100:
        return False
    h500 = text[:500]
    if h500.count('0x') > 5 and sum(1 for kw in ['function','var ','return'] if kw in h500) >= 2:
        return True
    return False
```

命中后同时清空 `detail_body` 和 `llm_summary`，然后重跑 LLM。

## 检测模式完整清单

| 模式 | 来源站点 | 示例 |
|------|---------|------|
| `浏览器环境检查中` | safe.gov.cn | 页面 title |
| `请开启 JavaScript 功能并刷新页面` | safe.gov.cn | body 开头 |
| `请稍等几秒钟` | safe.gov.cn | body 开头 |
| `Please enable JavaScript and refresh the page` | safe.gov.cn | body 开头 |
| `function u(o,s)` + `0x` | 多个站点 | JS 混淆代码 |
| `0x` 密度 >5 + `function` ≥3 | 多个站点 | 启发式检测 |
