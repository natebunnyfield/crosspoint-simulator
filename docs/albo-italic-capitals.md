# What a real italic does to its capitals

**Owner ask, 2026-09-15:** *"subagent to make historically accurate (use other
italic fonts for reference) albo italic capitals. do not touch regular roman."*

This is the research half. **The implementation is NOT done** -- the agent that
produced these measurements stopped when its session ended, after writing
`tools/wedge_serif/cmp_italic_caps.py` and its output but before drawing
anything. Nothing in `outlines/` was changed. Re-run:

```
cd tools/wedge_serif && python3 cmp_italic_caps.py <albo-regular.ttf> <albo-italic.ttf>
```

## Method

**17 roman/italic PAIRS**, each italic compared only with the roman it was cut
for, because that is the only comparison that means anything. Four measures:

- **width** -- advance over the face's OWN H-ink cap height, italic against
  roman. Not the em: cap-to-em runs 0.60 to 0.75 across these faces.
- **cap height** -- italic over roman, in em units.
- **slant** -- the capital's stem slope measured against the lowercase l's in
  the same font.
- **shape** -- round 104's oblique test applied to capitals: shear the roman by
  the italic's own angle and take intersection-over-union against the italic.
  **1.00 is a pure oblique; low means the letter was redrawn.** For calibration,
  round 104 measured real italic LOWERCASE at 0.31 to 0.43.

## Three negative results, and they are the useful ones

**Italic capitals are NOT uprighter than the lowercase beside them.** This is
the thing "chancery capitals" folklore predicts and the measurement refutes:
median lowercase slant **12.97 deg**, median capital slant **12.94 deg**.
A difference of +0.03 degrees is nothing. Do not build an upright-capital
italic on the strength of the idea.

**Italic capitals are NOT shorter than roman ones.** Median cap height ratio
**1.000**, and 13 of the 17 sit at exactly 1.000.

**The serifs are NOT reduced.** Median italic-over-roman serif spread
**1.005**. That is worth stating because the LOWERCASE does reduce its
serifs -- Albo's own `IT_SERIF` is 0.50, measured off Coelacanth in round 101 --
so the obvious generalisation to the capitals is wrong.

## What does change

**Width: about 5 per cent narrower.** Median ratio **0.953**.

**Shape: they are redrawn, but far less than the lowercase.** Median IoU
**0.690**, against the lowercase's 0.31 to 0.43. So the honest reading is
that an italic's capitals are mostly a narrowed roman with a handful of letters
genuinely re-cut -- which is a much smaller job than the lowercase was, and a
different one.

**The ranking is the deliverable.** Sorted by how redrawn each letter is:

| | width (it/rom) | shape (IoU) | verdict |
|---|---|---|---|
| N | 0.943 | 0.439 | REDRAW |
| H | 0.925 | 0.475 | REDRAW |
| Q | 0.935 | 0.552 | REDRAW |
| G | 0.928 | 0.577 | REDRAW |
| V | 0.919 | 0.590 | REDRAW |
| A | 0.944 | 0.591 | REDRAW |
| S | 0.983 | 0.597 | REDRAW |
| U | 0.943 | 0.618 | REDRAW |
| W | 0.925 | 0.637 | partial |
| O | 0.935 | 0.644 | partial |
| M | 0.962 | 0.657 | partial |
| D | 0.965 | 0.664 | partial |
| E | 0.973 | 0.689 | partial |
| C | 0.947 | 0.691 | partial |
| K | 0.961 | 0.709 | partial |
| Z | 0.949 | 0.717 | partial |
| T | 0.958 | 0.717 | partial |
| R | 0.985 | 0.725 | partial |
| X | 0.956 | 0.733 | partial |
| F | 0.976 | 0.748 | partial |
| P | 1.012 | 0.750 | partial |
| Y | 0.924 | 0.774 | width only |
| B | 1.000 | 0.791 | width only |
| J | 1.007 | 0.792 | width only |
| L | 0.931 | 0.813 | width only |
| I | 0.988 | 0.870 | width only |

**N, H, Q, G, V, A, S and U are the eight to redraw.** I, L, J, B and Y want
nothing but the width.

## The faces

| face | lowercase slant | capital slant | cap height it/rom |
|---|---|---|---|
| Van den Keere | 13.1 | 9.4 | 0.997 |
| Venetian 301 | 11.6 | 13.1 | 0.957 |
| Golden Cockerel | 12.0 | 12.0 | 1.000 |
| Lutetia Nova | 11.1 | 11.2 | 1.001 |
| DTL Romulus | 11.1 | 11.2 | 1.000 |
| Dante MT | 8.8 | 8.6 | 1.000 |
| Warbler Text | 17.8 | 15.7 | 1.000 |
| Coelacanth | 14.3 | 13.8 | 1.009 |
| Junicode | 13.0 | 16.0 | 1.003 |
| Accanthis | 15.1 | 15.0 | 1.000 |
| Domitian | 11.7 | 9.7 | 1.000 |
| DTL Fleischmann | 20.0 | 17.2 | 1.000 |
| Caledonia | 13.4 | 12.1 | 1.003 |
| Edgar | 18.3 | 15.0 | 1.000 |
| Times New Roman | 16.2 | 16.3 | 1.000 |
| Georgia | 13.0 | 12.9 | 1.000 |
| Albo TODAY | 10.8 | 10.9 | 1.000 |

**The Albo row is the agent's, and it is NOT re-verified.** It reads a slant of
11 degrees where Albo has been built at 13 since round 101, so it is probably an
older cut; the previous session's build directory is gone and it was not
re-measured. Treat Albo's own numbers here as unconfirmed and re-run the script
against a current build before using them.

## Not settled

- Nothing is drawn. The eight letters above are a list, not a design.
- Whether Albo's italic capitals should narrow by the measured 5 per cent
  uniformly or per letter (the per-letter ratios above range 0.92 to 1.01).
- The capital ampersand is queued separately -- the owner asked for a flowing
  adorned curved E form for the italic, which is the chancery *et*, and that is
  a construction question rather than a width one.
