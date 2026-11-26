---
name: china-web-data
description: >-
  Patterns for scraping/acquiring structured data from Chinese websites +
  WeChat ecosystem analysis and venue payment adaptation. Covers: what works
  (Wikipedia infoboxes, Amap API with key, akshare, Baidu AI Search), what
  fails (Baidu Baike 403, Baidu Map SPA, Ctrip SPA, Sogou noise), anti-scraping
  realities, Playwright RPA patterns for Chinese SPAs, WeChat official account /
  mini-program / H5 status research, and payment gateway adaptation analysis
  for tourism/venue scenarios. Load this whenever scraping Chinese POI,
  government, travel data, or evaluating WeChat ecosystem + payment
  integration.
tags: [scraping, china, rpa, playwright, chinese-web, wechat, payment, tourism, analytics]
---

# China Web Data Acquisition

## Key Reality

Chinese websites are **much harder to scrape** than Western sites. Heavy SPA architectures,
aggressive anti-scraping (Baidu returns 403 on many requests), and JS-rendered content
are the norm. Set expectations accordingly — a task that would take 5 minutes on a
US/European site may be impossible or take hours on Chinese equivalents.

## What Works

### Baidu AI Search API (百度千帆 AI 搜索) — #1 for Chinese real-time info
- `POST https://qianfan.baidubce.com/v2/ai_search/chat/completions`
- Returns structured results with dates, URLs, and content snippets
- Free tier: 100 requests/day (script hard-capped at 80)
- Use for: news, latest developments, current events, real-time data
- **This is the primary method for Chinese web search.** Do NOT scrape Sogou/Bing/Baidu search results.

### Baidu AI Search — Bilibili video transcripts
- `yt-dlp --cookies-from-browser chrome` to download audio from Bilibili
- `faster-whisper` with `tiny` model for Chinese transcription (fast, good quality)
- Avoid: openai-whisper medium on CPU (hours), faster-whisper medium (large download)
- Workflow: `yt-dlp -f worstaudio → faster-whisper tiny → LLM summary → HTML`

### Wikipedia Chinese (zh.wikipedia.org)
- **Best source for structured data**: infoboxes contain addresses, operators, coordinates
- No phone numbers typically
- Static HTML, easy to parse
- Use Playwright with `wait_until='networkidle'` → `page.locator('.infobox')`

### akshare (Python library)
- Excellent for Chinese financial/market data
- `ak.stock_zh_a_hist()`, `ak.stock_zh_index_daily()` for A-shares
- No tourism/scenic-spot functions as of 2024
- **⚠️ 财联社 (cls) 支持已废弃**: 财联社下线了 `/nodeapi/telegraphList` 接口，akshare 已移除 cls 相关功能。如需财联社电报数据，参见 `references/cailianpress-data-access.md`

### Amap (高德) POI API — Primary Method for Chinese POI Data

**Setup**: Register at https://console.amap.com/dev/key/app → create app, select "Web服务" → get API key. Free tier: 5000 requests/day.

**Text search** (batch query by name):
```
GET https://restapi.amap.com/v3/place/text
Params: key=XXX, keywords=景区名称, city=北京, output=JSON, offset=1
```
Response: `pois[0].tel` (phone), `pois[0].address`, `pois[0].name`, `pois[0].location` (lng,lat).

**Detail query** (deep info for specific POI):
```
GET https://restapi.amap.com/v3/place/detail
Params: key=XXX, id=POI_ID, output=JSON
```

**Batch lookup pattern** (with incremental saving every 10 items to survive interruptions):
```python
import requests, time, csv

for i, name in enumerate(entity_names):
    r = requests.get(API, params={'key': KEY, 'keywords': name, 'city': '北京', ...})
    data = r.json()
    if data['status'] == '1' and data['count'] != '0':
        poi = data['pois'][0]
        # Verify name match — API may return a different POI
        if poi.get('name') != name:
            print(f"[WARN] Name mismatch: {name} → {poi.get('name')}")
        # Extract: phone, address, location
    else:
        # Retry without city prefix (e.g. strip "北京")
        ...
    time.sleep(0.3)  # ~3 req/sec
    if (i+1) % 10 == 0:
        # Incremental save
```

**Address → District extraction**: match against Beijing's 16 districts (东城区, 西城区, 朝阳区, ...).

**Operator inference** (when deep_info has no company data):
- `XX公园` → `北京市XX公园管理处`
- `XX博物馆` → `XX博物馆`
- `XX寺/庙/宫` → `XX寺管理处`
- Annotate: `【推断】` vs API-sourced `【高德】`

**API pitfalls**:
- Name mismatch: API may match a similar-named POI. Verify `pois[0].name` vs query.
- Missing phones: parks/natural areas often have no phone — mark as "无电话", don't retry.
- Rate limit: ~5 req/sec. Free tier: 5000/day.
- API key exposure: key is in code. Remind user to rotate if shared.

### DataV GeoJSON API (阿里云 DataV) — Chinese administrative boundaries
- `https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json`
- **No API key required.** Free, public CDN. Returns GeoJSON FeatureCollection.
- Adcode structure: `100000`=China, `110000`=Beijing, `110101`=Dongcheng District
- Use `_full.json` suffix to include all sub-regions recursively
- Province codes: xx0000 (plus municipalities 110000/120000/310000/500000)
- County codes: 6-digit adcodes (e.g., 110101)
- ~580KB for China national boundary, ~100KB per province
- See `references/datav-geojson-api.md` for full adcode reference and integration patterns

### yfinance for Chinese stocks
- Major Chinese stocks available via `.SS` (Shanghai) or `.SZ` (Shenzhen) suffixes
- Example: `600519.SS` (Kweichow Moutai), `300750.SZ` (CATL)
- Works reliably

### Hermes Agent Self-Update (GFW 环境)

`hermes update` 底层依赖 `git pull` 从 GitHub 拉取，在中国大陆会被 GFW 阻断。解决方案：切换 git remote 至 GitHub 镜像站（如 ghproxy.net），详见 `references/hermes-update-china.md`。涵盖镜像选择、浅克隆兼容性、以及 pip 不可用的说明。

### List-page title truncation → recover from detail page `<title>`

Chinese list pages (PCAC 支付清算协会, many gov portals) truncate article titles at a fixed char count (often ~39 chars) ending with `...`. The full title lives in the detail page's `<title>` tag, which urllib can fetch directly **even when the article body is JS-rendered** (the `<head>`/`<title>` is always in the initial HTML). Recovery pattern:

```python
def fill_full_title(url, truncated):
    html = fetch(url)  # urllib, no browser needed
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL)
    full = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''
    full = re.sub(r'\s+', ' ', full)
    # only accept if meaningfully longer and not a nav/fallback title
    if len(full) > len(truncated) + 3 and not full.startswith('首页'):
        return full
    return truncated
```

Batch-apply to every truncated title in a scrape result (0.15s sleep, skip `.pdf` URLs). Rescued 13/13 truncated PCAC titles in one run.

### TRS/大汉 CMS 附件批量下载（政府网站预决算公开）

bjft.gov.cn 等 TRS 站点结构：栏目页 `breadcrumb → <ul class="bmjs">` 列部门子目录 → 子目录列表页列公开条目 → 条目页 `div.zw_enclosure` 内放附件 `<a href="./P0202....pdf">真实文件名.pdf</a>`。

三个必踩的坑：
1. **分页参数不是页数**：`createPageHTML('page_div',8,0,'index','shtml',115)` 的 `115` 是**条目总数**，不是页数（每页 15 条）。不要按总数生成 `index_1..index_114`（全 404，每个 404 还会被 retry 拖死）。正确做法：按 8 个一批并发探测 `index_N.shtml`，遇到第一个 404 即停。
2. **闭合标签带空格**：站点输出 `</a >`（`>` 前有空格），`href="..."[^>]*>(.*?)</a>` 匹配不到，会贪婪吞掉后续附件链接 → 每篇只抓到 1 个附件。正则要用 `</a\s*>`。
3. **附件名来自锚文本，不是 URL**：URL 一律是 `P020260205717607511365.pdf`，真实文件名只在锚文本里；有的站点锚文本自己就带重复后缀（`xx报表.pdf.pdf`），落盘时折叠一次。少数报表是 `.jpg` 图片，正则要额外放行 `zw_enclosure` 内的 jpg/png（全页放行会抓到 banner）。

验收：每条附件 `%PDF` 头 + `pdfinfo` Pages>0；按 `部门/附件名` 落地，另出清单 xlsx（部门/标题/附件名/大小/附件地址/公开页面）。2026-11 某城区 2026 部门预算：103 部门 / 301 条公开 / 604 个附件 / 156MB，0 失败。

## What Does NOT Work

### Baidu Baike (百度百科)
- **Returns 403 on almost all programmatic requests**
- Even mobile User-Agent fails
- Do not waste time trying

### Baidu Maps Web (百度地图)
- Heavy SPA, data loaded via JS + canvas
- `inner_text` returns empty for POI data
- Even with Playwright `networkidle` wait, POI data not extractable
- Internal API keys are embedded in obfuscated JS

### Ctrip (携程)
- SPA with JS-rendered search results
- Detail pages load data dynamically
- Playwright headless browser can't reliably extract phone/address

### Sogou WeChat (weixin.sogou.com) — WORKS with correct cookie chain (verified 2026-09-09)
- Earlier failures were missing the cookie chain: without SNUID, `/link` → antispider page.
- Working recipe and script: see `wechat-ecosystem-search.md` §2 or `/Users/you/quant-lab/sogou_link_follow.py`.
- Still rate-sensitive: keep `sleep(2)` pacing; noise in snippets remains an issue — parse the result page structure (`txt-box`, `<h3>`), don't grep raw text.

### General Chinese Government Sites
- Often SPAs with undocumented internal APIs
- Example: `banshi.whlyj.beijing.gov.cn/xinyong/#/mljq` — SPA, no discoverable API endpoint

## Playwright RPA for Chinese Sites

### Installation
```bash
pip3 install playwright
python3 -m playwright install chromium
```

### Pattern for Chinese SPAs
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        viewport={'width': 1280, 'height': 900},
        locale='zh-CN'
    )
    page.goto(url, timeout=30000, wait_until='networkidle')
    page.wait_for_timeout(3000)  # Extra wait for JS
    # Then try page.locator() for specific elements
```

### When Playwright RPA Fails
If `inner_text` returns empty or wrong data after `networkidle` + 3s wait,
the site is using canvas/WebGL rendering or AJAX loading that headless
browsers can't capture. **Stop and try a different data source** — don't
keep iterating on the same broken approach.

## CRITICAL: Rapid-Failure Rule

**If a scraping approach fails 2 times, STOP and switch data sources immediately.** Do NOT iterate on the same broken approach. Each failure site (Baidu Map, Ctrip, Baidu Baike, Dianping) was tested exhaustively — the result will not change with different headers, wait times, or selectors. The fastest path to useful data is to skip directly to Amap API (POI data), akshare (financial data), or Wikipedia (general info).

This is a hard-learned rule. Users get frustrated when you burn 30+ minutes cycling through blocked sites instead of pivoting to what works.

## POI Data Collection Workflow

When collecting structured data about Chinese local entities (scenic spots, businesses, POIs):

1. **Get Amap API key** (free, 5 minutes registration)
2. **Batch query** all targets via `place/text` endpoint (0.3s sleep between calls)
3. **Extract** phone + address from JSON response
4. **Infer** district from address string
5. **Attempt** deep_info for operator; fall back to name-pattern inference
6. **Annotate** data source reliability on each field
7. **Output** as xlsx/CSV with columns: name, phone, address, district, operator, source annotation

See `scripts/amap_batch_lookup.py` for full template and `references/chinese-scraping-failures.md` for exhaustive list of failed approaches.

When asked to scrape Chinese data:

1. **Check if akshare has it** (financial data) — if yes, use it
2. **Check Wikipedia** (general info, addresses, operators) — if yes, use Playwright
3. **Check if an API exists** (Amap for POI, etc.) — ask user for API key
4. **Be honest if scraping won't work** — don't burn time on Baidu Baike/Baidu Maps/Ctrip
5. **Suggest alternatives** — manual compilation, API keys, paid data services

### XHS (小红书) Social Media Data — Spider_XHS

For programmatic access to Xiaohongshu (小红书) — China's dominant lifestyle/travel social platform with rich tourism content (spot reviews, travelogues, food guides) — see [Spider_XHS](references/xhs-scraping-spider-xhs.md). It reverse-engineers XHS's client-side signature algorithms via environment completion (补环境), enabling keyword search, note detail extraction, comment scraping, and KOL data. Requires a real XHS login cookie. 6.3k+ stars on GitHub, actively maintained since 2023.

### Browser-Based Multi-Engine Search

When the Baidu AI Search API isn't suitable (rate-limited, need multi-engine, need real browser rendering), use the `universal_search.py` tool at `/Users/you/universal-search/`. See `references/web-search-tool.md` for full usage, engine reliability ratings, anti-detection features, and Kaggle/GitHub code research workflows.

### Government Report Scraping (政府工作报告)

For batch scraping Chinese government work reports (北京市及各区), see `references/gov-report-scraping.md`. Covers Baidu AI Search URL discovery, encoding handling (GBK/UTF-8), browser-based WAF bypass, PDF extraction via pdftotext, and common URL patterns for Beijing district portals.

### Government Policy Tracking (政府政策动态追踪)

For automated scraping of Chinese government websites for leadership changes and regulatory policy updates, see `references/gov-site-scraping-patterns.md`. Covers 26 tested URLs across PBoC, NFRA, SAMR, SAFE, Beijing municipal government, and local financial bureaus. Documents 3 scraping methods (urllib+BS4, urllib+regex, Browser/Playwright), encoding patterns (GBK vs UTF-8), nfra.gov.cn Angular SPA pitfalls, and article extraction regex patterns. Includes browser-verified data from xzxk.pbc.gov.cn (11 admin approval categories) and nucc.com (21+ articles across 3 tabs).

### Enterprise Customer Research (对公客户信息挖掘)

When researching Chinese companies for customer relationship mining (客户关系挖掘), credit assessment, or lead generation — given company names and/or unified social credit codes — see `references/enterprise-customer-research.md`. Covers a 4-layer data source hierarchy (basic registration → business activity → financial health → demand signals), a batch execution pipeline, and known limitations.

### WeChat Ecosystem Search (公众号 / 小程序 / H5)

When researching whether Chinese organizations have WeChat official accounts, mini-programs, or H5 pages, see `references/wechat-ecosystem-search.md`. Covers 5 search methods (WeChat 搜一搜, Sogou WeChat, Official Platform, third-party platforms, Baidu search + batch API pattern), URL structure, and anti-patterns. **Use Baidu AI Search API as the primary batch approach** — Sogou WeChat has aggressive anti-spider that blocks programmatic access.

## Consolidation History

- **2026-08-05**: Absorbed `gov-policy-tracker` — 中国政府网站政策动态追踪 skill was entirely a subset of this umbrella. Its 26 tested URLs, 3 scraping methods, encoding handling, and nfra.gov.cn patterns were already covered in `references/gov-site-scraping-patterns.md`. Unique operational detail (nfra.gov.cn ItemId table, pbc.gov.cn anti-crawl specifics, website rename tracking, date extraction priority, leader extraction template, Excel report format, quick decision tree) merged into the reference file.

- **2026-08-03**: Added `references/gov-site-scraping-patterns.md` — government site scraping patterns from full-scale testing of 26 Chinese government URLs. Documents which sites work with urllib (19/26), which require Browser rendering (5/26), encoding handling (GBK/UTF-8), nfra.gov.cn Angular SPA pitfalls, and reliable regex for article extraction.

- **2026-08-03**: Added `references/cailianpress-data-access.md` — comprehensive guide to acquiring Cailian Press (财联社) financial news/telegraph data via RSSHub, open-source libraries (cailianpress-unified, a-stock-data), Python scrapers, and paid RSS services. Documents deprecated endpoints and the signature-auth reality.

- **2026-07-15**: Absorbed `venue-payment-analysis` — the WeChat ecosystem payment adaptation workflow for tourism/venue scenarios. Moved to `references/venue-payment-analysis.md` and `references/fengtai-wechat-ecosystem.md`. The venue analysis builds on the WeChat ecosystem search and Baidu AI Search patterns already covered here.
- **2026-06-09**: Absorbed `web-search` skill — its universal_search.py tool reference, Kaggle research workflow, Chinese PDF hunting guide, and research report patterns moved here as reference files.

## Critical Workflow Rule

**Don't trial-and-error scrape.** If the user asks for Chinese web data, go straight to the known working approach (Amap API, Wikipedia, akshare). Do NOT try Baidu Map → Ctrip → Baidu Baike → Sogou → Dianping sequentially. Each dead end burns minutes and frustrates the user. One attempt at each category is enough before declaring it blocked and pivoting.

**Follow the user's specification EXACTLY.** If the user provides a detailed data schema (Excel columns, field names, grading rules), implement ALL fields. Do NOT simplify or create a "quick version". The user has explicitly rejected simplified outputs with "你有没有按照这个来做？". For government monitoring tasks, see `references/gov-site-scraping-patterns.md` for the full 20+16 field Excel specs.

### Official government leadership-page verification

For requests to inventory current leaders of Chinese district government departments, search results are discovery only, never evidence. Use the detailed checklist in `references/official-leadership-page-verification.md`. Resolve each result to the direct government URL, open that official page in a browser, and inspect the rendered body.

**⚠️ Accessibility tree trap**: Government department pages (especially leadership lists rendered via JavaScript tabs) often show NOTHING in the browser accessibility snapshot even though `document.body.innerText` contains the full leader data. **Always use `browser_console` + `document.body.innerText` as the primary extraction method**, not the snapshot. Example: 密云、延庆部门领导页的 accessibility tree 完全为空，但 innerText 包含完整【姓名】【职务】列表。

**⚠️ Tab-click pattern**: Department pages commonly use tabbed navigation (机构职责 | 领导介绍 | 内设机构). The "领导介绍/领导班子" tab must be **clicked first** before innerText will contain leader names. Without clicking, the page shows only institutional info. Click via:
```javascript
[...document.querySelectorAll('*')].find(x => x.innerText.trim() === '领导班子').click()
```
Tab elements may be `<li>` or `<div>`, not `<a>`. Verified across 密云、延庆、东城、大兴、朝阳.

Use `document.body.innerText` via browser console when accessibility text omits JS-rendered content. Record only names and titles literally present in the page body. Distinguish an official institution/function page from an actual "领导介绍/领导班子" page: if the official page has no leader list after clicking the tab, report "未找到官网领导页/页面未公开领导名单" rather than importing names from Baidu snippets, Baike, media, or third-party aggregators. For multi-district × multi-department work, maintain a matrix so every requested cell is explicitly marked found or not found, and include the direct official URL for every found page. Legacy government subdomains and HTTP pages can still be official; verify the breadcrumb, government-site footer, and hosting domain before accepting them. When discovery yields a Baidu `/link?url=` redirect, it is acceptable as a navigation hop only: follow it, capture the final resolved government URL, and cite/store that final URL—not the Baidu redirect. On Beijing portals, a person-detail template may expose the exact `领导姓名：...` and `职务：...` fields only through `document.body.innerText` even though the accessibility snapshot shows just the person's name; inspect both before declaring the page incomplete.
