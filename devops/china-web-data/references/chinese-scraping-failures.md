# Chinese Web Scraping: What Fails and Why

When trying to scrape structured data (phone, address, operator) about Chinese scenic spots or businesses, the following approaches were tested and ALL failed:

## Failed Approaches

| Source | Issue | Status Code |
|--------|-------|-------------|
| Baidu Map web | Heavy SPA, data in canvas/WebGL, Playwright `inner_text` returns empty | 200 but no data |
| Baidu Map search | JS-rendered results, DOM selectors don't match rendered content | 200 but tags mismatch |
| Ctrip (携程) | SPA, search results load via AJAX, detail pages blocked | 404 on search |
| Mafengwo (马蜂窝) | Anti-bot, returns 202 with captcha | 202 |
| Baidu Baike (百度百科) | Aggressive anti-scraping, 403 on all requests | 403 |
| Baidu Baike mobile | Same 403, even with iOS/mobile UA | 403 |
| Sogou (搜狗百科) | Returns 200 but no structured data in DOM | 200 but empty |
| Bing search | Returns search snippets with no phone numbers | 200, noisy |
| Dianping (大众点评) | Login wall, captcha, no data without auth | blocked |
| GitHub/Gitee | No open datasets found for Beijing scenic spots | 0 repos |
| Wikipedia Chinese | Has infoboxes with addresses and operators, but NO phone numbers | 200, partial |

## What Works

### Amap API (高德地图)
- Free tier: 5000 req/day
- Clean JSON response with `tel`, `address`, `location`
- 30 seconds for 72 entities
- Registration: https://console.amap.com/dev/key/app (free, 5 min)

### akshare (for financial data)
- `stock_zh_index_daily()` — indices always work
- `stock_zh_a_hist()` — may fail with proxy errors on `push2his.eastmoney.com`

### yfinance (for Chinese stocks)
- `.SS` suffix for Shanghai, `.SZ` for Shenzhen
- More reliable than akshare for individual stocks

## Key Insight

**Don't waste time scraping Chinese websites for structured data. Go straight to the Amap API** for POI/location data, and use akshare/yfinance for financial data. Web scraping in the Chinese internet ecosystem is significantly harder than Western equivalents due to:
- Widespread SPA architecture
- Aggressive anti-bot measures (even on public data)
- JS rendering requirements for basic content
- Captcha walls on previously open platforms
