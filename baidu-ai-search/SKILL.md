---
name: baidu-ai-search
description: >
  Real-time Chinese web search using Baidu AI Search API (百度千帆 AI 搜索).
  Use this whenever the user asks to search for current information, latest news,
  recent developments, or real-time data in Chinese. Triggers on: "搜索一下",
  "查一下最新", "最近有什么新闻", "联网搜索", "实时信息".
  每日免费额度 100 次。Deep search 模式更全面但更慢。
tags: [search, web, chinese, realtime, baidu, qianfan]
related_skills: [web-search]
---

# Baidu AI Search

Real-time Chinese web search via Baidu Qianfan AI Search API.

## API Details

- **Endpoint**: `POST https://qianfan.baidubce.com/v2/ai_search/chat/completions`
- **Auth**: `Authorization: Bearer {API_KEY}`
- **API Key**: stored in memory (`bce-v3/ALTAK-...`)
- **Free quota**: 100 requests/day
- **Hard limit**: 80 requests/day (leaves 20 buffer to avoid overage charges)
- **Counter file**: `~/.hermes/baidu_search_counter.txt` (auto-managed)
- **Deep search**: Set `enable_deep_search: true` for more comprehensive results (slower, ~60s). Default to `false` for quick lookups.

## Usage

### From Python
```python
from baidu_search import search, search_and_format

# Quick search (non-deep, ~10s)
result = search("BEST托卡马克 2026 进展")
print(result["summary"])            # AI-generated summary
for ref in result["references"]:    # Source links with dates
    print(f"[{ref['date']}] {ref['title']}\n  {ref['url']}")

# Deep search (more comprehensive, ~60s)
result = search("核聚变 最新进展", deep=True)

# One-liner with formatted output
print(search_and_format("关键词"))
```

### CLI
```bash
python3 /Users/you/quant-lab/baidu_search.py "搜索关键词"
python3 /Users/you/quant-lab/baidu_search.py "搜索关键词" --deep
```

## Response Format

```json
{
  "references": [
    {
      "title": "新闻标题",
      "url": "https://...",
      "date": "2026-05-18 15:30:17",
      "content": "内容摘要..."
    }
  ],
  "summary": "AI 生成的总结文本"
}
```

## 备用搜索：本地 360 搜索

当百度 AI Search 没有找到足够结果或需要发现中文官网页面时，可使用本地搜索包中的 360 搜索脚本：

```bash
python3 /tmp/local-web-search/local-web-search/scripts/search_360.py "关键词" --count 10 --resolve
```

已实测：360 可发现北京金融管理局领导“分管处室”等官方页面。

使用规则：

1. 百度 AI Search 仍是主力；360 只作补充发现页面。
2. 必须使用 `--resolve` 获取真实 URL。
3. 360 结果没有可靠日期和正文摘要，不能直接作为事实证据。
4. 找到结果后必须打开原始官网页面，提取完整正文并核验。
5. 搜狗脚本可能触发验证码，Bing 中文查询经常无结果，不作为主力。

领导分管业务搜索顺序：

```text
百度 AI Search
→ 360 搜索备用
→ 筛选官方域名
→ 打开官网正文
→ 判断是否明确出现“分管/负责/主管/联系”
→ 保存证据
```

**Use Baidu AI Search (this skill) when:**
- Searching for Chinese downloadable resources (PDFs, books, documents) — web scraping returns 0 results for copyright-filtered queries
- Need structured, dated, sourced results from the Chinese web
- Searching for Chinese news, real-time information, or recent developments
- The search query contains terms like "下载", "PDF", "免费" that trigger anti-scraping blocks
- **Searching for technical details of brand-new AI model releases (< 1 week old)** — Chinese tech media (钛媒体, IT之家, DoNews) often publish detailed technical breakdowns before arXiv papers or official English blogs appear. See `devops/html-report-generation` skill's `references/new-model-research.md` for full research workflow.

**Web scraping (universal_search.py) still works for:**
- General keyword searches that don't trigger copyright filters
- High-volume batch searches (99% reliability verified on 100-query test)

## Complementary Download Sources

When Baidu AI Search returns resource names but the links point to paywalled sites (book118, docin, renrendoc, taodocs — all require VIP/gold coins), pivot to these free sources for the actual download:

| Source | What | How |
|--------|------|-----|
| **GitHub** | Public domain / CC classical texts | `curl -s 'https://api.github.com/search/repositories?q=<keyword>+pdf'` — find repos with PDF releases |
| **Internet Archive** | Annotated/translated Chinese classics | `curl -s 'https://archive.org/advancedsearch.php?q=title:(<keyword>)+AND+mediatype:(texts)&fl[]=identifier,title&rows=10&output=json'` → `curl -s 'https://archive.org/metadata/<identifier>'` → download from `https://archive.org/download/<identifier>/<filename>` |

Pattern: Baidu search → identify the resource name → GitHub / Internet Archive → free direct download.

See `references/chinese-ebook-sources.md` for detailed examples and API patterns.

## Bulk Verification Pattern

Use this when you need to verify multiple rows from a spreadsheet against real-world web data (e.g., verifying 34 cultural tourism scenarios for WeChat official accounts, mini-programs, and payment capabilities).

```python
import sys
sys.path.insert(0, '/Users/you/quant-lab')
from baidu_search import search
import pandas as pd

df = pd.read_excel('data.xlsx')
verified = {}

for idx, row in df.iterrows():
    name = row['场景名称']
    queries = [f"{name} 公众号", f"{name} 小程序", f"{name} 支付"]
    
    all_refs = []
    for q in queries:
        result = search(q)
        all_refs.extend(result.get('references', []))
    
    text_dump = ' '.join([r.get('content', '') + r.get('title', '') for r in all_refs])
    verified[name] = {
        'has_official_account': '公众号' in text_dump or '微信公众' in text_dump,
        'has_miniprogram': '小程序' in text_dump,
        'has_payment': '购票' in text_dump or '预订' in text_dump or '支付' in text_dump,
        'sources': [r.get('title', '') for r in all_refs[:2]]
    }

# Generate comparison report
```

See `references/bulk-verification.md` for a complete worked example including mismatch detection and report generation.

## Pitfalls

1. **Daily limit is real**: The free tier is 100 requests/day. The script hard-caps at 80. If you hit the limit, you'll get an error message — do NOT bypass the counter.
2. **Deep search is slow**: Non-deep returns in ~10s, deep takes ~60s. Use deep only when the user explicitly needs comprehensive results.
3. **Timeout**: Set `timeout=120` for deep searches. The API occasionally takes longer than 30s.
4. **Function name is `search` NOT `baidu_ai_search`**: Common import error. The correct import is `from baidu_search import search, search_and_format`.
5. **This replaces web scraping for Chinese resources**: Baidu AI Search finds results that web scraping misses entirely due to copyright/content filters on Chinese search engines.
6. **Baidu results → paywall is normal**: Most Baidu search results for Chinese PDFs land on book118/docin/renrendoc/taodocs — all paywalled. Use the result titles as leads, then switch to GitHub + Internet Archive for actual free downloads (see Complementary Download Sources above).
7. **Summary field occasionally empty**: The API returns `references` reliably even when `summary` is null/empty. Always fall back to analyzing references directly. During bulk verification, concatenate all reference content/title and search for keywords rather than relying on the AI summary.
8. **Baidu Baike blocks direct scraping (403)**: `baike.baidu.com` pages return HTTP 403 when fetched with `urllib.request` or `curl` — consistently. Do NOT waste time retrying. Instead, rely on the Baidu AI Search API's `content` field in each reference, which already includes Baike summary text. When you need specific details like address or street info, use more targeted Baidu AI Search queries rather than scraping Baike directly.
9. **VisitBeijing (visitbeijing.com.cn) works for scraping**: Unlike Baike, VisitBeijing article pages return clean HTML with full text content extractable via `<p>` tag parsing. When searching for Beijing tourism entity lists (景区, 博物馆, etc.), prioritize VisitBeijing URLs from references for direct scraping — they contain authoritative, well-structured lists with addresses.

## Entity Discovery & Compilation Pattern

Use this when the user needs a comprehensive list of ALL entities of a specific category in a geographic area (e.g., "all scenic spots in Fengtai District", "all theaters in Xicheng"). See `references/entity-discovery-compilation.md` for the detailed workflow.

## Script Location

`/Users/you/quant-lab/baidu_search.py`
The script auto-manages the daily counter, enforces the hard limit, and displays remaining quota.
