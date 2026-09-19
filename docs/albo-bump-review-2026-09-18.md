# Adversarial review -- Albo roman bump fixes, uncommitted diff over 9c43b77 (2026-09-18)

Read-only. Nothing tracked was edited; no mutating git command was run. One side effect of mine:
`python3 -m outlines.build --help` is NOT a help flag -- the builder took `--help` as OUTDIR and wrote
`tools/wedge_serif/--help/Albo-Medium.ttf` into the repo tree; I deleted that directory (mine, untracked).
The pre-existing untracked `tools/wedge_serif/--out/` in `git status` is the same mistake made earlier by someone else.

Instruments (all under `$SP/review/`): `head/` = `git archive HEAD` of tools/wedge_serif, built to `head_rom/`
(diffglyphs vs r232_rom: 0, so r232 IS HEAD); `difflist.py`; `symdiff.py` / `geoprobe.py` / `rendercrop.py`
(TTF-level symmetric difference, r=6 and r=1.5 opening/closing, before|after crops at 5 px/unit with vertices,
in `crops/`, `crops2/`, `crops_it/`); `rawdump.py` + `cmpraw.py` + `clusters.py` (PRE-FIT polygons from
`build.draw()` in both trees, `raw_head_*`/`raw_new_*`, compared exactly); `archchords.py`; `efloor.py`;
`bumps_head/`, `bumps_new/` (the owner's `albo_bumps.py` on both builds); `touch_*.txt`, `space_*.txt`.

## Findings, most severe first

### F1. Two design departures beyond the named ask, in the default build -- owner's call before this lands
Severity: silent-wrong-output IF the owner did not want them; both are flagged in the agents' reports, but a
reader of the diff alone would not see either as a choice.
a. THE ROMAN ARCH TRAP IS OFF. glyphs/arches.py `N_TRAP_DEPTH = float(os.environ.get("ALBO_ROM_N_TRAP", 0.0))`
   removes the ruled notch from n h m (module docstring, still in the file: "the inner edge leaves the stem at
   0.52 xh with a trap notch"). The comment's justification "the round's brief rules out a notch as such" is the
   caller's COMMON.md rule about DEFECTS, read as a design ruling. Verified: the old trap really was a sealed
   speck -- HEAD n at y=200 has ink runs (2.0,81.0) and (83.4,86.1), an enclosed 2.4-unit hole inside the stem
   (`archchords.py`) -- so "leave it" was not available; "re-aim it" was (the re-aimed apex is still in the code,
   gated off). Owner asked only to "slightly reduce the weight of the joins" (R27/R29).
b. THE W CROWN AND THE w CROWN ARE NOW FULLY EXPOSED AT THEIR RULED SIZE. Raw diff W: +588 u2 in
   (381,584)-(422,648); w: +1,325 u2 in (196,354)-(278,413). The 2026-09-13 ruling "lower and reduce the
   protuberance of the top middle connector in W" was judged on the buried spur (`crops2/W_420_560.png` BEFORE);
   AFTER shows a 39x79 wedge with a long bracket; same on the w (`crops2/w_240_300.png`). The caps agent rendered
   `wcrown.png` for a ruling. Nothing about the crown's size was edited -- it is a consequence -- but it is the
   largest visible change in the caps.
Same list, smaller: the a's hood is the stem's width through the turn (f0 / A_HOOD_W: +472 u2, ink +0.5%, partly
undoing round 94's "slightly reduce the top stroke of 'a'" over the first third); the 9's tail body moved by
~19 units on average (6,415 u2 removed / 4,576 added -- a redraw, which R43 asked for).

### F2. Three new option dials crash the build on an unknown letter
Severity: latent. Verified by building with `=z`:
- glyphs/arches.py:256 `R_THIN_OPTS[R_THIN]` -> KeyError ('ALBO_ROM_R_THIN=z')
- glyphs/arches.py:203 `{'a':..,'b':..,'c':..,'d':..}[M_MID]` -> KeyError ('ALBO_ROM_M_MID=z')
- glyphs/caps_straight.py:768 `{...}[Q_TAIL_OPT]` -> KeyError ('ALBO_ROM_Q_TAIL_OPT=z')
Every other new dial falls through to today's drawing (G_BAR, A_OPT, F_BAR, DOT_PUNCH, QUOTE_OPT, HYPHEN_OPT,
AMP_OPT); `figures.OPT()` still maps unknown letters to 'a' (`ALBO_FIG_SET=z` builds all ten figures;
`ALBO_FIG_SET=h` builds roman AND italic, the italic drawing 'a' where its table has no row).

### F3. The four marks.py dials are un-prefixed and reach the italic when set
Severity: latent, no effect at default. ALBO_DOT_PUNCH (meant for both), ALBO_QUOTE_OPT, ALBO_HYPHEN_OPT,
ALBO_AMP_OPT have no pen.ITALIC gate; the italic ' " - & are marks.py's own glyphs (no @glyph('&') in aldine.py).
All four RAW IDENTICAL in both styles at default. A winner chosen by env moves both styles -- decide per style.

### F4. The owner's own bump detector: net -2 circles roman, +1 italic
Severity: cosmetic, but it is what the next markup sheet will show. albo_bumps.py HEAD -> merged: roman 213 -> 211,
italic 215 -> 216.
- Gone (roman): 1 flick spur; 9 crotch notch; one join speck each on h and m.
- New (roman): N spur (789,652) = the requested microserif tip (R11, expected); @ notch (563,472) 74.6 deg = the
  crotch where the cut-top spike meets the ring -- the owner's OWN box for R57, deliberately left alone; the stem
  moving 8 units left changed that crotch's angle enough to trip the detector (`crops2/at_490_420.png`).
- New (italic): ? spur (135,184) 99.7 deg = the descent's inner corner on the new pen-cut face
  (`crops_it/question_60_100.png`). The roman ? is not flagged; the shear sharpens the corner. The italic ? had
  no write-up (I124 blank) and now carries a circle it did not have.
- The e's counter floor (R19) is no longer a 3.5-unit STEP but a +/-2-unit WAVE in the raw polygon (`efloor.py`:
  HEAD 35.3 -> 38.2 jump at x 216-222; NEW 37.8 -> 40.2 -> 38.1 over x 204-270; TTF 38 -> 40 -> 38): the tail shedding
  the 0.92 thinning over its first 35% while the outer edge is at its minimum. Under the detector's threshold (e's
  count unchanged); reported because "correct curve" was the ask and a wave replaced the step.

### F5. Every pair ending in 4 tightened 3-10 units; none near the floor
Severity: for the record. cmp_space_2d.py --pairs HEAD -> merged: 14 0.041->0.037, 24 0.058->0.055, 34 0.054->0.050,
44 0.044->0.041, 54 0.053->0.050, 64 0.105->0.095, 74 0.175->0.167, 84 0.097->0.088, 04 0.112->0.103, z4 0.033->0.030
(tightest), s4 0.106->0.097, x4 0.074->0.066, a4 0.063->0.059; 94 LOOSENED 0.109->0.120; every 4X pair unchanged.
Class digit+digit 0.095 -> 0.094. Cause: hmtx (457,8) -> (454,6) plus the diagonal's top moving ~10 left. The solver's
W dict from a HEAD build vs merged differs ONLY in '4': 0.88 -> 0.90. cmp_touch: the same 4 TOUCHING (ff fi fT f-paren),
6 under floor, 14 exempt; moved rows: ff -0.0198 -> -0.0212, fT -0.0051 -> -0.0036, fl -0.0725 -> -0.0739 (the f's hook
tip), exempt Q4 -0.2447 -> -0.2504. Nothing new touches.

### F6. Attribution wording in two new comments
Severity: cosmetic. caps_straight.py header "it was ruled byte-identical for this round" -- COMMON.md's instruction
(the caller's), not an owner ruling; arches.py "the round's brief rules out a notch as such" (F1a). Every other quoted
2026-09-18 owner line in the nine files matches docs/albo-bump-markup-2026-09-18.md verbatim (R43 "treat the inside
join. too." is quoted with a comma). diagonals.py's "the guide's rule -- bury the thin a fifth to a third" is real:
docs/fjord-glyph-guide.md:297-300.

### F7. Sub-unit drift on the whole 3
Severity: cosmetic. g_three re-resamples both bowls from the new waist point T, so the raw diff is 320 u2 in 115
pieces along BOTH bowls (0.1-0.2 units) and the advance rounded 408 -> 407. "What did NOT move: both bowls' shapes"
is true to 0.2 units, not to the byte.

## Disproved candidates
- Italic s looked like a leak at the TTF level (1,127 u2 along the whole spine, lsb -2 -> 0, advance +1). RAW: 180 u2
  in exactly two regions, (54,-31)-(158,58) bottom-left ball 146 u2 and (265,345)-(333,395) top-right ball 34 u2. The
  spine is untouched; the TTF wobble is fit_aldine's dx = lsb - l moving a fraction (raw leftmost 54.4 -> 55.2) and the
  integer fit re-rounding every vertex. Same for the italic ! strips. NOT a leak.
- r=1.5 closing pieces remaining after the fixes (M counter tips 7 u2, 4 counter apex 6 u2, w crotch 2-5 u2, v crotch
  4 u2) are acute counter tips; identical pieces exist in HEAD at the same places.
- The new r=6 spur on the f at (409,705)-(412,713), 5 u2, is the hook's own pen-cut corner (identical shape before and
  after; the tip moved ~1 unit so the piece crossed the 2 u2 print threshold).
- `_half_bowl_flat` docstring says widths are "the primitive's own" while the code widens by dw/2 -- the algebra checks:
  outer edge = center - wfull/2 (flat), counter edge = center + wfull/2 - dw/2 = the primitive's exactly. Raw B/D diffs
  confirm: only 1-3-unit strips on the OUTER edges (B 36+67+22 u2, D 100+100 u2), 1.4-1.8 u2 of dust on the counter side.
- arch_geom's changes are NOT pen.ITALIC-gated, but nothing in the italic reaches it: aldine.py registers its own n h m,
  italic.py has its own italic_arch, ligatures.py does not import arches, and the italic TTF diff has no n/h/m/hbar/eng.

## Per-area CLEAN list (what I ran, what came back clean)
1. ITALIC LEAKS. TTF diff r234 -> r235: 54 glyphs, all in {c, s, stops, quotes, ?, @, dot-bearing symbols (ellipsis
   dieresis dotaccent periodcentered bullet uni2219 divide uni0326 cent exclamdown questiondown), fi/ffi (the i's dot,
   ligatures.py:38), composites of those}. Raw pre-fit polygons compared for c s . , : ; ! ? @ ' " - &: c only in its two
   ball regions (84 + 16 u2), s only in its two (146 + 34 u2), ' " - & RAW IDENTICAL, ? and @ carry exactly the roman's
   raw diff (4,466 / 4,865 u2 -- shared constructions). No other italic glyph moved.
2. OPTION DIALS AT DEFAULT. Byte-identical at default confirmed RAW for 2 (TWO_OPT d/e/f), ' " - &; by TTF diff for Q
   (Q_TAIL_OPT), 8 (EIGHT_OPT e/f/g), C. Default paths for G_BAR ('a' = the old bar call), R_THIN ('a' = (R_FLOOR,
   R_FLARE)), M_MID ('a' = (0.85,0.85), the fix), A_OPT/F_BAR/DOT_PUNCH ('a' = the fixed drawing) read as claimed.
   `_okw(d, rom, it)` picks the *_IT table in the italic and `.get(OPT(d), {})` never raises. Exception: F2.
3. ARCH TAPER. archchords.py on the raw n: join region (x 82-161, y 195-340) thinned 5.7-7 units per row, HEAD's
   hole at y=200 gone; above the join the vertical chords over shoulder/top change +0.7 (x=160), +0.3, +1.2 (x=200),
   +0.6, +0.1, +0.6, +0.2, +0.1 -- "within a unit above y 340" holds to 1.2 units, sign slightly HEAVIER. The u is
   untouched (g_u still calls pen_widths; not in either diff).
4. GEOMETRY CLAIMS. Crops at 5 px/unit before|after (crops2/): M crown (one flat from the corner, the 4.5-unit step
   gone), M right apex, M middle vertex (one flat on the baseline), W apex (peaks and dip gone, one flat), B bottom
   (2-unit step gone), f hook (stem corner and 4.9-unit inset gone), 9 root (17-deg re-entrant turn gone), 4 apex
   (ledge gone, corner-to-corner) and 4 bar-left (9-unit tooth gone), w apex, v vertex, n join, G beak (one straight
   cut, bracket tangent), S terminal (Z-kink and face zig gone), e bottom (F4). Opening/closing r=6 on M W B f 9 4 w v
   3 R: every BEFORE defect piece the agents named is absent AFTER (M spike above cap 8 u2, M vertex below baseline
   8 u2, W crown spur 9 u2 + notches, f stem corner 7 u2 + notches, 9 crotch 32 u2, v prong 8 u2, w spur 18 u2, R tooth
   7 u2 + notch, B corner steps 3 u2 x4); every remaining piece is a family wedge tip (40-50 u2 in 13x11), a foot
   micro-serif (8 u2) or an acute counter tip. No step, notch or spur above a unit remains in the crops.
5. THE 4. F5; the W dict differs only in '4'; no new touch.
6. primitives.py. git diff: one hunk `@@ -676,15 +676,64 @@`, the DOT_STYLE block and dot() only. Every caller is
   `dot(cx, cy, r)` (marks, stems, symbols, symbols2, accents, ligatures, italic, aldine's PR.dot(x, y, r0/r1));
   aldine's ij_dot does not call it; `k` is passed by nobody. Roman kern identical; cmp_space_2d classes HEAD -> merged:
   stop+letter 0.143 -> 0.141, quote+letter 0.196 -> 0.195, digit+digit 0.095 -> 0.094 (the 4), other five unchanged.
7. INVENTED RULINGS. Every dated quote verbatim against the markup doc; only F6's two attribution slips.

Unchecked, and said so: the option-letter fonts' geometry beyond "they build"; the italic c's pre-existing
ball-to-stroke notch (per the marks report); the 13 px word-image reads (the agents' PNGs, not re-rendered).
