# Albo: the Bold K's top-right serif (2026-10-04)

Owner, on the narrower-K page: *"13.5% narrower wins for regular roman but
bold needs rework (especially top right serif)"*. The Regular shipped at 0.865
as round 477.

**Status: SHIPPED** as round 479 (`docs/albo-round-479-2026-10-04.md`): T4 with the
connection points moved onto the Regular's (owner *"T4 is closest but move the
connection points to match regular better"*). Before that: two passes of options. The first pass's V0–V3 shrank the
spur; the owner's answer was *"try again, the top right bold serif is short ...
bold is messy"*. The dials:
- `ALBO_ROM_K_ARM_SERIF_700` (`outlines/glyphs/caps_straight.py`), the arm's
  end-wedge scale above stem 84. Today it is 0.9, `end_wedge`'s default.
- `ALBO_ROM_K_W_BOLD` (`outlines/build.py`), the width factor.

The defaults are round 477 byte for byte (control build).

## Why the serif turns into a horn

The K's arm is the family's `diagonal()` with `serif0=1`, so its top-right end
takes the diagonal wedge, 0.9 × the wedge unit `WL` by `WD`. That unit grows
with the stem. At the Bold's 116 the wedge stands up from the arm's end and
curls back into a horn, where the Regular's reads as a small spur.

## The arms (Bold only; all at the Regular's ruled 0.865 width)

| arm | width | arm serif | reads |
|---|---|---|---|
| today | 1.0 | 0.9 | |
| **V0** | 0.865 | 0.9 | narrower only, today's spur |
| **V1** | 0.865 | 0.6 | the spur about the Regular's in proportion |
| **V2** | 0.865 | 0.35 | a micro-spur |
| **V3** | 0.865 | 0 | no spur: the arm ends square |

**Moved:** K and Ķ.

**Gates (Bold, against round 477):** POOR GATES no delta. Touch 0 / 0, glitch
1 → 1 (pre-existing on Ķ).

Proof page: https://claude.ai/artifact/U6tuYio65AmgyayeZczwWF

## Second pass (2026-10-04): the junction cleaned, the serif longer

Owner, on the junction page: *"try again, the top right bold serif is short.
the regular J1 R is best, bold is messy"*. The Regular shipped J1 as round
478. For the Bold, two things, both seen only at a 700 px cap:

**The mess is the leg's buried end.** It runs 0.1 CS past the arm's
centerline at over half its full width (`kick`, bury 0.1, taper 0.45), and at
the Bold the leg (0.93 S) is twice the arm (0.47 S), so its top corner stands
through the arm's upper edge: a bump at u 0.24, a notch at 0.32. The Regular's
leg is narrow enough not to. `ALBO_ROM_K_LEG_CLIP_700=1` clips the leg to the
half-plane under the arm's upper edge, so nothing of it shows above the arm.
Every arm below has it.

**The serif is short** because the arm's end carries a single wedge on its
outer side, which curls up rather than out. New dial
`ALBO_ROM_K_ARM_SERIF_IN_700`: a second wedge on the arm end's inner side, the
two-sided terminal Albo's stem tops carry (H, N, U), which reads as a flared
end rather than a curl.

All at the Regular's ruled width (0.865) and junction (u 0.24, which in the
Bold measures 0.29 of the way along the arm, the bold references' 0.30–0.32):

| arm | outer wedge | inner wedge | reads |
|---|---|---|---|
| T0 | 0.9 | none | today's spur, junction cleaned |
| T1 | 1.3 | none | the spur 45% bigger |
| T2 | 1.6 | none | the spur 80% bigger, reaching the cap line |
| T3 | 0.9 | 0.7 | two-sided: today's spur plus a smaller inner wedge, a flared end |
| T4 | 1.3 | 1.0 | two-sided, bigger |

**Moved:** K and Ķ. **Gates (Bold, against round 478):** POOR GATES no delta
on every arm. Touch 0 / 0, glitch 1 → 1 (pre-existing on Ķ).

Proof page (second pass): https://claude.ai/artifact/9D5jrYTvSSPahDeg1VTHnG

## Third pass (2026-10-04): the arm's end in Albo's own style

Owner, after round 479 shipped T4: *"improve top right serif of bold K to
match albo style"*.

**What Albo's style is, read from the builders.** Every other diagonal that
ends at the top right ends the same way: the X's light stroke
(`g_X`, `serif0=-1` on `q0`), the V's and the Y's right strokes (`g_V`,
`g_Y`, `serif0=-1`), the W's last stroke (`g_W`, `P[3]`, side -1). The
stroke's centerline ends ON the cap line, the end is cut square to the
stroke, and ONE family wedge (`diag_wedge`, scale 0.9) hangs on the stroke's
right-hand side (side -1 in `end_wedge`'s convention, which on the K's arm
is the side facing the leg -- the "inner wedge" of the second pass),
bracketed back into the stroke. Rendered at a 700 px cap, the Bold X Y V W
and x y v all show it.

**The K was the exception, in both weights.** Its arm has always ended 0.36
of a stem UNDER the cap line (rounds 36-479) with its wedge on the UPPER
side (`serif0=1`). At the Regular's stem that is a small spur and was ruled
good; at the Bold's it grows into a horn, and round 479's T4 added a second
wedge under it -- a two-sided end no other Albo letter has.

New dial `ALBO_ROM_K_ARM_DROP_700`: the arm end's centerline under the cap
line, in stems (0.36 = rounds 36-479, 0 = the X's). The three options, all on
round 479 (width, leg clip and join unchanged):

| arm | env | the end |
|---|---|---|
| U1 | `K_ARM_SERIF_700=0 K_ARM_SERIF_IN_700=0.9 K_ARM_DROP_700=0` | the X's terminal exactly: family wedge on the right, end on the cap line |
| U2 | `K_ARM_SERIF_700=0 K_ARM_SERIF_IN_700=1.3 K_ARM_DROP_700=0` | the same, wedge 1.3 (T4's size) -- longer reach |
| U3 | U2 + `K_ROOT_700=0.385` | U2 with the arm pivoted on the leg's join, so the leg meets the arm at round 479's height |

(env names abbreviated: each is `ALBO_ROM_` + the name.)

**What raising the arm's end costs at the junction.** The join point is a
fraction of the way along the arm, so lifting the arm's end lifts the join.
Measured with `instruments/k_junction.py` (cap heights; crotch = where the
leg's upper edge meets the arm's lower edge, root = where the arm's lower
edge leaves the stem):

| | crotch right | crotch high | arm root |
|---|---|---|---|
| Regular (round 478) | 0.163 | 0.590 | 0.467 |
| Bold round 479 | 0.163 | 0.610 | 0.457 |
| U1, U2 | 0.160 | 0.637 | 0.467 |
| U3 | 0.157 | 0.613 | 0.437 |

U1 and U2 put the arm's root exactly on the Regular's and the crotch 0.027 C
(18 units) higher than round 479; U3 keeps the crotch and puts the root 0.02 C
lower. No setting keeps both: every compensation trades one connection for
the other (a smaller `K_U_700` keeps the height but moves the join toward the
stem, against the J1 ruling).

**Tops** (font units; the stem tops are at 676): round 479's K 686 (the
horn), U1-U3 694, against the Bold X 707, Y 706, V 695, W 691.

**Negative results, not offered:**
- *The X's wedge with the arm's end left where it was* (drop 0.36): the arm
  tops out at 648, 28 units under the stem tops (676), and the wedge hangs
  below that. It reads short, which is the owner's complaint about round
  478.
- *A milder pivot*, `K_ROOT_700` 0.392: crotch 0.617, root 0.440 -- between
  U2 and U3 on both measures, so it adds nothing to the choice.

**Gates (Bold, against round 479):** POOR GATES no delta on all three.
Moved: K, and Ķ in U1/U2 (the K's advance moves by one unit). Checked and
found CLEAN: contour hairs (letters and full sweep, nothing new), touch 0 / 0
-> 0 / 0, counter-dent lines 1 -> 1, glitch unchanged (U3's K 0 findings; the
pre-existing one is Ķ's), contour census unchanged (1056 glyphs), approved
letters unchanged, the e mouth gate ok. The dial's defaults rebuild round 479
byte for byte (`cmp_outlines`: IDENTICAL).

The Regular K is not touched: its arm keeps its small upper spur.

Nothing has shipped.

Proof page (third pass): https://claude.ai/artifact/7dAUe7sDPhpzAvCFK9LqQo

## Fourth pass (2026-10-04): the references traced

Owner, on the third pass: *"getting worse"*, then *"let's trace references and
see what is possible"*. U1-U3 are rejected; round 479 (T4) stands.

**Instrument:** `tools/wedge_serif/instruments/k_arm_trace.py`. Each face's K
is rendered unhinted with its OWN H's top on Albo's 676 (a capital, so the
faces share a cap height, not an x-height); the arm's two edges are fitted
over 0.66-0.84 C, and the end's ink is read row by row. It reads an Albo build
the same way. Three instrument bugs were found and fixed before any number
below was used, each of which produced a believable figure:
1. the H stem was read at half height, which is the crossbar (stems of
   400-660 units); it is read at a quarter;
2. the end took every run right of the stem, and a concave top splits the
   cap-line row into slivers, so Optima's own stem corner counted as arm
   (flat 360 for a 120-unit end); it takes the rightmost run;
3. the arm fit took the rightmost run in the band, and round 479's under-side
   wedge hangs a 9-unit sliver there, which read Albo's arm at 36 degrees where
   its edges run at 44.5; it takes the widest run.

**The one structure every reference shares and Albo lacks: the arm's end lies
FLAT ON THE CAP LINE.** All 13 bold references measure top = 676 exactly --
eleven with a bracketed serif along the line, Albertus and Optima with the
stroke flared and cut level. Albo's arm ends in a POINT 10 units (Bold) and 12
(Regular) over the line, 14 units across, in both weights.

Units Albo, cap 676; "own serif" = the face's H top serif, the most it reaches
over the top 40 units (out for the left reach, in for the right):

| face | stem | arm angle | arm / stem | top | flat / stem | reach left (x own serif) | reach right (x own serif) | depth left / right, stems |
|---|---|---|---|---|---|---|---|---|
| Albo Regular | 72 | 38.4 | 0.47 | 688 | 0.19 | 79 (1.33) | 0 (0.09) | 0.99 / 0.00 |
| Albo Bold 479 | 125 | 43.0 | 0.44 | 686 | 0.11 | 99 (1.59) | 50 (6.28) | 0.85 / 0.94 |
| Albertus | 104 | 50.7 | 0.87 | 676 | 1.67 | 23 (0.96) | 27 (1.18) | 0.62 / 0.59 |
| Trajan Bold | 112 | 45.6 | 0.45 | 676 | 2.02 | 73 (0.81) | 81 (1.05) | 0.67 / 0.57 |
| Berkeley Bold | 120 | 45.6 | 0.33 | 676 | 1.90 | 144 (1.74) | 54 (0.85) | 0.49 / 0.40 |
| Georgia Bold | 169 | 45.9 | 0.29 | 676 | 1.74 | 146 (1.47) | 97 (1.00) | 0.59 / 0.54 |
| Charter Bold | 134 | 50.3 | 0.48 | 676 | 1.70 | 118 (1.57) | 64 (0.84) | 0.48 / 0.41 |
| Times Bold | 162 | 38.9 | 0.24 | 676 | 1.62 | 175 (1.84) | 47 (0.49) | 0.57 / 0.25 |
| Baskerville Bold | 176 | 43.0 | 0.35 | 676 | 1.70 | 173 (1.95) | 80 (0.92) | 0.61 / 0.59 |
| Hoefler Black | 194 | 44.1 | 0.29 | 676 | 1.49 | 157 (1.55) | 89 (0.95) | 0.47 / 0.51 |
| Palatino Bold | 140 | 44.2 | 0.38 | 676 | 1.28 | 44 (0.53) | 80 (0.96) | 0.44 / 0.62 |
| Iowan Bold | 125 | 45.3 | 0.54 | 676 | 2.06 | 118 (1.48) | 65 (0.81) | 0.66 / 0.64 |
| Athelas Bold | 130 | 44.6 | 0.43 | 676 | 1.76 | 127 (1.72) | 44 (0.59) | 0.57 / 0.46 |
| Cochin Bold | 138 | 44.2 | 0.33 | 676 | 2.37 | 160 (1.53) | 89 (0.80) | 0.78 / 0.71 |
| Optima Bold | 148 | 49.7 | 0.47 | 676 | 0.81 | 5 (0.65) | 5 (0.76) | 0.07 / 0.11 |

Medians over the eleven serifed faces: the arm's serif reaches LEFT 1.55x the
face's own stem-top serif and RIGHT 0.85x; its brackets run 0.57 and 0.54 of a
stem down; its flat top is 1.74 stems; the arm stands at 44.6 degrees (45.3
over all 13). Albo's own stem-top serif (the H's) reaches 62 out and 8 in --
one-sided -- so 1.55x and 0.85x of 62 are 96 and 53 units.

**New dials** (`ALBO_ROM_K_ARM_FLAT_700` and its four numbers, all inert at
their defaults): the arm's end cut LEVEL on the cap line with `_flat_diag` (the
W's and M's apex cut), its centerline's end raised to the line at the same x
(U1's geometry), and ALBO's OWN stem-top wedge -- `stem`'s construction, d up,
sd sideways, bracket down the stroke's real edge -- seated on each corner of
that face. Three options, each set so the instrument reads the traced numbers:

| arm | left x WL | right x WL | depth x WD | drop x DROP | traced from | reads (reach l/r, depth l/r, flat) |
|---|---|---|---|---|---|---|
| H1 | 0.57 | 0.57 | 1.7 | 0 | Albertus: the stroke flared, cut level (target 28/32, 77/74) | 29/31, 73/80, 140 |
| H3 | 2.1 | 0.72 | 1.25 | 1 | the eleven serifed faces' medians, Albo's sloped wedge top (target 96/53, 71/68) | 97/54, 73/68, 142 |
| H4 | 1.84 | 1.0 | 1.25 | 0 | the same medians with the references' LEVEL top (target flat 218) | 100/55, 73/63, 231 |

All three put the top at 676. The arm itself is U1's: it stands at 48.2
degrees against round 479's 44.5 (references 39-51), and the join moves as it
did in U1 -- crotch 0.637 C high against 0.610, the arm's root 0.467 C, which is
the Regular's (`instruments/k_junction.py`, measured on H1, H3 and H4).

**Negative result: the family's wedge at 1/1/1 ("H2", not offered).** It reads
reach 38 / 70 and grows a KNOB on the arm's upper side. A stem's edge is
vertical; the arm's upper edge leans toward the wedge's own tip, so at depth
104.6 along that edge the bracket's foot lands 70 units left of the corner,
past the 52-unit tip, and the bracket turns convex. The stem wedge's numbers do
not transfer to a diagonal: the left wedge has to reach past its own bracket's
foot (about 1.4 WL or more) before its bracket is concave.

**Gates (Bold, against round 479):** POOR GATES no delta on H1, H3 and H4.
Moved: K and Ķ. Checked and found CLEAN on all three: contour hairs (letters
and the full sweep, nothing new), touch 0 / 0 -> 0 / 0, counter-dent lines
1 -> 1, glitch 1 -> 1 (the pre-existing one is Ķ's), contour census unchanged
(1056 glyphs), approved letters unchanged, the e mouth gate ok. The dials'
defaults rebuild round 479 byte for byte (`cmp_outlines`: IDENTICAL).

Nothing has shipped.

Proof page (fourth pass): https://claude.ai/artifact/4uu2GJm654FfVGWr7uH1Wo
