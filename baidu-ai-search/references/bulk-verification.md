# Bulk Verification Workflow with Baidu AI Search

## Use Case

Verify structured data (spreadsheet rows) against real-world web data. Typical scenarios:
- Audit a list of venues for digital presence (WeChat, mini-programs, payment systems)
- Validate claimed business capabilities against actual web evidence
- Cross-check government/corporate announcements against third-party sources

## Complete Example: Cultural Tourism Venue Audit

This pattern was used to verify 34 cultural tourism scenarios in a spreadsheet.

### Step 1: Load Data and Define Verification Queries

```python
import sys
sys.path.insert(0, '/Users/you/quant-lab')
from baidu_search import search
import pandas as pd

# Load spreadsheet
df = pd.read_excel('/path/to/your/data.xlsx', sheet_name=0)

# Define what keywords to search for each verification dimension
VERIFY_DIMENSIONS = {
    'has_official_account': ['公众号', '微信公众', '官方公众号'],
    'has_miniprogram': ['小程序', '微信小程序'],
    'has_payment': ['购票', '预订', '支付', '预约', '门票'],
}

# Map scenario name to search queries - customize per domain
def build_queries(scenario_name, operator=''):
    """Build 2-3 targeted search queries per scenario"""
    queries = []
    queries.append(f"{scenario_name} 公众号 小程序")
    queries.append(f"{scenario_name} 购票 预订")
    if operator:
        queries.append(f"{operator} {scenario_name}")
    return queries[:3]  # cap at 3 queries per scenario
```

### Step 2: Batch Search and Extract Signals

```python
results = {}
BATCH_SIZE = 10  # Pause between batches to avoid rate limits

for idx, row in df.iterrows():
    name = row['单位名称']  # adjust column name to match your data
    operator = row.get('运营（谋划）单位', '')
    
    print(f"[{idx+1}/{len(df)}] Verifying: {name[:40]}")
    
    queries = build_queries(name, operator)
    all_refs = []
    
    for q in queries:
        result = search(q, timeout=30)
        refs = result.get('references', [])
        all_refs.extend(refs)
    
    # Build search corpus from all reference titles + content
    text_dump = ' '.join([
        r.get('content', '') + r.get('title', '') 
        for r in all_refs
    ])
    
    # Signal detection: keyword matching
    # Note: Do NOT rely on AI summary - it's often empty
    results[name] = {
        'official_account': any(kw in text_dump for kw in VERIFY_DIMENSIONS['has_official_account']),
        'miniprogram': any(kw in text_dump for kw in VERIFY_DIMENSIONS['has_miniprogram']),
        'payment': any(kw in text_dump for kw in VERIFY_DIMENSIONS['has_payment']),
        'top_sources': [r.get('title', '')[:50] for r in all_refs[:2]],
        'query_count': len(queries),
    }
    
    # Optional: rate limiting
    if (idx + 1) % BATCH_SIZE == 0:
        print(f"Completed {idx+1}. Pausing...")
        # time.sleep(2)  # uncomment if needed

print(f"\n✓ Verified {len(results)} scenarios")
```

### Step 3: Compare Against Original Annotations

```python
comparison = []

for idx, row in df.iterrows():
    name = row['单位名称']
    verified = results.get(name, {})
    
    # Original annotations (customize column names to match)
    orig_mp = row.get('微信公众号', '')
    orig_xcx = row.get('微信小程序', '')
    orig_pay = row.get('涉及支付', '')
    
    # Convert to boolean for comparison
    orig_has_mp = orig_mp not in ['—', ''] and pd.notna(orig_mp)
    orig_has_xcx = orig_xcx not in ['—', ''] and pd.notna(orig_xcx)
    orig_has_pay = orig_pay == '是'
    
    search_has_mp = verified.get('official_account')
    search_has_xcx = verified.get('miniprogram')
    search_has_pay = verified.get('payment')
    
    def match_status(search_val, orig_val):
        if search_val is None:
            return '未验证'
        return '✓ 匹配' if search_val == orig_val else '✗ 不匹配'
    
    comparison.append({
        '序号': idx + 1,
        '场景名称': name,
        '建设情况': row.get('建设情况', ''),
        '原标注_公众号': orig_mp,
        '原标注_小程序': orig_xcx,
        '原标注_支付': orig_pay,
        '搜索_公众号': '有' if search_has_mp else ('无' if search_has_mp == False else '未验证'),
        '搜索_小程序': '有' if search_has_xcx else ('无' if search_has_xcx == False else '未验证'),
        '搜索_支付': '有' if search_has_pay else ('无' if search_has_pay == False else '未验证'),
        '公众号匹配': match_status(search_has_mp, orig_has_mp),
        '小程序匹配': match_status(search_has_xcx, orig_has_xcx),
        '支付匹配': match_status(search_has_pay, orig_has_pay),
        '来源1': verified.get('top_sources', [''])[0],
        '来源2': verified.get('top_sources', ['', ''])[1],
    })

df_comp = pd.DataFrame(comparison)
```

### Step 4: Generate Report and Save Output

```python
# Statistics
verified_count = len(results)
matched_mp = sum(1 for c in comparison if c['公众号匹配'] == '✓ 匹配')
matched_xcx = sum(1 for c in comparison if c['小程序匹配'] == '✓ 匹配')
matched_pay = sum(1 for c in comparison if c['支付匹配'] == '✓ 匹配')
mismatch_mp = sum(1 for c in comparison if c['公众号匹配'] == '✗ 不匹配')
mismatch_xcx = sum(1 for c in comparison if c['小程序匹配'] == '✗ 不匹配')
mismatch_pay = sum(1 for c in comparison if c['支付匹配'] == '✗ 不匹配')

print("=== Verification Summary ===")
print(f"Total scenarios: {len(df)}")
print(f"Verified: {verified_count}")
print(f"Official Account: {matched_mp} matched, {mismatch_mp} mismatched")
print(f"Mini Program: {matched_xcx} matched, {mismatch_xcx} mismatched")
print(f"Payment: {matched_pay} matched, {mismatch_pay} mismatched")

# Print mismatches for immediate review
print("\n=== Mismatch Details ===")
for c in comparison:
    if '不匹配' in [c['公众号匹配'], c['小程序匹配'], c['支付匹配']]:
        print(f"\n{c['序号']}. {c['场景名称'][:35]}")
        if c['公众号匹配'] == '✗ 不匹配':
            print(f"   Official Account: original={c['原标注_公众号']} vs search={c['搜索_公众号']}")
        if c['小程序匹配'] == '✗ 不匹配':
            print(f"   Mini Program: original={c['原标注_小程序']} vs search={c['搜索_小程序']}")
        if c['支付匹配'] == '✗ 不匹配':
            print(f"   Payment: original={c['原标注_支付']} vs search={c['搜索_支付']}")

# Save full comparison report
output_path = '/path/to/output/verification_report.xlsx'
df_comp.to_excel(output_path, index=False)
print(f"\n✓ Full report saved to: {output_path}")
```

## Key Insights and Pitfalls Learned

1. **Intent vs Reality Gap**: "意向谋划" (planning stage) scenarios are often annotated with future plans, but search shows no actual digital presence yet. Always flag this category separately.

2. **AI Summary is Unreliable**: The `summary` field from Baidu AI Search is frequently null/empty. Always analyze `references` directly by concatenating titles and content, then search for keywords.

3. **Query Optimization**: 2-3 queries per scenario is the sweet spot. More queries = more sources = higher signal-to-noise ratio but consumes quota faster.

4. **Quota Management**: 
   - 34 scenarios × 3 queries = 102 queries (at or near daily limit)
   - Plan accordingly: split large audits across multiple days or prioritize by confidence level

5. **False Negative Rate**: Search doesn't guarantee finding everything. A "not found" result means:
   - The thing truly doesn't exist
   - OR it exists but isn't indexed/visible to search engines
   - OR your keywords weren't specific enough

6. **False Positive Mitigation**: Verify top sources manually if the stakes are high. Cross-reference multiple sources for the same signal.

## Typical Output Pattern for Venue Audits

From the 34-scenario cultural tourism audit:
- **High match rate** for "已建成" (already built) venues: ~85% match between annotations and search
- **Low match rate** for "意向谋划" (planning stage) venues: ~30% match — most annotations represent future plans, not current state
- **Common mismatches**: Official account exists but no mini-program (marked as both in original data), payment system planned but not implemented
