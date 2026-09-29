# Albo issue sweep: letters that don't read as themselves, defects no gate sees, pending requests (2026-09-28)

Owner: *"subagent of high thinking to find and fix other issues."* A read-and-fix pass by a
subagent over all four cuts, lowercase first, then marks, figures and punctuation. **Nothing here
ships.** Every fix is behind an env dial whose default reproduces round 436 byte for byte; the
owner rules on the arms.

- **Surveyed:** simulator `7f24b9c` (round 436: the 400 Italic c's top drawn, arm E1). The work
  started on round 435 (`e9cc156`) and was re-proved on 436 when it landed. Baseline fonts: the
  round-436 build (`scratchpad/r436/Albo-*.ttf`).
- **Default identity, proved:** all four cuts built from the final tree with no dials (`sweep/def4`)
  against r436, `cmp_outlines.py --advances`: **IDENTICAL** (Regular, Italic, Bold, Bold Italic;
  outlines and advances).
- **Gates on everything at once** (the recommended dials together, build `sweep/REC4`):
  `instruments/poor_gates.sh r436 REC4 "Regular Italic Bold BoldItalic"` → **POOR GATES: no delta**
  (touch 0 → 0 in all four cuts; hairs, letters and full sweep, no new rows; "counter-dent lines
  1 → 1" in both bolds, which is the report's header line -- the dent count itself is 0 → 0;
  contour census unchanged at 1056; approved 2/2; e mouth ok). Each fix was also gated alone.
- **The glitch gate cannot see these moves** (found by the adversarial review): poor_gates passes
  glyph NAMES (`braceleft`, `uni0237`) to `cmp_glitch --chars`, which reads them as characters, so
  its "1 with findings → 1" is a sweep of the wrong glyphs. Re-run by hand on the real moved
  characters of each cut (REC4 against r436): only SPLIT notes, counts unchanged (Regular 57 → 57,
  Italic 63 → 63, Bold 57 → 57, Bold Italic 62 → 62). The contour gate likewise counts glyphs, so
  the contour count of every changed glyph was checked separately: unchanged in all four cuts.
- **Proof images** (PNG, native pixels, lossless, before/after at a display size and at the
  reader's sizes, integer NEAREST magnification) are in the session scratchpad, `sweep/final/`,
  regenerated from the final builds by `sweep/tools/final_proofs.sh` (instrument
  `sweep_proof.py`). Older explorations (iteration pictures, reference rows) are in `sweep/proof/`,
  `sweep/r/`, `sweep/j/`, `sweep/o/`, `sweep/zoom/`, built on earlier trees.

## Summary

All proof paths below are under `scratchpad/sweep/final/` unless named otherwise.

| # | issue | cut | evidence (measured) | dial = recommended | gates | proof |
|---|---|---|---|---|---|---|
| 1 | r arm is a ramp ending in a horn (the c's round-433 fault) | Italic, BI | every reference r arches over, terminal hangs to 0.72-0.76 xh; Albo's flag tip is the letter's top, ink 458 (I) / 457 (BI) against the o's 444; notch under the tip (junction STEP 4.5) | `ALBO_ALD_R_DRAW=1`, `ALBO_ALD_R_DRAW_700=1` | clean | `r_I.png`, `r_BI.png`; refs `sweep/ref_r.png`, overlay `sweep/r/w4_ov.png` |
| 2 | j wears a stale nub, not the i's head | Italic, BI | 10-unit tab with a square notch; cmp_jogs BI j t180 off 9.4, ȷ/ĳ jogs + STEP 4.0; Italic ĳ STEP 10.8 | `ALBO_ALD_J_HEAD_I=1`, `ALBO_ALD_J_HEAD_I_700=1` | clean; BI jogs/steps 0, Italic ĳ 10.8 → 1.9 | `j_I.png`, `j_BI.png` |
| 3 | italic tittle too small (owner request) | Italic | dot/xh 0.156, under every italic reference (0.198-0.262, median 0.221) and the roman's 0.211; i dot 1-3 dark px at 8-16 pt on the X3 | `ALBO_ALD_DOT_SCALE=1.38` (= the roman; 1.45 = the references' median) | clean | `dot_I.png` (today, 1.26, 1.38, 1.45, Regular) |
| 4 | acute a hairline; tilde and macron half-size | all four | acute mean width 0.29-0.33 of the stem vs the grave's 0.68-0.93 and every reference's 0.62-0.72 (acute = grave in all); e-acute 0 dark px at 8-12 pt (Regular), 0-1 (Italic) | `ALBO_ACUTE_OPT=b`, `ALBO_TILDE_OPT=b`, `ALBO_MACRON_OPT=b` | clean | `acc_Regular.png`, `acc_Italic.png`, `acc_Bold.png`, `acc_BoldItalic.png` |
| 5 | curly braces drawn as dented parentheses (owner request) | all four | every reference brace is two S-curves: hooked ends, beak at the middle | `ALBO_BRACE_OPT=b` | clean | `brace_R_I.png`, `brace_B_BI.png`; refs `sweep/brace/refs.png` |
| 6 | Bold Italic e eye closes at 8-12 pt (owner follow-up) | BI | bar 36 units = 0.35 stem (refs 0.37-0.45); eye open at 9/12 sizes | `ALBO_ALD_E_BAR_K_700=1.25` → 12/12 | clean | `e_BI.png` |
| 7 | Bold Italic o b d p q counters are lozenges | BI | round 270's hull chords: o longest straight 177.5 units + 2 corners, b 260.4 + 3, p 195.1 + 1 | `ALBO_ALD_O_OVAL_700=1`, `ALBO_ALD_BOWL_OVAL_700=1` → o 65.0 / 0 corners, b 88.1 / 2, p 94.4 / 0 | clean | `bowls_BI.png`; refs `sweep/ref_o.png` |
| 8 | z bottom-left is a zigzag | Italic, BI | diagonal's square foot across a 14-unit hook: two notches (I), three turns (BI), STEP 8.4 | `ALBO_ALD_Z_FOOT_FILL=1`, `ALBO_ALD_Z_FOOT_FILL_700=1` | clean | `z_foot.png` |
| 9 | parts_audit's FAINT check is wrong for flat bars | instrument | unpadded EDT puts a full-height bar's ridge on its top row: "italic dashes faint at 9/12 sizes" is an artifact; the reader draws them level 2-3 | fixed in `instruments/parts_check.py FAINT=1`; parts_audit.py needs the same one-line pad | n/a | §2 |

All together, before/after in a sentence per cut: `REC_Regular.png`, `REC_Italic.png`,
`REC_Bold.png`, `REC_BoldItalic.png`.

Not fixed (rulings or bigger drawing needed): the italic s foot, v/w/y/x flags, the k's and d's
heads, figure joins, 8 pt dots, the 400 e's eye, the straight double quote. §3. The 400 Italic c
was the main agent's and was drawn in round 436 while this pass ran; nothing here touches it.

## 1. The fixes

### 1.1 The italic r's arm, drawn (`R_DRAW`)

**The fault.** At one x-height every reference r -- Poetica, Coelacanth, Cancelleresca, Flanker,
Pagella, Berkeley, Georgia, and the three bold italics -- arches over: the arm crests at the x-line
and the terminal hangs on the right, its lowest point at 0.72-0.76 xh (overlay, unsheared,
`sweep/r/ov_I.png`; row, `sweep/ref_r.png`). Albo's arm is a straight ramp rising right into a flag whose tip
is the highest point of the letter (TTF ink top 458.2 Italic, 456.8 BI; the o's 443.7) with a
notch under the tip where the finial's swell corner meets the underside (`sweep/zoom/r_Italic.png`;
cmp_junctions `r STEP 4.5 at (346,344)`). Same mechanism as the c (round 433): `PR.finial_widths`
grows width about the path, so round 276's ball-to-finial conversion turned the ball into a flag.

**The construction** (`aldine.py`, `_r_drawn_arm`), modelled on `_c_drawn_top`: the arm is the n's
own shoulder (HM_ARCH_K, climb blended halfway to Flanker's steeper 0.55/0.76/0.88) stopped at a
junction (0.60 P, centerline 0.91 xh; 0.88 at the 700); a terminal is unioned on -- outer cubic
continuing the arch over to the tip (0.95 P, 0.90 xh; 0.87), a straight cut face 0.24 xh at 262
degrees, the face's lowest point cut back 20 units along both edges, and one concave underside
leaving at 95 degrees back to the arm's lower edge. Dials `ALBO_ALD_R_D*` (+`_700`), listed at the
definition.

**Measured after** (REC4): ink top 444.2 (I) / 438.6 (BI) -- at the o; junction steps 0 (both);
hairs, touch, glitch clean. The arm keeps its weight -- ink right of the stem and above 0.5 xh,
13,213 → 12,509 units² (Italic, -5%) and 15,590 → 16,511 (Bold Italic, +6%) -- so round 417's
"serif on right is too thin" weight is held, now hanging instead of flagging.

**Iteration record** (each seen at 3x with vertices,
`sweep/r/w*.png`): a junction at 0.654 P left the crest low (400 design) and the terminal right of
every reference; 0.55 P put a corner on the outer edge; a crest knot before the junction folded
the stroke's outer edge; a steep underside with a long arrival handle made an S-curve and a spike
at the counter's top (the c's lesson again); a plumb face against a 95-degree underside made a
13-degree point that `cmp_contour_hairs` reads as a REVERSAL (166.8 deg) -- hence the 20-unit
cut-back (`R_DTB`).

**Spacing -- the owner's call.** `build.fit_aldine` measures only ink inside the x-height band.
The flag stood above it; the drawn terminal hangs inside it. Band right edge +22.4 (I; the cut
facets the terminal's rightmost curve) / +13.8 (BI), so with the bench's bearing untouched the
advance goes **388 → 410** and **422 → 437**. Closest approach to the next letter
(`instruments/pair_gap2d.py`, shaped, Italic; today → R_DRSB=0 → R_DRSB=-15):

| pair | ra | re | ro | rc | rd | rs | rn | ri | ru | rt | rm | rr | rk | rv | ry |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| today | 120.7 | 103.0 | 108.2 | 107.9 | 108.2 | 119.4 | 55.2 | 49.7 | 70.8 | 56.9 | 53.3 | 57.9 | 97.0 | 70.4 | 71.7 |
| DRSB 0 | 118.0 | 105.3 | 108.7 | 108.9 | 107.8 | 121.8 | 67.4 | 61.6 | 83.8 | 72.3 | 65.5 | 70.3 | 119.3 | 78.3 | 79.6 |
| DRSB -15 | 105.2 | 91.4 | 95.3 | 95.1 | 94.4 | 107.6 | 52.9 | 47.1 | 69.4 | 57.7 | 51.0 | 55.8 | 104.8 | 63.8 | 65.0 |

Bold Italic, the same three rows for a sample: ra 110.7 / 111.1 / 97.5, rn 56.3 / 67.4 / 52.9, rt
57.9 / 78.0 / 63.0, rk 112.8 / 132.4 / 117.9. Advances: r (Italic) 388 / 410 / 395, (BI) 422 / 437
/ 422.

Round followers keep today's white at DRSB 0 (within 3 units); headed followers get 8-22 looser (the terminal
hangs away from their heads where the flag reached toward them). No single bearing matches both.
**Recommended: `R_DRSB` 0** -- and a trap for whoever dials it: build.py spaces the Greek sigma's
right side from the r's final bearing (`'σ': ('o', 'r')`), so any nonzero `R_DRSB` moves the
sigma's advance by the same units (measured: Italic sigma 648 → 633 at -15, BI 635 → 620). `R_DRSB`
only acts when `R_DRAW` is on and `R_OPT` is not `a` (option `a` never draws the arm).

### 1.2 The j wears the i's head (`J_HEAD_I`)

The block above `a_j` says the j "takes the i's [head] rather than a second drawing". It did when
both wore `wedge_head`; rounds 233-278 rebuilt the i's as `hm_head` (an entry stroke across a
stem top cut to follow it) and the j kept the wedge, which shows only as a nub: a 10-unit tab
with a flat underside meeting the stem in a square notch (`sweep/j/ij_head_I.png`). Every reference j
wears its own i's head (`sweep/ref_j.png`).

`J_HEAD_I` draws the j's top as the i's: `hm_head` on the j's stem top, the body's top face cut by
`hm_follow_cut` exactly as `hm_stem` cuts the i's. `J_HEAD_I_W` 1.38 starts the stem at its own
next key (58): at the j's 42 the stem flared under the head (a bulge on the right edge, a kink on
the left, `sweep/j/jw_all.png`). **Bearing:** the fit measures from the band's leftmost ink -- the nub
(lsb 20.7 I / 21.3 BI) -- and would measure from the head's tip, 73.0 / 76.5 units further left.
`J_HEAD_I_LSB` -56.2 puts the tip where the i's is (built: j -35.5 / -35.6 against the i's -35.5
/ -34.9); the stem then sits 16.8 / 20.3 units further from the letter before it, the i's own
relation; advance 227 → 243, 257 → 277. -73.0 / -76.5 would hold the stem and leave the head's tip
17-20 units closer than an i's. Moves j, ĳ, ȷ, ĵ, U+E002.

### 1.3 The italic tittle (`DOT_SCALE`; owner request)

Both axes of `ij_dot` ride ALD_WF, the stem's scale, so when the 400 moved to S 66.9 with the 0.92
nib (rounds 408-409) the dot shrank from the 86 x 87 box round 135 judged to 75 x 61. Measured on
built fonts (`instruments/tittle_measure.py`, the dot as an equivalent disc):

| | dot (units) | dot / stem | dot / xh |
|---|---|---|---|
| Albo Italic today | 66.9 | 1.12 | 0.156 |
| Albo Regular | 90.5 | 1.41 | 0.211 |
| italic references (Flanker, Pagella, Poetica, Coelacanth, Cancelleresca, Berkeley, Georgia, Times, STIX) | 74.9-127.9 | 1.16-1.69 (median 1.44) | 0.198-0.262 (median 0.221) |
| **DOT_SCALE 1.26** (the roman's dot/stem) | 82.3 | 1.39 | 0.192 |
| **DOT_SCALE 1.38** (the roman's dot/xh) | 89.3 | 1.50 | 0.208 |
| **DOT_SCALE 1.45** (the references' median dot/xh) | 96.5 | 1.62 | 0.225 |
| DOT_SCALE 1.5 | 99.9 | 1.68 | 0.233 |

Albo's dot/xh is taken at its OS/2 x-height, 429: its 'x' carries flags over the x-line (451-470
at the top), so an 'x'-top x-height -- what the first version of this table used -- read Albo 5-7%
too small an x-height and under-stated the dot by the same. The references' OS/2 x-heights are not
reliable (Poetica's reads 600), so theirs is still the 'x' top (`tittle_measure.py xheight()`).
The Italic's own lowercase stands about 1.5% over 429 (435), which does not change the ranking.

Dark pixels of the i's dot at the reader's sizes (`instruments/parts_check.py`; 1x = the X3):

| i | 8 | 10 | 12 | 14 | 16 | 18 | 8@2x | 10@2x |
|---|---|---|---|---|---|---|---|---|
| today | 1 | 1 | 1 | 3 | 2 | 4 | 2 | 5 |
| 1.26 | 1 | 1 | 3 | 5 | 6 | 6 | 6 | 9 |
| 1.38 | 2 | 1 | 3 | 6 | 6 | 9 | 6 | 11 |
| 1.45 | 2 | 2 | 5 | 6 | 6 | 11 | 6 | 13 |
| 1.5 | 2 | 2 | 5 | 7 | 7 | 11 | 7 | 13 |
| Pagella Italic | 2 | 2 | 5 | 6 | 8 | 11 | 8 | 13 |
| Flanker Italic | 2 | 3 | 4 | 7 | 9 | 11 | 9 | 14 |

No book italic passes 8-10 pt at 1x (Pagella, Flanker, Times; Georgia Italic, drawn for screens
with a large x-height and a big dot, does): a disc needs 2.4 px to own 4 dark pixels at every
pixel phase (computed), 144 units at 8 pt. `DOT_KEEP_FLOOR` 1 grows the dot upward,
the dot's floor held above the x-line (0.291 → 0.287 xh at 1.38 and 1.45). One shape note from
the review: the ruled cut facets the scaled dot to a box of 88 x 90 units at 1.38 (slightly tall;
the drawn ellipse is 104 x 93) and 106 x 96 at 1.45 -- the cut's phase, visible only at display
size. The 700 has its own
`DOT_SCALE_700`, left at 1.0: the Bold Italic's dot (1.20 of the stem) is inside its references'
1.10-1.22 and passes the parts check. **Recommended 1.38** (the roman's own proportion);
1.45 if the owner wants the references' median.

### 1.4 The acute, the tilde, the macron (`ACUTE_OPT`, `TILDE_OPT`, `MACRON_OPT`; owner follow-up "thin accents")

Drawn on the family's pen, the acute rises along the nib's own angle and comes out the pen's thin.
Mean stroke width (`instruments/mark_measure.py`, 2 x area / outline):

| | acute | grave | tilde | macron |
|---|---|---|---|---|
| Albo Regular today | 19 (0.29 S), 175 x 126 | 50 (0.78) | 26 (0.41), 185 x 63 | 27 (0.43), 172 long |
| Albo Italic today | 20 (0.33) | 56 (0.93) | 28 (0.47) | 29 (0.49) |
| Pagella / Flanker / Georgia / Berkeley (roman) | 0.64 / 0.65 / 0.70 / 0.67 | = acute | 0.58 / 0.68 / 0.61 / 0.59; 286-373 x 103-146 | 0.54 / 0.46 / 0.58; 312-335 long |
| **option b**, Regular | 50 (0.78) = the grave | 50 | 37 (0.58), 296 x 99 | 34 (0.53), 268 long |
| **option b**, Italic | 46 (0.77) | 56 | 40 (0.67), 312 x 100 | |

Every reference draws acute and grave as mirror images of one weight. Option b: the acute IS the
grave reflected; the double acute is two of its strokes at 0.80 weight spread to keep 0.60 of a
stroke of white (contour count held); the tilde is the same wave in a 0.62 x 0.44 xh box at 1.35x
the stroke (0.36 first: its ink measured 0.68 x 0.20 of the x-height, flatter than every reference,
the review's catch); the macron 0.62 xh long at 1.25x. In the italics the acute reads 46 against the
grave's 56 after the shear -- a mirrored stroke leans with the slant on one side and against it on
the other. Dark pixels of the MARK at the X3's sizes:

| | é 8 / 10 / 12 / 14 pt | ñ | ő |
|---|---|---|---|
| Regular today → b | 0 / 0 / 0 / 1 → 2 / 4 / 6 / 7 | 2 / 1 / 3 / 4 → 2 / 4 / 6 / 9 | 0 / 1 / 2 / 3 → 1 / 2 / 3 / 5 |
| Italic today → b | 0 / 0 / 1 / 3 → 2 / 3 / 7 / 10 | 1 / 1 / 2 / 5 → 2 / 4 / 8 / 12 | 0 / 2 / 2 / 3 → 0 / 2 / 3 / 6 |
| Bold Italic today → b | 1 / 3 / 4 / 5 → 5 / 7 / 12 / 15 | 2 / 5 / 6 / 8 → 6 / 10 / 15 / 19 | 0 / 1 / 3 / 6 → 3 / 4 / 7 / 10 |
| references (é): Pagella R, Flanker R, Pagella I, Flanker I | 2/4/9/9, 2/5/4/9, 4/4/6/7, 1/3/6/8 | | |

This is the accent Spanish and French books use most, and the Greek tonos composes the same mark.
Over the whole font (`parts_audit.py`, every glyph x 12 reader sizes, REC3 -- the tilde still at
0.36 -- against r435) the
accented glyphs' SMALL/FAINT-part findings fall 428 → 234 (Regular), 400 → 259 (Italic), 111 → 12
(Bold), 123 → 15 (Bold Italic); what remains in the 400s is mostly at 8 pt (159 of 234 in the
Regular, 161 of 259 in the Italic), led by the dieresis, dot accent, circumflex, caron and breve
left as they are.
63 glyphs move per cut (every acute, tilde, macron and double-acute composite, the combining forms
and the Greek tonos letters; 65 with the two braces in the same arm); advances change only for the
spacing marks themselves. The tilde keeps today's pen-cut ends, which read as small hooks at the
Bold's weight (`acc_Bold.png`); tapered ends would be a further option. **Height:** the acute b is
taller than today's, and the ĺ becomes the tallest glyph in each cut (Regular 941 → 971, Italic
957 → 984, Bold 956 → 1003, Bold Italic 969 → 1017; Ĺ 826 → 856 in the Regular). In both bolds it
passes usWinAscent 1000, which the ĥ (1002 / 1015) already does today, so the font's vertical
metrics are no worse than they were; a clip at the top of a line box would show on both. Checked and left: circumflex and caron (visible from 10 pt, narrower than the references: 192 vs 267-317
wide), dieresis and dot accent (level with the references), breve (weaker, visible).

### 1.5 The curly braces (`BRACE_OPT`; owner request "curly brackets need to work to match style")

Option a (today) is two thin cubics meeting at a shallow cusp, 0.30 xh wide: beside the references
it reads as a parenthesis with a dent (`sweep/brace/refs.png`). Option b (`symbols.py`, `_brace_b`): two
S-curves in the pen's widths -- a hook out of each end with the family's pen CUT, the shank on the
pen's thick, the turn into a beak at the middle where the two strokes taper into one point (a
closing 0.15 of the stroke wide makes the two ends one point; without it a slit ran into the tip,
seen at 3x). 0.42 xh wide, 1.28x Albo's paren (the references run 0.95-1.3x theirs). The italic
takes it sheared, as it does the parens. Dials `ALBO_BRACE_*`. Advance of each brace grows with its
ink ({ / }: Regular 254 → 310, Italic 400 → 431 / 424, Bold 270 → 309, Bold Italic 427 / 426 →
451 / 441). The tip's width (`BRACE_TIP`) is 0.18 of the stroke: at 0.30 the review found a 4.9-unit
step in the Italic } where the two strokes meet the beak. At 0.18, cmp_junctions on { } reads 0
steps in the Regular, Italic and Bold Italic and two 2.2-unit steps in the Bold (at the beak and
its mirror), under anything visible at 3x.

### 1.6 The Bold Italic e's bar (`E_BAR_K_700`; owner follow-up "the e bar breaking at small sizes")

`E_BAR_K` multiplies the widths along the bar (the arc from its start to the bar's right end, a
raised cosine out to the shoulder; the stub reads the same widths). Eye enclosed at level >= 2
(`parts_check.py COUNTERS=1`):

| | bar (units, / stem) | 8 | 10 | 12 | 14 pt 1x | 2x sizes |
|---|---|---|---|---|---|---|
| BI today | 36 (0.35) | closed | closed | closed | open | open |
| **BI K 1.25** | 44 (0.43) | open | open | open | open | open |
| Italic today | 24 (0.40) | closed | closed | closed | closed | open |
| Italic K 1.25 / 1.5 | 30 / 36 | closed x4 / closed x3 | | | | |

**Recommended: the 700 at 1.25**, the 400 untouched: its eye is too small for the bar to matter
(1.5 buys only 14 pt and puts the bar at 0.60 of the stem, over the references' 0.37-0.45); the
book italics close theirs at more sizes than Albo does (Pagella Italic and Flanker Italic: 6 of 12).
Moves e, eogonek, ae, oe (BI).

### 1.7 The Bold Italic's counters (`O_OVAL_700`, `BOWL_OVAL_700`)

At the 700 the pen's width is large against the outline's curvature, so the offset counter bends
in beside each thin point; round 270's convex hull ("for 700 and 900, counters should not have
indentations") bridges each dent with a straight chord, leaving flat sides and corners
(`sweep/ref_o.png`: the only lozenge counter among twelve italic o's). Rounding the width function's |cos|
minimum was tried first and moved nothing -- the corners are the hull's. The fix is round 204's,
which the g already takes (owner 2026-09-17, "smooth out counters to be even oval"): `PR.ovalise`
pulls the counter onto its own best-fit ellipse, the outer untouched, the wall never thinner than
0.25 S in the o (`OVAL_WALL`) and 0.40 S in b d p q (`BOWL_OVAL_WALL`). `instruments/counter_shape.py` (longest straight run on the counter, units / corners):

| BI | o | b | d | p | q |
|---|---|---|---|---|---|
| today | 177.5 / 2 | 260.4 / 3 | 94.4 / 1 | 195.1 / 1 | 95.3 / 1 |
| oval | 65.0 / 0 | 88.1 / 2 | 63.4 / 0 | 94.4 / 0 | 57.7 / 0 |

(What remains is a smooth oval's flank -- at 1.5 units' tolerance a 300-unit radius reads
straight over ~60 units -- and, in the b d p q, the stem's own edge; the b's two corners are where the counter meets the
stem.) **The bowls' floor:** at 0.25 S the review measured the b's and p's bottom walls thinned
from 47 to 33 units and the b's counter dropped into its crotch; at 0.40 the thinnest bowl wall
reads b 45.9, p 46.6, d 47.4, q 47.1 -- today's weight. The 400 dials exist
(`O_OVAL`, `BOWL_OVAL`): the Italic's b and p read 137 / 186 → 76 / 70 (measured at wall 0.25,
not re-measured at 0.40), but its counters have no
hull chords and the cut facets them anyway -- optional, not recommended. Moves b d dcroat eth o oe
ordmasculine oslash p q U+E000. The g (approved) is not touched.

### 1.8 The z's bottom left (`Z_FOOT_FILL`)

The diagonal ends on a square face across its thick foot (D x 1.52) while the bottom bar starts
there on a 14-unit hook; the face's corners stand out of the bar -- two notches in the Italic, a
three-turn zigzag in the Bold Italic (`z_foot.png`; the block in `a_z` already records "the
notch stays"). Inside a window round the foot (70 units right of it, up to 0.06 xh, which keeps the
crotch between the diagonal and the bar's top out of it) the ink is replaced by its own convex hull:
the corner's outer points stay, the bites between them go. Cutting the foot's face level was tried
first: the shear that levels it throws the face's upper corner ~36 units out along the diagonal at
the 700. The z's other STEP (top right, 8.5 / 6.3 units) is untouched.

## 2. An instrument bug: `parts_audit.py`'s faint-stroke check

The FAINT check takes each glyph's centre line as the local maxima of `distance_transform_edt(ink)`
on the TIGHT master bitmap. A flat bar fills its bitmap's height, so there is no background above
or below it inside the array and the maxima land on the TOP ROW; mapped to the reader raster, that
row is light. Verified by printing the reader's own levels: the Italic hyphen renders as a solid
row at level 2-3 at 10, 12 and 14 pt, while the audit called it 100% faint at 9 of 12 sizes. With
the bitmap padded by one pixel before the EDT (`instruments/parts_check.py FAINT=1`):

- **artifacts, now clean:** the Italic and Bold Italic dashes (were 9 / 6 of 12 sizes), both bolds'
  `=` (9), the Regular's `7` (6), `[` `|` and the other flat-topped marks;
- **real:** the comma and semicolon tails (Regular 8-9 sizes, Italic 5-6, BI 4-5), `~`, the
  Italic apostrophe (3), the Italic n and m arch hairlines (3 / 2 -- round 391's ruled 26-unit
  hairline).

`parts_audit.py` needs the same pad (`np.pad(ink, 1)` before the EDT, crop after); not edited here
(outside this pass's partition). The "faint italic dashes" follow-up needs no font change.

## 3. Found and not fixed

| what | cut | evidence | why not |
|---|---|---|---|
| c top: ramp and horn, as the 700's was | Italic | the 700's diagnosis (round 433) held for the 400 when this pass began | not this pass's letter; the main agent drew it in round 436 (arm E1, on by default) while the pass ran |
| s foot: a flat spike whose point dips below the baseline; top a flag | Italic, BI | ink bottom -24 (I) / -36 (BI) at xh 429 against every reference's -8 to -16 (Poetica, Coelacanth, Flanker, Pagella, Berkeley, Georgia, two bolds); its leftward reach, unsheared, 24 / 2 units, is inside theirs (0-27) -- the "long" look is the shear. The references end the lower bowl in a ball curling up or a vertical cut, `sweep/ref_s.png` | the s's ends are ruled (rounds 208, 283, 284); a drawn foot is a design choice for the owner |
| pointed terminals sink past the round letters' overshoot (o c e -16 since round 435; font units, not the s row's xh-429 scale): ink bottom s -27, k -23, t -21, z -20, x -19 (Italic); s -40, k -33, z -32, t -31, x -28 (Bold Italic); k -22 / -35, x -22 / -32 in the romans | all | TTF bounds, r435 (round 436 moves only the 400 Italic c) | the s is the outlier (above); the rest are the family's wedge tips; recorded as a measured survey, nothing moved |
| v w y top-right terminal: a flag ~12 units over the x-line | Italic, BI | references hook or drop (Berkeley alone draws this wedge), `sweep/ref_v.png`, `sweep/ref_y.png` | reads as the family's cut wedge; far milder than the r |
| x top-right: a rising flag (ink 457); small notches where the finials meet the strokes | Italic, BI | `sweep/zoom/x_Italic.png`, `sweep/ref_x.png` | same family as the r; a drawn terminal would be the fix; not attempted |
| b d p q bowl-to-stem crotch spur at the counter's lower left | BI | `sweep/o/bowls_ab.png`, both arms | round 343's crotch closing; pre-existing |
| BI e: a knob at the eye's shoulder | BI | `sweep/zoom/w_set2.png` | minor |
| figure joins: 3 and 5 tail-to-bowl bumps, 5 stem knob, 1 flag notch, 6 STEP 5.3 at (165,221) | BI | `sweep/zoom/w_figs.png`, cmp_junctions / cmp_jogs | figure options are ruled per digit (`FIG_SHIP_*`) |
| : ; ! ? dots 1-3 dark px at 8 pt | R, I | parts_check; Pagella, Flanker, Times italics the same | 144 units needed at 8 pt; over round 380's italic mark ruling |
| the 400 e's eye closes at 8-14 pt | R, I | §1.6 | the eye's size, not the bar; references close at more sizes |
| roman u bowl-to-stem joint; n arch STEP 2.0 | R, B | `sweep/zoom/w_set1.png` | the u's is the family's joint; 2 units |
| g connector knobs, ear notch | BI | `sweep/zoom/w_set3.png` | approved glyph |
| d: the stem's flat top stands 6-7 units above the end of the head's top edge -- a step at the very top of the ascender (the b shows a smaller one, under cmp_junctions' threshold) | Italic, BI | `sweep/zoom/dheads.png`, `sweep/zoom/heads.png`; cmp_junctions d STEP 6.0 (I) / 7.0 (BI) at (484-506,783) | `bd_head`'s end height against the stem top; small, visible at display size; not attempted |
| the k's head is `st()`'s generic slab flag -- not the h/l's `hm_head`, nor the b/d's `bd_head` (the italic ascenders wear three different heads); the Italic k's stem corner stands proud of it on the right, and the Bold Italic's head has a step in its top edge (cmp_junctions STEP 8.1 at (211,769)) | Italic, BI | `sweep/zoom/kheads.png` (l beside k) | the k's block records the choice ("drawing the k its own head would make one ascender disagree with the other four") on a premise that no longer holds; the k's stem is `st()` with a foot, so the j's fix does not carry over as is -- the next candidate for the same treatment |
| the straight double quote `"` is still the pre-round-404 parallel stroke: two heavy parallelograms beside the ruled `'` pen wedge ("j wins") | Italic, BI | `sweep/base/quotes_all.png` (the romans' pair is consistent) | the existing `ALBO_APOS_DOUBLES=1` makes the doubles follow the singles -- but it also gives the curly doubles the apostrophe's 0.85 head, in every cut; not built here, the owner's call |
| with `R_DRAW_700` the Bold Italic r's DESIGN outline has a 167.5-degree spike at the crotch where the drawn arm leaves the stem; the TTF's despike removes it (137.5 degrees there, no hair finding) | BI | the review, on the live outline; `cmp_contour_hairs` clean on the TTF | harmless in the font as built; recorded because a builder change to the despike would expose it |
| with `J_HEAD_I` the ĵ's circumflex moves: the new head reaches left, and the mark follows the ink, 24 (I) / 19 (BI) units left while the body's box moves 9 / 21 right | Italic, BI | TTF contour bounds, r436 vs REC4; `j_I.png`, `j_BI.png` (reads centred over the head at display size) | the composite's placement rule is the accents builder's; judged by eye only, not measured against a reference |

## 4. Checked and found CLEAN

- **Default builds** of all four cuts byte-identical to r436 (outlines and advances), final tree.
- **Every arm** passes poor_gates: alone for the r, the j, the dot, accents + braces, the e 700 and
  the ovals (on the r435 baseline, before round 436, which does not touch any of them); all
  together (REC4) on r436, the z included.
- **The adversarial review** (a read-only agent, 2026-09-28) tried to refute each fix. What it
  found and what came of it: the bowls thinned at wall 0.25 (fixed, `BOWL_OVAL_WALL` 0.40); the
  Italic } step (fixed, `BRACE_TIP` 0.18); the tittle table's x-height bias (fixed in the
  instruments, table re-measured); a stale r table (re-measured); the flat tilde (fixed, `TILDE_H`
  0.44); dials `gen_state.py` could not see because their names were built in a helper (rewritten
  as literal `os.environ.get` calls); `R_DRSB` reaching the r when `R_OPT` is `a` (gated); two
  copies of the j's tables (one). What it checked and found CLEAN: every diff hunk gated (at the
  defaults the `keyed_ring` calls and the bearings are unchanged); default identity byte for byte
  in all four cuts on both `9333452` and `7f24b9c`; hairs clean at tighter thresholds too (turn 150,
  hair 140 degrees); the junction steps §1 says are cleared are cleared (r 4.5; ĳ 10.8 → 1.9; BI j
  ȷ ĳ ĵ 4.0; z foot 8.4) and the z's top-right step untouched; BI counter dents 0 → 0; the approved
  Italic and Regular g untouched; the fj ligature (U+E002) does not collide with the new j head. It
  reproduced the r and j advances and bearings, the tittle rows, the reader-size tables, the stroke
  measurements, the counter table, the brace advances and the moved-glyph counts.
- **No leak across styles**, measured in REC4's moved lists: the Regular and Bold move only the
  accents and braces (the builders the romans share); every aldine.py change moves italic glyphs
  only. No Regular contour count changed, so no `PHASE_LEGACY_STYLE` entry is needed.
- The **f hook** (Italic, BI): the inner corner is the face's own corner; the TTF's sharper counter
  corner is the ruled cut's facet (`sweep/zoom/f_hooks.png` vs the live outline). A lower floor /
  longer swell smoothed the dense outline slightly and was removed as not worth a dial.
- **Italic and BI dashes** render solid (§2); hyphen thickness 40 (I) / 37 (R) units, 0.66 / 0.58
  of the stem, inside the references (Flanker I en dash 0.65, Pagella I 0.71, Georgia I 0.66).
- The **Bold's and Bold Italic's dots** (i j : ; ! ?) pass the parts check (BI j and ? at 8 pt
  aside); the BI i dot/stem 1.20 is inside its references' 1.10-1.22.
- The **grave** (0.68-0.93 of the stem), **dieresis** and **dot accent** sit with the references.
- The **Italic e bar** relative to its stem (0.40) is inside the references (0.37-0.45).
- The **italic y fork**: covered by `docs/albo-y-fork.md`, not re-measured.
- The **400 Italic o counter**: slight facets from the cut, no hull (hull is 700-only).
- **Accent placement**: composites keep their base's advance; contour counts of every changed
  glyph unchanged in all four cuts.

## 5. How sure

- Measured on built fonts and verified by eye at 3-4x with vertices: §1 all, §2, the counter
  table, the r and j spacing numbers, the reader-size tables.
- Measured against references with the same instrument on both: the tittle, mark weights, e bar,
  pair gaps. Reference ranges are over the fonts named; other faces may fall outside them.
- Inferred, not measured: that the owner will prefer R_DRSB 0 over a split; that the 400 bowl
  numbers at wall 0.40 are like those at 0.25; that the 400's e eye
  cannot be saved by the bar alone (1.5 was the largest arm tried).

`docs/albo-STATE.md` is regenerated in the commit that lands these dials: it lists the new dials
at their defaults, and the rest of its diff is line numbers moving. `gen_state.py --check` read
current before the commit and reads OUT OF DATE after it on one line only -- the header's "Read
from ... at `<hash>`", which names HEAD and so can never match the commit that contains it (the
file at `7f24b9c` named `9333452` the same way). The tables are current; the check's
self-reference is a gen_state.py quirk, not touched here (outside this pass's partition).

## 6. Instruments added (`tools/wedge_serif/instruments/`)

`sweep_sheet.py` (glyph sheets from built fonts), `ref_row.py` (one glyph across fonts at one
x-height, char on the command line), `ttf_zoom.py` (a built glyph at any zoom, vertices dotted,
optional overlay), `live_zoom.py` / `live_view.py` (the live builder, any glyph / any vertical
range), `band_extent.py` and `ttf_band.py` (what the italic fit reads, live and built),
`tittle_measure.py`, `mark_measure.py`, `bar_measure.py`, `counter_shape.py`, `parts_check.py`
(parts_audit's checks as a per-size table; FAINT with the pad fix), `pair_gap2d.py` (shaped
closest approach + row white), `sweep_proof.py` (display + reader-size before/after rows).
