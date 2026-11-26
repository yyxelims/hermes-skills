# Format-Preserving Text Replacement in DOCX

When rewriting document text while keeping ALL formatting intact (font, size,
bold, italic, underline, color, alignment), use this pattern:

## Core Technique

```python
import docx

doc = docx.Document("input.docx")

for para in doc.paragraphs:
    new_text = get_new_text_for_paragraph(para.text)
    if not new_text or new_text == para.text.strip():
        continue

    # 1. Save first-run font properties
    saved_font = None
    if para.runs:
        r0 = para.runs[0]
        saved_font = {
            "name": r0.font.name,
            "size": r0.font.size,
            "bold": r0.font.bold,
            "italic": r0.font.italic,
            "underline": r0.font.underline,
            "color_rgb": r0.font.color.rgb if r0.font.color and r0.font.color.rgb else None,
        }

    # 2. Remove all existing runs (use list() to avoid mutation-during-iteration)
    for run in list(para.runs):
        run._element.getparent().remove(run._element)

    # 3. Add single new run with saved font properties
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

## Why This Works

- Paragraph alignment, indentation, and spacing live on the paragraph element
  (`w:pPr`), NOT on runs. We never touch these.
- Each run carries its own font properties. By saving from the first run and
  applying to a single replacement run, we preserve the original styling.
- After clearing runs, paragraph-level properties remain intact.

## Verification

Always verify after saving:
```python
orig = docx.Document("input.docx")
new = docx.Document("output.docx")
for i in range(min(len(orig.paragraphs), len(new.paragraphs))):
    op, np = orig.paragraphs[i], new.paragraphs[i]
    if op.runs and np.runs:
        of, nf = op.runs[0].font, np.runs[0].font
        assert of.name == nf.name, f"P{i} font name mismatch: {of.name} vs {nf.name}"
        assert of.size == nf.size, f"P{i} font size mismatch: {of.size} vs {nf.size}"
```

## Pitfall: Chinese Curly Quotes in Python Source

When embedding Chinese text with `"\u201c...\u201d"` (left/right double quotation
marks) inside Python source code strings, Python 3.12+ may raise:

```
SyntaxError: invalid character '\u201c' (U+201C)
```

This happens because the parser treats `"` (U+201C) as a string delimiter.
Even though these are different Unicode codepoints from ASCII `"` (U+0022),
Python 3.12's stricter parser flags them as confusing.

**Workaround**: Store the text in a separate JSON file and read it at runtime.

```python
# Instead of embedding in source:
#   text = "系统更大的价值在于：把那些\u201c用一次就归档\u201d的审贷材料..."

# Use a JSON data file:
import json
with open("text_data.json", "r", encoding="utf-8") as f:
    text_map = json.load(f)
new_text = text_map["paragraph_9"]
```

JSON handles all Unicode codepoints without issue.
