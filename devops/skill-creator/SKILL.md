---
name: skill-creator
description: >
  Create, modify, and improve skills. Use this when the user wants to capture a workflow
  as a reusable skill, create a skill from scratch, edit or optimize an existing skill,
  or when the user says "turn this into a skill", "remember this workflow", "save as skill".
  Triggers on: "create a skill", "make a skill for", "turn into skill", "save workflow",
  "skill template".
tags: [skill, workflow, automation, meta]
---

# Skill Creator

Create and iteratively improve skills for the Hermes Agent system.

## When to Create a Skill

Create a skill when:
- A complex task succeeded (5+ tool calls) and you learned a reusable pattern
- You overcame errors and discovered pitfalls worth documenting
- A workflow was user-corrected and the corrected approach should be remembered
- A non-trivial workflow was discovered that will be used again
- The user explicitly asks you to save something as a skill

Do NOT create skills for:
- Simple one-off tasks
- Trivially obvious workflows
- Things easily discovered by reading documentation

## Skill Creation Process

### 1. Capture Intent
- What should this skill enable the agent to do?
- When should it trigger? (what user phrases/contexts)
- What's the expected output format?
- What tools are needed?

### 2. Document the Workflow
- Numbered steps with exact commands
- Expected inputs and outputs for each step
- Decision points and branches
- Verification steps (how to know it worked)

### 3. Add Pitfalls
- What went wrong during development?
- What errors were encountered and how were they fixed?
- OS-specific issues
- Common mistakes to avoid

### 4. Structure
```markdown
---
name: skill-name
description: When to trigger + what it does (be slightly pushy to avoid under-triggering)
tags: [relevant, tags]
---

# Skill Title

## When to Use
(optional - if description is not enough)

## Workflow
### Step 1: ...
### Step 2: ...

## Pitfalls
- Pitfall 1
- Pitfall 2

## Grouped Audit JSON Workflow
When maintaining a multi-file skill audit, treat the latest complete audit JSON as the authoritative inventory. Before writing a group file:
1. Load the existing group JSON files and collect their skill names.
2. Compute the set difference against the authoritative inventory; do not infer omissions from filenames or broad filesystem searches.
3. Preserve each audit record unchanged when assigning it to the new group; group files are partitions, not rewritten summaries.
4. Write valid UTF-8 JSON and immediately re-parse it, checking record count and names.
5. Report the absolute output path, count, and validation result.

Pitfall: broad searches from the home directory can time out or scan protected/system files. Prefer known plan directories and exact filenames. Also distinguish genuinely missing skills from names present in a prior audit but absent from the current installed inventory.

## Verification
- How to confirm the result is correct
```

### 5. Iterate
- After using the skill, if it's outdated or wrong, patch it immediately with `skill_manage(action='patch')`
- Skills that aren't maintained become liabilities

## Skill Writing Tips

- **Description is the trigger**: Include both what the skill does AND when to use it. Be slightly "pushy" to avoid under-triggering.
- **Keep it compact**: Skills are injected into context. Every token matters.
- **Numbered steps > prose**: Agents follow numbered instructions better than paragraphs.
- **Pitfalls section is mandatory**: The most valuable part of a skill is what NOT to do.
