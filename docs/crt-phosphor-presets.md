# The CRT page-color presets, and where their colors came from

Written 2026-08-16, when **Red CRT (11)** and **Gray CRT (12)** were appended to
`src/PanelPalette.h`. It records the phosphor research behind all four CRT rows,
the arithmetic that turned published chromaticities into the shipped bytes, and
the two candidates that were **rejected** — because the rejected half is what
stops the same idea being re-proposed every six months.

Every CIE coordinate below was read from the cited source. Every sRGB hex is
**our conversion**, not something a source printed; no source in this research
stated an sRGB value for any phosphor.

The rendered proofs — all four halves plus both rejected candidates, uncropped
at 480x800 — are published at
<https://claude.ai/code/artifact/8b634a2c-2e50-4c04-b916-f10aa718cf80>. That
page is the view; this file is the record.

---

## 1. What the four rows actually are

| Row | Phosphor | Composition | CIE x, y | Source |
|---|---|---|---|---|
| Green CRT (6) | **P1** | Zn₂SiO₄:Mn (willemite) | 0.208, 0.704 | Phosphor Technology Ltd, grade GK |
| Amber CRT (7) | **P3** | Zn₈BeSi₅O₁₉:Mn | *none published* | see §4 |
| Red CRT (11) | **P22R** | Y₂O₂S:Eu | 0.647, 0.343 | Phosphor Technology Ltd, grade QKL63 |
| Gray CRT (12) | **P4** | ZnS:Ag + (Zn,Cd)S:Cu and variants | *none published* — JEDEC white region used instead, see §3 | US 4512912 |

Verified directly (not via a summary) on 2026-08-16:

* Phosphor Technology Ltd's CRT phosphor table — P1 **0.208 / 0.704**,
  P22R **0.647 / 0.343**, P56 **0.650 / 0.346**, P31 **0.287 / 0.521**.
  <https://www.phosphor-technology.com/crt-phosphors/>
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

All four verified in pixels through the real renderer, not asserted — see
`docs/headless-qa.md` for the recipe. Reading the dominant colors back out of
each capture gives exactly the ink and paper above, plus the two interpolated
2-bit grays in the light halves (`#A45854` / `#DFB2B0` for Red,
`#737C85` / `#BECAD4` for Gray).

---

## 6. Open, for the owner to rule on

1. **Does Red CRT's dark half get to be actually red?** It is `#FF6F6C`
   (a bright scarlet) because 7:1 forbids anything more saturated — the
   authentic `#FF1B00` measures 5.41:1 against pure black and cannot be fixed.
   Making it authentic requires a **second** low-contrast exemption alongside
   Solarized, which the test deliberately blocks. Default answer taken here:
   no, keep the floor, ship the lifted red.
2. ~~**Spelling.**~~ **Settled while this was in progress — not open.** The row
   was written as "Grey CRT", which is how the work was asked for. `f0e5210`
   then landed on `main` mid-session carrying the owner ruling *"always use
   american spellings"*, so it ships as `kPresetGrayCrt` / **"Gray CRT"**,
   matching the existing `kPresetCoolGray` / "Cool Gray". The rest of this
   file was swept the same way.
3. **The Root.plist rows print the LIGHT figure**, as all eleven existing rows
   do. For Red CRT that means the label says 10.2:1 while the dark half is
   7.33:1. Printing both, or printing the weaker half, would be a change to
   every row, not just these two.
