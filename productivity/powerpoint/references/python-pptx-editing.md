# python-pptx Programmatic Editing

When the edits are primarily text changes, font unification, or color swaps across
many shapes — and the slide layout/structure doesn't need to change — use
python-pptx instead of the unpack/edit/pack XML workflow. It's faster and less
error-prone for these tasks.

## When to use python-pptx vs XML editing

| Task | Use |
|------|-----|
| Text-only content changes | python-pptx |
| Font unification across all slides | python-pptx |
| Shape fill color changes | python-pptx |
| Adding/removing slides | XML unpack/edit/pack |
| Reordering shapes or changing layouts | XML unpack/edit/pack |
| Complex shape restructuring | XML unpack/edit/pack |

## Inspection First

Always inspect the presentation structure before writing the edit script:

```python
from pptx import Presentation
prs = Presentation('input.pptx')
for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if shape.has_text_frame:
            t = shape.text_frame.text.strip()[:100]
            if t:
                print(f"Slide {i+1} [{shape.name}]: {t}")
```

## Shape Name Pitfalls

**Critical**: shape names (cNvPr `name` attribute) do NOT reflect visual hierarchy.
Always verify which shape is which by checking fill colors and text content:

```python
for shape in slide.shapes:
    try:
        c = shape.fill.fore_color.rgb
        print(f"  {shape.name}: fill={c}")
    except:
        pass
```

Common mistake: confusing a card body rectangle with its accent bar.
The accent bar is typically thin (small height) while the card body is large.

## Font Unification Pattern

**⚠️ CRITICAL: Must set ALL THREE font tags** (`<a:latin>`, `<a:ea>`, `<a:cs>`) at XML level.
Setting only `run.font.name` (which touches `<a:latin>`) or only `<a:ea>` leaves mismatches.
Stripping all overrides without explicit replacement also fails — PowerPoint theme defaults
can differ per text box. **Always run verification after font changes.**

For the complete verified script with all three elements and verification code, see
[references/font-unification.md](references/font-unification.md).

Standard font for Chinese PPTs: **Calibri** (universally available, handles Chinese acceptably on all platforms).

```python
# MINIMAL CORRECT PATTERN:
from lxml import etree
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
FONT = 'Calibri'

for run in all_runs:  # iterate all runs including table cells
    rPr = run._r.get_or_add_rPr()
    for tag in ['latin', 'ea', 'cs']:
        for old in rPr.findall(f'{{{A_NS}}}{tag}'):
            rPr.remove(old)
    run.font.name = FONT
    for tag in ['ea', 'cs']:
        el = etree.SubElement(rPr, f'{{{A_NS}}}{tag}')
        el.set('typeface', FONT)
```

## Replacing Text in Shapes

Use `text_frame.clear()` then add a new run:

```python
def set_text_shape(shape, text, latin="Arial", ea="Microsoft YaHei",
                   size=Pt(11), bold=False, color=None, alignment=None):
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    if alignment:
        p.alignment = alignment
    run = p.add_run()
    run.text = text
    set_font(run, latin=latin, ea=ea, size=size, bold=bold, color=color)
```

## Table Cell Coloring

python-pptx's `cell.fill` API is unreliable for background colors. Set fills via XML:

```python
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'

def set_cell_fill(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(f'{{{A}}}solidFill'):
        tcPr.remove(old)
    for old in tcPr.findall(f'{{{A}}}noFill'):
        tcPr.remove(old)
    sf = etree.SubElement(tcPr, f'{{{A}}}solidFill')
    srgb = etree.SubElement(sf, f'{{{A}}}srgbClr')
    srgb.set('val', hex_color)
```

**Common pattern**: color-code the "阶段" (pipeline stage) column to visually
group agents into pipeline clusters. Use alternating white/light-gray striped
backgrounds for body columns.

**Pitfall — column index**: Always verify column order before coloring.
`table.cell(row, 0)` may be the Agent name, not the stage column.
Dump a few rows first to confirm which column holds what:

```python
for ri in range(3):
    for ci in range(len(tbl.columns)):
        print(f"  cell({ri},{ci}) = {tbl.cell(ri, ci).text[:30]}")
```

## Visual Hierarchy in Bullet Lists

When a slide has business innovations and technical implementation details
mixed in a single column, differentiate them visually:

- **Business innovations** (core selling points): larger font (13pt), bold,
  accent color, prefixed with ★
- **Technical details** (supporting): smaller font (10pt), muted gray,
  indented with ▸, no bold

This lets the presenter emphasize the business story while keeping tech
details visible but secondary.

## Verification Loop

After running the edit script, ALWAYS verify:
1. Content: `python -m markitdown output.pptx`
2. Colors: dump shape fill colors programmatically (check card bodies stayed white, accent bars changed correctly, table cells grouped by color)
3. Fonts: check a few runs for latin + ea typeface values
4. Table columns: verify the colored column is the intended one (not accidentally coloring Agent names)

Fix any issues and re-run the script. The edit script should be idempotent —
you should be able to run it multiple times on the same file.
