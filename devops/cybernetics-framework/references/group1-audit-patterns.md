# Group 1 Audit Patterns (latest: 2026-08-06)

Cross-skill patterns discovered during the 36-skill Group 1 audits. **Re-audited 2026-07-28** — fifth consecutive audit (prior: 07-09, 07-14, 07-16, 07-21). Scores showed a **notable upward shift** across all dimensions this audit, attributed to auditor calibration differences (model: `deepseek-v4-pro` via cron job with no user interaction).

## Dimension Score Distribution (2026-07-28)

| Dimension | Avg | Min | Max | Δ vs 07-21 |
|-----------|-----|-----|-----|-------------|
| closure | 3.46 | 0 | 5 | +0.29 |
| stability | 3.71 | 0 | 5 | +0.32 |
| observability | 2.97 | 0 | 5 | +0.03 |
| optimization | 3.40 | 0 | 5 | +0.15 |
| cross_domain | 3.03 | 0 | 5 | +0.39 |
| **OVERALL** | **3.31** | — | — | — |

**2026-07-21 (prior audit) for reference:**

| Dimension | Avg |
|-----------|-----|
| closure | 3.17 |
| stability | 3.39 |
| observability | 2.94 |
| optimization | 3.25 |
| cross_domain | 2.64 |

**Key finding (07-28)**: Cross-domain saw the largest relative jump (+0.39, from 2.64 to 3.03), passing the 3.0 threshold for the first time. Observability barely changed (+0.03) — it remains the weakest dimension across all audits, confirming it's the hardest aspect to improve. Stability remains the strongest dimension (3.71). The **overall average of 3.31** is a new high for Group 1.

## Pattern 1: Tool-Manual Skills (thin CLI wrappers)

Skills that are essentially CLI reference manuals with no verification loops. **07-28 audit: yuanbao is the weakest skill in Group 1 (composite=7, avg=1.4).** The bottom-5 cluster is dominated by Apple ecosystem wrappers:

| Rank | Skill | Composite | Avg |
|------|-------|-----------|-----|
| 31 | blogwatcher | 11 | 2.2 |
| 32 | imessage | 10 | 2.0 |
| 33 | apple-reminders | 9 | 1.8 |
| 34 | apple-notes | 8 | 1.6 |
| 35 | yuanbao | 7 | 1.4 |

These skills cluster at closure=2 and stability=2-3. They're not "bad" — they serve as tool references — but they lack the verification loops that distinguish class-level skills from command cheat sheets. **07-28 note**: `arxiv` and `polymarket` were scored higher this audit (closure=3 and closure=2 respectively) — `arxiv` benefits from its multi-API research workflow integration, pulling it out of the tool-manual cluster.

**Recommendation**: Consider merging related tool-manual skills into broader umbrella skills with verification patterns. E.g., apple-notes + apple-reminders + imessage + findmy → a unified "macos-apps" skill with JSON parsing and error recovery.

## Pattern 2: Gold-Standard Skills (composite ≥20)

**2026-07-28 top-5** (composite = closure+stability+observability+optimization+cross_domain):

| Rank | Skill | Composite | Avg | Key traits |
|------|-------|-----------|-----|------------|
| 1 | touchdesigner-mcp | 23 | 4.6 | 5/5/5/5/3 — CRITICAL RULES, 36 MCP tools, proven audio recipe |
| 2 | llm-wiki | 23 | 4.6 | 5/4/4/5/5 — 12-point lint, SHA256 drift, contradictions, bulk ingest |
| 3 | research-paper-writing | 23 | 4.6 | 5/5/4/5/4 — 2,377-line full research lifecycle |
| 4 | comfyui | 21 | 4.2 | 5/5/4/4/3 — health_check→auto_fix_deps→run→verify loop |
| 5 | design-md | 20 | 4.0 | 4/4/4/4/4 — automated lint/diff/WCAG/export pipeline |

**Shift from 07-21**: `design-md` entered top-5 (replacing `dogfood` and `byted-supabase`, which now score at composite 18 and 16 respectively in this audit's calibration). `byted-supabase` dropped from the gold-standard cluster due to its platform-specific nature (cross_domain=2) — its operational excellence was previously given more weight.

**Common traits of gold-standard skills**:
1. Explicit verification step in the workflow (not just "user checks manually")
2. Structured error classification (pitfalls section with specific error→remedy mappings)
3. Programmable observability (JSON output, health checks, error codes — not just terminal text)
4. Fallback chains (multi-method with automatic degradation)
5. "Critical rules" or "core principles" section that encodes non-negotiable constraints

## Pattern 3: Oversized Skills (loading cost)

- **research-paper-writing** (107KB, 2,378 lines): Returned as `<persisted-output>` by skill_view(), requiring read_file with offset for full audit. The SKILL.md is 5x the typical size — it covers the full paper lifecycle in one file.
- **p5js**: Extremely long SKILL.md with 10 reference files. High load cost even when only a subset is needed.
- **baoyu-comic**: Long but well-structured with clear step numbering — the progress checklist helps navigation.

**Recommendation**: Skills exceeding ~50KB should consider:
- Splitting into a core SKILL.md (workflow overview + quick start) + phase-specific sub-skills
- Lazy-loading references only when needed
- Providing a "quick start" section at the top for common cases

## Pattern 4: Observability Gap — "User Opens in Browser"

A recurring anti-pattern across creative skills: the verification step is "user opens the file in a browser and looks at it." This audit confirmed the pattern persists across all 4 runs:

Affected skills: architecture-diagram, excalidraw, ascii-art, ascii-video (partial), manim-video (partial), p5js (partial), sketch (partial), pretext (partial), pixel-art (partial).

**07-21 update**: Notably, `sketch` partially addresses this by using browser_vision for visual verification — but it's still human-in-the-loop. No creative skill has achieved automated visual quality gates.

These skills could benefit from:
- Automated screenshot + vision analysis for visual verification
- JSON schema validation for structured formats (excalidraw)
- CSS/HTML linting for web outputs (architecture-diagram, sketch)
- Frame-level brightness checks (already in ascii-video, should be generalized)
- Color palette validation against WCAG contrast requirements

## Pattern 5: Ghost Skill Confirmation

`ideation` confirmed as ghost skill for the **15th** consecutive audit (2026-07-29). Already listed in persistent ghost skill list; no change needed but the count continues to grow. This is the single most-verified ghost skill across all audits. **All other Group 1 skills loaded successfully** — no new ghosts or ambiguous duplicates found this audit (07-29).

## Pattern 6: Creative Skills — High Creative Bar, Low Verification

Many creative skills (ascii-video, manim-video, p5js, baoyu-comic, baoyu-infographic, songwriting-and-ai-music) have excellent creative direction sections but lack automated quality verification. The "first-render excellence is non-negotiable" principle in ascii-video, manim-video, and p5js is aspirational — without automated checks, it's a hope, not a guarantee.

**07-21 update**: `baoyu-comic` scored closure=4, the highest among creative skills — its 8-step workflow with 2 user confirmation gates and progress checklist is the best in the creative cluster. `baoyu-infographic` scored closure=3 — slightly lower due to fewer verification gates.

**Recommendation**: Creative skills should add at minimum:
1. Output file existence check (already common)
2. File size sanity check (>0 bytes, >minimum expected size)
3. Format validation (ffprobe for video, JSON parse for structured formats, PNG header check for images)
4. Vision-based quality check for visual outputs (browser_vision or equivalent)

## Pattern 7: Domain-Specific Binding

Skills scoring low on cross_domain because they're tightly bound to a specific tool or API:

- **pretext**: Bound to @chenglou/pretext library (single npm package, cross_domain=3)
- **pixel-art**: Bound to specific image processing pipeline (cross_domain=3)
- **excalidraw**: Bound to Excalidraw JSON format (cross_domain=2)
- **polymarket**: Bound to Polymarket API (cross_domain=2)
- **baidu-ai-search**: Bound to Baidu Qianfan API (cross_domain=2)
- **aihot**: Bound to aihot.virxact.com (cross_domain=2)
- **blogwatcher**: Bound to blogwatcher-cli (cross_domain=1)

These skills could be strengthened by documenting the general pattern (e.g., "REST API query pattern" in polymarket, "image quantization+dithering pattern" in pixel-art, "RSS feed monitoring pattern" in blogwatcher).

## Pattern 8: Re-Audit Stability Signal

Five audit runs (07-09, 07-14, 07-16, 07-21, 07-28) over the same 36 skills show both consistency AND drift:

**Consistent findings** (stable across all 5 audits):
- **Gold standards** (touchdesigner-mcp, llm-wiki, research-paper-writing, comfyui) maintain top-tier positions. 3 of 4 hold the exact same composite=23 score as 07-21.
- **Tool-manual cluster** (apple-*, yuanbao, blogwatcher) remains at composite 7-11 across all audits.
- **ghost skill ideation** confirmed absent in all 5 audits (now 13th confirmation).
- **pixel-art ambiguous duplicate** confirmed in 3 of 5 audits.
- **research-paper-writing truncation** (>100KB) confirmed across all audits — always requires secondary read_file.

**Calibration drift (07-28 vs 07-21)**: All dimension averages shifted upward by 0.03–0.39. This is likely auditor calibration rather than skill improvement — the same skills assessed with a slightly more generous interpretation of "what counts as observable" or "what qualifies as cross-domain transferable." Key examples:
- `popular-web-designs` moved from cross_domain=1 to cross_domain=2 — 07-28 auditor considered "design system catalog as pattern library" as domain-transferable.
- `yuanbao` remained at composite=7 — the floor is stable; the ceiling shifted up.
- Observability barely moved (+0.03) — this dimension has the tightest inter-auditor agreement because it has the most concrete criteria (JSON output, structured logs, health checks).

**Implication**: The scoring methodology measures real skill characteristics, but absolute scores carry ±0.3 auditor calibration bias. Rankings and relative tiers are more reliable than absolute dimension scores for cross-audit comparison.

## Pattern 9: Execution Notes (08-06)

The 08-06 audit used `deepseek-v4-pro` via cron job (no user interaction). Full Group 1 scope (36 skills: apple ×5, autonomous-ai-agents ×4, creative ×18, uncategorized ×7, ghost ×1, ie. `ideation`). All skills loaded via sequential `skill_view()` in batches of 8 (slightly above the recommended 5 per turn, but successful). JSON written directly via `write_file` (29KB, 36 entries) — no truncation. Verified with `terminal` + inline `python3 -c`.

**Dimension averages (08-06)**:

| Dimension | Avg | vs 07-29 |
|-----------|-----|----------|
| closure | 3.44 | -0.06 |
| stability | 3.33 | -0.17 |
| observability | 3.25 | +0.15 |
| optimization | 3.19 | -0.01 |
| cross_domain | 2.69 | +0.29 |
| **OVERALL** | **3.18** | +0.04 |

**Key shifts from 07-29**: cross_domain rebounded +0.29 (from 2.40 to 2.69), partially recovering from 07-29's sharp drop. Observability continued its steady upward trend (+0.15, now at 3.25 vs 2.94 in 07-09). Stability and closure both declined slightly — the 08-06 auditor was more conservative on error-handling presence (several skills got stability=2 that previously scored 3).

**Top skills (08-06, composite ≥21)**:
| Rank | Skill | Composite | Dimensions |
|------|-------|-----------|------------|
| 1 | comfyui | 23 | c5 s5 o5 p5 x3 |
| 1 | neat-freak | 23 | c5 s4 o4 p5 x5 |
| 3 | claude-code | 22 | c4 s5 o5 p5 x3 |
| 4 | baoyu-comic | 21 | c5 s4 o4 p4 x4 |
| 4 | touchdesigner-mcp | 21 | c5 s5 o5 p4 x2 |

**Notable**: `neat-freak` tied `comfyui` at 23 — both achieve closure=5, but neat-freak earns cross_domain=5 as a pure methodology skill while comfyui is tool-bound. `baoyu-comic` entered top-5 for the first time (closure=5 workflow with backup rules + CWD drift pitfall). `hatch-pet` dropped from 07-29's top-5 — cross_domain=2 (Codex pet format binding) pulled its composite down.

**Bottom-5 (excl ghost, composite ≤10)**: apple-notes (8), yuanbao (8), apple-reminders (9), imessage (10), ascii-art (10). Same cluster as all prior audits — these are pure tool manuals with no verification loops.

**Ghost skill**: `ideation` confirmed absent — **19th** consecutive confirmation (now the single most-verified ghost skill across all audit groups).

**Execution reliability**:
1. All 36 skills loaded and scored in a single sequential pass — no `delegate_task` needed. Single-session sequential audit at ~36 skills is efficient; 8-per-turn batching works.
2. `write_file` for direct JSON (29KB) produced valid output, verified by Python re-read.
3. `sibling subagent warning` (sa-0-7eeaec90) received — known false positive from prior cron run, verified 36 entries with zero corruption.
4. Score distribution shows clear three-tier structure: gold-standard (composite ≥19), mid-range methodology (13-18), tool-manual cluster (8-10).

## Pattern 9: Execution Notes (07-29)

The 07-29 audit used `deepseek-v4-pro` via cron job (no user interaction). Same Group 1 scope (34 skills: apple ×5, autonomous-ai-agents ×4, creative ×18, uncategorized ×7). 34 entries (33 active + 1 ghost `ideation`). JSON written directly via `write_file` (35KB) — **no truncation or entry loss observed**, consistent with 07-28's finding that `write_file` for JSON is reliable.

**Dimension averages (07-29)**:

| Dimension | Avg | vs 07-28 |
|-----------|-----|----------|
| closure | 3.5 | +0.04 |
| stability | 3.5 | -0.21 |
| observability | 3.1 | +0.13 |
| optimization | 3.2 | -0.20 |
| cross_domain | 2.4 | -0.63 |
| **OVERALL** | **3.14** | -0.17 |

**Key: cross_domain dropped sharply** — the 07-29 auditor was more conservative. `claude-design` got cross_domain=5 (design methodology fully transferable), but most creative skills scored 2. `humanizer` and `neat-freak` scored cross_domain=5 (methodology is domain-agnostic). The 07-28 cross_domain uplift appears to have been auditor calibration rather than genuine improvement.

**Stability/optimization reverted to near-07-21 levels**, suggesting the 07-28 scores had auditor leniency. Observability remained the weakest non-ghost dimension but showed steady improvement across runs (2.94→2.97→3.10).

**Top skills (07-29, composite ≥20)**: `comfyui` (23), `hatch-pet` (22), `neat-freak` (21), `claude-code` (21), `touchdesigner-mcp` (21), `hermes-agent` (19).

**Reliability**: `write_file` with `sibling subagent warning` (sa-0-9e98c167) — false positive from prior cron run. Verified 34 entries, zero corruption.

## Pattern 9: Execution Notes (07-28)

The 07-28 audit used `deepseek-v4-pro` via cron job (no user interaction). Skills loaded sequentially in batches of 5-6 parallel `skill_view()` calls (36 total). JSON written directly via `write_file` (37KB, 36 entries) — **no truncation or entry loss observed.** Statistics computed via `terminal` + inline `python3 -c` after the write.

**Key reliability findings**:
1. `write_file` for direct JSON output (37KB) works reliably — the earlier "trap C" (silent entry loss) only affects Python source files, not JSON payloads.
2. The `sibling subagent warning` ("file was modified by sibling subagent 'sa-0-f82c71b7'") is a known false positive from prior cron runs — file integrity verified via Python re-read + entry count check.
3. `research-paper-writing` triggered `<persisted-output>` truncation (107KB) — resolved with `read_file(limit=150)` on SKILL.md directly. The skill's frontmatter and Phase 0-3 content sufficed for scoring.
4. Score computation was verified by a terminal Python script that confirmed 35 active + 1 ghost entries, computed dimension averages, and identified top/bottom clusters.

## Edge Case: `write_file` Sibling Subagent Warning

Writing `cybernetics_group1.json` triggered: `"file was modified by sibling subagent 'sa-0-242eb601' but this agent never read it"`. Root cause: prior cron job or leftover subagent process. Mitigation: verify content with `python3 -c "import json; ..."` before trusting the file, don't re-write without reading first. First documented 07-14, confirmed 07-21.
