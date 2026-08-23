# Paper colorimetry: measured sources for the light-mode paper table

Research pass 2026-08-22, for the twelve papers in
[src/LightInkPalette.h](../src/LightInkPalette.h) (`lightink::kPapers`) and the
tooth/formation fields they drive in [src/Letterpress.h](../src/Letterpress.h).
Companion to [ink-colorimetry-sources.md](ink-colorimetry-sources.md) and
[ink-palette-research.md](ink-palette-research.md), which this doc builds on
and does not re-derive (the ISO 12647-2 paper types, the FOGRA39/47/51/52
substrate Lab values and the ISO 2846-1 reference paper are taken from there
as already-verified).

**Method.** Every hex below marked "derived" was computed by this pass from a
published CIELAB value with the same pipeline as the ink doc: Lab(D50, 2°) →
XYZ(D50) → Bradford adaptation to D65 → linear sRGB → gamma encode. The source
Lab is always shown beside the hex. The converter was validated by reproducing
the ink doc's own derivations byte-for-byte (FOGRA51 paper 95.00/1.50/−6.00 →
`#EFF0FC`; K 16/0/0 → `#282828`).

**Transport honesty.** This session had no general web search (the quota was
consumed by the ink passes). Everything here came through scholarly APIs
(OpenAlex, Crossref, Europe PMC), direct fetches of known repositories (ICC
characterization-data registry, AIC Book and Paper Group annuals, J-Stage,
paperonweb, the University of Iowa *Paper through Time* site), and a render
proxy for two blocked pages. Several literatures that certainly hold more
(De Gruyter's *Restaurator*, JSTOR's *Drawing on Blue*, TAPPI) are paywalled
and are recorded below as located-but-unread rather than silently skipped.

**Provenance key** (same scheme as the ink doc):

- **[MEASURED]** — an instrumental number from a standard, a characterization
  dataset read directly, or a peer-reviewed measurement.
- **[FETCHED]** — the page/PDF was read by this pass; claim quoted or
  paraphrased from it, but it is not itself an instrumental color value.
- **[SNIPPET]** — seen only in a search result or abstract; not verified
  against the full source.
- **[UNMEASURED-WEB]** — a circulating figure with no instrument behind it.
- **[DERIVED]** — this pass's own computation or inference, flagged as such.
- **[NOT FOUND]** — hunted and not obtainable; a first-class negative result.

**The shipped twelve, in Lab** (inverse of the shipped bytes, this pass's
computation, for comparison against every measured value below) [DERIVED]:

| # | Row | Hex | L* | a* | b* |
|---|---|---|---|---|---|
| 0 | Bright White | `#FBFBF9` | 98.6 | −0.3 | +1.0 |
| 1 | Cream | `#F8F0D9` | 95.0 | −0.0 | +12.2 |
| 2 | Bone | `#EFEAE0` | 92.9 | +0.5 | +5.5 |
| 3 | Chamois | `#ECDAB7` | 87.9 | +2.4 | +19.7 |
| 4 | Press Gray | `#E9EAEC` | 92.7 | −0.1 | −1.1 |
| 5 | Sepia Toned | `#EEDFCC` | 89.7 | +3.0 | +11.3 |
| 6 | India | `#F9F3E9` | 96.1 | +0.8 | +5.6 |
| 7 | Vellum | `#F9E7D7` | 92.8 | +4.4 | +10.1 |
| 8 | Laid Antique | `#E3DBCA` | 87.7 | +0.7 | +9.4 |
| 9 | Kozo | `#EEE6C3` | 91.3 | −1.4 | +18.2 |
| 10 | Azzurrata | `#E0E0ED` | 89.5 | +1.8 | −6.4 |
| 11 | Newsprint | `#DEDCD3` | 87.7 | −0.5 | +4.7 |

---

## 1. Measured anchors for the stock classes we ship

### 1a. Newsprint — the best-measured stock in the table

Three measured substrate whites, all read directly from the ICC
characterization-data registry by this pass (each file states its own
measurement condition in its header):

| Dataset | Substrate (quoted from file header) | Paper Lab | Derived hex |
|---|---|---|---|
| **FOGRA42** ([registry](https://registry.color.org/cmyk-registry/fogra42), [chardata](https://registry.color.org/cmyk-registry/chardata/FOGRA42.txt)) | *"Offset printing, based on ISO 12647-2:2004, OFCOM, paper type SNP (Standard Newsprint)"*; D50/2°, 45/0, white backing | **82.38 / 0.11 / 3.28** | `#CFCDC7` |
| **IFRA26** ([registry](https://registry.color.org/cmyk-registry/ifra26), [chardata IFRA26S](https://registry.color.org/cmyk-registry/chardata/IFRA26S.txt)) | *"Newspaper Coldset-Offset printing according to ISO/DIS 12647-3:2004. standard newsprint, screen ruling 40 l/cm"*; GretagMacbeth SpectroScan, D50/2°, 45/0, white backing | **85.2 / 0.9 / 5.18** | `#DAD4CB` |
| **FOGRA48** ([registry](https://registry.color.org/cmyk-registry/fogra48), [chardata FOGRA48L](https://registry.color.org/cmyk-registry/chardata/FOGRA48L.txt)) | *"ISO 12647-2:2004, OFCOM, paper type INP (Improved Newsprint), 49 g/m2"*; M0, white backing | **88.00 / −0.00 / 2.00** | `#DEDDD9` |

All three **[MEASURED]**. The IFRA26 K solid was also read: **36.76 / 1.48 /
4.46** — a WARM black at L*36.8, which is what body ink actually is on
newsprint and nearly 21 L* units lighter than coated-stock K. (The FOGRA42
and FOGRA48 "K solid" patches returned by the reader were visibly wrong —
blue values — so only IFRA26's is carried; the paper whites, patch
`0/0/0/0`, are unambiguous in all three files.)

The mill datasheet the shipped row already cites — Norske Skog NorNews,
ISO 5631 C/2°: **L\* 82, a\* −1.1, b\* +5.3** → `#CDCCC2` — was verified in the
prior session and is retained from
[light-ink-picker.md](light-ink-picker.md) §9b [MEASURED, prior session; note
the different illuminant/observer convention: ISO 5631 is C/2°, the FOGRA
files D50/2°, so the a\*/b\* are not strictly commensurable with the rows
above].

**Brightness.** Newsprint ISO brightness is listed as **62–65** in
paperonweb's typical-properties table
([paperpro.htm](http://www.paperonweb.com/paperpro.htm)) [FETCHED, tertiary
source]. The task brief's "~57–63%" lower bound could not be verified this
session [NOT FOUND — the figure is plausible for Canadian standard newsprint
but nothing readable was found behind it].

**Two findings against the shipped row:**

1. **The deliberate lift is confirmed necessary.** Real standard newsprint
   (FOGRA42, `#CFCDC7`, Y = 0.611) fails the repo's 7:1 floor: worst ink
   ~6.7:1 (this pass, WCAG arithmetic over all 17 shipped inks) — matching
   the repo's own 6.81:1 finding. It cannot be offered under the floor,
   exactly as §9b already says.
2. **The lifted row is, measurably, IMPROVED newsprint.** FOGRA48's improved
   newsprint at 88.00/0/2.00 derives to `#DEDDD9` — within 6 code values of
   the shipped `#DEDCD3` on every channel, and it clears the floor (worst
   ink 7.78:1, this pass). The shipped "fresh newsprint, lifted" is
   byte-close to a real, measured grade with a name. See §5, correction C1.

### 1b. Modern woodfree / press stocks (Bright White, Press Gray context)

Carried from the ink doc, not re-derived [MEASURED, per
[ink-colorimetry-sources.md](ink-colorimetry-sources.md)]:

| Substrate | Lab | Hex (derived, this pass) |
|---|---|---|
| ISO 12647-2:2004 PT1 gloss-coated wood-free (black backing) | 93 / 0 / −3 | — (coated; not a book stock we model) |
| ISO 12647-2:2004 PT4 uncoated white, bb | 92 / 0 / −3 | `#E6E8EE` |
| ISO 12647-2:2004 PT5 uncoated slightly yellowish, bb | 88 / 0 / 6 | `#E0DCD1` |
| ISO 12647-2:2004 PT5, white backing | 90 / 0 / 9 | `#E8E2D1` |
| ISO 2846-1:2017 ink-test reference paper | 94.8 / −0.9 / 2.7 | `#F0F0EB` |
| FOGRA39 paper (2004-era coated, M0) | 95.00 / 0.00 / −2.00 | `#EFF1F4` |
| FOGRA51 paper (2013-era premium coated, M1) | 95.00 / 1.50 / −6.00 | `#EFF0FC` |
| FOGRA52 paper (wood-free uncoated, OBA-heavy, M1) | 93.50 / 2.50 / −10.00 | `#EAEBFF` |

Reading for our table: **PT4 (92/0/−3) is the measured "cool press stock"** —
a modern uncoated white whose mild blue is OBA. Our Press Gray (92.7/−0.1/−1.1)
sits at the same L\* but only a third of the blue; it is a *less-brightened*
uncoated white than the standard's, which is defensible but should be said
(§5, C2). **PT5 (88/0/6) is the measured modern unbrightened/lightly
brightened book wove** — the closest standards-grade anchor to our
Bone/Sepia band.

**Bright White:** no verified mill datasheet was obtained for the named
exemplar class (Mohawk Superfine; the site blocked both fetch paths)
[NOT FOUND]. The circulating "96–98 brightness" for premium text stock is
[UNMEASURED-WEB]. What CAN be said with measurement behind it: an
unbrightened bright sheet measures b\* ≥ 0 (ISO 2846-1's reference paper,
94.8/−0.9/+2.7; the shoji study's OBA-free sheets, §1d, all b\* positive),
and every OBA sheet measures b\* well negative under M1. Our Bright White at
b\* +1.0 is therefore **defensible as a non-brightened bright stock, and only
as that** — it cannot stand in for a modern brightened sheet, which is the
argument for a thirteenth row (§5, G1).

### 1c. Cream book wove, pre-OBA — the anchor is indirect

What was hunted: an instrumental L\*a\*b\* for unbrightened cream trade-book
stock, historic or reproduction. What was found:

- **ISO 12647-2:2004 PT5**, "uncoated, slightly yellowish", 88/0/6 (bb) —
  the standards-grade modern sheet closest to the unbrightened condition
  [MEASURED]. Our Cream (95.0/0/+12.2) is lighter and twice as yellow: it is
  a *new* cream sheet, where PT5 is a working offset stock.
- **University of Iowa, *Paper through Time*** (Barrett et al.,
  [paper.lib.uiowa.edu](https://paper.lib.uiowa.edu/), 1,578 specimens,
  14th–19th c., ASD spectrometer calibrated against an X-Rite) [FETCHED]:
  color is reported **only as ΔL\*/Δa\*/Δb\* against a reference, not as
  absolute Lab**, so it anchors trends, not tones: *"the mean values start
  out light, become darker, and then lighter again but they never attain the
  lighter fifteenth-century values until the invention of chlorine bleach
  around 1800."* I.e., good 15th-century rag paper was LIGHT, and the
  darkening of intermediate centuries partially reversed around 1800.
- Absolute CIELAB of historic book papers: **[NOT FOUND]** through open
  channels. The SurveNIR reference collection (≈1,400 dated historic papers,
  Strlič group) is the known dataset most likely to hold it; nothing openly
  readable surfaced. Barrow's permanence surveys predate CIELAB (reflectance
  "brightness" only) and were not obtainable this session.

So Cream/Bone/Chamois remain **reconstructions bracketed by measurement**:
lighter and yellower than PT5 at the fresh end (Cream), converging on PT5
(Bone), and beyond it toward the aged direction §4 supports (Chamois).

### 1d. Kozo / washi — a real measured anchor, with a caveat

**Hirai, Yokoyama & Gunji, "Study on Optical Property of Shoji Papers",
*J. Textile Machinery Soc. Japan* 56(7), 2003, T35–T40**
([J-Stage PDF](https://www.jstage.jst.go.jp/article/transjtmsj1972/56/7/56_7_T35/_pdf),
read in full by this pass) — ten commercial shoji papers including handmade
100% kozo (sample A) and machine-made 100% kozo (B), measured on a Suga
multi-light-source spectrophotometer, C illuminant, 2° observer:

- **[MEASURED]** The OBA-free sheets (A, B, C — the kozo-dominant ones) sit
  at **b\* positive, roughly +2 to +3, L\* ≈ 93–94.5** (read from the paper's
  Fig. 7 scatter, axes b\* ±5, L\* 92–95; reading error ~±0.5 unit
  [DERIVED from published figure]). Approximate hex for sample A at
  93.7/−0.5/+2.7: `#EEEDE8`.
- **[MEASURED]** The OBA-loaded machine sheets (D–J) sit at **b\* −1 to
  −4.5** — *"The commercial shoji papers often show a bluish whiteness
  according to the use of a fluorescent agent."*
- **[MEASURED]** After 80 h fade-o-meter exposure **every sample, OBA or
  not, ends at b\* positive (~+1 to +3)** — the OBA dies and the fibre
  yellows: *"The fastness of the agent to sunlight was not so excellent."*
- **[MEASURED]** Formation: the image-analysis formation index (CV of
  absorbance ×10; higher = cloudier) is **131.3 for handmade kozo vs 60–97
  for the machine sheets**, and the flock-size index is largest for the kozo
  sheets (24.5 vs 17.5–20.8): *"the shoji paper predominantly composed of
  broussonetia-kazinoki (Kozo) contains local aggregations of fibers."*
- **[MEASURED]** Surface: handmade kozo has the LOWEST specular (60°/60°)
  reflectance of the set and the highest diffuse share — *"the surface of
  the [machine] papers tends to become smooth… reflect light more directly
  and luster artificially as compared with hand-made shoji papers."*

**The caveat:** these are *white* (bleached-furnish or at least pale) shoji
sheets. Our Kozo row models UNBLEACHED washi at b\* +18.2, six times the
measured white-washi yellowness, and **no instrumental measurement of
unbleached kozo's tone was found** [NOT FOUND]. The row's hue depth is a
reconstruction; the measured support it does have is directional (kozo
without OBA is warm, never blue) plus the formation and surface findings
above, which are the strongest measured support any row's TOOTH claim has.

### 1e. Historic laid rag paper (Laid Antique)

Tone: no absolute Lab (§1c). Structure: the best-measured aspect of the whole
table — see §3c, which is directly renderable and currently unrendered.
The Iowa trend (§1c) supports the row's premise that a rag sheet reads
gray-cream rather than the yellow of aged wood pulp: rag papers surveyed
across five centuries stay comparatively light, and their darkening is
gradual rather than the groundwood cliff of §4.

### 1f. Parchment / vellum

**[NOT FOUND — but located.]** A study measuring exactly what we need exists:
**"Changes in Some Properties of Aged and Historical Parchment"**,
*Restaurator* 21(3), 2000,
([doi:10.1515/rest.2000.138](https://doi.org/10.1515/rest.2000.138)) —
modern parchment aged at 70/100/134 °C, properties **including colour
change** compared against historical parchments of the 5th, 18th/19th and
20th centuries. The abstract (read via OpenAlex) confirms colour was
measured; the numbers are behind De Gruyter's paywall and a CAPTCHA blocked
the render proxy. Anyone with library access can close this gap from that
one paper. The IDAP parchment-damage-assessment project was also hunted and
nothing openly readable surfaced. Our Vellum row (92.8/+4.4/+10.1, the
pinkest sheet in the table) therefore remains a reconstruction; its one
mechanistic claim — hair side and flesh side differ and neither is uniform —
is standard conservation description and stays [UNMEASURED-WEB].

### 1g. Carta azzurrata — mechanism sourced, tone not

Two conservation sources read in full [FETCHED]:

- **Irene Brückle, "Historical Manufacture and Use of Blue Paper", *AIC Book
  and Paper Group Annual* 12 (1993)**
  ([full text](https://cool.culturalheritage.org/coolaic/sg/bpg/annual/v12/bp12-02.html)):
  the blue is **dyed rag** — *"indigo obtained from the native European woad
  plant, Isatis tinctoria; imported indigo produced from Asian plants of the
  genus Indigofera; imported South American logwood or campeachy; and the
  native European litmus or turnesol"* — with pigments (*"smalt, Prussian
  blue, indigo, and synthetic ultramarine"*) added at the beater in later
  practice. And the aging direction: *"all blue papers have to be considered
  very susceptible to light fading."*
- **Roy Perkinson, "Summary of the History of Blue Paper", *BPG Annual* 16
  (1997)**
  ([full text](https://cool.culturalheritage.org/coolaic/sg/bpg/annual/v16/bp16-10.html)):
  timeline — earliest known example a Venetian woodcut ca. 1480; Venice/
  northern Italy through the 1500s (Dürer 1508, Leonardo 1510); Prussian
  blue used for light blue papers from the 1770s; smalt "blueing" frequent
  in England.

Both confirm the repo's §9b history. **Instrumental Lab of any historic blue
sheet: [NOT FOUND].** The one modern technical volume certain to hold
measurements — *Drawing on Blue* (2024), whose chapter "Examination of Blue
Paper" is exactly this topic
([doi:10.2307/jj.8137439.11](https://doi.org/10.2307/jj.8137439.11)) — is on
JSTOR and was not readable this session. Located-but-unread.

### 1h. India / Bible paper

**[MEASURED-adjacent, FETCHED abstract]** *Japan TAPPI Journal* 45(10), 1991
([doi:10.2524/jtappij.45.1079](https://doi.org/10.2524/jtappij.45.1079)):
*"The first thin paper was made as printing paper for the Bible at Oxford in
1841. The basis weight of thin paper is up to 40 g/m2… India paper is
printing paper for dictionaries or the Bible. The origin of this paper is
NAJIO-TORINOKO which is a kind of WASHI."* — confirms the class (≤40 g/m²,
Bible/dictionary stock) and adds a date nuance: the famous 1875 Oxford
launch (the repo's §9b date) was the commercial revival of an 1841 specimen
Bible. **Colorimetry of India paper: [NOT FOUND]** — no instrumental tone
anywhere reachable. The row stays a reconstruction; its defining renderable
property remains show-through (roadmap §1a), not tone.

---

## 2. Optical brighteners — the modern/historic divide

**The standards, verified by title** (via Crossref/BSI records, since ISO's
own catalog was unreachable this session) [FETCHED]:

- **ISO 2470-1** — *"Paper, board and pulps — Measurement of diffuse blue
  reflectance factor — Part 1: Indoor daylight conditions (ISO
  brightness)"* — illuminant C energy at 457 nm.
- **ISO 2470-2** — *"…Part 2: Outdoor daylight conditions (D65
  brightness)"* — same 457 nm band under D65, which carries far more UV, so
  an OBA sheet scores HIGHER under Part 2 than Part 1. The gap between the
  two numbers is itself an OBA meter.
- **ISO 11475** — *"Paper and board — Determination of CIE whiteness,
  D65/10° (outdoor daylight)"* (BSI record,
  [doi:10.3403/30287213](https://doi.org/10.3403/30287213)).
- **ISO 11476** — *"Paper and board — Determination of CIE whiteness, C/2°
  (indoor illumination conditions)"* (BSI record,
  [doi:10.3403/30287210](https://doi.org/10.3403/30287210)).
- **ISO 5631** — *"Paper and board — Determination of colour by diffuse
  reflectance"* — the C/2° colour method the NorNews mill sheet cites.

**The era signature, confirmed from data this repo already fetched**
[MEASURED]: coated-grade substrate b\* moved **−2 (FOGRA39, M0, 2004-era) →
−6 (FOGRA51, M1, 2013-era)**, and wood-free uncoated to **−10 (FOGRA52,
M1)**. The FOGRA51/52 file headers grade it explicitly against **ISO 15397**
(*"Graphic technology — Communication of graphic paper properties"*, title
verified via BSI): FOGRA51 *"fluorescence moderate (8–14 DeltaB)"*, FOGRA52
*"fluorescence high (> 14 DeltaB)"*. So the reading in the task brief is
confirmed: paper b\* under M1 is the era signature — every OBA generation
shows as more negative b\*, and part of the 39→51 shift is the measurement
condition itself (M0→M1) finally exciting the OBA that was already there.

**Independent confirmation from the washi study** [MEASURED]: OBA sheets
b\* −1 to −4.5, OBA-free sheets +2 to +3, and 80 h of light kills the OBA
and lands everything positive (§1d).

**Consequence for the table** [DERIVED]: negative b\* is *earned only by
brighteners or by blue dye*. Of our twelve, only Press Gray (−1.1, implied
mild OBA) and Azzurrata (−6.4, dyed) sit below zero — correct. Every
historic stock (Cream, Bone, Chamois, Sepia, India, Vellum, Laid, Kozo,
Newsprint) is positive — correct. Bright White at +1.0 is a NON-brightened
bright sheet and should be described as such — and the genuinely brightened
modern page (b\* −6…−10, faintly violet-blue) is absent from the table.
That is the measured argument for a thirteenth stock (§5, G1).

---

## 3. Physical structure → our sliders, with numbers

### 3a. Smoothness and the tooth ladder

Typical instrumental values obtained [FETCHED,
[paperonweb typical properties](http://www.paperonweb.com/paperpro.htm) —
tertiary but the only per-grade table reachable this session]:

| Grade | Parker Print-Surf (µm) | Bendtsen (ml/min) |
|---|---|---|
| Newsprint (40–49 g/m²) | **2.6–4.5** | 80–140 |
| Stationery/uncoated (45–135 g/m²) | **0.8–2.6** | 50–300 |

Plus the washi study's surface finding (§1d): handmade kozo has the lowest
specular/highest diffuse reflectance of ten sheets — instrumental support
for "handmade, never calendered" sitting at the rough end [MEASURED].

**Bekk and Sheffield per-grade tables: [NOT FOUND]** through open channels —
TAPPI T479/T538 and vendor application notes hold them but nothing readable
surfaced. Recorded so the next pass doesn't re-hunt the same ground without
a new channel.

**Verdict on the shipped ladder** [DERIVED from the above]: the ORDERING is
supported at every point measurement reaches —

- coated/calendered reference (1.00) < calendered thin India (1.12) <
  uncoated book (Cream 1.30, Bone 1.45): PPS says uncoated stationery is
  ~3× rougher than coated stock's sub-micron finish; India's heavy
  calendering putting it below every uncoated sheet is consistent but has
  no direct measurement [NOT FOUND for India specifically].
- Newsprint (1.70) above the uncoated-book band: PPS 2.6–4.5 vs 0.8–2.6 —
  supported [MEASURED ordering].
- Kozo (1.95) roughest: supported by the specular-reflectance measurement
  [MEASURED ordering]; Laid Antique (1.85) between newsprint and kozo is
  plausible and unmeasured.
- Press Gray 1.60 above Bone 1.45: no measurement either way [NOT FOUND].

No measured value contradicts the shipped ordering. The absolute amplitudes
remain chosen, as `Letterpress.h` already documents.

### 3b. Formation — what the literature measures, and the spatial scale

What is measurable and measured: image-analysis formation testers report a
**formation index** (coefficient of variation of transmittance/grammage) and
a **flock size index** over a ~100×100 mm area (the shoji study's FMT-2000
protocol, §1d) [MEASURED]; paper-physics work characterizes formation as the
**power spectrum of local grammage**, decomposing floc structure from
periodic streaks (e.g., *"Characterization of Non-stationary Structural
Non-uniformities in Paper"*, FRC 2001,
[doi:10.15376/frc.2001.2.1313](https://doi.org/10.15376/frc.2001.2.1313);
*"Fibre length effect on fibre suspension flocculation and sheet
formation"*, NPPRJ 2006,
[doi:10.3183/npprj-2006-21-01-p030-035](https://doi.org/10.3183/npprj-2006-21-01-p030-035),
which evaluates *"mean fibre floc size … by power spectrum analysis"*)
[SNIPPET — abstracts read, numbers paywalled].

**A citable floc-size-in-mm table: [NOT FOUND]** this session. What can be
said with sources: fibre flocs are aggregates of fibres whose own length is
1–3 mm (softwood), so floc scale is of order **several mm to a few cm**;
the formation instruments integrate over 100 mm squares because that is
where the structure lives; and the RELATIVE claim our model needs — that
handmade kozo is far cloudier than machine sheets — is directly measured
(formation index 131 vs 60–97, §1d) [MEASURED].

Consequence for the renderer [DERIVED]: `letterpress::kFormationCells = 3`
across the sheet puts one cell at roughly a third of the page — coarser
than real floc structure by an order of magnitude. Real formation
cloudiness on a book page is a texture with power concentrated around
~5–30 mm, i.e., dozens of cells across a page, not three. See §5, C4.

### 3c. Laid structure — measured geometry, directly renderable, not rendered

**The best-sourced renderable numbers in this document.** From *"Extracting
chain lines and laid lines from digital images of medieval paper using
spectral total variation decomposition"*, **Heritage Science 11 (2023)**
([doi:10.1186/s40494-023-01013-3](https://doi.org/10.1186/s40494-023-01013-3),
open access, read in full) [FETCHED; the averages cite van Staalduinen et
al. 2006]:

- **Laid lines: 5–15 lines per cm on average in medieval paper** — a pitch
  of **0.67–2.0 mm, typically ~1 mm**. Measured examples in the paper: 8,
  10, 11 lines/cm on Parker Library and Cambridge UL manuscripts
  [MEASURED].
- **Chain lines: 1.5–5 cm apart on average.** Measured page averages: 2.63,
  3.156, 3.37, 3.93 cm [MEASURED]. So the task brief's "25–30 mm" is inside
  the range but narrower than the truth — 26–39 mm measured, 15–50 mm
  quoted range.
- Chain spacing **tightens near the watermark** (*"chain line distances
  around a watermark tend to be smaller… the chain lines act as a support
  to the watermark wires"*) [FETCHED].
- Chain lines read darker/stronger than laid lines: they *"sit on top of
  the laid lines and therefore leave a larger imprint… described as a
  shadow"* — and Wikipedia's Laid-paper article adds the antique-laid
  mechanism: before the early 1800s the chain wires were attached directly
  to the mould's wooden ribs, which sucked extra pulp onto the rib line, so
  **antique laid shows darker strips along the chain lines**; post-1800s
  moulds lifted the wires and evened the sheet [FETCHED].
- The IPH International Standard (International Association of Paper
  Historians, 2013) is the registration convention (cm per 20 laid lines,
  chain distances) — cited in the Heritage Science paper; the standard
  itself was not directly readable [SNIPPET].

**This is the biggest missing texture in the model** — flagged in §9b and on
the roadmap as item 15, and this pass turns it from "a thing laid paper
has" into a drawable spec (§8, I5). At 1.85 px/mm equivalent: laid pitch
~1 mm → ~1.9 px; chain pitch 26–39 mm → ~48–72 px. The ~2 px laid pitch is
exactly the ST-008 hazard class the repo already documents: it must be
generated at output size, never in the framebuffer.

---

## 4. Aging trajectories

### 4a. Groundwood / newsprint under light

Three Restaurator studies located; abstracts read via OpenAlex (full texts
paywalled) [SNIPPET for magnitudes, FETCHED for the abstract claims]:

- **"The Influence of Light on Ageing of Newsprint Paper"**, *Restaurator*
  21 (2000) ([doi:10.1515/rest.2000.55](https://doi.org/10.1515/rest.2000.55)):
  *"Irradiating of groundwood paper (newsprint) by modified sunlight has a
  considerably high degradation effect which is manifested by yellowing,
  increased acidity and loss of mechanical qualities… the lignin component
  of such paper is most sensitive to light… The cellulose component of
  groundwood paper is resistant to the degradative effect of light."*
- **"Light-induced Oxidation of Newsprint Sheets in a Paper Block", Parts 1
  and 2**, *Restaurator* 27 (2006)
  ([Part 1](https://doi.org/10.1515/rest.2006.114),
  [Part 2](https://doi.org/10.1515/rest.2006.200)): colour change is a
  **balance of yellowing and bleaching**, set by the UV:VIS ratio reaching
  each sheet, and *"colour changes… are visible up to the tenth sheet in
  the block."*

**A published Δb\*-vs-exposure curve for newsprint: [NOT FOUND] in open
access.** The classic quantitative work (Leary; Heitner; *"Photoyellowing
of groundwood pulps"*, NPPRJ 1994) is paywalled. The famous "newsprint
yellows in days of sunlight" is left as [UNMEASURED-WEB] — mechanistically
certain from the above, numerically unpinned here.

### 4b. Rag paper by contrast

Iowa's five-century survey (§1c) [FETCHED]: rag papers stay light for
centuries; the drift across the corpus is slow darkening with the
16th–18th centuries darkest, partially reversed by chlorine-bleached stock
after ~1800 — nothing resembling the groundwood cliff. Consistent with
Restaurator 2000's "cellulose is resistant to light" [FETCHED]. Supports
the table's premise that Laid Antique is *gray-cream, not deep yellow*, and
that the deep-tan end (Chamois) belongs to wood-pulp-era stock.

### 4c. Thermal aging and the yellowing direction

Chromophore chemistry of cellulose aging is measured in the literature
(2,5-dihydroxyacetophenone and related carbonyls as key chromophores —
Talanta 2017,
[doi:10.1016/j.talanta.2017.02.053](https://doi.org/10.1016/j.talanta.2017.02.053))
[SNIPPET], and those chromophores absorb blue → **b\* rises with mild L\*
loss; a\* moves little on pure cellulose**. Every observation this pass
touched agrees with that direction: the shoji fade run (all sheets end
b\*-positive, §1d), the Iowa darkening trend (§4b), the foxing channel
signature (§4d). Magnitude tables for Δb\* under standard oven aging:
[NOT FOUND] open-access.

**Verdict on Chamois/Sepia hue directions** [DERIVED]: supported. Chamois
(+2.4 a\*, +19.7 b\*, L\* 87.9) is the b\*-dominant, slightly-warm,
mildly-darkened endpoint of exactly the measured direction; Sepia Toned's
stronger a\* (+3.0, pinker) matches the browning/foxing direction (§4d)
rather than pure-cellulose yellowing — right for a "toned sheet", which is
a treated/aged surface rather than clean fibre.

### 4d. Foxing

**Instrumental Lab of foxing spots: [NOT FOUND].** What exists and was read
[FETCHED]: *"Image-Based Quantitative Analysis of Foxing Stains on Old
Printed Paper Documents"*, **Heritage 2(3), 2019**
([doi:10.3390/heritage2030164](https://doi.org/10.3390/heritage2030164),
16th–20th c. books, camera RGB under controlled lighting): foxing regions
show *"significant brightness variations in blue color and green color
components while brightness levels of the red color component were
reasonably flat"* — i.e., a stain that eats blue first, then green, leaving
red: **b\*+ strongly, a\*+ mildly, modest L\* loss** [DERIVED from the RGB
finding; camera RGB is not colorimetry]. Stain vocabulary from the same
paper: *"spotty or diffused areas… with yellowish, brownish, reddish, or
blackish colors."* This matches the direction chosen for the repo's foxing
work in [paper-defects.md](paper-defects.md) and gives it its first
citable, if non-colorimetric, instrument reading.

---

## 5. Gaps and corrections

Corrections (tone/text changes an implementer could make now; append-only
discipline — tones may be corrected in place, indices never move):

- **C1 — Newsprint row: adopt the FOGRA48 anchor, in text.** The shipped
  `#DEDCD3` is within 6 code values of measured improved newsprint
  (FOGRA48, 88/0/2 → `#DEDDD9`) and both clear the floor. No byte change
  needed; change the row's STORY: it is not "fresh standard newsprint,
  lifted and named as a lie we own" — it is, to measurement precision,
  **improved newsprint (INP), a real grade**, with standard newsprint
  (FOGRA42 82.38/0.11/3.28 → `#CFCDC7`, fails the floor at ~6.7:1)
  recorded as the thing the floor excludes. Optionally nudge the tone to
  the derived `#DEDDD9` (Δ ≤ 6 code values) to sit exactly on the
  measurement.
- **C2 — Press Gray: name what the blue is.** At b\* −1.1 it is a mildly
  OBA-brightened uncoated white; the measured standards-grade equivalent
  (PT4, 92/0/−3 → `#E6E8EE`) is bluer. Either deepen to the PT4 derivation
  (Δ ≤ 3 code values per channel) and cite it, or keep the tone and note it
  models a *lightly* brightened sheet. Do not do both C2-deepen and G1 —
  after G1 the table wants Press Gray as the LOW-OBA gray it already is.
- **C3 — Kozo: scope the claim.** The b\* +18.2 depth is unmeasured; white
  kozo measures +2…+3 (shoji study). The row note should say "unbleached"
  is the reconstruction and that the measured support is the hue SIGN and
  the roughness/formation, which are instrumentally the best-supported in
  the table (§1d). No tone change proposed — an unbleached sheet IS much
  yellower than a white one; the depth is just not a measurement.
- **C4 — Formation cell count.** Real formation structure lives at mm-to-cm
  scale (§3b); 3 cells across a sheet is an order coarser. If the mottle is
  ever retuned, more cells (≈10–30 across the page width) is the direction
  measurement points; the ±55% symmetric-swing budget argument in
  `Letterpress.h` carries over unchanged because it is per-point.
- **C5 — India date nuance.** §9b's "from 1875" is the commercial launch;
  the first Oxford Bible-paper printing was 1841 (Japan TAPPI 1991, §1h).
  One clause in the doc, no code.

Gaps measurement argues to fill (new rows; append-only):

- **G1 — A true OBA-brightened modern stock is missing, and is the
  best-measured candidate row possible.** FOGRA51's substrate
  (95.00/1.50/−6.00 → `#EFF0FC`) is an actual measured M1 paper white, the
  reference the whole 2013-era print industry proofs against. Checked
  against this repo's own rules by this pass: clears 7:1 against all 17
  shipped inks (worst 9.34:1, Van Dyke), and ≥4 code values from every
  shipped row (nearest: Press Gray, ΔB 16). Tooth ≈ 1.0 (premium coated).
  The harder-brightened uncoated FOGRA52 (93.5/2.5/−10 → `#EAEBFF`, worst
  ink 9.08:1) is the alternative if the row should read "uncoated modern
  book page" rather than "coated proofing white"; it is also legal. One of
  the two, not both — they are 5 code values apart at the closest channel
  and the difference is a story about coating, not a visible pair.
- **G2 — A machine-calendered gloss art paper is NOT argued for.** §9b
  already rejected it as indistinguishable from row 0 in this model;
  measurement agrees (its distinguishing property is gloss/holdout, which
  the model does not render). Recorded so it stays rejected.
- **G3 — Aged newsprint stays excluded**, and now with two measured
  anchors for what is being excluded: fresh standard newsprint already
  fails (6.7:1), and aging only darkens (§4a). The §9c "second floor"
  discussion remains the honest lever; nothing new.

---

## 6. Summary table

| Stock | Best measured anchor | Source | Status |
|---|---|---|---|
| Bright White | unbrightened bright sheets measure b\* ≥ 0 (ISO 2846-1 ref paper 94.8/−0.9/2.7 → `#F0F0EB`); no mill datasheet verified | ISO 2846-1 via ink doc; Mohawk [NOT FOUND] | defensible as NON-brightened bright stock only |
| Cream | bracketed: PT5 88/0/6 → `#E0DCD1` (modern unbrightened wove) | ISO 12647-2:2004 T.1 | reconstruction between measured brackets |
| Bone | nearest: PT5 (above) | ISO 12647-2:2004 | reconstruction, closest row to a measured stock |
| Chamois | direction only: b\*+ dominant aging (§4) | Iowa; Restaurator; shoji fade | direction supported, magnitude unmeasured |
| Press Gray | PT4 92/0/−3 → `#E6E8EE` | ISO 12647-2:2004 | shipped row is less blue than the measured class (C2) |
| Sepia Toned | direction only: browning adds a\*+ (§4d) | Heritage 2019 foxing RGB | direction supported |
| India | class confirmed (≤40 g/m², Oxford 1841/1875); tone [NOT FOUND] | Japan TAPPI 45(10) 1991 | reconstruction |
| Vellum | measurements EXIST, paywalled | Restaurator 21(3) 2000, doi:10.1515/rest.2000.138 | located-but-unread; reconstruction |
| Laid Antique | structure: laid 5–15 /cm, chains 15–50 mm (26–39 measured) | Heritage Science 11 (2023) | tone reconstruction; STRUCTURE measured and renderable |
| Kozo | white kozo L\*≈93–94.5, b\*+2…+3; formation 131 vs 60–97; lowest specular | Hirai et al. 2003 (J-Stage) | hue sign + roughness measured; unbleached depth not |
| Azzurrata | colorants + fading sourced; tone [NOT FOUND] | Brückle 1993; Perkinson 1997 (BPG) | mechanism sourced; tone reconstruction |
| Newsprint | FOGRA48 INP 88/0/2 → `#DEDDD9` (≈ shipped); FOGRA42 SNP 82.38/0.11/3.28 → `#CFCDC7` (fails floor); IFRA26 85.2/0.9/5.18; NorNews 82/−1.1/5.3 (C/2°) | ICC registry chardata (fetched); mill sheet | **measured**; C1 renames the story |

---

## 7. What could not be found, stated plainly

1. **Absolute CIELAB of historic book/rag papers.** Iowa's 1,578-specimen
   survey publishes deltas only; SurveNIR's collection was not reachable.
   The largest single gap for this table.
2. **Parchment CIELAB** — exists in *Restaurator* 2000 (doi above), behind
   a paywall + CAPTCHA. Cheapest closure in this list: one library PDF.
3. **Blue paper CIELAB** — *Drawing on Blue* (2024), JSTOR
   jj.8137439.11, "Examination of Blue Paper". Second-cheapest closure.
4. **Unbleached kozo tone**, **India paper tone**, **foxing-spot Lab**,
   **Mohawk-class mill colorimetry** — nothing instrumental reachable.
5. **Δb\* magnitude curves**: groundwood photo-yellowing (NPPRJ 1994 etc.)
   and oven-aging b\* drift are paywalled; only directions are carried here.
6. **Bekk / Sheffield per-grade tables** — PPS and Bendtsen obtained
   (paperonweb), Bekk not.
7. **Floc size in mm** as a citable table — power-spectrum methods located,
   numbers paywalled.
8. **ISO 12647-3:2005's own aim values** — the standard text was not
   obtained; its measured realizations (FOGRA42, IFRA26) stand in, which is
   arguably better anyway (the aims are transforms, the chardata is ink on
   paper).
9. The **57%-end of the newsprint brightness range** in the task brief.
10. Transport note for the next pass: Bing (all formats) ignores operators
    and returns garbage for scholarly queries; DuckDuckGo CAPTCHAs;
    Semantic Scholar 429s without a key. What WORKS keyless: OpenAlex
    (`title_and_abstract.search`, abstract inverted-index reconstruction),
    Crossref (`query.bibliographic` — also resolves ISO/BSI standard titles
    via 10.3403 DOIs), Europe PMC REST, the ICC registry chardata files,
    cool.culturalheritage.org, J-Stage PDFs, and the r.jina.ai render proxy
    for JS-walled pages (blocked for google.com and De Gruyter).

---

## 8. Implementation notes — concrete changes an implementer could make

Each with its citation; none moves an index.

**Implementation status, 2026-08-22 (same day, follow-up session):** I1 and
C3 landed as comment/doc text (`src/LightInkPalette.h` Newsprint and Kozo
rows, [light-ink-picker.md](light-ink-picker.md) §9b); I2 was NOT taken (the
shipped bytes stay); I3 landed as row 12 "Brightened White" (`#EFF0FC`, tooth
1.05, formation 0.70 — the floor and separation re-proven by
`tests/light_ink_test.cpp`, worst ink 9.34:1); I4 was NOT taken (Press Gray
keeps its tone; after I3 the table wants it as the low-OBA gray, exactly as
this doc's C2 note says); I5 landed as `src/LaidStructure.h` +
`tests/laid_structure_test.cpp`, gated on a new per-stock `laid` flag and
documented in [letterpress-and-scanlines.md](letterpress-and-scanlines.md);
§3b's per-stock formation gap landed as `lightink::formationScaleFor` (kozo
1.90 on the measured 131-vs-60–97 index, India/Brightened White 0.70 floor).
I6 (the formation CELL COUNT, C4) and I7 (the aging dial) remain open; I8's
b\*-sign guard is carried by the per-channel tint-ramp test and the row
comments rather than a dedicated check.

- **I1 (text only).** Newsprint row note: cite FOGRA48 (INP, 88/0/2,
  `#DEDDD9`) as the measured grade the shipped tone coincides with, and
  FOGRA42 (SNP, 82.38/0.11/3.28, `#CFCDC7`, worst ink ≈6.7:1) as the
  measured grade the floor excludes. (§1a, §5 C1.)
- **I2 (optional, ≤6 code values).** Newsprint tone → `#DEDDD9` to sit
  exactly on FOGRA48. Verify with the existing 18×12 sweep; this pass
  measured worst ink 7.78:1.
- **I3 (new row, append).** "Brightened White" — FOGRA51 substrate
  95.00/1.50/−6.00 → `#EFF0FC`, tooth ~1.00–1.05, note "modern
  OBA-brightened proofing white, ISO 12647-2:2013 era; the page most books
  are printed on today". Pre-checked: 7:1 clears against all 17 inks
  (worst 9.34), ≥4 code values from every row. Alternative flavor: FOGRA52
  93.5/2.5/−10 → `#EAEBFF` (uncoated, harder-brightened; worst 9.08).
  (§2, §5 G1.)
- **I4 (text only).** Press Gray note: "lightly brightened uncoated white;
  the standards-grade PT4 measures bluer (92/0/−3 → `#E6E8EE`)". Or adopt
  the PT4 derivation outright if I3 is NOT taken. (§1b, §5 C2.)
- **I5 (the real texture work).** Laid structure for Laid Antique (and
  arguably Vellum stays clean): laid lines at ~1 mm pitch (5–15 /cm
  measured), chain lines at 26–39 mm (measured averages; 15–50 mm range),
  chains darker than laids, with the antique-laid extra: a soft dark strip
  ALONG each chain line (pre-1800s rib suction). At 1.85 px/mm that is
  ~1.9 px laid pitch — a regular field in ST-008 territory, so it must be
  generated at OUTPUT size like the grain and scanlines, never in the
  framebuffer; amplitude must stay darken-only and inside the letterpress
  paper budget so the 7:1 floor argument carries. Show-through (India,
  roadmap §1a) remains the other big absent texture. (§3c.)
- **I6 (if formation is retuned).** Raise `kFormationCells` toward 10–30
  across the page width; measurement puts real floc structure at mm–cm
  scale, not thirds-of-a-page. Budget math unchanged. (§3b, §5 C4.)
- **I7 (aging dial, future).** If an "age this sheet" dial is ever wanted,
  the measured direction is: b\* up strongly, L\* down mildly, a\* up
  slightly (more on wood pulp than rag); on a brightened sheet the FIRST
  move is the OBA dying — b\* rising through zero before any fibre
  yellowing shows (shoji 80 h fade; §2, §4). That is a one-dimensional
  locus per stock, same shape as the existing strength dial, and
  Beer–Lambert composition already fits it.
- **I8 (test guard, cheap).** If I3 lands, the light_ink test's paper-pair
  separation and floor sweeps cover it automatically; also pin that no
  OBA-negative b\* row ever claims a historic name in its note — the
  b\*-sign rule of §2 is the one colorimetric fact this whole document is
  most certain of.
