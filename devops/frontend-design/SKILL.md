---
name: frontend-design
description: >
  Create distinctive, production-grade HTML/CSS frontend interfaces with high design quality.
  Use this skill whenever the user asks to build web pages, HTML reports, interactive components,
  or visual dashboards. Generates creative, polished code that avoids generic aesthetics.
  Triggers on: "make a webpage", "build HTML", "create a dashboard", "design a page",
  "write an HTML report", "make it look good".
tags: [frontend, html, css, design, ui]
---

# Frontend Design

Create distinctive, production-grade frontend interfaces that avoid generic aesthetics.
Implement self-contained HTML files with inline CSS and JS.

## Interactive Diagram Patterns

When the user asks for "可交互" (interactive), "思维导图" (mind map), "给领导看" (for leadership), or "展开" (expandable), build a self-contained interactive pipeline diagram. See `references/interactive-pipeline.md` for the complete implementation template.

### Vertical Pipeline with Inline-Below Details (DEFAULT — always use this pattern)

**The user strongly prefers inline-below expansion for interactive diagrams.** Right-side floating detail panels have been rejected because they overlap when parallel branches exist.

**Core layout:**
- Nodes form a **vertical centered chain** connected by downward arrows
- Each node is a clickable card (icon + step label + title + summary + "▸ 展开详情" hint)
- Clicking a node toggles its detail panel **open directly below the node** (not to the side)
- Detail uses `max-height: 0 → 1200px` transition with `overflow: hidden` — pure CSS flow, no overlap risk
- **Nodes MUST stay in a straight vertical line** — they never shift horizontally
- **All nodes can expand simultaneously** — no mutex, no one-at-a-time restriction
- No JavaScript spacing calculations needed — the column flow layout handles it naturally

**Structure:**
```
.step-container (flex, centered)
  .step-inner (flex column)
    .pipe-node (clickable card)
    .step-detail (max-height animated, below node)
```

**Parallel branches:**
```
.par-label ("⚡ 并行区 ①")
.parallel-wrap (flex row, centered, gap: 24px)
  .parallel-col (flex column)
    .step-container → .step-inner → node + detail
  .parallel-col (same)
.par-label-merge ("▼ 两路结果汇聚 ▼")
```
Each branch's detail expands below its own node — **never overlaps** because they're in separate flex columns.

**Toggle button:**
- Wrap pipeline in `max-height: 0; overflow: hidden; transition: max-height 0.6s` container
- A centered "展开核心链路图 ▾" / "收起核心链路图 ▾" toggle button controls visibility
- Consider auto-opening a key step when first revealed

**Visual style:**
- Light theme with soft off-white bg (#f6f5f2), white surfaces, subtle borders
- Color-coded step icons (blue/teal/amber/green/purple/red for sequential steps)
- Active node gets accent border + subtle background (#f8fafc)
- Hover lifts the node slightly (transform: translateY(-1px))
- CSS variables for colors: `--accent: #0284c7; --green: #059669; --amber: #d97706; --red: #dc2626; --purple: #7c3aed`

### Pitfalls (user-validated, DO NOT repeat)

1. ❌ **Horizontal mind-map** — user rejected explicitly. Always vertical pipeline.
2. ❌ **Absolute-positioned right-side floating details** — FAILS with parallel branches. Details from side-by-side nodes overlap each other. User: "制式文件验真的展开卡片会被挡住。"
3. ❌ **Sticky detail panels** — details show at fixed page position, not beside the clicked node.
4. ❌ **One-open-at-a-time mutex** — user wants all nodes expandable simultaneously.
5. ❌ **JavaScript recalcSpacing()** — complex, fragile, unnecessary with inline-below pattern.

## Design Thinking

Before coding, pick a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: minimalist, maximalist, retro, organic, luxury, playful, editorial, brutalist, industrial, art deco, pastel, dark-tech
- **Differentiation**: What makes this UNFORGETTABLE?

**CRITICAL**: Choose a clear direction and execute with precision. Bold maximalism and refined minimalism both work - the key is intentionality.

## Design Defaults (User Preference)

**Default to LIGHT theme.** Use white/off-white backgrounds (#f8f9fb), dark text (#334155), subtle borders (#e2e8f0). Only use dark theme if the user explicitly requests it or the content domain demands it (terminal, code editors, gaming).

**Typography**: Noto Sans SC for Chinese body text. System sans-serif for code/monospace.
**Color accents**: Blues and ambers preferred over purples. Avoid purple gradients entirely.
**Mobile**: Responsive with media queries. Single-column below 600px.

## Implementation Standards

- **Single HTML file** with inline CSS/JS (no external dependencies unless explicitly requested)
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view

## Theme Default

**This user prefers LIGHT themes.** Use light backgrounds (#f8f9fb), white surfaces (#ffffff), dark text (#334155), and soft borders (#e2e8f0). Color accents should lean blue (#0284c7) for technical content, warm amber (#d97706) for emphasis. Use Noto Sans SC for Chinese text. Never default to dark themes unless the user explicitly requests one.

Replace the Aesthetics Guidelines "Prefer dark themes for technical content, light for editorial" with:
- **Default: Light theme.** Light backgrounds with clean typography. Dark text on light surfaces for readability.
- **When to use dark**: Only when user explicitly asks for "dark mode" or "dark theme."

## Aesthetics Guidelines

**Typography**: Use distinctive fonts. Avoid Arial, Inter, Roboto. Pair a display font with a refined body font. Use system font stacks or Google Fonts via @import.

**Color**: Commit to a cohesive palette. Use CSS variables. Dominant colors with sharp accents beat timid, evenly-distributed palettes. Default to light theme for this user. Recommended light palette: bg #f8f9fb, surface #ffffff, text #334155, accent #0284c7, hot #d97706. Use dark themes only when user explicitly asks.

**Motion**: Use CSS animations for page load reveals and hover states. `animation-delay` for staggered reveals. Avoid excessive motion - one well-orchestrated entrance beats scattered micro-interactions.

**Spatial Composition**: Unexpected layouts. Generous negative space OR controlled density. Don't center everything.

**Backgrounds**: Create atmosphere. Gradient meshes, subtle noise/grain, geometric patterns, layered transparencies. Never solid white or solid black backgrounds.

**Anti-patterns to AVOID**:
- Purple gradients on white backgrounds
- Inter/Roboto/Arial as only font choices
- Cookie-cutter centered layouts
- Bootstrap-like generic card components

Match implementation complexity to the vision. Maximalist = elaborate code. Minimalist = restraint + precision.

## Interactive Architecture Diagrams

For architecture flow, pipeline, or process diagrams: see `references/interactive-pipeline-diagrams.md`. Key rules from user feedback:
- Details expand BELOW the clicked node (not floating right — causes overlap in parallel sections)
- Multiple nodes must be toggleable simultaneously (no mutual exclusion)
- Pipeline starts hidden behind a "展开核心链路图" toggle button
- Parallel sections use flexbox side-by-side, each with its own detail area

## Output Pattern

1. Write the complete HTML file
2. Save it to the user's requested path
3. Tell the user: `open /path/to/file.html` to view

## Support Files

- **`references/interactive-pipeline.md`** — Full implementation template for interactive pipeline diagrams: HTML structure, CSS, dynamic spacing JavaScript, color-coding conventions, and user-validated pitfalls.
