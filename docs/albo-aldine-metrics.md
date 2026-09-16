# The Aldine ledger — what each letter is measured against

Owner, 2026-09-15: *"keep track of metrics that work for different letters
including line width."*

**The ledger is a SCRIPT, not this table.** `tools/wedge_serif/cmp_aldine_metrics.py`
builds the Aldine italic and checks every letter against its measured target,
exiting non-zero when one drifts more than 10%. Run it after any change to a
shared dial:

```bash
cd tools/wedge_serif && python3 cmp_aldine_metrics.py
```

It exists because the numbers move the moment a shared dial does, and prose
does not notice. **Contrast arm D moved the `o` from 0.624 to 0.823 against a
target of 0.617 and nothing said so for a round** — that is the failure this
replaces.

## What is tracked, and why those metrics

| metric | why this one |
|---|---|
| **counter / ink** | the letter's colour and its counter in one number, and it is measured the same way on a scan and on a rendered glyph — flood-fill the enclosed white, count the ink. Robust to resolution, which raw stroke widths are not. |
| **width / height** | the proportion, taken from the OUTLINE via `ControlBoundsPen`. **Never from `Image.getbbox()`** — these rasters are ink-0 on paper-255, so it returns the canvas and every figure derived from it is wrong (round 119). |
| **line width** | the letter's thick, × the family stem `S`. This is the one that varies most per letter and is easiest to lose. |
| **contrast arm** | which of the family's approved contrasts this letter is set to. **Per letter, not global.** |

## The letters

| ch | arm | line width | counter/ink | w/h | source |
|---|---|---|---|---|---|
| `a` | **C** 5.00 | 1.65 | 0.344 | *retired* | owner's target crop, 2026-09-15 |
| `e` | **C** 5.00 | 1.12 | 0.203 | — | `griffo-macro.png`, *naues*, 54 px xh |
| `i` | D 9.26 | 0.64 | — | — | `griffo-macro.png`, *rodigium* |
| `o` | **D** 9.26 | 1.63 | 0.617 | 0.759 | `griffo-macro.png`, *udos*, 54 px xh |
| `u` | D 9.26 | 0.64 | — | — | pitch 0.52 × xh, three stem pairs |
| `y` | D 9.26 | 0.64 | — | — | **DERIVED** — no `y` in any scan we hold |

Shared across every letter: **lean 13°** (`FJORD_SLANT=13`, the family's own,
confirmed at 13.7° on the owner's crop) and a **50° nib** (measured
independently on the `o` and on the `a`; the `e` was put on the same nib in
round 122).

## Two rules this ledger encodes

**Contrast is per letter.** Owner, after a global switch to C knocked the `o`
off the arm he had already set: *"o was set to D contrast. you are confusing
things."* `ALD_CON` is the module default and `CON_A` / `CON_E` / `CON_O`
override it. "Use C" said about the `a` is not a ruling on the `o`.

**A retired target is not a failed one.** The `a`'s w/h of 0.891 was measured
on a crop with a full-length exit; the owner then halved the tail, which
legitimately narrows the letter to ~0.69. That target is marked retired with
its reason rather than left to print a permanent false failure — which is how
a ledger stops being read.


## Autofit — measuring and solving a letter without hand-tuning

`tools/wedge_serif/aldine_autofit.py`. Owner 2026-09-15: *"be automated for the
remaining letters based on the scans and recent reference italics."*

```bash
cd tools/wedge_serif
python3 aldine_autofit.py --letters aeiou --dry   # just report the targets
python3 aldine_autofit.py --letters a             # measure, then solve its dials
```

Rounds 116–128 fitted five letters by hand and every one went the same way:
measure the source, sweep a dial, re-measure, find a second dial had moved,
sweep again. That loop is mechanical. Autofit runs it by coordinate descent —
one dial at a time, repeatedly, **because the dials interact**, which is the
single thing every hand-fitted letter proved.

**Where a target comes from, in order.** A hand-located SCAN CROP if one is
listed (automatic letter-finding was tried and failed repeatedly — template
correlation matches every round bowl beside a stem — and a wrong crop silently
poisons every number under it). Otherwise a REFERENCE ITALIC, and the letter is
reported `[DERIVED]` so it cannot be mistaken for measured.

**Validated against the one letter whose answer was already known.** Hand-fitted
the `a` at flank 1.36, stem 2.81, bowl 1.20 over eight rounds; autofit reached
**1.50 / 2.75 / 1.20 in two passes**, from the scan alone.

### Two limits found while building it, both worth knowing

- **The flank/stem pair is meaningless on a loop letter.** On `e o c s` the left
  and right runs are two sides of the same curve, not two strokes, and fitting
  to them drags the letter toward a shape it is not: the `e` solved at an error
  of **0.277** against a "stem" that does not exist. `HAS_STEM` gates the
  metric; the `e` then solves at **0.019**.
- **Counter/ink is sensitive to the crop box.** Autofit reads the `o` at 0.591
  where this ledger's hand crop gave 0.617 — the same letter, a few pixels of
  margin apart. Targets from the two routes are therefore NOT interchangeable,
  and the ledger keeps its own hand-measured numbers rather than adopting
  autofit's.


### Locating letters: `--segment`

```bash
python3 aldine_autofit.py --segment macro:330:420
```

Proposes letter boxes on one text line from the column ink profile, in reading
order, for a human to label. It deliberately does NOT identify letters —
naming them is the half a machine cannot do safely here, and rounds 115–116
proved it by getting the `a` wrong three times with template matching.

**Trustworthy because it reproduces a known answer:** box [8] on the
*naues* line comes back as (594,345,632,403), against the (592,342,634,406)
that round 117c found the slow way.

Touching letters return as one wide box — `na` at 114 px against the `e`'s 38 —
and that is visible in the width rather than hidden, which is the signal to
split by hand. `u` and `s` were added from this line and now carry SCAN targets
instead of Pagella fallbacks.

**One reading to distrust:** the `s` reports counter/ink 0.930, which is far too
high for an `s`. Either the crop admits white that is not a counter or the fill
leaks through a thin place. Recorded rather than used; do not fit the `s` to it
without re-cropping.


### `--label`: naming every letter on a line, and why it is still eyeballed

```bash
python3 aldine_autofit.py --label
```

The segmenter returns boxes in reading order and **the lines' text is known**,
so naming them needs no shape recognition at all — which is the thing rounds
115–116 lacked. Template matching was trying to answer "which letter is this?"
when the answer was already written down.

Italic letters TOUCH, so box count never equals letter count. The boxes are
aligned to the letters by **dynamic programming**: each box takes a contiguous
RUN of letters, and the split minimising the disagreement between each box's
width and its letters' expected widths wins. Boxes holding more than one letter
are dropped rather than split.

**It proposed 18 letters and FOUR were wrong** — it called an `a` a `c`, a `t`
an `n`, a blob a `t`, and a `u` an `i`. So every crop is rendered as a contact
sheet and looked at before it enters `SOURCES`. **An automatic labeller that is
78% right silently poisons every number underneath it**, and nothing downstream
would report it: a wrong crop still measures, still solves, still passes the
ledger.

Adopted from that pass, verified by eye: `b d h l m p q r s` — taking the
lowercase from 4 scan-measured letters to 14, plus a capital `B` for when the
capitals start.

### Per-letter weight

Every glyph in `aldine.py` is wrapped to record which letter is being drawn, and
the shared width paths multiply by `ALBO_ALD_LW_<ch>`. One hook rather than
twenty-six dials, and it is what lets the fitter reach a letter nobody has
hand-tuned — `dials_for()` falls back to it.
