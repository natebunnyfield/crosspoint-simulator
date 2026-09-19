# Albo as a FOUR-STYLE FAMILY — the audit, 2026-09-19

Owner, 2026-09-19: *"continue autonomously on all commonly needed roman,
italic, bold and bold italic characters. take at least one pass at smart
spacing for letters and words on all fonts."*

This file is the measured half of that night's work: what the character set
actually lacked, what was structurally wrong with the family, and the two
weight defects that the rendering hid. The per-round narrative stays in
`docs/albo-bump-markup-2026-09-18.md`; the spacing pass has its own dated
section in `docs/albo-spacing-method.md`; the bold masters are recorded in
`docs/wedge-serif-exploration.md`.

Everything below was measured on builds from this session, not inferred.

## 1. The character set was already nearly complete

Measured against a book face's working set, on the shipped roman:

| group | had | missing |
|---|---|---|
| ASCII | 95/95 | — |
| Latin-1 letters | 62/62 | — |
| Latin-1 other | 17/17 | — |
| Latin Extended-A, the common rows | 32/32 | — |
| the corpus list in the reader's own `docs/font-unicode-coverage.md` (U+2212, the arrows, degree, ≠, ≤, ∞, α, Δ, ✗, ✓) | 14/14 | — |
| punctuation and quotes | 15/18 | U+2010, U+201A, U+201E |
| the dash and space families | 1/12 | U+00AD, U+2010, U+2011, U+2012, U+2015, U+2027, and five typographic spaces |
| fractions | 4/8 | the thirds and the eighths |
| math in prose | 8/11 | U+00B5, U+2031, U+222B |
| the letters a Latin book face carries | 14/16 | U+0149, U+1E9E |

So the gap was a **dash family, a low-quote family, the fractions and one
letter** — not a hole in the alphabet. Sixteen characters were added (rounds
258–260) and every one of them is either the face's own existing drawing at a
codepoint it did not carry, or built from the shipping figures:

- **U+2010 HYPHEN, U+2011 NON-BREAKING HYPHEN, U+00AD SOFT HYPHEN** — the
  hyphen. The soft hyphen is the one that matters: justified text with
  hyphenation needs it, and the reader's own builtin faces all carry it as a
  real inked glyph (`lib/EpdFont/builtinFonts/*.h`), so Albo now behaves as
  every other face on that device does rather than differently.
- **U+2012 FIGURE DASH** at 0.45 of the cap, advance 442. Albo's figures are
  PROPORTIONAL old-style — advances 288 for the 1 to 494 for the 0, mean 440 —
  so there is no tabular width to match and the mean is the honest target. It
  is NOT the en dash's 624, which is what a first pass gave it.
- **U+2015 HORIZONTAL BAR** — the em dash, for quotation dashes.
- **U+201A and U+201E** — the comma, as the opening quotes of German and Czech.
- **U+02BC MODIFIER LETTER APOSTROPHE and U+02BB** — the letter rather than the
  punctuation: Ukrainian, Uzbek, transliterations, and the Hawaiian okina.
- **U+00B5 MICRO SIGN** — the one new drawing. Albo's own u with its left stem
  run on below the baseline, thinning to 0.62 and cut at the family angle the
  way the p's and q's stems end. Not a borrowed Greek mu.
- **U+2153 U+2154 U+215B U+215C U+215D U+215E** — the thirds and the eighths,
  through `symbols2._fraction` from the shipping figures, so a ruling on a
  digit reaches them and nothing can drift.

**Deliberately NOT added, and why.** U+1E9E CAPITAL SHARP S is a real
letterform with two competing standard shapes; inventing one silently is not
how anything else in this face was decided, so it should be offered as an
option ladder and ruled on. The five typographic spaces (U+2007, U+2008,
U+2009, U+200A, U+202F) need an advance-only glyph path — the builder derives
every advance from an ink bounding box — and that is a change to the fitting
code, so it went to the spacing pass rather than being bolted on here.
U+20BF (bitcoin), U+2117, U+20A9/20B9/20BD, U+2023, U+203B, U+2042, U+2031 and
U+222B were judged not commonly needed for a reading face and are recorded
here so the next pass does not re-propose them without a reason.

**One follow-up the additions needed.** A character the fitter does not know
falls to the new-symbol fallback, and four of the additions are quotes, so
they were fitted tighter than the drawings they copy: U+201A took advance 226
where its own drawing, the comma, takes 264, and U+02BC took 197 where the
apostrophe it copies takes 264. The four were added to `PUNCT_MARKS` (round
262) and now measure exactly as their models do — 264/78 for the singles,
415 against the double quote's 416.

## 2. The four styles could not bind as a family, so the bold was unreachable

This is the defect with the largest practical cost and nothing in the
rendering showed it. Measured on the built fonts before the fix:

| style | nameID 1 | nameID 2 | nameID 16/17 | usWeightClass |
|---|---|---|---|---|
| Medium | Albo | **Medium** | — | 500 |
| Italic | Albo | Italic | — | **400** |
| Bold | Albo | Bold | — | 700 |
| BoldItalic | Albo | **BoldItalic** | — | 700 |

The classic name table groups only the four RIBBI slots — Regular, Italic,
Bold, Bold Italic — by subfamily. A subfamily of "Medium" therefore puts the
roman in a family of its own, and **pressing the bold button in any
application cannot find the Bold.** The italic compounded it by declaring
weight 400 against its roman's 500, which separates the pair again on weight,
and "BoldItalic" was missing its space.

Fixed in round 261: nameID 1/2 carry the RIBBI grouping (Albo + Regular /
Italic / Bold / Bold Italic — the Medium is this family's regular weight, per
the owner's round-83 ruling "Rename to Medium"), nameID 16/17 carry the
typographic truth (Albo + Medium / Medium Italic / Bold / Bold Italic), and
`WEIGHT_CLASS["Italic"]` is 500. The full name and the PostScript name keep
each style's shipped identity, so an installed `Albo-Medium` or `Albo-Italic`
is not renamed under the owner. Outlines unchanged: 0 glyphs differ in both
shipped styles.

Structurally complete otherwise, checked rather than assumed: all four styles
carry the `kern` and `liga` features, all five f-ligatures, 485 encoded
codepoints each, identical vertical metrics (typo 1000/−300, win 1000/320,
x-height 429, cap 674), and correct italic angles.

## 3. THE BOLD ITALIC IS NOT A BOLD — 22 of its letters are the regular

The weight axis is `FJORD_STEM` (`outlines/pen.py`); the Medium is 84 and the
bold masters were probed at 107. Measured as the widest ink run across each
letter at y=215 for the lowercase and y=340 for the capitals, Italic against
BoldItalic:

**Byte-identical in both weights (22):** a b c d f h i j l m n p q r t u v w x
y z, and Y.
**Heavier in the bold (30):** e 73→95, g 95→96, k 114→123, o 74→94, s 146→183,
and the capitals — A 86→110, B 123→228, C 87→110, D 91→114, E 143→301,
G 123→220, H 142→297, I 79→100, N 97→122, O 74→92, and the rest.

The n is the clean case: its stems measure 71.0 and 81.5 in the Italic and
**71.0 and 81.5** in the Bold Italic, while the roman's n goes 80 → 101 between
Medium and Bold.

**Cause, located:** `outlines/glyphs/aldine.py` line ~820,
`HM_STEMW = _hm("STEMW", 70.0)  # units`, consumed as `sw = HM_STEMW * hm_u(c)`
where `hm_u(c) = c["xh"] / HM_UNIT`. The Aldine italic's lowercase stem is a
measured ABSOLUTE 70 units scaled only by the x-height ratio, so it cannot
move with the weight axis. The letters that do respond are the ones whose
width comes from `pen.S`, `TH_V` or the bowl profile — which is why the
capitals and e, g, k, o, s got heavier and the arches did not. The fix is to
express those targets as multiples of `pen.S` (dividing the measured value by
the Medium's 84, so the shipped Italic is unchanged to the unit).

The same failure appears in the spacing: the Bold Italic's word space is 232,
exactly the Italic's, while the Bold's is 308 against the Medium's 290.

## 4. The bold may be too light, and the number it rests on is stale

107 is the Bold master of the **retired variable font**
(`docs/wedge-serif-exploration.md`, around line 4072), a ladder anchored on a
Regular of stem 66.9 — a 1.6× jump from a 400. Against today's Medium of 84 it
is a 1.27× jump from a 500, and in a rendered paragraph at 13 px and 40 px the
Bold and the Medium are closer than a bold beside its own text weight should
be. A 500→700 step usually wants roughly 1.35–1.45, which is a stem near
113–122. Treat 107 as unverified until it is measured against real bold text
faces.

## 5. Word space, measured against four references

| | space | em | × the n |
|---|---|---|---|
| Albo Medium | 290 | 0.290 | 0.46 |
| Albo Medium Italic | 232 | 0.232 | 0.49 |
| Albo Bold | 308 | 0.308 | 0.43 |
| Albo Bold Italic | 232 | 0.232 | 0.49 |
| Georgia | | 0.241 | 0.41 |
| Times New Roman | | 0.250 | 0.50 |
| Palatino | | 0.250 | 0.43 |
| Charter Roman | | 0.278 | 0.49 |

The two readings disagree and the disagreement is the point. By the em Albo's
roman is wider than every reference; by the ratio to the n it is 0.46, well
inside their 0.41–0.50. Albo's x-height is large for its em, so the n-ratio is
the honest measure and the roman's word space is defensible as it stands.

## 6. Four spacing faults visible at reading size

Rendered from the sentence *"The printer set the page twice, once for the
proof and once for the run, and in between he changed his mind about the
spacing of the capitals."* in Medium at 13 px ×6 and 40 px ×2 — the same four
words break apart at BOTH sizes, so this is fitting and not rasterisation:

- **about** reads as *a bout*
- **capitals** reads as *capita ls*
- **the** reads as *t he*
- **between** reads as *bet ween*

They are all in the Bold too. The side bearings are NOT grossly wrong, which
is why the observation matters more than the table: the lowercase left
bearings run 25–48 with a median of 36 and the right bearings 21–48 with the
same median, so a+b is a nominal 77 units of gap and o+n is 83 — nearly the
same number, and yet *about* breaks and *on* does not. That is the trap
`docs/albo-spacing-method.md` documents doing exactly what it says: the a and
the c are OPEN on the right, so their own white is being counted as gap. It is
the case Measure 4 (`cmp_space_2d.py`) exists to see and the row-wise measures
cannot.

## What was checked and found CLEAN

- Every codepoint the reader's corpus doc names is present in Albo.
- All four styles carry the same 485 codepoints, the `kern` and `liga`
  features, all five f-ligatures, and identical vertical metrics.
- The sixteen added characters build in all four styles and pass the glitch
  sweep (0 findings of 122 swept) in both shipped styles; the touch sweep is
  unchanged at the roman's 4 pre-existing pairs and the italic's 0.
- Adding them moved no existing glyph: the outline diff against the previous
  build is exactly the new glyphs and nothing else.
- The roman's response to the weight axis is correct everywhere measured.
