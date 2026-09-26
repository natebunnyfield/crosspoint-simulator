# Albo kerning noise floor: held-out error and a blind re-ask bench (2026-09-25)

Owner ruling, 2026-09-25, answering the question raised in
`docs/research-claude-for-kerning-and-layout-2026-09-24.md` §0 and §3a:
*"Yes, build the re-ask bench"*.

That doc found two gaps in the spacing fit. `bench_fit.py` had no held-out
validation, so its mean error (8.61 at round 308) was an in-sample number that
flatters the model. And no bench row had ever been asked twice, so nobody knew
the owner's own repeatability. Together those two numbers decide whether more
pair-fitting can pay. This doc records what was built to measure them, the
first number (measured today), and how to read the second once he answers.

**Do not open `tools/wedge_serif/bench/reask-2026-09-25.key.json` before the
owner has answered.** It holds his previous answers. The page does not.

## 1. Held-out error: `bench_fit.py --cv`

**What it does.** It runs 10-fold cross-validation, repeated over 5
deterministic shuffles (seed 20260925). Every held-out pair is predicted by a
fit that never saw it, through the same pipeline that ships: the ridge at
λ = 1, the 4-reading/4-unit letter floor, the directly-solved marks, and the
capital kerns. A held-out capital pair gets no kern at all, because its kern is
its own judgment minus a letter bearing. That is the honest answer to "what
would the model have said about a pair he never judged". The flag also prints
per-class errors and a λ sweep scored on held-out error.

The default output and `--check` are unchanged byte for byte (diffed before and
after), so `gates.sh`'s bench ledger is untouched. `./gates.sh` after the change
printed `build.py matches the bench` and `GATES UNCHANGED`.

**Measured 2026-09-25** on `bench_values.json` as committed (370 non-g
judgments; g excluded by the 2026-09-21 ruling):

| | do nothing | in-sample (shipped integers) | **held-out** | held-out, continuous ridge |
|---|---|---|---|---|
| roman (182) | 14.82 | 9.00 | **11.72** (shuffles 11.36–11.99) | 11.61 |
| italic (188) | 12.53 | 7.66 | **11.60** (shuffles 11.44–11.73) | 10.71 |
| both (370) | 13.66 | 8.32 | **11.66** | |

All values are mean |error| in design units, against his own numbers. Round
308's 8.61 was fitted on a different 329-row set. The comparable in-sample
figure today is 8.32.

By class (held-out, shipped integers):

| | roman nothing | roman in | roman held-out | italic nothing | italic in | italic held-out |
|---|---|---|---|---|---|---|
| lower | 13.62 | 9.32 | 11.31 | 11.82 | 8.93 | 10.80 |
| cap | 23.17 | 0.00 | 17.70 | 14.76 | 0.00 | 14.93 |
| mark | 18.00 | 9.27 | 12.28 | 13.43 | 9.63 | 11.81 |

What this says [verified by the run above]:

- **The in-sample number flatters the model by about 3.3 units.** The model
  still beats doing nothing on held-out rows: 11.66 against 13.66, a 15% cut.
  In-sample it looked like a 39% cut.
- **The capital kerns do not generalize.** In-sample 0.00 is memorization: each
  capital pair is its own kern. Held out, the italic capitals score 14.93
  against 14.76 for doing nothing, so a capital pair he has not judged is
  predicted no better than by leaving it alone. This agrees with round 308's
  ruling that the italic capitals are not generalizable. It is a reason to keep
  them as per-pair kerns, not a defect.
- **λ is not the lever.** Held-out error by λ, 2 shuffles: roman 0.1: 11.80,
  0.3: 11.77, 1: 11.70, 3: 11.65, 10: 12.07. Italic 11.95, 11.83, 11.72, 11.64,
  11.84. It is flat from 1 to 3, so the shipped λ = 1 stays. The 0.05-unit gain
  at 3 is inside the shuffle-to-shuffle spread.

## 2. The blind re-ask bench

**Page (private artifact, `db` capability):**
`https://claude.ai/artifact/HPicRXrQTHyN19xM58upKC`. It was published from
`tools/wedge_serif/bench/reask-2026-09-25.html`, which is self-contained: both
fonts are embedded as data URIs, so the local file works offline too.

**How it matches the original bench.** The original is
`claude.ai/artifact/VCbkYNuYmZgV2m5Udd6ruy`. The re-ask page uses its card
markup, CSS, slider (−60..60 thousandths of an em, zero = what shipped),
"shipped" reset, three verdict chips, and 13/17/22 size switch. It uses the
**same two font files** the original page served. They are committed at
`tools/wedge_serif/bench/fonts-2026-09-20/`, sha256 `7c7dd2f2…` (Regular) and
`c2a345c1…` (Italic), with `head.modified` 2026-09-20 22:23. Every one of the
457 stored answers is timestamped later (first 22:56Z), so all of them were
given against these files. The per-row GPOS offset (`kr`/`ki`) is also the same.
A new answer and an old one are therefore measured from the same zero. The
original's row list is committed at `bench/bench-items-2026-09-20.json`.

**Two deliberate differences.** Roman and italic rows are mixed in one
shuffled list, and each card names its style. The card does not show the other
style's saved value, because on the original page that value was his previous
answer. No previous answer appears anywhere in the page source.

**Row choice** (`bench_reask.py select`, seed 20260925, deterministic; a re-run
reproduces both files byte for byte). There are 40 rows, 20 per style, and no
pair appears in both styles:

- **Outlier stratum** (5 per style): the pairs with the largest *held-out*
  residual. These are where a retest decides the most: a big residual is either
  his noise or the model's miss. They are reported apart from the typical rows,
  because they would inflate any estimate of his noise.
- **Typical stratum** (15 per style): a random draw per class, with 9 lower, 3
  capital and 3 mark.

The drawn split is roman 2 lower / 1 cap / 2 mark outliers plus 9/3/3 typical,
and italic 0/4/1 outliers plus 9/3/3 typical. That gives 30 typical and 10
outlier rows.

**How he answers.** He opens the link on any device and moves each slider as he
would on the bench, or taps "shipped". A row counts once it is touched, as on
the original. Answers save to the page's `reask` collection, as documents
`<style>_<id>` in the original's schema plus `bench: "reask-2026-09-25"`.
Without the db (for example, the local file), the "Copy answers" button gives a
JSON block to paste. Answers also persist in that browser's local storage.

The research doc suggests spreading re-asks over 3+ days, mixed into ordinary
sessions. This page is standalone. The original answers are 3–5 days old
(2026-09-20/22), which is long enough that anchoring on remembered numbers is
unlikely at slider resolution. If he answers in several sittings, that is
better.

## 3. Running the analysis once he answers

```bash
cd tools/wedge_serif
# from the page's database (Claude: ArtifactData list, collection "reask",
#   url https://claude.ai/artifact/HPicRXrQTHyN19xM58upKC, out_dir DIR):
python3 bench_reask.py analyze DIR
# or from a pasted "Copy answers" block saved to a file:
python3 bench_reask.py analyze answers.json
```

It prints a row table (previous, new, |Δ|, the model's held-out prediction, and
its error against the new answer). It then summarizes the typical rows, the
outlier rows, all rows, and each class:

- **Repeatability** is mean |new − previous| in units, with a 95% bootstrap
  interval. At n≈30 the interval is wide, about ±1.6 units on a simulated set,
  and the verdict should be read against it.
- **Implied noise per judgment** is sd = mean|Δ| · √π / 2. This assumes two
  independent judgments with equal Gaussian noise. It is cross-checked against
  sd(Δ)/√2.
- **Noise floor** is repeatability / √2: the mean error even a perfect model
  would show against one of his judgments.
- **Head-to-head.** On the same rows, it compares the model's held-out error
  against his *new* answer with his *previous* answer's error against the new
  one, and counts which is closer. This is the cleanest comparison, because
  both predictors are scored against the same fresh judgment and neither saw it.
- **The verdict** compares the bench-wide held-out error (recomputed live) with
  his repeatability on the typical rows.

The analysis was exercised end to end on a synthetic answer set and on a
synthetic db directory. No real answers exist yet.

## 4. What each outcome means

The decision variable is **bench-wide held-out error (11.66 today) against his
typical-row repeatability `m`**.

| Outcome | Meaning | Next step |
|---|---|---|
| **held-out ≤ m** | The model predicts his next answer at least as well as his own last answer does. | **Stop fitting pairs.** More rows on the same pairs buy nothing he could see twice. Spend bench time on what has never been asked (Greek, bold, new glyphs) and on the prospective test in research doc E5. |
| **m < held-out ≤ 1.25 m** | Close to the end of what pair-fitting can buy. | Only a better *model* is worth trying (class priors, shape features; research doc §3b). Accept it only if it lowers `--cv`, never on the in-sample number. |
| **held-out > 1.25 m** | His eye is steadier than the model. The model is the bottleneck. | Add structure before adding rows (§3b). More judgments of already-judged pairs would still mostly be averaged away by a model that cannot use them. |

Two further readings, whatever the verdict:

- **Outlier rows.** If he moves an outlier row toward the model's prediction,
  that residual was his noise. If he repeats his previous number, the model is
  wrong there, and that pair is a candidate for a per-pair kern.
- **A large mean drift** (new − previous consistently one sign) would mean his
  standard moved between sessions, not that he is noisy. Read that as drift
  before reading it as repeatability.

Whether any of this is visible on the X3 stays a separate question. One X3 pixel is about 37
units and the phone quantum is 1.16 units (`albo-spacing-method.md`), so an
error of 11 units is about a third of an X3 pixel.

## 5. Found while building this, not acted on

- **`bench_values.json` is stale by 73 judgments** [verified]. The live
  database (`spacing`, read 2026-09-25) holds **457** styled answers. The
  committed checkout holds 384. The 73 extra answers are all timestamped
  2026-09-22 00:14–01:00Z, after round 344's commit (09-21 18:56 −0500). All 73
  are new rows, not revisions: all 384 committed values equal the database.
  They were not folded in here. Refreshing the file would move the fitted
  tables and fail the gate, and that is a spacing round, not tooling. The db
  dump used for this work was a session scratch file and is not committed.
- **A zero judgment is dropped from the fit** [verified, `bench_fit.py`
  `judgments()`: `if d`]. A row he set to "shipped" (0 = the spacing is right)
  is evidence that the model should predict 0 there. Today it is discarded as
  if unanswered. None of the 384 fitted values is 0, so nothing shipped is
  affected. Two of the 73 unfitted answers are 0 (roman `Th`, roman `cr`), so
  it will matter at the next refit. The re-ask analysis counts a 0 answer as a
  real answer.
- **Checked and found clean:** the bench page's 396 rows map one to one to
  pairs (no duplicate pair keys). Every stored answer matches a row (no
  orphans). The fonts served by the bench predate every answer.

## RULED 2026-09-25 (owner)

- **The 73 answers `bench_values.json` is missing** (2026-09-21 evening, after round 344) wait for the re-ask. If the re-ask shows the held-out error beats his own repeatability, they are folded in as a spacing round with before/after proof. If not, pair fitting stops.
- **A bench answer of 0 ("the shipped spacing is right") COUNTS as a judgment** when the fit next runs. `judgments()` stops discarding it. This is applied together with the 73, not before.

## RESULT, 2026-09-25 (his 40 re-asked answers)

The answers and the full analysis are in `tools/wedge_serif/bench/answers/reask-2026-09-25-{answers.json,analysis.txt}`.

| | units |
|---|---|
| His repeatability on typical rows (mean abs new − previous, n=30) | **10.83** (95% bootstrap 8.57–13.13) |
| Implied noise per judgment | 9.60 |
| Floor for any model against one judgment (repeatability / √2) | 7.66 |
| Model held-out error, bench-wide (`bench_fit --cv`) | **11.66** |
| Model vs his NEW answer on typical rows | 13.14 (the model is closer than his previous answer on 11/30) |
| Outlier rows: his repeatability / the model's error | 14.00 / **31.94** |

- **Verdict, per his rule of 2026-09-25:** the held-out error (11.66) does NOT beat his repeatability (10.83). Pair-fitting stops. The 73 pending answers stay out and are moot for fitting.
- **Finding 1 — DRIFT.** On typical rows his new answers are **+5.4 units looser** than his 09-21 answers (sd of the difference 11.5, n = 30, ≈ 2.6 standard errors): lowercase +6.1, marks +6.3, capitals +2.7. This is a global tracking preference that no pair fit can express.
- **Finding 2 — REAL MISSES.** On the 10 rows the model gets most wrong he is consistent with himself (14.0) and the model is off by 31.9. Those are specific pairs where the model is wrong, not noise.


**Follow-up, 2026-09-26:** a hybrid model (glyph identity plus measured shape features) scores **10.73** held-out on the same folds, the first under his 10.83. VLM, CNN and optical-area approaches all measured worse than doing nothing. See [local-ai-spacing-options-2026-09-26.md](local-ai-spacing-options-2026-09-26.md).
