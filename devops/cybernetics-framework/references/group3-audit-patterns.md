# Group 3 Audit — Cross-Skill Patterns (2026-07-17)

**⚠️ Group recomposition**: Group 3 was reorganized from 13 categories (data-science/gaming/mlops/productivity/media/…, 39 skills) to 10 categories (autonomous-ai-agents/email/finance/media/mlops/note-taking/productivity/red-teaming/smart-home/social-media, 34 skills). This audit replaces the 2026-07-14 Group 3 report entirely — cross-reference previous patterns in the git history if needed.

34 skills audited: 30 resolved + 4 ghosts.

## Dimension Score Distribution (real skills only, ghosts excluded)

| Dimension | Avg | Min | Max | Top scorers (5) |
|-----------|-----|-----|-----|-----------------|
| closure | 3.2 | 2 | 5 | dspy, obliteratus, powerpoint, godmode |
| stability | 3.1 | 1 | 5 | claude-code, hermes-agent, godmode |
| observability | 3.2 | 1 | 5 | claude-code, hermes-agent, obliteratus, weights-and-biases, godmode |
| optimization | 2.7 | 1 | 5 | dspy, weights-and-biases, godmode |
| cross_domain | 2.5 | 1 | 5 | dspy, teach |

**Key insight**: This is the first Group 3 audit to find **observability=5** scores (previous 2026-07-14 report said "no skill scored observability=5"). This is partially due to group recomposition (claude-code and hermes-agent moved into this group) and partially due to scoring methodology accepting structured metrics + human-in-the-loop as observation=5 rather than requiring fully automated gating. Multi-dimension gold standard: **godmode** scored 5/5/5/5/4 — an unprecedented four-perfect-dimension skill.

## Confirmed Ghosts (4)

`audiocraft-audio-generation`, `evaluating-llms-harness`, `segment-anything-model`, `serving-llms-vllm` — same 4 ghosts as every audit since May 2026. These are stable. No new ghosts discovered. All confirmed via `skill_view()` → "not found" followed by `search_files` global verification. Note: audio and SW audits triggered `same_tool_failure_warning` (3+ consecutive `success: false` on `skill_view()` — expected behavior for bulk ghost confirmation, documented in framework pitfalls).

## Pattern 1: Autonomous-AI-Agents — The Mature Category

| Skill | closure | stability | observability | optimization | cross_domain |
|-------|---------|-----------|---------------|--------------|-------------|
| claude-code | 4 | 5 | 5 | 4 | 3 |
| hermes-agent | 4 | 5 | 5 | 4 | 4 |
| codex | 3 | 3 | 3 | 2 | 2 |
| opencode | 3 | 3 | 3 | 2 | 2 |

This category splits cleanly: **mature pair** (claude-code + hermes-agent, avg 4.4) vs **basic pair** (codex + opencode, avg 2.7). The gap is driven by documentation investment: claude-code's 15 pitfalls + JSON output + tmux monitoring vs codex's minimal error handling. hermes-agent benefits from being the framework's own documentation. Key differentiator: mature skills have **structured output formats** enabling programmatic verification; basic skills rely on terminal stdout parsing.

## Pattern 2: Category Stratification — New Grouping, New Landscape

| Category | Avg Score | Skills | Notes |
|----------|-----------|--------|-------|
| **autonomous-ai-agents** | 3.6 | 4 | Bimodal: mature(4.4) vs basic(2.7) |
| **red-teaming** | 4.6 | 1 | godmode — the highest-scoring skill in the entire group across all dimensions except cross_domain |
| **mlops** | 3.4 | 5 real + 4 ghosts | dspy+obliteratus+weights-and-biases push average up; huggingface-hub drags it down |
| **productivity** | 3.0 | 10 | Widest spread: powerpoint(4.2) to nano-pdf(1.2). Bimodal distribution confirmed. |
| **finance** | 3.2 | 1 | quant-finance: strong methodology but lacks automated validation |
| **media** | 2.4 | 5 | Structural ceiling: no media skill scores above observability=3 or optimization=3 |
| **email** | 2.5 | 1 | himalaya: solid CRUD, no automated verification |
| **social-media** | 2.8 | 1 | xurl: excellent stability (4), weak closure (3) |
| **smart-home** | 1.5 | 1 | openhue: pure CLI wrapper |
| **note-taking** | 1.5 | 1 | obsidian: filesystem operations guide |

## Pattern 3: Media Category — The Structural Observability Ceiling (Confirmed)

Same pattern as 2026-07-14 audit but with different skills: all 5 media skills (gif-search, heartmula, songsee, spotify, youtube-content) cap at observability=3 and optimization≤3. The root cause is unchanged: media generation quality requires HUMAN sensory judgment (is the song good? does the GIF match intent?). No programmatic quality metric exists in these skills' workflows.

**New observation in this audit**: spotify is the exception to the media pattern — it HAS structured observability (7 Hermes toolset tools returning JSON) and canonical patterns minimizing tool calls (optimization=3). It's the only media skill with a feedback loop (play → get_currently_playing → verify). Still capped at cross_domain=2 due to platform binding.

## Pattern 4: Productivity Category — Bimodal Distribution Strengthened

| Cluster | Skills | Avg closure | Pattern |
|---------|--------|-------------|---------|
| **Methodology cluster** (4 skills) | powerpoint, teach, teams-meeting-pipeline, ocr-and-documents | 4.25 | Explicit verification loops: subagent fresh eyes QA, quiz feedback, validate→token-health, tool-selection decision tree |
| **API/CRUD cluster** (4 skills) | airtable, google-workspace, linear, notion | 4.0 (stability/observability) but **2.5 (optimization)** | Excellent API documentation with structured JSON output and error handling, but optimized for human operator, not automated agent. These skills are API reference manuals dressed as skills. |
| **Tool manual cluster** (2 skills) | nano-pdf, maps | 1.7 | Minimal CLI wrappers. maps is the stronger of the two (8 commands, 46 categories, built-in verification) but still lacks automated feedback. |

**Key insight**: The "API/CRUD cluster" is the productivity category's unique contribution — these skills score high on stability (4.0 avg) and observability (4.0 avg) but low on closure (3.5 avg) and optimization (2.5 avg). They're well-documented API bindings that assume a human will interpret JSON output — no automated action-gating. This is distinct from the "tool manual cluster" which lacks even structured output.

## Pattern 5: dspy and teach — The Cross-Domain Twin Peaks

Only two skills in the entire group achieve cross_domain=5:
- **dspy** (mlops/research): declarative LM programming methodology — applicable to any LLM task from QA to RAG to classification
- **teach** (productivity): ZPD-based adaptive teaching framework — works for programming, yoga, physics, any knowledge domain

Both share a common architecture: abstract interface (Signature/Lesson) → concrete implementation → evaluation → optimization. The pattern is: define the class of problem, build a solution instance, measure outcomes, adapt. This is the cybernetics loop at the methodology level.

## Pattern 6: The Optimization Trinity

Three skills scored optimization=5: **dspy**, **weights-and-biases**, **godmode**. They share a structure:
- dspy: automatic prompt optimization (BootstrapFewShot, MIPRO, Bayesian) — the entire skill IS about optimization
- weights-and-biases: automated hyperparameter sweeps (bayes/grid/random) + model registry — optimization-as-a-service
- godmode: auto-jailbreak with per-model strategy ordering + Parseltongue tier escalation + ULTRAPLINIAN multi-model racing — meta-optimization over jailbreak techniques

The common DNA: **treat the task as an optimization problem** and build automated search over the solution space. These aren't skills that "do X" — they're skills that "find the best way to do X given constraints."

## Pattern 7: Tool Manual Bias — Quantitative Confirmation

14 of 30 real skills (47%) score closure≤2 or cross_domain≤1. These are thin CLI/API wrappers: gif-search, songsee, nano-pdf, openhue, obsidian, huggingface-hub, etc. They're not "bad skills" — they're command references that happen to be stored as skills. The scoring framework penalizes them because it was designed for methodology skills.

**Proposal from group2-audit-patterns.md still stands**: add a `tool_manual: true` flag to the JSON schema. Tool manuals should be scored on accuracy, completeness, and clarity — not on closure or optimization. Without this flag, ~half the skills in every grouping will appear as "low quality" when they're actually serving their intended purpose well.

## Pattern 8: Ghost Skill Stability — 4 Persistent Ghosts

Same 4 ghosts as every audit since May 2026: `audiocraft-audio-generation`, `evaluating-llms-harness`, `segment-anything-model`, `serving-llms-vllm`. All are in the mlops category (models/evaluation/inference subdirectories). Recommendation unchanged: either implement or remove from catalog. Each audit wastes 4 `skill_view()` calls + 4 `search_files` verifications on these.

## Pattern 9: Scoring Methodology Variance Between Audits

This audit (2026-07-17) produced higher closure and observability scores than the 2026-07-14 audit. The difference is NOT the skills — it's the scoring criteria:

| Dimension | 2026-07-14 Interpretation | 2026-07-17 Interpretation |
|-----------|--------------------------|---------------------------|
| closure=5 | Fully automated gating (no human in loop) | Structured verification with quantitative metrics + explicit fix loop, human-in-the-loop acceptable |
| observability=5 | Fully automated monitoring with alerting | Structured metrics output + monitoring hooks, human-interpretable acceptable |

Both interpretations align with Principle 1 (实践-理论-实践循环) and Principle 6 (反馈闭环). The 2026-07-14 interpretation is stricter ("feedback must be fully automated"). The 2026-07-17 interpretation accepts that human-in-the-loop verification IS a feedback loop for agent-driven workflows where the agent reads its own output. Future audits should **state which interpretation is used** at the top of the report to enable cross-audit comparison.

## Pattern 10: Write-File False Positive in Cron Context

When running as a scheduled cron job, `write_file` to `~/.hermes/skills/reports/cybernetics_group3.json` triggered the "modified by sibling subagent" warning. This was a **false positive** — the current cron job was the only writer. The warning appears because a previous cron run wrote to the same path. Mitigation: always verify file integrity after write (terminal + python3 json.load check). This is now documented in the SKILL.md pitfalls.
