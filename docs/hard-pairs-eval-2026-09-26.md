# The five hardest kerning pairs, judged by every cheap method we have (2026-09-26)

Owner, 2026-09-26: *"let's evaluate the five hardest kerning pairs in cheaper
models and vision addon and local options (mechanical and mixed with ai),
explain them all"*.

This follows `docs/local-ai-spacing-options-2026-09-26.md` (read its §2 for
the whole-bench numbers). That doc measured every method on all 370 bench
pairs. This one takes the five pairs the best model gets **most wrong** and
asks every method, one by one, what it would do with them.

Everything here was run on this Mac mini (Apple M4, 32 GB) on 2026-09-26,
with the tree at `86711b4` plus the scripts added by this commit. Labels:
**[measured]**, **[repo]** (read from a file), **[inf]** (inferred).

The scripts are all in `tools/wedge_serif/local_ai/`:

| script | job |
|---|---|
| `hard5_common.py` | every reading he has given, on one zero |
| `hard5_select.py` | picks the five |
| `hard5_stimuli.py` | renders the ladders and the 2AFC trials |
| `hard5_mech.py` | methods a, b, c, d, e, and the g2 ensemble |
| `hard5_vlm.py` | method f (local VLM) and the g1 mixed arm |
| `hard5_score.py` | the table and the position-bias checks |

Outputs (not committed; the scripts regenerate them): `$HARD5_DIR` =
`/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/c03d2901-2d80-4074-84f8-7539dfb0f2e2/scratchpad/hard5/`.

---

## 0. The answer in one table

**Units.** Every number is in design units on the **2026-09-20 zero**. That is
the font every bench and re-ask answer was given against. One pixel at the
reader's 54 px is 18.5 units.

**His answer** is the mean of his two readings of each pair.

| pair | his | a nothing | b shipped ridge | c B2 | d optical | e DINOv2 | e SigLIP | f VLM ladder | g1 B2 → VLM | g2 B2 + SigLIP |
|---|---|---|---|---|---|---|---|---|---|---|
| italic **Fo** (*For*) | **−36.5** | 0 | +8.0 | −16.8 | −64.1 | +5.4 | −2.7 | −25.5 | −13.9 | −9.8 |
| roman **Wa** (*Wayward*) | **+40.5** | 0 | +17.0 | +22.6 | +67.0 | +2.2 | +10.3 | +46.3 | +23.1 | +16.5 |
| italic **n'** (*don't*) | **−23.5** | 0 | 0.0 | −6.1 | −63.5 | −0.4 | −11.4 | −4.6 | +4.6 | −8.8 |
| roman **ed** (*named*) | **+30.5** | 0 | +5.0 | +14.9 | +29.7 | +9.7 | +3.5 | 0.0 | +18.5 | +9.2 |
| roman **it** (*with*) | **+32.0** | 0 | +16.0 | +16.6 | +5.1 | −1.1 | +8.0 | −37.0 | +27.8 | +12.3 |
| **mean \|error\|** | | **32.6** | **26.6** | **17.2** | **24.4** | **31.4** | **25.4** | **27.0** | **16.9** | **21.3** |

**What it says** [measured]:

1. **No method reaches these five.** The best, B2, is still 17 units off. That
   is almost a whole pixel at 54 px, and about 1.6 times his own
   repeatability (10.83).
2. **B2 is still the best single method.** Every learned or AI method is
   worse, alone or mixed with it. Averaging it with the vision add-on (g2,
   21.3) pulls it **toward zero**, and zero is where these pairs are wrong.
3. **The local VLM's numbers are noise.** It gave the letter **A** to 36 of
   40 ladders, wherever A sat in the list. In the 2AFC it answered
   "**2**" (the bottom line) 59 times in 60. Its 27.0 is wherever the
   shuffle happened to put an A (§3f).
4. **The mixed arm (g1, 16.9) is B2 plus nothing.** The VLM chose among B2's
   three nearest rungs. Snapping B2 to its own nearest rung gives 17.8. The
   VLM **never** picked the first image shown (0 of 20). When the order was
   reversed it kept its answer only 1 time in 10 (§3g).
5. **The five are hard for a shared reason.** He wants these pairs **much
   farther** from the zero than any model thinks (|his| 23–41, all
   confident). Every model **shrinks toward zero**. The two that do not
   shrink, the optical rule and the VLM, also go the wrong way on some
   pairs.

**Selection bias.** These five were picked **because** B2 misses them. B2's
17.2 here is the worst case by construction. Its error on the whole bench
is 10.73 (§2a of the options doc) [measured].

---

## 1. Which five, and why they are hard

### The criterion

This was computed from the data, not chosen by hand
(`hard5_select.py`, [measured]).

1. **Candidates are the pairs he answered more than once.** Readings come from
   the bench, the re-ask, the outlier bench, and active session 1, each
   converted to the 09-20 zero. That gives **59 pairs**, so his answer for
   each is a mean rather than one noisy slider.
2. **A pair is "confident" when all three hold:**
   - |mean| ≥ 20 units;
   - every reading has the same sign as the mean;
   - the spread (max − min) is at most the larger of 15 units and half the
     mean.

   **12 of the 59 pairs qualify.**
3. **Hardness is B2's miss when the pair is held out.** B2 is the shipped
   B2: bench plus every extra reading, skip weight 1. It is **refit without
   any reading of the pair**, and the miss is |B2's prediction − his mean|.
4. **The top five confident pairs by miss are the set.**

The 12 confident pairs, in order of miss:

| style | pair | his readings | his mean | spread | B2 held out | miss |
|---|---|---|---|---|---|---|
| italic | **Fo** | −40 bench, −33 re-ask | −36.5 | 7 | −16.8 | **19.7** |
| roman | **Wa** | +41 bench, +40 re-ask | +40.5 | 1 | +22.6 | **17.9** |
| italic | **n'** | −18 bench, −29 outlier | −23.5 | 11 | −6.1 | **17.4** |
| roman | **ed** | +28 bench, +33 outlier | +30.5 | 5 | +14.9 | **15.6** |
| roman | **it** | +30 bench, +34 re-ask | +32.0 | 4 | +16.6 | **15.4** |
| italic | Yo | +57, +52 | +54.5 | 5 | +40.0 | 14.5 |
| roman | 's | −42, −54 | −48.0 | 12 | −38.3 | 9.7 |
| italic | Ye | +42, +50 | +46.0 | 8 | +37.3 | 8.7 |
| italic | io | +18, +28 | +23.0 | 10 | +14.3 | 8.7 |
| italic | y. | +29, +29 | +29.0 | 0 | +20.5 | 8.5 |
| roman | 't | −23, −37 | −30.0 | 14 | −22.9 | 7.1 |
| italic | Fi | −41, −37 | −39.0 | 4 | −37.7 | 1.3 |

### Against the candidates the brief named

- **Yo, Ye, Fi and 's rank 6th, 8th, 12th and 7th.** Once session 1 and the
  outlier answers are in training, B2 already gets them within 1–15 units.
- **ks is not a candidate.** He has answered it only once.
- **Excluded for disagreeing with himself.** Some pairs had a bigger miss but
  failed the consistency test: italic `qu` (miss 44, but a spread of only 2
  on a mean of −19, so it fails the size test), roman `iv` (−26 then −4), and
  roman `Qu` (+37, +11, +47). Those are his noise, not a model's failure.

### Why each is hard

This is [inf], read from the features and the rows.

- **italic Fo, −36.5.** A capital F's open right side over a round
  lowercase. Italic `Fo` shares nothing with any other training pair:
  - B2's glyph-identity term for italic F comes from `Fi` (−41/−37) and
    `Fr`/`Fa`/`Fe` (never answered);
  - the shape features see an F arm over a low o, much like `To`/`Po`, which
    he closes far less (`Po` −18.5).
- **roman Wa, +40.5** (his readings agree within 1 unit). He wants `Wa` much
  **looser** than the zero. The zero already carries a −90 kern (bench items
  `kr`). Every classic rule says a W's diagonal over an a should be kerned
  **tight**, and the models learned that from `Va`, `Av` and `To`. His
  answer says this font's `Wa` kern was simply too deep.
- **italic n', −23.5.** The apostrophe is a mark with very few rows, and its
  left bearing is set by far more common pairs (`'s`, `'t`). B2's identity
  term for `'` gets pulled by the `'`-on-the-left rows, not by `n'`.
- **roman ed, +30.5** and **roman it, +32.0.** Common lowercase pairs that he
  opened a lot. They have no special shape. The identity terms for `e`'s
  right side, `d`'s left side, `i`'s right side and `t`'s left side are
  averages over many other pairs he opened far less. A pair-specific
  judgment this big sits outside what an additive two-bearings-plus-shape
  model can express without a kern for that pair.

### What ships for them today [measured]

Round 395 already carries his answer within 1–9 units on all five. It
measures −34, +44, −23, +39 and +24 against his −36.5, +40.5, −23.5, +30.5
and +32. The pairs are either hand kerns (the `HOLD` list in `b2_fit.py`:
italic `Fo`, `n'`; roman `ed`) or in-sample fits.

So "hard" here means **a model that has not seen his answer cannot
reproduce it**. That is the case for every pair he has not judged yet, which
is the case that matters.

---

## 2. The stimuli (for any judge, including the cheaper Claude models)

Location: `$HARD5_DIR/stimuli/` (listed in full below). The truth is
**only** in `$HARD5_DIR/key.json`, which sits outside `stimuli/`.

- **Rendering.** The same way the reader renders, via `b2_proof.Setter`:
  - FreeType with default load flags;
  - 2-bit coverage;
  - linear advances;
  - GPOS kern at 1/16 px;
  - each glyph placed at the pen rounded to a whole pixel;
  - 54 px em, on the zero fonts (`bench/fonts-2026-09-20/`).

  The images are lossless PNG. Each `x3/` folder holds the same pixels
  enlarged 3× with nearest-neighbor.
- **Ladders.** One folder per pair (`pair1` … `pair5`). Each holds a word
  ladder and a phrase ladder of nine rungs each, one PNG per rung.
  - Each rung is the zero **plus k whole pixels** at the pair, for k = −4 … +4,
    which is k × 18.5 units.
  - Labels A–I are shuffled per pair **and** per ladder (seeded).
  - The carrier words are the bench's own: *For, Wayward, don't, named,
    with*.
  - The phrases:
    - *For a moment she said nothing*
    - *Wayward was the road home*
    - *I don't know where they went*
    - *the man named in the letter*
    - *she came with the others*
- **Why not the brief's −40 … +40 in steps of 10.** This was measured first
  (`hard5_stimuli.py --step-check`).
  - At 54 px, 10 units is 0.54 px. Because the pen rounds to a whole pixel,
    rungs repeat: a 9-rung ladder gave only **5 (ed), 7 (Fo), 8 (it) and 9
    (Wa, n') distinct images**.
  - Even where two rungs differ, the pair's gap moves only in whole pixels,
    and the later letters jitter.
  - A judge cannot choose between identical pictures, so the step is the
    reader's own pixel.
  - His answers land on rungs ±1 or ±2, never on the edge of a ladder.
- **2AFC** (`afc/trial01..30.png`). One image with two lines of the phrase,
  labeled 1 (top) and 2 (bottom). Three comparisons per pair, each shown in
  **both** orders, and the trial numbers are shuffled.
  - **his vs zero:** the correction he made.
  - **his vs B2 held out:** what a model without his answer would ship.
  - **his vs round 395:** round 395 already carries his answer. At whole
    pixels **4 of these 5 comparisons are pixel-identical** (Fo, Wa, n' and
    ed: 8 of the 30 trials, counting both orders). These are **catch
    trials**. An unbiased judge splits them 50/50, so any lean there is pure
    position bias.

### `stimuli/INSTRUCTIONS.md`, verbatim

```
# Letter-spacing judging task

You are judging the spacing between two letters in a book typeface, as it
would be read on a small e-reader at book size.

## What the images are

- Every image is a lossless PNG of black text on white, rendered at a 54 px
  em, the size a reader sees on the device. The files in each `x3/` folder
  are the SAME pixels enlarged 3x (nearest-neighbor) for easier viewing;
  judge whichever you prefer, but they are the same picture.
- The label at the left edge of each image (a letter, or 1/2) is only an
  identifier. Labels are assigned in a random order and carry no meaning.

## Task 1: ladders (folders `pair1` .. `pair5`)

Each folder holds two ladders, `word_A..I` and `phrase_A..I`. Within one
ladder, the nine images are identical EXCEPT for the space between one pair
of adjacent letters:

| folder | text | the pair that varies |
|---|---|---|
| pair1 | italic "For" / "For a moment she said nothing" | F o (in "For") |
| pair2 | roman "Wayward" / "Wayward was the road home" | W a (in "Wayward") |
| pair3 | italic "don't" / "I don't know where they went" | n ' (in "don't") |
| pair4 | roman "named" / "the man named in the letter" | e d (in "named") |
| pair5 | roman "with" / "she came with the others" | i t (in "with") |

Question, for each ladder separately:

> Which image has the most even, natural spacing for reading at book size?
> Answer with the letter.

Give exactly one letter per ladder (10 answers: pair1 word, pair1 phrase,
... pair5 phrase). If you wish, add a confidence from 1 (guess) to 5 (sure).

## Task 2: two-alternative choices (folder `afc`)

Each `trialNN.png` shows the same phrase twice, labelled 1 (top) and 2
(bottom). The two lines differ at most in the space between one pair of
letters (the same pairs as the table above). Some trials may show two lines
that look the same; answer anyway.

> Which line has the more even, natural spacing for reading at book size?
> Answer 1 or 2.

Answer every trial (30), one line each: `trialNN: 1` or `trialNN: 2`.

## Rules

- Judge only from the images. There is no right answer hidden in file names,
  sizes or order.
- Do not measure pixels with tools; judge by eye, as a reader would.
```

**Scoring a new judge.**

- **Ladders:** `key.json` → `pairs[n].ladder[word|phrase][LETTER].units`
  turns a pick into units. Compare it with `pairs[n].his`.
- **2AFC:** `key.json` → `afc[trial]` gives `top`, `bottom` and `identical`.

---

## 3. Every method, explained

Each section says what the method is, how it decides, what it costs, and
what it did on the five.

### a. Change nothing

- **What it is.** Predict 0: keep the font he judged.
- **How it decides.** It does not. This is the floor every method has to
  beat.
- **Cost.** Nothing.
- **Result.** 32.6. On these five that is simply the mean of |his|.

### b. Today's shipped fit (bench_fit ridge, the round-395 pipeline)

- **What it is.** One number per glyph side (a left and a right bearing),
  solved jointly from all his bench answers with a ridge penalty.
  - Lowercase bearings ship only when a side has at least 4 readings and at
    least 4 units.
  - Every capital pair becomes a kern of his raw number.
  - Marks are solved directly.
- **How it decides.** For a pair it has never seen, the prediction is
  right-bearing(first) + left-bearing(second). There is no shape at all.
- **Cost.** About 1 ms per refit, CPU, and a Python process of about 130 MB.
- **Result.** Refit on the bench **without** the pair: **26.6**.
  - A held-out capital pair gets no kern, so `Fo` reads +8 against his −36.5.
  - `n'` gets 0.
  - The continuous ridge without the floors does a little better, 21.6.

### c. B2: glyph identity + shape features, one ridge (the fit round 396 ships)

- **What it is.** b's two bearings per glyph, plus 38 **measured**
  shape features of the pair (`features.py`):
  - the bbox gap;
  - the 2-D closest approach;
  - per-band row gaps;
  - a depth-limited white area;
  - each facing side's depth profile at 8 heights;
  - each glyph's own inner white;
  - a blurred-ink "darkness" of the gap;
  - class flags.

  One ridge per style fits all of it.
- **How it decides.** Identity says what he wants of *this* glyph. The
  features carry that to pairs he never judged, through their shape.
- **Cost.** Under 0.1 s per refit (59 held-out refits and their features
  took 3.2 s in all) and about 2 s to measure every pair's features. CPU, under 200 MB.
- **Result.** Refit without any reading of the pair: **17.2**, the best
  single method.
  - It gets the **direction** right on all five.
  - It gets roughly **half the size** on every one. That is ridge shrinkage
    meeting pairs he pushed further than their neighbors.

### d. Classical optical spacing (no learning)

- **What it is.** The HT Letterspacer / Tracy premise: each class
  (lowercase, capital, mark) has **one target white**, and a pair is moved
  until its white reaches the target. It is built on the repo's two
  measures: the depth-limited white **area** (area_x) and the **2-D closest
  approach** (d2, `cmp_space_2d.py`'s measure 4).
  - The targets are the class medians of (measure + his answer) over the
    bench, with the pair left out.
  - "optical" averages the two measures; "area" and "2-D gap" use one each.
- **How it decides.** The prediction is target − current, for every pair
  of the class alike.
- **Cost.** Instant (under 1 ms).
- **Result:**

  | variant | mean \|error\| |
  |---|---|
  | optical (both measures) | 24.4 |
  | area only | 25.2 |
  | 2-D gap only | 30.3 |

  - It is the only method that moves **as far as he does**:
    - Wa: +67 against +40.5;
    - ed: +29.7 against +30.5, the best of any method on that pair.
  - But it overshoots the open pairs. `Fo` reads −64 and `n'` −64 against
    his −36.5 and −23.5, because the F's and the apostrophe's own open white
    counts as "gap".
  - That is `albo-spacing-method.md`'s standing finding: a letter's own open
    white belongs to the letter.

### e. Vision add-on: frozen pretrained image encoder + a small trained head

- **What it is.** A network pretrained on hundreds of millions of images
  turns a **picture of the pair** into a vector, with its weights frozen.
  A ridge "head" learns to map that vector (plus a style flag) to his
  answer.
  - **The picture.** The pair alone at the zero, FreeType, 110 px em,
    centered in 224 × 224. The five inputs are saved in
    `$HARD5_DIR/vision_inputs/`.
  - **Training.** On every other pair he answered: 489 pairs, both styles,
    using each pair's mean of readings, the same data B2 sees. Both styles'
    copies of the held-out pair are removed.
  - **The penalty.** Chosen by 5-fold CV **inside** the training rows.
- **The two encoders:**
  - **DINOv2-small** (Meta, self-supervised, 22 M parameters).
    - Download about 88 MB [inf, from the listing].
    - Load 2.8 s, 13.6 ms per image on the CPU.
    - RSS 990 MB.
  - **SigLIP-base-patch16-224** (Google, image–text, 93 M-parameter vision
    tower).
    - The whole Hugging Face cache for both models is 859 MB [measured].
    - Load 6.4 s, 33 ms per image.
    - Peak RSS 1.83 GB.
  - The PyTorch, torchvision and transformers install grew the venv from
    398 MB to 1.1 GB [measured].
  - Head fit: 0.18 s.
- **How it decides.** Pairs that *look* alike to the encoder get similar
  answers. Nothing in it knows what spacing is.
- **Result on the five:**
  - DINOv2: **31.4**, no better than doing nothing;
  - SigLIP: **25.4**.
- **Result on every answered pair** (10-fold, 489 pairs, [measured]):

  | method | mean \|error\| |
  |---|---|
  | SigLIP head | 11.64 |
  | DINOv2 head | 12.05 |
  | **B2 on the same folds** | **9.59** |
  | doing nothing | 13.38 |

  The add-on learns something, about 1.7 units better than nothing. It is
  still 2 units **worse than B2** on everything. On the five hard pairs it
  shrinks to near zero, the most of any learned method.
- **Why [inf].** A 224 px image at a 16 px patch cannot resolve a 1–2 px
  change in one gap, and 489 examples is too few to teach the head which
  of 768 dimensions carry it. It is the same wall the from-scratch CNN hit
  (options doc §2b, 13.28), softened by pretraining.

### f. Local VLM as a judge (Qwen3-VL-8B-Instruct, 4-bit MLX, LM Studio)

- **What it is.** A general vision-language model shown the stimuli from §2,
  with the INSTRUCTIONS question, and asked for a letter.
  - Ladders: all nine rung images in one message, in letter order A…I and
    again reversed; native and x3; word and phrase. That is 40 calls.
  - 2AFC: all 30 trials, native and x3. That is 60 calls.
  - Temperature 0.
  - Loaded, run, unloaded, and the server stopped.
- **How it decides.** Whatever its training taught it about "evenly spaced
  text". Nothing in that training targets this.
- **Cost:**
  - LM Studio RSS 7.0–7.3 GB while loaded;
  - ladder call (9 images) median 10.7 s;
  - 2AFC call median 3.4 s;
  - the full pass took 14.5 minutes.
  - **21 of 120 calls gave no answer** on the first pass. It wrote prose and
    ran out of its 40-token budget. They were re-asked with "Reply with only
    the letter" (or "1 or 2") added. Those rows are marked `retry` in the
    log.
- **Position and label bias** (the whole story, [measured]):

  | check | result |
  |---|---|
  | ladder picks by letter | **A 36 of 40**, F 2, G 2 |
  | the ladder's first-shown image | chosen 40% of the time: A is first in one order and last in the other, so it chose the **label A**, not a position |
  | ladder order-reversal agreement | 16/20, and **only because** it said A both times |
  | 2AFC answers | **"2" 59 of 60** |
  | 2AFC catch trials (8 identical trials × native/x3) | chose "his" 8/16 (it answered "2", so this is the shuffle, not sight) |
  | 2AFC his vs zero | chose his 9/20 |
  | 2AFC his vs B2 held out | chose his 10/20 |

- **Result.** 27.0 on the ladders. That is where the shuffle happened to
  put each "A":
  - `Wa`'s A was +74 on the word ladder, so the model "found" +46;
  - `it`'s A was −37, so it reads −37 against his +32.

  **Verdict:** the same as the options doc §2c. It is a label-bias machine,
  not a judge. The larger local model (Qwen3.8-27B, 116 s per judgment,
  2 of 7 self-consistent in §2c) was **not** re-run here. It has already
  shown the same failure, and the P0 rule forbids a run that teaches
  nothing new.

### g1. Mixed: B2 proposes, the VLM disposes

- **What it is.** B2 (held out) picks the **three rungs nearest its
  prediction**. The VLM sees only those three images, under their own random
  letters, in both orders, for word and phrase. That is 20 calls.
- **How it decides.** The mechanical model narrows the choice to plausible
  answers; the VLM supplies the "eye".
- **Cost:** B2 plus 2.1 s per call (three images) on the 8B model, which is
  about 10 s for a pair.
- **Result:** **16.9**. Snapping B2 to its own nearest rung, with no VLM,
  scores **17.8**, so the VLM adds 0.9 units, and that is noise:
  - it **never picked the first-shown image** (0 of 20);
  - it kept its answer when the order was reversed **1 time in 10**.

  Among three plausible rungs, a random pick averages to roughly the middle
  one. The mechanical pre-filter does all the work.

### g2. Mixed: B2 + vision add-on, averaged

- **What it is.** The mean of c and e (SigLIP, the better head on the
  all-pairs CV).
- **How it decides.** The two predictions are averaged.
- **Cost:** the sum of c and e, about 25 s and 1.8 GB the first time. After
  that the embeddings are cached.
- **Result:** **21.3**, worse than B2 alone (17.2). Both shrink toward zero,
  so averaging them shrinks further.
- **Not measured:** the ensemble across all pairs. A 50/50 mix of a 9.6 and
  an 11.6 model is unlikely to beat the 9.6 [inf].

---

## 4. Cheaper Claude models (Haiku 4.5, Sonnet 5) -- judged 2026-09-26

Run by the orchestrator as two blind Claude Code subagents (model overrides `haiku`, `sonnet`), each told to use only `stimuli/` and INSTRUCTIONS.md, never the key; answers in `scratchpad/hard5/judge-{haiku,sonnet}.json`, scored in `results_claude.json`. Ladder estimate = mean of the word and phrase picks, in units.

| judge | ladder MAE | vs change nothing (32.6) | label bias | stated confidence | 2AFC vs zero chose his | identical catch trials chose his | vs B2-held chose his |
|---|---|---|---|---|---|---|---|
| Haiku 4.5 | **62.2** | worse | picked "E" on 6 of 10 ladders | 4/5 on all 10 | 4/10 | 5/8 | 5/10 |
| Sonnet 5 | **35.1** | no better | picked "A" on 6 of 10 ladders | 2/5 on all 10 | 6/10 | 3/8 | 2/10 |

- **Haiku did not look at every rung**: it viewed 74 images of the 120 (all 18 of pair1, 5-8 of each other pair), so most of its ladder picks were made without seeing the options. Confidently wrong (conf 4 throughout) -- e.g. `it` +32 answered -74.
- **Sonnet looked at all 120** and reported low confidence (2) throughout, which was honest: it lands at change-nothing. It got the direction right on Fo and Wa (-46, +46 vs his -36, +40) and wrong on n', ed, it.
- **Both lean to the top line** in 2AFC (Haiku 19/30 "1", Sonnet 20/30 "1") and are at chance against the unchanged font and on identical catch trials.
- **Verdict**: like the local VLMs (section 3), general vision models cannot judge spacing at this grain -- a one-pixel difference at 54 px. They are usable as ORCHESTRATORS of the loop, not as judges. B2 (17.2) remains the best method on the hard five.

## 5. What follows [inf]

- **The five hard pairs are not a model problem that more model fixes.**
  Each is a pair he pushed well past what its glyphs' averages predict.
  Only an answer to **that pair** fixes it, and all five already ship with
  his answer (§1). The practical lesson is for pairs he has **not** judged:
  the active bench (options doc §11) is the tool, because the model will
  under-call exactly this kind of pair.
- **One thing a model could add** is to learn *when* it is likely to
  under-call, and send those pairs to him. B2 held out misses big where
  |his| is big and the pair is a capital or a mark, or a common lowercase
  pair far from its glyphs' averages. That is a selection signal for the
  active bench, not a new judge.
- **Not worth building:**
  - the local VLM, in any role (f, g1);
  - the vision add-on as a scorer (e): worse than B2 overall and the worst
    at shrinkage;
  - the optical rule as an engine (d).

  The optical rule is the only method that moves as far as he does, which
  is worth knowing, but it overshoots every open-sided pair.

## 6. Checked and found clean or negative

- **Stimuli contain the pair and differ only at it.** Checked by eye:
  `pair3/x3/phrase_A.png` and `afc/x3/trial01.png`. Every ladder's nine rungs
  are pixel-distinct (asserted in the script).
- **The vision inputs show the pair, centered:** `vision_inputs/italic_Fo.png`,
  checked by eye.
- **No held-out leak:**
  - B2 and b are refit without every reading of the pair;
  - the vision head drops both styles' copies of it;
  - the optical targets exclude it.
- **Model shutdown.** LM Studio was unloaded and the server stopped after
  each pass. `lms ps` confirmed nothing loaded.

## 7. Not verified

- The 27B VLM was not run on these stimuli (§3f).
- The download sizes for the individual encoders are from their listings.
  Only the combined cache (859 MB) was measured.
- The 21 retried VLM calls used a one-sentence-longer prompt. The label bias
  is the same with or without the retry: 22 of the 25 first-pass ladder
  answers were A, and 14 of the 15 retries were A.
