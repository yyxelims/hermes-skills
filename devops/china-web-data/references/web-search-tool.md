# Universal Web Search Tool (universal_search.py)

Concrete browser-based multi-engine search tool at `/Users/you/universal-search/universal_search.py`.
Use this when the Baidu AI Search API isn't sufficient and you need real browser-rendered search results.

## Quick Usage

```bash
cd /Users/you/universal-search

# Single engine
python3 universal_search.py "关键词" -e baidu --headless --no-random

# Multi-engine
python3 universal_search.py "关键词" -e baidu,bing,sogou --headless --pretty

# Multi-page (3 pages)
python3 universal_search.py "关键词" -e baidu -p 3 --headless --no-random

# Output to file
python3 universal_search.py "关键词" -o results.json

# With proxy
python3 universal_search.py "关键词" --proxy http://127.0.0.1:7890
```

## Flags

| Flag | Effect |
|------|--------|
| `-e ENGINE` | Engine(s): baidu, bing, sogou, so360 (comma-separated) |
| `-p N` | Number of pages to fetch (default: 1) |
| `--headless` | Run browser in headless mode (no window) |
| `--no-random` | Skip random delays (faster, less stealthy) |
| `--pretty` | Pretty-print JSON output |
| `-o FILE` | Save output to file |
| `--proxy URL` | Use HTTP proxy |

## Engines

| Engine | ID | Reliability | Notes |
|--------|-----|------------|-------|
| 百度 | `baidu` | ★★★★★ | Most reliable for Chinese content. CSS selectors cover old+new layouts. |
| 必应 | `bing` | ★☆☆ | **Broken from CN IPs without proxy.** Redirects to cn.bing.com, returns Chinese brand spam for English queries. Skip unless you have `--proxy`. |
| 搜狗 | `sogou` | ★★★☆ | Tencent-backed. Good alternative to Baidu. |
| 360搜索 | `so360` | ★★★☆ | Decent alternative. |

## Output Format

```json
{
  "query": "搜索词",
  "engines": ["baidu"],
  "total_pages": 1,
  "timestamp": "2026-05-19T10:30:00",
  "data": {
    "baidu": {
      "total_results": 10,
      "results": [
        {"title": "...", "url": "https://...", "snippet": "...", "rank": 1}
      ],
      "error": null
    }
  }
}
```

## Anti-Detection Features

The tool includes 8 anti-crawling strategies:
1. 11 User-Agent strings randomly rotated (macOS/Windows Chrome, Safari, Firefox, Edge)
2. Browser fingerprint spoofing (hides `navigator.webdriver`, fakes plugins/languages/hardwareConcurrency)
3. Random operation delays (0.5~5s, can be disabled with `--no-random`)
4. Human-like scrolling + mouse movement simulation
5. Randomized engine search order
6. Random browser type (Chromium / Firefox)
7. Homepage warmup before target search
8. CAPTCHA auto-detection and graceful abort

## Performance

- Per search: 3-8 seconds (results found), 12-15 seconds (no results / special page)
- Batch of 100: ~15 minutes
- No rate limiting — each search launches a fresh browser instance
- Batch test script at `/Users/you/universal-search/batch_test.py` (99% reliability over 100 searches)

## When to Use

Use this tool when:
- You need to search Chinese web content and the Baidu AI Search API is rate-limited or unavailable
- You need multi-engine results (Baidu + Sogou + So360 simultaneously)
- You need real browser-rendered SERP results (can capture SPA-rendered content)

Do NOT use when:
- The Baidu AI Search API (`baidu-ai-search` skill) works — it's faster and more reliable
- You need academic papers — use `arxiv` skill
- You just need a single web page — use `browser_navigate`

## Kaggle / Competition Code Research Workflow

When searching for Kaggle competition solutions and their GitHub code:

1. **Search GitHub API directly** — bypasses web-search engine issues for English repos:
   ```bash
   curl -s "https://api.github.com/search/repositories?q=kaggle+<competition-keywords>&sort=stars&order=desc&per_page=10" | python3 -c "import json,sys; ..."
   ```
2. **Clone the top 5-8 repos** in parallel to a local reference directory.
3. **Inspect README + key source files** to extract feature engineering patterns and model architecture.
4. **Compile findings into an HTML report** (light theme, comparison tables, technique breakdowns).
5. **Open report** with `open report.html`.

## Research Workflow

For research tasks (e.g., "what's new in ML this week"):

1. **Search multiple engines** for topic keywords (Chinese + English) — run searches in parallel
2. **Search arXiv** for recent academic papers on the topic
3. **PRESENT PARTIAL RESULTS AFTER 2-3 ROUNDS of searches.** Do NOT keep searching silently.
4. **Compile findings** into an HTML report (light theme, Noto Sans SC font, clean layout)
5. **Open with `open file.html`** to display in browser

## Finding Chinese Academic PDFs

When searching for Chinese academic books/papers and web scraping returns 0 results (copyright filters on doc88/book118/docin/taodocs), use the two-step workflow:

1. **Baidu AI Search API** to find source URLs (bypasses content filters)
2. **GitHub search** to find mirrored PDFs (repos are rarely purged)

See `references/chinese-pdf-hunt.md` for the full guide with known repositories and anti-patterns.
