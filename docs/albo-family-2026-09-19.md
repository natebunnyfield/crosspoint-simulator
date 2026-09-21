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

## 14. Round 268 — the italic 700 corrected, and the ring at both heavy ends

Owner 2026-09-19, narrowing the round-267 pass: *"italic is just 400 and
700."* So the italic pass is one weight, the BoldItalic at stem 116, judged
against the shipped Italic at 66.9, which must not move.

| style | glitch before | after | touching / under the floor before | after |
|---|---|---|---|---|
| BoldItalic 700 | 2 (P, ħ) | **0** | 8 touching, 5 under | **0 / 0** |
| Italic 400 | 1 (β, ruled) | 1 | 0 / 0 | 0 / 0, byte-identical |
| Bold 700 | 0 | 0 | 4 / 7 / 14 exempt (round 267's) | unchanged; only the ring moved |
| Black 900 | 0 | 0 | — | rebuilt for the ring; 0 findings |
| Regular 400 | 1 (β) | 1 | — | byte-identical |

**The P (class 3, a declared position drifting with weight).** The italic P's
hairline gap is a cut rectangle placed by `P_GAP_X`, a number calibrated at
the 400 where the stem's right edge sits at x0 + 33 and the cut 10 units past
it, down through the arm's free terminal and out to the paper — so the 400's
counter is OPEN and its census shows no hole at all. At 116 the stem is 132
wide: the same cut sat entirely inside it (a 9 × 86 rectangle of paper with
four vertices, the 581-unit CRACK), while the thicker arm reached below the
cut's bottom and above its top and landed on the stem. Both edges are now
read from the strokes actually drawn above stem 84 — the cut sits 10 units
past the stem's measured edge and spans the terminal's measured thickness —
so the 400's construction holds at the 700: free terminal, open counter. The
pilcrow is built from this bowl and was a solid black mass at the 700 for the
same reason; it inherits the fix. My first diagnosis was wrong and is
recorded: deepening the arc's end with weight changed nothing, because the
hole was the rectangle, not the arm.

**The barred letters (ħ đ Đ Ð ŧ Ŧ Ħ).** The ħ's bar runs under the italic
h's head bracket and the two enclose a sliver 49 units long and 4 wide at its
mouth (209 units² drawn, 90 after the build's 1.2-unit ink spread narrows
it). A 2-unit close did nothing — a close fills only what is narrower than
twice its radius — so it is the C's 4, gated above 84 AND to the italic: the
roman 700 and 900 barred letters had no finding and are byte-identical.

**The q's foot, thirteen kern pairs, gated above 84.** The italic q ships
the p's measured 116-unit foot, which does not move with weight; the next
letter's descender does. At the 700 the foot touched f y p j 1 2 v w and ran
under the floor against m r n i, and the R's leg under it against the 1.
Each value is the measured overlap plus the 0.012 em floor plus clearance,
**added to what the pair already carried** — qj qf qy qp were kerned at 126
108 90 18 and the overlaps were measured with that kern in. The first cut
assigned instead of adding and made three of the four worse (qj −0.0205 →
−0.1125 em, exactly the 92 units it took away). The Italic's GPOS is
identical: 526 pairs, 0 changed.

**The ring accent (class 2, both styles, both heavy ends).** Found by the
`--all` sweep, which the round-267 pass did not run: the ring's radius is on
the accent grid and its wall is 0.62 of the pen, so at the 700 the wall is 72
units on a 93-unit radius and the counter is two slits 7 and 8 units wide —
in the roman 700 too, and å Å ů Ů carry it. The wall now scales by
`min(1, 84/S)` above 84 as the Greek bowls do: at the 700 the counter is
3,080 units² and 22 wide, at the 900 3,026 and 21. This is the ONE glyph
that moved in the roman 700 (`ring`, and the four composites that reference
it); the 200 is under the gate and was not rebuilt.

**Names.** The Italic declared usWeightClass 500 and "Medium Italic" since
round 261, when the Medium was the text weight; since the re-anchor it is the
Regular's italic and now declares 400, "Italic", "Albo Italic". Outlines and
kerning untouched.

**The rest of the `--all` sweep, recorded and not fixed.** At the 400s: ¥ β
√ ♕ ♣ ♤ ♧ ⇔, all documented in `cmp_aldine_glitch.py`'s own list of accepted
symbol cracks. At the 700s the same set plus ✓ (2.5 units, the tick's fold,
whose documented cure changes every `_s` glyph) — and none of them is a
letter.

**An instrument bug.** `diffglyphs.py`'s "kern same" compared the legacy
`kern` table, which these fonts do not carry, so it read None == None and
would have called any GPOS change identical. It compares GPOS pair values now;
every byte-identity claim above was re-made with it.

**Owner's report the same day, measured — the u's right stem.** *"check that
the right stem of 'u' is bit low on any shipping font faces."* Rasterised at
one pixel per unit, the top of each stem against the 429 x-height:

| face | u left stem | u right stem | n left stem | ı |
|---|---|---|---|---|
| Regular 400, Bold 700, Black 900, ExtraLight 200 | 430 | **430** | 430 | 430 |
| Italic 400 | 422 | **400** (−29) | 422 | 430 |
| BoldItalic 700 | 425 | **368** (−61) | 426 | 430 |

Confirmed on both italics and on no roman. The aldine u's right stem is
`hm_stem(c, x1, 0, xh * 0.985)` with a cut head, so the cut's drop grows
with the stem's width — 22 units under its own left stem at the 400 and 57
at the 700. Not corrected in this round; awaiting the ruling.

**What remains before a TestFlight build carries these fonts** (asked the
same day). Albo is already an installed family in the firmware recipe
(`lib/EpdFont/scripts/sd-fonts.yaml`, installed 2026-09-14) and the seed
tree the deploy uses (`~/src/crosspoint-reader/fs_/fonts/Albo`, 1x + 2x)
carries the 2026-09-14 TTFs — five cuts, the pre-Aldine italic, the old
500 as the text weight. So the route is a refresh, not an install:

1. Copy the four TTFs of this round into
   `~/src/crosspoint-reader/lib/EpdFont/local_fonts/Albo/` and delete
   `Albo-SemiBold.ttf` (the 500 is retired; the reader has four style slots).
   Update the recipe's comment block (five cuts → four, 11° → 13°, 470 → 486
   glyphs); its `metrics: {ascent: 1023, descent: -343}` still clears the new
   extents (yMax 1004, yMin −322).
2. `build-sd-fonts.py --only Albo` at 1x and `--scale 2` into that seed
   tree; the ramp is `[8, 10, 12, 14, 16, 18]`.
3. `tools/validate_seed_fonts.py` on the tree with the recipe — the gate the
   iOS configure runs anyway.
4. A 1x contact sheet from the `.cpfont` (the reader's own raster, 2-bit,
   autohinted): 13 pt is 27 px on the X3, the Regular's stem 1.8 px and its
   hair 0.2 px. The 400's paleness against the reference regulars (section
   11, deferred) is decided on that raster, not on FreeType's.
5. `osascript ios/deploy.applescript "CROSSPOINT_SEED_FONTS_DIR=$HOME/src/crosspoint-reader/fs_/fonts"`
   from a GUI Terminal, after both repos are pushed.

Not blocking, worth knowing: the `reading` interval's codepoints Albo does
not draw fall to Noto on the page (the build prints the count); the 200 and
900 have no reader slot and are family cuts only.

Proofs: `tools/wedge_serif/shape/weights268/` and the page
https://claude.ai/artifact/Jkd26fTEVfcfi1XANnNeBE

## 15. Round 269 -- the bold italic evened

Owner 2026-09-19: *"subagent to correct unequal illegible weights of italic
700. need to be more even in common english word images."* BoldItalic at stem
116, judged against the shipped Italic 400 at 66.9, which may not move.

**The cause, measured before anything was edited.** Horizontal ink runs at one
pixel per unit on five rows of the x-height (a shear maps a horizontal run to
a horizontal run of the same length, so no unshearing is needed), round-268
BoldItalic beside the shipped Italic: **t c f w y v x z j g came out
byte-identical at the two weights** -- the t's stem 67 at both, the v's thick
79, the y's 69/36, the c's wall 69 -- and the bowls of a b d p q read the same
70-72 wall at the 700 as at the 400, beside stems that had gone 57 -> 98. The
ridge survey said the same thing as a ratio: the weight axis takes a stem from
the 400 to the 700 by 1.73x, the hm letters measured 1.65-1.69x, and those ten
letters measured **0.98-1.03x** -- no response to the axis at all. In the
capitals the R (1.00x), Y (0.97x) and K (1.32x) were the same fault.

Round 263 had put the hm_* letters on the axis through `ALD_WF = S / 84` and
left every other declared width where the reference measured it. Those widths
sit in six places, and every one is in absolute units that never met ALD_WF:
`d_pen`'s tables (f t j v w x y z, the k's arm and leg), `d_ball` (the v w x y
terminals and the y's drop), `keyed_ring`'s tables (the a b d p q bowls and
the g's two rings), the c's `C_RING`, the g's neck and ear pen (`G_R_PEN` 84),
the r's ball (`R_ARM_W/H`), the p and q's foot thickness (`PQ_FOOT_T`), and in
the capitals `_R_traced`'s widths (x the CAP, so the R and K) and the Y's
cap-unit width tables.

**The fix is one factor.** `ALD_WF_UP = max(1.0, S / 84)` -- S / 84 above the
Medium and exactly 1.0 at and under it -- multiplies every width in that list.
It is not folded into ALD_WF, deliberately: ALD_WF is 0.796 at the 400 and the
shipped Italic depends on it being so; a factor that also went DOWN would
re-cut ten letters of a face the owner has already judged. `keyed_ring` takes
it as a new `wscale` argument at the five lowercase call sites and the g's two
rings rather than inside the helper, because the capital O's ring was already
on the axis (1.67x) and a factor inside the helper would have scaled it twice.
The hand tables (`A_DROOP_HAND`, the g's presses) and every POSITION -- the
heads' reaches, the foot's two arms, the pitch, the tails' extents -- are left
in their own units, for the reason ALD_WF's note gives.

| letter | run at 0.50 xh, before | after | what it is |
|---|---|---|---|
| t | 67 | 91 | stem (`d_pen`) |
| f | 74 | 101 | stem (`d_pen`) |
| j | 70 | 96 | stem (`d_pen`) |
| c | 69 | 96 | left wall (`C_RING`) |
| v | 79 / 33 | 108 / 45 | thick / thin (`d_pen`) |
| w | 65 / 32 / 65 / 33 | 89 / 43 / 88 / 45 | four strokes (`d_pen`) |
| x | 72 | 99 | thick (`d_pen`) |
| y | 69 / 36 | 95 / 49 | thick / thin (`d_pen`) |
| z | 50 | 69 | the diagonal, a hairline by design (`d_pen`) |
| k | 80 (0.30 row) | 110 | arm (`d_pen`) |
| a | 72 / 98 | 98 / 98 | bowl wall / stem (`A_RING`) |
| b | 99 / 71 | 99 / 96 | stem / bowl wall (`B_BOWL_RING`) |
| d | 71 / 99 | 96 / 99 | bowl wall / stem (`D_RING`) |
| p | 99 / 70 | 102 / 96 | stem / bowl wall (`B_RING`) |
| q | 71 / 100 | 96 / 100 | bowl wall / stem (`A_RING`) |
| g | 97 / 61 | 129 / 76 | bowl walls (`G_RING` on `_g_roman`'s pen) |
| r | 111 (0.85 row) | 127 | the ball |
| R | 67 | 99 | bowl (`_R_traced`, x cap) |
| Y | 66 | 89 | arm (x cap) |
| K | 97 / 40 (0.30 / 0.70) | 128 / 54 | arm / leg (`_R_traced`) |

The n's stem is 97-99 on every row before and after; the roman 700's is
109-111. The a's counter at 0.50 goes 157 -> 131 wide, the b's 174 -> 149,
the p's 187 -> 158, the q's 202 -> 177 -- all still wider than the roman 700's
(89, 214, 206, 205) except the b's, and open.

**The ridge survey, regrouped by construction family** (BoldItalic against the
roman 700, `cmp_weight_survey.py` at 380 px, `--slant 13`; the survey's own
case grouping flags the alphabet rather than the drawing):

| family | n | median before | after | spread before | after | over 15% before | after |
|---|---|---|---|---|---|---|---|
| stem | 30 | 99.3 | 99.3 | -34% .. +30% | **-11% .. +30%** | f t R j p light; J L P B D F T H heavy | J L P B D F T H heavy, as the roman's F H I J L P T are |
| round | 11 | 80.2 | 90.7 | -23% .. +35% | **-23% .. +20%** | g c light; s G O S Q heavy | e (the roman's e reads -28%); Q |
| diag | 11 | 70.0 | 81.3 | -42% .. +34% | **-35% .. +21%** | y z x w light; A W V | y; V |
| figure | 10 | 86.9 | 86.9 | -22% .. +25% | -22% .. +25% | 4, 1 | 4, 1 -- set aside by ruling |

Per letter, the italic 700's stroke over the roman 700's: the lowercase ran
**0.46 (y) .. 1.15** before, with t f j p at 0.58-0.63 and y w z x at
0.46-0.69; it runs **0.60 (y) .. 1.19** after, with t f j p at 0.81-0.84 and
w z x v at 0.78-1.02. The three letters that still read light on this
instrument -- y (-35% of the diagonals), e (-23% of the rounds), z -- read
light in the ROMAN 700 by the same measure and for the same reason: most of
their centerline is a hairline (the y's tail, the e's eye, the z's diagonal),
and the ridge median reports what most of the centerline is, not what the
letter's thick is. The y's thick is 94.1 now, the stems' 97-101.

**Two slivers the weight opened, and how they were closed.** The v's and the
y's thick stroke turns ~130 degrees at its apex; at the 700's 83 units the
inner offset of that turn crosses itself and the union left a pocket 2-3
units wide on the hook's concave side (41 and 76 units of area) -- the glitch
gate's CRACK, visible as a white fleck at 2 px per unit. A 4-unit
morphological close (the C's and the barred letters' fix) took the v's and
left the y's at 8 x 7 units, and a close wide enough for that also fills the
fork's apex 13-23 units up from where the two strokes meet. `_solid` drops
interiors under 200 units^2 instead -- a real counter is thousands, these two
letters have none -- and moves no edge; gated above 84 like the rest.

**What was tried and did not help, or was checked and left.**

- The FIT table's b and p rows (0.550 weight, 0.725 width) looked like a
  cause of the p's light bowl; they are popped at import (`FIT.pop('b')`,
  line ~3052) and inert. The env dials `ALBO_ALD_LW_*` do work.
- The b d p heads (`bd_head`, 58 reach / 44 drop / 96 down the stem) are in
  absolute units and were left: the head's thickness at the stem is already
  the 700 stem's own width, and scaling it makes a 133-unit flag on a 97-unit
  stem.
- `PQ_FOOT_T` is scaled (the foot's thickness, 21 -> 29 at the tips, 67 -> 93
  at the stem); its two arms' reach is not.
- The ligatures fi fl ff ffi ffl come from the roman f's parts and were on
  the axis already -- none of the five is among the 58 glyphs that moved;
  "first office fluffy" is on the 40 px sheet.

**What is left, with the numbers.**

- **Five pairs under the touch gate's 0.012 em floor, none touching**: qy
  0.0009, qf 0.0049, qj 0.0049, f? 0.0111, qp 0.0114 (the gate exits 1). All
  five are terminals that now carry the bold's weight -- the y's, f's and j's
  tail drops and the f's hook ball -- against the q's foot and the ?'s hook.
  The ruled remedy is a kern pair (round 268's block in `kern.py`, "a descender
  clash is a kern pair, not a wider fitting band"), and `kern.py` was outside
  this round's fence. By that block's own rule (overlap + floor + 2-3 units,
  ADDED to what the pair carries), the values are **qy +14, qf +10, qj +10,
  qp +3, f-question +3**. Four of the five occur in no English word.
- **The Italic 400 has the mirror of this fault and is byte-locked.** At the
  400 the same ten letters sit at the Medium's weight over stems at 0.796 of
  it: t 67, f 74, v 79, c 69 against the n's 57 at 0.50 xh. `ALD_WF_UP` is
  1.0 there by design; evening the 400 means letting the factor go below 1,
  which re-cuts ten letters of the shipped face and wants its own ruling.
- The italic u's right stem (61 under the x-height at the 700) is untouched,
  awaiting the ruling recorded in section 14.

Proofs: `tools/wedge_serif/shape/weights269/` -- the 100 most common English
words and a paragraph, before and after, at 13 px x8, 17 px x6 and 40 px x2
nearest, the shipped Italic with the BoldItalic inline, and the five pairs'
collision zones -- and its `index.html`.

The page: https://claude.ai/artifact/1MKtph3thcXCwaAGNkiSeL

## STANDING RULING — at the 700 and the 900, counters have no indentations

Owner 2026-09-19, verbatim: *"for 700 and 900, counters should not have
indentations in their counters."* Stated as geometry in `primitives.ring` and
`ring_from`: above stem 84 a counter is its own convex hull, one Chaikin
pass to round the chord ends, the outer untouched. `cmp_counter_dents.py` is
the gate that measures it. The one designed exception is the ampersand's
lower loop, which carries the same concavity at the 400 (737 units², 9
deep) and is drawn that way; it stands at the 700 and the 900 until ruled
otherwise.

## 16. Round 270 — the counters at the heavy ends, and five kern top-ups

**What was there.** Every bowl's counter in this face is the outer shape
offset inward by the pen's width at each tangent. The width carries the
stress — thick at the sides, thin at top and bottom — and at the 400 the
swing is small enough that the counter stays a clean oval. At 116 and 148
the thick sides push in 7–18 units further than the thin top and bottom,
and the counter becomes an hourglass with a dent at 3 and at 9 o'clock.
Measured as ink inside the counter's own convex hull, thicker than 6 units:

| face | dents | glyphs | deepest | where |
|---|---|---|---|---|
| Regular 400 | 1 | 1 | 9.1 | the & (drawn so) |
| Italic 400 | 1 | 1 | 13.7 | the 9's tail join (drawn so) |
| Bold 700 | 9 | 5 | 12.5 | 8 g a @ & |
| Bold Italic 700 | 3 | 2 | 15.5 | & o |
| Black 900 | 17 | 8 | 18.2 | 8 g @ a o 6 & q |

`ovalise` (round 204, the g's cure) was the same finding fixed for one
letter; this is the ruling applied to every ring. After: one dent per face,
the ampersand's, at every weight. The glyphs that moved at the 700 and the
900, both styles: O Q a b d g o p q 0 6 8 9 % @ ¤ © ª ® and the ring accent
— 57 outlines in the roman 700, 55 in the 900, 60 in the bold italic (the
composites that reference a moved base count). At the wall's thickest the
letter is lighter by the dent's depth — 12 units of a 148 stem on the 900's
o — and nothing else moves.

**What did NOT catch it.** The glitch sweep looks for holes narrower than a
hairline and for cracks; a counter with a 12-unit dent is neither. A
narrow-notch measure (white narrower than 16 units) was tried first and
found only hairline slivers — the P's slot, the italic heads' brackets, the
M's crotch — none of which is what a reader sees. The convex-hull measure
is the one that found the thing on the page, and it is the tool that
ships.

**Five kern top-ups.** Round 269 put the bold italic's y, f, j and p on the
weight axis, so their tails and the f's hook came back down against the q's
foot: qy 0.0009 em, qf and qj 0.0049, qp 0.0114, f? 0.0111 — under the
floor, none touching. Added to what the pairs carry, in round 268's gated
block: qy +14, qf +10, qj +10, qp +3, f? +3. The bold italic's touch sweep
reads 0 touching, 0 under the floor.

**Byte identity.** Regular 400 and Italic 400: no counter moved (the gate is
the stem), and the Italic's GPOS is unchanged; the Regular differs from
round 269 only in the M and the ™ built from it (round 271). ExtraLight
200: the same two glyphs. The roman 700 and 900 keep their round-267 touch
counts (4/7/14 and 5/7/14).

Proofs: `tools/wedge_serif/shape/weights270/` — the dented letters before
and after at 0.40 px/unit for the roman 700, the roman 900 and the bold
italic, and runs at 13 and 40 px; the page
https://claude.ai/artifact/Fqs4aZzvSeu7ao7Do5fmQL

## 17. Round 271 — the M's right top from the left top's recipe

Owner 2026-09-19: *"M needs to have symmetrical stem tops, based on left
top"* and, on a "come to a point" ladder drawn the same hour and withdrawn
before it was shown, *"left was okay before, just need to match right to
left."* The left top is round 243's, untouched.

**Measured first**, row by row at one pixel per unit against the letter's
own extremes: the right serif projected 7 units further than the left at
the 400, 28 at the 700 and 46 at the 900, and only the left top carried the
17-unit peak over the cap line. Round 243 had rebuilt the right crown from
the left's recipe, but seated it on the thick stem's outer corner where the
left's sits 0.35 of the thin stroke's width inside its top — so the two
never matched, and the gap grew with weight.

**The recipe, on the right's own strokes.** The wedge projects past the
thick stem's outer edge by exactly what the left wedge projects past the
thin stroke's; the peak is the thin inner stroke's inner top corner, as the
left's is the thick inner stroke's; the fill and the trim are the same
shapes. Two things it took to get there, both recorded because each cost a
render: mirroring the left top's INK dragged a chunk of the thick inner
stroke onto the thin one (a shelf on the inside of the junction); and the
thick outer stem's inner top corner stood 30 units past the thin stroke's
edge on the inside at the 900 — both strokes' tops are centred on one point
— so the stem's ink left of the thin stroke's inner edge, above where the
two edges cross, is cut, with a half-plane rather than the stem's own face
as the boundary (a boundary on the face left a zero-area loop that the
build's ink spread inflated into a 2.4-unit sliver).

**What moved:** the M and the ™ built from it, in every roman weight, the
400 included — an owner instruction. The italic M is the aldine module's
own and is untouched. Glitch sweep on the M: 0 findings at 400, 700, 900.

Proofs: `tools/wedge_serif/shape/weights271/` — the M at 400/700/900 before
and after at 0.5 px/unit, and MIMICRY runs at 13 and 40 px; the page
https://claude.ai/artifact/PeDcULppdXAS9EnbHKaUvM

## 18. Round 272 — six instructions on the heavy ends, and the review's findings

Owner 2026-09-19, in order: *"'o' bold italic needs thinning to match other
letters"*; *"for roman 700 and 900, 'w' 'v' and possibly others are too heavy
compared to others. ampersand is way too wide"*; *"roman 700 and 900 'a' is
too thick especially lower right within counter"*; *"correct errors and
defects of M in the after (shards and glitches)"*; *"the inside of the
diagonal right stroke of M has a fracture"*; *"fix the overlap mismatch
glitches on the right of 'a'."* Every fix is gated above stem 84; the Regular
400 and the Italic 400 differ from round 271 only in the M and the ™ (the
peak-height change below), the ExtraLight 200 the same two.

**The bold italic o** (`aldine.py` `a_o`). Its pen is a fraction of S and
grew one for one with it; the bowls of a b d p q and the c's wall are
absolute Aldine widths on `max(1, S/84)` since round 269 and grow from the
Medium's 72, not the 400's — so below 84 the o is the lighter (66.9 against
72, which the owner has passed) and above it outgrows them: thickest 110 on
the ridge against a 101.6, b 99.3, d 102.4, c 103.9. Above 84 the pen is
measured on √(84 S): 99.3 now. The contrast arm is untouched.

**The M's shards and the fracture** (`caps_straight.py`). The shoulder cut's
line ran from the thin diagonal's corner to the axis's end at the vertex, a
line that converges into the stroke, so it shaved a wedge off the diagonal's
inside down to the box's floor and left a 4-unit step at C − 200 at every
weight — the fracture. It is the axis direction now. The left crown's trim
had its boundary exactly on the fill's top edge, which left a zero-width
strip the ink spread inflated to a 26 × 2.4 sliver on the cap line at the
700; both trims overshoot by a third of a unit. The right peak stood 5–10
units under the left's (the review): it is carried up the thin stroke's edge
to the left peak's height at every weight. Shards, slivers and holes: 0 at
200, 400, 700 and 900.

**The a** (`stems.py` `g_a`). The counter's lower right was the stem's
INSIDE FOOT: under the bottom stroke at the 400, its bracket climbs into the
counter with the weight — a chamfer from (191, 61) to the stem's edge at y
160 at the 900, the counter covering 35% of its own lower-right 60 × 60
against 67% at the 400 and 88% at its own lower left. Above 84 the stem
carries its right foot only: 93% at the 700, 98% at the 900. The hood's
profile (0.85–1.12 of the pen, a 125–165 unit hood at the 900) is scaled by
√(84/S) above 84, ramped in past the run. The right-edge glitches were the
hood leaving the stem 1.5 units narrower than the stem as drawn (the arc's
first tangent leans, the bowl profile hands it a smaller width, then the
widths are smoothed) plus the stem's own chamfered corner: the hood is now
built, its edge just above the stem's top read against the stem's edge just
below, and built again scaled by the miss; the run is trimmed to the stem's
footprint, the outer edge held at the stem's edge for 30 units, the corner
filled. Steps: 2–3 units → 0.2. Two things that did NOT work, recorded: a
flat thinning factor put a 10-unit step where the arc starts; cutting the
bowl's ink inside the stem's footprint did nothing, because the stem is drawn
after and fills it back.

**The diagonals** (`diagonals.py`, `caps_straight.py`, `ampersands.py`
`pw`). Round 51's rule makes a down-right diagonal the pen's broad, ~1.10 of
the stem at every weight. Above 84 the pen's width is capped at `DIAG_CAP` ×
S = 0.93 — where the n's stem itself measures at those weights. Ridge
maximum over the n's stroke, before → after: v 1.12 → 1.09 and 1.23 → 1.18,
w 1.17 → 1.09 and 1.22 → 1.17, x 1.11 → 1.05 and 1.18 → 1.11, y 1.09 → 1.02
and 1.19 → 1.14, A V W 1.12 → 1.05 and 1.17 → 1.11–1.14. What is left at the
900 is the VERTEX, where two strokes merge — the n reads 190 there against
its 135 stem by the same measure — and the w's color, 1.09 of the n's,
which is four strokes in a w's width. K, Y, Z do not go through `pw` and
did not move.

**The ampersand** (`ampersands.py`, `marks.py`). Its whole skeleton is drawn
in `CUR_W` = 8.76 stems, so it grew with the weight like a stroke: 629 units
of ink at the 400, 1,004 at the 700, 1,245 at the 900, against an H of 744
→ 780. Above 84 the skeleton's stem is 66.9 × (S/66.9)^0.17 and the strokes
lighten by √(84/S) with the foot wedge seated on the lightened stroke: 694
and 736 now (&/H 0.92, 0.94). With the narrower skeleton the loops' counters
dented 14 and 19 units where the diagonal crosses, so the ruling reaches the
ampersand above 84 too (`convex_holes`); the round-256 concavity stands at
the 400.

**The adversarial review of rounds 268–271** (read-only, 2026-09-19) and
what was done:

| finding | severity | done |
|---|---|---|
| bold italic ¢: round 269's thicker c swallowed the bar's daylight (counter 3,094 units² → none) | silent-wrong-output | the bar is centered on the c's counter above 84 (`_currency_bar(counter=True)`); the 400s' marginal placement is left for a ruling |
| ° a solid dot at the 900; Φ a solid disc; Ω a closed ring at 700 / 900 / bold italic; roman ¶ an enclosed slot with a dent; ß dented 21–34 | silent-wrong-output, outside every sweep | ° and Φ walls scale by min(1, 84/S); the Ω's cut is max(0.06 C, 0.55 S) above 84; the ¶'s feet under the slot are cut so it opens to the baseline; the ß's counters convex above 84 |
| the Black declared usWeightClass 400 with the REGULAR bit | latent | 900; the REGULAR bit only on the Regular; ExtraBold 800 added |
| the M's right peak 5–10 units under the left's | cosmetic | at the left's height now |
| §15's b and p walls read 91 / 90 after round 270's hull, not 96; §16's moved-list omits ° º ∞ β δ σ α Þ ø ð ‰ and the super/subscript figures; §14 omits ✔ at the 700s and the 900's `--all` ($, ¸ and the cedilla composites, « », ∞, ▫ △ ▽); the bold italic 6 keeps a 4.0-unit dent under the tool's threshold | docs | recorded here, as stated |
| `kern.py:33`'s "18 units is a sixteenth of a pixel" is 16× off (it is 0.97 px at 54 px/em) | docs, out of scope | recorded |

The review's clean list stands as written in its report: `convex_counter`'s
gate and its interaction with `oval`, round 269's factor sites and the
`_solid` interior filter, the kern block's values against the built GPOS,
the round-271 cuts at four weights, the round-268 P, the name table, and
every byte-identity claim re-made.

**Gates on the final builds.** Glitch: 0 at 700 / 900 / bold italic, the
ruled β alone at the 400s and the 200; every named glyph also clean under
`--all`. Touch: unchanged at every weight (bold italic 0 / 0). Dents
(`cmp_counter_dents.py`): 0 in all three heavy fonts — the ampersand
included now. Figure spread 1.42×. Byte identity: Italic 400 exact; Regular
400 and ExtraLight 200 differ in M and ™ only.

Proofs: `tools/wedge_serif/shape/weights272/` and the page
https://claude.ai/artifact/ViZgNhEz6ATEqUfAVUtPzu

## 19. Round 273 — the italic u's right stem, and the finials ladder

**The u.** Owner 2026-09-19: *"check that the right stem of 'u' is bit low
on any shipping font faces"*, and after the numbers, *"status on fix 'u'
right stem top being short."* Measured at one pixel per unit against the 429
x-height, every roman face tops both of the u's stems at 430; the Italic's
right stem topped at 400 and the Bold Italic's at 368 (`aldine.py` `a_u`).
The stem was `hm_stem(c, x1, 0, xh * 0.985)` with the helper's default top
cut — the face cut down for a HEAD to lie across, on the one stem in the
alphabet that gets none — so the cut's drop, which grows with the stem's
width, was the miss. The stem is now built to the x-height, its top read,
and built again raised by the miss: 431 in both italics, beside the ı's 430.
Moved: u, µ and the ten u composites in both italics; the Italic 400 moves
by the owner's word. GPOS unchanged; glitch and touch unchanged (0 / 0 on the
bold italic, 0 / 0 / 1 exempt on the italic). The Regular is byte-identical.

Proofs: `tools/wedge_serif/shape/weights273/` and the page
https://claude.ai/artifact/Dxqw8sbaoHEGUTbUtnsSdk

**The finials ladder, open.** Owner 2026-09-19: *"change out round finials
(like c top serif)."* The roman c's top is the exemplar — a swell to 1.10 of
the pen into a −28° face, which reads as a ball — and `ALBO_ROM_C_TOP` in
`rounds.py` `g_c` draws five ends, `a` being today's byte for byte: `b` the
pen cut with no swell, `c` the flared cut (the stroke widens 15% over its
last 12% into the family's cut, variant C's rule), `d` the pen cut with the
family's diagonal end wedge hanging into the aperture, `e` the capital C's
beak with its lip. Shown at 400 and 700 with a word:
https://claude.ai/artifact/HZfp3UosWv2BEBn4RqyoyC. Awaiting the pick; the
winner then goes to every round finial in the roman — f r j y s, the g's
ear, C G S J, the ?, the figures' ends — each measured before it ships.

## 20. Round 274 — the bold italic's junctions

Owner 2026-09-19, on a crop of the bold italic "u n ı u": *"fix glitches."*
Every junction of the arch letters at the 700 was measured, fixed at its
cause in `aldine.py`'s `hm_*` helpers, and re-measured; every change is
gated on `ALD_JUNCT = S > 84.0`, so the Italic 400 is byte-identical
(`diffglyphs`: `glyphs differing: 0 [] | GPOS pairs changed: 0`, against a
build of the same tree with the round-273 `aldine.py`). Two detectors,
now `tools/wedge_serif/cmp_junctions.py`: white SLIVERS and ink SHARDS
narrower than 6 units (the region minus its opening at 3, pieces of 10
units² and over), and STEPS (a jog of 1.5 units or more between two
turns of opposite sign whose neighbors run nearly parallel). Numbers are
design units unless marked; "before" is the round-273 build.

| junction | letters | cause | before | after |
|---|---|---|---|---|
| white wedge under the head | i l n m h r | the head flattens with the weight (its tip stays 0.157 xh under the top, its end drops with `HM_HEAD_W`): the underside runs at 12° at the 700 against 20° at the 400, and the stem's top face falls to the left at a fixed 24° — and not even 24°: `stroke` moves the cut corner 22 units, past the 11-unit resample spacing, and `_unfold` drops it, so the face ran at 18.4° from the point before. The underside stood ABOVE the face by 11.8 units at the stem's left edge, 4.6 at its center | 80–106 units² per letter (n m r i 80, h l 106 in the shipped outline) | 0; the face is cut by `hm_follow_cut` to run `HM_JUNCT_BURY` (5.5) under the head's underside at the left edge — 8.6°, buried 5.6 / 6.1 / 3.9 / 1.3 / 0 across the stem; at the 400 the same underside sits 5.9–8.1 BELOW the 24° face, so the 400 has no wedge |
| stem corner proud of the head's end face | i l n m h r | `hm_top_right_y` crossed the face at the NOMINAL edge `xc + sw/2` while the stem's top is `ent_waist` wider (100.1 against 96.7), and the head's end sat at a fixed 0.45 sw, which puts the face's lower corner 1.5 short of the edge at the 700 (1.4 PAST it at the 400) | a 2.4-unit step at the corner (1.9 on the m's capped head) | 0: `hm_head_geom` solves the head's end so the face's lower corner lands on the stem's actual top edge, with the face normal `stroke` itself will use (the last resampled segment, not the chord — the chord left the two corners one font unit apart in the shipped h and l, a 13-unit hairline, found by the detector on the first build) |
| stem corner proud of the arch's outer edge | n h m | the right stem topped at 0.86 xh with a square face; the arch's centerline ended at 0.78 xh heading 12° right of vertical with a 96.7 landing under a 100.1 stem | a ledge of 11.6 (n h), 14.5 (m) — the notch in the crop | 0: the arch lands LEVEL — its end face is cut square to the baseline (`cut1 = -θ`, θ read off the resampled centerline), its landing width is the stem's top width × cos θ so the level face IS the stem's top, and the stem is drawn up to that face (`hm_arch_end`); the outer edge leaves the stem's edge with a 12° bend. The crown, the climb and the width profile are untouched |
| the arch's fold under the crown | n h m | `stroke` offsets the two sides and `_unfold` drops points that step backwards; the inner side folds through the crest while the width ramps, and a fold whose chord still runs forward survives, the chord cutting across the true edge — a 27-unit needle of white, [−52..−19 × 360..374] of the landing stem, which the stem's square top at 0.86 xh used to hide (the m showed 4 units² of it above that top) | hidden (n h), 3.9 units² (m) | 0: `hm_sweep` draws the arch as the union of its swept quads, which differs from `stroke` by exactly that needle (59 units²) and nothing else — the crest's vertices are identical |
| the exit at the foot | i l n m h u, the a | the exit's underside passed the stem's foot corner at +0.8 (i), +0.2 (h), −0.4 (u), −1.3 (m), −2.8 (l), −4.7 (n): the shorter the exit (`k`), the flatter its run off the knee and the higher its underside at the corner, so the corner poked through or grazed it | steps of 4.4 / 3.0 (h), 4.0 (m) in the shipped outline; the i's corner 0.8 through | `hm_exit` reads its underside at the foot corner and rebuilds with the turn lowered by the shortfall: −5.4 to −6.1 under the corner on every letter, the tip unmoved; the lowest point of the hook now −7.4 (n) to −10.4 (l) against the design's intended −9 (it had been −3.8 to −6.8) |
| the u's left stem | u | drawn with the round-233 45° cut (`cut0`), which round 234's follow cut never reached: the corner stood at 459 | 30 units over the x-line, 28 over its own head — the spike in the crop | the top is clipped to the follow face (the path and its width table are not moved, see below): ink top 432, the head's own |
| the m's middle foot | m | the round cap was sw/2 wide under a stroke whose start is `ent_waist` wider | 1.8-unit steps each side of the rim | 0: the cap takes the stroke's start width |
| the ı | ı | not this module's: the italic's dotless i fell through to `accents.py`'s roman stem (a wedge head, a two-sided foot, sheared, the italic entry and exit laid over them) | at the 700 a forked head with three spurs, steps of 3.0 / 3.0 / 1.8 | at the 700 it is the i without its dot (`a_dotlessi`, fitted with the i's bearings); its eight composites follow |

Gates on the BoldItalic, verbatim: `cmp_aldine_glitch.py --ttf` → `122
glyphs swept, 0 with findings`; `cmp_touch.py` → `0 pair(s) TOUCHING, 0
below the 0.012 em floor`; `cmp_figure_space.py --body` → `even: p90/p10 is
1.41x, within the 2.50x allowed`; `cmp_counter_dents.py` → `0 dent(s) in 0
glyph(s)`; `cmp_junctions.py` → `white slivers < 6: 0, ink shards < 6: 0,
steps >= 1.5: 5` (before: `6, 0, 15`). The five steps left are named below.
Glyphs that moved in the BoldItalic: 39 — a h i l m n r u ı and their
composites (ª µ æ ħ ĳ ł ŋ ⁿ ì í î ï ĩ ī ĭ į ù ú û ü ũ ū ŭ ů ű ų ĥ ĺ ļ ľ);
0 GPOS pairs.

**What was tried and did not work.** (1) Starting the u's one-path stroke
lower, at the follow face, instead of clipping it: the path's widths are
keyed on the fraction of its length, so a top 30 units lower shifted every
width along the turn and the rise, and the rise came out 7–9 units heavier
at 0.25 xh — the u's crotch grew a 24-unit² sliver. (2) Lowering the
landing stem to the arch's end without touching the arch: it exposed the
crest fold above (10–14 units² per letter). (3) Deriving the head's face
normal from the chord `end − mid` rather than the resampled spline's last
segment: the head's corner and the stem's corner rounded to font units one
apart, a 13-unit hairline on the h and the l in the shipped outline. (4) A
vertical arrival for the arch (a knot at 1.0 P above the end) was priced
and not taken: to be vertical and stem-wide by 0.86 xh the width ramp has
to be compressed into the descent and the crest gains 7–14 units of weight;
the level end face costs the crown nothing.

**Left as constructed, for a ruling.** The outstroke's underside leaves the
stem's flat foot in a concave corner on every one of these letters at both
weights — the stem is square-footed and the exit rounds the baseline, so
the two meet at 26–34° — and lowering the hook steepened it on the short
exits: the detector reads it as a step of 6.0 (l) and 7.0 (a) now, 2.0 on
the i and the ı, where before it read 4.4 / 3.0 on the h and 4.0 on the m
and nothing on the l and the a (the 400 reads 3–6 on i h l m n u a). Making
it disappear means rounding the foot into the exit, which is a change to
the letter and not a repair. The m's capped head meets the stem's right
edge in the crotch under its round (4.7 in the shipped outline, 2.8 in
design; 1.9 before) — that is the round of M_HEAD_CAP hanging past the
stem, as ruled in round 143.

**The Italic 400's own numbers, unchanged and recorded** (`cmp_junctions.py`
on the shipped Italic): the head's end face pokes 1.4 units past the stem's
edge (steps of 1.9 and 1.7 at the corner on n i r h l); the arch's landing
ledge is 9.7 (n h) and 8.7 (m); the exit seams read 3–6 on i h l m n u a;
the u's left stem tops at 438 against its head's 431 (9 over the x-line,
the same 45° cut); the m's capped head 6.8; the ı is the roman stem in the
italic, with 2.0-unit steps at its head and foot, and it is not the i
without its dot — at the 400 the i and the ı are two constructions, and so
are í ì î ï ĩ ī ĭ against the i. Fixing any of these moves a shipped glyph
and is the owner's call; the mechanism is the same as the 700's and the
gate is one comparison.

Proofs: `tools/wedge_serif/shape/weights274/` — before above after at 3
px/unit for u n ı m h l r i a, and the runs at 13 px ×8 and 40 px ×2.

## STANDING RULING — the wedge serif above the 400 is the 400's

Owner 2026-09-19: *"reduce the amount of flare serif on bold. I would like
the serif to be optically similar to the 400 serif"*, and on a ladder of four
sizes (as drawn; the 400's absolute; square-root growth; the 400's × 1.15):
*"b wins."* `pen.WL / WD / DROP` are taken at stem 66.9 above 84 — 52.3,
104.6, 17.2 — in both styles; at and under 84 they follow the stem as they
always did. Confirmed for the 900 on its own ladder the same day (*"a wins"*, the
400's wedge against 1.15 / 1.30 / 1.49 / 1.75); the 200 takes 0.75 of the
400's (round 279).

## 21. Round 277 — the bold serifs

The wedge's three numbers were fractions of S, so the 700's wedge was 91 ×
181 and the 900's 116 × 232 against the 400's 52 × 105 — 1.73× and 2.2× in
every dimension, which is the flare the owner saw. One line in `pen.py`
(`_SWEDGE = S if S <= 84 else 66.9`) puts the 400's wedge on every weight
above it. Moved: 212 glyphs in each of the Bold and the Black and 125 in the
Bold Italic — every wedge-bearing glyph. Regular 400 and Italic 400
byte-identical; ExtraLight 200 untouched (differs from round 275 in the cent
alone, round 276's ruling).

**One pair.** The fitter measures the ink in the band, and with the smaller
wedges it drew the V and the I closer at the 700: 0.0108 em under the floor →
−0.0026, touching. `kern.py`'s roman block gives the pair back 8 above stem
84 (−108 → −100): 0.0054 at the 700, 0.0111 at the 900, under the floor and
not touching, as before.

**Gates.** Glitch 0 at 700 / 900 / bold italic, the ruled β at the 400s and
the 200; touch 4 / 6 / 14 at the 700 and 5 / 6 / 14 at the 900 (the round-275
baselines), 0 / 0 on the bold italic; dents 0 in all three heavy fonts;
figure spread 1.42×; `cmp_junctions.py` on the bold italic 0 slivers, 0
shards, 5 steps (round 274's own number).

Proofs: `tools/wedge_serif/shape/weights277/` and the page
https://claude.ai/artifact/Aepy8FgRGaKoTmACyW2YQq

## 22. Round 279 — the 200's wedge

Owner 2026-09-19, on a ladder of five sizes for the ExtraLight's wedge
(stem-scaled 0.66 of the 400's; 0.75; the square root of the stem ratio,
0.81; 0.90; the 400's own): *"b wins."* The 200's wedge is 0.75 of the
400's — 39.2 long, 78.4 deep, drop 12.9 — instead of 34 × 68. `pen.py`'s
rule is now three-valued: below the 400's stem 0.75 × 66.9, at the 400 the
stem's own, above 84 the 400's (round 277). Moved: 179 glyphs in the 200,
every wedge-bearing one; the Regular 400 byte-identical. Gates at the 200
unchanged: the ruled β alone, touch 2 / 17 / 14.

Proofs: `tools/wedge_serif/shape/weights279/`.

## 23. Round 278 — the Italic 400's junctions

Owner ruling 2026-09-19 (recorded in `tools/wedge_serif/README.md`): round
274's junction rebuild — the head on the stem, the arch's landing, the exit
at the foot, the u's left stem top, the dotless i as the i without its dot —
applies to the ITALIC 400 as well as the 700. This round takes the gate
off. "Before" is a build of HEAD (`30929b6`) with the gate in place; every
number is the 400's, design units unsheared from the design-space probe
unless marked "font" (the built outline, sheared and spread, read by
`cmp_junctions.py`).

**What was gated.** `ALD_JUNCT = pen.S > 84.0` in `aldine.py`, read at
eleven sites: `hm_stem`'s follow cut (`if ALD_JUNCT and headed`),
`hm_head`'s solved end (`hm_head_geom` against a fixed end at
`HM_HEAD_R_FOLLOW × sw`), `hm_exit`'s bury loop, `hm_arch`'s level landing
(`hm_sweep` against `stroke`), the landing stems' top in the n, the h and
twice in the m (`hm_arch_end(c)` against `xh * 0.86`), the m's middle-foot
cap width, the u's left-stem clip, and `a_dotlessi`'s fallback to the roman
stem — plus a twelfth at the foot of the module, `if ON and pen.S > 84.0:
BEARINGS['ı'] = BEARINGS['i']`. All twelve are gone, with the flag and the
arms only it selected. One arm that looked dead is not and stays: the
round-234 face in `hm_stem` is what the u's right stem (`headed=False`)
draws at both weights, so `hm_head_face` and `hm_top_right_y` remain.
Nothing else was ungated — round 269's `ALD_WF_UP`, round 272's o
(`_So`), round 268's P gap and the finials' floors were each read and left
as they are.

| junction | letters | before (400) | after (400) |
|---|---|---|---|
| the stem's top face under the head | i l n m h r | no wedge at this weight: the head's underside runs at 20.6° and sits 5.6 / 5.9 / 6.2 / 6.9 / 8.0 units under the stem's face across it (left → right), the face at 22.6° — at the 400 the 24° cut's corner moves 12.8 units, past the resample spacing, and `_unfold` keeps it here where it dropped it at the 700 | `hm_follow_cut` cuts the face to 17.4°, buried 3.5 / 2.3 / 1.1 / 0.3 / 0 under the head's underside; `HM_JUNCT_BURY` is 3.2 at this weight (4.0 × 66.9 / 84), so the numbers are smaller than the 700's 5.6 / 6.1 / 3.9 / 1.3 / 0 by construction |
| stem corner against the head's end face | i l n m h r | the face's lower corner 1.4 past the stem's edge: two steps at the corner, 1.9 and 1.7 (font), on n i r h l; the m's 6.8 (its capped head) | 0: the corner is solved onto the stem's actual top edge (57.7 wide against a nominal 55.8), the stem's corner 396.5 = the face's 396.5 |
| stem corner proud of the arch's outer edge | n h m | ledge 9.7 (n h), 8.7 (m) (font); 9.5 / 12.2 in design | 0: level landing at `hm_arch_end` (0.780 xh), the face's corners the stem's |
| the arch's fold under the crown | n h m | hidden under the stem's square top at 0.86 xh | 0 (`hm_sweep`) |
| exit underside at the foot corner (− is under) | i h u m l n a | −0.8 / −1.3 / −1.7 / −1.9 / −4.4 / −5.8 / −3.2 | −4.2 / −4.6 / −3.2 / −5.0 / −4.4 / −5.8 / −3.2: only the four short of the bury moved (i h u m); the l and the n already passed the corner by more and the a by exactly 3.2, the bury itself, so the loop's 0.05 tolerance left all three alone — **the a does not move at the 400**, which is why it is missing from the glyph list below. The hook's lowest point: i −4.3 → −8.0, h −5.1 → −8.0, m −5.6 → −8.0, u −4.1 → −5.5 (font: −6 / −6 / −7 → −9 on i h m) |
| the u's left stem | u | tops at 438 (font), 9 over the x-line, 7 over its own head — the 45° cut's corner; a 2.7 step where the head's face meets it | clipped to the follow face: 431, the head's own top; 0 steps |
| the m's middle foot | m | cap sw / 2 wide under a start `ent_waist` wider | the cap takes the stroke's start width |
| the ı | ı | the roman stem sheared, with the italic entry and exit over it: steps 2.0 at its head and 2.0 at its foot (font), advance 283 | the i without its dot: 0 steps, advance 218 = the i's, and ì í î ï ĩ ī ĭ take it |

`cmp_junctions.py` on the 400: before `white slivers < 6: 0, ink shards <
6: 0, steps >= 1.5: 24`; after `0, 0, 5`. The five left are the ones round
274 left at the 700 (§20, "left as constructed"): the outstroke's underside
leaving the square foot in a concave corner — u 6.0 (4.0 before: the lowered
hook steepened it, as predicted for the short exits), a 5.0, n 3.0, l 3.0
(the last three unmoved) — and the m's capped head hanging past its stem,
7.8 (6.8 before; it grew by 1.0 because the head's end is now solved 1.4
units further left, onto the stem's edge, and round 143's round hangs the
further past it).

**Gates, verbatim.** `cmp_aldine_glitch.py --ttf` → `122 glyphs swept, 1
with findings` (β, the ruled crack, as before); `cmp_figure_space.py --body`
→ `even: p90/p10 is 1.37x, within the 2.50x allowed` (1.36 before);
`cmp_touch.py` → `0 pair(s) TOUCHING, 1 below the 0.012 em floor, 1 exempt`
(before: `0, 0, 1`). **The one pair under the floor is `f?` at 0.0119 em
(0.0134 before), and it is an instrument reading, not a spacing change:**
neither the f nor the ? moved (0 outline, advance or GPOS difference), the
pair's white measured from the OUTLINES with its kern (−18) is 11.44 units =
0.0114 em in both builds — under the floor in outline space before and
after, the raster read it a pixel high before — and the f's own raster at
the tool's 699 px em differs by 558 of 45,008 pixels between the two fonts
though its outline is byte-identical: FreeType's autohinter takes its blue
zones from letters this round moved, and every glyph's raster shifts by up
to a pixel with them (4f, qf, O1, UW, RR moved one pixel the same way, in
both directions). Not kerned — a kern on an unmoved pair for an
instrument's pixel is a change beyond the ruling; it is left here for a
ruling (one line in `kern.py`'s italic block, +18, would read 0.0134 in
outline space). `cmp_aldine_metrics.py` before → after: i w/h 0.322 →
0.320 (the hook), u w/h 0.770 → 0.782 (the left stem's top off the spike),
a / e / o counter-to-ink ±0.002 (raster; those letters did not move — the
a's +21% OFF is pre-existing and unchanged); no letter crossed its 10%
tolerance.

**Moved.** 35 glyph records differ, 0 GPOS pairs: h i l m n r u ı µ ħ ĳ ł ŋ
ⁿ and 21 accented composites whose placement or advance follows them (ì í î
ï ĩ ī ĭ ù ú û ü ĥ ĺ ļ ľ ũ ū ŭ ů ű ų); eight more (į ñ ń ņ ň ŕ ŗ ř) are
components referencing a moved base with an unchanged record and move with
it on the page — 43 glyphs in all, against the 39 recorded for the 700 (the
a, ª, æ and į are the difference: the a did not move here, and the 700's
count was `diffglyphs`' records too). Advances: the ı and ì í î ï ĩ ī ĭ 283
→ 218 (the i's, `BEARINGS['ı'] = BEARINGS['i']`), ħ 435 → 428, ľ 378 → 375
(their marks are placed off the base's ink, which moved at the head).
BoldItalic and Regular: byte-identical to builds of HEAD (`glyphs
differing: 0 [] | GPOS pairs changed: 0`, each) — the gate selected nothing
above 84 and nothing in the roman, so removing it changed a gate and only a
gate.

Proofs: `tools/wedge_serif/shape/weights278/` — before above after at 3
px/unit for u n ı m h l r i a (the same rows and bands as round 274's), and
the runs at 13 px ×8 and 40 px ×2.

## 24. Round 281 — the Q's tail under the marks (laddered, ruling pending)

Round 280's kern was withdrawn the same day (owner: *"lose the Q punctuation
kerning. you misunderstood the need entirely"*); asked what the need is, he
chose *"Tail under the marks"* — the , ; . sit on the baseline right after
the bowl and the tail sweeps BELOW them, nothing spaced apart. Measured on
the built fonts the tail already passes under them at every weight; what
fails is the CLEARANCE, because the comma descends with the weight (−81 /
−139 / −176) and the tail thickens: 136 units of white between the comma's
lowest point and the tail's upper edge at the 400, 59 at the 700, 10 at the
900 — so at 13 px on the reader (77 units to a pixel) the 700 and the 900
merge the comma into the tail. `caps_straight.q_tail_deep` scales the tail's
control points in y about the baseline until a least clearance `Q_CLEAR` is
met, above stem 84 only; the dial `ALBO_ROM_Q_CLEAR` (0 = as drawn, the
default until ruled) built the ladder: a 77 (1 px), b 115 (1.5 px), c 154
(2 px). The Black's tail bottom goes −294 → −366 / −407 / −449 against a
−300 descender line. **Ruled the same day: "for Q, leave as is" — the tail
stays as drawn at every weight; the dial ships 0 and the item is closed.** The touch sweep's "Q, −0.41 em" was never an ink
collision: the comma sits in the concave between the bowl and the tail's
upturned end and the row-wise measure reads the tail's tip to its right as
overlap (the `cmp_space_2d` case). The 400 is byte-identical with the code
in.

Proofs: `tools/wedge_serif/shape/weights281/`.

## 25. Round 282 — the s's finial: parity with the c

Owner 2026-09-19: *"for round finial, c is fine but there needs to be parity
with s in small scale rendering. right now it is too light and low on
vertical grid."* Round 275 had left the roman s alone: its ends were the
20-degree pen cut with a 1.25 flare, and the head runs down a steep diagonal
where the pen is thin, so its face was 21 units tall against the c's 42 and
sat one pixel row under the c's at 13 px. `stems.g_s` now puts the family's
finial on both ends (held to `rounds.c_top_width()`, the c's own 60.8 at
the 400), raises the head's start 0.80 → 0.82 xh so its face tops out at
397 where the c's does, and reaches further per weight (`_s_head_x`, 1.00 /
1.04 / 1.10 / 1.12 at the 200 / 400 / 700 / 900) because the finial's face
is trimmed back by its own throw and a fixed start lost 27 units of the
letter's width at the 400 and 25 at the 900; the built s is as wide as it
was. The italic s already had the finial (round 276) but its head sat 34
under the c's: `S_HEAD_Y` 0.86 → 0.94 at the 400 (437 against the c's 441)
and 0.89 at the 700 (458 = the c's), on the stem between. Every weight,
both styles; the shipped 400s move (the owner's ask). Gates at baseline in
all six fonts: only s ś ŝ ş š ș moved, no kern pair changed, glitch and
touch counts as before, 0 dents.

Proofs: `tools/wedge_serif/shape/weights282/`.

## 26. Round 283 — the s's terminals settled, and the 900 deburred

Three owner rulings on round 282's page, applied in one pass. *".93/.82
wins"* on the ladder of head starts: the head's reach stays at the drawn
0.93 (round 282's per-weight stretch to 1.04–1.12 is gone), so the built s
is 10% narrower (advance 399 → 361 at the 400) and the head tucks over the
bowl. *"the bottom needs to be optically equal to the top and the top is
too heavy"*, then *"for all s, make the top equally or less visually heavy
than the bottom"*: the foot keeps the c's finial (the 1.10 swell held to the
c's end width) and the head's end is `S_HEAD_END` = 0.85 of the foot's,
tapering into its face where the foot swells into its — the head's blunt
near-vertical face on a stroke that stays thick all the way in was the
heavier terminal to the eye whatever the ink area said (the foot had 3–15%
more); the foot's start is the head's mirrored about the two apexes (0.11 of
the width, from 0.06). The italic s reads the same dial (56 / 66 at the 400,
77 / 91 at the 700). *"deburr the 900 s"* (there is no italic 900; the Black's
s carried the burrs): a nub stood into each aperture. It is not a fold — the
spine's tightest bend clears the half-width by 8 units — and not a sliver (a
morphological opening of radius 10 removed 18 square units); the pen's own
width climbs 54 → 136 across that bend, where the direction crosses the thin
axis, and the inner offset of a width rising that fast on a bend that tight
bulges. Above stem 84 the pen widths are box-averaged over ±0.6 stem of
path before the finials go on (`stems._smooth_widths`; ±0.35 leaves the
nubs, ±0.6 clears both). Gates at baseline in all six fonts.

Proofs: `tools/wedge_serif/shape/weights283/`.

## 27. Round 284 — the s spaced, and its foot slightly the bigger end

Owner 2026-09-19: *"all s need work, mostly spacing work but also the bottom
needs to be slightly bigger than the top."*

SPACING. Round 283 brought the head back to its drawn reach and the letter
narrowed 38 units at the 400; the bearing rows were round 97's solve against
a wider drawing, so `cmp_space_2d` read the roman s at 0.072 em on its right
and 0.090 on its left against the lowercase median of 0.106 — the tightest
letter in the alphabet on both flanks, with `st` at 0.062 and `so` at 0.069.
`build.BEARING_ADJ['s']` goes (1, −15) → (17, 19), which puts both sides on
the median (0.103 / 0.111). The italic's left goes −2 → 10 in
`aldine.BEARINGS` (its foot's forward corner has hung 30 units under the
previous letter since round 276): the tight three lift (`is` 0.074 → 0.084,
`as` 0.086 → 0.095) and the two loosest stay under 0.13.

THE TERMINALS. Round 283's flat `S_HEAD_END` 0.85 left the foot half again
the head's end ink at the 400 and 55% more at the 900. Measured, the two
ends are unequal at EQUAL end widths and not by a constant — the foot's ink
runs 3% more at the 200, 8% at the 400, 13% at the 700, 16% at the 900,
because the pen is wider where the foot leaves the bowl and the 28-degree
face crosses each stroke at its own angle. So the head's size is SOLVED
(`stems.s_head_end`, bisect, ceiling 1.00) for a foot/head end ink of
`S_FOOT_RATIO` = 1.12: it lands 0.959 / 0.983 at the 200 and 400 and takes
nothing at the 700 and 900, where the pen alone already does it. The italic
solves the same way. Gates at baseline in all six fonts; only the s and its
five composites moved, no kern pair changed.

Proofs: `tools/wedge_serif/shape/weights284/`.

## 28. Rounds 285 and 286 — the s's flow, and its two spaces

Owner 2026-09-19: *"give me more options with an improved flow and smaller
top."* Read off the drawing, the two bowls were the SAME width (lower over
upper 0.994) where a humanist s carries the lower wider, and that equality
is what made the letter read stiff. Five options went out
(`stems.S_OPTS`, `ALBO_ROM_S_OPT`, a = the drawing as it stood, byte-identical):
b draws the upper bowl in toward the letter's axis (`S_UP` 0.88) and trims
the top terminal (`S_FOOT_RATIO` 1.30); c, d and e go further on both, e also
moving the mid points.

**Ruled: b, with an amendment.** *"b wins, but the space on the top loop
needs to be reduced and the bottom space needs to increase"*, then on the
ladder of waist heights *"plus .01 wins."* `S_WAIST` rides the waist 0.01 of
the x-height higher, which shrinks the top space and grows the bottom in one
move — measured on the convex hull minus the ink, top over bottom 0.994
(before 285) → 0.951 (b) → 0.896 (shipped). Round 284's spacing holds with
no bearing change (0.100 / 0.108 em against the lowercase median of 0.108).

One thing that could NOT be had: the spine carries a second inflection at a
thirtieth of its length, at the head. Every head placement that removed it
stood the terminal's face up past the arch as a notch, so it stays, and the
flow gain is the bowl balance rather than the inflection count.

The ITALIC's spine is untouched: it already carried the proportion the
amendment asks for (top over bottom 0.739 at the 400, 0.765 at the 700).
What did change there is its top terminal — it had been reading the roman
option's `ratio` field, so picking a roman option silently re-cut the italic;
`S_FOOT_RATIO_IT` states it (1.30) instead.

Proofs: `tools/wedge_serif/shape/weights286/`.

## 29. Round 288 — the redrawn letters re-spaced

Owner 2026-09-19: *"fix the spacing around the recently redone characters."*

WHICH CHARACTERS, read off the fonts rather than off memory: diffed against
the pre-268 build, the roman 400 moved J M a f r s y 3 5 cent (plus
composites) and the italic 400 moved J c f h i j k l m n r s u v w x y 2 3
dotlessi. Each was then measured on its own two flanks with
`cmp_space_2d.py` — closest approach in TWO dimensions, by class and side,
the only one of this project's four spacing measures that can see an open
shape — against the lowercase median of 0.108 em (roman) and 0.098
(italic).

WHAT WAS OFF AND BY HOW MUCH. The roman f's right flank read 0.093 and the
r's 0.094, the two tightest right sides in the alphabet: both ends were
re-cut in round 275's finials, which shortened the f's hook and the r's arm,
and the band rule priced the shorter reach as spacing. In the italic, rounds
274/276/278 moved where the ink STANDS without moving the table that says
where it sits: the f's right had fallen to 0.068, the x's to 0.082, the w's
to 0.086 and 0.088, the v's left to 0.085, while the c's right had opened to
0.123, the y's to 0.116. Deltas in units — roman f +16, r +15; italic c −27,
f +45 (in two passes; its hook reaches so far right that the band rule
prices almost none of it), i +10, m +9, v +14, w +11/+13, x +17, y −19.
Every one now reads within 0.005 em of its median.

THE ff LIGATURE HAD TO FOLLOW THE f. `uniFB00` is the one f-ligature that
ENDS in an f, so its right side is the f's; it is fitted independently and
did not pick the +16 up. `cmp_touch`'s pair white is
`getlength(ab) − getlength(b)`, which puts the ligature's advance against
the plain f's, so it read ff as newly touching at every roman weight while
the ligature's drawing had not moved a unit. The +16 on the ligature is the
real fix rather than the tool's.

WHAT WAS TRIED AND PUT BACK: the italic j at −16 on its left. Its left was
only 0.015 loose, and tightening it closed Rj, 4j and qj onto the touch
sweep — a bad trade for a mild looseness.

Gates: fT stops touching at the 200 and the 400 (the f's hook had been on
the T's arm); the 200's sub-floor count falls 17 → 3 and the 400's 5 → 4;
the Italic 400's one sub-floor pair clears to 0. Nothing new touches at any
weight, glitch counts and counter dents are at their baselines, the figure
spread is 1.37×, and no kern pair changed in any of the six fonts.

NOT IN SCOPE, measured and deliberately left: letters the recent rounds
never touched that still read off the median — the roman k, j, b, w, z, q
and x, and the italic d, p, g, t and z. Re-fitting those is its own round.

Proofs: `tools/wedge_serif/shape/weights288/`.

## 30. Round 287 — the Black e's wave, its crack, and its bar

Owner 2026-09-19, on a magnified Black `e`: *"subagent to address to wobble
wave and bumps of 900 e"*, then *"that e could be heavier."* Two separate
faults and one weight change. Everything here is gated on `pen.S > 84.0`
(`rounds.E_HEAVY_S`, between the Regular's 66.9 stem and the Bold's 116), so
the ExtraLight, the Regular, the Italic and the Bold Italic are byte-identical
— 0 glyphs and 0 GPOS pairs against round 288 in all four.

THE INSTRUMENT FIRST, because the one this project already has cannot see
either fault. `albo_bumps.py` returned nothing on the roman `e` at the 900,
before or after — 202 circles on the sheet either way, none of them on this
letter. That is correct behavior, not a miss: after its 2026-09-18
recalibration it looks for NOTCHES and SPURS, features of the ink at the pen's
scale, and it was deliberately moved off exactly the edge-waviness detectors
that the owner had called a complete miss. A wave in an edge is not a notch.
So two measures were written for this round (`efinal.py`, in the round's
scratch): the deepest REVERSAL on the outer contour (a turn over 150 degrees,
with its depth from the chord of its neighbors) and the lower counter's
FLOOR read left to right as y(x), counted by turning points. A floor that is
one curve falls to the bowl's low point and rises to the tip: one turning
point. Every extra one is a wave.

THE WAVE. The tail's inner edge — the counter floor the reader sees against
the white — is one cubic from the bowl's inner edge out to the tip (round
245). Its second control point is pulled back from the tip along the tip's own
direction by 0.55 of the chord, which leaves it at a nearly FIXED HEIGHT:
measured 18.9, 20.3 and 20.5 units at the 400, 700 and 900, because the tip
sits at 0.19 of the x-height at every weight and only the chord grows. The
point the curve STARTS from, though, climbs with the pen: 19.3, 41.6, 56.0. At
the 400 the two are level and the floor is one curve. At the 900 the control
sits 35 units BELOW the start and the cubic sags between them — the floor rose
2.5 units, fell 5.6 and rose again, six turning points against the 400's one,
and at its lowest it dug 1.5 units under the bowl's own counter floor. The
handle is now SHORTENED until the floor is monotone (`_monotone_handle`), and
only shortened, never turned: C2 stays on the ray back from the tip, so the
terminal's angle — E_TIPDEG_R, a ruling of round 110 — is untouched whatever
the clamp does. At the 900 it takes the handle from 101.1 units to 73.1, a
28% trim, and at the 400 it is a no-op even ungated, which is the second
reason to believe the diagnosis.

THE CRACK — the "bumps" half, and an older fault. Round 245 gave the roman
tail its INNER edge as the drawn curve, starting at the ring's own inner point
on the ray. The RING went on being cut by `_normal_cut`: a face through the
ray's point on the OUTER contour, along the normal of the OUTER cubic that an
inner-edge tail no longer draws. Two different lines, so the two pieces do not
meet. Measured at the bottom of the bowl, the tail's outer edge starts 3.0
units to the right of the ring's cut face at the 400 and 9.6 at the 900, and
the union leaves the difference as a crack — a reversal of 174 to 177 degrees
whose depth runs 0.5 units at the 400, 8.8 at the 700 and 21.7 at the 900. It
is the needle standing up out of the letter's underside in the owner's render.
`_inner_cut` takes the face from the TAIL instead: through the tail's own
start point, along the normal of its inner edge there, out to the outer
contour. `edge_stroke(..., side=-1)` offsets by exactly that normal, so the
tail's outer edge at t=0 lands on the returned Po and the two pieces share an
edge. w0 feeds the taper, the taper moves the tip, and the tip moves the
edge's start tangent, so it is iterated to a fixed point; three passes settle
it under a hundredth of a unit.

MEASURED, on the built fonts:

| cut | crack before | crack after | floor turns before | after |
|---|---|---|---|---|
| ExtraLight 200 | none | none | 1 | 1 |
| Regular 400 | none | none | 1 | 1 |
| Bold 700 | 9.0 u, 174° | **none** | 2 | **1** |
| Black 900 | 22.0 u, 175° | **none** | 2 | **1** |

On the 900's own turn-angle ledger the change is starker still. Before, three
of the five sharpest features on the whole outer contour were the crack: 175°
at (297,8) on a 22-unit segment, with 89° and 94° mouth corners either side of
it. After, all three are gone and the sharpest things left are the tail's tip
(91°, 90°), the bar's two ends (86°, 81°) — every one of them a designed
corner.

THE WEIGHT, measured before it was moved. Against its own CONSTRUCTION family
at the 900 — the rounds, o c a b d g p q s, and NOT the case group, which
flags the alphabet rather than the drawing — the `e`'s color is 0.418 against
the family's median 0.457, −8.5%, and on `cmp_weight_survey.py`'s chamfer-ridge
stroke median it is 72.3 against 103.5, −30%, the LIGHTEST of the family. Only
the `c` is lighter on color, and the `c` is legitimately lighter for being an
open letter. So heavier is a CORRECTION, not a departure. (For the record, the
case-grouped survey reads the `e` at −48% of the lowercase median; that is the
grouping CLAUDE.md warns about, and it is not the number this round acted on.)

THE BAR IS THE LEVER, and the other two were ruled out rather than passed
over. The BOWL cannot take it: the e's ring is `ring()`'s pipeline at the e's
radius, so its pen is the o's pen at the same tangent by construction, and
widening it here would make the `e` the one round whose pen is its own. The
TAIL cannot take it either — it is the bottom-right stroke the owner has twice
asked to make LIGHTER (round 94, then 2026-09-14), and `E_ARM_THIN` 0.92 IS
that instruction; thickening it would quietly reverse a standing ruling. The
bar is 20% of the letter's ink. `E_BAR_HEAVY` = 1.22 multiplies `E_TH` above
the gate. Its top is a ruling of round 39, so it grows downward only: the eye
is untouched and the lower counter pays.

| measure | 400 | 700 before | 700 after | 900 before | 900 after |
|---|---|---|---|---|---|
| bar (units) | 25.9 | 43.2 | **49.5** | 54.4 | **62.4** |
| bar / stem | 0.387 | 0.372 | **0.427** | 0.368 | **0.422** |
| eye height | 160.7 | 138.0 | 138.0 | 123.4 | 123.4 |
| lower counter | 205.9 | 166.1 | 159.8 | 140.1 | 132.1 |
| ink area | 58797 | 93757 | 95781 | 113985 | 116563 |

1.22 is the largest rung that keeps the lower counter clearly larger than the
eye (132.1 against 123.4 at the 900) while lifting the bar above the Regular's
share of the stem — which is the direction a Black should move, since the
bar/stem ratio was FALLING with weight (0.387, 0.372, 0.368) where a heavier
cut should carry proportionally more horizontal. 1.35 makes the two counters
equal and 1.50 inverts them; the ladder is on the proof page so another rung
can be chosen without a rebuild.

WHAT WAS DELIBERATELY NOT DONE. The face's contrast is weight-invariant by
design — TH_H / S is 0.566 at the 400, the 700 and the 900 alike — and
changing that is an architectural call for the owner, not a number to tune in
one letter. So only the `e`'s own bar moves.

A LEFTOVER, measured and left. The new join rounds to two coincident integer
points at the 900: the contour runs 301,−14 → 304,−14 → 305,−13 → 305,−13 →
312,−12, an exact duplicate vertex plus a 1.4-unit segment. It draws no ink
(1.4 units against a 674 cap is 0.2%, well under a pixel at any reading size)
and the glyph already carried one such duplicate at the tail's tip in every
weight, this round included. It is NOT cleaned, because a general
duplicate-vertex pass at export would move the shipped 400s, which this round
may not do. It is recorded here so the next session does not re-diagnose it —
and note that it is what makes a naive circle-fit residual read WORSE after
the fix (14.55 against 3.57 at the 900): a circle fitted across a cluster of
sub-unit segments returns garbage. The turn-on-a-real-segment measure above is
the honest one.

## 31. Rounds 289 and 290 — the Black e's bottom stroke, and why it had to move

Owner 2026-09-19, after round 287: *"the 900 e lowest stroke does not have a
bumpfree simple curve to it."* Round 287 had stopped the floor SAGGING by
shortening its outgoing handle until the cubic's y no longer turned back.
Monotone it was; simple it was not, and no choice of handles could have made
it so.

THE MECHANISM IS THE TWO ENDS, NOT THE CURVE. The floor leaves the bowl on
the counter's own tangent and must arrive at the terminal on E_TIPDEG_R's 50
degrees (round 110). Between those fixed ends the room to rise collapses as
the stroke thickens, because the bowl's counter climbs — 8.6, 19.3, 41.6,
56.0 at the 200, 400, 700 and 900 — while the terminal sat at 0.19 of the
x-height at every weight. The chord from handover to tip flattens from 28.5
degrees to 13.2; against a departure tangent of about 13 degrees that leaves
headroom of +14.7, +13.0, +5.0 and −0.8. At the Black it is NEGATIVE: the
floor must leave the bowl rising and still arrive below where its own tangent
would carry it, so it dips and recovers. That is the corner he was pointing
at, and it was decided before any curve was drawn.

RULED, on a sheet of four cuts: *"d is closest but still not graceful
curve"*, then on a second sheet *"d2 wins"*. The terminal now RIDES UP WITH
THE WEIGHT (`_e_tipy`): 0.19 at and below the 400, ramping to
`E_TIPY_HEAVY` = 0.28 at the 900, which restores +10.2 degrees of headroom
there and +10.8 at the 700 against the 400's +13.0. The floor itself is one
circular arc (`_arc_handles`) with its outgoing handle eased 1.6× so the
curvature peaks mid-run and relaxes into the terminal, which is the shape the
400 has; the curvature profile goes from climbing-to-the-tip to a single hump
at both heavy weights.

A BUG OF MINE, recorded because it cost a round: `_match_kappa_handle`
returned the LONGEST first handle when the bowl's curvature was out of
reach, where it should return the shortest — curvature at the start goes as
1/h², so the long handle flattened the floor's first half into a straight and
then bent it at the tip. That is what made the first cut of d read stiff, and
the owner caught it by eye before the measurement did.

TRIED AND RULED OUT, with numbers: moving the departure point later around
the bowl (headroom −48.8 degrees at 300 degrees, −73 at 310, because the
counter is climbing steeply there); pulling the terminal inward rather than
upward (+0.3 degrees, nothing); and the tangent-INTERSECTION construction for
the floor, whose triangle is near-degenerate here — the end tangents meet 4.4
units in front of the tip at the 900 and 25.3 units behind it at the 700 — so
it built a curve at one weight and refused at the other.

Moved: the e and its composites at the 700 and the 900 only. The 200, both
400s and both italics are byte-identical; glitch, touch and dent counts are
at their baselines and no kern pair changed.

Proofs: `tools/wedge_serif/shape/weights290/`.

## 32. Round 291 — the hairs and the fractures: a closing, and a union

Owner 2026-09-19, on large renders of common words: *"bold italic 700 has
errors and glitches and fractures and hairs"*, and then of the 400, *"italic
has some hairs and stray lines."* Two distinct faults were under those four
words, and NEITHER was visible to any gate this project had. `cmp_aldine_glitch
--all` on the BoldItalic reported 23 findings and every one of them was a
symbol or a punctuation mark; the letters came back clean and the `s` and the
`g` were not clean. That gate sweeps a RASTER for islands, cracks and splits.
Both of this round's faults live in the CONTOUR's own point stream, one layer
above it, and nothing was reading that.

### The first fault: a morphological closing tripled the point count

`geom.close_corners` (round 205b) fills the concave corner a union leaves by
dilating by `r` and eroding by `r`. Exactly two glyphs in the face call it —
the `a_s` at `S_BLEND` 18 units and the `_g_roman` the italic `g` is drawn
from at `G_R_BLEND` 10 — and those are exactly the two glyphs that were
broken.

Shapely's round buffer lays a fan of `quad_segs` points per quadrant against
EVERY vertex of its input, and the input here is already a dense polyline at
this project's `SPACING` of 11 units. Instrumented at the call, the `s` went
in at 117 points and came out at 338, the `g` in at 322 and out at 841 —
while the SHAPE moved by 0.19% and 0.07% of its area. So the closing was
doing essentially nothing to the drawing and everything to the point stream.
Measured on the built fonts, before:

| glyph | points | segments under 2 units | duplicate points |
|---|---|---|---|
| bold italic `s` | 286 | 170 (59%) | 52 |
| bold italic `g` | 605 | 291 (48%) | 236 |
| italic 400 `s` | 273 | 149 (55%) | 45 |
| italic 400 `g` | 599 | 292 (49%) | 234 |

The same measure on the face's own `c e n o` reads 0 to 6%. That is the
scale of it: two thirds of those two letters' contours were degenerate.

IT COSTS TWICE, and the second cost is the one that was not obvious. The
exporter rounds every point to the integer em grid, so a run of 0.3-unit
segments rounds into coincident points and one-unit stair-steps — the
faceting and the fractures the owner could see. AND `geom.fit_curves` finds a
contour's corners by the turn between consecutive segments, which on a
0.3-unit segment carrying a hundredth of a unit of buffer noise is noise:
every vertex read as a corner, no run was ever long or gentle enough to fit,
and these two letters would have exported as raw polygons even with
`ALBO_CURVES` on.

THE FIX is Douglas-Peucker at `geom.CLOSE_TOL`, a tenth of a unit, applied to
the closing's own output. DP rather than a resample because **it cannot cut a
corner** — the recursion always keeps the point of greatest deviation, so a
wedge tip and a finial cut survive exactly while a fan of near-collinear
points collapses — and the tolerance is the whole guarantee: every point of
the result lies within 0.10 units of the closed outline, a ten-thousandth of
the em, a thousandth of a pixel at 13 px. After: the `s` 131 points with 13
under two units, the `g` 354 with 14, and not one duplicate point left in
either letter in either style. `ALBO_CLOSE_TOL=0` is the old dense polygon,
byte for byte.

### The second fault: the union leaves a hairline of white at a shallow join

`geom.ink` ADDS strokes, it does not blend them — the principle `cmp_joints.py`
has carried since round 179. Where two strokes meet at a shallow angle the
boolean's boundary runs out along one stroke's edge and straight back along
the other's, leaving a tapering hairline of WHITE driven into solid ink. The
italic `x`'s upper join carries one 18 units long closing to 1.0 units; the
`y`'s tail join one 18 long and 4.7 wide. Both render in FreeType exactly as
they measure, at any size large enough to resolve them. At 13 px they are a
quarter of a pixel of gray, which is why sixteen rounds of reading-size
proofs never caught one and why the owner found them on large renders.

`geom.weld_slivers` splices across such an excursion, and fires only when ALL
SIX hold: the excursion is one or two vertices long; its ends close to within
`WELD_WIDTH` 8 units; the path removed is at least `WELD_MIN_LEN` 12 units;
the area recovered is under `WELD_MAX_AREA` 120 square units; the first and
last segments are antiparallel to within 40 degrees (`WELD_TURN` 140); and
the splice ADDS ink.

Two of those six are there because the pass failed without them, and both
failures are worth recording. **Without the antiparallel test it shaved serif
tips** — the `l`'s foot and its ascender top both qualify on width, length
and area, because a wedge tip between two 11-unit facets is narrow and long
too. **Without the add-ink test it shaved terminals**: a ring's area changes
by minus the signed area of the spliced run, so the sign of that area is
exactly "fill" against "shave", and with shaving allowed the pass took eight
units off the italic `6`'s entry terminal (−0.222% of the glyph) and nicked
the `9`'s tail (−0.113%). Every weld that survives the test ADDS between
0.005% and 0.2% of its glyph's ink.

**The designed hairline gap is safe, and the VERTEX COUNT is the reason
rather than any width.** The Y's and the P's gap (`docs/albo-hairline-gap.md`)
is about eight units wide — the same order as these cracks — but it is held
within a unit of that width over 0.04 to 0.10 of the cap, 27 to 67 units,
which at 11-unit sampling is three to six vertices down each flank. A crack
is one or two, and a two-vertex splice cannot reach a parallel-sided gap.

### The roman DID move, and the defect is provably in it

The brief for this round said the roman weights should not move at all. They
moved, because the same fault is in them and this is said explicitly rather
than quietly: the Regular's `e` at (261, −13) and its `y` at (296, 14) each
carry an EXACT 180-degree reversal, and the ExtraLight's `m` three. Twelve
welds land in the Regular, three in the Bold, three in the Black, and each
one adds between 0.01% and 0.09% of its glyph's ink. No kern pair changed in
any of the six fonts.

### What is NOT fixed, and the measurement that decided it

The `y`'s crack is still there. Its ends close to 8.52 units against the
pass's 8, and reaching it needs a width of 12 — at which the pass stops
repairing and starts blunting. That was not reasoned, it was rendered: a
before-and-after sheet of all 26 sites a width of 12 would newly touch shows
the wedge tips cut off the `a h m n u y A K M N Q V W 4 6 9`. Raising the
antiparallel threshold to 152 degrees cut the new sites to 14 and still
blunted the `u`, the `M`, the `4` and the `9`. The true repair for these is
to re-aim the two strokes where they meet, per letter, which is what
`cmp_joints.py` said in round 179: *the fault is in the direction the edges
arrive at, not in how fat they are.* That is a drawing decision and it is
left for a ruling.

### The e is not faulted, and this is the number

The bold italic `e` was reported as having an angular left edge to its eye and
a terminal that ends on a step. Both are there and neither is a defect.
`ALBO_CURVES` has been 0 since round 231 (build.py:371, a deliberate ruling),
so **every contour in this face is a polygon at 11-unit facets** — zero
off-curve points in any lowercase letter of either style, checked — and the
integer em grid then leaves one-unit jogs wherever a shallow edge crosses it.
The `e` carries four such jogs and zero reversals. Eleven units is 0.14 px at
13 px and 0.44 px at 40; one unit is 0.013 px and 0.04 px. The `e` is
byte-identical before and after this round. The same reading applies to the
one-unit "spurs" on `i m n r u`: they are the grid, they are on every letter
in the face, and the weld's 12-unit minimum path deliberately leaves them.

### The gate

`tools/wedge_serif/cmp_contour_hairs.py` is new. It reads the contour's own
point stream and fails on a REVERSAL past 165 degrees, on a HAIR (a reversal
past 150 whose shorter arm is under 8 units), and on DEGENERATE DENSITY (more
than a quarter of a glyph's segments under two units). `--letters` sweeps only
the Latin letters, which is the arm now nearly green; the full sweep still
carries symbol and mark findings, the same territory `cmp_aldine_glitch`
reports.

Coincident points are collapsed BEFORE any angle is taken, and that is
load-bearing. A zero-length segment has no direction, so a spike sitting
beside a duplicate point reads as 90 degrees, or as nothing, or as a division
by zero, depending on which way the arithmetic falls — and all three readings
are wrong. This is also the correction to a number that reached this round in
the brief: an earlier detector reported 9 reversals in the italic `s` and 69
in its `g`. There are none. Those counts were its own duplicate points being
measured as directions, which is exactly the trap the collapse exists for.
The duplicates are counted in their own column instead, where they turned out
to be the strongest single symptom of the closing bug — 236 of the `g`'s 841
points.

| font | letters with findings, before | after | all 306 glyphs, before | after |
|---|---|---|---|---|
| bold italic 700 | 14 | **3** | 45 | 22 |
| italic 400 | 19 | **12** | 67 | 50 |
| extralight 200 | 13 | **9** | 59 | 50 |
| regular 400 | 8 | **5** | 44 | 32 |
| bold 700 | 3 | **1** | 24 | 15 |
| black 900 | 4 | 4 | 36 | 27 |

Proof page: `tools/wedge_serif/shape/weights291/`.

## 33. Round 292 — the italic g thinned to its family

Owner 2026-09-20: *"italic 400 g needs to be thinned out."* Measured on the
built Italic 400 with `cmp_weight_survey.py`, he is describing the heaviest
letter in the italic lowercase: the g's color reads 0.307 against the
family's 0.275 median, its stroke 63.2 against 58.7 (+8%), and its thick 82.0,
beaten only by the v's 81.3. So this is a correction rather than a departure.

`G_WALL` scales the width table of BOTH rings in `_g_roman` — the arm that
actually ships, `G_STYLE` defaulting to roman; the cursive arm is dead code
kept as the record, and an early cut of this dial went into it and moved
nothing, which is worth knowing before editing this letter. The shapes, the
centers and round 205's crown anchor are untouched; only the walls move.

Laddered at 1.00 / 0.94 / 0.90 / 0.86 / 0.82 and RULED on the render:
*"e wins"* — 0.82. That is the rung which lands the g on the family's COLOR
median (0.272 against 0.275) rather than its stroke median, which 0.90 would
have given. The two are different rungs because the g's color runs high for
its stroke: two bowls and a neck are packed into one x-height, so it carries
more ink per unit of area than a single-bowl letter at the same wall.

Moved: the g and its four composites in both italics. Every roman weight is
byte-identical; glitch and touch counts unchanged; the contour-hair gate
reports exactly the same pre-existing findings before and after (b, p, W),
so the thinning introduced none.

Also in this commit, two dials added and left INERT pending rulings: the
f-ligatures' internal fit (`ALBO_FI_PUSH`, `ALBO_FL_PUSH`, `ALBO_FF_STEP` in
`ligatures.py`, laddered for the owner) and the k's inner spacing at the
heavy weights (`ALBO_ALD_K_SPREAD`, default 0). Neither changes a glyph.

Proofs: `tools/wedge_serif/shape/weights292/`.

## 34. Round 293 — the BoldItalic k, the white under its kick

Owner 2026-09-20: *"BoldItalic 700 k needs spacing inside"*, then, when the
first cut opened the wrong white, *"spacing under kick do not split up two
branches."* The second message is the ruling: the air goes UNDER THE KICK and
the arm and the leg stay where they are.

WHICH WHITE, and the measurement. The wedge between the stem's own foot
outstroke and the descending leg reads 8,415 square units at the BoldItalic
against the Italic 400's 14,396, with a widest inscribed disc of 55.5 against
83.5, and its apex sits 35 units lower — it is squeezed shut from ABOVE by a
foot that reaches as far as it ever did while the leg beside it thickens with
the weight. The k is not in `HM_EXIT_BY`, so it takes the longest outstroke
in the alphabet, the n's.

`K_FOOT` shortens the k's OWN foot (a new `head_w`/`foot_len` pair on `st`
carries it), above stem 84 only, touching neither branch. Laddered at
0.80 / 0.56 / 0.44 / 0.32 of the stem and RULED at *"d"* — 0.32, which brings
the widest disc to 81.5 against the 400's 83.5. The wedge's total area stays
smaller at 10,317 because the leg beside it is genuinely thicker; the disc is
the measure that tracks what the eye reads as air, and the area is not.

TRIED AND DROPPED on his ruling: `K_SPREAD`, which pushed the arm's start up
and the leg's down to open the pocket where the two branches leave the stem.
It works (that pocket goes 30,592 → 34,099 at 0.12) and it is the wrong
white. The dial is left in the file at 0, with his words beside it.

Moved: the k and its two composites in the BoldItalic alone. Every other
weight byte-identical; glitch, touch and dent counts unchanged.

Proofs: `tools/wedge_serif/shape/weights293/`.

## 35. Round 294 — the BoldItalic k's mid serif

Owner 2026-09-20: *"thicken top serif and whatever else balances letter"*,
then the correction that decides the round — *"not top serif, the mid
serif."* On this letter the mid serif is the ARM's terminal, the finial at
x-height on the right.

MEASURED against the c's top end, which is the family's reference finial and
the very shape round 276 built this one from: the k's arm reads 30.1 units
thick at the Italic 400 against the c's 30.9 — a match — and 26.4 against
38.8 at the BoldItalic. A third thinner, and thinner in ABSOLUTE units than
the 400's, so it got lighter as the letter got heavier. The cause is that the
arm's width table is declared in design units that do not follow the pen,
while the c's finial floor does.

`K_ARM_END` multiplies the arm's final width above stem 84 (and half as much
at the 0.70 key before it, so the taper does not step). Laddered at
1.00 / 1.25 / 1.50 / 1.75 and RULED at *"b"* — 1.25.

JUDGED ON THE RENDER, and that is a method note worth keeping: thickening
this end also LENGTHENS the arm, because the family's finial swells before
its face, so the reach runs 502 to 519 units across the ladder. Every attempt
to measure the terminal in isolation was confounded by the face's angle
moving with the tip — a fixed x-slab at the tip reported the terminal getting
THINNER as it was thickened, and an ink-in-a-disc measure put the c's own
terminal lighter at the Bold than at the Regular, which is impossible. The
numbers above are the honest ones; the choice was the eye's.

NOT RULED, and left off: `K_HEAD_W`, the k's head weight, built on the first
reading of "top serif". The measurement behind it stands — the k's head is
the lightest of the bold italic's ascenders, 11,208 units of ink against
b 12,546, d 12,628, h 12,731, l 12,738 — and thickening an angled head also
raises its top, on a letter already standing 17 units above h and l, so any
future cut has to pair the two. Nobody has asked for it.

Moved: the k and its one composite in the BoldItalic alone. Every other
weight byte-identical; glitch, touch and contour-hair findings identical
before and after.

Proofs: `tools/wedge_serif/shape/weights294/`.

## 36. Round 295 — the spikes the integer grid leaves

Owner 2026-09-20, asked whether the new contour-hair gate should carry an
exemption table or be driven to green: *"Chase them to zero first."* This
round is the part of that which can be had for nothing, and an honest account
of why the rest cannot.

THE GRID MAKES MOST OF THEM. `build` writes each contour by ROUNDING a dense
polyline to the em grid, and rounding points that are a fraction of a unit
apart lands two on the same integer, or lands one a unit to the wrong side of
its neighbors. That is a spike with 1-unit arms in a letter whose drawing is
clean, and 33 findings across the six fonts had exactly that shape, very
often an exact 180 degrees. `geom.despike` removes them at export, where they
are made: duplicates first, then any vertex past 150 degrees whose shorter arm
is under 6 units AND whose two neighbors lie within 2.5 units of each other
— which is what "the contour doubled back" means. Cost, measured: the worst
glyph in any of the six moves 0.02% of its area.

WHAT COULD NOT BE HAD, with the numbers. A second rule was tried for the
SHALLOW spurs that remain — a vertex sitting within a small distance of the
chord between its neighbors, which is what the italic q's 3.6-unit spur on a
373-unit edge is. Three cuts of it all failed the same way:

- Bounding the INK a removal moves eats real corners at light weights. An
  ExtraLight arrow's tip is a corner holding only a few square units, and
  `arrowboth` lost 4.1% of itself. A corner is thin, not small.
- Bounding the DEVIATION and iterating drifts. Each removal is within 1.8
  units of its own local chord, but the chords move with it, so a long edge
  walks a little further every pass; the arrows GAINED 4.1%, their concave
  notches flattened.
- One non-adjacent sweep at a fixed tolerance still cost `arrowright` 2.9%.

So the shallow rule ships OFF (`ALBO_DESPIKE_DEV` 0) with its code and these
measurements beside it. The remaining findings — 24 letters across the six
fonts, down from 33 — are in the DRAWING, where two strokes meet at a shallow
angle, and want per-letter work rather than a global simplifier. Chasing them
with one is how 73 glyphs get damaged to help seven.

Moved: 45 / 10 / 5 / 8 / 48 / 12 glyphs by at most 0.02% of their area, in
the ExtraLight, Regular, Bold, Black, Italic and BoldItalic. No kern pair
changed; glitch, touch and dent counts unmoved.

## 37. Round 296 — the 24 were three sites, and the six that are left are one

Owner's ruling of the day before stands: *"Chase them to zero first."* Round
295 took the gate from 33 letter findings to 24 by removing the spikes the
integer grid leaves, and handed the rest over as drawing faults wanting
per-letter work. **They were not 24 faults. They were three shared sites
around ONE call**, and they are six now. Regular 400 and Black 900 are GREEN.

| font | before | after |
|---|---|---|
| ExtraLight 200 | 6 | 1 |
| Regular 400 | 3 | **0** |
| Bold 700 | 1 | 1 |
| Black 900 | 3 | **0** |
| Italic 400 | 9 | 3 |
| BoldItalic 700 | 2 | 1 |
| **total** | **24** | **6** |

### The one call

`build.draw` finishes every glyph with `g.buffer(1.2, join_style=2)` — the
record's ink spread, kept because those 1.2 units were part of the shipped
weight. **An offsetter cannot say anything true about a feature finer than the
distance it is offsetting by**, and three different things go wrong there.

**Its INPUT carried degenerate edges.** `primitives.wedge` ends its outline
`inner + fil[1:] + [B, A]`, and `fil` already ends at B — so every wedge in
the face repeats its apex, and a union of two parts that share a corner
exactly repeats that corner as well. A zero-length edge has no direction, so
the offset normal at it is arbitrary. Measured on the ExtraLight v's top-left
serif: the raw union is one straight face from the stroke's corner, and after
the spread it came back with a 2.8-unit HORIZONTAL spur standing off it. That
site is `v y w W M` and the `r`'s terminal — six of the 24.

**Its OUTPUT carries them at a shallow concave corner**, where the two offset
edges are near-antiparallel and their intersection is a pair of vertices a
fraction of a unit apart rather than one. The M's left apex is the same shape
from a different cause: round 272 cut the crown's trim with a lip dilated by
0.34 units, to stop a zero-width strip the spread would inflate, and the
dilation ends where the strokes' ink above the line ends — a 0.75-unit step on
the apex edge at every roman weight.

`geom.collapse_micro` cleans both sides of the spread: a vertex within
**one unit** of the last vertex KEPT before it is dropped. One unit is the
whole argument for the number — it is the grid the exporter rounds to, so
nothing the pass can reach survives into the font anyway, and it is under the
1.2 units the very next operation offsets by. **The rule moves no point**: a
vertex is kept exactly where it is or removed, and a removed vertex lies
within a unit of a retained one, so no excursion larger than a one-unit disk
can be taken out. That is the property round 295's shallow-spur pass could not
have — it compared each vertex to a chord that MOVED as its neighbors were
removed, which is how an iterated sweep drifted and flattened the ExtraLight
arrows' concave notches. Here the comparison is always against a retained
point and there is nothing to drift along. Measured on the letters round 295
could not help: `arrowboth` moves **0.511%** of its area and `arrowright`
**0.181%**, against the 4.1%, 4.1% and 2.9% the three rejected rules cost
them.

### The third site: the vertices that lie ON the line they are in the middle of

Where two diagonals meet — the `w`'s and the `W`'s inner vertex, the `m`'s
arch against its stem, the `r`'s shoulder — the union's boundary arrives along
one straight run and leaves along another, and the spread's offset lands its
intersection a few units short of the nearest vertex on each run. The corner
is then a real 150-degree crotch with a 3-unit arm on it, which is exactly the
signature `cmp_contour_hairs` calls a HAIR: *"a drawn corner has two long arms,
a spike has one arm a unit or two long."* Here both are true at once, because
the vertex NEXT to the crotch is redundant. Measured on the Black `w`'s
crotch, that neighbor stands **0.0006 units** off the chord through it.

`geom.drop_collinear` removes it, at a fiftieth of a unit — two
hundred-thousandths of the em, and a quarter of the 0.076 units of sagitta an
11-unit chord already carries across a 200-unit bowl. No sampled curve is
reachable: at the Regular the roman `o` and `0` keep all 230 and 231 of their
points, the `s` loses 3 of 180 and the `8` one of 300. The straight-sided
letters are another matter, and that is the finding nobody was looking for —
**the face was exporting its straight edges as staircases.** The ExtraLight em
dash is two straight lines and it shipped as 148 points stepping 207, 208,
208, 208, 209; it is 4 points now. The Regular `M` goes 466 → 59, the `W`
470 → 48, the `v` 164 → 31, the `z` 108 → 31.

| font | total points | after |
|---|---|---|
| ExtraLight | 58,024 | 38,831 (−33.1%) |
| Regular | 56,747 | 38,935 (−31.4%) |
| Bold | 54,384 | 38,426 (−29.3%) |
| Black | 52,439 | 37,860 (−27.8%) |
| Italic | 57,792 | 41,557 (−28.1%) |
| BoldItalic | 53,665 | 40,362 (−24.8%) |

### Three negative results, each of which cost a build

**Douglas-Peucker is the wrong sweep for this, by its anchors.** DP carries
the right bound — every dropped point is measured against the chord that
replaces it, so a run cannot bow away from the line a little at a time — but
it picks the point FARTHEST from a chord as a split and keeps it whatever it
is, and at a crotch the vertex beside the corner is exactly that point.
Measured on the Black `w`: DP at this tolerance merged the run on one side of
the crotch into 265 units and kept a 2.0-unit stub on the other. The shipped
pass is a forward sweep that re-checks every held point against the new chord,
which has DP's bound and none of its anchors.

**A tolerance loose enough to be a simplifier creates findings.** DP at a
fiftieth of a unit applied globally cleared five and CREATED five, in letters
that had none — the ExtraLight `h`, the italic `r`, four of the BoldItalic —
because at that point it starts keeping a SUBSET rather than the same line,
and a three-point wobble that was two 8-degree turns becomes one 16-degree
turn somewhere else. A local rule instead — walk out from each sharp corner,
drop the neighbor within a hundredth of its own chord — was built and
measured and is worse still, **20 findings**, because the crotch it is aimed
at turns 149.9 degrees and sits under any threshold that does not also admit
half the letter.

**Neither pass may run inside `draw()`.** `fit_aldine` reads its bearings off
the vertices whose ROUNDED y falls in the x-height band, and `solve_widths`
re-solves each capital's and figure's multiplier off `geom.bbox(draw(...))`
until its ink width hits a target. Dropping a vertex that happens to sit on
the band's edge moves a bearing by whatever that vertex was holding: with the
collinear pass inside `draw()`, the ExtraLight `four` came out **349 wide
against 444** and the `seven` 470 against 402, which put 35 more pairs on
`cmp_touch`'s TOUCHING list and took `cmp_figure_space`'s roman spread to
2.57x, over its 2.50x. It runs at export now, after `fit`, beside round 295's
despike; the fitter sees every vertex it always saw and only the written
outline is decimated. `collapse_micro` is the exception and stays in `draw()`,
because it is what the spread itself needs on both sides — and it moves at
most two units of advance on at most twelve glyphs in any font.

### The six that stay, and the measurement that says they cannot be drawn out

All six are one thing: a CONCAVE CROTCH where a bowl or an arch springs from a
stem. **A crotch of included angle θ advances its own vertex `1.2 / sin(θ/2)`
units up the bisector under the ink spread, and that comes off both arms.**

| glyph | raw crotch | included | raw arms | spread eats | an 8-unit arm needs |
|---|---|---|---|---|---|
| ExtraLight `m` | 160.5° | 19.5° | 8.15 / 10.71 | 7.09 | 15.1 |
| Bold `m` | 142.2° | 37.8° | 11.73 / 5.89 | 3.71 | 11.7 |
| Italic `q` | 162.0° | 18.0° | 7.19 / 10.82 | 7.68 | 15.7 |
| Italic `b` | 158.9° | 21.1° | 4.60 / 12.08 | 6.54 | 14.5 |
| Italic `p` | 166.7° | 13.3° | 9.78 / 1.60 | 10.38 | 18.4 |
| BoldItalic `p` | 154.9° | 25.1° | 11.11 / 9.09 | 5.51 | 13.5 |

The last column is the one that settles it. **Five of the six would need a
last facet longer than `geom.SPACING`, the project's own 11-unit sampling**,
before the spread could leave an 8-unit arm — so the arm the gate wants does
not exist in the drawing to begin with, and no amount of vertex hygiene can
produce it. Resampling every crotch arm to a full 11 units was priced and
would not clear ONE of the six: the Bold `m` would go 5.89 → 11 and leave a
7.29-unit stub, the BoldItalic `p` 9.09 → 11 and leave 5.49. Nor is it the
mitre limit — `join_style=2` at limits 5, 20 and 100 gives byte-identical
geometry at the ExtraLight `m`'s crotch, so GEOS is not beveling anything; the
short arms are the true offset.

Rendered before and after, these six are the same drawing (figure 6 on the
page). **They are recommended as EXEMPTIONS**, and there are two ways to zero
that are both the owner's to rule on: open those crotches, which is a shape
change in the `m` and in the italic `b p q` and which nobody has asked for; or
have `cmp_contour_hairs` measure the arms on the contour BEFORE the ink
spread, where they are 4.6 to 12.1 units and nothing has been eaten.

### What moved

No letter in any of the six fonts moves more than **0.80%** of its area
(ExtraLight `z`, which is all straight lines and whose staircases collapsed),
and only sixteen letters across all six move more than 0.3%: ExtraLight
`z` +0.80, `A` +0.69, `W` +0.66, `M` +0.60, `v` −0.46, `Y` +0.35, `x` −0.32,
`F` +0.31, `Z` +0.31; Regular `V` +0.41, `M` −0.40, `z` +0.31; Bold `x` +0.31;
Black `A` +0.32, `V` +0.31; Italic `l` +0.39; BoldItalic none. Every one is a straight-sided letter and the
direction is the staircase being replaced by the line it was sampling.

The largest move in the whole build is on the MARKS, and it is the same effect
at a smaller scale: the ExtraLight `acute` −2.25%, `asciicircum` −2.08%, the
dashes +1.4 to +1.5%. A thin mark's long edge was a stair snapping to whole
units at each sample; as one segment it rounds once, which is worth up to half
a unit of thickness either way. That is a coin flip per edge and it is
recorded rather than defended, because it is the price of the em dash not
being 148 points.

### What the adversarial pass found, and what it cost

Three real findings, all fixed before this shipped, and they are the reason
the two functions look the way they do rather than the obvious way.

**`collapse_micro` could delete a whole RING, and the guard it had could not
see it.** The rule chains — each dropped vertex is within a unit of the last
KEPT one — so a ring every one of whose vertices is within a unit of the last
collapses entirely, however long it is: a 100-unit sliver of 17.5 units² area
qualifies. The caller then dropped the polygon or the hole, which is a
perfectly VALID result, so the `res.is_valid` fallback never fired and its
comment described a failure mode that was not the reachable one. It fires on
the real corpus: three holes, in the `a`, the feminine ordinal and the `æ`,
each 0.08 × 0.33 units and 0.02 of area — which `contours(min_area=40)` drops
anyway, so nothing had changed. `clean()` now returns the ring untouched
rather than short. Latent and ungated is not the same as absent.

**The forward sweep's bound was `tol` everywhere except at the ring's seam,
where it was 2·`tol`.** `pts[0]` is wherever the ring happened to start and is
kept by construction, so it is tested last — but the points already dropped on
either side of it were measured against chords that ENDED or BEGAN at it, and
popping it moves their chord without re-checking them. Measured on the yen
sign at the Regular: **0.0289 units off the final chord against a tol of
0.02.** Cosmetic at three hundred-thousandths of the em, and the docstring's
claim was still false. The seam's two runs are re-checked now; the bound is
`tol` on every vertex of every ring.

**One doc claim did not reproduce and one was wrong.** The advance figure is
above. *"The roman o s 0 8 keep every point they had"* was corrected to the
measured 230→230, 231→231, 180→177 and 300→299 before the review landed, and
the review found the mechanism behind the two that do move: `cut.blend` puts
points onto their chords, and a chord is exactly what this pass removes. On
the shipped build `FJORD_CUT=0` so the blend is a no-op and the effect is
three points in the `s`; it is worth knowing that a build WITH the cut would
see much more of it.

**One thing to re-run, not a fault:** `outlines/cmp/variety.py` — the
detwinning sweep — compares serifs for byte-identical twins, and every outline
in the face has moved. Its "129 of 144" figure
(`docs/albo-variety-audit-2026-09-13.md`) is stale until it is re-run. And a
pre-existing note it surfaced, not new this round: `hmtx`'s `lsb` is computed
from `conts` while the exported `xMin` comes from the decimated-then-rounded
points, so a decimation can move `xMin` inward by up to `tol` before rounding.
Round 295's `despike` already had this and it is bounded by a unit.

### What was checked and found CLEAN, this round

`cmp_aldine_glitch --all` 18 / 19 / 23 / 25 / 20 / 23 findings, **identical**
to the baseline in all six. `cmp_touch` 1 / 2 / 4 / 5 / 0 / 0 TOUCHING,
identical (the Regular's *below the floor* count improves, 4 → 2).
`cmp_counter_dents` 1 / 1 / 0 / 0 / 1 / 0, identical, the `&`'s and the italic
`9`'s single dents moving by at most one unit of depth. Contour and hole
counts are unchanged on every glyph in every style. `cmp_figure_space
--body` 1.77 / 1.62 / 1.54 / 1.54 / 1.36 / 1.47x, all *even*, the Italic alone
moving and by 0.01x. **GPOS: 0 pairs changed in any of the six.** Advance
widths move by at most 2 units, on 0 to 12 glyphs per font — **measured on the
shipped build configuration**, which matters: adversarial review measured the
same thing with `FJORD_STEM` alone and got 19 to 26 glyphs and up to 4 units,
because `FJORD_CUT=0` makes `pen.CUT_AMOUNT` 0 and `cut.blend` a no-op, and
without it three of every four dense points sit on their chords where
`drop_collinear` can reach them. Quote an advance figure with the env that
produced it. `cmp_cap_space`
reports the same WIDE/TIGHT rows before and after in both the Regular and the
Italic, the largest move being `RY` by 0.0025 em.

**The reading-size color does not move.** A 1,300 px line of English plus the
letters that changed most (`MWvz`, the em dash, the acute), rendered through
FreeType at 13 px and 26 px in four of the six styles: the mean ink of the
whole field moves by at most **0.045 of a code value out of 255** — the Black
at 26 px, which is 0.2% of its ink — and by 0.003 to 0.015 everywhere else.
Between 1.3% and 3.9% of the pixels differ at all, which is the edges that
moved by their half unit.

**And the sweep nobody asked for: the gate's FULL run, all 306 glyphs rather
than the 52 letters, improves in every one of the six and is worse in none** —
30 → 20, 21 → 15, 12 → 11, 20 → 12, 34 → 18, 15 → 13, a total of 132 → 89. The
symbols and the marks were carrying the same three faults as the letters.

Page: `tools/wedge_serif/shape/weights296/`.

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
- Round 268: the Regular 400 and Italic 400 are byte-identical to the round-267 builds in outlines, advances AND GPOS pair values; the Bold 700 differs only in `ring`; the Black 900 rebuilt clean (0 glitch findings). The italic 400's touch sweep is still 0 / 0 with one exemption. The bold italic's figure spread is 1.42× (allowed 2.50×).
- Round 268: the pilcrow's construction at the 700 italic now matches the 400's (open counter, 328 vertices, no hole); the composed å Å ů Ů carry the opened ring at the 700 in both styles.
- Round 269: the Italic 400 is byte-identical to the round-268 build in outlines, advances AND GPOS pair values (0 of 486 glyphs differ; only `head`'s timestamps differ between the two files). The BoldItalic differs from round 268 in exactly 58 glyphs -- the twenty base letters `K R Y a b c d f g j k p q r t v w x y z` and their composites -- and 0 GPOS pairs. Glitch sweep 0 of 122; figure spread 1.42x.
- Round 269: the hm letters (a's stem, b d h i l m n p q r u, the heads, exits, arches and dots), the o, e, s, the italic figures and every capital except R Y K were already on the weight axis (700/400 stroke 1.62-1.93x) and were not touched. The capital O's `keyed_ring` is on the axis through its own `unit`, which is why `wscale` is a call-site argument and not a change inside the helper.
- Round 269: the a b d p q counters stay open at the 700 (131-177 wide at half the x-height); the g's bowl counter is 84-126 wide across the x-height and its loop's 140 at -0.30 xh (194 before).
- Round 269: the five f-ligatures are not among the 58 glyphs that moved -- they are built from the roman f's parts and were already on the axis.
- Round 270: after the convex counters, the dent detector reads one dent per face at every weight, the ampersand's; the bold italic's touch sweep is 0 / 0; glitch 0 at 700 / 900 / bold italic and the ruled β alone at the 400s and the 200.
- Round 271: the M's two tops read the same projection past their stems at all three roman weights; the ExtraLight 200 differs from round 267's build only in the M and the ™.
- Round 272: with the ampersand's counters convex, `cmp_counter_dents.py` reads 0 dents in the Bold, the Black and the Bold Italic over its whole charset; the a's counter lower-right reads 93% / 98% white at 700 / 900 against 88% / 89% at its lower left; the M has 0 ink shards and 0 white slivers at 200 / 400 / 700 / 900.
- Round 273: the italic u's right stem tops at 431 in both italics against the ı's 430; no other glyph moved but the u's composites and µ.
- Round 275: the round finials of the roman changed out for the c's top end -- see docs/albo-finials-2026-09-19.md.
- Round 274: the bold italic's head/stem, arch/stem and exit/foot junctions read 0 white slivers, 0 ink shards on u n ı m h l r i a; the Italic 400 is byte-identical in outlines, advances and GPOS to a build of the same tree with the previous `aldine.py`; glitch 0 of 122, touch 0 / 0, figure spread 1.41×, dents 0. The arch's crest is not moved by `hm_sweep` (vertices identical); the u's right stem keeps round 273's top (431); the r has no exit and takes only the head fix; the a moves only at its exit.
- Round 277: after the wedge ruling, every roman and italic weight passes the gates it passed before; the 400s are byte-identical; the one pair the fitter tightened (VI at the 700) is kerned back under the floor.
- Round 276: the italic's round finials changed out for the c's top end, both weights — see docs/albo-finials-2026-09-19.md.
- Round 278: with round 274's gate removed, the BoldItalic and the Regular are byte-identical to builds of HEAD (0 of 486 glyphs, 0 GPOS pairs, each); the Italic 400 reads 0 white slivers, 0 ink shards on u n ı m h l r i a, glitch the ruled β alone, figure spread 1.37×; the a's outline did not move (its exit already passed the foot corner by the bury); the u's right stem keeps round 273's top (431) on the round-234 face, which is live and was not removed; no letter in the metrics tool crossed its tolerance; the other `S > 84` sites in `aldine.py` (rounds 268, 269, 272) were each read and left alone; the `f?` touch reading is the raster, not the outline (0.0114 em in both builds).
- Round 287: the ExtraLight 200, the Regular 400, the Italic 400 and the BoldItalic are byte-identical to the round-288 builds in outlines, advances AND GPOS pair values (0 of 486 glyphs, 0 pairs, each of the four). The Black 900 differs in exactly `e ae oe` and the Bold 700 in `e ae oe eacute`; `eacute` is a true composite referencing `e`, so at the 900 it inherits the change with no record of its own, and at the 700 its own record moves only because the accent's x offset rounds 107 → 108. No kern pair changed at either weight.
- Round 287: gates at baseline. Black 900 — glitch 306 swept / 25 with findings, touch 5 pairs touching / 6 below the 0.012 em floor / 14 exempt, dents 0. Bold 700 — glitch 306 / 23, touch 4 / 6 / 14, dents 0, all three identical before and after. The counter-dent gate was re-run specifically because the bar thickened, and the eye is untouched by construction (the bar's top is a round-39 ruling and it grows downward only).
- Round 287: the `o` and the `c` were measured alongside the `e` and are NOT affected by either fault. Their outer contours read 0.09–0.10 units of circle-fit residual at every weight; the `e`'s read 0.11 at the 400 and 3.92 / 4.12 at the 700 / 900, which is what localised the fault to the tail's handover rather than to the shared ring. The o's counter does wave at the heavy weights (1.53 units at the 900 against 0.05 at the 400) — that is the inward offset of a superellipse at a heavy pen, a separate and much smaller effect, and it was deliberately not touched this round.
- Round 287: `albo_bumps.py` was run before and after and is unchanged — 202 circles on the roman 900 sheet, 204 on the italic, none of them on the `e` in either build. It cannot see either of this round's faults by design: after its 2026-09-18 recalibration it detects notches and spurs at the pen's scale, having been deliberately moved off the edge-waviness detectors the owner had rejected. This is recorded so the next session does not read its silence as the letter being clean.
- Round 287: the export curve fitter (`geom.fit_curves`) was checked and ruled out as the cause — `ALBO_CURVES` is 0, so every contour ships as the dense polygon at both the clean 400 and the wavy 900, and the fault reproduces in the design geometry before export. `geom.SPACING`, `close_corners` and the ink-spread mitre were likewise not involved: the defect is present with all three unchanged and absent at the 400 with all three unchanged.
- Round 291: gates at baseline in all six fonts. Glitch — bold italic 306 swept / 23 findings, italic 400 306 / 20, Regular 306 / 19, Bold 306 / 23, Black 306 / 25, all identical before and after; the ExtraLight fell from 21 findings to 18. Touch — bold italic 0 / 0, italic 400 0 / 0 / 1 exempt, ExtraLight 1 / 3 / 14, Regular 2 / 4 / 14, Bold 4 / 6 / 14, Black 5 / 6 / 14, every one identical and the same named pairs (VI, ff, fi, Q, Q; QQ). Counter dents 0 in the bold italic, the Bold and the Black, 1 in each 400 and the 200 (the ampersand's, the drawn exception), unchanged. Figure spread 1.47× / 1.37× / 1.77× / 1.62× / 1.54× / 1.54×, unchanged. **No GPOS pair value changed in any of the six fonts.**
- Round 291: `close_corners` has exactly two callers in the whole face — the italic `s` (`S_BLEND` 18) and the `_g_roman` the italic `g` is drawn from (`G_R_BLEND` 10). The `c`'s `C_BLEND` is 0 and its closing is a no-op; the roman `s` and `g` are drawn elsewhere and never call it. Checked by instrumenting the function and logging every call: one call per letter, and the roman 400's whole charset makes none. That is why the density fault was on two glyphs and no others, and why the simplify cannot reach a third.
- Round 291: the `e` was reported faulted and is not. Zero reversals, four one-unit grid jogs, byte-identical before and after in both italics. Its "angular" eye is the 11-unit polygon every contour in this face is made of (`ALBO_CURVES` = 0 since round 231, deliberately), verified by counting off-curve points: **zero in every lowercase letter of both the Regular and the Italic 400**, so nothing in the face is a curve and the facets are the declared texture rather than a defect.
- Round 291: the one-unit "spurs" reported on `e i m n r u` are the integer em grid, not the drawing. Each is a 1.0-unit segment between two ~100-degree turns on a shallow edge; the weld's 12-unit minimum path length leaves every one of them, deliberately, and they are present on letters nobody reported. One unit is 0.013 px at 13 px.
- Round 291: welding was tested at `WELD_WIDTH` 12 (which would reach the `y`'s 8.52-unit crack) and REJECTED on a rendered before/after sheet of all 26 sites it would newly touch — it cuts the tips off the wedge serifs of `a h m n u y A K M N Q V W 4 6 9`. Re-tested at `WELD_TURN` 152 with the same width: 14 new sites, still blunting the `u`, the `M`, the `4` and the `9`. Both arms recorded so the same candidate is not re-proposed.
- Round 291: the designed hairline gap on the Y and the P is untouched. The weld can splice at most two vertices, and that gap is three to six vertices down each flank by its own measured width and run (`docs/albo-hairline-gap.md`); the italic Y's single weld adds 13.7 square units, 0.015% of the glyph, at its arm junction and not at the gap.

## 38. Round 297 — the v's top RIGHT serif, and the y that the first measure could not see

Owner 2026-09-20: *"Italic 400 v needs higher left top serif"*, corrected within
the same turn to *"top right serif of v, not topleft"*, then *"look at w and
others too"*, then *"d wins, correct y too"*.

### What the fault is

The top right serif is the rising hairline's terminal. Measured on the shipped
Italic 400 as the top of each letter's own right-hand half:

| letter | top of its right side, x x-height |
|---|---|
| x | 1.050 |
| c · y | 1.029 · 1.028 |
| o · e · s | 1.019 · 1.016 · 1.013 |
| u · z | 1.004 |
| n · m · r | 0.988 · 0.987 · 0.986 |
| **w** | **0.971** |
| **v** | **0.956** |

The v's terminal stops a twentieth of an x-height below anything else, and its
LEFT apex is meanwhile the tallest thing in the whole lowercase at 1.041. The
letter is not merely short on the right, it is **tilted**: 1.041 on one arm
against 0.956 on the other.

### The measure that was wrong, and the owner caught it

That table reads the top of each letter's right-hand HALF, and on a letter as
narrow as the y that half catches the LEFT stroke's crown — so the y read 1.028
and this document's first draft said the y was clean. It is not. Measured on
the rightmost FIFTH instead, which is the terminal and nothing else:

| | v | w | y |
|---|---|---|---|
| terminal top | 0.956 | 0.936 | **0.919** |

The y is the worst of the three. **A whole-half measure cannot see a terminal on
a narrow letter; take the slice.** The x (1.050) and the z (1.004) are genuinely
clean by either measure, so the family is v, w and y and nothing else.

**AND THE BAND ABOVE IS A HALF-MEASURE BAND — do not compare it against these
three numbers.** Found by the pre-release review, 2026-09-20. "0.986 to 1.050"
comes from the FIRST table, the letter's right-hand half; the v/w/y figures come
from the rightmost FIFTH. Read on the fifth measure the alphabet does not run
0.986 to 1.050 at all:

```
  k 0.918   y 0.919   w 0.936   v 0.956   o 0.962   m 0.965   g 0.968   e 0.985
```

**The k reads 0.918, below the y**, and four more letters sit under 0.986. Those
are INSTRUMENT ARTIFACTS, not low terminals: a round letter's rightmost fifth is
its shoulder, and the k's is the foot of its leg. That is exactly why this has
to be written down — a session re-running the adopted measure finds five more
"low terminals" and has nothing here telling it they are not real.

The ruling stands on the comparison that is like for like: terminal-of-a-diagonal
against terminal-of-a-diagonal, the v, the w and the y are the three lowest and
the x and the z the two highest.

### What shipped

`DIAG_ENTRY_Y`'s sibling `DIAG_TERM_RISE` in `outlines/glyphs/aldine.py`, at
**0.10 of the x-height** — the owner's arm d off the ladder, which takes each
letter's terminal up to its own apex so the tilt goes to zero. The dial lifts
the terminal's own point and half-lifts its neighbor, so the hook keeps its
shape and its turn back to the left; the hairline's rise, its width table and
round 276's finial are untouched. On the v and the w the terminal is the
stroke's LAST point; on the y it is the tail's FIRST, because the y's right
stroke carries on past the baseline into the swash instead of stopping.

One qualification on "the finial is untouched", from the pre-release review:
true of its WIDTH, not of its ANGLE. `finial_cut` reads `tangents(p)[-1]`, so
raising the last point steepened the v's final segment from about 107 to about
101 degrees and the terminal's face rotates with it, roughly 6 degrees. The
width genuinely does not move — `finial_widths` reads `bf(1.0)` and
`fin_floor()`, neither of which changed, confirmed on the y's far end where the
widths below the baseline match to 0.04 units. The owner judged arm d from a
render, so the rotated face is in what he approved.

| | v | w | y |
|---|---|---|---|
| terminal, before → after | 0.956 → 1.048 | 0.936 → 1.028 | 0.919 → 1.007 |
| tilt, before → after | 0.085 → 0.000 | 0.091 → 0.000 | 0.109 → 0.021 |

It applies at every italic weight, the BoldItalic included: this is the drawing,
not a heavy-end repair.

### The fitting did NOT need to move, and that was measured rather than assumed

A raised terminal reaches further right — the v's ink to 462 design units
against 453, the w's to 652 against 642, the y's to 487 against 483 — so the
right-side fit was re-measured on 24 pairs, as closest approach in 2-D. Every
delta among those 24 is under 0.006 em against a 0.098 em lowercase median, they
go in BOTH directions (`ve` +0.005, `yn` −0.004), and the tightest of them
(`yy` at 0.063) does not move at all.

**THAT IS A BOUND ON THE 24, NOT ON EVERYTHING THAT MOVED, and the first draft
of this section said otherwise.** Corrected by the pre-release review,
2026-09-20. There are **213 pairs per style** with v, w or y on the left, and
the ones not picked — v/w/y followed by a CAPITAL — move three to four times
that bound:

```
  Italic      vV 0.201 -> 0.179   wY 0.214 -> 0.192   yY 0.222 -> 0.201
  BoldItalic  vV 0.196 -> 0.172   vW 0.172 -> 0.156   yp 0.067 -> 0.058
```

"No bearing changed" needs the same care. The BEARINGS **table** did not (the
v's lsb is 44.59 before and after). The fitted advance and the right sidebearing
of the shipped TTFs did:

| upm 1000 | Italic v | w | y | BoldItalic v | w | y |
|---|---|---|---|---|---|---|
| rsb before | 18 | 20 | 22 | 16 | 17 | 22 |
| rsb after | 9 | 9 | 15 | 5 | 6 | 14 |

The mechanism is worth keeping, because it will catch the next person who moves
a point on a sheared face: `fit_aldine` measures the right edge in UNSHEARED
space, so raising a point by 0.10 of the x-height subtracts `shear x dy` — about
9.9 units at 13 degrees — from its unsheared x. The advance therefore SHRINKS by
0.9 to 3.4 while the sheared `xMax` GROWS by 9 to 10.

**Nothing in the drawing needs fixing, and that was checked rather than
asserted**: `cmp_touch.py` is green on both arms (0 touching, 0 under the 0.012
em floor, both italics), the tightest v/w/y pair after the change is `y1` at
0.041 em, `cmp_space_2d --per-glyph lower` moves only the v's left median
(0.099 -> 0.102) and `letter+quote` (0.135 -> 0.131), and the `.cpfont` converter
sources each glyph bitmap from FreeType's `bitmap_left`/`bitmap_top` rather than
from the advance, so a 5-unit right sidebearing cannot clip anything on the
device. What was wrong was the record, and the record is what the next spacing
round would have trusted instead of re-measuring.

### The despike chord, 2.5 → 3.0

Raising the w's terminal tripped a NEW hair-gate finding on the BoldItalic w —
153.4 degrees at (410, 103), arms 4.5/2.0. It is not a drawing fault. The
outline there exports as `(412,107) (410,103) (410,105)`: a two-unit spur the
integer grid left, whose neighbors are 2.83 apart, so round 295's `chord_lim`
of 2.5 skipped it by a third of a unit. **The same spur is in the shipped
drawing** at (413,107), where the arm is 5.0 and the turn falls just under the
gate's 150 — latent grid noise that a one-unit shift anywhere would have
tripped.

Widened to 3.0, and measured first, because round 295 records three tolerance
rules that each ate the arrows. Across all six shipped fonts:

- **17 points removed in total** — 2 to 4 per font, 2 to 4 glyphs touched.
- Total ink moves by **+0.0000%**.
- **No arrow moves at all.**
- The only glyph whose area moves by more than a hundredth of a percent is the
  ExtraLight's `currency`, by 3 units of 29,099 (+0.010%).
- Hair findings: BoldItalic 2 → 1, every other font unchanged.

It touches all six point streams, and is taken under the owner's standing
*"Chase them to zero first"*.

Counter dents: the COUNTS are identical before and after (1/1/0/0/1/0), but
"byte-identical" was too strong — the Italic `9`'s dent moved 1058/13.7 to
998/13.1, because the despike removed a point from `nine`. It got smaller.
Collision sweep: every font is unchanged, and the roman is not "two touching
pairs" — two is the REGULAR's count. ExtraLight 1, Regular 2, Bold 4, Black 5,
all four pre-existing and all four unmoved. Both corrections from the
pre-release review, 2026-09-20.

### Measured and NOT ruled: the left entry serifs

Taken before the owner's correction, and kept because it is real and cost the
measurement. The entry serif's tip bottoms at **0.815 xh on the i, m, n, r and
u — all five at the same figure** — and at **0.745 to 0.750 on the v, w, x, y
and z**. The five diagonals hang a fourteenth of an x-height below the
alphabet's one entry line. `DIAG_ENTRY_Y` is in the file at its shipped 0.755,
so every letter is byte-identical on that axis. It is recorded rather than acted
on, because it is not what was asked about.


## 39. Round 298 — the entry becomes a table, and the 9's tail is still on its counter

Owner 2026-09-20, ruling on the four open items rendered at
`claude.ai/artifact/BQcMcb3sghy6xWnSDMd7H8`:

1. *"vary the entry to slightly improve legibility within common english words"*
2. *"improve '8' roman, fix 9 to not have its tail overlapping its counter"*
3. *"need an improved version center. show me roman and italic 'g' to compare."*
4. *"leave as is"* — **the E's bars are closed.** The 24%-heavy measurement
   stands in the record; it is no longer an open item and does not return to
   triage.

### The entry is a TABLE now, not one number

`DIAG_ENTRY_Y` was a single dial and the round-297 record proposed lifting all
five diagonals onto the alphabet's one entry line. The ruling is the other
thing: **lift, then separate again.** A line every letter shares is a
difference the reader does not get (`docs/albo-imperfections.md`), so
`entry_y(ch)` in `outlines/glyphs/aldine.py` is a base plus a per-letter delta
in reference units at A_UNIT 429, inside the face's 2-to-7 unit band.

The table is FOR the pairs that meet in running English, and not for the
alphabet: **v/w**, because the w is the v doubled and this module already
records that it "reads as a blot where the v reads as a letter"; and **v/y**,
because above the baseline the y IS the v and *every*, *very* and *vary* put
them a letter apart. The **x** and the **z** ride the line — entered by an arm
and by a bar tip respectively, they are already distinct in construction.

`ALBO_ALD_ENTRY_ARM` selects the ladder; **`a` is shipped and was verified
byte-identical** (0 glyphs differ against build 205's italic), so an unset env
changes nothing. Arms b–e touch exactly 12 glyphs: `v w x y z`, `wcircumflex`,
`yacute ycircumflex ydieresis`, `zacute zcaron zdotaccent`.

Measured on a raster — the lowest ink in the leftmost ink column of the
letter's TOP BAND:

| arm | v | w | x | y | z |
|---|---|---|---|---|---|
| a shipped | .698 | .698 | .698 | .693 | .693 |
| b flat line | .757 | .757 | .757 | .751 | .751 |
| c cut by 3 | .762 | .746 | .757 | .757 | .751 |
| d cut by 7 | .767 | .741 | .757 | .762 | .751 |
| e short of the line, cut by 7 | .761 | .723 | .750 | .750 | .739 |

`i m n r u` read .746 on every arm — they are not touched.

**THE BAND COMES FIRST, AND THAT IS THE INSTRUMENT'S WHOLE CORRECTNESS.** The
first measure taken here read the leftmost point of the whole letter and
returned 0.455 for the `n`: on a sheared face the stem's BOTTOM-LEFT corner is
further left than the entry serif, so a whole-letter measure reads the foot.
Round 297 met the same shape of bug at the other end of the stroke. **These
figures are also NOT the 0.815 / 0.745 of the round-297 record** — that measure
is defined differently, and the two must never be compared; what is comparable
is the gap, .048 xh here against .067 there, and the ordering, which agrees.
Noise floor about ±0.005 (arm e reads the untouched `i` 0.004 high).

### The 9's tail is on its counter, and rounds 211–212 did not finish it

The owner's report is exact. At 560 px the tail's inner edge runs through the
ring's wall and leaves a **white sliver in the ink at the counter's lower
right**. `NINE_JOIN_SINK_IT` was set to 30 in round 211 for this very fault
(*"the tail's inner edge crossed the counter and bit a notch out of it"*), with
the diagnostic that sinking DEEPER makes it worse. It is still there.

Four arms, all reached by existing env dials, no code change:
`b` exit −35°, `c` entry width 0.30 over 0.40 of the run, `d` join sink 45,
`e` exit −35 with the wider entry. Page:
`claude.ai/artifact/CsEcYnbMi33ZzrrPTjh3RL`.

### What the 8 and the g are waiting on

The 8 is the construction job round 195 named and declined: its rings want
putting on the pen the way the g's were in round 182, and `ring(con=)` cannot
invent the direction-dependence a nib has. The g's item was found STALE while
rendering it — see the correction below.

### The compound g flag is attached to a letter the face retired

**Checked rather than assumed, and the open-items record was wrong.** Building
the italic with `ALBO_ALD_G_COMPOUND=1` changes **zero glyphs**. The flag is
read inside the *cursive* g (`G_STYLE == 'cursive'`, rounds 197–225) and the
face has shipped `ALBO_ALD_G_STYLE=roman` since round 226, so round 196's
compound work — recorded as "built, inert, one located fault from finishing" —
sits on a construction the type no longer draws. Confirmed by diff: shipped vs
cursive differs in 5 glyphs (`g gcircumflex gbreve gdotaccent uni0123`), and
cursive vs cursive+compound differs in the same 5. So it is not one fix from
shipping; the owner's *"need an improved version center"* is a ruling on the
CURSIVE arm.

### An interactive spacing bench

Owner, same day: *"make an update interactive page for me to give letter
spacing feedback on using real words"* —
`claude.ai/artifact/VCbkYNuYmZgV2m5Udd6ruy`. Eighteen real English words, each
opened at one pair, with a slider in thousandths of an em and a verdict.

**The slider's zero has to be what ships, and that costs a kern lookup.**
Splitting a word to put an adjustable gap in it loses the font's own kern at
exactly that pair, so every item carries its GPOS pair value (roman and italic
separately), read out of the built font by `kernlookup.py`, and the page
re-applies it. Every other pair in the word keeps the font's kerning. The
verdicts persist in the artifact's own store under `spacing/<word>`, which is
where the next spacing round reads them from.


## 40. Round 299 — the owner's bench values, and the quantum that was wrong by 16x

Owner 2026-09-20, having used the bench: *"roman and italic need different
settings. i just updated roman settings, how do you get them?"* and then
*"saved italic"*. The values are read straight out of the artifact's own store
(`read_db` on the bench artifact), not exported by hand.

His 35 judgments are DELTAS on what each pair already carries — the bench's
slider zero re-applies the shipped GPOS value for that pair, so a number he
left is a correction. They live in `BENCH_DELTAS` in `outlines/kern.py`,
per style, with `ALBO_KERN_BENCH` unset by default (a build is byte-identical
to build 205's kerning, verified).

**The shape of his answer.** Capitals into lowercase want OPENING in both
styles (roman `W a` +41, `Q u` +37, `T o` +24; italic `Y e` +42). Lowercase
running text barely moves in the roman (−5 to +18) and moves consistently
POSITIVE in the italic (mean +9). Both roman punctuation pairs want closing
hard — `y '` −50 is the largest correction in the bench — where the italic's
comma wants −1.

### THE DEVICE QUANTUM IS 1.16 UNITS, NOT 18.5

`kern.py`'s own docstring says its 18-unit step is "one sixteenth of a pixel
at 13 pt on the 2x app", and `CLAUDE.md` repeats it as "quantum 18.5 units on
the phone / 37 on the X3". **Both are wrong by a factor of 16**, and the error
is load-bearing: it is the stated reason the lowercase is not kerned at all
("a median of −24 from the 69 lowercase pairs — below the quantum").

`fontconvert_sdcard.py` encodes `raw = round(du * (ppem/upm) * 16)` into a 4.4
signed fixed-point int8 — 1/16 PX resolution, not one pixel. So:

| | ppem | quantum (design units, upm 1000) |
|---|---|---|
| phone, 13 pt at 2x | 54 | **1.16** |
| X3, 13 pt at 1x | 27 | **2.31** |

Every value in the bench survives to the device. The smallest, the italic's
+2 on `w i`, is 2/16 px on the phone and 1/16 on the X3; the −24 lowercase
median that was called sub-quantum is 20/16 px, a pixel and a quarter.

**Found alongside, and NOT changed:** `('T','A')` and `('VW','A')` at −216
units are −11.66 px at 54 ppem, outside the 4.4 format's −8.0…+7.94 range, so
**the phone clamps them to −8 px and the desktop does not**. A separate fault;
recorded rather than quietly fixed inside a kerning round.

### The instrument was wrong twice, and both were caught before the type moved

1. **One bench row was mislabelled.** `away` was opened at the wrong index: the
   row said `w a` and rendered **a y**. His −4 / +17 is that pair and is
   recorded as that pair. Every one of the nineteen rows was then audited by
   rebuilding its label from its own index — one mislabel of eighteen. `w a`
   has never been shown; a new `wander` row carries it.
2. **The apostrophe pair missed the glyph it was judged on.** The bench renders
   `story's` with U+0027 quotesingle and the table keyed only U+2019
   quoteright, so the largest correction in the bench landed on a glyph the
   page never drew — and the fault was invisible in the class arm, whose
   `quote` class holds both. Both keys carry it now.

Rule this is an instance of, and it is the same one round 297 met: **a bench
that renders a pair is not the same thing as a table that names one.** Rebuild
the label from the data and compare, every round.

### Two arms, and the trade between them

Page: `claude.ai/artifact/GhW3SNViaQ5RzHHENnqcRM`.

- **Arm A, `pairs`** — each judged pair becomes a single-glyph exception at
  exactly his number. Nothing he did not look at moves. It does not
  generalize: `v e` is corrected while `v o`, `v a` and `v c` are not.
- **Arm B, `classes`** — each judgment moves the class cell it belongs to and
  two words in one cell are averaged. This is the face's own mechanism and the
  shape the `.cpfont` stores natively. **Its cost is the STEP rule**: cells
  must be multiples of 18, so six of his lowercase corrections round to
  nothing, `v e` +17 among them.

Not ruled yet; the owner picks.


## 41. Round 301 — every common pair, measured off his own books

Owner 2026-09-20: *"set those aside and give me all remaining common pairs
including To to Ot ot"*. The four he names are the ask in miniature: the same
two letters in both ORDERS and both CASES, because `To`, `to`, `Ot` and `ot`
are four different meetings and a bench that shows one of them has said
nothing about the other three.

**"Common" is MEASURED, not guessed.** `tools/wedge_serif/pair_census.py`
counts pairs over the corpus `outlines.cmp.corpus` already uses — the epubs
under `~/src/claude-tools`, the reader's real-world books — and picks the
commonest real word carrying each pair. An English frequency table written for
someone else's prose would have done, badly: this is what HIS reader renders.

| | |
|---|---|
| books | 36 |
| words | 508,518 |
| distinct pairs | 1,486 |
| pair instances | 2,007,794 |
| top 50 pairs | 49.9% of all instances |
| top 250 pairs | 91.1% |
| pairs carrying a CAPITAL | 771 distinct, **3.9%** of instances |
| pairs carrying a MARK | 271 distinct, **4.2%** |

That last pair of rows is the finding worth keeping: **the lowercase is where
the reading is.** 92% of every letter meeting in his books is lowercase beside
lowercase, which is also why this face's fitting rule (round 3) carries the
lowercase and its kern table is capitals and punctuation.

### The bench is 396 rows now, and the cut is stated

A naive expansion of his ask produced **627 rows** — every case and order
variant of every seeded pair that the corpus contains — and most of the extra
was rare capital noise (`Ot` itself occurs 59 times). The shipped cut:

- **lowercase**, a pair occurring 1,200 times or more (241 rows);
- **capital + lowercase**, where the capital is one whose own shape changes
  the meeting — `A C F G J L O P Q R S T V W Y`, an overhang, a diagonal, a
  round or an open corner — and the pair occurs 50 times or more (108 rows);
- **marks**, 400 times or more (47 rows);
- B D E H I K M N U are deliberately absent as a first letter: they are flat
  on the side that matters and their pairs are the fitting's job, not the
  kern table's.

**397 rows, 94.7% of every pair instance in his books.** His 35 existing
judgments keep their own rows and their stored values; 18 pairs were already
covered and are not duplicated.

The page groups by class, pages 40 at a time, filters to what is still unset,
and shows each pair's own corpus count beside it so he can spend his attention
where the reading is.


## 42. Round 302 — 189 judgments, and what they are actually saying

Owner 2026-09-20, having worked the 396-row bench: *"updated"*. 111 roman and
78 italic values, read out of the artifact's store.

**They are not 189 kerns.** Sorted by what they have in common, most of them
are four or five decisions about LETTERS:

| group | n | mean | sd | reading |
|---|---|---|---|---|
| roman · marks | 39 | −17 | 14 | per MARK, not one number (below) |
| roman · lowercase | 66 | +5 | 14 | by the LEFT letter: round +11, flat +2 |
| roman · capitals | 6 | +23 | 12 | all six positive |
| italic · lowercase | 17 | +8 | 8 | **uniform** — 12 of 17 within half a phone pixel |
| italic · capitals | 29 | +2 | 20 | **not** uniform: −41 to +57, real per-pair work |
| italic · marks | 32 | −5 | 15 | small; the italic already tucks its marks |

**The clearest single finding: the roman apostrophe is 41 units too far out.**
He pulled it in on all seven words carrying one, mean −41 with a spread of ±9
— nothing else in the bench is that consistent. Period −12, comma −15, colon
−7, semicolon −6. That is a ruling on the MARK'S OWN BEARING: one change to
one glyph, against a kern for every letter that can precede it.

**The clearest structural finding: in the roman lowercase, the LEFT letter
predicts his number and the right one does not.** A round letter before
anything wants +11 where a flat one wants +2 (the right-hand letter: +5
either way). So the roman's round lowercase — `b c d e g o p q s` — is fitted
about a third of a phone pixel too tight on its right side. A bearing, not 66
kerns.

**And one place the structure is genuinely absent**: the italic capitals, mean
+2 with a −41..+57 range. Generalising there would spend his work badly, so
the model leaves them alone and they stay per-pair.

### Two arms, and why neither is the recommendation

`bench_values.json` carries both, per style, and `ALBO_KERN_BENCH=literal|model`
builds them (`docs` page: `claude.ai/artifact/L39ZyK3hi4PomUDBg52wJR`).

- **literal** — 111 + 78 pairs at exactly his numbers. Safe, inconsistent:
  `o n` corrected while `o m` is not, though they are the same meeting.
- **model** — 395 + 314 pairs: his numbers where he gave one, the structure
  above where he did not.

**Recommended and NOT yet ruled:** neither, quite. The marks and the roman's
round lowercase are BEARING faults — fix them in the drawing, where each costs
one number and reaches every pair nobody will ever judge — then kern what is
left, which is the capitals. About six letter changes plus ~40 kern pairs,
against 709.
