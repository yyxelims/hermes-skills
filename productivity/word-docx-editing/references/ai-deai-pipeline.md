# AIGC De-AI-ification Pipeline

Complete workflow for detecting and removing AI-generation markers from
Chinese documents while preserving all formatting.

## Step 1: Baseline Detection

```bash
python3 scripts/ai_detect.py original.docx
```

Records the baseline AI probability score and per-dimension breakdown.

## Step 2: Rewrite Text

Rewrite with these strategies (in priority order):

### Strategy A: Replace AI Buzzwords

| Original | Replacement (vary these) |
|----------|--------------------------|
| 依托 | 利用 / 基于 / 通过 / 借助 |
| 适配 | 适用 / 匹配 / 适合 |
| 全流程 | 端到端 / 贯穿始终 / 整体 / 从…到… |
| 引擎 | 模块 / 组件 (keep only where it's a proper product name) |
| 助力 | 帮助 / 支持 / 推动 |
| 赋能 | 删除或改为"提升能力" |
| 深耕 | 扎根 / 专注 / 在…领域持续投入 |
| 夯实 | 巩固 / 加强 |
| 盘活 | 激活 / 重新利用 |
| 支撑 | 支持 / 保障 |
| 一体化 | 整合 / 统一 |
| 体系 | 框架 / 系统 / 机制 |
| 架构 | 结构 / 设计 |
| 维度 | 角度 / 方面 |
| 闭环 | 完整链路 / 端到端 |
| 落地 | 实施 / 应用 / 真正用起来 |

### Strategy B: Break Parallel Structures

- Replace "一是…二是…三是…四是…" with varied phrasing ("第一…第二…另外…还有一点…")
- Break "风险点：…应对措施：…" mechanical symmetry — use different structures for each risk
- Vary paragraph openings instead of repeating the same pattern

### Strategy C: Add Concrete Voice

- Add specific scenario examples ("比如一家借款企业…", "以客户经理的实际工作为例…")
- Use colloquial expressions sparingly ("贷完款就不管了", "用一次就归档")
- Vary sentence length — mix short punchy sentences with longer explanatory ones
- Add a closing/summary section if the document ends abruptly

### Strategy D: Structural Fixes

- Add a conclusion/summary section at the end if missing
- Break up walls of text with natural paragraph breaks
- Ensure transitions between sections feel natural, not template-driven

## Step 3: Apply with Format Preservation

Use the pattern from `references/format-preserving-text-replace.md`:

```python
import json, docx

# Load new text from JSON (avoids Chinese curly quote issues in Python source)
with open("new_text.json", "r", encoding="utf-8") as f:
    text_map = json.load(f)

doc = docx.Document("original.docx")

for i, para in enumerate(doc.paragraphs):
    key = str(i)
    if key not in text_map:
        continue
    new_text = text_map[key]
    if new_text == para.text.strip():
        continue

    # Save first-run font
    saved_font = None
    if para.runs:
        r0 = para.runs[0]
        saved_font = {
            "name": r0.font.name, "size": r0.font.size,
            "bold": r0.font.bold, "italic": r0.font.italic,
            "underline": r0.font.underline,
            "color_rgb": r0.font.color.rgb if r0.font.color and r0.font.color.rgb else None,
        }

    # Clear and replace
    for run in list(para.runs):
        run._element.getparent().remove(run._element)
    nr = para.add_run(new_text)
    if saved_font:
        nr.font.name = saved_font["name"]
        nr.font.size = saved_font["size"]
        nr.font.bold = saved_font["bold"]
        nr.font.italic = saved_font["italic"]
        nr.font.underline = saved_font["underline"]
        if saved_font["color_rgb"]:
            nr.font.color.rgb = saved_font["color_rgb"]

doc.save("output.docx")
```

**Why JSON for text storage**: Chinese curly quotes (`"` U+201C, `"` U+201D) inside
Python source strings cause `SyntaxError` in Python 3.12+. JSON handles all
Unicode without parser issues.

## Step 4: Verify

### Format Check
```python
orig = docx.Document("original.docx")
new = docx.Document("output.docx")
for i in range(min(len(orig.paragraphs), len(new.paragraphs))):
    if orig.paragraphs[i].runs and new.paragraphs[i].runs:
        of = orig.paragraphs[i].runs[0].font
        nf = new.paragraphs[i].runs[0].font
        assert of.name == nf.name, f"P{i} font name: {of.name} vs {nf.name}"
        assert of.size == nf.size, f"P{i} font size: {of.size} vs {nf.size}"
print("All paragraphs: font name & size PRESERVED")
```

### AI Score Comparison
```bash
python3 scripts/ai_detect.py original.docx
python3 scripts/ai_detect.py output.docx
```

Target: AI probability reduction of >50%, buzzword density near zero.
