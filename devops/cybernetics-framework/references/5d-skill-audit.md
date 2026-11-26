# 5-Dimension Skill Audit Methodology

Systematic scoring framework for batch-evaluating skills against the cybernetics
principles. Produces structured JSON arrays suitable for comparison, ranking,
and gap analysis across large skill catalogs (35+ skills at a time).

## Scoring Dimensions (each 1-5)

### 1. Closure (闭环性) — IS THERE A FEEDBACK LOOP?
Does the skill contain a verify-and-correct cycle?

| Score | Description |
|-------|-------------|
| 1 | Pure instruction manual, no loop at all |
| 2 | Linear generate→output, no verification |
| 3 | Has verification step but manual/optional |
| 4 | Structured loop: act→verify→fix, partial automation |
| 5 | Fully automated loop: monitor→detect→correct→verify |

Key question: "If a step fails silently, will this skill detect and correct it?"

### 2. Stability (稳定性) — HOW DOES IT HANDLE FAILURE?
Does the skill document failure modes, recovery strategies, and edge cases?

| Score | Description |
|-------|-------------|
| 1 | No error handling or pitfalls documented |
| 2 | Mentions some limitations only |
| 3 | Has pitfalls section with basic recovery hints |
| 4 | Comprehensive pitfalls + troubleshooting + platform quirks |
| 5 | Exhaustive: pitfalls catalog, diagnostic tools, multi-layer recovery |

Distinguish transient environment failures (missing binary, bad config) from
design-level stability (retry logic, graceful degradation, sentinel handling).

### 3. Observability (可观测性) — CAN YOU TELL WHAT HAPPENED?
Does the skill produce signals that external systems can consume?

| Score | Description |
|-------|-------------|
| 1 | Text-only output, no structured data |
| 2 | Some structured output but incomplete |
| 3 | Good structured output (JSON) for main operations |
| 4 | Structured output + progress tracking + health checks |
| 5 | Full telemetry: structured output, streaming progress, health probes, error telemetry |

Look for: JSON output modes, health check endpoints, progress bars, log file
locations, structured error codes, and whether output is machine-readable
for downstream consumption (not just human-facing).

### 4. Optimization (优化性) — DOES IT SELF-IMPROVE?
Does the skill contain parameter search, cost control, or adaptive strategies?

| Score | Description |
|-------|-------------|
| 1 | No optimization at all |
| 2 | Basic config options only |
| 3 | Some parameter/strategy variants documented |
| 4 | Systematic search: parameter grids, quality profiles, cost controls |
| 5 | Full optimization: adaptive strategies, automated hyperparameter search, budget caps, parallel optimization |

Look for: grid search, hyperparameter tuning, quality presets, cost/budget
controls, hardware detection and adaptation, and whether optimization is
automated vs. manual.

### 5. Cross-Domain (跨域性) — HOW TRANSFERABLE IS THE METHODOLOGY?
Can the core ideas be applied to different tools/domains?

| Score | Description |
|-------|-------------|
| 1 | Single platform/tool specific, no reusable methodology |
| 2 | Tool-specific but has one transferable pattern |
| 3 | Methodology is reusable but implementation is tool-specific |
| 4 | Core methodology is domain-agnostic, some tool binding |
| 5 | Fully general principles, no tool lock-in |

Look for: Do the patterns apply if you swap the underlying tool? Is the skill
a "how to think about X" or a "how to use tool Y"?

## Principles Mapping

Each skill is tagged with the cybernetics principles it demonstrates:

1. 信息反馈原则 — Information feedback
2. 黑箱方法 — Black box method
3. 功能模拟法 — Functional simulation
4. 稳定性理论 — Stability theory
5. 最优控制 — Optimal control
6. 自组织系统 — Self-organizing system
7. 自适应系统 — Adaptive system
8. 学习系统 — Learning system
9. 系统评价与决策 — System evaluation and decision
10. 大系统理论 — Large system theory
11. 智能控制 — Intelligent control
12. 分散控制 — Decentralized control
13. 人机系统 — Human-machine system
14. 系统工程方法论 — Systems engineering methodology

Tag conservatively — only when the skill explicitly demonstrates the principle,
not when it merely "could" apply.

## Audit Process

### Phase 1: Load All Skills
Load every skill in the batch via `skill_view(name)`. For large batches (30+),
load in parallel batches of 5 to stay within rate limits.

### Phase 2: Score Independently
Score each skill on all 5 dimensions BEFORE comparing across skills. Each
dimension is independent — a skill can score 5 on stability and 1 on closure.

### Phase 3: Validate Consistency
After scoring the full batch, scan the list for anomalies:
- Skills in the same category should have roughly comparable scores
- CLI-tool-manual skills should all cluster low (5-12 range)
- Full-pipeline skills should cluster high (18-25 range)
- If a creative skill outranks a data-science skill, verify the scoring

### Phase 4: Output JSON
Produce a single JSON array with all entries. Each entry must have:
- `name` (string)
- `category` (string matching the skill directory grouping)
- `closure`, `stability`, `observability`, `optimization`, `cross_domain` (int 0-5)
- `*_note` fields explaining each score
- `principles` (array of ints, may be empty)
- `issues` (frank assessment, 1-3 sentences)

Write to `~/.hermes/skills/reports/cybernetics_groupN.json`.

### Phase 5: Verify JSON
Run: `python3 -c "import json; d=json.load(open('path')); print(f'{len(d)} entries')"`
Confirm the count matches expectations.

## Scoring Anti-Patterns

**Halo effect**: A skill with great documentation gets inflated scores across
all dimensions. Counter: score each dimension against its specific rubric,
not against your overall impression.

**Category bias**: Assuming data-science > creative. Counter: comfyui (23) is
in creative and outranks eda-quick-analysis (12) in data-science.

**Freshness bias**: Skills you loaded recently seem better. Counter: re-read
the first skill you loaded before finalizing the last one.

**Unscored ghost entries**: Skills in the available_skills catalog but missing
on disk. Score them as 0/0/0/0/0 with `issues: "SKILL NOT FOUND"`. Don't
omit them — they distort the catalog.

## Output Path Convention

```
~/.hermes/skills/reports/cybernetics_group{N}.json
```

Where N is the group number. This path is predictable for downstream consumers
(cron jobs, curator, reporting dashboards).
