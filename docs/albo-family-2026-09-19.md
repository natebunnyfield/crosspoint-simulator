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
