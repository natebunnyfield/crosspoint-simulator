# Portable prompts

For running the work outside a skill-enabled Claude session. When the user asks
for these, fill in `[TOPIC]` with their topic and hand them over as
copy-pasteable blocks.

## Prompt 1 — Gemini Deep Research (optional research pass)

Run in Gemini; export the report to Google Docs (readable later via the Drive
connector) or paste it back into Claude alongside Prompt 2.

```
Deep research report on [TOPIC] for a motivated beginner who wants
working competence, not a survey. Cover: the 5-10 core principles and
why each works; the standard techniques step by step; the mistakes
beginners actually make and how to recognize them; what equipment/
materials matter vs. don't; and where experts disagree. Cite sources.
Prefer authoritative/practitioner sources over listicles.
```

## Prompt 2 — Lesson builder (paste into any Claude session)

Attach the research report if one exists.

```
Build me an interactive lesson on [TOPIC] as a single self-contained
HTML file (inline CSS/JS, zero external resources, works offline).

WHY: I want working competence in this — enough to actually do it well —
not a shallow overview.

RESEARCH FIRST: [If I attached a research report, treat it as the primary
source and verify anything surprising.] Research the topic using
authoritative and practitioner sources. Only include facts, ratios,
temperatures, and techniques you verified — omit what you can't verify
rather than guess.

ARCHITECTURE: Store all lesson content as structured data (sections,
key ideas, common mistakes, check-yourself questions with explanations),
rendered by the page — don't hardcode prose into markup. On load, run a
self-test that every section renders and every question has an answer
and explanation; show a visible error if not.

PRESENTATION: Talk to me like a knowledgeable friend — direct, concrete,
zero filler, never patronizing. Lead with why things work, not rules to
memorize. Progressive sections I click through; "common mistakes" shown
as real scenarios; a check-yourself quiz per section where wrong answers
get an explanation, not just a red X; progress saved in localStorage.
Light/dark friendly.

SCOPE: A lesson for doing, not an encyclopedia — cut history and trivia
unless they explain a technique. Make minor decisions yourself; don't
ask clarifying questions.

DONE MEANS: confirm the self-test passes and report how many sections,
key ideas, and quiz questions the lesson contains.
```
