# The italic x as options (2026-10-01)

Owner, 2026-10-01: *"give me options for italic x"*.

**Status: OPTIONS, awaiting a pick.** Nothing shipped. Three arms sit behind
`ALBO_ALD_X_ARM` (`outlines/glyphs/aldine.py`, the `ROUND 458` block above
`a_x`). Unset draws today's letter: the default Italic and Bold Italic rebuilt
from this tree match build 282 exactly (`cmp_outlines.py`: 0 of 530 glyphs
differ, both cuts).

- **Surveyed:** commit `0d89e2f`, the shipping fonts of build 282.
- **Instruments:** `tools/wedge_serif/instruments/x_italic.py` (the reference
  sheet, the pen signature, the hairline widths) and `instruments/x_arms.py`
  (the proof pictures).
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
x sits at 0.83–1.38 of its own o. The four ends are therefore as heavy as the
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

- **Spacing moves with the shape.** The B2 model re-spaces the new drawing on
  its own: X3 comes out 33 units narrower in the Italic, because its open top
  left lets the letter close up. The proofs show the arms spaced as they
  would ship.
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
