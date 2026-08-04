---
name: prototype-prompt
description: Method for one-shot building of self-contained interactive prototypes (trainers, games, visualizers, calculators, simulators, single-file HTML tools) and for writing the reusable one-shot prompts that produce them. Use this whenever the user asks to build an interactive HTML prototype or tool, asks for a "one-shot prompt" for building something, mentions a trainer/quiz/drill app, or wants a self-contained artifact they can open in a browser — even if they don't say "prototype" or "one-shot". Also use it when the user asks to improve or debug a prototype that was built with it.
---

# One-Shot Prototype Method

Two modes — pick by what the user asked for:

- **Build mode**: the user wants the prototype itself. Follow this method directly and build it.
- **Prompt mode**: the user wants a portable one-shot prompt to paste into a fresh session later. Fill the skeleton below and hand it over as a copy-pasteable block.

Either way, read `LESSONS.md` in this skill directory first — it holds corrections from previous uses that override anything here.

## The core mental model

A one-shot prototype prompt is a **contract, not a recipe**. Current Claude models
(Fable 5, Opus 5) do their best work from a complete, goal-stated spec in one turn;
step-by-step choreography reduces quality. Spend your specification budget on four
things only: the deliverable contract, the failure modes designed out, the way
wrongness becomes visible, and the definition of done. Leave the *how* to the model.

## The seven principles

1. **Specify the deliverable contract precisely.** Artifact form (usually: one
   self-contained HTML file, inline CSS/JS, zero external resources so it works
   offline and as an artifact), runtime constraints, and how it will be consumed.
   Most one-shot disappointment is contract mismatch, not capability failure.

2. **Research before build, with "verify or omit."** Any prototype containing
   factual content (game theory, real data, API behavior) gets a research phase
   first, and the model gets a legal way out of guessing: *"only include what you
   verified against sources; omit what you can't verify."* "Be accurate" does
   nothing; an escape hatch from fabrication does. Say "if web access is
   available" so the prompt works in offline contexts too.

3. **Forbid the hard general solution when a narrow one suffices.** A hand-rolled
   chess engine, date library, parser, or physics sim is where one-shot bugs live.
   If the actual need is covered by a lookup table, a move tree, or precomputed
   data, ban the general mechanism explicitly ("do NOT write a move-legality
   engine — validate input against the tree"). Name the domain's known traps;
   models handle "here's the trap, avoid it" extremely well.

4. **Make wrongness visible.** Require a startup self-test or consistency check
   that turns silent wrongness into a visible error naming the problem — a
   confidently rendered wrong result is the worst outcome; a caught error is a
   fixable one. Pair with an explicit definition of done: "finish by running it,
   confirm the self-test passes, report [concrete measurable]." That converts
   "I wrote code" into "I verified a working thing."

5. **Data-first for content-heavy prototypes.** Specify the data schema (what
   every node/record stores, e.g. `{san, from, to, why}`), because hallucination
   lives in data, not logic. A model filling a schema is far more constrained
   than one writing freeform.

6. **Make the taste calls yourself.** Interaction model, orientation, visual
   defaults — pick the reliability-cheap options (Unicode glyphs over SVG sets,
   click-to-move over drag, system fonts). Every unspecified taste decision is a
   re-roll. State light/dark friendliness if the artifact surface has themes.

7. **Scope-guard both directions.** Say what NOT to build ("an opening trainer,
   not a play-vs-engine app") and grant autonomy: "make minor decisions yourself;
   don't ask clarifying questions." Current models can silently widen scope and
   can also stall on questions in a fresh session — this line prevents both.

## Model-specific notes (Fable 5 / Opus 5)

- Full spec up front in one turn — drip-feeding requirements degrades results.
- Do NOT add "double-check your work" — these models self-verify; the
  instruction causes over-verification. The *in-artifact* self-test (principle 4)
  is product code and stays; process nagging goes.
- They follow instructions literally: write only real constraints, at normal
  volume — no "CRITICAL: YOU MUST".
- Give the reason behind the request ("I keep losing to this gambit online") —
  intent resolves ambiguity in the user's favor.

## The skeleton

```
Build me [DELIVERABLE] as [ARTIFACT FORM + runtime constraints].

WHY: [one sentence of intent — who uses it, for what]

RESEARCH FIRST (do not skip): [what to look up before coding]. Only
include [content] you verified against sources — omit what you can't
verify rather than guess.

ARCHITECTURE (do not deviate): [the narrow mechanism] — do NOT
[the general hard thing]. Data model: [schema]. On load, run a
self-test that [validates data/logic] and shows a visible error
naming the problem instead of rendering wrong output.

PRODUCT DECISIONS (don't relitigate): [3–6 taste calls]

SCOPE: This is [X], not [adjacent thing Y]. Make minor decisions
yourself; don't ask clarifying questions.

DONE MEANS: [run/test it], confirm the self-test passes, and report
[concrete measurable — counts, coverage, what was verified].
```

For a fully worked example (chess opening trainer, with the rationale per
section), read `references/examples.md`.

## Improvement loop — keep this skill honest

The skill is source code; each prototype is a build. After every use:

1. If the output disappointed, fix **the prompt/skill**, not just the artifact —
   otherwise the same failure recurs next time.
2. Append a dated entry to `LESSONS.md`: what was built, what worked, what
   failed, and the prompt change that fixes it. One paragraph is enough.
3. When a lesson has appeared twice or clearly generalizes, promote it into the
   principles above (and delete it from LESSONS.md). Keep LESSONS.md short —
   it's an inbox, not an archive.
4. If a whole domain recurs (chess trainers, flashcard apps…), add a worked
   example to `references/examples.md` so future prompts start from a proven
   instance instead of the blank skeleton.
