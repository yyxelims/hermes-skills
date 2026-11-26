# Paper Reading Workflow — Proven Pattern

This document captures the complete workflow for teaching academic papers, refined across multiple sessions.

## Step 1: Paper Discovery & Confirmation

**User may describe papers imprecisely.** They might use nicknames, rough keywords, or partial titles. Do NOT guess — search and confirm.

Search sources (in order):
1. **arXiv API**: `http://export.arxiv.org/api/query?search_query=all:<keywords>&max_results=8&sortBy=submittedDate`
2. **arXiv ID lookup**: `http://export.arxiv.org/api/query?id_list=<arxiv_id>` — use this to fetch full metadata once you have the ID
3. **AI HOT** (`aihot` skill): for recent context and Chinese-language discussions. API: `https://aihot.virxact.com/api/public/items?q=<keyword>` (must set browser UA)

**Pitfall**: arXiv search returns fuzzy matches. Always present the top candidates and ask the user to confirm before proceeding.

## Step 2: Workspace Setup

Create under `~/Documents/本地/ai探索/paper-study/` (or user-specified path):

```
workspace/
├── MISSION.md              # Why learning these papers
├── RESOURCES.md            # Paper list + supplementary reading
├── NOTES.md                # User preferences, teaching style
├── learning-records/       # One .md per insight gained
└── lessons/                # Sequentially numbered HTML files
```

## Step 3: User Preferences for Lessons

- **Language**: Chinese teaching, English terms kept as-is
- **Style**: Direct, efficient. No padding. Lead with the big insight.
- **Theme**: Light background, Noto Sans SC, card-based layout
- **Lesson duration**: 12-18 minutes reading time
- **Quiz**: 3-5 self-test questions per lesson. Answers provided on request — don't make them wait.
- **Deep questions welcome**: User engages strongly with philosophical cross-paper connections and human vs AI learning comparisons. Include open-ended thinking questions.

## Step 4: Lesson Sequence for Papers

| Lesson | Focus |
|--------|-------|
| 0001 | Big picture intuition — "why this matters". Use analogies. Include quiz. |
| 0002 | Architecture / method details. How does it actually work? |
| 0003 | Experimental results. What did they test and how did it perform? |
| 0004+ | Cross-paper synthesis, connections, implications |

## Step 5: Proven Lesson Patterns

### The "LLM Analogy" Pattern
When teaching AI/ML concepts, always use the LLM (GPT/Claude) analogy:
- "This is just like how GPT predicted next token → emerged reasoning"
- "Same pattern: generative pretraining → emergent understanding"

### The "Human vs AI Learning" Pattern
User responds strongly to comparisons between human and AI learning:
- "Human babies: comprehension before production. AI: production before comprehension."
- These can become deep philosophical discussions. Encourage them.

### The "Dual Insight Connection" Pattern
When teaching multiple papers, find the meta-pattern that connects them:
- Vision Banana + KDA: "both show that generation/error-correction is more fundamental than the target capability"

### The "Quiz → Answer → Deep Thoughts" Pattern
- Ask quiz questions at end of each lesson
- When user asks for answers, provide immediately with full explanations
- For open-ended questions, provide multi-layered analysis (surface answer + deeper implications)

## Step 6: Common Pitfalls

- **Don't start with equations.** Even for math-heavy papers, lead with intuition first.
- **Don't forget to record.** After each lesson, write a learning record.
- **Don't skip the cross-paper synthesis.** User values seeing the big picture.
- **Don't make quiz answers "wait for next lesson".** Provide immediately on request.
- **Don't assume the user knows related work.** If a paper builds on InstructCV, DeltaNet, Mamba, etc., briefly explain the prerequisite.
