# Interactive Pipeline Diagram — Implementation Template

Complete reference for building vertical, centered, multi-expandable pipeline diagrams.
User-validated through multiple iterations. Do NOT deviate from this pattern without explicit user request.

## HTML Structure

```html
<!-- Toggle button -->
<div class="toggle-wrap">
  <button class="toggle-btn" onclick="togglePipeline()">
    <span>展开核心链路图</span><span class="arrow">▾</span>
  </button>
</div>

<!-- Pipeline (hidden by default) -->
<div class="pipeline-wrap" id="pipelineWrap">
<div class="pipeline">

  <!-- Single node -->
  <div class="step-container" id="sc1">
    <div class="step-inner">
      <div class="pipe-node" onclick="tgl('s1','sc1',this)">
        <div class="node-icon ni-blue">📥</div>
        <div class="step-num">STEP 1</div>
        <div class="step-title">节点标题</div>
        <div class="step-summary">简要描述</div>
        <div class="step-hint">▸ 展开详情</div>
      </div>
      <div class="step-detail" id="dt1"></div>
    </div>
  </div>

  <!-- Connector -->
  <div class="pipe-connector">
    <div class="pipe-arrow"></div>
    <div class="pipe-arrow-head"></div>
  </div>

  <!-- Parallel section -->
  <div class="par-label">⚡ 并行区 ①：描述</div>
  <div class="parallel-wrap">
    <div class="parallel-col">
      <div class="step-container" id="sc3a">
        <div class="step-inner">
          <div class="pipe-node" onclick="tgl('s3a','sc3a',this)">...</div>
          <div class="step-detail" id="dt3a"></div>
        </div>
      </div>
    </div>
    <div class="parallel-col">
      <div class="step-container" id="sc3b">
        <div class="step-inner">
          <div class="pipe-node" onclick="tgl('s3b','sc3b',this)">...</div>
          <div class="step-detail" id="dt3b"></div>
        </div>
      </div>
    </div>
  </div>
  <div class="par-label-merge">▼ 结果汇聚 ▼</div>

</div>
</div>
```

## Key CSS Patterns

### Node
```css
.pipe-node {
  background: var(--surface); border: 2px solid var(--border);
  border-radius: 12px; padding: 16px 22px;
  cursor: pointer; transition: all 0.2s;
  box-shadow: var(--shadow); width: 320px; text-align: center;
}
.pipe-node:hover { border-color: #94a3b8; box-shadow: var(--shadow-md); }
.pipe-node.active { border-color: var(--accent); background: #f8fafc; }
```

### Detail (inline-below, NEVER absolute-positioned)
```css
.step-detail {
  width: 100%; overflow: hidden;
  transition: max-height 0.4s ease, opacity 0.3s ease;
  max-height: 0; opacity: 0;
}
.step-detail.open { max-height: 1200px; opacity: 1; margin-top: 8px; }
```

### Pipeline toggle
```css
.pipeline-wrap {
  max-height: 0; overflow: hidden;
  transition: max-height 0.6s ease; opacity: 0;
}
.pipeline-wrap.show { max-height: 20000px; opacity: 1; }
```

### Parallel section
```css
.parallel-wrap {
  display: flex; align-items: flex-start; justify-content: center;
  gap: 24px; width: 100%; max-width: 800px;
}
.parallel-col {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; max-width: 340px;
}
```

## JavaScript

```javascript
const openNodes = {};
function tgl(nodeId, containerId, el) {
  const container = document.getElementById(containerId);
  const detailDiv = container.querySelector('.step-detail');
  if (openNodes[nodeId]) {
    detailDiv.classList.remove('open');
    setTimeout(() => { detailDiv.innerHTML = ''; }, 400);
    el.classList.remove('active');
    delete openNodes[nodeId];
  } else {
    if (!detailDiv.innerHTML) {
      detailDiv.innerHTML = '<div class="detail-inner">' + dt[nodeId] + '</div>';
    }
    detailDiv.offsetHeight; // force reflow
    detailDiv.classList.add('open');
    el.classList.add('active');
    openNodes[nodeId] = true;
  }
  setTimeout(() => {
    if (openNodes[nodeId]) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 150);
}

function togglePipeline() {
  // toggle .show on pipeline-wrap, update button text/arrow
  // On close: clean up all open nodes
}
```

## Color Coding Convention

| Step | Color | CSS class |
|------|-------|-----------|
| Input/submit | Blue #0284c7 | `.ni-blue` |
| Dispatch/schedule | Teal #0d9488 | `.ni-teal` |
| Parallel processing | Amber #d97706 | `.ni-amber` |
| Output/report | Green #059669 | `.ni-green` |
| Analysis/mining | Purple #7c3aed | `.ni-purple` |
| Risk/monitoring | Red #dc2626 | `.ni-red` |
| ML/prediction | Indigo #4f46e5 | `.ni-indigo` |

## User-Validated Pitfalls

1. **Right-side floating details** → OVERLAP with parallel branches. Always use inline-below.
2. **Absolute positioning** → Requires fragile JS spacing calculations. Avoid.
3. **One-open-at-a-time mutex** → User: "我是想要可以同时展开多个节点！！！"
4. **Horizontal mind-map** → User: "不是。。。你还没明白我意思"
5. **Node shifting off vertical line** → User: "现在你点击某个节点那个节点就跑右边去了"
6. **Details appearing at fixed page top** → User: "详情框都在链路图最上方展示"
7. **No toggle button** → User: "点击这个平台的展开链路图按钮后再动态展示"
