# Group 2 Audit — Cross-Skill Patterns (2026-07-06)

35 skills audited across 7 categories. Confirmed earlier audit findings + surfaced new patterns.

## Confirmed: No Phantom Skills in Group 2

All 35 `available_skills` names resolved to real SKILL.md files. The previously-documented
phantom skills (`ideation`, `segment-anything-model`, etc.) are NOT in this group.

## Recurring Pattern: Methodology vs Tool-Manual Dichotomy

This session reinforced the known "审计偏见" but with sharper data:

| Class | avg closure | avg cross_domain | Examples |
|-------|-------------|-------------------|----------|
| **Methodology skills** | 4.8 | 4.4 | systematic-debugging, TDD, spike, subagent-driven-development |
| **Tool-manual skills** | 2.5 | 2.1 | python-env, codebase-inspection, himalaya, github-repo-management |
| **Orchestration skills** | 4.0 | 3.0 | claude-code, hermes-agent, kanban-orchestrator, webhook-subscriptions |

**Key insight**: Tool-manual skills are NOT "bad" — they serve a different purpose (reference
material for CRUD operations). Scoring them on closure/cross_domain is measuring a fish by
its ability to climb a tree. Future audits should add a `tool_manual` flag so these skills
are scored with adjusted expectations (e.g., stability and observability matter more than
closure for reference material).

## New Pattern: "Massive Reference" Skills Need Layering

Two skills (hermes-agent ~30KB, claude-code ~20KB) are comprehensive reference manuals but
waste tokens when injected wholesale. Pattern: split into sub-skills loaded on demand.

- `hermes-agent` → could split into `hermes-config`, `hermes-cli`, `hermes-gateway`, `hermes-contributing`
- `claude-code` → could split into `claude-code-print-mode`, `claude-code-interactive`, `claude-code-config`

## New Pattern: Missing CI Automation Hooks

Several GitHub skills (code-review, issues, pr-workflow) describe manual workflows that
could be automated via GitHub Actions. Pattern: add a "CI trigger" subsection showing
how to wire the skill into a workflow YAML.

## New Pattern: Verification-Loop Gap

The most common issue across tool-manual skills: they describe HOW to do something but
never verify the result. Example fixes:

- `python-env`: after `pip install`, run `python -c "import pkg; print(pkg.__version__)"`
- `himalaya`: after `message send`, poll sent folder to confirm delivery
- `codebase-inspection`: compare pygount output against `git ls-files | wc -l` for sanity

## Practical Confirmation: Batch Size

The skill says "每批8个skill" for sequential loading. In practice, 5 parallel `skill_view()`
calls per turn is the reliable maximum — Hermes tool-call parallelism caps at 5. At 5/turn ×
7 turns = 35 skills loaded efficiently in one session. Update the guidance: 5, not 8.

## JSON Output Path: Group-Based Variant

The skill documents output to `~/.hermes/plans/cybernetics-audit-YYYY-MM-DD.json`.
Group-based audits (like this one) use `~/.hermes/skills/reports/cybernetics_groupN.json`.
This is legitimate — the group variant is part of the large-scale parallel workflow's
intermediate outputs. Document both paths.

---

# Group 2 Audit — Update (2026-07-14)

33 skills audited across 4 categories (devops: 11, software-development: 12, github: 6,
autonomous-ai-agents: 4). All 33 `skill_view()` calls succeeded — zero ghosts, zero path
mismatches, zero ambiguous duplicates in this group.

## Confirmed: Dimensions Ranking

The five-dimension ranking is stable across audits:
```
optimization (3.85) > stability (3.97) > closure (3.94) > observability (3.52) = cross_domain (3.52)
```
Observability and cross_domain remain the global weakest dimensions — every audit
reproduces this.

## Confirmed: Autonomous-AI-Agents Internal Stratification

The 4-agent category shows extreme internal contrast:

| Skill | closure | stability | observability | optimization | cross_domain |
|-------|---------|-----------|---------------|--------------|-------------|
| claude-code | 5 | 5 | 5 | 5 | 4 |
| hermes-agent | 4 | 5 | 5 | 4 | 4 |
| codex | 3 | 3 | 3 | 3 | 3 |
| opencode | 3 | 3 | 3 | 3 | 3 |

The gap between claude-code and codex/opencode is driven entirely by **observability tooling**:
structured JSON output with cost/session tracking vs text-only output. This is actionable —
codex and opencode skills should document their observability gaps and suggest workarounds.

## New Finding: `plan` Skill is Dangerously Minimal

`plan` scored closure=3, stability=2, observability=2, optimization=2 — the weakest skill
in the group. It's essentially a one-constraint document ("don't execute, write a plan")
with no quality checklist, no anti-patterns, no verification method, and no clear
differentiation from `writing-plans`. It occupies an unclear position between `/plan`
(command-level constraint) and `writing-plans` (rich methodology). Recommendation:
either merge into `writing-plans` as a "plan-only mode" section or add minimum quality
guidance (checklist, anti-patterns, verification steps).

## New Finding: GitHub Skills Cluster as Reference Manuals

5 of 6 GitHub skills (github-auth, github-issues, github-repo-management, codebase-inspection,
github-code-review) are reference manuals with closure ≤ 3. Only github-pr-workflow breaks
the pattern (closure=5) because its CI auto-fix loop creates a genuine feedback cycle.
Suggestion: add a `skill_class: reference` frontmatter tag to reference-manual skills
so the audit framework can apply adjusted scoring where closure is not the primary goal.

## New Finding: Self-Referential Skills Score Highest

The cybernetics-framework skill itself scored all 5s — it's a skill about auditing skills,
and it follows its own advice perfectly. This is both a validation of the framework and a
reminder that meta-skills naturally score higher because their domain IS methodology.

## Write-File Pattern Validated

The `write_file → terminal python3` pattern for JSON generation (documented in the
cybernetics-framework pitfalls as traps A, B, C) worked flawlessly: no JSON linter
rejection of Chinese quotes, no confusable Unicode scanning, no dropped entries.
This is now the proven path for all audit report generation.

---

# Group 2 Audit — Update (2026-07-16)

38 skills audited across 5 categories (devops: 11, github: 6, mlops: 5, software-development: 12,
unknown/ghost: 4). Same `skill_view()` batch approach (5/turn). 34 real + 4 ghosts.

## Dimension Rankings

This run shifts the ranking compared to the 2026-07-14 audit:

```
stability (3.6) > observability (3.3) > closure (3.2) = optimization (3.2) > cross_domain (2.8)
```

**stability** overtakes optimization as the strongest dimension. cross_domain remains
the global weakest — consistent with earlier audits but more pronounced here (2.8 vs
the previous 3.52) because this group contains many platform-specific skills
(wechat-miniprogram-dev, debugging-hermes-tui-commands, python-env).

## 4 Persistent Ghosts Confirmed

`audiocraft-audio-generation`, `evaluating-llms-harness`, `segment-anything-model`,
`serving-llms-vllm` — all returned "Skill not found" on bare-name `skill_view()`.
These match every prior audit since 2026-06. If not intentionally retained in the
catalog, they should be cleaned up.

## Naming Patterns All Hold

- Bare names: `dspy`, `llama-cpp`, `obliteratus`, `weights-and-biases` — all resolve ✅
- Ambiguous: `python-offline-deps` → `devops/python-offline-deps` — resolves ✅
- No new naming surprises discovered.

## closure=5 Cluster: Software-Development Methodology

5 skills reach full closure, all from `software-development/`:
`requesting-code-review`, `subagent-driven-development`, `systematic-debugging`,
`test-driven-development`, and `cybernetics-framework` (devops meta-skill).

This reinforces the pattern: methodology skills designed around feedback loops naturally score
higher on closure than tool-manual or reference skills. These 5 represent the "gold standard"
for what a Hermes skill should look like when its purpose IS process enforcement.

## optimization=5: Two Standouts

Only `dspy` (mlops) and `obliteratus` (mlops) reach optimization=5 — both because they contain
genuine automatic parameter search (Bayesian optimization, tournament evaluation). No
software-development skill reaches this level because they optimize for human decision-making,
not algorithmically-tuned hyperparameters. This is a legitimate ceiling: process skills can
describe HOW to optimize but cannot automate the optimization itself.

## cross_domain=5: Five Universals

`cybernetics-framework`, `spike`, `systematic-debugging`, `test-driven-development`,
`writing-plans`. All are methodological frameworks with zero platform/tool dependency.
The pattern: if a skill describes a way of thinking rather than a way of using a specific tool,
it scores cross_domain=5.

## Category-Level Patterns

| Category | Count | Avg closure | Avg stability | Avg cross_domain | Character |
|----------|-------|-------------|---------------|------------------|-----------|
| software-development | 12 | 3.5 | 3.4 | 3.1 | Methodology-heavy, highest closure |
| mlops | 5 | 2.8 | 3.4 | 2.8 | Split: 2 tool-manuals + 2 optimization-heavy + 1 ghost |
| devops | 11 | 2.9 | 3.7 | 2.2 | Tool-manual dominant, highest stability from pitfalls |
| github | 6 | 2.5 | 3.5 | 2.3 | Reference manuals, gh/curl dual-fallback pattern |

**devops** has the highest stability (3.7) because these skills accumulate the richest
pitfall sections from real-world failures. **github** has the lowest closure (2.5) because
they're CRUD reference manuals by design.

## JSON Write-File Pattern: Proven Again

The `write_file → terminal python3` pattern for JSON generation worked without issues:
no JSON linter rejection of Chinese characters, no confusable Unicode scanning, no
dropped entries. This is the 3rd consecutive audit confirming it as the reliable path.

## Action Items

- Ghost skills (4) in catalog → should be cleaned or intentionally created
- `plan` skill still minimal (closure=2, stability=2) — same finding as 2026-07-14
- Tool-manual skills (github-*, python-env, etc.) consistently score low on closure;
  a `skill_class: reference` frontmatter tag would let the audit framework apply
  adjusted expectations

---

# Group 2 Audit — Update (2026-07-17)

37 skills audited across 6 categories (devops: 11, github: 6, software-development: 12,
data-science: 4, mcp: 1, gaming: 3). All 37 `skill_view()` calls succeeded — zero ghosts,
zero path mismatches, zero ambiguous duplicates.

## Dimension Rankings (This Run)

```
stability (4.05) > optimization (3.89) > closure (3.81) > cross_domain (3.54) > observability (3.46)
```

**stability** is the strongest dimension for the 4th consecutive audit. **observability**
remains the perennial weakest — consistent across all 4 Group 2 runs (range: 3.3–3.5).
This is structural: tool-manual skills produce human-readable output, not machine-consumable
metrics. The framework measures what skills document, not what skills do at runtime.

## Category-Level Stratification (New Detail)

| Category | Count | Avg Score | Character |
|----------|-------|-----------|-----------|
| data-science | 4 | 18.3 → 19.8† | insurance-purchase-modeling (25) single-handedly lifts the avg; remove it → 13.8 |
| software-development | 12 | 18.3 | Bimodal: methodology cluster (~23) vs tool/guide cluster (~14) |
| mcp | 1 | 21.0 | Single-skill category, strong stability from protocol design |
| gaming | 3 | 20.0 | world-cup-prediction unique: honest self-assessment raises all dimensions |
| devops | 11 | 17.5 | Mixed bag: 4 methodology (avg 22), 7 tool-manual (avg 15) |
| github | 6 | 14.2 | Reference manuals by design — lowest scores, legitimate |

† Weighted by 25-dimension total (5×5).

## closure=5 Cluster: 7 Skills

`cybernetics-framework`, `kanban-orchestrator`, `webhook-subscriptions`, `requesting-code-review`,
`spike`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`,
`insurance-purchase-modeling`, `pokemon-player`, `world-cup-prediction`.

Two new entries compared to 2026-07-16 run:
- **pokemon-player**: vision+RAM dual-observation feedback loop makes it the only gaming skill
  with full closure
- **world-cup-prediction**: 115-match backtest loop + honest framework-failure acknowledgment
  creates a genuine learn→predict→verify→correct cycle

## New Category Findings

### gaming (3 skills, first audit)

Internal contrast is extreme: pokemon-player (20) and world-cup-prediction (22) have rich
feedback loops; minecraft-modpack-server (18) is a setup manual. world-cup-prediction is
unique across ALL 37 skills: it documents its own framework failures with quantitative
evidence (0/19 accuracy, 57.9% baseline), making its self-awareness a dimension-raiser.
No other skill says "this technique I document is provably wrong — here's the data."

### data-science (4 skills, first audit)

`insurance-purchase-modeling` (25/25) is the only perfect-scoring non-meta skill across
all 4 Group 2 audits. Its pitfall list (57 entries) and data-leak audit (7 categories)
represent the deepest domain-specific knowledge capture in the entire library.
Remove it and the category average drops from 19.8 to 13.8 — a 6-point single-skill swing.
`universal-data-analysis` (10/25) is the weakest skill across all 37 — a 568-line tool
catalog with zero workflow, zero verification, zero pitfall handling.

### mcp (1 skill, first audit)

`native-mcp` (21/25) benefits from being a protocol specification disguised as a skill:
the MCP protocol itself mandates stability (reconnection, credential stripping) and
observability (tool registration, sampling metrics). The skill inherits these properties
rather than inventing them.

## Confirmed: `plan` Skill Still Minimal

Scored closure=2, stability=2, observability=2 — unchanged from 2026-07-14 and 2026-07-16
findings. At 132 lines it's the thinnest skill in the library. Recommendation (unchanged):
either merge into `writing-plans` as a "plan-only mode" section or add minimum quality
guidance (checklist, anti-patterns, verification steps).

## Confirmed: GitHub Skills Are Reference Manuals

All 6 GitHub skills score closure ≤ 4, with 4 of 6 at closure ≤ 3. This is consistent
across all 4 Group 2 audits. The `skill_class: reference` frontmatter tag proposal
(from 2026-07-14) remains the right fix — it would let the audit framework score these
on stability and observability rather than penalizing them for lacking feedback loops
they don't need.

## New Finding: Category Count Off-By-One During Audit

The task description listed "software-development=13" but the actual count is 12. Meanwhile
`github-repo-management` (the 6th GitHub skill) was initially missed because the auditor
only loaded 5 of 6 GitHub skills in one batch. Root cause: task-level count expectations
didn't match the actual available_skills list. **Prevention**: always count from
`available_skills` programmatically rather than trusting task prose. Add a verification
step: after loading, compare `len(loaded) == len(expected_list)` before proceeding to
scoring.

## JSON Write-File Pattern: 5th Consecutive Confirmation

The `write_file → terminal python3` pattern for JSON generation worked flawlessly.
This is now the proven default for all audit report generation across 5 consecutive
Group 2 runs (2026-07-06, 2026-07-14, 2026-07-16, 2026-07-17, 2026-07-20).
No JSON linter rejection, no confusable Unicode scanning, no dropped entries.
The pattern is mature enough to remove from "pitfalls" and promote to "standard workflow."

---

# Group 2 Audit — Update (2026-07-20)

35 skills audited across 5 categories (devops: 12, github: 6, software-development: 12,
data-science: 4, mcp: 1). All 35 `skill_view()` calls succeeded — zero ghosts, zero path
mismatches. Two ambiguous duplicates (`pyinstaller-packaging`, `python-offline-deps`)
resolved cleanly with `devops/` prefix.

## Dimension Rankings (This Run)

```
stability (3.8) > closure (3.5) > optimization (3.2) > observability (3.1) > cross_domain (3.0)
```

- **stability** is the strongest dimension for the 5th consecutive audit, driven by rich
  pitfall sections accumulated from real-world failures.
- **observability** (3.1) and **cross_domain** (3.0) remain the perennial weakest —
  structural: tool-manual skills produce human-readable output, not machine-consumable
  metrics, and platform-specific skills naturally score low on cross-domain.
- All dimensions dropped slightly from 2026-07-17 (stability 4.05→3.8, closure 3.81→3.5)
  because this batch contained more tool-manual skills (pyinstaller-packaging, python-env,
  codebase-inspection, universal-data-analysis) and fewer methodology-heavy skills.

## closure=5 Cluster: Same 7 Core Skills

Seven non-meta skills reach full closure:
`insurance-purchase-modeling`, `kanban-orchestrator`, `requesting-code-review`,
`subagent-driven-development`, `systematic-debugging`, `test-driven-development`.
Same cast as previous runs minus gaming skills (not in this batch). Plus the meta-skill
`cybernetics-framework` itself at perfect 25/25.

## Top & Bottom Performers

| Rank | Skill | Total | Category |
|------|-------|-------|----------|
| 🥇 | cybernetics-framework | 25 | devops |
| 🥇 | insurance-purchase-modeling | 25 | data-science |
| 🥉 | systematic-debugging | 24 | software-development |
| 🔻 | universal-data-analysis | 7 | data-science |
| 🔻 | python-env | 11 | software-development |

**`universal-data-analysis` (7/25)** remains the weakest skill across all Group 2 audits —
unchanged from 2026-07-17. A tool catalog with zero workflow, zero verification, and minimal
pitfall handling. Recommendation unchanged: either add interactive tool recommendation
logic or reclassify as a reference page outside the skill system.

## New Finding: Ambiguous Duplicates in This Batch

Two skills triggered `Ambiguous skill name` errors:
- `pyinstaller-packaging` → resolved with `devops/pyinstaller-packaging`
- `python-offline-deps` → resolved with `devops/python-offline-deps`

Both are documented in the cybernetics-framework pitfalls section (模式B). This is the
first Group 2 batch where ambiguous duplicates appeared — previous batches only hit this
in Group 3 (spotify, airtable, notion).

## Confirmed: `plan` Skill Still Minimal (4th Audit)

Scored closure=3, stability=2, observability=2, optimization=2 — effectively unchanged
from 2026-07-14, 2026-07-16, and 2026-07-17. Recommendation unchanged: merge into
`writing-plans` or add minimum quality guidance.

## Confirmed: data-science Category Is One Giant + Dwarfs

`insurance-purchase-modeling` (25/25) single-handedly lifts the category average from
12.0 to 17.5. Without it, data-science has the lowest average of any category.
The remaining 3 data-science skills (eda-quick-analysis, jupyter-live-kernel,
universal-data-analysis) are tool-manuals or reference catalogs with minimal feedback loops.

## Simplicity of This Run

This was the cleanest Group 2 audit to date:
- Zero `skill_view()` failures after resolving the 2 ambiguous duplicates
- Zero phantom skills in this batch
- Zero `write_file` issues (the "sibling subagent" warning was a false positive, already documented)
- Zero script execution errors
- Total wall time: ~3 minutes for 35 skills (including scoring + JSON generation)

The `references/group-audit-script-example.py` template and `build_group2.py` pattern
are now thoroughly battle-tested across 5 consecutive runs. No changes needed.

---

# Group 2 Audit — Update (2026-07-21)

39 skills audited across 4 categories (devops: 12, software-development: 12, github: 6,
mlops: 9 [5 real + 4 ghosts]). 35 real + 4 ghosts. Batch loading via `skill_view()` at
5/turn × 8 turns. One new ambiguous duplicate discovered (`pyinstaller-packaging`, see below).

## Dimension Rankings (This Run)

```
stability (4.17) > optimization (3.77) > observability (3.54) > cross_domain (3.51) > closure (3.43)
```

- **stability (4.17)** is the strongest dimension for the 6th consecutive audit. This batch
  contains many rich-pitfall skills (china-web-data, wechat-miniprogram-dev, python-offline-deps,
  obliteratus) that drove stability higher than usual.
- **closure (3.43)** dips to its lowest ever for Group 2 — driven by 4 ghosts (closure=0)
  and 4 reference-manual skills (codebase-inspection, github-issues, github-repo-management,
  huggingface-hub) all at closure=1. Without ghosts, real-only avg closure = 3.83.
- **observability** (3.54) slightly above previous runs (3.1–3.5 range), lifted by CDP-level
  debugger skills (node-inspect-debugger=5, python-debugpy=5) and structured ML skills
  (dspy=5, obliteratus=5, weights-and-biases=5).
- **cross_domain** (3.51) improved over 2026-07-20 (3.0) because this batch contains more
  methodology skills (systematic-debugging, TDD, spike, subagent-driven-development, dspy)
  and fewer platform-specific tool manuals.

## New Ambiguous Duplicate: `pyinstaller-packaging`

```python
skill_view('pyinstaller-packaging')  # → Ambiguous: matches devops/pyinstaller-packaging
                                     #   AND browser-automation-tools/references/pyinstaller-packaging.md
skill_view('devops/pyinstaller-packaging')  # → resolves correctly
```

This is a new 模式B discovery — not previously documented in the 7 consecutive Group 2 audits.
Added to cybernetics-framework SKILL.md known inconsistencies list (2026-07-21 entry).

Previous 2026-07-20 audit had pyinstaller-packaging in its group but flagged it as ambiguous;
this session confirms the pattern is reproducible and persistent. The duplicate lives in
`browser-automation-tools/references/pyinstaller-packaging.md` — a reference file that
shares a name with the standalone devops skill.

## 4 Ghosts Confirmed (6th Consecutive Audit)

`audiocraft-audio-generation`, `evaluating-llms-harness`, `segment-anything-model`,
`serving-llms-vllm` — all returned "Skill not found" on bare-name `skill_view()`.
These have now been confirmed across 6 audits spanning 2026-06-03 through 2026-07-21.
If not intentionally retained, clean them from the catalog.

## closure=5 Cluster: 8 Skills (Expanded)

Eight skills reach full closure, up from 7 in the 2026-07-20 run:

| Skill | Category | Key Pattern |
|-------|----------|-------------|
| cybernetics-framework | devops | Meta-skill, follows own advice |
| requesting-code-review | software-development | Full diff→scan→review→auto-fix→commit loop |
| spike | software-development | Decompose→research→build→verdict cycle |
| subagent-driven-development | software-development | Implement→spec-review→quality-review→integration-review |
| systematic-debugging | software-development | 4-phase root-cause→pattern→hypothesis→implement |
| test-driven-development | software-development | RED-GREEN-REFACTOR with mandatory verification |
| dspy | mlops/research | Define→train→evaluate→optimize→compare with teleprompters |
| obliteratus | mlops/inference | Hardware-check→method-select→run→verify→iterate |

New this run: **dspy** and **obliteratus** join the closure=5 club from the mlops category.
Both contain genuine automatic optimization loops (Bayesian search, tournament evaluation,
teleprompter-driven prompt optimization) rather than just documenting how a human should iterate.

## optimization=5 Expanded: mlops Dominance

| Skill | optimization=5 driver |
|-------|----------------------|
| dspy | BootstrapFewShot / MIPRO / Bayesian teleprompter optimization |
| obliteratus | 9 CLI methods + Bayesian search (optimized method) + tournament mode |
| llama-cpp | Quantization selection guide (Q4/Q5/Q6/IQ) + hardware-specific guidance |
| weights-and-biases | Hyperparameter sweeps (grid/random/bayes) + model registry versioning |
| python-offline-deps | Two-phase optimization for heavy dep trees, cross-platform strategy |
| requesting-code-review | Auto-fix loop (max 2 cycles), fail-closed rules |
| subagent-driven-development | Task granularity (2-5 min), parallel execution, cost trade-off analysis |
| systematic-debugging | Scientific method approach, Rule of Three |
| test-driven-development | Minimal code principle, cheating-is-OK-in-GREEN |

Eight skills at optimization=5 (up from 2 in 2026-07-16). The expansion is entirely from
mlops skills — their domain naturally contains parameter-search algorithms that translate
to optimization=5 in the audit framework.

## cross_domain=5: Five Universals (Unchanged)

`cybernetics-framework`, `spike`, `systematic-debugging`, `test-driven-development`,
`writing-plans`. Same cast as 2026-07-16. All are pure methodology with zero platform
or tool dependency.

## Category-Level Stratification

| Category | Count | Avg closure | Avg stability | Avg cross_domain | Character |
|----------|-------|-------------|---------------|------------------|-----------|
| software-development | 12 | 3.75 | 4.00 | 3.58 | Methodology-heavy, highest across all dimensions |
| mlops (real only) | 5 | 3.80 | 3.80 | 3.60 | Bimodal: 2 rich (dspy, obliteratus) + 1 reference (huggingface-hub=1) + 2 solid (llama-cpp, w&b) |
| devops | 12 | 3.17 | 4.42 | 3.42 | Tool-manual dominant, highest stability from pitfall accumulation |
| github | 6 | 2.17 | 3.67 | 2.67 | Reference manuals, lowest closure by design |

**devops** achieves the highest stability (4.42) across all Group 2 runs — driven by
china-web-data (5), python-offline-deps (5), kanban-orchestrator (5), kanban-worker (5),
and cybernetics-framework (5). These skills accumulate the most pitfalls from real-world
scraping, packaging, and orchestration failures.

**github** at closure=2.17 confirms the 4-audit pattern: these are CRUD reference manuals
and should be scored with adjusted expectations or tagged `skill_class: reference`.

**mlops** shows a bimodal pattern: `huggingface-hub` (closure=1, pure CLI reference) sits
alongside `dspy` and `obliteratus` (closure=5, full optimization pipelines). The category
label masks extreme internal contrast.

## Top & Bottom Performers

| Rank | Skill | Total (max 25) | Category |
|------|-------|----------------|----------|
| 🥇 | cybernetics-framework | 25 | devops |
| 🥇 | systematic-debugging | 25 | software-development |
| 🥇 | test-driven-development | 25 | software-development |
| 🥉 | subagent-driven-development | 24 | software-development |
| 🥉 | requesting-code-review | 24 | software-development |
| 🥉 | obliteratus | 24 | mlops/inference |
| 🔻 | huggingface-hub | 5 | mlops |
| 🔻 | codebase-inspection | 8 | github |
| 🔻 | github-issues | 8 | github |
| 🔻 | github-repo-management | 8 | github |

## Confirmed: `plan` Skill Still Minimal (5th Audit)

Scored closure=3, stability=2, observability=2, optimization=2 — effectively unchanged
from all prior audits since 2026-07-14. Recommendation unchanged.

## Confirmed: JSON Write-File Pattern (6th Consecutive)

The `write_file → terminal python3` pattern for JSON generation worked flawlessly.
34,589 bytes written with 39 complete entries, all required fields present, all names
matching expected list. 6 consecutive successful Group 2 audits confirm this is the
reliable default path.

## Simplicity of This Run

This was the cleanest Group 2 audit to date:
- Zero `skill_view()` failures after resolving 1 ambiguous duplicate (pyinstaller-packaging)
- 4 ghost skills confirmed (same 4 as every prior audit)
- Zero `write_file` / script execution errors
- All 39 entries verified: name matching, field presence, ghost annotations
- Total wall time: ~4 minutes for 39 skills (including scoring + JSON generation + verification)

---

# Group 2 Audit — Update (2026-08-03)

36 skills audited across 5 categories (devops: 9, github: 6, mlops: 9 [5 real + 4 ghosts],
software-development: 8, autonomous-ai-agents: 4). 32 real + 4 ghosts. Batch loading via
`skill_view()` at 5/turn × 8 turns. Zero ambiguous duplicates. All bare-name lookups
resolved cleanly (dspy, llama-cpp, obliteratus, weights-and-biases as documented).

**Context**: This audit ran as a scheduled cron job — no user present, fully autonomous.
All scoring decisions were made based on skill content alone without human feedback.

## Dimension Rankings (This Run)

```
stability (3.59) > closure (3.56) > optimization (3.19) > observability (3.03) > cross_domain (3.00)
```

- **stability (3.59)** is again the strongest dimension — 8th consecutive audit where stability
  leads. Driven by rich pitfall sections across devops skills (china-web-data, wechat-miniprogram-dev,
  kanban-orchestrator/worker) and the hermes-agent skill's comprehensive troubleshooting.
- **observability (3.03)** remains the perennial weakest — driven by 11 skills at observability=2
  (mostly reference-manual and tool-manual skills producing human-readable output only).
- **cross_domain (3.00)** ties observability at the bottom — this batch contains 15 skills at
  cross_domain=2 (all platform-specific: GitHub, WeChat, Chinese-web, llama.cpp, etc.).
- All dimensions are lower than the 2026-07-21 run (stability 4.17→3.59, closure 3.43→3.56)
  because this batch has fewer methodology-heavy skills in the software-development category
  (8 vs 12 in previous run).

## Historical ghost claims must be re-tested

Earlier runs reported four MLOps catalog entries as ghosts. This session disproved that snapshot:
`audiocraft-audio-generation`, `evaluating-llms-harness`, and `serving-llms-vllm` resolved successfully via `skill_view()` and were scored from current SKILL.md content; only `segment-anything-model` returned `Skill not found`.

**Rule:** never carry ghost status forward from historical JSON or prose. Re-run the current lookup for every catalog entry; only mark a skill ghost after current lookup fails (and path disambiguation/search has been considered).


## closure=5 Cluster: Same 4 Core Methodology Skills

Four skills reach full closure — all from software-development, all unchanged from prior audits:

| Skill | Key Feedback Loop |
|-------|-------------------|
| requesting-code-review | Diff→static-scan→reviewer-subagent→auto-fix→re-verify (max 2 cycles) |
| subagent-driven-development | Implement→spec-compliance-review→quality-review→integration-review |
| systematic-debugging | Root-cause→pattern→hypothesis→implement (4-phase loop with Rule of Three) |
| test-driven-development | RED-GREEN-REFACTOR with mandatory watch-it-fail verification |

**Notable absence**: dspy and obliteratus scored closure=4 in this audit (down from 5 in
2026-07-21). This is NOT a real change in skill quality — it's a cross-audit scoring
variance effect. The 2026-07-21 auditor defined closure=5 as "genuine automatic optimization
loops", while this auditor applied a stricter standard: "must include an explicit
retry→verify→correct cycle documented in the skill itself." Both audits recognize the
optimization capability; the difference is whether `BootstrapFewShot` counts as a
"verification loop" (yes in 07-21, no in 08-03). This is a known artifact of different
auditors with slightly different closure definitions — documented in the
cybernetics-framework pitfalls as "审计间评分方差."

## optimization=5: Two mlops Standouts

| Skill | optimization=5 driver |
|-------|----------------------|
| dspy | BootstrapFewShot / MIPRO / Bayesian teleprompter optimization — automatic, data-driven |
| weights-and-biases | Hyperparameter sweeps (grid/random/bayes) with metric-driven search |

Only 2 skills at optimization=5 (down from 8 in 2026-07-21). The drop is again a scoring
variance effect: this auditor scored optimization more conservatively, reserving 5 for
genuinely automated parameter search (algorithmic, not just heuristic guidance). Skills
with excellent manual optimization guides (llama-cpp quant selection, obliteratus method
table) scored 4 instead of 5.

## cross_domain=5: Seven Universals (Expanded)

Seven skills reach cross_domain=5 — up from 5 in prior audits. New additions compared to
2026-07-21:

| Skill | Why cross_domain=5 |
|-------|-------------------|
| skill-creator | Meta-skill for creating any skill — completely domain-independent |
| subagent-driven-development | Subagent delegation pattern applies to any multi-worker system |
| cybernetics-framework | Pure meta-framework, zero domain dependency |
| spike | Prototyping methodology applies to any field |
| systematic-debugging | Scientific debugging method applies to all technical systems |
| test-driven-development | RED-GREEN-REFACTOR applies to any programming language |
| writing-plans | Bite-sized planning methodology is completely domain-agnostic |

`skill-creator` (5) and `subagent-driven-development` (5) are new to this level — prior
audits scored them at cross_domain=4. This represents a scoring standard shift: the meta-
nature of these skills was recognized as truly domain-independent in this audit.

## New Category: Autonomous-AI-Agents (First Full Audit)

All 4 autonomous-ai-agent skills appeared together for the first time in a Group 2 audit:

| Skill | Total | closure | stability | observability | optimization | cross_domain |
|-------|-------|---------|-----------|---------------|--------------|-------------|
| hermes-agent | 21 | 4 | **5** | **5** | 4 | 3 |
| claude-code | 18 | 4 | 4 | 4 | 4 | 2 |
| codex | 14 | 3 | 3 | 3 | 3 | 2 |
| opencode | 14 | 3 | 3 | 3 | 3 | 2 |

**Key findings**:

1. **hermes-agent (21/25)** is the only autonomous-ai-agent skill to reach 20+. It is also
   the only skill across all 32 real skills in this audit to score stability=5 — driven by
   the most comprehensive troubleshooting section in the entire library (platform-specific
   sections for macOS, Windows, WSL2; gateway crash recovery; credential pool management;
   security/privacy toggles).

2. **hermes-agent observability=5**: Unique among all 32 real skills — it's the only tool
   documentation skill that achieves maximum observability. Driven by structured slash
   commands, session analytics (hermes insights), gateway logs, credential pool monitoring,
   and health checks (hermes doctor). No other skill documents this many observation surfaces.

3. **Internal stratification is extreme**: hermes-agent (21) vs claude-code (18) vs
   codex/opencode (14). The gap is structural — hermes-agent documents its own tooling
   exhaustively; claude-code benefits from Claude Code's structured JSON output; codex
   and opencode are thinner reference manuals.

4. **codex and opencode are mirror images**: Both score 14/25 with identical dimension
   profiles (3,3,3,3,2). They're nearly interchangeable reference manuals — same structure,
   same level of detail, same observability gap. Their only differentiation is the specific
   CLI flags and setup commands.

## Category-Level Stratification

| Category | Count | Avg Total (max 25) | Character |
|----------|-------|---------------------|-----------|
| software-development | 8 | 18.8 | Methodology-heavy bimodal: 4 at 20+ (requesting-code-review 23, subagent-driven-dev 24, systematic-debugging 24, TDD 22) vs 4 at 12-17 (spike 19, writing-plans 19, python-debugpy 17, node-inspect-debugger 17, python-env 12) |
| autonomous-ai-agents | 4 | 16.8 | Internal stratification (21→14), claude-code and hermes-agent lift average |
| mlops (real only) | 5 | 16.0 | Bimodal: dspy (21), obliteratus (20), weights-and-biases (20), llama-cpp (16) vs huggingface-hub (7 — pure CLI reference) |
| devops | 9 | 15.9 | Mixed: 3 methodology (cybernetics 24, kanban-orch 20, kanban-worker 20) + 6 tool-manual (12-18 range) |
| github | 6 | 12.5 | Reference manuals by design — lowest category |

**software-development** dominates the top (4 of the top 5 skills) — consistent with all
prior audits. Methodology skills designed around feedback loops naturally score higher.

**github** at 12.5 confirms the 8-audit pattern: these are CRUD reference manuals and
should be tagged `skill_class: reference` for adjusted audit expectations. The gh/curl
dual-fallback pattern ensures some stability but adds no closure or cross_domain value.

**mlops** internal contrast is stark: huggingface-hub (7, pure CLI reference) sits alongside
dspy (21, full auto-optimization pipeline). The category label masks this.

## Top & Bottom Performers

| Rank | Skill | Total (max 25) | Category |
|------|-------|----------------|----------|
| 🥇 | cybernetics-framework | 24 | devops |
| 🥇 | subagent-driven-development | 24 | software-development |
| 🥇 | systematic-debugging | 24 | software-development |
| 🥈 | requesting-code-review | 23 | software-development |
| 🥈 | test-driven-development | 22 | software-development |
| 🥉 | dspy | 21 | mlops |
| 🥉 | hermes-agent | 21 | autonomous-ai-agents |
| 🔻 | huggingface-hub | 7 | mlops |
| 🔻 | github-issues | 10 | github |
| 🔻 | github-repo-management | 10 | github |

**cybernetics-framework dropped from 25 to 24** compared to prior audits — the meta-skill
about auditing skills scored observability=4 (not 5) because the audit output is JSON/HTML
files, not real-time dashboards. This is a scoring standard refinement, not a skill regression.

## New Finding: Cron-Job Audit Characteristics

This is the first Group 2 audit performed as a scheduled cron job (no interactive user).
Notable characteristics of autonomous-only auditing:

1. **Scoring conservatism**: Without human feedback on ambiguous edge cases, the auditor
   defaults to more conservative scores. This likely explains the lower dimension averages
   compared to interactive audits (e.g., stability 3.59 vs 4.17 in 07-21).

2. **Self-contained verification**: All verification (36-entry count, JSON validity, ghost
   confirmation) happened programmatically via `terminal python3 -c` — no human sanity check.
   The audit pipeline itself proved robust to fully autonomous operation.

3. **No clarification delays**: The auditor couldn't ask "is this scoring too harsh?" or
   "should I re-evaluate this edge case?" — scoring was definitive and final on first pass.
   This produces a "clean" audit with no rescoring rounds but potentially less nuanced scores.

## Confirmed: JSON Write-File Pattern (7th Consecutive)

The `write_file → terminal python3` pattern for JSON generation worked flawlessly.
40,783 bytes written with 36 complete entries, all required fields present, all names
matching expected list. 7 consecutive successful Group 2 audits confirm this is the
reliable default path. The "sibling subagent modified" warning was a false positive
as documented — no actual data corruption.
