# WeChat Ecosystem Search Methodology

How to check if a Chinese organization/venue/scenic-spot has WeChat official accounts (公众号),
mini-programs (小程序), or H5 pages.

## Five Methods (ranked by practicality)

### 1. WeChat In-App "搜一搜" — Most Authoritative
- Open WeChat → top search bar → type the name
- Results auto-categorized: 公众号 / 小程序 / 文章 / 视频号
- Shows account verification status, recent posts, mini-program features
- **Pro**: Direct from WeChat backend, most authoritative
- **Con**: Manual only, one-by-one. No batch capability.

### 2. Sogou WeChat Search (weixin.sogou.com) — PC Batch, Programmatically Verified 2026-09-09
- URL: `https://weixin.sogou.com/weixin?type=2&query=<URL编码>` (type=1 公众号 / type=2 文章)
- Shows: avatar, name, WeChat ID, description, recent articles
- **Pro**: PC-friendly, batch-checkable, server-rendered HTML (no JS rendering needed). Only public portal for searching 公众号文章全文 from outside WeChat.
- **Con**: Cannot search mini-programs (mini-programs only searchable within WeChat app)
- **Con**: Anti-spider threshold exists (rate/cookie-based, not IP-based — worked from US egress IPLOC=US)

**Verified programmatic recipe** (full chain tested 2026-09-09, script: `/Users/you/quant-lab/sogou_link_follow.py`):
1. **Cookie chain is mandatory**: GET homepage first (sets SUID/ABTEST) → first search response sets **SNUID**. Without SNUID, `/link` redirects to `antispider/` page. Reuse one cookie jar throughout (`curl -b jar -c jar`).
2. Result page: parse `href="/link?url=..."` entries (token is time-limited — always re-extract from a fresh result page).
3. **`/link` is NOT a 302**: it returns a small HTML with JS fragments `url += '...';`. Concatenate all fragments, strip `@` chars → real `mp.weixin.qq.com/s?...` article URL. (WebFetch-style redirect-following will land on antispider or garbage — must do this manually.)
4. GET the assembled article URL with Referer `https://weixin.sogou.com/` → full server-rendered article HTML (3MB+). Extract `gh_[A-Za-z0-9_]{6,}` (account ID) and `nickname` via regex.
5. Pacing: `sleep(2)` between requests. If antispider triggers: back off, rebuild cookie chain from step 1; don't hammer.
6. Required headers: browser `User-Agent` + `Referer: https://weixin.sogou.com/...` on /link and article requests.
7. **Time filtering (verified 2026-09-09)**: server-side params are ALL dead anonymously — `tsn=3` returns an empty shell page, `ft`/`et` timestamps are silently ignored (result still relevance-sorted with decade-old articles first). Filter client-side instead: each result block (`class="txt-box"`) embeds `timeConvert('<unix-ts>')`; keep only entries with ts >= now − N days. Caveat: some old articles show *re-index* time, not publish time — article page date is the ground truth.
8. **Multi-word queries break `/link`**: the echoed `/link?url=...&k=信用卡 监管` path contains raw CJK + spaces → curl exit=3 (URL malformed). Percent-encode every char that is non-ASCII/space/quote before requesting: `''.join(c if (ord(c)<128 and c not in ' "') else quote(c) for c in u)`.
9. **Article extraction — strip `<script>` before div-depth scan**: the article page's JS strings embed HTML fragments (`</div>` etc.) that pre-collapse naive depth counting (symptom: only ~8 chars of boilerplate extracted like "预览时标签不可点"). Do `re.sub(r'<script[\s\S]*?</script>', ' ', seg)` first, then depth-scan from `<div id="js_content">`. Real effect: 8 chars → 5,259 chars on a KPMG article.
10. **Deregistered accounts**: relevance-sorted old hits are mostly dead accounts — article page returns a real 31KB error page "此账号已自主注销，内容无法查看" (title meta may even be present). Detect by body length (<80 chars) or that marker; the time filter from step 7 avoids most of them.

Production integration (policy-tracker, 2026-09-09): `脚本/scrape_sogou_wechat.py` — 8 keywords × top-5 × 30-day window → full body + gh_/nickname → DeepSeek summary (`_llm.json`) → merged into Excel Sheet2. First run: 7 articles captured, 7/7 summaries OK.

**Complement**: once you have `gh_` account ID, TikHub API (`/api/v1/wechat_mp/v2/fetch_account_profile|fetch_account_articles`, key in `~/.hermes/.env`) gives structured profile + article lists without further scraping (verified 2026-09-03).

### 3. WeChat Official Platform (mp.weixin.qq.com) — Verify Authenticity
- Login → Tools → Account info query
- Or: In WeChat app, enter account profile → check "认证主体" (verified entity)
- **Pro**: Confirms whether an account is the official one (shows company legal name)
- **Con**: Requires WeChat Official Platform account

### 4. Third-Party Data Platforms — Advanced Filtering
- **新榜 (newrank.cn)** — account rankings + search, filter by industry/region
- **西瓜数据 (data.xiguaji.com)** — account analytics
- **Pro**: Industry/region filtering, batch discovery
- **Con**: Most features require paid membership

### 5. Baidu Search + Site Filtering — Batch Scriptable (Recommended)
- Search: `景区名 微信公众号` or `景区名 小程序`
- WeChat articles indexed by Baidu at `mp.weixin.qq.com` — extract account names from article URLs
- Baidu Baike entries often list official accounts and mini-program QR codes
- Use Baidu AI Search API for batch automation (see baidu-ai-search skill)
- **Pro**: Free, broad coverage, scriptable via API
- **Con**: Not WeChat-official data; may be incomplete or outdated; requires cross-validation

## Batch Search Pattern with Baidu AI Search

```python
from hermes_tools import terminal

searches = [
    ("label1", "景区名1 微信公众号 小程序"),
    ("label2", "景区名2 微信公众号 小程序"),
]

for label, query in searches:
    result = terminal(
        f'python3 /Users/you/quant-lab/baidu_search.py "{query}" 2>&1 | head -50',
        timeout=30
    )
    # Parse mp.weixin.qq.com URLs to extract account names
    # Look for patterns like: "公众号: XXX", "小程序: XXX"
```

## Key WeChat URL Patterns

- Official account article: `https://mp.weixin.qq.com/s?__biz=Mz...==&mid=...`
  - `__biz` parameter uniquely identifies the account
- Official account profile: `https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=...`
- Mini-program: Cannot be linked directly from web — must search in WeChat app

## Common Anti-Patterns

- **Sogou WeChat CAN be scraped programmatically** (verified 2026-09-09) — but only with the full cookie chain (SUID→SNUID) and the `/link` JS-fragment assembly. Naive single-shot curl will hit antispider. See §2 recipe. Don't confuse noisy general Sogou web search with weixin.sogou.com structured results.
- **Do NOT assume every venue has a dedicated account** — many smaller venues are only covered by umbrella accounts (e.g., district government accounts like "北京某城区", "文旅某城区")
- **Government-run venues** often outsource their digital presence to district-level platforms rather than maintaining their own accounts
