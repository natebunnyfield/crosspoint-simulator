# Existing spacing, kerning and legibility tools, tried on Albo (2026-09-26)

Owner, 2026-09-26, on whether to train a spacing prior on pedigreed fonts:
*"it seems overdue to see what other existing tools can offer"*.

Taken literally: every existing tool that could be made to run headless on
this Mac was **run on Albo**, its output was turned into a predicted white for
each pair he has answered, and it was scored against **his own numbers** with
the **same held-out folds** that scored B2. The tools that cannot run here
(commercial apps, a service, dead code) are described with what they would
cost and how to test them. A score door (`score_font.py`) is in place for any
font such a tool returns.

Everything is in `tools/wedge_serif/tool_survey/`. Each claim is marked
**[measured]** (a script in that folder, run today), **[source]** (read in the
tool's own code, with the file), or **[web]** (from the tool's site or repo
page, not tested here).

---

## 0. The answer

**No existing tool comes close to his answers, and none adds anything to B2.**

- The runnable spacers (HT Letterspacer, CounterSpace, Kernagic) are all
  **worse than doing nothing** as they come. The best raw result was
  HT Letterspacer at depth 25: 22.54 against doing nothing's 13.66.
- Given two free numbers per style fitted on his answers (a tracking offset
  and a gain), the best existing tool (HT Letterspacer at depth 25) reaches
  **12.74**. That beats doing nothing but is far behind B2 (**10.33**) and
  his own repeatability (**10.83**).
- Added to B2 as a 39th feature, every tool changes B2's held-out error by
  **+0.00 to +0.06**. None helps. Kernagic, the OCR judge and the pedigree
  prior make it slightly *worse*, and their confidence intervals exclude
  zero.
- **OCR at degradation** (Apple Vision, the Kept Legibility Index's reader):
  its pair-by-pair answers are noise. They correlate **+0.04** with his, and score **27.61** raw and 13.60 with a fitted gain, against doing nothing's 13.66. Averaged over all 489 words, it prefers looser white only faintly (character accuracy 0.60 at −40, 0.63 at +30).
- **A pedigree-font prior** (built here the cheap way, from seven Apple text
  serifs plus the repo's three reference italics): the most informative of
  everything tried (r = +0.51 with his answers), but still only 11.96 alone
  and +0.06 inside B2. **Do not build a bigger one** (§5).

The one real legibility finding came from a tool pointed at the whole face,
not at pairs: the Kept Legibility Index reads Albo's roman **e as o 131
times** in round 397, against **6** in the 2026-09-20 font (§4b).

### The table

The scale: mean |error| in design units against his answers. **Lower is
better.** The reference lines are measured by the same harness on the same
rows:

- do nothing: **13.66**
- the shipped B2 fit (round 397), held out: **10.33**
- his own repeatability: **10.83**
- the floor for any model: **7.66**

Column meanings:

- **raw**: the tool as it comes, on the 370 bench pairs.
- **cal**: the tool plus one tracking constant per style.
- **lin**: the tool times a gain plus a constant, per style.
- **+his corr.**: an identity ridge fitted on (his answer − tool).
- **in B2**: B2 with the tool as a 39th feature.

cal, lin, +his corr. and in B2 are held out on B2's own folds (10 folds × 5
shuffles, seed 20260925), trained on the bench plus the later benches, exactly
as round 397 was.

| tool | runs headless here? | raw | cal | lin | +his corr. | in B2 | time (both styles) | install | license | reproducible for other fonts |
|---|---|---|---|---|---|---|---|---|---|---|
| *do nothing* | — | 13.66 | 13.55 | 13.55 | 10.69¹ | 10.33 | — | — | — | — |
| *B2, round 397* | — | — | — | — | — | **10.33** | < 1 s | < 200 MB | ours | yes, with his answers |
| **HT Letterspacer**, defaults (area 400, depth 15) | yes, via a verified port | 31.55 | 19.12 | 12.84 | 14.58 | 10.33 | 0.15 s | 10 KB port (repo 4.8 MB) | GPL-3.0 | yes |
| HT Letterspacer, depth 25 | yes | 22.54 | 19.21 | **12.74** | 14.60 | 10.34 | 0.12 s | same | same | yes |
| **CounterSpace** (Cozens), smoothing 0 | yes, own venv | letters only: 26.08 | 25.52 | 12.34 | 14.17 | 10.47² | 61 s | 186 MB venv | Apache-2.0 | yes; **marks fail** |
| CounterSpace, smoothing 2 (class default) | yes | letters: 66.17 | 31.80 | 12.34 | 22.02 | 10.44² | ~11 min³ | same | same | same |
| CounterSpace, smoothing 20 (README's serif advice) | yes | letters: 94.55 | 84.60 | 12.30 | 65.25 | 10.42² | ~11 min³ | same | same | same |
| **Kernagic**, gap method (Kolås) | yes, after a patched build | 95.62 | 34.87 | 13.43 | 17.33 | 10.37 | 1.4 s | 1.4 MB + gtk+ 62 MB | GPL-3.0 | yes, upright only |
| **pedigree-font prior** (built here, §5) | yes | 38.25 | 18.16 | 11.96 | 14.18 | 10.39 | 2.5 s | none beyond the venv | ours; training fonts are Apple's | yes |
| **OCR judge, Apple Vision** (§4a) | yes | 27.61 | 27.57 | 13.60 | 28.09 | 10.37 | 10 min (52,812 images; 10 ms each to read) | Swift binary 70 KB | MIT (the reader) | yes |
| atokern / kerncritic (Cozens) | **no**: its model file 404s | — | — | — | — | — | — | TF 1.x | MIT | no weights anywhere |
| YinYangFit (Kosch) | **no**: broken as published | — | — | — | — | — | — | 144 MB repo | Apache-2.0 | no |
| FontLab 8 auto metrics / auto kerning | no (GUI only) | untested | | | | | | | $499 | via `score_font.py` |
| Glyphs 3 + KernOn / BubbleKern | no (GUI only) | untested | | | | | | | Glyphs $299.90 + plug-in | via `score_font.py` |
| iKern (Marini) | no (a paid service) | untested | | | | | | | quoted per project | via `score_font.py` |
| Fontra, fontmake, ufo2ft, MetricsMachine, SpaceCenter | no auto-spacing at all | — | | | | | | | | — |

Notes:

1. Identity ridge alone, with no tool. This is the number every "+his corr."
   cell must beat. None does.
2. Letter pairs only, against B2 on the same subset: **10.42**. CounterSpace
   returns nonsense for any pair containing a mark (§2b).
3. Three variants ran at once, so each ran slower. One variant alone took 61 s.

Paired bootstrap (`paired.py`, 4,000 draws over the 1,850 held-out rows):

| tool | in B2 − B2 | lin − do nothing | lin − B2 |
|---|---|---|---|
| HT Letterspacer | +0.00 (−0.02 .. +0.03) | −0.82 (−1.06 .. −0.59) | +2.50 (+2.04 .. +2.99) |
| HT Letterspacer, depth 25 | +0.01 (−0.01 .. +0.03) | −0.92 (−1.19 .. −0.66) | +2.40 (+1.94 .. +2.86) |
| Kernagic | +0.04 (+0.01 .. +0.07) | −0.23 (−0.40 .. −0.07) | +3.10 (+2.62 .. +3.57) |
| pedigree prior | +0.06 (+0.02 .. +0.11) | −1.70 (−2.03 .. −1.37) | +1.62 (+1.19 .. +2.07) |
| OCR judge | +0.04 (+0.02 .. +0.05) | −0.06 (−0.19 .. +0.07) | +3.27 (+2.80 .. +3.75) |

Rows repeat across the 5 shuffles, so the intervals are slightly narrow. That
does not change any sign.

**How to read "lin".** A tool can point the right way and still be far off
in size. "lin" fits a gain per style. The fitted gains are small:

- HT Letterspacer: **0.21** roman, **0.20** italic.
- pedigree prior: **0.27** roman, **0.28** italic.
- Kernagic: **0.09** roman, **0.04** italic.

So the best any tool can do is keep about a quarter of each move it proposes.
Its moves are 1.5–5× larger than his and only weakly correlated with them:

- HT Letterspacer: r = +0.32 to +0.38.
- pedigree prior: r = +0.49 to +0.53.
- Kernagic: r = +0.17 to +0.20.

---

## 1. Method (what "scored against his answers" means)

**His answers.**

- Each answer is `d` on the 2026-09-20 bench fonts: he wants the pair's white
  at `white0920 + d`. White is `rsb + kern + lsb`, the measure every key file
  uses (`b2_fit.white_fn`).
- The 370 non-g bench judgments, plus the later readings in
  `bench/answers/extra-judgments.json`. That makes 489 answered pairs: 242
  roman and 247 italic.
- **The later readings are pinned to round 397** (commit `c25375b`: the
  outlier bench plus active sessions 1–2, 150 rows).
  - Session 3 was ingested while this survey ran (`2a3a27a`), and it would
    have moved every CV number mid-survey.
  - `TOOL_SURVEY_EXTRAS=live` reads the working tree instead.
  - The harness reproduces **13.66** (do nothing) and **10.33** (B2) exactly
    [measured].

**Turning a tool into a prediction.**

- A tool proposes an absolute white `W(p)`. Its prediction of his answer is
  `W(p) − white0920(p)`.
- Tools that only set sidebearings (HTLS, Kernagic) give
  `W = rsb'(a) + lsb'(b)`, with no kerning, because they write none.
- Every tool ran on the **2026-09-20 fonts**, the ones his answers are
  measured on.
- HTLS, Kernagic and CounterSpace also ran on the **round-397 fonts**
  (`bench/fonts-2026-09-26-r397/`). Their scores there agree with the
  2026-09-20 runs to within about 1 unit on every column:
  - HTLS: raw 30.68, cal 19.99, lin 12.64, in B2 10.33.
  - Kernagic: raw 94.11, lin 13.32.
  - CounterSpace s0, letters only: raw 26.87, lin 12.40.
  - The r397 runs are scored against the same 09-20 zero, so outline changes
    since then add a little error. It does not change any conclusion.

**Controls** [measured, `score_font.py`]:

- The 2026-09-20 fonts scored as if they were a tool give **exactly 13.66**.
  This proves the white pipeline.
- Rounds 395 and 397 score about 9.2 raw. That is **in-sample** (they were
  fitted on these answers), so it is not a comparison. Their "in B2" cell is
  leakage and is not reported.

**HT Letterspacer is a port, and the port is verified.**

- `htls_port.py` is a line-for-line port of HTLS's own engine
  (`htls/engine.py`, commit of 2026-08-17). Only the Glyphs API calls are
  replaced by fontTools geometry.
- `validate_htls_port.py` runs it on **HTLS's own example font**
  (`Examples/ExampleFont-Glyphs3.glyphs`, 3 masters × 52 letters, with the
  masters' stored `paramArea / paramDepth / paramOver`). It reproduces the
  stored sidebearings:
  - Regular and Bold: **100%** within 1 unit (mean |diff| 0.03).
  - Light: **99%** within 1 unit (mean 0.10) [measured].

---

## 2. The spacing tools that ran

### 2a. HT Letterspacer (Huerta Tipográfica): the reference autospacer

- **What it is** [source]: github.com/huertatipografica/HTLetterspacer,
  GPL-3.0, maintained (last commit 2026-08-17). A Glyphs 3 plug-in only; there
  is no headless build.
- **How it spaces** [source]: per side, it measures the white between the
  glyph's outline and its extreme within a reference zone (the x's height for
  lowercase, the H's for capitals). The white is capped at a **depth**
  (15% of x-height by default) and counters are closed at 45°. It then sets
  the sidebearing so that area equals a target **area** (400 by default,
  × 1.25 for capitals).
- **It sets sidebearings only.** It writes no kerning.
- **On Albo** [measured]:
  - As shipped it is **+28 units looser** on average than where he puts the
    pairs.
  - Capitals come out at **60** error, because `Yo To Vo` get no kern.
  - Marks come out at **39**.
  - Lowercase alone scores **24.8** against doing nothing's 12.8.
  - The depth parameter is the one that matters. At depth 25 the bias falls
    to +10.6 and raw error to 22.5; at depth 10 it rises to 46.9.
- **Its structure disagrees with his.** Fitting his per-glyph corrections on
  top of HTLS (14.58) is worse than fitting them on top of nothing (10.69).
  HTLS's own per-glyph opinions are the wrong ones for Albo.
  - The italic is worse than the roman (35 against 25). HTLS measures italic
    sidebearings on the de-slanted outline, and Albo's italic was fitted to
    his eye, not to a slanted-slot rule.
- This is the premise that `local-ai-spacing-options-2026-09-26.md` §2a option
  C already tested and rejected (15.86). The real tool, run faithfully, agrees
  with that result.

### 2b. CounterSpace (Simon Cozens, funded by Google Fonts)

- **What it is** [source]: github.com/simoncozens/CounterSpace, Apache-2.0,
  last commit 2024-04-27, "experimental ... I wouldn't yet trust it to
  automatically kern a whole font".
- **How it spaces** [source]: it fits three Gaussian "lights" so that the key
  pairs `HH OO HO OH EE AV`, at the font's **own current** spacing, show equal
  lit counter-area. It then sets every pair to the lit area of its reference
  pair (`nn` if a lowercase letter is involved, `HH` otherwise).
- **It is self-calibrating to the font, and it kerns**: `space(l, r)` returns
  a full pair distance.
- **Getting it to run** [measured]:
  - Its pinned `tensorfont==0.0.6` no longer imports, because
    `skimage.util.pad` is gone.
  - `tensorfont 0.2.0` has the same API and works.
  - The `serif_smoothing` argument must be an integer, because the library
    slices arrays with it.
- **On Albo** [measured]:
  - **Every pair with a mark comes back absurd** (errors in the thousands).
    `reference_pair()` sends marks to `HH`, and the search for the matching
    area never crosses it.
  - Letter pairs only, at smoothing 0: **26.1** raw (lowercase 19.5, capitals
    70.7), still worse than doing nothing (13.15 on the same subset).
  - Its failures are capital kerns far too tight: `Vi` −170 where he wants −9,
    and `To` −109 where he wants +16.
  - The README's advice for serifed faces (smoothing 20) makes it much worse
    (94.6).
  - Inside B2 it adds nothing (10.47 against 10.42).

### 2c. Kernagic (Øyvind Kolås, 2013)

- **What it is** [source]: github.com/hodefoting/kernagic, GPL-3.0, C + GTK2,
  last commit 2019-03-27.
- **Getting it to run** [measured]:
  - It needs `brew install gtk+` (62 MB).
  - It needs a patched build line (`-D_GNU_SOURCE -D_DARWIN_C_SOURCE`), because
    stock `make` fails on an undeclared `strdup`.
  - Its batch mode is `kernagic IN.ufo -m gap -o OUT.ufo`.
  - **Trap:** the default snap is 0 and the `gap` method divides by it, so
    every advance comes back 0. `-s 1` fixes it.
- **Methods compiled in** [source]: `original` (no change), `bounds` (zero
  bearings) and `gap`. `gap` places each glyph's outermost detected stems a
  fixed fraction of the x-height (0.3) from the advance edges. The
  `gray.c` / `cadence.c` / `rythm.c` sources are in the tree and not
  registered.
- **On Albo** [measured]:
  - **+94 units** too loose.
  - Its stem detection sees an `o` with 75/80 bearings, where the font has
    37/35 and his answers barely move it. The `i` gets 100/95.
  - Even with a fitted gain it keeps only 4–9% of each move (lin 13.43).
  - It is designed for sans stems and does not read a wedge serif.

---

## 3. The spacing tools that do not run here

- **atokern / kerncritic** (Simon Cozens, 2017–19, MIT) [source, measured]:
  - A CNN trained on Google Fonts to flag badly kerned word images, not to
    produce values.
  - `kerncritic` downloads `badkerndetector.hdf5` from
    `dealer.simon-cozens.org`, and that URL returns **404** [measured]. The
    same is true of `autokerner.py`'s `kernmodel.hdf5`. No weights are
    published anywhere [web].
  - Cozens' own "Neural Kerning Log" (2019) records that a regression variant
    collapsed to a constant output, and that area-based tools did better
    [web].
  - Running it means retraining on Google Fonts under TensorFlow 1.x.
    **Not worth it:** it would be a generic prior, and §5 measures what a
    generic prior buys.
- **YinYangFit** (Sebastian Kosch, Apache-2.0, "work in progress", last commit
  2022-11-27) [source]: a V1-style filter-bank model of letterfitting.
  **Broken as published:**
  - `engine/__init__.py` has `import pyopencl as cl` commented out, while
    `set_up_gpu_processor_kernel` calls `cl`.
  - Its best-distance loop `break`s after the first distance, so the "best"
    is always the first one tried.
  - Fixing both would mean writing the model, not trying a tool.
- **FontLab 8** [web]:
  - $499.
  - Auto metrics (optical / tight / custom), and auto kerning with two
    engines (K1, K2) whose methods are undisclosed.
  - Python runs only inside the running app.
  - **How to test:** open the 2026-09-20 fonts, run auto metrics and auto
    kerning, export, then run
    `score_font.py fontlab R.ttf I.ttf; score.py fontlab`.
  - The survey predicts it will land where HTLS did, because an optical
    autospacer does not know his taste. It is worth a 30-day trial only if he
    wants a GUI.
- **Glyphs 3** ($299.90) [web]: it has no shape-based autospacing of its own.
  Metrics keys copy sidebearings by formula.
  - **KernOn** (Tim Ahrens, paid plug-in): you kern "model" pairs by hand, and
    it fills the rest consistently with them. It is the closest commercial
    analog of what B2 already does (his answers are the model pairs).
    Its engine is closed and GUI-bound. The price was not verified.
  - **BubbleKern** (Toshi Omagari): minimum-distance "bubbles", kerning only.
  - Both can be scored through `score_font.py` if he ever runs them.
- **iKern** (Igino Marini) [web]: a closed paid **service**. You send the font
  and get it back spaced and kerned, usually within a week. It is priced per
  project, with no public list.
  - It is the one tool whose makers claim a global white-space model.
  - **How to test:** send the two 2026-09-20 fonts, then score the returned
    files with `score_font.py`. That is ~50 answered pairs per style that the
    service never saw, since his answers never leave the machine.
  - **Worth it only if** he wants a professional second opinion. It cannot
    learn *his* taste, which is what B2 encodes.
- **No auto-spacing at all** [web/source]: Fontra (metrics keys are still a
  feature request), fontmake / ufo2ft / fontTools (compilers only; ufo2ft's
  kern writer writes the UFO's existing kerning), MetricsMachine and KernTool
  (manual pair editors), and SpaceCenter (a preview).
- **Frank Blokland's LeMo** [web]: a free, closed-source GUI (Mac / Win /
  Linux) for his unitized "patterning" model. It has no batch mode. Kernagic
  was begun from his research and "deviates" from it, so §2c is the nearest
  measured relative.
- **ML papers** [web]: "Learning to Kern" (Nakatsuru & Uchida, arXiv
  2402.14313, 2024; set-wise transformer on ~2,500 Google Fonts, about 5.3 px
  error) has **no code or weights released**. No other kerning or spacing
  paper with working code was found.

---

## 4. Legibility and word-image tools

### 4a. OCR at degradation as a pair judge [measured, `ocr_judge.py`]

**The question:** if a machine reader is the judge, where does it want each
gap?

**Setup:**

- **Words:** for each of the 489 answered pairs, the word it was benched in.
- **The move:** that one gap at −40 … +40 units in steps of 10, with every
  other glyph untouched.
- **Rendering:** the 2026-09-20 fonts through HarfBuzz and FreeType at 4× and
  box-filtered, so a 10-unit move is a real sub-pixel change.
- **Degradation:** four conditions, chosen by a pilot so that character
  accuracy at 0 sits at 0.50–0.66:
  - 10 px clean;
  - 12 px with blur 0.7 px;
  - 12 px with noise 0.10;
  - 14 px with noise 0.15.
- **Repetitions:** three per condition.
- **The reader:** the Kept Legibility Index's Apple Vision reader (accurate,
  language correction off). It reads at about 12 ms per image.
- **Its answer** is the vertex of a quadratic through mean character accuracy
  against the move.

**Result** [measured]:

- **No pair signal.**
  - Correlation with his answers: **+0.04**.
  - Direction right on only **50%** of the pairs where he moved 15 or more.
  - Raw error **27.61**. Even with a fitted gain it is 13.60, which is no
    better than doing nothing (95% −0.19 .. +0.07).
  - Inside B2: **+0.04**, slightly worse.
- **The reader barely cares about one gap.** Mean character accuracy over all
  489 words and every condition:

  | move (units) | −40 | −30 | −20 | −10 | 0 | +10 | +20 | +30 | +40 |
  |---|---|---|---|---|---|---|---|---|---|
  | accuracy | 0.598 | 0.610 | 0.615 | 0.604 | 0.604 | 0.621 | 0.630 | 0.633 | 0.629 |

  - The whole ±40 range moves accuracy by 3.5 points.
  - A single word's curve spans a median 24 points, which is repetition noise.
    That noise sends its "answer" to the ends of the grid (−40 on 20% of pairs,
    +40 on 17%).
- **Why** [inf]: the reader fails on letter identity (e→o, k→l, n→m; see §4b)
  long before a 10–40 unit gap matters to it. His spacing judgments live
  below the level of degradation at which a machine reader starts to fail.
  **Negative. Do not use OCR as a pair judge.**

### 4b. The Kept Legibility Index on the whole face [measured]

github.com/JessieSalas/kept-legibility-index (MIT, 2026). Twelve degraded
conditions, Apple Vision, 8 repetitions. Run with its own
`bench/score_candidate.py` against three system serifs. It took 78 s.

| face | grand mean | crowded | legible down to |
|---|---|---|---|
| Charter | 94.8% | 99.3 | 9 px |
| Georgia | 94.0% | 91.7 | 10 px |
| Times New Roman | 90.2% | 87.7 | 11 px |
| Albo 09-20 | 89.1% | 68.0 | 9 px |
| **Albo r397** | 88.1% | 63.5 | 9 px |
| Albo r395 | 87.5% | 52.6 | 9 px |
| Albo Italic r397 | 86.3% | 77.2 | 11 px |

The index calls differences under about one point ties. Its confusion counts
are single runs, so treat them as hints. With that said:

- **The roman e reads as o 131 times in round 397**, against 117 in round
  395 and **6** in the 2026-09-20 font. Georgia, Charter and Times score 0.
  - Something between 09-20 and round 395 changed how the e survives
    degradation. The rounds 391–395 thick/thin re-cuts are the obvious
    suspects [inf; not traced].
  - This is the largest single confusion in the run, and the one finding here
    worth a look by eye.
- **The `crowded` condition** (11 px, tracking −0.01 em) is the only spacing
  test in the index. It runs 09-20 68.0 > r397 63.5 > r395 52.6: the machine
  reader prefers the looser 09-20 spacing.
  - That is a tracking effect. It does not say B2's per-pair choices are
    wrong.
  - Round 397 recovered 11 points of the 13 that round 395 lost.
- Other large confusions in r397: `0→o` 57 (the 09-20 font was the same),
  `k→l` 40, `I→l` 34, `n→m` 31. The italic reads `a→e` 76 times.

### 4c. Checked and not useful

- **Fontbakery's ISO 15008 profile** (`fontbakery check-iso15008`, v1.1.0, a
  57 MB venv) [measured]: 7 FAIL, 3 PASS. The checks are bounds for **in-car
  sans display** type:
  - stem / ascender between 0.10 and 0.20 (Albo: 0.064 roman, 0.057 italic);
  - `ll` white between 1.5 and 2.4 stems (Albo: 210 units).
  - Any text serif fails them. They say nothing about his spacing.
- **Pelli-lab CriticalSpacing / NoiseDiscrimination** (MATLAB / Psychtoolbox,
  unmaintained since 2020) and **EasyEyes** (browser, MIT, active) [web]:
  these measure **human** crowding and identification thresholds. They are
  the right instrument if he ever wants human data other than his own on
  Albo's spacing. EasyEyes takes a custom WOFF2. They are not a model to run
  here.
- **Tesseract 5.5.3** is installed. It was not run as a second pair judge
  because the Vision judge's mean curve moved 3.5 points across the whole ±40 range and its pair answers correlate +0.04 with his. A second reader answering the same question would not teach anything new (the P0 rule on runs that teach nothing).

---

## 5. Is a pedigree-font prior worth building?

**Built the cheap way and measured** (`pedigree_prior.py`, 2.5 s):

- **Training faces:** seven Apple text serifs (Palatino, Hoefler Text, Iowan
  Old Style, Baskerville, Charter, Georgia and Times New Roman, roman and
  italic), plus Flanker Griffo, Coelacanth and Pagella for the italic.
- **Scaling:** each face is scaled to Albo's x-height.
- **Features:** spacing-invariant shape only. Depth profiles at 8 heights,
  closest and mean recess per band, inner white, and class flags.
- **Model:** a ridge per style, with a per-face tracking intercept.
- **Training set:** 1,694 roman and 2,470 italic rows. These are the pairs
  he answered, as each pedigree face spaces them.

**What it says** [measured]:

- **Shape predicts a pedigree face's own spacing only coarsely.** Leave one
  face out: mean error **12–26 units** after removing that face's tracking,
  even though the correlation is high (r = 0.81–0.94).
  - Well-spaced faces do not agree with each other to better than about 15
    units on the same shapes.
  - His corrections are 13 units on average. The prior's own uncertainty is
    as large as the thing it would have to predict.
- **On Albo it is the best of everything tried, and still not useful.**
  - Correlation with his answers: **+0.51** (HTLS +0.34).
  - Held out with a gain: **11.96**.
  - Inside B2: **+0.06** (95% +0.02 .. +0.11), which is slightly worse.
  - B2 already knows what the prior knows about shape, from Albo's own
    features fitted on his answers.
- **Albo is set looser than the pedigree faces**, by 36 units at equal
  x-height. That is his taste, and a prior would pull against it.

**Recommendation: do not build a larger pedigree prior.**

- A bigger version (more faces, a neural net, Google Fonts at scale) is
  atokern and "Learning to Kern" again.
- The best such model published reaches about 5 px of error on fonts it was
  trained to imitate. Here the limit is not the model's capacity. It is that
  *his* spacing is not the pedigree faces' spacing.
- His next minutes are better spent where the active bench already points
  them (`local-ai-spacing-options-2026-09-26.md` §11), and every session so
  far has moved B2's held-out score (10.73 → 10.37 → 10.33).

---

## 6. Recommendation

1. **Keep B2 as the spacing engine.** No existing tool beats it, and none
   adds anything as a feature. There is nothing to adopt.
2. **Do not buy FontLab or iKern for spacing.** If he wants a professional
   second opinion anyway, `score_font.py` scores whatever comes back, against
   his own answers, in one command.
3. **Do not build a pedigree-font prior** (§5).
4. **Look at the roman e** (§4b). A machine reader confuses it with o about
   20× more often than in the 2026-09-20 font. That is a shape question, and
   his call.
5. **The Kept Legibility Index is worth keeping as a face-level check.**
   78 s per run, on any build, against Georgia and Charter. It does not judge
   pairs.

## 7. Checked and found clean or negative

- The harness reproduces 13.66 and 10.33 exactly [measured].
- The HTLS port reproduces HTLS's own example font, 99–100% within 1 unit
  [measured].
- The white measure matches the bench zero on Albo: the 09-20 fonts score
  exactly 13.66, and the pedigree prior's own white code matches it to 0.000
  [measured].
- All three CounterSpace smoothing settings were tried. None helps.
- Four HTLS settings were tried (depth 10, 15 and 25; area is one constant per
  class, which "cal" already covers). None helps.
- Kernagic's other methods (`original` = no change, `bounds` = zero bearings)
  are trivial. Its unregistered sources were not wired in.
- Scores on the round-397 fonts agree with the 09-20 runs for HTLS, Kernagic
  and CounterSpace.

## 8. Not verified

- FontLab, Glyphs + KernOn / BubbleKern and iKern were not run. Their methods
  are closed, and their prices are from their sites.
- The OCR judge used one reader and four conditions. A different degradation
  might change its curve. A second reader was not run (§4c).
- The Kept Legibility Index confusion counts are from a single run of 8
  repetitions.

## Files

- `tools/wedge_serif/tool_survey/common.py`: answers (pinned), folds and the
  score columns.
- `tools/wedge_serif/tool_survey/score.py`: scores saved tool predictions.
- `tools/wedge_serif/tool_survey/paired.py`: the paired bootstrap.
- `tools/wedge_serif/tool_survey/score_font.py`: scores any font file.
- `tools/wedge_serif/tool_survey/htls_port.py`: the HT Letterspacer port.
- `tools/wedge_serif/tool_survey/validate_htls_port.py`: checks the port
  against HTLS's own example font.
- `tools/wedge_serif/tool_survey/run_counterspace.py`: runs CounterSpace.
- `tools/wedge_serif/tool_survey/run_kernagic.py`: runs Kernagic.
- `tools/wedge_serif/tool_survey/ocr_judge.py`: the OCR pair judge.
- `tools/wedge_serif/tool_survey/pedigree_prior.py`: the pedigree-font prior.
- `tools/wedge_serif/tool_survey/preds/*.json`: every tool's predicted white.
- `tools/wedge_serif/tool_survey/results.json`: every score.

The tools themselves (clones, venvs, the Kernagic binary) live in the session
scratchpad. Each script's docstring gives the exact install line.
