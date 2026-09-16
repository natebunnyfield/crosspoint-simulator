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
