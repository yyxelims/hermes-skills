# Entity Discovery & Compilation Workflow

Proven pattern for building comprehensive, structured lists of all entities of a category within a geographic area (e.g., "all scenic spots in Fengtai", "all theaters in Xicheng").

## Step 1: Broad Discovery (2-3 queries)

Run parallel broad searches to surface overview articles and authoritative list pages:

```python
queries = [
    "北京{区名} {类别} 大全 列表 A级",
    "{区名} {类别} 必去 十大 攻略",
    "{区名} {类别} 完整名单 2024 2025",
]
for q in queries:
    result = search(q)
```

Key signals in results:
- **VisitBeijing (visitbeijing.com.cn)**: Gold standard — authoritative, well-structured, scrape directly
- **Government sites (bjft.gov.cn, beijing.gov.cn)**: Official A-level ratings, but often 403 or JS-rendered
- **Baidu Baike**: Summary text available via API's `content` field (DO NOT scrape directly — 403)
- **Ctrip/travel blogs**: Supplementary, less authoritative

## Step 2: Scrape the Best Source

Target VisitBeijing first — it returns clean HTML with entity names, addresses, and descriptions:

```python
import urllib.request, re
req = urllib.request.Request(visitbeijing_url, headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
})
html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore')
# Remove scripts/styles, extract <p> text
text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', text)
```

## Step 3: Fill Gaps with Targeted Searches

After extracting the main list, identify info gaps (addresses, street assignments, ratings) and run targeted searches:

```python
# Per-entity detail search
search("{entity_name} 某城区 地址 所属街道 级别")
```

The API's `content` field usually contains Baike summary with addresses.

## Step 4: Compile to Structured Excel

Use `pd.ExcelWriter` with `mode='a'` and `if_sheet_exists='replace'` to add as a new sheet:

```python
df = pd.DataFrame(entities)
with pd.ExcelWriter(path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df.to_excel(writer, sheet_name='SheetN_类别名', index=False)
```

## Anti-Patterns to Avoid

- **Do NOT scrape baike.baidu.com directly**: Consistently returns 403. Use API `content` field.
- **Do NOT keep searching silently**: After 2-3 rounds, compile what you have and present results. The user says "你在干嘛" when searches drag on.
- **Do NOT visit every reference URL**: Pick the 1-2 best-looking overview pages and scrape those alone.
- **Government sites are often JS-rendered**: `bjft.gov.cn` etc. may return 403 or only load content via JS. Skip and use VisitBeijing + API references.

## Example Session (Fengtai Scenic Spots)

1. **Broad search** (3 queries): Found VisitBeijing "某城区十大景点" article + government AAA rating notice
2. **Scrape VisitBeijing**: Extracted 10 entities with names, addresses, descriptions
3. **Targeted searches** (6 queries): Filled street-level info for 青龙湖, 莲花池, 绿堤, 露营公园, 某城区花园, 紫谷伊甸园
4. **Gap fill** (1 query): Found 2A-rated parks (万芳亭, 石榴庄)
5. **Compile**: 21 entities written to Sheet3_景区

Total: ~12 API calls, ~2 minutes wall time. Result: complete structured list with name, A-level, street, address, supervisor, ownership, opening status, notes.
