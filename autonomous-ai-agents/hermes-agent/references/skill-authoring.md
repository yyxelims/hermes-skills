# Authoring Hermes-Agent Skills (in-repo)

## Overview

Two places SKILL.md can live:
1. **User-local:** `~/.hermes/skills/<category>/<name>/SKILL.md` — personal. Created via `skill_manage(action='create')`.
2. **In-repo:** `<repo>/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`.

## Required Frontmatter

- Starts with `---` as first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- `name` field present.
- `description` field present, ≤ **1024 chars**.
- Non-empty body after closing `---`.

Peer-matched shape:
```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (~36k tokens).
- Peer skills sit at **8-14k chars**. Push past 20k → split into `references/*.md`.

## Peer-Matched Structure

```
# <Title>
## Overview — what and why
## When to Use — bulleted triggers + counter-triggers
## <Topic sections> — quick-reference tables, code blocks, recipes
## Common Pitfalls — numbered list of mistakes and fixes
## Verification Checklist — post-action checkboxes
```

## Directory Placement

`skills/<category>/<skill-name>/SKILL.md`

Categories: `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `media`, `mcp`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

## Workflow

1. Survey peers in target category: `ls skills/<category>/`
2. Draft with `write_file` to `skills/<category>/<name>/SKILL.md`
3. Validate frontmatter + size limits
4. `git add skills/<category>/<name>/ && git commit`
5. Note: current session's skill loader is cached — new skill won't appear until next session.

## Common Pitfalls

1. Using `skill_manage(action='create')` for in-repo skill — writes to `~/.hermes/skills/`, not repo.
2. Leading whitespace before `---` — validator checks `content.startswith("---")`.
3. Description too generic — start with "Use when ...".
4. Forgetting `author/license/metadata` block — not enforced but every peer has it.
5. Duplicating a peer — prefer extending an existing skill.
6. Expecting current session to see new skill — loader initialized at session start.
7. Linking to user-local skills from in-repo — breaks for other clones.
