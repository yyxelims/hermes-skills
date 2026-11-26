---
name: powerpoint
description: "Create, read, edit .pptx decks, slides, notes, templates."
license: Proprietary. LICENSE.txt has complete terms
platforms: [linux, macos, windows]
---

# Powerpoint Skill

## When to use

Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions "deck," "slides," "presentation," or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill.

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) |
| Programmatic text/color/font edits | Read [references/python-pptx-editing.md](references/python-pptx-editing.md) |
| Create from scratch | Read [pptxgenjs.md](pptxgenjs.md) |

---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for XML-based editing, or [references/python-pptx-editing.md](references/python-pptx-editing.md) for programmatic edits.**

**XML (unpack/edit/pack) — use for:** adding/removing/reordering slides, restructuring layouts.\n1. Analyze template with `thumbnail.py`\n2. Unpack → manipulate slides → edit content → clean → pack

**python-pptx — use for:** text-only changes, font unification, shape color swaps, table cell coloring, bulk content updates across many shapes. Faster and less error-prone than XML for these tasks. See [references/python-pptx-editing.md](references/python-pptx-editing.md) for patterns and pitfalls.

**Workflow preference**: write the complete python-pptx script in one pass, then run it. Do not use step-by-step trial-and-error — the user prefers direct, complete solutions. Always dump shape names + fills before writing the script to avoid confusing card bodies with accent bars.

---

## Complete Rebuild Workflow

When the existing PPTX needs major restructuring (new layouts, swimlane diagrams, flowcharts, color system overhaul), **rebuilding from scratch with pptxgenjs** is an option. However, **always ask the user first** before doing a full rebuild — they may prefer incremental edits to an existing file. If they say "改的不好" after a rebuild, revert to python-pptx patches on their preferred version.

The template [templates/fintech-pptx-builder.js](templates/fintech-pptx-builder.js) provides a complete starting point with:

- **Design system**: Semantic color palette, card factory (white bg + shadow + top 4px accent bar), slide helpers
- **Icon pipeline**: react-icons (FontAwesome) → sharp → base64 PNG — no emoji, consistent rendering
- **Common patterns**: Cover/closing dark slides, 3-card pain points, value-chain flow with arrow connectors, swimlane architecture diagrams, competitor comparison bars, 2×2 value grids, agent cards
- **Pitfall prevention**: Shadow/option factories (never reuse objects — pptxgenjs mutates them), RECTANGLE not ROUNDED_RECTANGLE for accent-bar cards

Requirements: `npm install pptxgenjs react-icons react react-dom sharp`

Copy the template, edit the `C` palette and slide blocks, run `node build.js`.

For non-PPT document tasks that arise during PPT work:
- Extracting Word comments: see [references/docx-comment-extraction.md](references/docx-comment-extraction.md)
- Inserting large content blocks into existing .docx programmatically: see [references/python-docx-bulk-insertion.md](references/python-docx-bulk-insertion.md)
- Generating LaTeX PDFs from technical content: see `latex-chinese-docs` skill (tectonic + ctex for Chinese docs)

---

## Design Ideas

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**For Chinese PPTs**: Use **Calibri** — PowerPoint default since Office 2007, universally available, handles Chinese acceptably. Do NOT use Arial+Microsoft YaHei combo unless the user explicitly asks for it. Do NOT use Noto Sans SC — not a standard system font.

**For English-only PPTs**: Pick from the table below.

**When font unification is needed**: use the script in [references/font-unification.md](references/font-unification.md) which sets all three XML font elements (`latin`, `ea`, `cs`) and verifies afterwards.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection.

**Preferred path (when LibreOffice + Poppler are available):**

```bash
soffice --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

**Fallback (macOS without LibreOffice):**

`qlmanage -t` generates a single composite thumbnail, NOT per-slide images. Visual QA with subagents is blocked when LibreOffice is unavailable. In that case:
- Rely on `markitdown` content extraction for QA
- Verify no left-over placeholder text (`grep -iE "xxxx|lorem"`)
- Manually scan for cardinal layout errors (overlapping coordinates, text overflow from container dimensions)
- Open the file and inspect manually when possible

If you CAN install LibreOffice: `brew install --cask libreoffice` and `brew install poppler`.

---

## Dependencies

- `pip install "markitdown[pptx]"` - text extraction
- `pip install python-pptx` - programmatic editing (text/color/font changes)
- `pip install lxml` - XML manipulation for East Asian font support
- `pip install Pillow` - thumbnail grids
- `npm install -g pptxgenjs` - creating from scratch
- LibreOffice (`soffice`) - PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) - PDF to images
