# Learning Record Format

Learning records live in `./learning-records/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc. Create the directory lazily — only when the first record is written.

They are the teaching equivalent of ADRs: they capture non-obvious lessons, key insights, and stated prior knowledge that will steer future sessions.

## Template

```md
# {Short title of what was learned or established}

{1-3 sentences: what was learned, and why it matters for future sessions.}
```

## Optional sections

- **Status** frontmatter (`active | superseded by LR-NNNN`)
- **Evidence** — how the user demonstrated the understanding
- **Implications** — what this unlocks or rules out for future sessions

## When to write a learning record

1. The user demonstrates they've learned something non-obvious
2. The user states prior knowledge that changes the teaching plan
3. You discover a gap or misconception that reshapes upcoming lessons
4. A lesson produces an unexpected insight worth capturing

Do NOT write a record simply to log that a lesson was completed.
