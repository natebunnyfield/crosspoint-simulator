# The italic x as options (2026-10-01)

Owner, 2026-10-01: *"give me options for italic x"*.

**Status: SHIPPED, round 461** (`docs/albo-round-461-2026-10-02.md`). The
pick: X1 with the C bottom left at 1.125 weight (owner 2026-10-02, *"X1 but
with more options on bottom left"*, then *"halfway between c1 & c2"*). These
are the defaults `ALBO_ALD_X_ARM` "X1C" and `ALBO_ALD_X_BL_W` 1.125, and
`ALBO_ALD_X_ARM=""` (set, but empty) draws the round-457 letter. The option
history follows, sections 4-9.

- **Surveyed:** commit `0d89e2f`, the shipping fonts of build 282.
- **Instruments:** `tools/wedge_serif/instruments/x_italic.py` (the reference
  sheet, the pen signature, the hairline widths, and since round 461 `--ink`:
  the x / n ink and the bottom-left terminal width) and
  `instruments/x_arms.py` (the proof pictures).
- **Certainty:** every number below was measured by those scripts on built
  outlines. Nothing is estimated.

## 1. What is wrong with today's x, measured

Twelve reference italics at one x-height, unsheared by their measured slant
(`refs_registry` for the five registered faces). The system faces are
Palatino, Hoefler Text, Iowan, Baskerville, Georgia, Charter and Times, read
at their declared angle.

**It carries as much ink as its own n.** The x's ink over the n's ink:

| | Albo I | refs (12) | Albo Z | bold italic refs (9) |
|---|---|---|---|---|
| x / n ink | **0.99** | 0.74–0.98, median **0.81** | 0.83 | 0.76–0.83, median 0.79 |

**The thick diagonal is what is heavy.** These are perpendicular widths from a
distance transform at each run's center, as fractions of the face's own o
(`x_italic.py --hair`):

| | Albo I | refs, range | median |
|---|---|---|---|
| x thick / o thick | **0.93** | 0.70–0.85 | 0.78 |
| x thin / o thinnest | 1.54 | 0.90–1.31 | 0.98 |
| x thin / v hairline | 0.99 | 0.82–1.04 (7 faces) | 0.89 |

The thin row needs care. Albo's x hairline is the v's to within 1%
(31.4 / 31.6 units). It is heavy against the o only because Albo's rising
hairlines (v, w, x) all are. So it is a family trait, not an x fault, and no
arm makes the x lighter than the v by more than the references do. The v row
counts seven faces: in Flanker, Pagella, Palatino and Georgia the instrument's
band (.35–.65) caught the v's other stroke, so those four are left out.

**It is drawn on two width tables, not on a pen.** Run through
`cmp_g_strokes`' pen signature (width binned by run direction,
`x_italic.py --pen`), Albo's x shows 2.03:1 contrast against its own o's
3.16:1. That is 0.64 of the o, and 0.60 in the Bold Italic. Every reference
x sits at 0.83–1.38 of its own o.

**Correction (adversarial review, 2026-10-02):** the shipped x is drawn with
`nib()` widths, but this ratio did not move. It reads 1.89 / 3.16 = **0.60**
in the Italic and 1.97 / 3.27 = **0.60** in the Bold Italic. So in this
letter the ratio does not tell a pen from width tables, and nothing here
should be read as the redraw having "fixed" it. The measured faults the arms
do address are the ink and the thick (sections 5 and 9). The four ends are therefore as heavy as the
strokes they finish:

- the foot's centerline reaches (378, .135) and then curls back to
  (368, .185), so the hook folds over itself into a boot;
- the bottom-left turn carries a notch on its inner edge;
- the thin's top runs at 49 degrees, exactly along the nib's 50, just before
  its finial, so it necks before the swell.

## 2. Checked and found CLEAN (do not re-propose)

- **Width.** x / o ink width is 1.23 against the references' median 1.21. The
  x reads wide beside the n (0.96 against a median 0.86) only because Albo's
  italic n is narrow. Poetica (0.99) and Cancelleresca (0.98) sit there too.
- **Height.** The x's top right is 457 units, the v's is 456. That is the
  family finial (round 276), shared by v, w, x and y, not an x fault.
- **The hairline's weight.** It is the v's, as above.
- **No scan holds an x.** `docs/albo-aldine-targets.md` lists none, and the
  Soncino Petrarca photograph in ~/Downloads, checked here, is Italian with
  no x in it.

## 3. History that constrains the options

- **Round 108 (2026-09-14).** "Hooks at every end of the x" were part of a set
  the owner called much worse. The x was redrawn as two strokes "with one
  light turn each" (`italic.py` `g_x_it` still carries that drawing).
- **The Aldine module (2026-09-15/16)** redrew it from Poetica and Flanker
  with four ends again.
- **2026-09-16.** The owner then straightened the bottom-left turn only
  slightly: **X_BL 0.10, the least of four rungs he was shown**. So he liked
  that turn.
- **Round 276 (2026-09-19).** No balls in this italic. The top-right end is
  the family finial, and every arm keeps it.

## 4. The arms

Every arm is drawn on ONE PEN: `nib()`, the module's 50-degree edge, so a run's
width follows its direction (`albo-method.md` section 1). The pen is 57 / 20
reference units at the 400 and 66 / 22 at the Bold Italic, linear on the stem
between (`X_PEN_THICK`, `X_PEN_THIN`). Those values put the 400's thick at 0.80
of the o's thick and its thin at 0.92 of the v's. At the old pen the Bold
Italic fell to 0.71 of its n's ink. The thin's finial grows out of the hairline
on the v's own terminal table (`grow`). Beyond the pen, each arm changes at
most one end:

| arm | top left | bottom left | foot, top right |
|---|---|---|---|
| **X1** | today's entry, its crest rounded into one arch | today's turn (X_BL 0.10) | foot ends rising, no back-curl; family finial |
| **X2** | as X1 | **a flat foot** on the baseline running out to a point (Pagella, Palatino, Cancelleresca) | as X1 |
| **X3** | **no entry**: the thick starts on its own line at a square pen cut (round 108's x) | as X1 | as X1 |

X2 revisits the 2026-09-16 bottom-left ruling. X3 keeps it.

## 5. What each arm measures (built fonts)

| arm | cut | x / n ink | thin | thin / v | thick | thick / o | advance | lsb |
|---|---|---|---|---|---|---|---|---|
| today | I | 0.992 | 31.4 | 0.99 | 67.2 | 0.93 | 544 | 34 |
| X1 | I | 0.851 | 28.9 | 0.92 | 58.0 | 0.80 | 533 | 31 |
| X2 | I | 0.832 | 29.3 | 0.93 | 57.9 | 0.80 | 533 | 12 |
| X3 | I | 0.809 | 29.4 | 0.93 | 58.4 | 0.81 | 511 | 9 |
| today | Z | 0.825 | 41.9 | 1.01 | 85.9 | 0.84 | 558 | 30 |
| X1 | Z | 0.792 | 42.9 | 1.03 | 89.3 | 0.87 | 542 | 21 |
| X2 | Z | 0.772 | 40.9 | 0.98 | 89.3 | 0.87 | 542 | 14 |
| X3 | Z | 0.743 | 42.1 | 1.01 | 89.7 | 0.88 | 530 | 9 |

Notes on the table:

- **Spacing (CORRECTED 2026-10-02).** This said the B2 model re-spaces a
  new drawing on its own. It does not. The fit places the x by its UNSHEARED
  x-band, where the head stays the leftmost ink, so a terminal that reaches
  further left only once sheared changes every neighbor's white untouched.
  The shipped cup cost 20 units on every pair with x on the right; round 461
  restores it (`docs/albo-round-461-2026-10-02.md`). The option proofs in
  sections 5, 8 and 9 were spaced WITHOUT that restoration.
- **The Bold Italic's thick is a little heavier than today's** (0.87 of the o
  against 0.84) while its ink falls. The ends lose more than the thick gains.

## 6. Gates (each arm against today)

| | contour hairs (letters / all) | touch | touch, composites | kern classes |
|---|---|---|---|---|
| today | none / none | 0 / 0 below | 0 | ok |
| X1 | none / none, both cuts | **0 / 0**, both cuts | 0 | ok |
| X2 | none / none | **R x touches in the Z** (-0.0019 em); I under the 0.012 floor (0.0093) | 0 | ok |
| X3 | none / none | Z: R x under the floor (0.0039); I clean | 0 | ok |

If X2 or X3 is picked, the clearance loop (`local_ai/clearance.py`) adds the
one R x pair, as for any round.

**Two glyphs move per arm: x and χ.** The italic chi takes its italic/roman
proportion from the x (`greek_italic.py`, `VIA_ROMAN`), so its ink moves by
0.3–1.5%. Nothing else changes (`cmp_outlines.py`, both cuts, every arm).

## 7. Reproduce

    cd tools/wedge_serif; source build_env.sh
    env "${ALBO_ITA_ENV[@]}" ALBO_ALD_X_ARM=X1 PYTHON_GIL=0 python3 -m outlines.build OUT --style Italic
    env "${ALBO_BIT_ENV[@]}" ALBO_ALD_X_ARM=X1 PYTHON_GIL=0 python3 -m outlines.build OUT --style BoldItalic
    $VENV/bin/python instruments/x_italic.py --fonts OUT --sheet refs.png --measure --pen --hair
    $VENV/bin/python instruments/x_arms.py proof PROOF today=T X1=A1 X2=A2 X3=A3

The proof line is built from the owner's 41 books (667,633 words). The
commonest x-words are next 338, exactly 314, six 266, context 246, box 210,
expected 174, fox 162, fixed 154 and text 146. The commonest x pairs are
ex 4,760, xt 1,194, xp 1,144, ix 1,016 and xi 968.

Proof page: https://claude.ai/artifact/SGF54ZGgzxYW4JJYxTw7DT

## 8. Round 459: X1's bottom left as options (2026-10-02)

Owner: *"X1 but with more options on bottom left"*. So X1's head, foot,
finial and pen are ruled. Each option below swaps only the thin's start,
`ALBO_ALD_X_ARM=X1A`...`X1F`, and X1A is X1:

| option | the bottom left | x / n ink (I / Z) | lsb (I / Z) | touch |
|---|---|---|---|---|
| X1A | X1's turn: the comma (X_BL 0.10, the pen swells it as it swings left) | 0.851 / 0.792 | 31 / 21 | clean |
| X1B | the family finial, as the hairline's top right has (round 276) | 0.809 / 0.752 | 56 / 61 | clean |
| X1C | an upturn: the hairline cups up to the left, mirroring the thick's foot | 0.856 / 0.798 | 15 / 11 | **R x touches in Z** (-0.0019 em); I under the floor (0.0065) |
| X1D | a short wedge foot, heavier and shorter than X2's | 0.819 / 0.765 | 24 / 22 | R x under the floor, both (0.0079 / 0.0053) |
| X1E | bare: the hairline runs out at the baseline on a pen cut | 0.791 / 0.734 | 65 / 67 | clean |
| X1F | X1A's turn kept at hairline weight: a thin curl, not a comma | 0.833 / 0.771 | 38 / 36 | clean |

Notes on the table:

- **Every option keeps X1's advance** (533 Italic, 542 Bold Italic). The
  spacing model places the glyph by bands the bottom left does not reach, so
  only the left bearing moves and the options compare like for like.
- **The other gates pass on all six.** No contour hairs (letters or full
  sweep), composites touch 0, kern classes ok. Only x and χ move against
  today.

Two drawings were tried and fixed or dropped on the way, recorded so they are
not retried:

- **A closed teardrop** (the curl carried round to point back up into the
  hook) folded onto its own stroke and left a white sliver between the tip
  and the inner edge, in both cuts. It was replaced by X1F.
- **The first finial (X1B)** started at y 0.012. With the face sheared 28
  degrees toward vertical, its corner hung to -31 in the Italic and -44 in the
  Bold Italic, an arrowhead under the baseline. It now starts at 0.065 and
  bottoms at -15 / -28 with the rest of the letter.

The proof adds `pairs_<cut>.png`: "ex ix ox" at 100 pt, which is where the
bottom left meets the letter before it (ex is the commonest x pair in his
books, 4,760).

Proof page: https://claude.ai/artifact/7Aq2A2qVwLCGbrgXV11RCB

## 9. Round 460: X1C and X1F with heavier bottom-left ends (2026-10-02)

Owner: *"make C and F options with thicker bottom left serifs"*. One dial,
`ALBO_ALD_X_BL_W` (default 1.0 = X1C / X1F exactly as shown in round 459),
scales the terminal's weight on those two options only. The terminal width
below is the largest perpendicular width (twice the distance transform)
within the left 30% of the ink and below .25 xh, unsheared, in units at
xh 429.

| option | dial | terminal width (I / Z) | x / n ink (I / Z) | advance (I / Z) | touch (R x) |
|---|---|---|---|---|---|
| X1A (reference) | -- | 47.6 / 71.1 | 0.851 / 0.792 | 533 / 542 | clean |
| C1 = X1C | X1C 1.0 | 42.9 / 62.4 | 0.856 / 0.798 | 533 / 542 | Z touches (-0.0019 em); I under the floor |
| C2 | X1C 1.25 | 49.4 / 70.0 | 0.878 / 0.813 | 534 / 546 | Z touches (-0.0019); I under the floor (0.0065) |
| C3 | X1C 1.5 | 58.0 / 78.7 | 0.899 / 0.833 | 544 / 559 | Z under the floor (0.0039); I clean |
| F1 = X1F | X1F 1.0 | 34.6 / 46.3 | 0.833 / 0.771 | 533 / 542 | clean |
| F2 | X1F 1.25 | 43.0 / 57.2 | 0.845 / 0.783 | 533 / 542 | clean |
| F3 | X1F 1.5 | 56.8 / 83.7 | 0.863 / 0.804 | 533 / 542 | Z under the floor (0.0053); I clean |

No contour hairs, composites 0, kern classes ok, on all six. Only x and χ
move against today.

How the weight is carried, and what each step cost to get right:

- **C (the upturn).** Widths over the first third of the stroke are boosted
  (`boost0`), easing off along the rising diagonal rather than in the cup.
  Easing off inside the cup put a hump in the counter's floor, and the
  Bold Italic showed it. The tip tapers less as the weight grows.
- **Two things kept the heavier C level and open.** Grown about its
  centerline, the cup sank: its underside reached -26 (I) and -45 (Z),
  where the rest of the letter bottoms at -15 / -28. So the cup is lifted
  by half what it gains. The Bold Italic's pen already swells this cup, so
  there it takes 60% of the extra weight and twice the opening; at x1.5 its
  counter otherwise folded into a V-notch at the tip. The Bold Italic C3
  still carries a gentle wave in that floor (no gate reads it).
- **F (the thin turn)** was X1A's turn capped at 30 units. Raising the cap
  converges on X1A: at x1.5 the cap no longer binds and F3 measured
  identical to X1A (47.6 units, same ink and bearing to three decimals).
  So F3 instead carries X1A's own turn a fifth heavier (`boost0` 1.2), and
  X1A sits between F2 and F3.
- **C2 and C3 are re-spaced by the model.** Their cups reach further left,
  and the advance grows 1 / 4 units (C2) and 11 / 17 (C3). The F steps keep
  X1's advance.

Proof page: https://claude.ai/artifact/9EjkV7RqugD7omVYAiRpp3

## 10. The Bold Italic's head notch, as an option (2026-10-02)

Round 461's adversarial review, finding 2 (cosmetic). Where the entry arch
turns into the thick diagonal, the Bold Italic's inner outline overshoots
and doubles back. That leaves a nick of white beside a barb of ink: point #9
at (174, 380), a −122.5 degree reversal on 6- and 8-unit arms. It sits under
the hair gate's 150 degrees and the bump tool's 70-square-unit floor. The
Italic's corner there is a clean round turn.

**Option N1:** `ALBO_ALD_X_CLOSE=8`, 8 units of mitre closing on the x at
stems above 84 (the Bold Italic only), as `greek_italic._close3` does for ε
and ξ. Measured on the live outline against `ALBO_ALD_X_CLOSE=0`:
- +20.0 square units filled at the junction;
- 1.5 and 1.2 square units off two convex corners;
- nothing else.

At 3 and 5 units the barb survived. Built, only the x moves (`cmp_outlines`),
hairs none, touch 0 / 0. **Default 0, awaiting his call** (defects are his).
