# Interactive Pipeline / Architecture Diagrams

Proven pattern for interactive architecture flow diagrams. Emerged from multiple
iterations on a credit-audit multi-agent platform proposal.

## Core Layout

Vertical centered pipeline with connected nodes (arrows between them), plus a
"展开核心链路图" toggle button that reveals the entire pipeline on click.

## Key Interaction Rules (from user feedback)

1. **Details expand BELOW the clicked node**, not floating to the right.
   - Use `max-height` transition (0 → auto) with `overflow: hidden`
   - The detail panel slides open inline, pushing subsequent content down naturally
   - DO NOT use `position: absolute` with `left: calc(50% + ...)` — this causes
     overlap when multiple nodes in a parallel section are both open

2. **Multiple nodes can be open simultaneously.** Never use mutual-exclusion
   logic (closing others when one opens). Each node toggles independently.

3. **Parallel sections** (two or more nodes side-by-side):
   - Use `display: flex; gap: 24px` for the parallel row
   - Each parallel branch gets its own column with its own detail area below
   - Label parallel zones clearly with `<div class="par-label">⚡ 并行区</div>`

4. **Dynamic spacing** to prevent overlap when multiple expanded nodes have
   tall detail panels. Use JavaScript `recalcSpacing()` that measures
   `scrollHeight` and adjusts `margin-bottom`.

5. **Toggle button** that shows/hides the entire pipeline. Pipeline starts
   hidden (`max-height: 0; overflow: hidden`), expands on click.
   Button text toggles between "展开核心链路图" and "收起核心链路图".

6. **Auto-scroll** the clicked node into view using
   `el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })`.

## Node Styling

```css
.pipe-node {
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: 12px;
  padding: 16px 22px;
  cursor: pointer;
  width: 320px; /* fixed width keeps pipeline aligned */
  text-align: center;
}
.pipe-node.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(2,132,199,0.12);
}
```

Each node has: icon (38×38 rounded box), step number label, title, one-line summary,
and a click hint ("▸ 展开详情").

## Detail Panel

```css
.step-detail {
  width: 100%;
  overflow: hidden;
  transition: max-height 0.4s ease, opacity 0.3s ease;
  max-height: 0;
  opacity: 0;
}
.step-detail.open {
  max-height: 1200px;
  opacity: 1;
}
```

The detail content is inserted via JavaScript from a `details` object keyed by node ID.
Each detail card has a left border accent color matching the node.

## JS Toggle Logic (simultaneous open)

```javascript
const openNodes = {};

function tgl(nodeId, containerId, el) {
  const container = document.getElementById(containerId);
  const detailDiv = container.querySelector('.step-detail');

  if (openNodes[nodeId]) {
    detailDiv.classList.remove('open');
    el.classList.remove('active');
    delete openNodes[nodeId];
  } else {
    detailDiv.innerHTML = '<div class="detail-inner">' + dt[nodeId] + '</div>';
    detailDiv.offsetHeight; // force reflow
    detailDiv.classList.add('open');
    el.classList.add('active');
    openNodes[nodeId] = true;
  }
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
```

## Pitfalls

- **Absolute positioning for details causes overlap** in parallel sections.
  Always use inline-below expansion.
- **Mutual exclusion** (closing other nodes when one opens) was explicitly
  rejected by the user. Keep nodes independently toggleable.
- The pipeline must start HIDDEN behind a toggle button for presentation flow.
- Connector arrows between nodes use simple CSS: 3px wide gradient line + CSS triangle.
