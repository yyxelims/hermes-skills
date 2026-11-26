---
name: teach
description: Teach the user a new skill or concept, within this workspace. Use when the user says "teach me", "I want to learn", "show me how to", "help me understand", or any learning request.
argument-hint: "What would you like to learn about?"
---

The user has asked you to teach them something. This is a stateful request - they intend to learn the topic over multiple sessions.

## Teaching Workspace

Treat the current directory as a teaching workspace. The state of their learning is captured in this directory in several files:

- `MISSION.md`: A document capturing the _reason_ the user is interested in the topic. This should be used to ground all teaching. Use the format in [MISSION-FORMAT.md](./MISSION-FORMAT.md).
- `./reference/*.html`: A directory of reference materials. These are the compressed learnings from the lessons - cheat sheets, reference algorithms, syntax, yoga poses, glossaries. They are the raw units of learning. They should be beautiful documents which print out well, and are designed for quick reference.
- `RESOURCES.md`: A list of resources which can be explored to ground your teaching in contextual knowledge, or to acquire knowledge and wisdom. Use the format in [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md).
- `./learning-records/*.md`: A directory of learning records, which capture what the user has learned. These are loosely equivalent to architectural decision records in software development - they capture non-obvious lessons and key insights that may need to be revised later, or drive future sessions. These should be used to calculate the zone of proximal development. They are titled `0001-<dash-case-name>.md`, where the number increments each time. Use the format in [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md).
- `./lessons/*.html`: A directory of lessons. A **lesson** is a single, self-contained HTML output that teaches one tightly-scoped thing tied to the mission. This is the primary unit of teaching in this workspace.
- `NOTES.md`: A scratchpad for you to jot down user preferences, or working notes.

## Philosophy

To learn at a deep level, the user needs three things:

- **Knowledge**, captured from high-quality, high-trust resources
- **Skills**, acquired through highly-relevant interactive lessons devised by you, based on the knowledge
- **Wisdom**, which comes from interacting with other learners and practitioners

Before the `RESOURCES.md` is well-populated, your focus should be to find high-quality resources which will help the user acquire knowledge. Never trust your parametric knowledge.

Some topics may require more skills than knowledge. Learning more about theoretical physics might be more knowledge-based. For yoga, more skills-based. For academic paper comprehension, see `references/paper-reading-pattern.md` for the proven lesson structure and user preferences.

## Lessons

A lesson is the main thing you produce — the unit in which knowledge and skills reach the user. Each lesson is one self-contained HTML file, saved to `./lessons/` and titled `0001-<dash-case-name>.html` where the number increments each time.

**Use the lesson HTML template at [lesson-html-template.html](./lesson-html-template.html).** It provides a proven, beautiful layout: light theme, Noto Sans SC, card-based sections, analogy grids, flow diagrams, quiz boxes, and stat highlights. The user has confirmed this style works well. Start from the template and adapt the sections to the lesson content — don't redesign from scratch.

A lesson should be **beautiful** — clean, readable typography and layout — since the user will return to these later to review.
The lesson should teach ONE THING only. It should be completable very quickly - but give the user a tangible win that they can build on. It should be directly tied to the mission, and should be in the user's zone of proximal development.

Make opening a lesson as easy as possible — ideally a single CLI command the user can run to open the HTML file in their browser.

Each lesson should link via HTML anchors to other lessons and reference documents.

**Lesson HTML Template**: A battle-tested template with common patterns (insight cards, comparisons, flow diagrams, stat boxes, quizzes) is available at [templates/lesson-html-template.html](./templates/lesson-html-template.html). Use it as a starting point — it has all CSS and reusable component patterns built in.

**Proven lesson patterns**:
- **Intuition-first**: Start with the core question and an intuitive answer, then layer on technical detail. Never lead with equations.
- **LLM analogy**: When teaching AI/ML concepts, use the LLM (GPT/Claude) analogy heavily — users already have a strong mental model there.
- **Quiz-driven**: End every lesson with 3-4 self-test questions. Users should answer these before moving to the next lesson.
- **Cross-paper connections**: When teaching multiple papers in sequence, include a "共鸣" (resonance) section that links insights across papers. Users deeply value these meta-level connections.
- **Human vs AI comparisons**: Users respond strongly to comparisons between how humans learn and how AI learns. Include these when relevant.

### Paper-Reading Workflow

When the user wants to learn from academic papers, follow this sequence:

1. **Confirm the papers.** The user may describe papers by rough keywords, nicknames, or partial titles. Search arXiv (`http://export.arxiv.org/api/query?search_query=...`) to find the exact paper, verify the title, and confirm with the user before creating lessons. AI HOT (`aihot` skill) can supplement with recent context.
2. **Fetch full metadata.** Use `id_list=` to get the complete abstract, authors, and publication date.
3. **Set up the workspace.** Create `MISSION.md`, `RESOURCES.md` (list the papers + supplementary reading), and `NOTES.md`.
4. **Teach the big picture first (Lesson 0001).** Give the intuitive "why this matters" before diving into methods. Use analogies. Include a self-test quiz.
5. **Go deeper in subsequent lessons.** Lesson 0002 can cover architecture/methods, 0003 experimental details, etc.
6. **Record learning after each lesson.** Write a `learning-records/` entry capturing the key insight gained.

## The Mission

Every lesson should be tied into the mission - the reason that the user is interested in learning about the topic.

If the user is unclear about the mission, or the `MISSION.md` is not populated, your first job should be to question the user on why they want to learn this.

Failing to understand the mission will mean knowledge acquisition is not grounded in real-world goals. Lessons will feel too abstract. You will have no way of judging what the user should do next.

Missions may change as the user develops more skills and knowledge. This is normal - make sure to update the `MISSION.md` and add a learning record to capture the change. Confirm with the user before changing the mission.

## Zone Of Proximal Development

Each lesson, the learner should always feel as if they are being challenged 'just enough'.

The user may specify an exact thing they want to learn. If they don't, figure out their zone of proximal development by:

- Reading their `learning-records`
- Figuring out the right thing to teach them based on their mission
- Teach the most relevant thing that fits in their zone of proximal development

A user may tell you that they already know about that topic. If so, record it in their `learning-records`.

## Acquiring Knowledge & Skills

Lessons should be designed around a skill the user is going to learn. The knowledge in the lesson should be only what's required to acquire that skill. You teach the knowledge first, then get the user to practice the skills via an interactive feedback loop.

Knowledge should first be gathered from trusted resources. Use `RESOURCES.md` to keep track of them. Lessons should be littered with citations - links to external resources to back up any claim made. This increases the trustworthiness of the lesson, and gives the user a path to acquire more knowledge if they want to go deeper.

Each lesson should contain a reminder to ask followup questions to the agent. The agent is their teacher, and can assist with anything that's unclear.

### Skills

Skills should be taught through interactive lessons. There are several tools at your disposal:

- Interactive lessons, using quizzes and light in-browser tasks
- Lessons which guide the user through a list of real-world steps to take (for instance, yoga poses)
- In-agent quizzes, where you ask the user scenario-based questions about what they've learned

Each of these should be based on a **feedback loop**, where the user receives feedback on their performance. This feedback loop should be as tight as possible, giving feedback immediately - and ideally automatically.

## Acquiring Wisdom

Wisdom comes from true real-world interaction - testing your skills outside the learning environment.

When the user asks a question that appears to require wisdom, your default posture should be to attempt to answer - but to ultimately delegate to a **community**.

A community is a place (online or offline) where the user can test their skills in the real world. This might be a forum, a subreddit, a real-world class (budget permitting) or a local interest group.

You should attempt to find high-reputation communities the user can join. If the user expresses a preference that they don't want to join a community, respect it.

## Reference Documents

While creating lessons, you should also create reference documents. Lessons can reference these documents - they are useful for tracking raw units of knowledge useful across lessons.

Lessons will rarely be revisited later - reference documents will be. They should be the compressed essence of the lesson, in a format designed for quick reference.

Some learning topics lend themselves to reference:

- Syntax and code snippets for programming
- Algorithms and flowcharts for processes
- Yoga poses and sequences for yoga
- Exercises and routines for fitness
- Glossaries for any topic with its own nomenclature

Glossaries, in particular, are an essential reference. Once one is created, it should be adhered to in every lesson.

## `NOTES.md`

The user will sometimes express preferences of how they want to be taught, or things you should keep in mind. This is the place to record those preferences, so you can refer back to them when designing lessons or working with the user.

## Multi-Paper / Multi-Topic Teaching

When teaching multiple related papers or topics across lessons:

- **Cross-paper synthesis is expected.** After completing individual lessons for each topic, offer a synthesis lesson that connects them conceptually. This user values seeing the overarching patterns (e.g., "both papers show that generation pretraining → emergent understanding").
- **Quiz answers on request.** If the user asks for quiz answers, provide them immediately with full explanations — don't make them wait for the next lesson. Save answers as a learning record.
- **Open-ended thinking questions work well.** Include questions that bridge topics or connect to broader philosophical questions. The user engages deeply with these.
- **Connect to user's prior knowledge.** If the user mentions their academic background (specific models they've worked on, papers they've studied), weave those references into the teaching — it deepens engagement.
