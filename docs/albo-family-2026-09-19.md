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

**Fixed in round 263.** `ALD_WF = pen.S / 84.0` multiplies every absolute
THICKNESS in `aldine.py` — the lowercase stem, the head's body and tip, the
exit's tip, the arch's hairline, the dot's two axes, and the B, D, P and Q
capitals' stems, which were absolute 70s as well. POSITIONS are deliberately
not scaled: the pitch, the spring, the arch's apex, the head's reach and the
exit's reach say where the letter is, not how heavy it is. The factor is
exactly 1.0 at the Medium's stem of 84, so the shipped Italic is unchanged to
the unit. Measured after: the n's stems go 71.0 / 81.5 in the Italic to 90.0 /
94.9 in the Bold Italic (they were 71.0 / 81.5 in both), the m, h, u and l the
same way, and **17 of the 26 lowercase now respond to the axis where 5 did.**
The 9 that still do not are recorded as unfinished rather than claimed.

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

## 7. Where the four styles stand at 03:40, measured

| style | glitch sweep | touching pairs | figure spread |
|---|---|---|---|
| Medium | 0 of 122 | 4, all pre-existing (ff, fi, f), fT and VI) | 1.60× |
| Italic | 0 of 122 | 0 | 1.31× |
| Bold | **1** of 122 | 5 | 1.62× |
| Bold Italic | **2** of 122 | 5 | 1.42× |

The two shipped styles are clean. The bold pair's defects, by glyph, so the
next pass does not have to find them again:

- **Bold, the x** — SPLIT, two ink islands of 87,873 and 7,006 units². The
  bottom-left wedge (`X_BL_WEDGE`, `diagonals.py`) comes adrift from the
  strokes at a 107 stem; it is attached at 84.
- **Bold Italic, the P** — CRACK, a hole whose mean width is 6.31 against the
  12.0 floor (area 581, perimeter 184). The bowl closes on the stem.
- **Bold Italic, the ħ** — CRACK, mean width 2.16 (area 128). The bar crosses
  the ascender and the gap left is a hairline.
- **Bold, Q+comma and Q+semicolon** — the long tail crosses the mark. A kern
  pair, not a fitting change, per the rule in `docs/albo-capital-spacing.md`.
- **Bold Italic, q+f, q+p, q+y, q+j, q+1** — five pairs, and these are a
  CONSEQUENCE OF ROUND 263 and must be named as such: before the italic
  followed the weight axis the Bold Italic had 0 touching pairs, because its
  lowercase was not bold. Making the q's tail actually heavy is what put it
  into its neighbours. They want kern pairs at bold italic weight.

None of these five is a reason to undo round 263 — a bold italic whose
lowercase is the regular has no touching pairs for the same reason a blank
page has none.

## 8. The bold masters — measured, and the stem is YOUR ruling

The bold pass measured the `l`'s stem, the `H`'s stem, the `o`'s thinnest bowl
and the `n`'s advance across 12 upright and 11 italic Regular/Bold reference
pairs (`tools/wedge_serif/cmp_bold_stem.py`):

| | stem / x-height | cap stem / cap height |
|---|---|---|
| Albo Medium (84) | 0.1851 | 0.1344 |
| Albo Bold 107 | 0.2345 | 0.1738 |
| **Albo Bold 116** | **0.2526** | **0.1902** |
| Albo Bold 122 | 0.2680 | 0.2033 |
| reference regulars, median | 0.181 | 0.1375 |
| **garalde bolds** (Charter, Dante, Van den Keere, Venetian) | **0.2545** | **0.1933** |
| all 12 reference bolds, median | 0.2999 | 0.2381 |

**116 hits the garalde bold on both measures.** 107 is 8% light on the stem
and 10% on the cap stem — it measures between Hoefler Text's *Regular* and
Dante's *Medium*. The all-reference median wants about 135, but that group is
transitional and Scotch and its bolds are black; Albo belongs with the garalde
four. The counters agree: at 107 the `a` and `e` counters are looser than
every reference bold measured, at 116 they sit inside them.

**The width stays 95, not the 100 I had guessed.** Reference bolds gain only
1.3% (garalde) to 4.2% (all) of `n` advance over their regular. Albo at 116/95
already gains **17.5%**, because the face's own rule holds the n's counter
constant as the stem grows. 100 would add another 2.5 points and buy counter
width the `a` does not need.

**The honest trade, and why nothing is shipped.** With the x fixed, Bold at
107 sweeps **0 findings of 122**. At 116 it is **2** and the bold italic **3**
— new cracks in the `ß` and `φ`, all the same class of butt-join as the x. So
107 is clean and measures like a Medium; 116 measures like a bold and owes two
joins. That is a ruling, not a calculation, and the image that answers it is
`tools/wedge_serif/shape/bold/stem-ladder/ladder-40px-x2.png`.

**Fixed: the roman `x` split in two at bold weight.** `end_wedge` anchors a
wedge half the width it is *given* off the centreline, and the x's bottom-left
wedge is deliberately given the THICK diagonal's width (the owner's 2026-09-14
"increase the visual weight of the bottom left serif in 'x'") while the stroke
under it is drawn at 0.72 of that. The root therefore stands 0.14 of the pen's
width outside the stroke's edge — a fraction of the stem, so it grows with
weight. At 84 the wedge's body bridges it; by 107 it does not. `x_bl_anchor()`
holds the overhang at the units it has at the Medium via `min(1.0, 84/pen.S)`,
exactly 1.0 at 84, so the Medium is untouched.

**An instrument bug that inverted the answer once, recorded because it looked
right.** The first cut of the bold measurement read the x-height off the `x`
alone — and Albo's `x` has flaring wedge serifs that overshoot its own
x-height (ink 481 against a declared 429), an overshoot that GROWS with the
stem, so the denominator moved with the thing being measured. Albo Medium read
0.1663 where it is 0.1851: the difference between "lighter than every regular
measured" and "the median regular". The tool now takes the minimum ink height
over `x z v w`. Declared metrics are no fallback either — Dante MT declares an
`sxHeight` of 403 on a 2048-em body, a 5× error that looks entirely plausible.

## 9. What a weight axis actually changes — Albo against 23 reference pairs

Owner, 2026-09-19: *"so bold just increases the stroke widths without
increasing the width as much, give me the numbers for regular (skip medium
500) and bold changes to width, thickness, thinness, contrast, etc in albo and
other reference fonts."*

**The premise is true of the references and false of Albo.** That is the
finding. Instrument: `tools/wedge_serif/cmp_weight_axis.py`, which imports
`cmp_bold_stem`'s measures rather than re-implementing them. Albo's Regular is
the 400 (`FJORD_STEM=66.9`), not the shipped Medium.

**Bold ÷ regular, median across the families:**

| | 12 upright references | 11 italic references | **Albo 66.9 → 116** | Albo italic |
|---|---|---|---|---|
| thickness (stem/xh) | **1.66×** (1.42–2.25) | 1.59× (1.43–2.50) | **1.69×** ✓ | 1.69× ✓ |
| thinness (hair/xh) | 1.39× (1.11–2.66) | 1.31× (0.97–2.08) | **1.68×** high | 1.58× |
| contrast (thick:thin) | 1.17× (0.85–1.53) | 1.22× (0.90–1.59) | **1.00×** flat | 1.07× |
| **WIDTH (n advance/xh)** | **1.04×** (0.97–1.16) | 1.03× (0.97–1.40) | **1.30×** ✗ | 1.10× |
| cap stem (cap/capH) | 1.68× (1.47–1.94) | 1.66× (1.45–1.87) | 1.76× ✓ | 1.81× ✓ |

**The width is the anomaly, and it is the owner's own observation inverted.**
A real bold buys almost no width — the median family widens its `n` by 4%
while thickening its stem by 66%, and five of the twelve get *narrower*
(Venetian 0.97, Van den Keere 0.98, Edgar 0.99). Albo widens **30%**. The
cause is the face's own documented rule, `NW = n_width·WF + (S−110)·0.9`,
which holds the n's counter constant as the stem grows; every reference lets
the counter close instead. At 116 Albo's `n` advance is 1.70 x-heights where
the widest reference bold is Baskerville's 1.51 and the median is 1.31.

**Albo's contrast does not move at all, at any weight**, because the axis
defines `hair = stem × (1 − CONTRAST)` and so preserves the ratio exactly.
The references mostly *increase* contrast into the bold (Warbler 1.53×,
Georgia 1.44×, Dante 1.43×), a few decrease it (Baskerville 0.85×).

**And the absolute numbers say the roman is flat and light to begin with:**

| | Albo Regular | reference regulars |
|---|---|---|
| thickness, stem/xh | **0.1495** | 0.144–0.207, median 0.181 |
| thinness, hair/xh | **0.1134** | 0.058–0.118, median 0.081 |
| contrast, thick:thin | **1.32:1** | 1.49–3.00:1, median 2.34:1 |

Albo's Regular has the *second thickest hairline in the set* and nearly the
thinnest stem, so its contrast is the lowest of the thirteen. The Aldine
italic does not share this — it measures 2.11:1, inside the italic
references' 1.36–2.94 — so this is the ROMAN's low contrast, not the face's,
and it is pre-existing at every weight rather than anything the bold did.

None of the three is fixed. They are design questions: whether the bold should
buy less width, whether the roman's contrast should rise into the bold as most
references do, and whether the roman's 1.32:1 is the intended colour.

## STANDING RULING — the italic is TWO weights: 400 and 700

Owner, 2026-09-19, asked whether to run the end-correction pass on the italic
200/700/900: **"italic is just 400 and 700."**

So the italic family is the Italic (400) and the Bold Italic (700) and nothing
else: no italic 200, no italic 900 — not built, not gated, not proofed. They
stop appearing in ladders and triage. The roman keeps its four.

## STANDING RULING — the family is FOUR weights: 200, 400, 700, 900

Owner, 2026-09-19: *"for future cuts: only test and ship 200 400 700 900."*

So 100, 300, 500, 600 and 800 are **out of scope**: not built, not gated, not
proofed, not shipped. They stop appearing in ladders and in triage. The nine-
rung sweep below is the evidence that produced this ruling and stays as a
dated record; it is not a plan.

Two consequences worth stating plainly, because both cut against what the
repo says today:

- **The 500 is no longer a shipping class.** Today's `Albo-Medium.ttf` IS the
  500 (the owner's round-83 ruling, *"Rename to Medium"*), and it is the only
  finished drawing in the face. Under this ruling the shipping regular becomes
  the **400**, which is the class round 76 derived at stem 66.9 and which
  nothing in the repo currently builds. That is a rename and a re-anchor, not
  a redraw, and it needs its own ruling before anything moves.
- **900 — extrapolated, then MEASURED, and it holds.** Its stem of 148 was
  extrapolated with nothing behind it. Measured 2026-09-19 on the families on
  this machine that ship a black: Charter's black is 1.35× its bold and
  Superclarendon's 1.25× (serif/slab median **1.30×**); Avenir Next 1.34× and
  Gill Sans 1.45× (sans median 1.39×). Albo's 148 is **1.28× its 700**, which
  at the serif median would be 151 — within 2%. So 148 stands, and this is a
  negative result recorded so it is not re-derived: the black-over-bold step
  is the right anchor because the 700 was itself calibrated; the black-over-
  regular step (serif median 1.82× → 122) is not, because Albo's 400→700 step
  already sits at the top of the reference band. Two serifs is a thin sample;
  Iowan Old Style ships a Black too but its file was not where the script
  looked, and it is the next family to add.

## 10. The nine-weight ladder, "Hamburg and wafflers."

The original test is **round 76, 2026-09-13** (`outlines/cmp/weights.py`,
page https://claude.ai/code/artifact/565ef7ca-ef1c-48fe-b27f-78e1b1ff7ed0).
It sets *Hamburgefonstiv 1928* and covers **100 to 500 only** — the owner's
ask that day was *"make thinner versions (calibrate against industry norms
(100 200 300 400) if we consider this to be 500"*. The fonts are still in
`build/fjord-fonts/weights/`. There was never a 600–900 end; it did not exist
until 2026-09-19.

Re-run 2026-09-19 with "Hamburg and wafflers." across all nine classes. Only
the stem moves — contrast held at 0.80 and width at 95 for every rung, so it
is a pure weight axis with nothing confounded. Page:
https://claude.ai/artifact/TUa5tMhuQekcdhXiPQuMEP

| class | name | stem | × the 500 | where the number comes from | glitch findings |
|---|---|---|---|---|---|
| 100 | Thin | 28.9 | 0.34 | round 76, measured | 12 |
| 200 | ExtraLight | 43.8 | 0.52 | round 76, measured | 9 |
| 300 | Light | 54.6 | 0.65 | round 76, measured | 4 |
| 400 | Regular | 66.9 | 0.80 | round 76, measured | 3 |
| 500 | Medium | 84 | 1.00 | the anchor, shipped | **0** |
| 600 | SemiBold | 100 | 1.19 | interpolated 500–700 | 3 |
| 700 | Bold | 116 | 1.38 | measured on the garalde bolds (§8) | 2 |
| 800 | ExtraBold | 132 | 1.57 | extrapolated | 2 |
| 900 | Black | 148 | 1.76 | extrapolated | 8 |

The light end thins the hairline faster than the stem, so by 200 and 100 the
bowls break — round 76 already called those two *"previews, not finished
cuts."* The heavy end closes the counters and the `ffl` ligature blocks up
first, which is why 900 jumps back to eight findings after 700 and 800 sit at
two. **The usable span today is about 300 to 800, and only the 500 is
finished.** The 800 and 900 stems rest on nothing measured: no serif family on
this machine ships either class.

## 11. What the 400 and the 500 WERE, and what they are now

Both were first built on 2026-09-13 in round 76 and those files are still on
disk at `build/fjord-fonts/weights/` (94 glyphs each; today's builds carry
486). Measured with the same instrument:

| | stem/xh | hair/xh | thick:thin | n adv/xh | cap/capH |
|---|---|---|---|---|---|
| 400 — round 76 | 0.1461 | 0.0932 | 1.57 | 1.3171 | 0.1078 |
| 400 — now | 0.1495 | **0.1134** | **1.32** | 1.3106 | 0.1082 |
| 500 — round 76 | 0.1779 | 0.1078 | 1.65 | 1.4413 | 0.1348 |
| 500 — now | 0.1851 | **0.1388** | **1.33** | 1.4437 | 0.1344 |

**The stems did not move.** 66.9 and 84 design units then and now; the 2–4%
in the measured column is a hundred and eighty rounds of redrawing, not the
axis. **The widths and the capitals did not move either** — 1.3171 → 1.3106
and 1.4413 → 1.4437, 0.1078 → 0.1082 and 0.1348 → 0.1344.

**What changed is the hairline.** It thickened 22% on the 400 and 29% on the
500, and the contrast fell from 1.57 and 1.65 to 1.32 and 1.33. Round 76
built both at a CONTRAST dial of 0.95 (the 400 at its own derived 0.892);
every build since runs at **0.80**, which is the round-62 default the code
still carries — round 65's amendment to 0.95 survives as a comment in
`pen.py` above the line that sets 0.80, and every build command in the repo
passes `FJORD_CONTRAST=0.80` explicitly anyway. The dial is
`hair = stem × (1 − contrast)`, so 0.95 gives a hairline 5% of the stem and
0.80 gives 20%. That one number is most of the difference, and it is why the
roman now measures as the flattest face on the weight plane.

**And the names changed under them.** The file called `Albo-Regular.ttf` WAS
the 84-stem drawing. Round 76 recommended renaming it and the owner ruled it
in round 83 — *"Rename to Medium"* — so the drawing that had been the Regular
became the 500, and a NEW, lighter 400 was derived beneath it at stem 66.9.
The 500 is what ships. **The 400 does not ship**: no build command in the
repo produces it, and it exists only as those round-76 files and as a recipe.

Graphs of the whole plane, every reference family and both of Albo's nine-rung
ladders: `tools/wedge_serif/cmp_weight_plots.py`,
https://claude.ai/artifact/3oRe6qTBt6jMNFngAwvkok

## RULING — the family re-anchors on the 400 at stem 66.9 (round 266)

Owner 2026-09-19, asked how to resolve the four-weight ruling against a face
drawn and judged at stem 84: **re-anchor to 66.9**. He was shown the
measurement first — 66.9 puts stem/x-height at 0.1495 where the twelve
reference regulars run a median of 0.181, so the shipping face lands lighter
than every one of them — and ruled for it. `DESIGN["stem"]` is 66.9.

**The contrast ruling survives the move**: the 400 measures **1.71:1**,
against the 1.67 the 500 measured, so "around 1.7" holds at the new anchor
without touching the dials.

**What it cost, and what I fixed.** The two shipped styles went from 0 glitch
findings to 3 each. All three were the same failure: **a part positioned on
the x-height grid, which does not move, overlapping a stroke sized in S, which
thins with the weight.** Two are fixed, weight-proof:

- **the ffi ligature** shipped as three ink islands. Measured, the first f's
  bar ends at x 274 and the second f's begins at 302 — a 28-unit gap that does
  not exist at 84. `_bridge` in `ligatures.py` joins two f-bars across
  whatever gap the weight opens, in their own y band and at their own
  thickness, and returns nothing when they already touch, so the drawing at 84
  is untouched. It covers ff, ffi and ffl.
- **the Ω** shipped as three islands, its two feet loose. The ring's cut was
  swept at 84, where CAP × 0.05–0.06 gives one island; it now scales as
  `CAP × 0.06 × min(1, S/84)`, cutting lower — more leg into the foot — as the
  face lightens.

**RULED 2026-09-19: the β stays as it is.** Owner, offered a re-sweep, a
wider Greek pass, or leaving it: *"Leave it, it is recorded."* So both shipped
styles carry one glitch finding, in a Greek lowercase, deliberately. It stops
appearing in triage; the measurement and the failed attempt below are the
record for whoever picks it up.

**Still broken, and not guessed at: the β.** The two bowls' centres were swept
at 84, where (0.68, 0.26) just closes the slit where they meet the stem; at
66.9 it reopens as a 4.17-unit crack. Moving the bowls toward each other — the
same move that closed it at 84 — made it **worse**, two cracks of 5.84 and
2.89, so the relation is not monotonic in the centres and the fix is a
re-sweep of that letter at the new anchor, not a nudge. One finding in each
shipped style, in a Greek lowercase.

Final gates at the new anchor: roman **1 finding**, 3 touching pairs (down
from 4), figure spread 1.62×; italic **1 finding**, 0 touching. The other
three weights are unchanged in kind — ExtraLight 7 findings, Bold 2, Black 7 —
and remain unfinished cuts.

## RULING — the contrast ships at 1.7 (round 265)

Owner 2026-09-19, on the dialling page: **"around 1.7 wins"**. Step 2 of the
grid ships: `BOWL['hair'] = 0.46` (`primitives.py`) and `O_FLOOR_ADJ = 0.50`
(`rounds.py`). Round 92's floor is lowered by his ruling; the `1 − 0.5c`
mapping is kept in the file as history and no longer decides.

Built and measured on all four styles:

| style | thick:thin | hairline | stem | glitch | touching |
|---|---|---|---|---|---|
| Medium | **1.67** | 47.5u | 79.6u | 0 of 122 | 4, all pre-existing |
| Italic | 2.15 | 30.6u | 65.7u | 0 of 122 | 0 |
| Bold | 1.68 | 64.7u | 108.4u | 2 | 4 |
| Bold Italic | 2.26 | 40.1u | 90.4u | 3 | **8** |

**The two shipped styles are clean and their gates did not move** — glitch 0
of 122 on both, the roman's four pre-existing touching pairs, the italic's
zero, figure spread 1.59× and 1.32× against the 2.50× allowed. The roman went
from flatter than every reference regular (1.32) to inside their range (1.67).

**What it cost, stated plainly.** 103 roman glyphs and 62 italic glyphs
changed outline — every round shape in the face, which is what a contrast
ruling means. And the **bold italic's touching pairs went 5 → 8**: thinner
hairlines at bold weight bring more near-collisions. That style is not yet
finished and its gates were already the worst of the four, but the regression
is real and is recorded rather than glossed.

**The italic barely moved** — 2.11 → 2.15 — because the Aldine italic was
already drawn with real contrast and sits inside its own reference band
either way. The ruling is effectively a roman change.

Proofs: `tools/wedge_serif/shape/contrast/ship-{13,17,40}px.png`.

## 12. Round 264 — the contrast is three clamps, and the last is a ruling

Owner 2026-09-19, choosing between a new test phrase and a redraw:
**"Redraw Albo's contrast."** Nothing is shipped; both new dials default to
today's drawing and the Medium and Italic builds are byte-identical, 0 of 486
glyphs differing.

Laddered at the **400**, since that is the regular under the four-weight
ruling. What was found, in order:

1. **`FJORD_CONTRAST` cannot reach a real contrast.** From 0.80 to 0.98 the
   built thick:thin moves only **1.32 → 1.50**. The bowl's hairline is
   `BOWL['hair'] = 1 − 0.5c` (`primitives.py`), which bottoms out at 0.50 of
   the stem even at c = 1.0. The architecture, not the setting, holds Albo
   flat.
2. **Bypassed with a direct dial (`ALBO_BOWL_HAIR`), it saturates at 1.61.**
   The o's hairline may not go under `O_FLOOR_ADJ` × the stem.
3. **Lowering that floor (`ALBO_O_FLOOR`) reaches 1.87 and stops again**, on a
   third clamp not chased further.

| arm | bowl hair | o floor | thick:thin | hairline, units | glitch |
|---|---|---|---|---|---|
| today | 0.60 | 0.55 | 1.32 | 48.6 | 3 |
| mid | 0.50 | 0.55 | 1.57 | 40.9 | 3 |
| opened | 0.40 | 0.46 | **1.87** | 34.3 | 3 |
| reference regulars | | | 1.49–3.00, median 2.34 | | |
| Albo italic today | | | 2.11 | | |

**CORRECTION to point 3 above.** There is no third clamp. The saturation at
1.87 was the o's floor binding again, because that ladder held the bowl hair
at 0.40 while only the floor moved. Lowering both together reaches **2.15:1
at the 400**, against the reference regulars' median of 2.34 — so the face can
very nearly get there, and the only thing in the way is round 92's ruling.
Measured across the whole grid, the contrast the two dials reach:

| | 200 | 400 | 700 | 900 |
|---|---|---|---|---|
| step 0 (today: hair 0.60, floor 0.55) | 1.30 | 1.32 | 1.32 | 1.33 |
| step 1 (0.53 / 0.55) | 1.44 | 1.49 | 1.47 | 1.49 |
| step 2 (0.46 / 0.50) | 1.70 | 1.71 | 1.68 | 1.69 |
| step 3 (0.40 / 0.46) | 1.86 | 1.87 | 1.88 | 1.92 |
| step 4 (0.34 / 0.40) | 2.05 | **2.15** | 2.18 | 2.19 |

The ratio holds within 0.05 across all four weights at every step, so the two
dials move the whole family together rather than one weight at a time.

**`O_FLOOR_ADJ` is an owner ruling, not an oversight.** Round 92 set it
because the o "read hollow — its knot the lowest of any letter (−11%), the
hairs dropping to gray at 13 pt", which is the size he reads at on the
four-level pipeline. Opening the contrast is therefore a LEGIBILITY trade, and
the three arms are rendered at 13 px, 17 px and 40 px for him to rule on:
https://claude.ai/artifact/GuqYrtvf5hbNqc8dKhaDtu

Glitch sweep is 3 findings on every arm, so opening the contrast breaks
nothing that was not already broken at this weight.

**The dialling page** is twenty real builds — four weights by five contrast
steps, each built, measured and subset, with the sliders swapping between them
rather than interpolating: https://claude.ai/artifact/K6YU6cCokZiZd4G4NbdGE2
It is regenerated by `tools/wedge_serif/albo_dial_grid.py` (build, measure,
subset, emit) and `albo_dial_page.py` (the page). Judge SHAPE there: it renders
with the browser's antialiasing, not the reader's four grey levels, so the
legibility half of the ruling still belongs to the 13 px proofs.

## 13. Round 267 — the 200 and the 900 corrected, by class

Owner 2026-09-19: *"take pass at correcting 200 and 900 issues based on
prior md findings and strategies."* The strategies were the ones already in
this file: the x's `min(1, 84/S)` anchor, the Ω's scaled cut, the ffi bridge,
`ALD_WF`. Every finding at both ends fell into one of three classes, and every
fix is weight-proof and gated so the shipped 400 does not move except where a
letter was structurally redrawn.

| weight | before | after | what is left |
|---|---|---|---|
| 200 (stem 43.8) | 7 findings | **1** | the β, ruled |
| 400 (shipped) | 1 | **1** | the β, ruled |
| 700 (stem 116) | 2 | **0** | — |
| 900 (stem 148) | 7 | **0** | — |
| italic 400 | 1 | **1** | the β, ruled |

**Class 1 — joins sized in S that open at the light end** (a part on the
x-height grid, which does not move, overlapping a stroke sized in the stem,
which thins). The **y**'s diagonal ended S × 0.4 below the line, 17.5 units at
43.8, and the tail's ink no longer covered it: the end is now the deeper of
S × 0.4 or 0.16 of the descender, gated under the 400's stem so the shipped
letter is byte-identical. The **γ**'s short stroke ended 39 units beside the
long one's centreline and now ends on it. The **θ**'s bar stopped inside the
counter and now runs into the walls. The **Ω**'s feet ended 18 units short of
the legs and now reach under them. The **ε**'s upper arc ended its corner on
the lower arc's edge (a 2.8-unit point contact) and now buries 7 units inside
it. The **ff/ffi/ffl** first hook only kissed the second hook (2.2 units) and
goes further in and higher under the 400's stem.

**Class 2 — small counters that collapse at the heavy end.** At a 148 stem
a bowl wall of 0.86–0.92 × S is 127–136 units against radii of 112–154, so
the θ, φ, ω, ρ and þ counters closed to slits — and I misread the ρ and þ as
join faults first, pushed their bowls into the stem, and measured no change
before seeing why. All five now scale the wall by `min(1, 84/S)` above the
stem they were drawn at; at and under 84 they are as drawn. The **ß**
lightens its three curved strokes by √(84/S) for the same reason.

**Class 3 — positions that drift with weight.** The **Œ** placed the E by a
fraction of the E's own width, and at 148 the E's serifs widen its box faster
than the O's flank reaches it, so the pair split. `_joined` now tests the
inked union and slides the second letter left in 4-unit steps until exactly
one island merges, capped at a quarter of its width, and builds from the raw
parts — so æ, œ, ĳ and Ĳ, which needed no slide, are byte-identical. (The
first cut of that loop asked for a single island and slid the ĳ, which has
two dots, 240 units into itself; caught by the 400 diff.) The **C**'s beak
left a 2.9-unit sliver against the arc at 148 and takes a 4-unit
morphological close above stem 84.

**Moved at the shipped 400, in both styles: Ω, γ, ε, θ, ω** — five Greek
letters, none ruled on, each a structural join. Every Latin glyph, every
figure and every ligature is byte-identical to the build before this pass.
The italic's figure spread reads 1.36×; it was 1.36× before the pass too (the
re-anchor moved it from 1.32×), so nothing here touched it.

Proofs: `tools/wedge_serif/shape/weights267/` (every failing glyph before
and after at both ends, and runs at 13 and 40 px) and the page
https://claude.ai/artifact/JfDfKSeZL8mNbX1nggfSNH

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
