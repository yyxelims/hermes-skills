# AI HOT HTML 日报生成器 — 可复用 Python 模板

将以下代码保存为 `.py` 或直接在 `execute_code` 中运行。修改 `DAILY_DIR` 为实际路径。

```python
from hermes_tools import terminal, write_file
from datetime import datetime, timezone, timedelta
import json

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/YOUR_SERVER_IP Safari/537.36"
BEIJING_TZ = timezone(timedelta(hours=8))
DAILY_DIR = "/Users/you/Documents/本地/ai探索/AI日报"

# 拉取日报（v1：响应包在 report 里）
result = terminal(f'curl -sSL --compressed -H "User-Agent: {UA}" "https://aihot.news/api/v1/dailies/latest"', timeout=15)
daily = json.loads(result["output"]).get("report") or {}
date_str = daily["date"]
now_bj = datetime.now(BEIJING_TZ)

# 时间转换: UTC ISO → 北京时间相对时间
def utc_to_relative(iso_str):
    if not iso_str: return ""
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    bj = dt.astimezone(BEIJING_TZ)
    diff = datetime.now(BEIJING_TZ) - bj
    if diff.days == 0:
        h = diff.seconds // 3600
        return f"{h} 小时前" if h > 0 else f"{diff.seconds // 60} 分钟前"
    elif diff.days == 1:
        return f"昨天 {bj.strftime('%H:%M')}"
    return bj.strftime("%m/%d %H:%M")

# 智能截断：按句号/分号/感叹号断句，保留完整句子
def smart_truncate(text, soft_limit=150):
    if not text or len(text) <= soft_limit:
        return text
    # 找到最后一个句子分隔符（。！？；）在 soft_limit 附近
    candidates = []
    for sep in ["。", "！", "？", "；"]:
        idx = text.rfind(sep, 0, soft_limit + 60)
        if idx >= soft_limit - 40:
            candidates.append(idx)
    if candidates:
        cut = max(candidates) + 1  # 保留分隔符
        return text[:cut] + "…"
    # 回退：硬截断但在逗号处断
    comma = text.rfind("，", 0, soft_limit)
    if comma >= soft_limit - 40:
        return text[:comma] + "…"
    # 最终回退
    return text[:soft_limit] + "…"

# Category → 标签映射
cat_map = {
    "模型发布/更新": ("cat-model", "模型"),
    "产品发布/更新": ("cat-product", "产品"),
    "行业动态": ("cat-industry", "行业"),
    "论文研究": ("cat-paper", "论文"),
    "技巧与观点": ("cat-tip", "观点"),
}

# 构建 sections（全局编号）
num = 1
sections_html = ""
for sec in daily.get("sections", []):
    if not sec.get("items"): continue
    css, tag = cat_map.get(sec["label"], ("cat-model", "模型"))
    sections_html += f'\n    <div class="section">\n      <div class="section-title">{sec["label"]} · {len(sec["items"])} 条</div>'
    for item in sec["items"]:
        title = item.get("title", "")
        url = (item.get("links") or {}).get("original") or (item.get("links") or {}).get("aihot") or "#"
        source = (item.get("source") or {}).get("name") or ""
        # 智能截断：按句号/分号断句，保留完整句子，软上限约 150 字
        full = item.get("summary") or ""
        summary = smart_truncate(full, soft_limit=150)
        sections_html += f'''
      <div class="item">
        <div class="item-header">
          <span class="item-num">{num}</span>
          <span class="item-title"><a href="{url}" target="_blank">{title}</a></span>
          <span class="category-tag {css}">{tag}</span>
        </div>
        <div class="item-meta"><span class="source">{source}</span></div>
        <div class="item-summary">{summary}</div>
      </div>'''
        num += 1
    sections_html += '\n    </div>'

# Lead + Flashes（略，见完整模板）

total = num - 1
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<!-- [完整 HTML 模板见 SKILL.md 的 "给用户的输出格式" 节] -->
...
<div class="header">...</div>
{sections_html}
...
<div class="footer">数据来源：AIHOT (aihot.news) · 文件：{DAILY_DIR}/AI日报_{date_str}.html</div>
</html>'''

# 写入
import os; os.makedirs(DAILY_DIR, exist_ok=True)
write_file(f"{DAILY_DIR}/AI日报_{date_str}.html", html)
print(f"OK: AI日报_{date_str}.html ({total} 条)")
```

## 关键注意

- **UA 必带**：否则 403。已内置在模板中。
- **时间转相对**：`utc_to_relative()` 处理 ISO 8601 UTC → "X 小时前" / "昨天 HH:MM"
- **全局编号**：num 在 section 间递增，不重置
- **空 section 跳过**：`if not sec.get("items"): continue`
- **HTML 模板**：完整 CSS 在 SKILL.md 的"给用户的输出格式"中，复制时注意缩进。CSS 已含两级响应式断点（768px 平板+手机、400px 小屏手机），无需额外处理。

## 独立脚本

`~/quant-lab/ai_daily.py` — 纯 Python 标准库（urllib），零 pip 依赖，可直接 cron 调用。支持 `python3 ai_daily.py [YYYY-MM-DD] [--open]`。

## 独立脚本

完整独立脚本（零依赖，纯标准库）：`~/quant-lab/ai_daily.py`

```bash
python3 ~/quant-lab/ai_daily.py              # 最新日报
python3 ~/quant-lab/ai_daily.py 2026-07-14   # 指定日期
python3 ~/quant-lab/ai_daily.py --open       # 生成后自动打开浏览器
```

该脚本可直接用于 cron 定时任务，不依赖 Hermes Agent。
