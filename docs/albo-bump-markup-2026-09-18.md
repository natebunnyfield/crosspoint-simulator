# Albo bump markup — the owner's yellow regions, indexed (2026-09-18)

**What this is.** After the recalibrated bump sheets (`albo_bumps.py`, commit
`0eced05`), the owner marked both styles' sheets in yellow — every region that
needs a fix, whether the instrument had circled it or not — and said: *"each
yellow region has one or multiple issues I have identified and want to write
up the issue."* This file is the index those write-ups hang on: one row per
yellow region, **R01–R57 roman, I01–I127 italic**, read off his four marked
half-sheets by eye (display coordinates of a 2000-px view, mapped back through
the sheet's cell geometry, then snapped to the nearest ink where the reading
missed the outline — 62 of 184 needed the snap, which is the measure of how
loosely an eye reads a coordinate off a screenshot: ±20 px, ±100 units).

The crops are on the artifact page (one per region: the built outline at up to
3 px/unit, vertices as dots, the read box in yellow, the sheet's own circle
numbers in red). Regenerate with `tools/wedge_serif/markup/render.py` (needs the
two shipped TTFs and the sheets' JSON indexes in the scratchpad paths named at
its head) and `page.py`.

**"My reading" is what I found in the geometry before his write-up** — filled
in where a region was zoomed and measured, left as a class name or blank where
it was not. His column is authoritative; mine is a first guess to be corrected.

## What the zoomed regions have in common (roman, before the write-up)

Six construction classes account for every roman region that was measured:

1. **Two stroke ends meeting at a point without a miter** — the M's crown spike
   (10 units over the cap line), the M's middle vertex (a notch and a spur, 15
   units of jag), the W's middle apex, the v's vertex, the K's arm and leg at
   the stem (a 4-unit notch, an 8-unit spur). The M and W fixes (`flat_face`,
   `flat_corner`, `crotch_blunt`) are documented in `caps_straight.py`'s own
   comments and are NOT in the code: they went with the round-81 caps revert
   ("leave K R Q M W as is, before agent was better").
2. **A curved stroke meeting a straight one off its line** — the f's hook
   starts 6.7 units inside the stem edge; the j's tail 8 units; the U's bowl
   bulges 4 units past the stem; the a's arch meets its stem at 40° with a
   ledge; the h's arch inner edge jogs 10 units; the e's counter floor steps 4;
   the B's and D's bowl bottoms rise 2–3 units before the stem because the ring
   is past its tangent when it gets there.
3. **A stroke end left standing where it should be buried** — the R's 7-unit
   tooth on the counter floor (the bowl's lower end face crossing the stem
   edge), the G's spur.
4. **Terminals that run to a needle** — the c's upper terminal (the inner edge
   goes vertical for 12 units into a 102-unit straight cut face), the S's top
   terminal (plus a 6-unit Z-kink where two pieces of spine overlap), the G's
   beak.
5. **Serif pieces not flush with the stroke they sit on** — the M's and w's
   crown wedge 4.5 units below the diagonal's flat top; the L's inside corner,
   where the stem's entasis flare meets the arm as a 2.3-unit angle.
6. **The dots are 11-gons.** `primitives.dot` at `DOT_STYLE` 1 draws
   `12 - style` = 11 sides (the owner's 2026-09-14 pick from a "handcut" ladder
   judged at 54 px); at a 300-px cap the facets read as a glitch, on i j . , :
   ; ! ? alike. With `HAND_SCALE` at 0 the style's jitter is already zero, so
   the facet count is the only thing the style still does.

And one class that is the italic's: **every italic stem is swayed** — round
180's `ENT_CAP_SWAY` (4 units), `ENT_SWAY` (3) and `ENT_DIAG_SWAY` (4), an S
laid along every capital stem, lowercase stem and capital diagonal so that no
run of outline is straight. That is what the owner's full-length marks on the
italic H K L N P R T Y b h l are, and it is NOT the hand table round 231 zeroed
(`ALBO_HAND_SCALE`): a second, separate source of wave.

## Roman

| id | glyph | region | my reading (correct me) | owner's write-up |
|---|---|---|---|---|
| R01 | `A` | left leg at the crossbar | no notch found at 6 px/unit: crossbar top/bottom meet the thin leg cleanly; thin leg straight. UNEXPLAINED -- say what you see |the outside edge is slightly funky and distracting |
| R02 | `B` | lower bowl meets the foot | bowl bottom edge rises 2.3 units over its last 30 units before the stem: the ring is past its tangent point when it reaches the stem (half_bowl); wants a flat from the stem to the tangent |straighten, no fracture |
| R03 | `D` | bowl meets the foot | same as R02, 3 units |straighten |
| R04 | `G` | arc terminal (19) | the beak: a 2-unit jog on the cut face and a needle tip -- the arc thins to a point where the cut face meets the inner edge |make it one cohesive serif, not overlapping |
| R05 | `G` | the bar | a keystone: both ends pen-cut the same way so the bar is 180 wide at its underside and 145 at its top; overhangs the spur 69 left / 22 right; underside sits on the spur with two steps |give me other options with more calligraphic treatment |
| R06 | `K` | arm and leg meet the stem (36/37) | arm: a 4-unit triangular notch where its lower edge meets the stem 7 units below the stem-edge turn; leg: its cut end pokes 8 units above its own upper edge (a spur) at the stem |I did not highlight this |
| R07 | `L` | inside corner (40) | the stem right edge kinks 2.3 units outward over the last 100 units above the arm -- the entasis flare meets the arm as an angle, not a bracket |use the same treatment as B D and other similar joints |
| R08 | `M` | top-left crown (48) | the crown wedge top edge ends 4.5 units below the diagonal flat top: a step at x 124 |make cohesive and straightened |
| R09 | `M` | top of the right stem | the thin diagonal cut end stands 10 units above the cap line as a spike (the documented flat_face fix is not in the code -- reverted with round 81) |make cohesive and straighten |
| R10 | `M` | middle vertex | two cut end faces cross: a notch between them and the thin stroke corner pokes 8 units right; the bottom spans 15 units of height (-13 to +2). Same missing fix as R09 |remove small overlapping triangle on right |
| R11 | `N` | top-left of the right stem | a bare square corner: top=right gives that stem a serif on the right only; the H right stem has both |add a microserif on left inside of top right stem |
| R12 | `Q` | tail (58 + its length) | tail leaves the bowl bottom-left and runs under it with a thin white sliver between (the notch at 58); its edges are 11-unit facets along a 700-unit stroke |give me more options that are less distracting with the bulge placement and size |
| R13 | `R` | bowl/leg junction (63) | a 7-unit tooth stands up from the counter floor where the bowl lower stroke end face crosses the stem edge; the leg top edge meets the bowl underside with a notch (63) |remove tooth from counter |
| R14 | `S` | top terminal (64) | a 6-unit Z-kink on the outer edge two thirds down the terminal (two pieces of spine overlap), a 3-unit zig on the cut face, and a needle tip: the last 12 units taper to nothing |make cohesive and without any kink |
| R15 | `U` | left stem into the bowl | the bowl outer edge bulges 4 units left of the stem line where the ring starts (its leftmost point is not on the stem edge): a knee |correct shitty joins |
| R16 | `W` | middle apex (81/78) | jagged crown: a spur left at 629, peaks at 686 and 692 with a dip at 678 between, and a step on the right; the documented flat_face/crotch_blunt fix is not in the code |despur entirely |
| R17 | `a` | shoulder | the arch outer curve meets the stem right edge at ~40 degrees off vertical with a 3-unit ledge: a corner on the shoulder |remove corner on shoulder, also give me an option that reduces visual imbalance in bottom right and options for a top left serif where the corner was |
| R18 | `c` | upper terminal (100) | a needle: the inner edge runs vertical for the last 12 units and meets a 102-unit straight cut face at 20 degrees; a 2-unit jog on the cut face |despur |
| R19 | `e` | lower stroke / terminal (104) | the counter floor steps up 4 units at x 257 where the tail stroke takes over from the ring; the terminal tip beyond |correct curve |
| R20 | `f` | hook leaves the stem | the hook outer curve starts 6.7 units inside the stem left edge at y 634: a step |remove corners on both sides |
| R21 | `f` | bar, left end | plain rectangle end, 41 units past the stem, square |give me options for slightly calligraphic treatments |
| R22 | `f` | bar, right end | square end 106 units past the stem; one level bar (403-447) |give me options for slightly calligraphic treatments |
| R23 | `h` | arch inner edge (114) | a 10-unit jog on the counter top at (241,401): the shoulder stroke inner edge and the arch inner edge do not meet |correct weird thin bending |
| R24 | `i` | the dot | an 11-gon (dot() at DOT_STYLE 1: 12-1 sides), asymmetric |replace lines with more metal punch inspired treatment |
| R25 | `j` | the dot | same 11-gon |same R24 |
| R26 | `j` | tail (118) | the tail outer edge starts 8 units inside the stem right edge at y -188: a step; the tip a 12-unit blunt face |remove corner from bottom right (outside of what you highlighted, but within what I highlighted) |
| R27 | `m` | first arch inner edge | class of R23: the arch inner edge jog where it springs |I did not highlight this, I wanted to slightly reduce the weight of the joins |
| R28 | `m` | feet of the 2nd and 3rd stems (133/135/131) | the 0.66-xh stems feet under the arches |reduce the interior serifs slightly and give me options for the middle stem |
| R29 | `n` | arch inner edge | class of R23 |same as R27 |
| R30 | `n` | right stem foot (143) | the foot under the arch |same as R26 |
| R31 | `r` | stem, right side, top to bottom | the arm leaves the stem; the trap notch at 0.52 xh; the foot |THIS IS NOT WHAT I HIGHLIGHTED. remove burr on right side of stem, give me options for thinning out the right side for word image legibility |
| R32 | `v` | vertex (162) | two cut end faces meeting at the baseline, class of R10 |THIS IS NOT WHAT I HIGHLIGHTED. improve the heavy join. |
| R33 | `w` | top-left serif to first apex | class of R08: the crown wedge on a diagonal top |correct join to be without corners and overlapping bullshit |
| R34 | `1` | flag (189) | the flag stroke |remove errant flick |
| R35 | `1` | feet (186/187) | — |give me options for improved 1 |
| R36 | `2` | spine | the diagonal from the bowl to the base |NOT HIGHLIGHTED. give me options for improving the diagonal and join in bottom left |
| R37 | `2` | base, left end (190/191) | — |same as R36 |
| R38 | `3` | waist | where the two bowls meet at the left |NOT WHAT I HIGHLIGHTED. redo middle stem |
| R39 | `4` | apex (194) | diagonal meets the stem at the top |correct bad join in counter where I highlighted, not what you highlighted |
| R40 | `4` | bar, left end (197) | — |correct bad join on middle left, not what you highlighted |
| R41 | `6` | top terminal (200) | — |correct end of tail and give me options to choose from |
| R42 | `8` | the whole 8 | — |redo entire character to match the rest, give me options |
| R43 | `9` | right side into the tail (206) | class of R15: bowl to tail |NOT WHAT I HIGHLIGHTED. redo bottom and middle right side of loop. treat the inside join. too. |
| R44 | `.` | the dot | 11-gon (R24) |same R24 |
| R45 | `,` | head and tail (207) | 11-gon head; the tail stroke |same R24 |
| R46 | `:` | both dots | 11-gons |same R24 |
| R47 | `;` | dot and comma (208) | 11-gons; the tail |same R24 |
| R48 | `!` | the dot | 11-gon |same R24 |
| R49 | `?` | terminal | — |fix stray corner in bottom right of stroke, fix bad bulge on left |
| R50 | `?` | the dot | 11-gon |same R24 |
| R51 | `'` | the mark (209) | a straight stroke with one pen cut |give me calligraphic options |
| R52 | `"` | both marks and the line between (210/211) | — |same R51 |
| R53 | `-` | the hyphen | a plain bar, square ends |same R51 |
| R54 | `&` | upper loop | — |give me options that fix the unattractive lumpy and droopiness |
| R55 | `&` | right leg / terminal (212) | — |R54 |
| R56 | `&` | bottom-left foot | — |R54 |
| R57 | `@` | inner a / tail end (213) | — |NOT WHAT I HIGHLIGHTED. fix overthickness in middle, right of interior strokes |

## Italic

| id | glyph | region | my reading (correct me) | owner's write-up |
|---|---|---|---|---|
| I01 | `A` | apex (3) | two diagonal cut ends meeting; the apex serif | |
| I02 | `D` | bowl top meets the stem (11) | — | |
| I03 | `D` | bowl bottom meets the stem (10) | — | |
| I04 | `E` | top arm, right end (14) | the pen cut plus the hanging wedge: the double facet with a ledge | |
| I05 | `E` | middle arm | its cut end: a tooth under the arm end | |
| I06 | `F` | top arm, right end (17) | as I04 | |
| I07 | `F` | middle arm | as I05 | |
| I08 | `G` | the bar | as R05 | |
| I09 | `G` | spur meets the bowl (21) | — | |
| I10 | `H` | both stems, full length | the round-180 S-sway (ENT_CAP_SWAY 4 units) on every capital stem; visible bend at the crossbar | |
| I11 | `J` | tail end (34) | — | |
| I12 | `K` | stem, full length + junction (36) | sway (I10); arm/leg meet the stem | |
| I13 | `L` | stem, full length | sway (I10) | |
| I14 | `M` | top-left (50) | — | |
| I15 | `M` | right junction (46) | — | |
| I16 | `M` | middle vertex (52) | — | |
| I17 | `N` | both stems and the diagonal | sway on all three (ENT_CAP_SWAY, ENT_DIAG_SWAY) | |
| I18 | `P` | stem, full length | sway | |
| I19 | `P` | bowl top meets the stem (60) | — | |
| I20 | `Q` | tail root (63) | — | |
| I21 | `R` | stem, full length | sway | |
| I22 | `R` | bowl / leg junction (65) | — | |
| I23 | `S` | top terminal (70) | — | |
| I24 | `S` | bottom terminal (69) | (faint mark -- confirm) | |
| I25 | `T` | stem, full length | sway | |
| I26 | `T` | bar top, over the stem | — | |
| I27 | `V` | vertex (80) | — | |
| I28 | `W` | middle apex (81/82) | — | |
| I29 | `W` | left vertex (83/86) | — | |
| I30 | `W` | right vertex (87) | — | |
| I31 | `X` | crossing (92/93) | — | |
| I32 | `Y` | stem, full length + junction (95) | sway; the junction | |
| I33 | `Z` | top bar, left end (101) | — | |
| I34 | `Z` | top bar meets the diagonal (98/99) | — | |
| I35 | `Z` | bottom bar meets the diagonal (100/103) | — | |
| I36 | `Z` | bottom bar | — | |
| I37 | `a` | top of the bowl / arch (104) | — | |
| I38 | `b` | stem, full length | sway (ENT_SWAY 3 units, lowercase) | |
| I39 | `b` | bowl meets the stem (108) | — | |
| I40 | `c` | top terminal | no circle: the detector missed it | |
| I41 | `d` | ascender top (entry) | — | |
| I42 | `d` | foot / exit (109/110) | — | |
| I43 | `e` | terminal | — | |
| I44 | `f` | hook end | — | |
| I45 | `f` | bar | — | |
| I46 | `f` | descender tail end | — | |
| I47 | `h` | stem, full length + top (117) | sway; the head | |
| I48 | `h` | foot / exit (115/118) | — | |
| I49 | `i` | head (121) | the entry head across the stem top: its end face and the re-entrant notch under it | |
| I50 | `i` | foot / exit (122/123) | the exit flick root: a step at the stem bottom | |
| I51 | `j` | head | as I49 | |
| I52 | `j` | tail end | — | |
| I53 | `k` | head (127) | as I49 | |
| I54 | `k` | foot (125/126) | as I50 | |
| I55 | `l` | stem, full length + head + foot (128/129/130) | sway; head; exit | |
| I56 | `m` | first head (136) | — | |
| I57 | `m` | arch crowns (135/137) | — | |
| I58 | `m` | first foot (133) | — | |
| I59 | `m` | last foot / exit (138/139) | — | |
| I60 | `n` | head (143) | — | |
| I61 | `n` | arch crown (141) | — | |
| I62 | `n` | first foot | — | |
| I63 | `n` | exit (142/144) | — | |
| I64 | `o` | top join (146) | the two strokes of the o meet at the top | |
| I65 | `o` | bottom join (147) | — | |
| I66 | `p` | head (148) | — | |
| I67 | `p` | bowl top meets the stem | — | |
| I68 | `p` | descender foot (150) | — | |
| I69 | `q` | bowl top / head (152/153) | — | |
| I70 | `q` | bowl bottom meets the stem (151) | — | |
| I71 | `q` | descender foot (154/155) | — | |
| I72 | `r` | the whole r | head, arm, foot | |
| I73 | `s` | bottom terminal (158) | — | |
| I74 | `s` | top terminal (156/157) | (faint -- confirm) | |
| I75 | `t` | top (160/161) | — | |
| I76 | `t` | tail / foot (159/162) | — | |
| I77 | `u` | first head (166/167) | — | |
| I78 | `u` | second head (164/168) | — | |
| I79 | `u` | right stem and foot (163/165) | — | |
| I80 | `v` | top-left (170) | — | |
| I81 | `v` | vertex (169) | — | |
| I82 | `w` | top-left (174) | — | |
| I83 | `w` | middle top (172) | — | |
| I84 | `w` | left vertex (171/175) | — | |
| I85 | `w` | right vertex (173) | — | |
| I86 | `x` | top-left (178) | — | |
| I87 | `x` | top-right (176) | — | |
| I88 | `x` | crossing (177) | — | |
| I89 | `x` | both feet | — | |
| I90 | `y` | top-left (180) | — | |
| I91 | `y` | top-right | — | |
| I92 | `y` | junction (179/181) | — | |
| I93 | `y` | tail end | — | |
| I94 | `z` | top-left (182) | — | |
| I95 | `z` | top-right (184/186) | — | |
| I96 | `z` | bottom-left (185) | — | |
| I97 | `z` | bottom-right (183) | — | |
| I98 | `0` | top-right join | — | |
| I99 | `0` | bottom-left join | — | |
| I100 | `1` | flag (187/189/190) | — | |
| I101 | `1` | foot (188) | — | |
| I102 | `2` | spine, top-right to bottom-left | — | |
| I103 | `2` | base, left end (192/193) | — | |
| I104 | `3` | top terminal (195/196) | — | |
| I105 | `3` | waist | — | |
| I106 | `4` | apex (197/198) | — | |
| I107 | `4` | bar, left end (199) | — | |
| I108 | `4` | foot (196/200) | — | |
| I109 | `5` | bottom terminal (200) | — | |
| I110 | `6` | top terminal stroke | — | |
| I111 | `6` | bowl junction (203) | — | |
| I112 | `7` | bar, left end (204) | — | |
| I113 | `7` | bar, right end / top (205/206) | — | |
| I114 | `7` | leg, full length | — | |
| I115 | `7` | foot (207) | — | |
| I116 | `8` | the whole 8 | — | |
| I117 | `9` | bowl right join (208) | — | |
| I118 | `9` | tail end (209) | — | |
| I119 | `.` | the dot | — | |
| I120 | `,` | head and tail (210) | — | |
| I121 | `:` | both dots | — | |
| I122 | `;` | dot and comma (211) | — | |
| I123 | `!` | the dot | — | |
| I124 | `?` | terminal | — | |
| I125 | `?` | the dot | — | |
| I126 | `&` | right leg / terminal | — | |
| I127 | `&` | bottom-left | — | |

## The owner's roman write-up, 2026-09-18 -- what it says about the index

Ten of the 57 boxes were NOT what he marked (R06, R27, R29, R31, R32, R36, R38, R39, R40, R43, R57 -- his words on each row); the eye-read coordinates put the box on the nearest feature rather than his. His text names the real target in each case and the fix goes by his text, not the box. Fourteen rows ask for OPTIONS (G bar, Q tail, a, f bar, m middle stem, r, 1, 2, 6, 8, quotes, hyphen, &), the rest are direct fixes.

## Unresolved by the geometry

* **R01** (roman A, left leg at the crossbar): nothing found — both crossbar
  junctions are clean at 6 px/unit and the thin leg is straight. Waiting on the
  write-up.
* **R11** (roman N, top-left of the right stem) and the whole-glyph marks
  (R42 / I116, the 8s; I72, the italic r) are design questions rather than
  outline defects; the write-up decides them.
