# The CRT page-color presets, and where their colors came from

**RETIRED 2026-08-17 — read before citing §7 or the Sepia CRT rows below as
current.** Owner ruling *"remove sepia phosphor"*: `kPresetSepiaCrt = 14` in
`src/PanelPalette.h:124` is now commented `// retired; do not reuse this
number` — it is absent from `isKnownPreset()` (`src/PanelPalette.h:230-267`,
confirmed by `tests/panel_palette_test.cpp:469` asserting
`!isKnownPreset(kPresetSepiaCrt)`) and from the `resolve()` switch, and
`migratePreset()` does NOT redirect it to a replacement — unlike Cool Gray (4)
and Soft (13), which migrate forward to Reading Cool/Warm, a stored 14 now
falls through to Default like any unrecognized integer
(`tests/panel_palette_test.cpp:507`). The number 14 is never reused. **This is
a deletion, not a migration** — §7's whole derivation, its ΔE2000 collision
table and the "Open" items about it (§8.5, §8.6) below are kept for the
research (the sepia-is-not-a-phosphor argument and the brown-perception
argument are still correct and may matter again), but none of it describes a
row that resolves to anything today. The six-row group this file was written
about is five rows now: Green, Amber, Gray, Blue, Red.

Written 2026-08-16, when **Red CRT (11)** and **Gray CRT (12)** were appended to
`src/PanelPalette.h`. It records the phosphor research behind all four CRT rows,
the arithmetic that turned published chromaticities into the shipped bytes, and
the two candidates that were **rejected** — because the rejected half is what
stops the same idea being re-proposed every six months.

**Extended the same day** with **Sepia CRT (14)** and **Blue CRT (15)**, which
close the group out at six rows — see [§6](#6-blue-p11-is-real-and-the-floor-bites-harder-here-than-anywhere)
and [§7](#7-sepia-is-not-a-phosphor-and-the-dark-half-cannot-be-brown). One of
those two is a real phosphor and one is not, and the file says which.

Every CIE coordinate below was read from the cited source. Every sRGB hex is
**our conversion**, not something a source printed; no source in this research
stated an sRGB value for any phosphor.

The rendered proofs — all four halves plus both rejected candidates, uncropped
at 480x800 — are published at
<https://claude.ai/code/artifact/8b634a2c-2e50-4c04-b916-f10aa718cf80>. That
page is the view; this file is the record.

The proofs for **Blue CRT and Sepia CRT** — both halves of each, plus the
side-by-side collision check against Amber CRT, Paper · Sepia and Red CRT, all
uncropped at 480x800 — are at
<https://claude.ai/code/artifact/b495aa47-3316-4c24-b16d-d704218b2de2>.

---

## 1. What the six rows actually are

| Row | Phosphor | Composition | CIE x, y | Source |
|---|---|---|---|---|
| Green CRT (6) | **P1** | Zn₂SiO₄:Mn (willemite) | 0.208, 0.704 | Phosphor Technology Ltd, grade GK |
| Amber CRT (7) | **P3** | Zn₈BeSi₅O₁₉:Mn | *none published* | see §4 |
| Red CRT (11) | **P22R** | Y₂O₂S:Eu | 0.647, 0.343 | Phosphor Technology Ltd, grade QKL63 |
| Gray CRT (12) | **P4** | ZnS:Ag + (Zn,Cd)S:Cu and variants | *none published* — JEDEC white region used instead, see §3 | US 4512912 |
| Blue CRT (15) | **P11** | ZnS:Ag,Cl or ZnS:Zn | 0.147, 0.076 | Phosphor Technology Ltd, grade BE |
| Sepia CRT (14) — **RETIRED 2026-08-17, see notice above** | **none — not a phosphor** | Ag₂S, a print-toning product | n/a | see §8 |

Verified directly (not via a summary) on 2026-08-16:

* Phosphor Technology Ltd's CRT phosphor table — P1 **0.208 / 0.704**,
  P22R **0.647 / 0.343**, P56 **0.650 / 0.346**, P31 **0.287 / 0.521**,
  and (fetched again for the blue row) **P11-BE, ZnS:Ag, 0.147 / 0.076**,
  P22B-X **0.148 / 0.062**, P47-BH **0.170 / 0.103**. The table has **no P3
  and no P4 row at all**, which is why those two are derived elsewhere here.
  <https://www.phosphor-technology.com/crt-phosphors/>
* Wikipedia, *Phosphor* — the JEDEC P-number table. Rows read verbatim:
  **P1 (GJ)** Zn₂SiO₄:Mn, green, 525 nm, "Oscilloscopes and monochrome
  monitors"; **P3** Zn₈:BeSi₅O₁₉:Mn, yellow, 602 nm, "Amber monochrome
  monitors"; **P4** ZnS:Ag+(Zn,Cd)S:Ag, white, 565/540 nm, "Black and white TV
  CRTs and display tubes"; **P11 (BE)** ZnS:Ag,Cl or ZnS:Zn, blue, 460 nm,
  0.01–1 ms, "Display tubes and VFDs; Oscilloscopes (for fast photographic
  recording)"; **P22B** ZnS:Ag+Co-on-Al₂O₃, blue, "Blue phosphor for TV
  screens". <https://en.wikipedia.org/wiki/Phosphor>
* Wikipedia, *Monochrome monitor* — "if the P1 phosphor is used, the screen is
  green monochrome", "If the P3 phosphor is used, the screen is amber
  monochrome", "If the P4 phosphor is used, the screen is white monochrome
  (known as 'page white')". **It names no red screen anywhere.**
  <https://en.wikipedia.org/wiki/Monochrome_monitor>
* US 4512912, *White luminescent phosphor for use in cathode ray tube* — the
  JEDEC white parallelogram, corners **A (0.273, 0.282)**, **B (0.267, 0.303)**,
  **C (0.286, 0.326)**, **D (0.290, 0.303)**, reference **6500 K + 7 MPCD**.
  <https://patents.google.com/patent/US4512912A/en>
* int10h.org, *Simulating CRT Monitors with FFmpeg Pt.2* — "the kinda-bluish P4
  phosphor used in black and white TVs"; "AFAIK there was no 'standard' amber
  phosphor, and varying mixtures were used"; green monitors were P39 or P31.
  No red option exists in its monitor-color list.
  <https://int10h.org/blog/2021/02/simulating-crt-monitors-ffmpeg-pt-2-monochrome/>

Read once, via a research pass rather than re-fetched here (treat as
second-hand): the labguysworld JEDEC/EIA phosphor compilation
(<http://www.labguysworld.com/crt_phosphor_research.pdf>), US 4377768 (a white
data-display CRT at x 0.275 ± 0.015, y 0.295 ± 0.010, ~10,600 K), US 4694217
(P45 Y₂O₂S:Tb at 0.269, 0.311), and EP 0098976 A2 (the amber data-display
phosphor, §4).

---

## 2. Red: there was never a red terminal, and the row says so

**No red monochrome terminal shipped as a commercial product.** The three
monochrome screen colors are exhaustively green / amber / white in every
general reference checked, and no red P-number in the JEDEC list carries "data
display" as its application. The eye peaks near 555 nm; green (~525) and amber
(~580–602) sit near it and red does not, and amber specifically was *marketed*
on reduced eye strain.

Red CRTs that did exist, none of them a terminal:

1. **The red tube of a three-tube CRT projector** — a genuinely monochrome
   red CRT. P56 (Y₂O₃:Eu, 0.650 / 0.346) or P22R.
2. **The red gun of every color tube** — P22R. This is also the EBU / Rec.709
   red primary (0.640 / 0.330), i.e. the phosphor got standardized.
3. **Beam-penetration ("Penetron") displays** at low anode voltage — air
   traffic control, avionics, radar.

So Red CRT is labeled **P22R phosphor**, which is true, and the header comment
states plainly that it is a real phosphor rendered as a page rather than a
machine anyone sat in front of.

### OVERTURNED 2026-08-17: the radar oranges ship, and so does everything else

Owner: *"where is the orange radar? be sure to include all possible phosphors"*,
and when told they had been ruled near-duplicates: *"i said all possible
phosphors, you ruled they were near dupes"*. **The rejection below is void.**
P19, P26, P33 and P38 all ship, along with every other JEDEC P-number this
repo can honestly render — 42 phosphor rows in total. See §10.

The reasoning that reversed it is the same one recorded at the end of this
file: colour was the only thing a row had when the rejection was written, and
persistence is now rendered. Two rows that paint the same page but decay 1095 ms
and 2828 ms are not the same control.

The original rejection, kept because the emission facts in it are still true:

### Rejected: the radar oranges

P19, P26, P33, P38 (all fluoride:Mn, very long persistence, the classic PPI
scope) were considered and **rejected**: they emit at **590–595 nm**, which is
Amber CRT's territory. Labeling them red would be wrong, and shipping them
would give two rows that paint nearly the same page. If a *third* CRT row is
ever wanted between amber and red, the honest name for it is "radar orange",
not "red".

### The 7:1 floor makes the authentic red impossible — measured, not guessed

Red carries only **0.2126** of the sRGB luminance coefficient. P22R at the
brightest luminance sRGB can render that chromaticity is `#FF1B00`, whose
relative luminance is **0.2203**. Against *pure black* that is

```
(0.2203 + 0.05) / (0.0 + 0.05) = 5.41 : 1
```

There is no tube color that improves it — black is already the floor of the
denominator. **A full-purity 611 nm red cannot reach 7:1 in sRGB, at all.**

The shipped dark ink is therefore P22R blended **14.9% toward D65 in linear
light** — same dominant wavelength, lower purity, which is also what a real
trace does when the beam saturates the phosphor — giving `#FF6F6C` at
**7.33:1**. That is the tightest non-exempt figure in the whole preset list and
it is as red as the floor permits.

The alternative was a second `isLowContrastByDesign()` exemption. That is a
ruling the owner has to make deliberately (the test asserts exactly one preset
may claim it), so it was not taken inside a palette commit. See "Open" below.

---

## 3. Gray: P4 has no published CIE point, so the JEDEC white region stands in

There is no manufacturer chromaticity for P4 itself — searched and not found.
What *is* published is the region every P4 screen must fall inside: the JEDEC
white parallelogram from US 4512912. Its centroid is

```
x = (0.273 + 0.267 + 0.286 + 0.290) / 4 = 0.2790
y = (0.282 + 0.303 + 0.326 + 0.303) / 4 = 0.3035
```

That point sits **below and to the left of D65 (0.3127, 0.3290)**, so JEDEC
white is *definitionally* cooler than daylight — the blue cast is the
specification, not a liberty taken here. McCamy's approximation puts its CCT
around **9,300 K**; a separately patented white data-display CRT (US 4377768)
gives ~10,600 K, which agrees. It is also exactly why int10h calls P4
"kinda-bluish".

Rendered at the brightest luminance sRGB can carry that chromaticity:
**`#C9E7FF`**, relative luminance 0.7684. That is the dark half's ink, straight.

### Rejected: the light paper derived at the family's luminance

The first light half was derived the same way Green and Amber's were — tint the
phosphor toward D65 until it reaches the family's paper luminance (~0.81).
For P4 that needs only an **18% blend**, giving `#D4ECFF` at a perfectly legal
**10.23:1**.

**It renders as a sky-blue page.** Arithmetic does not show this and the test
would have passed it; the capture is what caught it. Green and Amber never hit
this because their phosphors sit so far outside sRGB that reaching page
luminance desaturates them anyway — P4 is already nearly white, so almost no
desaturation is required and the tint stays at full strength.

The shipped paper blends **52.5%** instead: `#E7F4FF`, **11.14:1**, same hue
direction at a quarter of the saturation. Paper spread (max channel minus min)
is **24**, against Green CRT's 23 and Cool Gray's 7 — tinted like the CRT
family, three times the neutral row it must not be confused with.

### Why "Gray" and not "White"

Because the page it makes is a gray page. It is also why the tint is allowed to
show at all: a P4 page derived honestly and then neutralized lands on top of
Cool Gray, and two rows that paint nearly the same page is a control that
appears to do nothing.

---

## 4. Amber, checked in passing — the label is defensible, the history is messier

Not changed, but recorded so it is not re-litigated:

* **P3 is the designation every general reference cites for amber**, and
  Wikipedia says so verbatim.
* **P3's registered application is "early radar (c. 1939)", not terminals**, and
  it is a *beryllium* phosphor (Zn₈BeSi₅O₁₉:Mn) — beryllium phosphors were
  abandoned on toxicity grounds.
* **1980s amber terminals generally used cadmium-silicate ambers.** EP 0098976
  A2 specifies Cd₂Si₁.₅O₅:Mn,As centered ~580 nm, CIE roughly
  0.500 < x < 0.625, 0.375 < y < 0.500, and explicitly names P3 and P25 as
  *inferior* alternatives. The industry gave that blend no P-number.

So "Amber CRT — P3 phosphor" is the textbook answer and stays. Anyone wanting
to be strictly accurate would have to invent a label for a phosphor that never
got one.

Same footnote for green: the famous IBM 5151 is usually attributed to **P39**,
and most fast green monitors were **P31** (0.287 / 0.521, a yellower, much less
saturated green). "Green CRT = P1" is the textbook answer, not the one you
actually sat in front of.

---

## 5. The shipped bytes, and how each was derived

Construction, matching what Green and Amber already do:

* **dark paper** = phosphor sRGB × 26/255 (Green: `00FF00` → `001A00`)
* **dark ink** = phosphor, desaturated toward D65 only as far as the floor forces
* **light paper** = phosphor blended toward D65 (see §3 for the Gray exception)
* **light ink** = phosphor scaled in linear light to the family's ink luminance
  (Green `0B3D0B` L=0.0343, Amber `4A2E00` L=0.0341)

| Row | Half | Ink | Paper | Contrast |
|---|---|---|---|---|
| Red CRT | light | `#6E0500` (P22R, linear ×0.155) | `#FFE2E1` (75.6% toward D65) | **10.22:1** |
| Red CRT | dark | `#FF6F6C` (P22R, 14.9% toward D65) | `#1A0300` (P22R × 26/255) | **7.33:1** |
| Gray CRT | light | `#2D353C` (P4, linear ×0.0445) | `#E7F4FF` (52.5% toward D65) | **11.14:1** |
| Gray CRT | dark | `#C9E7FF` (P4, full emission) | `#14181A` (P4 × 26/255) | **13.92:1** |
| Blue CRT | light | `#001F9E` (P11, scaled to L 0.0342) | `#E5E7FF` (78.7% toward D65) | **10.18:1** |
| Blue CRT | dark | `#8B92FF` (P11, 25.8% toward D65) | `#00061A` (P11 × 26/255) | **7.35:1** |
| Sepia CRT | light | `#663B11` (sepia axis at L 0.060, §7) | `#FFDFCE` (toned highlight at L 0.78) | **7.59:1** |
| Sepia CRT | dark | `#FFCCAF` (toned highlight, 40% to D65) | `#1A1512` (ink × 26/255) | **12.51:1** |

All eight verified in pixels through the real renderer, not asserted — see
`docs/headless-qa.md` for the recipe. Reading the dominant colors back out of
each capture gives exactly the ink and paper above, plus the two interpolated
2-bit grays in the light halves (`#A45854` / `#DFB2B0` for Red,
`#737C85` / `#BECAD4` for Gray, `#566AC2` / `#B3BBEA` for Blue,
`#9F7858` / `#DEBBA5` for Sepia).

---

## 6. Blue: P11 is real, and the floor bites harder here than anywhere

**P11 is a genuine, widely-manufactured CRT phosphor**, and unlike Red it does
not need a caveat about being a projector tube: Wikipedia's P-number table
gives its application as **"Display tubes and VFDs; Oscilloscopes (for fast
photographic recording)"**. Blue was *the* photographic phosphor, because
blue-sensitive film is where a trace could be recorded at speed. Phosphor
Technology Ltd sells it today as grade **BE**, ZnS:Ag, at **x 0.147, y 0.076**.
It is also the same ZnS:Ag chemistry as **P22B**, the blue gun of every color
tube (0.148 / 0.062) — so, exactly as with P22R and red, the phosphor got
standardized into the sRGB primary you are reading this on.

**But no blue monochrome TERMINAL shipped**, the same finding as red. Wikipedia's
*Monochrome monitor* article enumerates green (P1), amber (P3), white (P4) and
names no blue; int10h's monochrome survey lists P4, P39, P31, amber, white,
paper-white and P7 and names no blue either. So Blue CRT is a real display-tube
phosphor rendered as a page, not a machine anyone sat in front of.

### The contrast ceiling: 3.01:1, and there is nothing to be done about it

Blue carries **0.0722** of the sRGB luminance coefficient — a third of red's
0.2126, a tenth of green's 0.7152. P11's chromaticity is *just* outside the
sRGB gamut (the raw linear RGB is `-0.366 / +0.426 / +10.712`, one negative
component), so rendered at the brightest luminance sRGB can carry it, clipped
to the boundary, it is **`#0038FF`**, relative luminance **0.1005**. Against
*pure black*:

```
(0.1005 + 0.05) / (0.0 + 0.05) = 3.01 : 1
```

Red at full purity managed 5.41:1 and could not reach the floor. Blue manages
**3.01:1**. This is the hardest wall in the whole preset list, and it is not a
gamut artifact — it is the luminous efficiency of the eye at 460 nm.

The shipped dark ink is therefore P11 blended **25.8% toward D65 in linear
light** — the identical construction Red used, with the identical physical
excuse (a saturating beam loses purity, not dominant wavelength) — giving
**`#8B92FF` at 7.35:1**, a hair above Red CRT's 7.33:1. Red keeps the title of
tightest non-exempt figure by 0.02.

### Distinctness: no argument here

Blue CRT's nearest neighbour in the whole 15-row list is Cool Gray's dark
*paper* at ΔE2000 6.1 — and both are near-blacks, where the metric means
little. On the ink, which is what a reader looks at, it is **16 to 25 ΔE2000
from everything**, including Gray CRT (16.0 light / 20.9 dark), the row it
shares the coolest corner with. Nothing else in the list is blue.

---

## 7. Sepia is not a phosphor, and the dark half cannot be brown

**RETIRED 2026-08-17 — this whole section describes a row that no longer
resolves; see the notice at the top of this file.** Kept for the research.

Two separate honest problems, and the row is built around both.

### 7a. There is no sepia phosphor. There was never going to be.

**Sepia is a photographic toning process, not an emission.** The metallic
silver of a finished black-and-white print is converted to a **silver sulfide**,
which is "at least 50% more stable than silver" — the process was done for
archival life, and the brown was the side effect
(<https://en.wikipedia.org/wiki/Photographic_print_toning>). The word itself is
the cuttlefish: sepia is "a reddish-brown color, named after the rich brown
pigment derived from the ink sac of the common cuttlefish"
(<https://en.wikipedia.org/wiki/Sepia_(color)>).

Searched and **not found**: any sepia P-number, any sepia entry in Wikipedia's
JEDEC table, any sepia screen in the *Monochrome monitor* article (green / amber
/ white, exhaustively), any sepia in int10h's monochrome survey. So the row is
labeled **"CRT · Sepia — toned, not a phosphor"** in Settings, and it is a
**toned tube**: the P4 monochrome page put through the toning bath, which is
something you could genuinely have done to a photograph of a screen, rather than
an invented P-number.

### 7b. A brown trace is not a gamut problem — it is a perceptual impossibility

This one is worth stating carefully, because it looks like the red problem and
is not.

> "Brown exists as a color perception only in the presence of a brighter color
> contrast." — <https://en.wikipedia.org/wiki/Brown>

Brown **is** dark orange, perceived against something brighter. A trace on an
unlit tube is the brightest thing in the frame; it has nothing to be dark
against, so it reads as orange, full stop. Driving the sepia hue to full
emission confirms it in arithmetic: `#704214` scaled up in linear light until a
channel clips gives **`#FF9D3B`**, which is **ΔE2000 10.4 from Amber CRT's
`#FFB000`** — Amber with extra steps.

A toned print's *bright* end is a warm cream, so the dark half takes the toned
**highlight**: **`#FFCCAF`** on **`#1A1512`**, 12.51:1.

### The tone axis, and two deliberate departures from the other CRT rows

The axis is the sepia pigment itself, **`#704214`** (Maerz and Paul, *A
Dictionary of Color*, 1930, via Wikipedia; HSV 30°, ISCC–NBS "strong brown").
Both departures below exist for one reason: **the warm quadrant of this list is
already occupied**, by Paper · Sepia, Amber CRT, Red CRT and Gruvbox Light.

1. **The light INK sits at luminance 0.060, not the family's 0.034.** Toning
   tones the shadows too — a toned print's dark end is a brown, not a black —
   and at the family's ink luminance the sepia axis lands on `#54300C`, which is
   **ΔE2000 4.2 from Amber CRT's `#4A2E00`**: a duplicate. Lifting it to
   `#663B11` costs contrast (7.59:1, the second-lowest non-exempt figure after
   Latte's 7.06) and buys ΔE2000 **7.3**.
2. **The light PAPER is derived from the toned highlight, not from the
   pigment**, and it lands on the *reddish* side of sepia. Blending `#704214`
   up to page luminance washes the hue out completely — `#E9E7E5`, channel
   spread **4**, a neutral page. This is the exact mirror of the trap Gray CRT
   hit (there the honest derivation was too saturated; here it is too weak), and
   like that one it was only visible in pixels.

   The shipped paper `#FFDFCE` sits at hue ~21°, redder than the pigment's 30°.
   That is not a fudge: Wikipedia's first line on sepia is "a **reddish**-brown
   color", and the yellow-brown half of sepia's range is precisely what Amber
   CRT and Paper · Sepia already paint. The red half is both free and the more
   canonical reading of the word.

### The collision check, measured and then looked at

The two named risks, in ΔE2000 (below ~2 is indistinguishable side by side,
below ~5 needs a careful eye, above ~10 is obvious):

| Pair | Half | Ink ΔE00 | Paper ΔE00 |
|---|---|---|---|
| Sepia CRT vs **Paper · Sepia** | light | 15.8 | 10.3 |
| Sepia CRT vs **Paper · Sepia** | dark | 11.9 | 2.3 |
| Sepia CRT vs **Amber CRT** | light | 7.3 | 10.5 |
| Sepia CRT vs **Amber CRT** | dark | 20.8 | 4.7 |

**Calibration, which is the part that makes those numbers mean anything:**
Amber CRT's light paper and Paper · Sepia's light paper are **already ΔE2000
2.4 apart** in the shipped set, and Gray CRT's is 4.6 from Cool Gray's, and
Default's is 4.3 from Cool Gray's. The near-black dark papers are all within
3–10 of each other by construction. **Sepia CRT is more distinct from both of
its neighbours than those two shipped rows are from each other.**

**And then rendered, because a number is not a verdict.** All three light halves
put through the real renderer at 480x800 (the proofs are linked at the top):
Amber CRT is a **yellow** cream page with dark brown ink; Paper · Sepia is a
**soft warm cream** with near-black ink; Sepia CRT is a **peach-pink** page with
mid-brown ink. Side by side a person can tell all three apart without effort.
The honest caveat is the other direction: **shown one of them alone, "warm page"
is the impression all three leave**, and Sepia CRT's nearest neighbour by eye is
not Amber at all — it is **Red CRT**, whose paper is also pink (ΔE2000 7.0),
separated by its oxblood ink against Sepia's brown.

**Verdict: ship it, distinct.** Not a near-duplicate. But it is the fourth warm
row in a fifteen-row list, and that is the crowding, not this row's derivation.

---

## 8. Open, for the owner to rule on

1. **Does Red CRT's dark half get to be actually red?** It is `#FF6F6C`
   (a bright scarlet) because 7:1 forbids anything more saturated — the
   authentic `#FF1B00` measures 5.41:1 against pure black and cannot be fixed.
   Making it authentic requires a **second** low-contrast exemption alongside
   Solarized, which the test deliberately blocks. Default answer taken here:
   no, keep the floor, ship the lifted red.
2. ~~**Spelling.**~~ **Settled while this was in progress — not open.** The row
   was written as "Gray CRT", which is how the work was asked for. `f0e5210`
   then landed on `main` mid-session carrying the owner ruling *"always use
   american spellings"*, so it ships as `kPresetGrayCrt` / **"Gray CRT"**,
   matching the existing `kPresetCoolGray` / "Cool Gray". The rest of this
   file was swept the same way.
3. **The Root.plist rows print the LIGHT figure**, as all eleven existing rows
   do. For Red CRT that means the label says 10.2:1 while the dark half is
   7.33:1. Printing both, or printing the weaker half, would be a change to
   every row, not just these two.

Added with Sepia CRT and Blue CRT (2026-08-16):

4. **Same question as (1), for Blue, and it is worse.** Blue CRT's dark half is
   `#8B92FF` at 7.35:1 because full-purity P11 measures **3.01:1 against pure
   black** — the hardest wall in the list. Making it authentic needs the same
   second low-contrast exemption. Default answer taken here: no, keep the floor,
   ship the lifted periwinkle.
5. **RESOLVED 2026-08-17 — moot: the row was removed, not tuned.** Owner ruling
   "remove sepia phosphor" (`src/PanelPalette.h:124`) answered this by deleting
   Sepia CRT rather than picking a trade; kept below for the record.
   **Sepia CRT's light half is 7.59:1**, the second-lowest non-exempt figure
   after Latte's 7.06. That is deliberate: at the family's ink luminance the
   sepia axis is ΔE2000 4.2 from Amber CRT and the row would be a duplicate, so
   contrast was spent on distinctness (§7). If the owner would rather have the
   contrast than the separation, the trade is `#54300C` at 8.8:1 — and a row
   that reads as a slightly browner Amber CRT.
6. **RESOLVED 2026-08-17 — moot, same ruling as (5).**
   **Sepia CRT's page is peach-pink, not the yellow-brown "sepia" most people
   picture** — because the yellow-brown is already Amber CRT's and Paper ·
   Sepia's, and Wikipedia's own first line calls sepia "a reddish-brown color"
   (§7). Its nearest neighbour by eye is Red CRT, not Amber. If the owner
   pictured the yellow one, the honest answer is that Paper · Sepia already is
   it and this row should not exist rather than be moved on top of it.
7. **The CRT group is sorted by P-number and Sepia has none**, so it sorts last
   in the group, after Red (P22R). Green (P1) · Amber (P3) · Gray (P4) · Blue
   (P11) · Red (P22R) · Sepia. That placement is a convention, not a derivation.

## 9. Persistence, and the full P-number table (added 2026-08-17)

Asked for as "incorporate the speed of persistence". Every CRT row now carries
its phosphor's published decay in `panelpalette::PresetInfo`, for ST-009's glow.

**Source:** Patrick Jankowiak (KD5OEI), *Cathode Ray Tube Phosphors Of Interest
To The Experimenter*, rev. 20100226.1844,
`labguysworld.com/crt_phosphor_research.pdf`. Its persistence column is defined
as **time to decay to 10% of peak** — the figure a fade wants. It is also the
first source found here that prints persistence per P-number at all; Phosphor
Technology's table (§2) gives chromaticity but not decay.

### Shipped rows

| Row | P | Persistence, verbatim | `decayMs` |
|---|---|---|---|
| Green | P1 | 20ms (also "Medium 1–100 ms") | 20 |
| Amber | P3 | 13ms | 13 |
| Gray | P4 | not over 7% of peak after 33 ms | 33 |
| Blue | P11 | 2ms (BE grade: "0.01–1 ms") | 2 |
| Red | P22R | "Medium" — **class only, no figure** | 0 |

`decayMs` is 0 where the table gives a class rather than a number. That is
deliberate: the glow falls back rather than having a figure invented for it.

### SHIPPED 2026-08-17: the remaining phosphors

Owner: "remove setting always have it on for crts. now add remaining crts." The
glow existing is what unblocked these -- until a page decayed at the phosphor's
own rate, a second green next to P1 was just a second green. Now they differ in
WHEN they stop emitting, which is what made them different machines.

| Row | P | Persistence (source) | decayMs | Trail at 20x |
|---|---|---|---|---|
| Green Long | P39 | "Long" (class) | 150 | 3.0 s |
| Green Fast | P31 | "Medium short 0.01-1 ms" | 1 | 20 ms |
| White | P45 | "Medium" (class) | 10 | 200 ms |
| Blue Fast | P47 | "Very short" (class) | 0.05 | 1 ms |
| Red Projector | P56 | "Medium" (class) | 10 | 200 ms |

**Most of these publish a CLASS, not a figure**, so `decayMs` comes off a ladder
(very short 0.05, short 0.5, medium short 1, medium 10, long 150, very long
1000) which is THIS REPO'S interpretation and is labelled as such in
`PresetInfo`. The ordering is the source's; only the numbers between the rungs
are ours. The alternative -- one fallback for every class-only row -- made P39,
whose entire identity is a long tail, decay exactly like P45.

**P39 takes P1's chromaticity**, which is the honest call rather than a gap: it
is Zn2SiO4:Mn,**As** at 525 nm against P1's Zn2SiO4:Mn at 525 nm. The same
emitter with an arsenic co-activator added for persistence -- same light, longer
tail, which is precisely why it belongs beside P1 instead of replacing it.

**The glow has no switch any more.** A CRT palette is a claim that the page is a
tube, and a tube glows; they were never separate choices.

### P7, and the color-shifting decay it forced (shipped 2026-08-17)

P7 is the dual-layer one — a blue-white flash over a yellow-green layer that
runs ">1 minute in low ambient illumination". It is the only phosphor in the
table whose identity IS persistence, and it could not be a palette row as the
others are: **its trail is a different color from its fresh emission.** A pair
of hex values cannot say that.

So the glow grew a second control. `SimulatorOverlay::setPanelGlowTail(tint)`
takes the color the trail decays TOWARD; null (every ordinary phosphor) means
the trail keeps the tone it was drawn in. It is applied as a color multiply on
the ghost that ramps in as the ghost fades, so at full brightness the trail is
what was written and by the end it is the afterglow hue. `PresetInfo` carries
it per row (`afterglow`, null for all but P7), and
`CROSSPOINT_SIM_PANEL_GLOW_TAIL=RRGGBB` overrides it for a desktop or headless
run — the same escape hatch every other dial here has, and for the same reason:
without it the cascade's whole point could only be seen on a phone.

**Both of P7's layers are borrowed on chemistry, not eyeballed.** The flash is
P11's ZnS:Ag pulled toward white (P7's front layer is the same silver-activated
zinc sulphide); the tail's hue is P31's ZnS:Cu (same copper activator — the
cadmium in P7's (Zn,Cd)S:Cu shifts it yellower, which is the direction the
shipped `69FF87` sits in). Shipped: flash `0022A9` on `F1F2FF` light,
`C4C6FF` on `000327` dark, afterglow `69FF87`.

**Measured, because "it fades" is not the claim.** Headless A/B on a real page
transition, reading the ghost's emission over the paper it sits on:

| | fresh (150 ms) | decayed (900 ms) | G/R |
|---|---|---|---|
| tail unset (ordinary phosphor) | (161, 161, 178) | (50, 51, 56) | 1.00 → 1.02 |
| tail `69FF87` (P7) | (144, 161, 164) | (28, 51, 36) | **1.12 → 1.82** |

The control arm stays neutral as it dims; P7's trail goes green as it decays.
That is the property, and it is the thing a screenshot of a single frame cannot
show.

### Earlier candidate table, kept for the derivation

Owner asked to expand to the full list. These four are derived from the CIE
points in §2 by the same path the shipped rows use — xyY at Y=1 → XYZ → linear
sRGB → normalise → encode — then lifted toward white until they clear the band
the other CRT rows sit in (~10:1), which is the same treatment Red CRT needed in
§5:

| P | Chemistry | Persistence | Light | Dark |
|---|---|---|---|---|
| P31 | ZnS:Cu or ZnS:Cu,Ag | Medium short 0.01–1 ms | `0B4A1B` on `F2FFF3` (10.1:1) | `3DFF6F` on `03270A` (12.1:1) |
| P39 | Zn₂SiO₄:Mn,As | Long | *not derived — no published CIE* | |
| P45 | Y₂O₂S | Medium | `304248` on `F8FDFF` (10.3:1) | `B6EFFF` on `182327` (12.8:1) |
| P47 | Y₂SiO₅:Ce | Very short | `1D2B99` on `F2F2FF` (10.2:1) | `B0B4FF` on `030527` (10.3:1) |
| P56 | Y₂O₃:Eu | Medium | `7B0800` on `FFF1F1` (10.2:1) | `FFA5A4` on `270100` (10.2:1) |
| P7 | (Zn,Cd)S:Cu on ZnS | **dual**: blue-white short + yellow-green ">1 minute in low ambient illumination" | *not derived — two-layer, needs a two-tone treatment* | |

**Why they were declined once, and what changed.** §5 rejected the radar oranges
because they "would give two rows that paint nearly the same page", and every
candidate above is a SECOND row of a hue already present — P31 a second green
next to P1, P45 a second white next to P4, P47 a second blue next to P11, P56 a
second red next to P22R, P22B a third blue. By the standard set here, that was a
reason to decline, and it stood until the glow existed.

**Persistence is what changed it.** P11 is 2 ms and P31 is up to 1 ms while P39
is "Long" and P7 is over a minute. With the glow shipped, two rows of the same
hue are genuinely different to look at, because the difference is in how the
page decays rather than in its color — so the honest order was glow first, then
these rows, and that is the order they landed in. All of them are now shipped
(presets 19–25); `PresetInfo` carries each one's published persistence band
verbatim and the decay this repo interprets it as, and the ladder from band to
milliseconds is documented at that struct rather than being spread through the
rows.

**The ladder is this repo's interpretation, and is labelled as such.** The
published figures are 2–33 ms, one to two frames, and invisible. It is the RATIO
between phosphors that is real; the multiplier is taste, and taste lives in the
host (`kGlowScale` in the iOS shim), not in the HAL — which is handed a duration
and knows nothing about phosphors at all.


---

## 10. The whole registry (2026-08-17)

Owner ruling: **"be sure to include all possible phosphors."** Every JEDEC
P-number in the source table now has a row, except the exclusions named below.

**42 phosphor rows**, presets 6–55, sorted hue-first and fastest-to-slowest
inside each hue, cascades then the scotophor last.

### CORRECTION 2026-08-17: the first derivation washed every hue out

Owner picked **Terminal Green** and reported a mismatch between the row and the
page. He was right, and the fault was in the derivation, not the picker: every
script-derived green came out a pale mint (`81FFB5`, `81FFD7`, `81FF99`…) where
the hand-derived P1 is `33FF33`. P20 rendered `A5FF81`, a washed lime.

The cause: for an out-of-gamut spectral colour the first version **added
equal-energy white** until every component went non-negative, then broadened by
another 22% toward white. Both operations dump white into saturated hues.
Clamping negatives to zero instead — the obvious alternative — fixes the
saturation but **collapses the family**: 520, 525, 530, 543, 544 and 545 nm all
land on the same `59FF59`.

Both attempts were wrong in the same place. **A phosphor's chromaticity is not
its peak wavelength's.** It emits a band tens of nm wide, and a band sits well
inside the spectral locus. So the broadening now happens FIRST, in chromaticity
space, before any gamut mapping: the locus point moves 18% toward D65.

**That figure is fitted, not chosen.** The four phosphors here with both a
published peak and a measured CIE point (P1, P11, P22R, P47) give a best fit at
k = 0.18, mean error 0.042 in xy; P11, P22R and P47 land within ~0.03, and P1 is
worst at 0.06 because willemite's band is unusually broad. A measured
chromaticity still beats the model everywhere it exists.

Result — vivid and, crucially, still distinguishable:

| | before | after |
|---|---|---|
| P15 504 nm | `81FFD7` | `00FFCA` |
| P24 505 nm | `81FFD5` | `00FFC7` |
| P46 530 nm | `81FFB5` | `00FF97` |
| P43 545 nm | `81FF95` | `00FF5B` |
| P20 555 nm | `A5FF81` | `7CFF00` |

**Two rows were also renamed, because the name promised a hue the source does
not give.** JEDEC calls P20 "Yellow-Green", so "Terminal Green" was overselling
it — it is now **Yellow-Green Long**. P34's source colour is "Bluish Green-Yellow
Green" with no published peak, so "Storage Green" became **Green Longest**,
which claims only what is actually known about it (that it is the slowest).

### Derived by script, not by hand

`tools/derive_phosphors.py` + `tools/phosphor_table.py` +
`tools/gen_phosphor_rows.py`. Twelve rows were hand-derived and that was fine at
twelve; thirty more by hand guarantees they drift from each other — one lifted a
little further toward white, one rounded differently. One method now applies to
every new row:

1. published peak wavelength → CIE 1931 xy (Wyman/Sloan/Shirley analytic fits,
   JCGT 2013, ~1% of peak error)
2. xy at Y=1 → XYZ → linear sRGB, D65
3. negatives clipped, desaturated toward white only as far as the gamut requires
4. **band broadening**: 22% toward white, because a phosphor is a BAND and
   rendering its peak as a spectral line is more saturated than any real tube
5. paper tinted 25% toward the phosphor (light) or 1% of it (dark)
6. ink lifted until the pair clears 10:1

**A measured CIE point always beats a reconstructed one.** The seven rows with a
published chromaticity keep it, and the white phosphors (P6, P18, P23, P35, P40)
are taken from the JEDEC white region rather than from a two-peak monochromatic
mix, which produced obviously wrong tinted "whites".

### Two more cascades

P14 (*"Blue with Orange persistence"*) and P17 (*"Blue-Yellow, Blue-Short
Yellow-Long"*) join P7. Each has its **own** afterglow constant — sharing P7's
green would have made all three decay to the same hue and thrown away the only
thing that distinguishes them. The test now pins that all three tails differ.

### One scotophor

**P10 (KCl) does not emit — it darkens.** A dark-trace tube's beam colours the
F-centres and the trace goes dark violet on the screen's own pale ground, so it
is the one CRT row whose LIGHT pair is the authentic one and whose "ink" is not
a phosphor colour at all. Derived by hand, marked in the table.

### A trail floor of one frame

P46 is published at 70 ns and P24 at 1–10 µs. Compressed honestly those are
0.7 ms and 6 ms — less than one frame at 60 Hz, i.e. a trail that is drawn zero
times. `kTrailFloorMs = 16.7` is the smallest lie that keeps "very fast
phosphor" meaning "one frame of ghost" rather than meaning nothing.

### Rows that paint the same page

The duplicate check was absolute and is now conditional, which is a ruling:
**two rows may share tones if they decay differently.** It is driven off
`kPresetInfo` rather than the old hand-written list — which had silently stopped
covering anything appended after it, and would have let all thirty rows land
unchecked.

Exactly one pair is identical in both tone AND decay, and it is listed by name
in the test: **P19 (KF,MgF₂):Mn and P38 (Zn,Mg)F₂:Mn** — both 590 nm, both
"Orange-Yellow", both "Long". Different chemistry, no published difference in
emission, so deriving a difference would be inventing one. They ship as twins
because a catalogue that silently drops the second of an identical pair is not
the catalogue that was asked for.

P13/P27 (640/635 nm) survive as distinct: identical light page, one byte apart
in the dark one. The rule is now "identical in BOTH polarities".

### Excluded, and why

| | Reason |
|---|---|
| **P29** | "Alternating P2 and P25 stripes" — a striped screen, not a two-tone page. Nothing here can render it honestly. |
| **P4 (Cd-free)** | A re-formulation of P4, not a separate colour. Same row. |
| unnumbered entries | The table's trailing "additional phosphor types" have no P-number and no distinct published emission. |

Nothing else in the source table is left out. P16's peak is 380 nm (UV) and is
rendered at 400 nm, the visible edge of what that tube looks like — noted rather
than silently fudged.
