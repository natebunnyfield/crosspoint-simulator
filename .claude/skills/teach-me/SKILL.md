---
name: teach-me
description: Turn any topic the user wants to learn into a researched, interactive, single-file HTML lesson — cooking recipes and techniques, DIY and home-improvement skills (interior painting, tiling), hobbies, practical how-tos. Use this whenever the user says they want to learn, understand, or get good at something practical, asks to be taught a technique, or asks for a lesson, tutorial, or explainer they can interact with — even if they don't say "lesson" or "interactive". Also use it when the user asks for the portable learning prompts (the Gemini Deep Research prompt or the lesson-builder prompt) to run elsewhere, or hands over a research report to turn into a lesson.
---

# Learn: topic → interactive lesson

Turn a topic into working competence: research it honestly, then present it as
an engaging, non-patronizing interactive lesson in one self-contained HTML file.

Read `LESSONS.md` in this skill directory first — corrections from previous
uses override anything here.

## Three ways in

1. **Topic only** ("teach me pan sauces"): research yourself, then build.
2. **Topic + research report** (a Gemini Deep Research export, a pasted doc, a
   Google Drive file): treat the report as the primary source, verify anything
   surprising, fill gaps with your own research, then build.
3. **"Give me the prompts"**: the user wants to run the work elsewhere or later.
   Serve the portable prompts from `references/portable-prompts.md`, filled in
   with their topic. Don't build anything.

## Research rules

- Use authoritative and practitioner sources; prefer them over listicles.
- **Verify or omit**: only include facts, ratios, temperatures, measurements,
  and techniques you verified against sources — leaving something out beats
  guessing. If web access is unavailable, restrict to well-established
  knowledge and say so in the lesson header.
- Cover what a motivated beginner needs for *doing*: core principles and why
  each works, standard techniques step by step, the mistakes beginners actually
  make and how to recognize them, what equipment/materials matter vs. don't,
  and where experts disagree.

## Build contract

One self-contained HTML file: inline CSS/JS, zero external resources, works
offline and as an artifact, light/dark friendly.

- **Data-first**: all lesson content lives in structured data (sections, key
  ideas, common mistakes, quiz questions with explanations) rendered by the
  page — no prose hardcoded into markup. Hallucination lives in data;
  a schema constrains it.
- **Self-test on load**: verify every section renders and every quiz question
  has an answer and an explanation; on failure show a visible error naming the
  problem instead of rendering a broken lesson.
- **Interaction**: progressive sections the user clicks through; common
  mistakes framed as real scenarios; a check-yourself quiz per section where a
  wrong answer gets an explanation, not just a red X; progress in localStorage
  with a reset control.

## Voice

Knowledgeable friend, not a textbook: direct, concrete, zero filler, never
patronizing. Lead with *why things work*, not rules to memorize. Cut history
and trivia unless they explain a technique — this is a lesson for doing, not an
encyclopedia. Make minor decisions yourself; don't ask clarifying questions.

## Done means

Run/verify the self-test passes, then report: section count, key-idea count,
quiz-question count, and which sources the content was verified against.

## Improvement loop

Same as the `prototype-prompt` skill: after each real use, if the lesson
disappointed, fix this skill (not just the artifact) and append a dated
one-paragraph entry to `LESSONS.md` — what was built, what failed, the fix.
Promote recurring lessons into this file and delete them from the inbox.
