# PPTX Font Unification — Correct Approach

## Problem

Using `run.font.name = "Calibri"` in python-pptx only sets the `<a:latin>` font element.
Chinese text uses `<a:ea>` (East-Asian), and some systems use `<a:cs>` (complex script).
If any of these are left with old values or missing, fonts appear inconsistent when opened.

## Wrong Approaches

1. **Only setting `font.name`** — misses `<a:ea>` and `<a:cs>`, so Chinese text keeps its original font.
2. **Stripping all font elements** (removing `<a:latin>`, `<a:ea>`, `<a:cs>`) — lets PowerPoint use its theme defaults, which may differ per text box or paragraph, causing visible inconsistency.
3. **Setting only `<a:latin>` and `<a:ea>`** — some runs have `<a:cs>` with a different font that overrides.

## Correct Approach

Set ALL THREE font elements (`latin`, `ea`, `cs`) to the same target font at the XML level:

```python
from lxml import etree
from pptx import Presentation

A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
FONT = 'Calibri'  # Safe default for cross-platform PPT compatibility

prs = Presentation('input.pptx')

for slide in prs.slides:
    for shape in slide.shapes:
        # Regular text shapes
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if run.text.strip():
                        rPr = run._r.get_or_add_rPr()
                        # Remove old font elements
                        for tag in ['latin', 'ea', 'cs']:
                            for old in rPr.findall(f'{{{A_NS}}}{tag}'):
                                rPr.remove(old)
                        # Set all three
                        run.font.name = FONT  # sets <a:latin> via API
                        for tag in ['ea', 'cs']:
                            el = etree.SubElement(rPr, f'{{{A_NS}}}{tag}')
                            el.set('typeface', FONT)
        # Table cells (separate text frames)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    for para in cell.text_frame.paragraphs:
                        for run in para.runs:
                            if run.text.strip():
                                rPr = run._r.get_or_add_rPr()
                                for tag in ['latin', 'ea', 'cs']:
                                    for old in rPr.findall(f'{{{A_NS}}}{tag}'):
                                        rPr.remove(old)
                                run.font.name = FONT
                                for tag in ['ea', 'cs']:
                                    el = etree.SubElement(rPr, f'{{{A_NS}}}{tag}')
                                    el.set('typeface', FONT)
```

## Verification (mandatory after font changes)

**⚠️ ALWAYS verify after font changes. The user will notice inconsistency immediately and will be frustrated if it's not fixed.**

Always verify by scanning ALL runs and checking for mismatches:

```python
fonts_seen = {}
for slide in prs.slides:
    for shape in slide.shapes:
        for source in _all_text_frames(shape):  # include tables
            for run in source.runs:
                rPr = run._r.find(f'{{{A_NS}}}rPr')
                latin = ea = 'MISSING'
                if rPr is not None:
                    le = rPr.find(f'{{{A_NS}}}latin')
                    ee = rPr.find(f'{{{A_NS}}}ea')
                    if le is not None: latin = le.get('typeface')
                    if ee is not None: ea = ee.get('typeface')
                key = f'{latin} | {ea}'
                fonts_seen[key] = fonts_seen.get(key, 0) + 1

if len(fonts_seen) != 1:
    print(f"MISMATCH! Found {len(fonts_seen)} font combinations:")
    for k, v in fonts_seen.items():
        print(f"  {v} runs: {k}")
else:
    print("ALL UNIFIED")
```

## Recommended Font for Chinese PPTs

- **Calibri**: PowerPoint default since Office 2007, universally available, renders Chinese acceptably on all platforms.
- **Microsoft YaHei (微软雅黑)**: Better Chinese rendering, but NOT available on macOS by default. Only use if the presentation will exclusively be viewed on Windows.
- Do NOT use Noto Sans SC — not a standard system font on either macOS or Windows and will cause fallback issues.
