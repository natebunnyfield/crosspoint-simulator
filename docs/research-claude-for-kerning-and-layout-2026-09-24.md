# Using Claude to learn to kern and lay out words better than the owner does — research and a staged plan

2026-09-24. Research only: no code or font was changed to write this. Surveyed
against simulator `901a6ae` and the firmware checkout at `~/src/crosspoint-reader`
as it stood the same day.

Owner's ask, verbatim:

> *"come up with a plan for how to best use claude for learning how to kern and
> layout words better than I do (research tex and other respected ways to
> maximize legibility and enjoyment in reading)"*

**How sure each claim is.** Every claim carries one of three tags:

- **[repo]** means read in this repo or the firmware repo, with a file cited.
- **[src]** means checked this session against the linked source. That is
  usually an abstract, a publisher page or a tool's own documentation, not a
  full reading of the paper.
- **[inf]** means my inference or estimate, and it is labeled as one.

Any number without a tag is an estimate.

**Read §0 first.** It lists what already exists, so nothing below re-proposes
work this repo has already measured or ruled out.

---

## 0. What already exists, so this plan starts from it

### Letter spacing: the Albo bench

**[repo] The bench.** It lives at
`claude.ai/artifact/VCbkYNuYmZgV2m5Udd6ruy`. It has 396 rows, and each row is
a real English word opened at one letter pair. Rows are chosen by frequency
across the owner's 36 epubs: 2,007,794 pairs counted by
`tools/wedge_serif/pair_census.py`, and the rows cover 94.7% of letter meetings.

**[repo] The fit.** The judgments are fitted as one ridge-regularized system
with two unknowns per glyph (`rsb`, `lsb`) in `tools/wedge_serif/bench_fit.py`,
at λ = 1 (`bench_fit.py:24`).

- A letter side ships only on 4+ readings and 4+ units.
- A mark ships on 3+ readings.

**[repo] The error.** Mean |error| against his own numbers:

| Round | Pairs | Before | After |
|---|---|---|---|
| Round 308 | 329 | 13.83 | 8.61 |
| Round 344, roman | — | 14.82 (do nothing) | 9.00 |
| Round 344, italic | — | 12.53 (do nothing) | 7.66 |

Source: `docs/albo-spacing-method.md`, "The bench" and "Round 344".

### Two gaps in that fit [repo, checked by grep of `bench_fit.py`]

1. **There is no held-out validation.** The 8.61 is an IN-SAMPLE residual, so
   it flatters the model.
2. **No row has ever been re-asked.** The bench has no measure of its own test–retest noise.

Nobody yet knows whether 8.61 units is above or below the owner's own
repeatability. That single number decides whether more pair-fitting can pay at
all (§5, E1–E2).

### The device's resolution floor [repo]

- Kerns are stored in 4.4 fixed point, in pixels.
- The kern quantum is 1.16 design units on the phone at 2x and 2.31 units on the
  X3. One X3 pixel is about 37 design units (`CLAUDE.md`; the four instrument
  bugs in `albo-spacing-method.md`).
- The cursor accumulates fractional advance and snaps to whole pixels
  (`typography-possible-2026-08-25.md` §4.4).

So on the X3 a change of a few units moves a glyph by a whole pixel only
sometimes. The bench's current mean error is about a quarter of an X3 pixel.
**[inf]** Further pair work may be invisible on the device he reads on, while
still visible on the phone at 2x.

### Rulings that bound this plan [repo]

- **Tracking.** *"Leave the tracking alone"* (round 258). No whole-face
  tracking move.
- **Word space.** Roman 301 and italic 258, at a ratio of about 2.55 (round
  359). He has twice landed wider than the references' absolute value: *"stop
  proposing 0.25."*
- **Ligatures.** A frequency count picks what to DRAW, never what SHIPS. `Th`
  was withdrawn on his eye.
- **Device layout.** No runtime tracking dial and no word-space dial.
- **Justification.** Stays automatic, by measure; the threshold is a firmware
  row, default 40.
- **Hyphenation.** The Automatic mode shipped 2026-09-11 (hyphens only in the
  `[40, 50)` character band).

Sources: `crosspoint-reader/docs/typography-possible-2026-08-25.md` §7;
`auto-justification.md`; `line-breaking-2026-08-25.md` §10.

### Line breaking on the device [repo, `crosspoint-reader/docs/line-breaking-2026-08-25.md`]

**The breakers.**

| Breaker | Function | Status |
|---|---|---|
| Greedy first-fit that hyphenates | `computeHyphenatedLineBreaks` | Ships as the default |
| Total-fit DP | `computeLineBreaks` | Minimizes squared trailing slack |

- The DP **cannot weigh a hyphen candidate**, because hyphenation mutates the
  eight parallel word arrays.
- It has **no hyphen penalty**.
- Justification **stretches only and never shrinks**
  (`typography-possible` §3.10).
- The DP runs O(n × words-per-line).

**Measured quality.** Measured on host, the DP buys 4–14% on the worst line of
each paragraph (`paraWorst`) over greedy at equal hyphenation. But the shipped
greedy+hyphens beats it by 21–32% on `paraWorst`, because hyphenation moves the
page 4.5–35× more than the algorithm does (§8c–8d).

**The verdict.** *"Classical Knuth–Plass — total fit WITH hyphen points — is the
missing cell and the real prize."*

**Measured cost.**

| Measure | Figure |
|---|---|
| DP vs greedy, isolated (host) | 1.57× |
| Whole-book pagination (simulator) | +0.27 ms per page |
| ESP32-C3 cost | NOT measured |

**Hanging punctuation is already on**, at both edges (`ParsedText.cpp:325-340`).

### Reading outcomes [repo, `docs/reading-experiments.md`]

- Phase 1 logging ships. The Phase 2 randomizer is wired to nothing, by ruling.
- The power estimate (§6) says a **10% effect is reachable in weeks**, and the
  2–4% that separates two well-set faces is out of reach on any practical
  timescale.
- **Kerning will never show up in reading speed on one reader.** Plan for that
  from the start.

### Perceptual method [repo, `docs/perceptual-test-method.md`]

- Wash out between stimuli: 900 ms between trials and 350 ms between the two
  cards of one trial.
- Carry catch trials.
- Never ask a comparison he cannot make ("too close, a waste of my time").
- Spread pairings early and refine late.
- Record ties.

### His time

The zen reading goal is **5 minutes per session** (`docs/reading-allowance.md`,
2026-09-24). That is a natural unit for owner-facing sessions: ≤ 5 minutes each.

---

## 1. The respected methods — what each is, and what it offers THIS project

### 1a. Knuth–Plass total-fit line breaking (TeX)

**Source.** D. E. Knuth and M. F. Plass, "Breaking Paragraphs into Lines",
*Software: Practice and Experience* 11(11):1119–1184, 1981
([Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1002/spe.4380111102)) [src].

**The model** [src + standard TeX knowledge, inf where noted]:

- **Boxes, glue and penalties.** A paragraph is a sequence of these.
  - Boxes are glyphs and words.
  - Glue is a space with a natural width, a stretch and a shrink.
  - Penalties are candidate breaks with a cost; a discretionary hyphen is one,
    carrying `\hyphenpenalty`.
- **Adjustment ratio r.** Per line, the glue must stretch or shrink by r to
  fill the measure.
- **Badness.** About 100·|r|³, capped at 10000. The cube is what lets one
  terrible line outweigh many mediocre ones. The firmware doc (§8d) says the
  same about "the metric the mean cannot see."
- **Demerits.** Per line, (`\linepenalty` + badness)² plus the penalty², plus
  extra demerits:
  - `\adjdemerits`, when adjacent lines are in fitness classes (tight, decent,
    loose, very loose) more than one apart;
  - `\doublehyphendemerits`, for consecutive hyphenated lines;
  - `\finalhyphendemerits`, for a hyphen on the penultimate line.
- **Plain TeX defaults** [src,
  [Sojka's hyphenation tutorial](https://www.fi.muni.cz/~sojka/PB029/hyptut.pdf),
  [Wermuth, TUGboat 39:1](https://www.tug.org/TUGboat/tb39-1/tb121wermuth-adem.pdf)]:

  | Parameter | Value |
  |---|---|
  | `\pretolerance` | 100 |
  | `\tolerance` | 200 |
  | `\linepenalty` | 10 |
  | `\hyphenpenalty` | 50 |
  | `\adjdemerits` | 10000 |
  | `\doublehyphendemerits` | 10000 |
  | `\finalhyphendemerits` | 5000 |

- **Two passes.** The first pass tries without hyphenation at `\pretolerance`
  and only hyphenates if that fails. That is the same question the firmware's
  Automatic mode asks, answered per paragraph instead of per measure band.
- **Looseness.** `\looseness` asks for n more or fewer lines than optimal. It is
  used to kill widows and to pull a paragraph back.
- **Complexity** [src,
  [Wikipedia](https://en.wikipedia.org/wiki/Knuth%E2%80%93Plass_line-breaking_algorithm)]:
  O(n²) worst case and near-linear in practice with an active-node list;
  O(n) is possible via SMAWK.
- **Modern relatives** [src].
  - Chrome's `text-wrap: pretty` scores only the last four lines
    ([Chrome blog](https://developer.chrome.com/blog/css-text-wrap-pretty)).
  - WebKit's implementation scores the whole paragraph but does not combine
    well with `justify`
    ([WebKit blog](https://webkit.org/blog/16547/better-typography-with-text-wrap-pretty/)).
  - "Knuth–Plass Revisited" (DocEng 2015) extends the model
    ([ACM](https://dl.acm.org/doi/10.1145/2682571.2797091)).

**What it offers here.** Almost everything the firmware doc calls the "missing
cell":

- hyphen points as weighed candidates;
- a hyphen penalty and a double-hyphen penalty (the firmware has neither);
- fitness classes, so a loose line never sits directly under a tight one;
- shrinkable glue, which the device does not have at all today.

### 1b. Microtypography (pdfTeX, LuaTeX, the `microtype` package)

**Sources.**

- Hàn Thế Thành, *Micro-typographic extensions to the TeX typesetting system*,
  PhD thesis, Masaryk University 2000, TUGboat 21(4):317–434 [src, cited in the
  [microtype manual](https://www.tug.org/docs/latex/microtype/microtype.pdf)].
- R. Schlicht, the `microtype` manual
  ([CTAN](https://ctan.org/pkg/microtype?lang=en)) [src].

**The features, and whether each fits this device.**

| Feature | What it does | Fit for THIS device [inf unless tagged] |
|---|---|---|
| **Protrusion** (margin kerning) | Hyphens, periods, commas and quotes, and partially round letters like O, hang into the margin, so the edge *looks* straight | **Partly shipped.** The firmware hangs punctuation today (`ParsedText.cpp:325-340`) [repo]. What is missing: partial protrusion of round and diagonal letters (A, V, W, T, O, C), and a per-character protrusion *amount* table instead of all-or-nothing. It is cheap: one table in the font build, x-only, and `xpos` is already baked into the section cache. |
| **Font expansion** | Glyphs are widened or narrowed by ±1–2% per line, so justification needs less word-space variation | **Not viable on the device.** Glyphs are 4-level bitmaps (`.cpfont`), so there is no outline to scale at runtime, and "Keep 4 levels" is ruled [repo, surface-roadmap 2026-08-24]. Pre-baking ±1% cuts would double font RAM on a device holding one cut in 320 KB (`typography-possible` §5.1) [repo]. |
| **Interword-space adjustment** (`spacing`) | Per-character adjustment of the space after punctuation | Possible, as a small table in the build. Low value. |
| **Additional kerning** (`kerning`) | Space before `; : ! ?` (the French convention) | Not wanted for English. |
| **Tracking / letterspacing as a justification variable** | pdfTeX can letterspace a font. Some composers (InDesign's paragraph composer) use a ±few-% letterspace range as an extra degree of freedom beside word space | **Ruling-sensitive.** The owner declined a tracking *dial* on 2026-08-24. A ±1/16 px per-glyph adjustment *inside the justifier* is a different proposition: per line, invisible as "tracking", only used to remove gaping. It still touches the letterfit he built by hand. **Needs a ruling before any build; do not assume it is allowed.** |

### 1c. Liang's hyphenation patterns

**Source.** F. M. Liang, *Word Hy-phen-a-tion by Com-put-er*, Stanford
STAN-CS-83-977, 1983 ([TUG PDF](https://www.tug.org/docs/liang/liang-thesis.pdf))
[src].

**The method.** Competing patterns of increasing level, generated by Patgen
from a hyphenated dictionary, treated as a compression problem.

**Already in the firmware** [repo]:

- `LiangHyphenation.h`;
- English and Spanish tries only (`line-breaking` §8b);
- a minimum prefix and suffix of 2 (`typography-possible` §7).

**What is left to gain.**

- Better-quality breaks. `line-breaking` §8f already measures "hyphen quality,
  not hyphen count".
- Tries for more languages, since his corpus may contain some.

There is one newer paper worth a look:
"The Art of Hierarchical Competing Patterns: Gaussian Process Optimization of
Hyphenation", [arXiv 2609.07638](https://arxiv.org/pdf/2609.07638). I found it
by search and did NOT read it; the title alone marks it as relevant.

### 1d. Bringhurst, *The Elements of Typographic Style*

Rules cited widely [src,
[summary pages](https://www.inkwell.ie/typography/bringhurst.html),
[type.today on spaces](https://type.today/en/journal/spaces)]; the book itself
was not re-read this session:

- **Measure.** 45–75 characters, with 66 ideal. Justified text below about 40
  characters gives "white acne or pig bristles" (§2.1.2, quoted in the firmware
  doc).
- **Word space.** About M/4 for a normal text face. **Albo is ruled wider, on
  his eye**; do not re-propose M/4.
- **Leading.** Choose a basic leading suited to the face, the measure and the
  x-height. Long measures and large x-heights want more.
- **Rag.** Set ragged right with a gentle rag, a minimum line length, and no
  hyphenation of short words.

**What it offers here.** The measure rule is already the auto-justify
threshold [repo]. The leading guidance is the one open lever: the Line Spacing
ramp is "narrower than it looks" (`typography-possible` §3.2) [repo]. It is a
candidate for a reading-ledger arm, because it is plausibly a ≥10% lever
(Legge and Bigelow, below) [inf].

### 1e. Walter Tracy, *Letters of Credit* (1986): the spacing method

[src,
[n8willis/kernall tracy.md](https://github.com/n8willis/kernall/blob/master/tracy.md),
[Society of Fonts](https://www.societyoffonts.com/2018/09/19/spacing-a-font-part-1/)]

**The method.**

1. Space `n` first: half the counter width on each side, adjusted by eye in
   `nnnn`.
2. Space `o` in `nnonn`.
3. Assign every other lowercase side from those two values, by edge type:
   straight, round, diagonal, or open.
4. For capitals, use `H` and `O`, where `H` carries the largest capital bearing.

**What it offers here.** A **prior**. The bench's ridge fit shrinks toward
zero, meaning "what ships". A Tracy-structured fit would shrink each side
toward *its edge class's* value. Rounds and stems would share evidence, so a
five-reading glyph borrows strength from its class instead of from nothing.
That is exactly the "a class mean is not a finding" trap
(`albo-spacing-method.md`), inverted into a legitimate hierarchical prior.
[inf]

### 1f. Kerning practice (Adobe, Miguel Sousa; OpenType; HarfBuzz)

**OpenType mechanics.** GPOS `kern` holds PairPos Format 1 (glyph pairs) and
Format 2 (class pairs). Subtable order and precedence matter: the first
subtable that matches a pair wins, including an explicit zero. That is exactly
the bug found in `crosspoint-reader/docs/kerning-subtable-precedence-2026-09-07.md`,
where the extractor summed subtables and dropped zeros [repo].

**Sources** [src]:

- the [AFDKO feature-file spec](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html);
- the Adobe practice of shipping class kerning plus exceptions in one `kern`
  feature ([Typophile thread](http://www.typophile.com/node/29125));
- Simon Cozens, [*Fonts and Layout*](https://simoncozens.github.io/fonts-and-layout/features.html).

**The practice** [inf, standard type-design lore]:

- Space first and kern last.
- Kern classes by edge shape, then exceptions.
- Kern only what spacing cannot fix: pairs such as `To Va Ly f) ."`.
- Test in words, never in pair tables.

The bench already follows the last rule (real words).

**On the device** [repo]:

- The `.cpfont` class matrix holds `uint8` class IDs and 4.4 kerns.
- `hb-shape` was used as the reference when verifying the extractor fix.
- **Use HarfBuzz as the oracle for every future kern-table change.**

### 1g. Frank Blokland: LeMo and the "harmonics" of Latin type

**Source.** Blokland's PhD, Leiden 2016: *Harmonics, Patterns, and Dynamics in
Formal Typographic Representations of the Latin Script* [src,
[lettermodel.org](https://www.lettermodel.org/),
[biography](https://www.lettermodel.org/biography.html)].

**The thesis.** Renaissance roman and italic type was *unitized*: stems and
counters sit on a rhythm, and spacing follows from that rhythm. LeMo is the
resulting auto-spacing software.

**What it offers here.** A *rhythm* check rather than a white-area check:

- measure stem-to-stem distance across word images;
- flag pairs that break the face's own period.

That is the "Measure 4" family (2-D closest approach) in a different basis.
Albo is aldine-derived, so Blokland's italic analysis is directly on topic.
[inf]

### 1h. Autospacing tools and their assumptions

| Tool | Method | Status [src] | Relevance here |
|---|---|---|---|
| **HT Letterspacer** (Huerta Tipográfica) | Sets bearings so the white *area* in a band beside each glyph hits a target, with a depth limit and an x-height band | Open source, Glyphs macro ([GitHub](https://github.com/huertatipografica/HTLetterspacer), [tutorial](https://tutorial.letterspacer.huertatipografica.com/)) | An area model. `albo-spacing-method.md` Measure 2 (mean gap across the band) is its cousin and **failed here**: it counts an open letter's splay as spacing |
| **iKern** (Igino Marini) | Proprietary; theory described, algorithm unpublished | Service ([Typographica](https://typographica.org/on-typography/automated-kerning-with-ikern/)) | Not reproducible. Useful only as "a professional service exists" |
| **Kernagic** (Øyvind Kolås) | Several strategies, including a "cadence" (rhythm) mode | Standalone, UFO ([kernall survey](https://github.com/n8willis/kernall)) | The cadence mode is a LeMo cousin |
| **YinYangFit** (Sebastian Kosch) | Neuroscience-inspired: evenness as texture perception, balance as competition between gestalt groups, legibility as n-gram detection | Research project, partly Google-funded ([site](https://skosch.github.io/YinYangFit/)) | **The most relevant model for "perceptual models of white space"** (§3c) |
| **atokern** (Simon Cozens) | A neural network discriminating well- from badly-kerned word images | 2017–19 ([GitHub](https://github.com/simoncozens/atokern), [log](https://simoncozens.github.io/neural-kerning-log/)) | His own warning [src]: 98% right means 2% *confidently* wrong, which is 1,800 errors over 300×300 pairs. That is the reason a model here only *proposes* and the owner *rules* |

### 1i. Legibility research that constrains what "better" can mean

**Letter spacing.** Chung 2002 (*IOVS* 43:1270): RSVP reading speed **peaks at
standard letter spacing** and falls for both tighter and looser spacing
([IOVS](https://iovs.arvojournals.org/article.aspx?articleid=2200181)) [src].

- Loosening past normal does not help fluent readers.
- Consequence here: letter-spacing work is about *evenness and beauty*, not
  speed. Do not promise reading-speed gains from kerning.

**Crowding.** Pelli and Tillman 2008 (*Nat. Neurosci.* 11:1129): critical
spacing and "the uncrowded window" limit reading speed
([Nature](https://www.nature.com/articles/nn.2187)) [src].

- It sets a *floor*: pairs must not crowd.
- Above the floor there is no gain.
- `cmp_touch.py`'s collision sweep is the floor's gate [repo].

**Print size.** Legge and Bigelow 2011 (*JoV* 11(5)): the fluent range runs
from about 0.2° to 2° of x-height; below the critical print size speed
collapses ([JoV](https://jov.arvojournals.org/article.aspx?articleid=2191906))
[src].

- Size and leading are the levers large enough for the reading ledger to see.
  Kerning is not.
- MNREAD's critical-print-size method
  ([MNREAD](https://mnread.umn.edu/reading-measures)) [src] is the model for a
  one-reader size calibration.

**Letter design.** Beier and Larson 2010 (*Information Design Journal* 18:2):
variants of frequently misrecognized letters were tested at distance and at
short exposure, and some variants were measurably more legible
([PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/06/Beier-Larson-2010-Design-Improvements-for-Frequently-Misrecognized-Letters.pdf))
[src].

- The method, glance and threshold tasks on letter variants, is the right one
  for Albo's *letter shapes* (`albo-figure-options`, the g), not for spacing.

**Serifs.** Arditi and Cho 2005 (*Vision Research*): serifs make no difference
to reading speed ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0042698905003007))
[src]. A caution against legibility claims about style features.

**Glance legibility.** Dobres et al. 2016 (*Ergonomics* 59(10)): an adaptive
staircase (lexical decision) measures glance legibility by typeface, size and
**polarity** ([PubMed](https://pubmed.ncbi.nlm.nih.gov/26727912)) [src].

- **This is the method for a JND or threshold experiment here** (E1).

**Individual differences.** Wallace, Bylinskii, Dobres et al. 2022 (*ACM
TOCHI*), "Towards Individuated Reading Experiences": individuals' fastest font
beat their slowest by 35% without loss of comprehension, and the best font
differs by person ([ACM](https://dl.acm.org/doi/10.1145/3502222),
[Readability Matters](https://readabilitymatters.org/articles/towards-individuated-reading-experiences))
[src].

- It supports optimizing for ONE reader, which is what this repo does.
- [inf] Their fastest-vs-slowest gap spans very different fonts. It is not the
  gap between two tunings of one face.

**Adaptive fonts.** Kadner, Keller and Rothkopf, "AdaptiFont", CHI 2021: a
generative font space (NMF over classic fonts) plus **Bayesian optimization on
measured reading speed**, per reader
([ACM](https://dl.acm.org/doi/10.1145/3411764.3445140),
[code](https://github.com/RothkopfLab/AdaptiFont)) [src].

- **The closest published analog to this plan's end state.**
- [inf] Check their session counts and effect sizes before copying the design.
  I read the abstract only.

**Aesthetics.** Larson and Picard 2005, "The Aesthetics of Reading", and
Larson et al. 2006, "Measuring the Aesthetics of Reading" (Microsoft Research).
Good against bad typography of a *New Yorker* issue, read for 20 minutes, did
not change reading speed. It changed **mood**, measured by cognitive tasks
known to shift with positive affect
([PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/06/Larson-Hazlett-Chaparro-Picard-2006-measuring-the-aesthetics-of-reading.pdf))
[src, abstract level].

- **This is the "enjoyment" half of the ask, and it is the one measure that
  might move with spacing quality.**

**Justification vs ragged.** Gregory and Poulton 1970: justification is worse
at about 38 characters and shows no disadvantage by about 66 [repo, cited in
firmware `line-breaking` §10c].

**Regressions.** Schotter, Tran and Rayner 2014 (*Psych. Sci.* 25:1218):
blocking regressions (RSVP-like) hurts comprehension
([Sage](https://journals.sagepub.com/doi/10.1177/0956797614531148)) [src].

- Any "reading speed" protocol must allow normal page reading with
  regressions, **not** RSVP.

**The field.** Readability Research: An Interdisciplinary Approach
([arXiv 2107.09615](https://arxiv.org/pdf/2107.09615)) [src]. It is the field
overview from the same group.

---

## 2. What "better than I do" can honestly mean

**The problem.** The owner is both the designer and the only reader. Spacing
has no external ground truth, and the reading-speed ledger cannot resolve
spacing-sized effects (§0). So "better" must be defined *before* any work
starts, or every result will be re-read to fit.

**Four defensible definitions, strongest first** [inf]:

1. **Blind self-preference.** A layout or spacing that he, blind and after a
   delay, prefers over his own hand-set version, at a rate above his measured
   catch-trial noise.
   - This is the primary outcome.
   - It needs catch trials and a delay of days, so he is not recognizing his own
     choice.
2. **Consistency beyond his own.** A model whose held-out prediction error is
   *smaller than his test–retest error*.
   - At that point the model is a better estimate of "what Nate wants" than
     any single judgment Nate makes. This is the literal sense in which a
     learned model can kern better than its teacher: it averages away his noise.
   - Measurable within weeks (E1–E2).
3. **Worse-case avoidance.** Fewer and smaller extreme failures on his own
   corpus:
   - the loosest line per paragraph (`paraWorst`);
   - rivers;
   - consecutive hyphens;
   - touching pairs;
   - pairs off the face's own rhythm.

   Objective and offline, with no owner time. A human hand-setting pages cannot
   look at 2 million pairs or every paragraph of 36 books; a program can.
4. **Reading outcomes.** Characters per minute and completion, measured by the
   ledger, *for levers large enough to see*: size, leading, measure, breaker.
   Plus a one-tap enjoyment rating per session (Larson and Picard's lesson:
   typography moves mood before speed).

**Anything that fails (1) is not better, whatever (3) says.** That is the
ligature rule generalized: *measure to choose what to attempt; render to decide
what ships.*

---

## 3. How Claude can go further than the current bench

### 3a. Measure the noise floor first (test–retest plus held-out error)

- **Re-ask 40 already-judged rows.** Mix them into ordinary bench sessions
  without marking them, and spread them over at least 3 days.
- **Report the owner's own repeatability** as mean |Δ| in units, per class.
- **Replace the in-sample 8.61** with a k-fold (e.g., 10-fold) cross-validated
  error from `bench_fit.py`, and tune λ by cross-validation instead of fixing it
  at 1.

Decision rule [inf]:

- If held-out error ≈ retest error, **stop pair-fitting.** The bench has
  converged and more rows buy nothing.
- If held-out error > retest error, the *model* is the bottleneck. Add
  structure (§3b), not rows.

### 3b. A better model: hierarchical, shape-aware, still his

- **Tracy prior.** Each glyph side shrinks toward its edge class (stem, round,
  diagonal, open, overhang) instead of toward zero. Classes come from
  Measure 4 geometry, not from a hand label.
- **Shape features.** Predict a pair's desired white from both sides' 2-D
  profiles: closest approach, open area at x-height, ascender and descender
  overlap.
  - Features in, his judgments as targets.
  - A small ridge or GP regression.
  - This generalizes to glyphs he has not judged: the Greek of
    `albo-greek-2026-09-23.md`, new marks, the bold.
- **Keep the floors.** A side ships only on evidence (4+ readings and 4+ units).
  A model prediction for an unjudged glyph is a **proposal rendered into a word
  image for him to rule**, never a shipped number.

### 3c. Active learning: choose the next row, do not just take the next frequent one

Rows are chosen by frequency today. That is the right *weight* and the wrong
*selector*.

**Select by expected information × frequency.**

- Score = the model's posterior variance on a pair's white, times the pair's
  corpus count, times a visibility factor.
- The visibility factor is 0 when the predicted change is below the X3 pixel
  quantum *and* the phone's JND (E1).

**Interleave four kinds of row:**

- the top-scoring rows;
- about 10% catch trials, meaning repeats of earlier rows;
- about 5% identity trials, where the shipped value is the answer;
- rows that probe a *class*, such as the first reading of an edge pairing.

**Stop rule.** Stop when the expected reduction in frequency-weighted error per
session drops below his retest noise.

**Cite for the principle**: AdaptiFont's Bayesian optimization loop [src].

### 3d. Pairwise comparison (2AFC / Bradley–Terry) — where it beats the slider

The slider is a **method of adjustment**. It gives magnitude and is efficient
for one-dimensional pair white; keep it for pairs.

**Whole-paragraph layout has no scalar knob**, for example greedy vs
Knuth–Plass, or protrusion on vs off. There, use **2AFC with a tie option**,
aggregated by Bradley–Terry.

- Model annotator reliability as in **Crowd-BT** (Chen, Bennett,
  Collins-Thompson and Horvitz, WSDM 2013)
  ([ACM](https://dl.acm.org/doi/10.1145/2433396.2433420)) [src].
- For one annotator, the useful piece is a per-session reliability term fitted
  from catch trials [inf].
- Follow `perceptual-test-method.md` exactly: spread early and refine late;
  guard repeats; record ties; check the arithmetic (games = 2 × comparisons).
- **Budget** [inf, binomial arithmetic]. To detect a true 70/30 preference at
  p < 0.05 two-sided, about 40 non-tied trials are needed (z ≈ 2.5). A 60/40
  preference needs about 200. So **only offer layout comparisons whose
  difference is large enough to be decisive in ≤ 40 trials**. That is the
  dE-20 lesson of the phosphor run, transposed to type.

### 3e. A perceptual model of white space as a critic, not an oracle

**Build.** A YinYangFit-style scorer [src for the approach; implementation
here is inf]. Band-pass filter the rendered word image at reading size and the
device's own pixel grid, then measure:

- **Evenness.** The variance of local white energy along the line.
- **Grouping.** Whether a pair's white exceeds the within-letter white nearby.
  This is `albo-spacing-method.md`'s principle: the space between letters is
  judged against the space inside them.

**Use.**

- Run it over the 2M-pair census, weighted by frequency, and **rank outliers
  against the seven reference faces**.
- Its top 20 become candidate bench rows (§3c).
- It *never* sets a number.

This is "Claude as adversarial critic against references".

**The trap it must be built to avoid.** Measures 1–3 in
`albo-spacing-method.md` each failed plausibly. Every new measure must first
reproduce the verdicts the owner already ruled before its ranking is trusted.
That means a **calibration gate**: it must agree with ≥ 80% of his ruled
bench signs, held out.

### 3f. TeX-quality paragraph layout, proved on the ACTUAL panel

**Offline, in the firmware's own host harness** (`test/line_break_quality`
[repo]). Add a third breaker: a true Knuth–Plass with Liang hyphen points as
penalty items.

- Implement it non-destructively: consume `Hyphenator::breakOffsets` without
  mutating the eight arrays (`line-breaking` §1) [repo].
- Add a hyphen penalty, a double-hyphen penalty, fitness classes, and optional
  shrink.

**Report on his corpus**, using the doc's own metrics:

- mean, p95, p99, `paraWorst`;
- rivers;
- hyphen runs;
- hyphen quality.

Report at the X3's 512 px measure and the phone's measure, at his actual font
and size, **against the shipped default** (greedy + hyphens). §8d's lesson is
that the right baseline is the shipped one, not the other DP.

**Proofs.** Render real pages through the simulator at X3 render scale 1, which
is device-exact. Crop native-pixel, PNG and lossless, per CLAUDE.md's proof
rules. Pair the same paragraph under both breakers for 2AFC (§3d).

**No owner time is needed until the offline numbers win.**

### 3g. What Claude should NOT be used for

- **Setting numbers directly from a model.** The atokern warning, and the
  `Th` ligature.
- **Re-litigating ruled questions.** Tracking, M/4, a word-space dial, a
  Justified/Ragged row, deeper glyph bit depth.
- **Claiming reading-speed effects for spacing.** Chung 2002 and the ledger's
  power (§0, §1i).
- **Building a proof from an unverified environment.** The round-344 `Foot`
  reading of +9 where the truth was −41 came from building without
  `build_env.sh`. Every before/after proof sources `albo_build`.

---

## 4. The staged plan

Owner time is the scarce input. Each owner-facing session is **≤ 5 minutes**,
matching the zen reading goal. At about 8 s per slider row, that is about 35
rows. At about 6 s per 2AFC trial plus the washout, it is about 40 trials.
[inf]

### Stage 0 — instruments and honesty (no owner time; days)

1. **`bench_fit.py --cv`.** k-fold held-out error, λ by cross-validation, and
   per-class residuals. Record in-sample and held-out side by side in
   `albo-spacing-method.md`.
2. **Catch-row support** in the bench artifact: re-ask rows, unmarked, and
   store both readings.
3. **Visibility table.** For every glyph pair, the device-pixel movement a
   given unit change produces on the X3 (1x) and the phone (2x), from the 4.4
   quantization and the fractional cursor. This filters out invisible
   proposals.
4. **Calibration gate for any perceptual scorer** (§3e) against his ruled
   signs.

### Stage 1 — his noise floor and his thresholds (3–4 sessions × 5 min)

- **E1: the JND staircase**, below.
- **E2: test–retest**, below.

This decides whether pair work continues at all.

### Stage 2 — Knuth–Plass offline, then on his eye (offline days; then 2 sessions)

1. **E3.** Build the true-KP breaker in the host harness and sweep it.
2. **E4.** Only if E3 wins on `paraWorst` and p95 without raising hyphen runs:
   run a blind 2AFC of about 40 paragraph pairs across 2 sessions.

### Stage 3 — active-learning bench plus the shape model (ongoing; ≤ 1 session a week)

- **E5.** Hierarchical, shape-aware fit plus uncertainty-driven row selection,
  scored on held-out error against the retest floor.
- **E6.** Critic-proposed outlier rows from the whole-corpus census.

### Stage 4 — reading outcomes for big levers only (needs a ruling on Phase 2)

- **E7.** A randomized arm on **leading** or **breaker**, both plausibly
  ≥ 10% levers, with a one-tap end-of-session enjoyment rating.
- **Color stays frozen** unless ruled otherwise.

### What the firmware would need for Knuth–Plass on the ESP32-C3

**Estimates, not measurements. No device timing exists
(`line-breaking` §4) [repo].**

**Working set per paragraph** [inf]:

- A 200-word paragraph with about 0.5 legal hyphen points per word gives
  n ≈ 300 break candidates.
- **Array DP** (the existing `computeLineBreaks` shape, extended with 4 fitness
  states): `dp[n][4]` as int32 plus `prev[n][4]` as uint16 is about 7 KB.
- **Classic active or passive node lists**: about 28 bytes per node, at worst
  about 1,200 nodes, which is about 34 KB. Typically a few hundred nodes, about
  8–17 KB.
- **Prefer the array form.** The heap is the device's known failure mode:
  `reading-path-heap-budget-2026-09-10.md` records two heap-exhaustion crash
  reports [repo]. The array form's size is known up front and can be refused
  cleanly, falling back to greedy.

**Time** [inf]:

- The existing DP measured 1.57× greedy on host, and pagination +47% ≈ +0.27 ms
  per page on the simulator [repo].
- Adding hyphen candidates multiplies n by about 1.5, and the prefix widths of
  fragments must be measured. `getTextAdvanceX` on the fragments is likely the
  dominant new cost, not the DP.
- Expect about 2–3× greedy on host. Pagination is lazy and chapter-bounded on
  the device, so the cost lands at chapter open, not per page turn.
- **Measure on a device before promising anything.**

**Cache** [repo, `typography-possible` §1]:

- The breaker changes `xpos`, so it needs a `ReaderRenderSpec` value.
- The existing `hyphenationEnabled` byte already carries 0/1/2. A new value 3
  would repaginate only cards that choose it.
- **`SECTION_FILE_VERSION` should not need to move** if the byte's meaning is
  extended rather than the header reshaped. Verify, as §10e did.

**Shrink** [repo + inf]:

- Justification stretches only today.
- KP with shrinkable glue (e.g., word space down to about 0.8 of natural) is
  where the biggest `paraWorst` gains usually come from [inf].
- It changes the look of tight lines, so **it is a separate arm and needs its
  own ruling.**

**Protrusion table** [inf]:

- Add a per-codepoint protrusion amount (for example 1/16 px units) to the
  `.cpfont` build.
- The header's reserved bytes exist, but they are hashed into `contentHash`,
  so any use invalidates every section cache on every card
  (`typography-possible` §5.2) [repo]. Price that before building.

---

## 5. First experiments, ranked

The effect sizes are **[inf] estimates**, stated so that the result can
surprise.

| # | Experiment | Owner time | What it decides | Expected effect | How it is detected |
|---|---|---|---|---|---|
| **E1** | **JND staircase for pair white.** Word images (`nnonn` style plus real words) at reading size on the phone at 2x and on the X3 at 1x. A 2AFC "which is evenly spaced", QUEST-style adaptive steps (the Dobres et al. method), about 60 trials per device, catch trials included | 3 × 5 min | The smallest unit change he can see, per device. Every future proposal below it is dropped | JND around 15–40 units on the X3 (about ½–1 px) and lower on the phone [inf] | 75% threshold with a bootstrap CI; a catch-trial error rate under about 10% validates the session |
| **E2** | **Bench test–retest plus held-out error.** 40 unmarked repeats and `bench_fit --cv` | 1–2 × 5 min | Whether pair-fitting has converged (held-out ≈ retest) | Retest mean \|Δ\| around 8–15 units, held-out error around 10–12 [inf] | Direct comparison with CIs. If held-out is below retest, the model already beats his single judgment (§2 def. 2) |
| **E3** | **True Knuth–Plass (hyphen penalty, fitness classes) in `test/line_break_quality`**, swept against greedy + hyphens | 0 | Whether the "missing cell" is worth building | `paraWorst` 5–20% better than the shipped default at equal or fewer hyphens [inf; the DP's 4–14% gain at equal hyphenation, §8d, is the anchor] | The doc's own sweep. The win must hold in ≥ 5 of 6 configurations, and hyphen runs must not rise |
| **E4** | **Blind 2AFC: KP vs shipped, real pages, device-exact crops** | 2 × 5 min | Whether E3's number is visible to him | Preference around 60–75% for KP if E3 wins by 15% or more [inf] | About 40 non-tied trials, Bradley–Terry, ties recorded, catch trials. p < 0.05 needs about 70% |
| **E5** | **Hierarchical, shape-aware bench fit plus active row selection** | 0 now; ≤ 5 min a week | Generalization to unjudged glyphs (Greek, bold, marks) | Held-out error falls by about 10–20% vs the flat ridge [inf] | k-fold CV. Plus a prospective test: predict before he judges new rows, and score after |
| **E6** | **Critic outliers**: a white-space scorer, gated on his ruled signs, ranks the census and 20 outliers become bench rows | 1 × 5 min | Whether a perceptual model finds faults he did not | Around 5–8 of 20 are confirmed as moves [inf] | His slider on each: confirmed if \|move\| exceeds the E1 JND |
| **E7** | **Reading-ledger arm on leading (or breaker)**, randomized per session, one-tap enjoyment rating | Ordinary reading | A reading-outcome answer for one big lever | Around 5–10% chars/min between extremes of the leading ramp [inf; per Legge and Bigelow, size and spacing levers are the large ones] | `reading-experiments.md` §6 power: weeks of reading. **Needs a Phase 2 ruling** |

**Order of operations.** E2 and E3 first: they are cheap and they gate the
rest. Then E1, then E4, then E5 and E6. E7 waits on a ruling.

---

## 6. The traps, from this repo's own record

Each one has already cost a round here. **Re-read before running any of the
above.**

**Bench and fit** (`albo-spacing-method.md`):

1. **A mislabeled row.** `away` rendered `a y`. Rebuild every label from its own
   index.
2. **The wrong codepoint.** U+0027 was rendered while U+2019 was keyed.
3. **Summing advances instead of `rsb + kern + lsb`.** Use `gap_measure.py`.
4. **A wrong device quantum**, off by 16×.
5. **Fitting halves separately.** Each half absorbs the other's error.
6. **A class mean read as a finding.**
7. **A complete model added on top of the constants it replaced.** It
   double-counts.
8. **A proof built without the shipping environment.** `Foot` read +9 where the
   truth was −41. Use `albo_build`.
9. **Frequency ≠ quality.** `Th`.
10. **A tracking or word-space proposal that re-opens a ruling.**

**Line breaking** (`line-breaking-2026-08-25.md`):

11. A comparison confounded by hyphenation (§8c).
12. Mean and sd hide the worst line (§8d).
13. A dead axis produces identical rows, so pin a precondition that the axis is
    live.

**Perceptual testing** (`perceptual-test-method.md`):

14. Comparisons too close to call.
15. Closest-rated pairing that manufactures coin flips.
16. No catch trials.
17. Analyzing a variable the stimulus does not render.

**Method** (`albo-method.md` §10):

18. Tuning a model not yet verified as the right model. *Before you turn a
    dial, measure whether the thing the dial controls is the thing that is
    wrong.*

**Reading experiments** (`reading-experiments.md` §3):

19. Pages per minute instead of characters per minute. It manufactures a
    font-size effect.

---

## 7. Checked and found already done (do not re-propose)

- **Hanging punctuation, both edges** [repo, `ParsedText.cpp:325-340`].
- **Automatic justification by measure** [repo, `auto-justification.md`].
- **Automatic hyphenation in the `[40, 50)` band** [repo, `line-breaking` §10].
- **Class kerning with correct subtable precedence**, verified with `hb-shape`
  [repo, `kerning-subtable-precedence-2026-09-07.md`].
- **Per-family `tracking_em` and `word_space_em`, baked at build**
  [repo, `typography-possible` §4.4].
- **Widow and orphan control, keep-2/2** [repo, `typography-possible` §3.4].
- **Word-frequency pair census across his 36 epubs** [repo, `pair_census.py`].
- **A 2-D closest-approach spacing measure** [repo, `cmp_space_2d.py`].
- **Collision sweep** [repo, `cmp_touch.py`].

## 8. Not verified

- None of the papers was read beyond abstracts or summary pages. In particular,
  AdaptiFont's session counts, Larson and Picard's effect sizes, and Bringhurst's
  exact wording were not checked.
- The TeX default values come from TUG articles, not the TeXbook itself.
- No ESP32-C3 timing or heap figure for any breaker exists. §4's figures are
  arithmetic.
- KernType-style drills (Mark MacKay's `type.method.ac` game) were considered as
  owner *training*. Not researched further: the ask is for the system to learn
  his taste, and a public game scores against someone else's.

## Sources

- Knuth and Plass 1981: https://onlinelibrary.wiley.com/doi/abs/10.1002/spe.4380111102
- Knuth–Plass (Wikipedia): https://en.wikipedia.org/wiki/Knuth%E2%80%93Plass_line-breaking_algorithm
- Knuth–Plass Revisited, DocEng 2015: https://dl.acm.org/doi/10.1145/2682571.2797091
- Chrome `text-wrap: pretty`: https://developer.chrome.com/blog/css-text-wrap-pretty
- WebKit `text-wrap: pretty`: https://webkit.org/blog/16547/better-typography-with-text-wrap-pretty/
- Sojka, hyphenation tutorial for TeX users: https://www.fi.muni.cz/~sojka/PB029/hyptut.pdf
- Wermuth, TeX's additional demerits, TUGboat 39:1: https://www.tug.org/TUGboat/tb39-1/tb121wermuth-adem.pdf
- microtype manual: https://www.tug.org/docs/latex/microtype/microtype.pdf · CTAN: https://ctan.org/pkg/microtype?lang=en
- Liang 1983: https://www.tug.org/docs/liang/liang-thesis.pdf
- Hyphenation GP optimization (not read): https://arxiv.org/pdf/2609.07638
- Bringhurst summaries: https://www.inkwell.ie/typography/bringhurst.html · https://type.today/en/journal/spaces
- Tracy method: https://github.com/n8willis/kernall/blob/master/tracy.md · https://www.societyoffonts.com/2018/09/19/spacing-a-font-part-1/
- AFDKO feature file spec: http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html
- Class kerning practice: http://www.typophile.com/node/29125
- Cozens, Fonts and Layout: https://simoncozens.github.io/fonts-and-layout/features.html
- atokern: https://github.com/simoncozens/atokern · https://simoncozens.github.io/neural-kerning-log/
- Blokland / LeMo: https://www.lettermodel.org/ · https://www.lettermodel.org/biography.html
- HT Letterspacer: https://github.com/huertatipografica/HTLetterspacer · https://tutorial.letterspacer.huertatipografica.com/
- iKern: https://typographica.org/on-typography/automated-kerning-with-ikern/
- kernall survey (Kernagic et al.): https://github.com/n8willis/kernall
- YinYangFit: https://skosch.github.io/YinYangFit/
- Chung 2002: https://iovs.arvojournals.org/article.aspx?articleid=2200181
- Pelli and Tillman 2008: https://www.nature.com/articles/nn.2187
- Legge and Bigelow 2011: https://jov.arvojournals.org/article.aspx?articleid=2191906
- MNREAD measures: https://mnread.umn.edu/reading-measures
- Beier and Larson 2010: https://www.microsoft.com/en-us/research/wp-content/uploads/2021/06/Beier-Larson-2010-Design-Improvements-for-Frequently-Misrecognized-Letters.pdf
- Arditi and Cho 2005: https://www.sciencedirect.com/science/article/pii/S0042698905003007
- Dobres et al. 2016: https://pubmed.ncbi.nlm.nih.gov/26727912
- Wallace et al. 2022: https://dl.acm.org/doi/10.1145/3502222 · https://readabilitymatters.org/articles/towards-individuated-reading-experiences
- AdaptiFont: https://dl.acm.org/doi/10.1145/3411764.3445140 · https://github.com/RothkopfLab/AdaptiFont
- Larson et al. 2006: https://www.microsoft.com/en-us/research/wp-content/uploads/2021/06/Larson-Hazlett-Chaparro-Picard-2006-measuring-the-aesthetics-of-reading.pdf
- Schotter, Tran and Rayner 2014: https://journals.sagepub.com/doi/10.1177/0956797614531148
- Readability research overview: https://arxiv.org/pdf/2107.09615
- Crowd-BT: https://dl.acm.org/doi/10.1145/2433396.2433420
