# A local AI that adjusts Albo's letters and kerning: options, measured (2026-09-26)

Owner, 2026-09-26: *"let's determine how to build an ai i can run on my mac
mini 32gb ram and lm studio that is able to adjust letters and kerning well
based on word image legibility"*.

This is an **architecture decision for the owner**. Nothing here was built
beyond probes. Every number below comes from a script in
`tools/wedge_serif/local_ai/`, run on this Mac mini (Apple M4, 32 GB) on
2026-09-26 at commit `12b75e9`. Each claim is marked **[measured]**,
**[repo]** (read from a file, with the path) or **[inf]** (inferred, not
measured).

---

## 0. The answer in one table

The scale: mean |error| in design units against his own bench numbers, on
judgments the model **never saw**. Four lines matter:

| line | units | what it is |
|---|---|---|
| do nothing | **13.66** | predict 0 for every pair |
| shipped ridge (`bench_fit.py --cv`) | **11.66** | today's method |
| his repeatability | **10.83** | his re-ask answer against his own earlier answer (typical rows, n = 30) |
| floor for any model | **7.66** | the best a perfect model could score against one of his noisy judgments |

The noise-floor doc framed the stopping rule as "held-out error against his
repeatability". That line is where a model predicts his next answer as well as
his last answer does. The **floor** (7.66) is the real limit. A model can go
below 10.83 because it averages many of his judgments, and one old answer
cannot.

| option | what it does | held-out error | vs shipped | compute / RAM / time | build effort | verdict |
|---|---|---|---|---|---|---|
| **A. Local VLM as judge** (Qwen3.8-27B installed; Qwen3-VL-8B downloaded) | looks at word images, picks the best-spaced of three arms | **18.29** (27B, 7 rows) / **28.34** (8B, 40 rows), against do-nothing 13.1 / 18.5 on the same rows | worse than doing nothing | 27B: 16 GB, **116 s** per judgment; 8B: about 6.5 GB, 1.4 s | small (probe exists) | **negative**: position bias, not sight |
| **B1. Shape features → ridge** | predicts his d from 38 measured gap and shape features; knows no glyph identity | **10.94** | −0.72 (95% −0.08 .. +1.54, not significant) | < 1 s to fit, CPU | done (probe) | generalizes to unseen glyphs |
| **B2. Hybrid: glyph identity + shape features, one ridge** | today's model plus the shape features | **10.73** | **−0.93 (95% −0.25 .. −1.64)**, significant | < 1 s to fit, CPU, < 200 MB | small: one function in `bench_fit.py` | **best measured**; first model under his repeatability |
| B3. Gradient boosting on features | nonlinear version of B1 | 11.46 | −0.20 | 12 s for 50 fits, CPU | done (probe) | no better than linear |
| B4. Tiny CNN on pair images (MLX, GPU) | learns from the rendered pair directly | **13.28** | worse; equal to doing nothing | 12 s per fit on the GPU | done (probe) | **negative**: 370 rows is far too few |
| **C. Classical optical spacing** (per-class target area + 2-D gap, HT Letterspacer's premise) | no learning; each class has one target white | **15.86** | worse than doing nothing | instant | done (probe) | **negative**, and it repeats `albo-spacing-method.md` Measure 2's failure |
| **D. Hybrid: LLM orchestrates, scorer disposes** | the local LLM drives build → measure → B2 score → gates → proposal page | = B2's accuracy; the LLM adds no accuracy | model 16 GB; build 1 s per style, gates 5 s | medium | **recommended shape**, but the LLM is optional |

**Recommendation (§6).** Build **D with B2 as the scorer**. The scorer is a
small ridge on measured shape, not a neural net or a VLM. The LLM is a
convenience layer that the scorer and the gates discipline, never the judge.
Spend his time on an **active-learning bench** (§4), not on more rows of the
same kind. The learning curve (§2b) says more random rows buy about 0.15 units.

---

## 1. What exists, and what this builds on [repo]

- **The bench.** 396 rows (a real English word opened at one pair), a slider in
  thousandths of an em, both styles. 384 answers are committed in
  `tools/wedge_serif/bench_values.json`. 370 remain once the g rows are dropped
  (ruled 2026-09-21). The 73 answers from 2026-09-22 stay out, per the
  2026-09-25 ruling (`docs/albo-kerning-noise-floor-2026-09-25.md`).
- **The re-ask.** 40 rows asked twice (`bench/answers/reask-2026-09-25-*`). His
  repeatability is 10.83 (95% 8.57 .. 13.13). His new answers drift **+5.4
  looser** on typical rows.
- **The outlier bench.** 50 answers against `fonts-2026-09-25`, a different
  zero. They shipped as kerns in round 390. They are **not** used here, because
  they are measured from a different baseline font. Using them would need a
  rebase (§4).
- **His slider picks.** Round 394/395 (`docs/albo-thick-thin-options-2026-09-26.md`
  §10, `docs/albo-round-395-2026-09-26.md`): about 10 continuous picks on
  thick/thin dials. This is the only shape (not spacing) data he has given in
  slider form.
- **The measures.** `gap_measure.py` (rsb + kern + lsb), `cmp_space_2d.py`
  (2-D closest approach), `pair_census.py` (2,007,794 pairs from his 36 epubs),
  and the gates: `gates.sh`, `approved.py`, `cmp_touch.py`,
  `cmp_contour_hairs.py`, `cmp_counter_dents.py`, `bench_fit.py --check`.

---

## 2. The decisive measurements

### 2a. Held-out accuracy of every non-VLM approach [measured]

`tools/wedge_serif/local_ai/probe_fit.py` uses the **same folds as
`bench_fit.py --cv`**: per style, 10 folds × 5 shuffles, seed 20260925. Models
that pool both styles train on both styles' training folds at the same index,
so no held-out pair reaches any fit. Hyperparameters were fixed before the run
(ridge α = 30 on standardized features, α = 1 on glyph identity). The one sweep
printed is labeled as optimistic. It is flat: α 3 .. 100 gives 10.95 .. 11.01.

Features (`local_ai/features.py`) are measured on the **same font files the
bench served** (`bench/fonts-2026-09-20/`), shaped with HarfBuzz. The kern the
features read agrees with the bench's recorded `kr`/`ki` on all 396 rows, and
the script refuses to run otherwise. Features, in design units: the bbox gap,
the 2-D closest approach, per-band row gaps (descender / x / ascender), an HT
Letterspacer depth-limited area, each facing side's depth profile at 8
heights, each glyph's own inner white, a blurred-ink "optical darkness" of the
gap, and class flags.

| model | roman | italic | **both** | 5 shuffles | lower | cap | mark | vs his NEW answer, typical (n = 30) | outlier (n = 10) |
|---|---|---|---|---|---|---|---|---|---|
| do nothing | 14.82 | 12.53 | 13.66 | — | 12.75 | 16.20 | 15.96 | 15.87 | 29.00 |
| his training mean (a tracking move) | 14.89 | 12.37 | 13.61 | — | 12.54 | 15.94 | 16.64 | 15.35 | 29.18 |
| **shipped ridge pipeline** | 11.72 | 11.60 | **11.66** | 11.42 .. 11.81 | 11.07 | 15.41 | 12.07 | 13.14 | 31.94 |
| identity ridge, continuous (no floors) | 11.61 | 10.71 | 11.15 | 11.01 .. 11.29 | 11.01 | 12.08 | 11.26 | 12.44 | 20.94 |
| C: optical, per-class targets | 16.12 | 15.61 | 15.86 | 15.69 .. 16.07 | 14.49 | 23.71 | 17.25 | 14.79 | 29.66 |
| B1: features → ridge | 11.96 | 9.94 | 10.94 | 10.73 .. 11.43 | 11.02 | 13.49 | **9.27** | 12.61 | **12.06** |
| B3: features → gradient boosting | 12.39 | 10.56 | 11.46 | 11.37 .. 11.57 | 11.38 | 12.74 | 11.12 | 12.72 | 17.34 |
| **B2: hybrid, identity + features** | 11.30 | 10.18 | **10.73** | 10.55 .. 10.92 | 10.97 | **10.15** | 10.10 | **11.37** | 15.17 |
| ensemble, identity ridge + GBM | 11.48 | 10.13 | 10.79 | 10.67 .. 10.84 | 10.77 | 11.89 | 10.29 | 12.25 | 18.51 |

**Paired comparisons** (same held-out rows; bootstrap over pairs, 4,000 draws;
`probe_fit.py --paired`):

- **B2 vs shipped:** 0.93 units better (95% 0.25 .. 1.64). Closer on 55% of
  pairs.
- **B1 vs shipped:** 0.72 better (95% −0.08 .. 1.54). Not significant.
- **B2 vs continuous identity ridge:** 0.42 better (95% −0.08 .. 0.88). Most of
  B2's gain over the shipped pipeline comes from dropping the 4/4 floors and
  from the capitals. The shape features add about 0.4 on top.

What this says:

1. **B2 is the first model measured under his repeatability** (10.73 against
   10.83). By the 2026-09-25 rule, that is the "held-out ≤ m" outcome: it
   predicts his next answer at least as well as his own last answer does.
   The margin is 0.1 units. The re-ask interval runs 8.57 .. 13.13, so read
   this as **"at his repeatability", not "beats it"**.
2. **Shape is what fixes the capitals.** A held-out capital pair gets no kern
   under the shipped pipeline (15.41, no better than doing nothing, 16.20).
   B2 gets 10.15, because the features see that the Y is open and the o is
   round. The same shows on the re-ask outliers (`Ye Yo Fi Fo 's 't`): the
   shipped model is 31.94 off his new answer, B1 12.06 and B2 15.17.
3. **The italic is more learnable than the roman** (9.94 against 11.96 on
   features alone). The roman capitals and marks carry the most error.
4. **Nonlinear models do not help at this data size.** Gradient boosting is
   worse than the linear model on the same features, and the CNN (§2b) is
   worse still.
5. **The optical model is worse than doing nothing.** One target white per
   class, whether area or 2-D gap, is the HT Letterspacer / Tracy premise. On
   his answers it scores 15.86. `albo-spacing-method.md` already recorded why:
   a letter's own open white belongs to the letter, and an area rule counts it
   as spacing. **Do not build C as the engine.** Its measures are useful as
   *features* inside B.

### 2b. The image model and the learning curve [measured]

**Tiny CNN, MLX on the GPU** (`probe_cnn.py`).

- Input: the shaped pair, FreeType coverage at 16 units/px, a 64 × 80 crop
  around the gap, one channel per glyph, plus the style flag.
- Network: three convolutional layers and two dense layers, Huber loss, 120
  epochs.
- Scored on bench_fit's first shuffle, 10 folds.
- Crops were checked visually before the run (`ve Yo 's o,`, correct and
  centered).

| first shuffle, 370 held-out | error |
|---|---|
| MLX CNN on pair images | **13.28** |
| shipped ridge pipeline | 11.78 |
| B2 hybrid | 10.76 |
| do nothing | 13.66 |

Each fit took 11.9 s. The CNN learned essentially nothing it could carry to a
held-out pair. That is expected at 333 training images. An image model needs
thousands of judged images, or a pretrained backbone (§2c), before it can
compete with 38 hand-measured features. **Negative result; do not pursue at
this data size.**

**Learning curve** (`probe_fit.py --curve`, each training fold thinned, 2
shuffles):

| training rows | 133 | 199 | 266 | 333 |
|---|---|---|---|---|
| shipped | 12.83 | 12.03 | 11.86 | 11.71 |
| B2 hybrid | 12.12 | 11.01 | 10.99 | 10.84 |

Both curves have flattened. Going from 80% to 100% of the data buys about 0.15
units. **More rows chosen the way the bench chose them (by frequency) will not
carry either model toward 7.66** [inf, extrapolating the curve]. What is left
is his noise (9.6 per judgment), his between-session drift (+5.4), and pairs
whose shape the features do not describe. Only the third is a model problem.

### 2c. The local VLM as judge [measured]

**Can the installed model see images?** Yes.

- `~/.lmstudio/models/lmstudio-community/Qwen3.8-27B-MLX-4bit/config.json`:
  `Qwen3_5ForConditionalGeneration` with a 27-layer vision tower,
  `language_model_only: false`.
- `lms ls --json` reports `"vision": true`.
- A transcription check read "Yesterday" and the A/B/C labels correctly.
- The image costs about 750 prompt tokens.

**Thinking cannot be switched off from the API** [measured]. I tried
`chat_template_kwargs.enable_thinking=false`, `reasoning: {effort: "none"}`
and a system prompt. Every call still produced reasoning tokens.
`reasoning_effort: "low"` is the shortest the chat template accepts. Decoding
runs at about **6.5 tokens/s** (1,499 tokens in 231 s on the first try, at the
default "xhigh" effort, which ran out of tokens before answering). LM Studio
loaded it at 16.08 GB.

**The probe** (`probe_vlm.py`). It uses the 40 re-asked rows, because their
target is the **mean of two of his judgments**. A 20-row sample was drawn
(seeded) to keep the run bounded.

- Each word is rendered three times at a 96 px em, differing only at the bench
  pair: −30, 0 and +30 units, about 2.9 px, visible, and inside the slider's
  range.
- The three are labeled A/B/C in random order, and each row is asked twice
  with the order reversed.
- The pick maps to −30 / 0 / +30.

Two models were run. The second is the small non-thinking vision model this
brief allowed downloading: `lmstudio-community/Qwen3-VL-8B-Instruct-MLX-4bit`,
5.78 GB.

| | Qwen3.8-27B (installed, thinks) | Qwen3-VL-8B-Instruct (downloaded) |
|---|---|---|
| rows / calls | 7 / 14 (stopped early, see below) | 40 / 80 |
| time per judgment | **116 s** median (71–175) | **1.4 s** |
| RAM | 16.08 GB loaded | about 6.5 GB (LM Studio process RSS) |
| order-reversed self-agreement | **2 of 7** | 40 of 40, but only because it answered "B" all 80 times |
| label counts | A 5, B 7, C 2 | A 0, **B 80**, C 0 |
| MAE vs the mean of his two answers | **18.29** (ridge 9.09 and do-nothing 13.1 on the same rows) | **28.34** (ridge 16.42, do-nothing 18.46) |
| direction right where \|his\| ≥ 15 | — | 30% (ridge 65%) |
| correlation with his mean | — | +0.01 (ridge +0.24) |

**Verdict: negative, for both models** [measured].

- The 8B always answers with the middle label. Its "estimate" is whichever arm
  the shuffle put in slot B. That is pure position bias and carries no
  information.
- The 27B reasons at length and changes its answer when the order is reversed
  in 5 of 7 rows. On the same 7 rows it is worse than doing nothing (18.3
  against 13.1).
- The 27B run was stopped at 7 of the planned 20 rows. At about 4 minutes per
  row, two orderings are self-inconsistent 5 times in 7, and the remaining 13
  rows would have cost about 50 minutes to confirm the same thing (the P0 rule
  on runs that teach nothing new). Both raw logs are committed:
  `probe_vlm-qwen3.8-27b-stdout.txt`, `probe_vlm-qwen3-vl-8b-stdout.txt` and
  `probe_vlm-qwen3-vl-8b-instruct-mlx.json`.

**Why this was expected** [inf]:

- Vision encoders tokenize at 16–32 px patches. A 3 px change in one gap is
  under one patch.
- Nothing in their training asks whether "Yo" is spaced evenly.

Two changes could help a VLM, and neither is worth building before B2:

- a magnified crop of the pair alone, which removes the resolution excuse but
  also removes the word-image context the owner judges by;
- fine-tuning on his answers, which hits the same 370-row wall the CNN did.

**Larger alternatives, not downloaded** (sizes from the Hugging Face
listings): `Qwen3-VL-30B-A3B-Instruct-MLX-4bit` (MoE, about 3B active, so
roughly 8B speed with 30B knowledge, about 17 GB) and `gemma-4-31B-it-MLX-4bit`
(about 18 GB). Both fit in 32 GB. Neither changes the patch-size argument, so
neither was worth a download over 15 GB.

---

## 3. "Adjust LETTERS" too: what an optimizer could move, and how shape would be scored

**What can move safely** [repo]:

- `docs/albo-STATE.md` lists **720 env dials** read from the builders.
- A build of both styles takes **about 1 s per style** and `gates.sh` about
  **5 s** on this machine [measured].
- So a candidate costs about 10 s to build, gate and measure. An optimizer
  could try a few hundred arms an hour without the owner.

The fence it must stay inside is already built:

- **Frozen:** every glyph in `approved.json` (`approved.py --check` fails if its
  outline moves) and every ruled dial in the rulings tables
  (`docs/fjord-glyph-guide.md` §3). The optimizer gets an **allow-list of dials
  per glyph**, never the whole table.
- **Must stay green:** `gates.sh` (touch, hairs, contours, bench),
  `cmp_counter_dents.py`, and `ladder.py`'s rule that a dial must be proved live
  before it is laddered.
- **Spacing moves** (bearings and kerns) are the safe first tier. They change
  no outline, and `bench_fit.py --check` already gates them. Kerns are
  quantized at 1.16 units on the phone and 2.31 on the X3.

**How legibility of a SHAPE change would be scored.** This is the hard part,
and nothing measured today answers it.

- **B2 scores spacing, not shape.** Its features do move when a glyph's side
  profile moves, so it would score a shape change *through its effect on
  spacing*. It knows nothing about stroke contrast, counters or terminals.
- **His thick/thin slider picks are the right kind of data, but there are
  about 10 of them** (one per dial). That is enough to record a ruling, not to
  train a scorer. Every pick is a method-of-adjustment answer on one dial,
  the same form as the spacing bench. So the cheapest route to shape data is
  **the same bench, pointed at dials**: a word, one dial, a slider, his pick.
  Collected across many dials × many words, that becomes a dataset.
- **Until that data exists, a shape optimizer can only propose.** An arm is
  ranked by the existing instruments (`cmp_weight_survey.py`,
  `cmp_aldine_shape.py` IoU against the references, `cmp_seven_legibility.py`,
  the glitch and hair gates) and rendered into word images for him to rule on.
  That is what the ladders already do by hand. The gain is automation, not
  judgment.
- **A zero-shot VLM is not a shape judge either** (§2c). On spacing, the
  easier task, its answers tracked label position, not the image.

---

## 4. What data is missing, and the cheapest way to get it

In order of value per minute of his time:

1. **Active-learning rows, not frequency rows.** Score every census pair that
   is not on the bench by B2's uncertainty and pick the next row by
   *(disagreement between B2 and the shipped fit, or across B2's CV fits)
   × corpus frequency × visibility*. Visibility is 0 when the proposed change
   is under the X3's 37-unit pixel and under the phone's quantum.
   `docs/research-claude-for-kerning-and-layout-2026-09-24.md` §3c specifies
   this. B2 is the posterior it lacked. Include 10% catch rows (repeats), to
   keep measuring his noise and drift per session.
2. **A session ID on every answer.** The +5.4 drift between sessions is a
   global offset that no pair model can express. With a session ID, the fit
   can carry one offset per sitting, and part of what reads as his noise today
   becomes signal [inf; the committed `bench_values.json` has no timestamps,
   and the live database has them].
3. **Pairwise (2AFC) rows for the outliers.** Where B2 and his answer
   disagree by more than 20 units, ask "A or B" between the two proposals.
   That is about 3 s of his time per row, against about 15 s for a slider.
4. **Fold in the 50 outlier-bench answers with a rebase.** They were answered
   against `fonts-2026-09-25`. Measure each pair's white in both fonts with
   `gap_measure.py` and convert them to the 2026-09-20 zero. That adds 50 rows
   on the hardest pairs at no cost to him.
5. **Dial benches for shape** (§3). The same page, one dial per card. This is
   the only way to get training data for "adjust letters".

The 73 pending answers stay out under the 2026-09-25 ruling. If B2 is adopted,
that ruling's own condition is met: a model at his repeatability is what it
asked for before folding them in. That is his call (§7).

---

## 5. The workflow he would run on the Mac mini

```bash
# once
uv venv -p /opt/homebrew/bin/python3.12 ~/.venvs/albo-ai
uv pip install -p ~/.venvs/albo-ai/bin/python -r tools/wedge_serif/local_ai/requirements.txt

# a round (D with B2): about 1-2 minutes of machine time, no LM Studio needed
cd tools/wedge_serif
~/.venvs/albo-ai/bin/python local_ai/features.py      # 4.5 s: measure every bench pair
~/.venvs/albo-ai/bin/python local_ai/probe_fit.py     # 45 s: held-out score of every model
#   (not built) propose.py: fit B2 on all answers, write proposed bearings/kerns,
#   albo_build, gates.sh, render a before/after word-image page, and pick the next
#   bench rows by uncertainty
```

- **LM Studio's role.** It is optional, and only as the orchestrator in D: it
  reads the round's numbers, runs the commands above through a coding harness
  (the `albo-local-model-handoff.md` pattern), and writes the round note. It is
  **not** the judge.
- **Time per round.** A proposal needs about a minute of CPU. His review is the
  existing bench page plus a before/after word page, about 5 minutes.
- **Where results land.** The proposal is a bench/proposal page (an Artifact,
  as today), and the numbers go in a dated doc under `docs/`. Nothing ships
  without his ruling and `gates.sh`.

---

## 6. Recommendation

1. **Adopt B2 as the fit**, behind a flag first (built 2026-09-26 as
   `ALBO_SPACING_FIT=b2`, §10). Replace the
   4-reading floors with the continuous hybrid, and re-run `--cv` to reproduce
   10.73. Ship integers only where the change is at least one phone quantum.
   This is a spacing round, and it needs his ruling (§7).
2. **Build D without depending on the LLM.** The scorer is ridge + features:
   deterministic, instant, and auditable pair by pair. The LLM, if used, is a
   harness around it.
3. **Point his next bench minutes at active-learning rows** (§4.1), with
   session IDs and catch rows.
4. **For letters, build the dial bench before any shape optimizer.** Without it
   there is nothing to optimize against except the existing instruments, and
   the ladders already use those.

**What NOT to build:** a VLM judge (§2c), a CNN trained from scratch (§2b), or
a pure optical-area engine (§2a). All three measured at or below doing nothing
on his answers.

## 7. Decisions for the owner (one at a time, in this order)

1. B2 as the spacing fit (a spacing round, with a before/after word proof).
2. Whether B2 at his repeatability satisfies the 2026-09-25 condition for
   folding in the 73 pending answers.
3. Active-learning bench: yes / no.
4. Dial bench for shape: yes / no.

## 8. Checked, and found negative or clean

- **The feature kern is the bench's kern:** 0 mismatches of 396 per style
  [measured].
- **CNN crops contain the pair:** checked visually before training [measured].
- **Build and gates run clean from this checkout:** `gates.sh` printed
  `GATES UNCHANGED` [measured].
- **Thinking cannot be disabled on Qwen3.8 through LM Studio's API**: three
  switches tried [measured].
- **Gradient boosting, the ensemble, and geometry without class flags**
  (ridge 11.18, GBM 11.51) are all no better than B1/B2 [measured].
- **The optical per-class target is worse than doing nothing** [measured].
- **The only asdf Python is the free-threaded 3.14t.** scikit-learn and MLX are
  not installed there. The probes ran in a separate 3.12 venv (Homebrew)
  [measured].

## 9. Not verified

- Only two VLMs were tried (§2c). The 30B-A3B and Gemma 4 31B sizes are from
  the Hugging Face listings, not measured here. The 27B probe covers 7 rows,
  not 20.
- No published autospacer (HT Letterspacer, Kernagic, KernOn) was run. The
  optical probe implements HT Letterspacer's *premise*, not its code.
- B2 has not been rendered into word images for him. It is a held-out number,
  and "render to decide what ships" still applies.


---

## 10. The B2 arm, built behind a flag (2026-09-26)

Built so the owner can judge decision 1 by eye. **Default off.** Nothing ships
until he rules on it.

### How to build it

```bash
cd tools/wedge_serif && source build_env.sh
ALBO_SPACING_FIT=b2 albo_build_all OUTDIR   # the arm
albo_build_all OUTDIR                       # unset: round 395, unchanged
```

- `outlines/build.py` (`SPACING_FIT`) swaps `ROM_LC_ADJ`, `ALD_LC_ADJ` and
  both `*_PUNCT_FIT` tables for the arm's tables. The g stays at round 340's
  fit, and the fi/ffi/fl/ffl ligatures ride their last letter as before.
- `outlines/kern.py` swaps `_BENCH_PAIRS_*` for the arm's kerns and applies
  the holds.
- Any value other than `b2` refuses to build.
- The tables are `outlines/spacing_b2.json`, written by `local_ai/b2_fit.py`
  in two passes: fit, then build, then measure the holds.

### What the arm is

- **One ridge per style, fitted on all 370 non-g judgments.** Inputs: glyph
  identity (α 1) plus the 38 shape features (α 30). In-sample error: roman
  8.01, italic 7.04.
- **Lowercase and mark bearings** are the identity coefficients, rounded, with
  no reading floor:
  - roman letters: a (+12, -6), b (-3, -6), c (-4, +7), d (+3, -7), e (+1, +6), f (+1, +2), h (+0, +1), i (-5, +5), k (+0, -10), l (+5, +3), m (-5, -2), n (+7, -9), o (+2, +4), p (-3, +10), r (-5, +0), s (-3, +4), t (+9, -11), u (+2, -1), v (-7, +4), w (+7, -2), x (-8, +0), y (-1, -4)
  - roman marks: ' (-9, -3), , (-2, +0), : (+4, +0), ; (+3, +0)
  - italic letters: a (-7, -4), b (+4, -1), c (-1, +7), d (+0, -6), e (-5, -8), f (-1, +1), h (-3, -1), i (-5, +0), k (+0, -13), l (+0, +2), m (-1, +7), n (+1, -3), o (+1, -11), p (+5, +2), q (+0, -2), r (+9, +2), s (+2, +3), t (-2, -6), u (-4, +6), v (+0, +7), w (+6, +8), y (+0, +9)
  - italic marks: ' (+3, -1), , (+4, +0), . (-3, +0), : (+3, +0), ; (-6, +0)
- **Kerns.** For each pair in scope: the model's prediction minus what the new
  bearings already give, kept at 4 units or more.
  - Scope is every bench pair, plus every census pair seen at least 200 times,
    or at least 10 times when it carries a mark.
  - The census has grown to **41 books, 2,665,458 pairs**.
  - The first build used the 200 threshold for marks too. It opened `h'`,
    `m'` and `c'` about 30 units, because the apostrophe's bearing moved while
    only its common pairs were kerned.
  - Excluded from scope: pairs with a g, cap+cap, mark+mark, and pairs a
    ligature swallows.
  - Count: roman 428 kerns, italic 438.
  - Reader limit: its limit is on kern CLASSES (255 per side,
    `fontconvert_sdcard.py:552`), not on pairs. With about 100 codepoints a
    side it cannot bind.
- **Holds.** Every pair he set by hand after the bench (the kerns of rounds
  384, 388, 389 and 390) keeps **round 395's white exactly**:
  - roman: 25 glyph pairs compensated;
  - italic: 36;
  - verified afterwards: 0 units moved on every held pair checked (roman
    `Qu ki ba t. 's or rd gr Yo`, italic `Fi Fo Ye Yo Pa Wa or es hy um`).

### Proof that the default is untouched [measured]

- **Outlines and advances:** `cmp_outlines.py --advances` against round 395
  (`12b75e9`, built before any edit) is **IDENTICAL on all four cuts**.
- **GPOS:** the full table's XML is also identical on all four cuts.

### Gates on the arm [measured]

- **`ALBO_SPACING_FIT=b2 ./gates.sh`:** exit 0, `GATES UNCHANGED`, 2 approved
  glyphs unchanged, contour census unchanged.
  - `bench_fit.py --check` reads `build.py`'s TEXT tables, so under the flag
    it passes trivially. It gates the default, not the arm.
- **`cmp_touch.py`, four cuts:** 0 touching and 0 below the floor, the same as
  round 395.
- **`cmp_contour_hairs.py`:** `--letters` exits 0 and the full sweep passes on
  all four cuts.
- **Outlines:** they move only by their sidebearing. The accented composites
  carry their accent with the base (checked on a/aacute, e/egrave,
  c/ccedilla). The Greek follows the Latin bearings, as it already does under
  the shipped tables.

### What moved [measured, `local_ai/b2_moved.py`; summary and top 30 in `local_ai/b2_moved-2026-09-26.json`]

White = rsb + kern + lsb (HarfBuzz), on all 1,486 census pairs.

| | pairs moved | by 4+ units | frequency-weighted mean Δ | mean \|Δ\| | largest \|Δ\| |
|---|---|---|---|---|---|
| roman | 995 | 611 | +0.43 | 3.42 | 45 |
| italic | 983 | 587 | +0.62 | 3.67 | 73 |

- **The average move is about 3.5 units per pair.** That is 3 phone quanta and
  a tenth of an X3 pixel.
- **The net is near zero** (+0.4 to +0.6), so this is not a tracking move.

The top 30 by |Δ| × count:

| style | pair | count | r395 | B2 | Δ | word |
|---|---|---|---|---|---|---|
| roman | `he` | 68,121 | 95 | 90 | -5 | the |
| italic | `in` | 54,252 | 45 | 51 | +6 | in |
| roman | `es` | 38,079 | 88 | 96 | +8 | does |
| italic | `ve` | 23,953 | 52 | 63 | +11 | have |
| roman | `re` | 43,721 | 99 | 93 | -6 | are |
| roman | `st` | 32,597 | 108 | 116 | +8 | first |
| italic | `an` | 46,222 | 87 | 92 | +5 | and |
| roman | `in` | 54,252 | 114 | 118 | +4 | in |
| italic | `at` | 31,840 | 103 | 97 | -6 | that |
| italic | `ne` | 21,599 | 84 | 76 | -8 | one |
| roman | `ti` | 27,278 | 70 | 64 | -6 | times |
| italic | `ed` | 25,402 | 78 | 84 | +6 | usted |
| italic | `de` | 20,917 | 31 | 24 | -7 | de |
| italic | `is` | 28,567 | -15 | -10 | +5 | is |
| italic | `it` | 28,566 | 61 | 56 | -5 | it |
| italic | `th` | 68,240 | 39 | 41 | +2 | the |
| italic | `pp` | 2,392 | -58 | -115 | -57 | appears |
| italic | `re` | 43,721 | 47 | 44 | -3 | are |
| roman | `se` | 21,583 | 109 | 115 | +6 | because |
| italic | `on` | 42,190 | 80 | 83 | +3 | on |
| roman | `hi` | 15,576 | 94 | 86 | -8 | which |
| roman | `ar` | 29,741 | 95 | 91 | -4 | are |
| roman | `ha` | 23,757 | 111 | 106 | -5 | that |
| italic | `nt` | 23,307 | 103 | 98 | -5 | into |
| roman | `ra` | 19,362 | 115 | 109 | -6 | rather |
| italic | `of` | 10,429 | -177 | -166 | +11 | of |
| roman | `ng` | 28,537 | 75 | 79 | +4 | English |
| roman | `ll` | 14,102 | 97 | 105 | +8 | all |
| italic | `vi` | 6,870 | 51 | 67 | +16 | Suvi |
| italic | `ti` | 27,278 | 53 | 57 | +4 | times |

**Look at these first** [inf]. They are the model's largest calls on pairs he
**never judged**. They are extrapolations of the shape features, and the reason
the proof exists:

- **Italic descender-against-descender:** `fy` −73, `py` −69, `pp` −57
  (`appears`, 2,392), `yp` −56. None touches, per `cmp_touch`.
- **Italic mark pairs:** `y;` `p;` `k;` about −40.
- **Italic F:** `Fr` `Fa` `Fe` about −35 to −38.
- **Roman apostrophe + letter:** `'v` `'d` `'r` `'m` about −34 to −45. This
  follows his own `'s` and `'t` judgments.
- **`Op`:** +30 roman, +40 italic.
- **Roman `g'` +29:** the g is out of kern scope by ruling, so it follows the
  apostrophe's new bearing uncorrected.

### The proof page (not published)

- Location: `/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/c03d2901-2d80-4074-84f8-7539dfb0f2e2/scratchpad/b2proof/index.html`. Generated by
  `local_ai/b2_proof.py BASE B2 moved.json OUT`.
- Content: two English paragraphs plus long words, roman and italic, round 395
  over B2.
  - 27 px enlarged 2× with nearest-neighbor.
  - 54 px native, both arms on round 395's line breaks.
  - A 54 px difference view: gray = both, blue = round 395 only, red = B2
    only.
  - The 15 most-moved pairs per style in their words at 108 px.
- Rendering: FreeType as the reader renders (default load flags, 2-bit
  coverage, linear advances, kerns in 1/16 px).
- Lossless PNG. No image is sized by CSS.

---

## RULED 2026-09-26 (owner)

- **Decision 3, the active-learning bench:** *"Build it."* Built as §11.
  Decisions 1 (B2 as the fit), 2 (the 73 pending answers) and 4 (a dial bench
  for shape) are still open.

## 11. The active-learning bench (2026-09-26)

### Files

- **Selection and page:** `tools/wedge_serif/local_ai/active_bench.py`, with
  its template `active_bench.html`. The template is `bench/build_live.py`'s
  live bench with the long-word and gap-flag sections removed.
- **Ingest:** `local_ai/active_ingest.py`.
- **Zero font:** `bench/fonts-2026-09-26/`. These are the shipped round-395
  fonts, built at `12b75e9` (sha256 `d2128b34…` Regular, `64aaa471…` Italic).
- **Session key:** `bench/active-2026-09-26-s1.key.json`. It holds the
  selection evidence and each row's white at both zeros. The page shows none
  of it.
- **Converted answers:** `bench/answers/extra-judgments.json`.

### How rows are chosen, per session

Seeded, so a run can be reproduced.

- **Candidates.** Every pair in B2's scope that he has never answered on any
  bench in that style: **885**.
- **Uncertainty.** The sd of B2's predicted white for the pair, across 200
  fits on bootstrap draws of his 370 judgments. Each draw keeps its unique
  rows, about 63%, so this is a resample spread, not a strict bootstrap.
  - Spread over the candidates: **min 2.0, median 4.5, p90 7.0, max 40.3
    units**.
  - The top of the range is every pair with a glyph he has never judged: `j`,
    `J`, and the italic `pp`.
- **Visibility.** 0 when B2's proposed move from the shipped font is under the
  phone's kern quantum (1.16 units). This removes 136 candidates, leaving 749.
- **Score** = sd × count in his books × visibility.
- **Session 1** has **50 rows**: the top 45 by score plus **5 repeats** (10%),
  drawn at random from bench pairs he has already answered. That is 21 roman
  and 29 italic.
  - The 45 chosen rows' sd runs 3.5 to 40.3, median 5.3.
  - Most are common pairs never put on a bench: `cr hr pi mp ef cl fe ld ep ci
    ck`.
  - A few are high-uncertainty rare ones: `Ja ja ju pp`.

### What the page stores

It uses the **`db` capability**, the same as the outlier and re-ask benches.
Without it, answers stay in the browser and he uses Copy answers.

- **Collection:** `active`, one document per row, `<style>_<id>`.
- **Fields:** `{delta, verdict, touched, style, pair, bench, session, at}`.
  - `bench` names the page (`active-2026-09-26-s1`).
  - `session` is minted when the page opens (the time plus 4 random
    characters), so every **sitting** is distinguishable. That is what lets a
    later fit carry one offset per sitting for his +5.4 drift.
- **localStorage** holds the same answers under `albo-<bench>`.
- **Copy answers** exports `{bench, answers: [{style, id, pair, delta,
  verdict, at, session}]}`.

### Ingest

`active_ingest.py <answers.json | ArtifactData dir>`.

- It puts every answer on the fit's zero:
  `d = white(page font) + delta − white(09-20 bench font)`.
  - It also records `d_r395`, the same answer read against the shipped font.
  - White is `rsb + kern + lsb` from HarfBuzz, the measure every key file
    uses.
- It reports the session's repeats (mean |new − previous| and drift) against
  the re-ask's 10.83 / +5.4.
- It writes the rows to `extra-judgments.json`, replacing any earlier rows
  from the same bench.
- `b2_fit.py --census … --extra` then refits B2 with each pair's judgment as
  the mean of all its readings. A 0 from these pages counts as an answer, per
  the 2026-09-25 ruling.
- **Tested end to end on a synthetic 20-answer file** (3 of them repeats),
  then removed. **Not yet run on real answers.**

### The 50 outlier-bench answers, converted [measured]

- **`active_ingest.py --outliers`** moves them from `fonts-2026-09-25` to the
  fit's zero.
- **The white read on the page's font matches the outlier key's recorded white
  on 50 of 50 rows.**
- **The shift between the two zeros:** median +2, range −23 to +52 units.
- **Against the shipped font** the mean |answer| is 5.3 units, against 10.8 as
  answered. Round 390 already shipped most of them as kerns, and the rest is
  mostly round 393's tracking.
- **They are in `extra-judgments.json`**, so they count in any `--extra` fit
  and are excluded from future selection as answered.
- **Limits.**
  - The conversion is exact for spacing. It is not exact where an outline
    changed between the two fonts (the round 391–395 thick/thin re-cuts).
  - Their g pairs stay out of the fit, as in `bench_fit`.
- **The committed B2 arm (§10) was NOT refit with them.** The proof shows the
  arm as fitted on the 370. Folding them in is the first `--extra` refit,
  after session 1.

## 12. Tuning a model: LoRA and the cheaper alternatives (asked 2026-09-26)

Owner: *"explain lora and other options besides qwen, maybe with cheaper models than opus 5.5"*. Recorded so the answer is not re-derived. Status of each line: measured here, or inferred (not yet measured).

- **LoRA** freezes a base model and trains two small low-rank matrices per layer (typically 0.1-1% of the weights), so a vision model can be taught from few examples on the Mac mini (MLX `mlx-vlm`, 4-bit base + adapter, QLoRA). The adapter loads in LM Studio beside its base. Inferred: at 370-420 answers it is unlikely to beat B2; section 4's from-scratch CNN (13.28) is the measured warning, though a pretrained base is far more data-efficient than scratch.
- **Pretrained image embedding + a small head** (SigLIP / DINOv2 small, 20-90M parameters, frozen; a linear or 2-layer head trained on his pairs). Inferred to be the most data-efficient learned arm: the features are pretrained, only the head learns. Seconds to train on the M4. Not yet measured -- the obvious next probe arm.
- **B2** (ridge + measured shape features): measured best, 10.73 held-out, CPU, sub-second.
- **Small local VLMs as judges without training** (Qwen3-VL-8B, Gemma 3, SmolVLM): measured negative for Qwen (position bias, order flips); zero-shot judging is out.
- **Claude models** cannot be fine-tuned from here. Their role is the ORCHESTRATOR -- running build, gates, score, proof, ingest -- not the judge. Haiku 4.5 or Sonnet 5 are enough for that and far cheaper than Opus; the local Qwen 27B in LM Studio does it for free, slowly (~2 min per turn measured in section 4).
- **Hosted fine-tuning services** would send rendered bitmaps and his answers off the machine; outlines never leave, but it is a data-leaving step and not needed at this scale.
