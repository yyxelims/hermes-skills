# Multi-Day Combined AI Daily Report Generator

When the user asks for "上次更新以后的新AI日报" or a date range of dailies, use this pattern.

## Workflow

1. **Check existing reports**: list `~/Documents/本地/ai探索/AI日报/` to find the latest date covered
2. **List available dailies**: `curl -sH "User-Agent: $UA" "https://aihot.news/api/v1/dailies?limit=30"`
3. **Determine date gap**: find which dates are missing (after the last existing report)
4. **Fetch each daily**: `curl /api/v1/dailies/{YYYY-MM-DD}`，取响应里的 `report`
5. **Check today**: 若当天日报未生成（北京时间 08:00 前），退回 `https://aihot.news/api/v1/agent/latest` 取滚动 24 小时内容
6. **Merge by category**: collect all items across dates, group by `section.label`, within each category sort by date descending
7. **Generate single HTML**: use the standard HTML template, but add `day-label` span showing date per item. Title format: "AI HOT 日报 · YYYY-MM-DD 至 YYYY-MM-DD"

## Key Code Pattern

```python
from hermes_tools import terminal, write_file
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import json, os

UA = "Mozilla/5.0 ... Chrome/YOUR_SERVER_IP Safari/537.36"  # browser UA required
BEIJING_TZ = timezone(timedelta(hours=8))
DAILY_DIR = os.path.expanduser("~/Documents/本地/ai探索/AI日报")

# Fetch all dailies for missing dates
merged = defaultdict(list)
for date in missing_dates:
    result = terminal(f'curl -sH "User-Agent: {UA}" "https://aihot.news/api/v1/dailies/{date}"', timeout=15)
    daily = json.loads(result['output']).get('report') or {}
    for sec in daily.get('sections', []):
        for item in sec.get('items', []):
            item['_date'] = date
            item['_section'] = sec['label']
            merged[sec['label']].append(item)

# Today fallback: 当天日报未生成时，用 agent/latest 的滚动 24 小时内容
result = terminal(f'curl -sSL --compressed -A "aihot-skill/2.0.0 (+https://aihot.news/aihot-skill/)" "https://aihot.news/api/v1/agent/latest"', timeout=15)
today_md = result['output']
# Map category slugs to Chinese labels
cat_label = {
    'ai-models': '模型发布/更新', 'ai-products': '产品发布/更新',
    'industry': '行业动态', 'paper': '论文研究', 'tip': '技巧与观点',
}
# Convert to daily-section format and merge
```

## Naming Convention
- `AI日报_YYYY-MM-DD_单日.html` for single day
- `AI日报_YYYY-MM-DD至MM-DD_合辑.html` for date ranges (e.g., `AI日报_2026-06-25-29_合辑.html`)

## Pitfall
- Daily generation runs at ~08:00 Beijing time. If today's daily returns 404, fall back to `items?mode=selected`.
- Always clean up old intermediate files (e.g., the 6/25-28 version when 6/25-29 supersedes it).
- Add a small note in the header if today's data comes from the items pool rather than the daily (explains fewer items).
