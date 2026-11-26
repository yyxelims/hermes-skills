# Skill Audit Methodology

Systematic skill audit using 钱学森《工程控制论》 principles, derived from a full audit of 32 skills (Group 1: apple/creative/research/uncategorized).

## Five Scoring Dimensions (1–5)

### 1. 闭环性 (Closure)
Does the skill form a complete feedback loop — execution → verification → correction?

| Score | Criteria |
|-------|----------|
| 1 | No feedback mechanism |
| 2 | Implicit feedback only (user must manually verify) |
| 3 | Partial feedback (some verification, no correction loop) |
| 4 | Complete feedback loop with verification steps |
| 5 | Full closed loop: measure → compare → correct → re-verify |

### 2. 稳定性 (Stability)
Does the skill handle errors, edge cases, and environmental variance?

| Score | Criteria |
|-------|----------|
| 1 | No error handling mentioned |
| 2 | Implicit assumptions about happy path |
| 3 | Some error handling or pitfalls documented |
| 4 | Comprehensive error handling + pitfalls section |
| 5 | Anticipatory: failure modes, fallbacks, recovery strategies, env variance |

### 3. 可观测性 (Observability)
Can the agent detect success/failure without human judgment?

| Score | Criteria |
|-------|----------|
| 1 | Output is raw/unstructured, human must interpret |
| 2 | Visual output only (screenshots, rendered pages) |
| 3 | Structured output (JSON, exit codes) processable by agent |
| 4 | Multi-signal: JSON + health checks + structured logs |
| 5 | Full instrumentation: metrics, dashboards, automated alerts |

### 4. 最优化 (Optimization)
Does the skill encode efficiency — fewer steps, less cost, faster results?

| Score | Criteria |
|-------|----------|
| 1 | No optimization guidance |
| 2 | Basic command reference only |
| 3 | Some best practices or efficiency tips |
| 4 | Explicit optimization: performance budgets, parallelization, caching |
| 5 | Multi-tier: quality profiles, hardware detection, auto-scaling, cost/time tradeoffs |

### 5. 跨域可迁移性 (Cross-Domain Transfer)
How much of the skill's methodology transfers to unrelated domains?

| Score | Criteria |
|-------|----------|
| 1 | Fully tool/platform specific |
| 2 | API pattern reusable but heavily bound to one service |
| 3 | Core methodology transferable, implementation tool-specific |
| 4 | Methodology broadly applicable across many domains |
| 5 | Abstract principles applicable to any domain (e.g., QA methodology, knowledge management) |

## Patterns of High-Scoring Skills (total ≥23/25)

Skills scoring highest share these structural patterns:

1. **Rich `references/` directory** — Multiple reference files covering: troubleshooting, API docs, workflow details, templates, composition/design patterns
2. **Verification checklist** — Explicit, actionable checklist items the agent can run mechanically (not "did it look good?")
3. **Pitfalls section** — Hard-won lessons from real sessions, numbered, with before/after examples
4. **Performance budgets** — Concrete targets (e.g., "100-200ms/frame", "60fps sustained") the agent can measure against
5. **Multi-tier quality** — Quality profiles (draft/medium/production) with explicit resolution/fps/time tradeoffs
6. **Hardware detection** — Auto-detect capabilities, route to appropriate quality tier or cloud fallback
7. **Structured feedback signals** — Not just "look at the output", but JSON health checks, console error scans, ffprobe validation, color count assertions

## Patterns of Low-Scoring Skills (total ≤13/25)

Common weaknesses:

1. **Pure tool manual** — Lists commands but no workflow, verification, or error recovery
2. **No feedback loop** — Output is rendered/page/file, agent cannot programmatically verify correctness
3. **No pitfalls section** — Leaves agent to discover failure modes through trial and error
4. **Human-dependent verification** — "Open in browser and see if it looks right" is the only verification step
5. **Single-tool binding** — Methodology inseparable from one specific CLI/API

## Group 1 Audit Results (2026-05-28)

- 32 skills across apple(5), creative(19), research(6), uncategorized(2)
- 1 ghost skill: `ideation` (in available_skills list but not on disk)
- Dimension averages: Closure 3.77, Stability 3.84, Observability 3.42, Optimization 3.71, Cross-Domain 2.97
- Cross-domain is the weakest dimension across all skills — most skills are too tightly coupled to specific tools
- Report: `reports/cybernetics_group1.json`
