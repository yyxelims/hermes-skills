---
name: skill-export
description: Package Hermes skills to a portable .md/.txt format.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skill, export, packaging, portable, meta]
    related_skills: [skill-creator]
---

# Skill Export / Packaging

Flatten existing Hermes skills into a self-contained portable format so they can be
moved to another folder, machine, or shared as plain text — no Hermes install required.

## When to Use

- User says "包装成 XX 格式的技能", "导出技能", "把技能放到某文件夹", "package these skills".
- User wants skills as plain `.md`/`.txt` files carrying name + description + Instructions.
- User wants "依赖少" skills — prefer ones whose value is the method/instructions themselves.

## Portable Format (per skill)

```
<skill-id>

name: <skill-id>
description: <one-line description>

## Instructions

<full body — code examples preserved verbatim>
```

Rules learned from the user:
- File name = skill ID; write BOTH `.md` and `.txt` with identical content.
- Keep code (JSON/HTML/bash/pytest snippets) inside the body verbatim — "如果有代码，就把代码也复制进去".
- Drop frontmatter metadata (version/author/license/tags) — keep only `name:` + `description:`.
- Drop the body's leading `# Title` heading (redundant with the `name:` field).

## Workflow

1. Read each source `SKILL.md`.
2. Parse the YAML frontmatter with a regex, not a YAML lib — the flat `key: value` shape
   is all that's needed: `^---\n(.*?)\n---\n(.*)$` → frontmatter + body.
3. Extract `name:` and `description:` (strip surrounding quotes).
4. Strip the leading `# Title` heading from the body.
5. Assemble `<id>\n\nname: …\ndescription: …\n\n## Instructions\n\n<body>` and write
   `<id>.md` + `<id>.txt`.

Ready-made script: `scripts/pack_skills_to_portable.py` (stdlib only).

```bash
python3 scripts/pack_skills_to_portable.py OUTDIR SKILL.md [SKILL.md ...]
# pack every SKILL.md under a skills tree:
find ~/.hermes/skills -name SKILL.md > /tmp/list.txt
python3 scripts/pack_skills_to_portable.py OUTDIR $(cat /tmp/list.txt)
```

## Pitfalls

- "依赖少" ≠ "no code": prefer pure-instruction skills (ponytail, grill-me,
  systematic-debugging, spike, writing-plans, test-driven-development) and output skills
  that only hand-write JSON/HTML (excalidraw, architecture-diagram). Skip skills whose
  value depends on a third-party CLI/lib.
- For a batch transform across many files, write a small stdlib Python script to a file
  and run it via `terminal` — this avoids per-file manual transcription and doesn't wait
  on interactive approval.
- The output folder may be on an external volume (e.g. `/Volumes/TSU303`); confirm it
  exists and is writable before writing. A folder outside the workspace still accepts
  plain `write_file`/`terminal` writes.
- Verify by listing the output dir and reading one file back — check the format matches
  (ID on first line, then `name:`/`description:`, then `## Instructions`).
