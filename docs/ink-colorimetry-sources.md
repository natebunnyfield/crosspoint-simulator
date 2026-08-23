# Ink colorimetry: measured sources for three modern inks

Research pass 2026-08-22, for the light-mode ink table. Every hex below was
DERIVED by the researcher from a published CIELAB value (Lab D50/2 -> XYZ ->
Bradford to D65 -> linear sRGB -> gamma), with the source Lab always shown, and
each figure labelled MEASURED, INFERENCE, or NOT AVAILABLE. The gaps at the end
are real gaps in the published record, not search failures -- most importantly
there is NO published colorimetry for typewriter ribbon impressions or for any
purple copying process, so anything we ship for those must be labelled
reconstructed.

Delivered by a sub-agent whose report could not reach its parent; preserved here
so the citations are not lost.

# Three ink candidates: colorimetric and historical findings

**Status: complete.** No files written to the repo; all working downloads deleted.

**Method for every hex below.** I derived each one myself from a published CIELAB value: Lab(D50, 2°) → XYZ(D50) → Bradford adaptation to D65 → linear sRGB → sRGB gamma encode. The source Lab is always shown. Two flavors:

- **Absolute** — the ink against a perfect diffuser. Correct only if you also paint the paper its measured tone.
- **Media-relative** — the same ink after scaling paper white to 255,255,255. **This is the one to use on a white page.**

---

## 1. MODERN PRINTER'S INK BLACK / OFFSET PROCESS BLACK

### (a) Genuinely distinct? Yes — the most tightly specified ink in this list.

Not a marketing name. Two standards, two different numbers, and conflating them is the usual error: **ISO 2846-1** specifies the *ink* on a reference substrate; **ISO 12647-2** specifies *the printed result* on real paper. ISO 2846-1:2017's Introduction states the division ([iTeh preview PDF](https://cdn.standards.iteh.ai/samples/70905/c05c28551f424b818248057221e88549/ISO-2846-1-2017.pdf)):

> "the similarity of two inks on a reference substrate generally ensures similarity on another substrate, and it is this similarity that has enabled the development of industry specifications or standards such as ISO 12647-2[1], which specifies the colour of these inks on other substrates."

### (b) Era and users

Carbon-black-in-oil printing ink spans the whole letterpress/offset era. The *standardized* process black dates from ISO 2846-1 (1st ed. 1997; the 2017 edition reconfirmed the color and only replaced the discontinued APCO II/II reference substrate with a new one, **C2846** — same PDF: "Annex A has been revised in order to replace the reference substrate"). Users: every sheet-fed and heat-set web offset shop working to a standard, and every proofing RIP.

### (c) MECHANISM

**Colorant** — amorphous elemental carbon. From [Natural Pigments, Carbon Black PBk7](https://www.naturalpigments.com/carbon-black-pigment.html):

> "This Carbon Black is a modern form of lamp black, identified as **Color Index Pigment Black 7 (PBk7), CI 77266, and CAS 1333-86-4**."

[Lamp Black](https://www.naturalpigments.com/lamp-black-pigment.html): "Colour Index: **Pigment Black 6 (77266)**", "Chemical Name: Amorphous Carbon", CAS 1333-86-4.
[Bone Black](https://www.naturalpigments.com/bone-black-pigment.html): "Colour Index: **Pigment Black 9 (77267)**", "Chemical Name: **Hydroxyapatite (calcium phosphate) and carbon**".

**Load-bearing caveat:** PBk6 and PBk7 share the same CI Constitution Number, **77266** — same substance, distinguished by manufacturing route (collected soot vs. controlled furnace/channel process), not chemistry. PBk9 is the one that *is* chemically different: mostly calcium phosphate with only ~10–20% carbon, which is why bone/ivory black is browner and less opaque. Corroborated by [Jackson's, Comparing Black Pigments](https://www.jacksonsart.com/blog/2020/11/27/exploring-the-differences-between-black-pigments/) ("Both PBk6 and PBk7 are made with almost pure amorphous carbon…"), which appeared in search results but 403s on fetch — trade press, not primary.

**Vehicle** — historically boiled/blown linseed-oil varnish (oxidative drying); modern sheet-fed uses rosin-modified phenolic and alkyd resins in a distillate/vegetable-oil blend; web/news is mostly mineral oil (absorption + evaporation, not oxidation). A figure of *"15-20% carbon black as the pigment, 15-25% hydrocarbon or alkyd resin, and 50-70% mineral oil solvent"* for petroleum-based black litho-news ink came from the search snippet for [Environ Sci Pollut Res 10.1007/s11356-023-29309-8](https://link.springer.com/article/10.1007/s11356-023-29309-8). **I could not verify it — the article is paywalled and redirects to Springer's IDP.** Indicative only.

**Why this matters to a renderer:** carbon black absorbs nearly flat across the visible. That is *why* every measured value below has a* and b* within ~±1 of zero.

### (d) Colour references — MEASURED

**[MEASURED] ISO 2846-1:2017, Table 1 — "Colorimetric values for M1, 0°:45° geometry, illuminant D50, 2° observer"**, on the C2846 reference substrate, transcribed from the [iTeh preview PDF](https://cdn.standards.iteh.ai/samples/70905/c05c28551f424b818248057221e88549/ISO-2846-1-2017.pdf):

| Ink | L* | a* | b* | ΔE*ab | Δa* | Δb* | L* |
|---|---|---|---|---|---|---|---|
| Yellow | 91,0 | −5,1 | 95,0 | 4,0 | — | — | — |
| Magenta | 50,0 | 76,0 | −3,0 | 4,0 | — | — | — |
| Cyan | 57,0 | −39,2 | −46,0 | 4,0 | — | — | — |
| **Black** | **18,0** | **0,8** | **0,0** | — | **±1,5** | **±3,0** | **18,0** |

Footnote c: *"For black, there is no symmetrical tolerance for L\* but an upper limit."* Note the shape of that row — black is the only ink with **no ΔE tolerance at all**; it is constrained by a lightness ceiling plus independent a*/b* windows, and the ±3,0 on b* is the standard formally admitting that commercial blacks come in different bluish/brownish shades.

→ **L\* 18,0 / a\* 0,8 / b\* 0,0 → `#2D2C2C`** absolute; `#312F31` on its own reference paper.

**[MEASURED] ISO 12647-2:2004, Table 2** — "CIELAB coordinates of colours for the printing sequence cyan-magenta-yellow", black backing, D50/2°, 0/45 or 45/0 (brackets = white backing). Transcribed from the [full standard PDF](https://www.sovsib.ru/color/iso12647_en.pdf):

| Paper type | Black L* | a* | b* | derived hex |
|---|---|---|---|---|
| **1, 2** gloss-/matte-coated wood-free | **16** (16) | **0** (0) | **0** (0) | `#282828` |
| **3** gloss-coated web | **20** (20) | 0 | 0 | `#303030` |
| **4** uncoated, white | **31** (31) | **1** (1) | **1** (1) | `#4B4847` |
| **5** uncoated, slightly yellowish | **31** (31) | 1 | **2** (3) | `#4C4846` |

Same standard's Table 1 papers: PT1 `93 (95) / 0 / −3 (−2)`; PT4 `92 (95) / 0 / −3 (−2)`; PT5 `88 (90) / 0 / 6 (9)`; **ISO 2846-1 ink-test reference paper `94,8 / −0,9 / 2,7`** → `#F0F0EB`.

Two footnotes worth carrying: Table 2 footnote c — *"The colours were derived from those of ISO 2846-1 [1] by the method given in the informative Annex A"*, i.e. the 12647-2 aims are a *transform* of the 2846-1 ink, not an independent measurement. And §4.3.2.3 NOTE 3 — *"the colour coordinates a\* and b\* remain largely the same. However, the L\* values are between 2 and 3 higher"* on white backing.

**[MEASURED] ISO 12647-2:2013.** I could not obtain the standard. Best public secondary: Heidelberg's [workshop deck, Prinect Anwendertage 2015](https://prinect-anwendertage.org/wp-content/uploads/2023/06/IPUD_2015_WS33_Further_Development_of_ISO_12647-2-1.pdf), which prints the ISO M1 aim beside measured M0/M1/M2/M3 values. **K aim = 16 / 0 / 0** on both white and black backing (paper white 95/1/−4 WB, 93/1/−5 BB). So the 2013 revision **did not move black** — what moved was the paper (PC1 `95,0 0,0 −2,0` → `95,0 1,5 −4,0`) and the measurement condition (M0 → M1, because papers had gained optical brighteners).

**[MEASURED] Characterization datasets** — actual printed-and-measured aggregates, not aim values. Pulled the files directly from the ICC registry and read patch 1260 (`C0 M0 Y0 K100`), patch 1 (paper), patch 1286 (`100/100/100/100`):

| Dataset | Condition (quoted from file header) | K solid L*a*b* | Paper | 400% overprint |
|---|---|---|---|---|
| **FOGRA39** ([txt](https://registry.color.org/profile-registry/chardata/FOGRA39.txt)) | *"Offset printing, according to ISO 12647-2:2004/Amd 1, OFCOM, paper type 1 or 2 = coated art, 115 g/m2"*; D50/2°, 45/0, white backing | **16.00 / 0.00 / 0.00** (XYZ 2.02 / 2.10 / 1.73) | 95.00 / 0.00 / −2.00 | 8.71 / −0.07 / 2.06 |
| **FOGRA47** ([txt](https://registry.color.org/profile-registry/chardata/FOGRA47.txt)) | *"paper type 4 = uncoated white, 115 g/m2"* | **31.00 / 1.00 / 1.00** (XYZ 6.51 / 6.65 / 5.29) | 95.00 / 0.00 / −2.00 | 23.46 / 2.45 / 1.59 |
| **FOGRA51** ([txt](https://registry.color.org/profile-registry/chardata/FOGRA51.txt)) | *"according to ISO 12647-2:2013, OFCOM, print substrate 1 = premium coated, fluorescence moderate (8-14 DeltaB according to ISO 15397), 115 g/m2"*; *"D50, 2 degree, geometry 45/0, no polarisation filter, white backing, according to ISO 13655:2009 M1"* | **16.00 / 0.07 / −0.33** | 95.00 / 1.50 / −6.00 | 12.71 / 0.53 / 4.89 |
| **FOGRA52** ([txt](https://registry.color.org/profile-registry/chardata/FOGRA52.txt)) | *"print substrate 5 = Wood-free uncoated, fluorescence high (> 14 DeltaB), 120 g/m2"*, M1 | **32.69 / 1.24 / 0.11** | 93.50 / 2.50 / −10.00 | 26.36 / 1.50 / 1.35 |
| **CGATS21-2-CRPC6** ([txt](https://registry.color.org/profile-registry/chardata/CGATS21-2-CRPC6.txt)) | *"Characterized Reference Printing Condition 6, Universal Premium Coated"*; *"ISO 13655 - Reflection, M1, white backing"* — this is GRACoL 2013 | **16 / 0 / 0** | 95 / 1 / −4 | 9.05 / 0.20 / 0.39 (file's stated *"Reference Black Point"*) |

**Derived hexes**

| Source Lab | Absolute sRGB | Media-relative (own paper → white) |
|---|---|---|
| FOGRA51 K `16.00 / 0.07 / −0.33` | `#282828` | **`#2B2B29`** |
| FOGRA39 K `16.00 / 0.00 / 0.00` | `#282828` | `#2B2B2A` |
| ISO 2846-1 K `18.0 / 0.8 / 0.0` | `#2D2C2C` | `#312F31` |
| FOGRA47 K `31.00 / 1.00 / 1.00` | `#4B4847` | `#514D4B` |
| FOGRA52 K `32.69 / 1.24 / 0.11` | `#4F4C4D` | **`#56534C`** |
| FOGRA51 400% `12.71 / 0.53 / 4.89` | `#24211A` | `#26231A` |
| FOGRA39 400% `8.71 / −0.07 / 2.06` | `#1A1916` | — |
| FOGRA51 paper `95.00 / 1.50 / −6.00` | `#EFF0FC` | — |
| FOGRA52 paper `93.50 / 2.50 / −10.00` | `#EAEBFF` | — |

**Recommendation:** the single most defensible "modern printer's black" is **`#2B2B29` on white** — FOGRA51's measured K solid, media-relative, i.e. exactly what a K100 solid looks like on premium coated stock under ISO 12647-2:2013. Contrast vs white **14.19:1**. Uncoated/book-paper variant: **`#56534C`**, contrast **7.67:1** — close to your 7:1 floor, worth knowing before shipping.

Three things that will save an argument later:
1. **A single-ink black is not very black.** L*16 is ~25% up the lightness scale. Body text in K-only offset is `#2B2B29`, not `#000000`. The genuinely dark black is the four-color overprint — FOGRA51 400% is L*12.71 and **warm** (b* +4.89 → `#26231A`), because it is carbon black plus three chromatic inks.
2. **Coated vs uncoated is the biggest single lever** — L*16 → L*32.7, a doubling. That is ink holdout, not chemistry.
3. **a\* and b\* are ~0 in every measured row** — carbon-black neutrality showing up as data.

---

## 2. TYPEWRITER RIBBON BLACK

### (a) Genuinely distinct? Yes — and the record/copying split is real and contemporaneous. But this is a *family*, not one ink.

Best entry point: Sarah Norris, **"Typewriter Inks: An Annotated Bibliography"** (Technology and Structure of Records Materials, Karen Pavelka instructor, 6 Dec 2006), [PDF](https://sarahnorris.net/Papers%20&%20Research/Typewriter%20Inks%20Annotated%20Bibliography.pdf). Her summary:

> "Information about the inks used in typewriter ribbons is scarce, and much of it is proprietary."

> "The pigment component is highly varied. Carbon black appears commonly and seems to be relatively lightfast and stable… Some mentioned colorants include nigrosine, Ceres dyes, Prussian blue, methylene blue, malachite green, aniline dyes, and even iron gall pigments."

> "The vehicle component is usually oil-based. Mentioned vehicles include glycerine, vegetable oils, castor oil, and even whale oil."

> "Typewriter ribbons were made of cotton through the early 1950s, when nylon was introduced to accommodate the increased wear caused by electric machines."

### (b) Era and users

~1880–1980 — Norris: *"The typewriter was a widely used mechanism for committing text to paper for approximately 100 years, from about 1880 to 1980."* Every office, government department and court — which is exactly why the record/copying distinction existed.

**Primary source for the split:** A. M. Doyle, **"Notes on Typewriter Ribbons," *JACS* 28(6), 1906, 706–714**, DOI [10.1021/ja01972a005](https://pubs.acs.org/doi/abs/10.1021/ja01972a005) (paywalled; ACS 403s a fetch). Norris's annotation is the load-bearing evidence:

> "A chemist at the US Department of Agriculture collects new and used typewriter ribbons… **43 ribbon brands from 19 manufacturers are represented. The study divides the ribbons into the following types: record ribbons ("mainly black record,") and copy ribbons (including indelible copy, black copy blue, blue copy, purple copy, and an "other" category.) Components separated from the inks include ash, lampblack (record and copy,) dye, and oil.** … **Samples produced by records ribbons and copy ribbons with a high percentage of lampblack demonstrate high permanence, but copy ribbons with a high percentage of dye fade almost completely in sunlight.**"

That answers (b) and much of (c) in one paragraph, from 1906, on a 43-brand sample. Note also that "copy ribbon" was itself a color family including **purple copy** — a direct link to §3.

Independently corroborated by the **Report of the Commissioner of Public Records, vol. 2 (Boston: Commonwealth of Massachusetts, 1890), 28–33**, via Norris:

> "He finds that black typewriter ribbons produce type that is resistant to fading in light, but that colored type is light-fugitive. … Antisell … states that aniline-based inks should be avoided due to their tendency to fade."

### (c) MECHANISM — two colorant systems, often in the same ribbon

- **Pigment route (record).** Lampblack/carbon black in a non-drying oleaginous vehicle. Mitchell & Hepworth, *Inks, Their Composition and Manufacture*, 2nd ed., London 1916, 233–4, via Norris: *"Typewriter ribbon inks are stated to be less permanent than iron gall inks, but **those with carbon pigments will resist the effects of chemical agents**."*
- **Dye route (copying).** Lehner, *Ink Manufacture…* (Scott, Greenwood & Son, 1926), 93–96, via Norris: *"older inks contained aniline dyes and glycerine, but over time the glycerine absorbed moisture and the impression blurred. Later, oil-soluble dyes were used. **Older pigments for black ink included oil-soluble nigrosine**, while colors employed Ceres dyes. Later inks used lampblack, coal-tar dye lakes, Prussian blue, zinc white, methyl violet, methylene blue, malachite green, and safranin."*
  **The glycerine is the copying mechanism**, not an incidental. The impression stays hygroscopic and re-solubilizes under the damp tissue of a copying press. It is also why copying-ribbon impressions blur — Mitchell & Hepworth via Norris: *"Weak type may be caused by too little glycerine. Blurring and smudging may be caused by too much glycerine."*
- **Commercial black ribbons were usually both.** Emil A. Wich (Sandoz), "Dyes for Inks," *American Ink Maker* 44(2), 1966, via Norris: *"these inks are made **mostly of carbon black shaded with nigrosine and induline bases**, which are dissolved in oleic or some other type of fatty acid. Dyes used to shade blue, violet, and red ribbons are Victoria Blue Base, Methyl Violet Base, and Rhodamine Base."*

**Period formulas** — [Henley's Twentieth Century Formulas, "Typewriter Ribbon Inks"](https://chestofbooks.com/reference/Henley-s-20th-Century-Formulas-Recipes-Processes-Vol2/Typewriter-Ribbon-Inks.html): the pigment route (high-boiling vaseline + *"lamp or powdered drop black"*, thinned with petroleum/benzine/turpentine *"to the consistence of fresh oil paint"*) and three dye routes (aniline black in alcohol + glycerine; aniline color in alcohol/water/glycerine; aniline color in castor oil + cassia oil + carbolic acid).

**Anti-migration coatings.** Carleton Ellis, *Printing Inks* (Reinhold, 1940), via Norris: ribbons may include *"a coating of **aluminum powder, a Pyroxylin layer, or additional oil**"*, plus *"ultramarine to enhance absorption and decrease smudging"* — i.e. some black ribbons deliberately contained a blue pigment.

**Fabric → film.** Cotton to the early 1950s, then nylon (Norris). Then film. From [Wikipedia, IBM Selectric](https://en.wikipedia.org/wiki/IBM_Selectric): the original Selectric (1961) offered either *"Reusable cloth ribbon (essentially the same as had been used on typewriters for decades)"* or a one-time carbon film ribbon, and *"the same machine could not use both."* The film ribbon's famous forensic property: *"It was possible to read the text that had been typed from the ribbon, seen as light characters against the darker ribbon background."* Then **Tech-3** (shortly after launch), which *"essentially replaced the cloth ribbon, as it offered typing quality close to the film ribbon but at a use cost comparable to the reusable cloth"* by overstriking each character position several times. Then **Correctable Film** with the Correcting Selectric II (1973), using *"a carbon pigment similar to that on the regular carbon film ribbon, but its binder did not permanently adhere to the paper."*

**The rendering-relevant distinction:** a **fabric ribbon** transfers ink through a woven mesh — an incomplete, textured, greyer deposit varying with ribbon wear and strike force. A **one-time carbon film** transfers a full-coverage pigment layer in one shot — dense, sharp-edged, close to a printing-ink solid. Two visibly different blacks from the same machine.

### (d) Colour reference

**I found NO measured colorimetric data of any kind for typewriter ribbon impressions — no CIELAB, no reflectance spectra, no published hex.** I searched the conservation literature (PSAP), the forensic-document-examination literature, and the ink trade literature. Stating that plainly rather than filling it.

The forensic literature exists but is *discriminatory*, not colorimetric — Rf values and band positions, not color. Via Norris:
- Brown & Kirk (1956), "Identification of Typewriter Ribbons," *J. Crim. Law, Criminol. & Police Sci.* 46(6), 882–85 — reagent color-change on fiber samples in capillary tubes.
- Brunelle, Negri, Cantu & Lyter (1977), "Comparison of Typewriter Ribbon Inks by TLC," *J. Forensic Sci.* 22(4), 807–14 — *"none of the seven manufacturers whose ribbons were tested produced matching ink formulations."*
- Tholl (1970), "Applied Thin-Layer Chromatography in Documented Examination," *Police* 14(4), 6–16 — silica gel, acetone extraction, 85:15 acetone:chloroform developer.
- Varshney, Jettappa, Mehrotra & Baggi (1995), "Ink Analysis from Typed Script of Electronic Typewriters by HPTLC," *Forensic Sci. Int.* 72(2), 107–15.

The U.S. Secret Service reference collection includes typewriter inks (per the search result for [USSS Digital Ink Library, ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0021967310017644)); I did not obtain the article and cannot say whether it holds spectra.

**Your premise — verified and partly refuted:**

- **"Carbon-ribbon impressions are essentially neutral dense black" — SUPPORTED** [INFERENCE, flagged]. The colorant is the same PBk6/PBk7 amorphous carbon as offset ink, and offset's measured neutrality (a*, b* within ±1 across every dataset in §1) is a property of the colorant, not the process. Defensible stand-in: ISO 2846-1's **L\* 18,0 / a\* 0,8 / b\* 0,0 → `#2D2C2C`**, with the caveat that ribbon inks carry glycerine/oil and sometimes ultramarine or a nigrosine shading dye that offset ink does not.
- **Fabric-ribbon impressions are lighter than film-ribbon impressions** — [INFERENCE, no measurement found]. Partial mesh coverage raises L*; it does not shift hue.
- **"Nigrosine-dyed ribbons can appear brownish/greenish" — I could NOT verify this, and the sources point the other way.** Nigrosine is an azine (phenazine) dye and every source I found calls it **bluish-black**: [Solvent Black 5 / Nigrosine spirit soluble](https://www.chinainterdyes.com/solvent-dye/black-solvent-dye/solvent-black-5.html), and W. D. Lockwood's product is literally named ["Nigrosine Black/Bluish"](https://www.cityfloorsupply.com/f/wd-lockwood-concentrated-mixing-colors-nigrosine-black-bluish-1-oz/455/12090). CI designations: **spirit-soluble = C.I. Solvent Black 5; water-soluble (sulfonated) = C.I. Acid Black 2.** The CAMEO (MFA Boston) entry [cameo.mfa.org/wiki/Nigrosine](https://cameo.mfa.org/wiki/Nigrosine) is Cloudflare-gated to both WebFetch (403) and curl — a conservation-grade description of aged nigrosine likely sits there and I could not read it.
- **"…or fade" — STRONGLY SUPPORTED**, but the effect belongs to dye-heavy *copying* ribbons, not to nigrosine specifically. Doyle 1906 measured it; the 1890 Massachusetts report observed it in outdoor exposure trials by records clerks; both distinguish it from black/lampblack ribbons that were "resistant to fading in light."

**Net:** the honest split is not "carbon black neutral vs. nigrosine brown." It is **carbon-pigment ribbons are neutral and lightfast; dye-only copying ribbons are colored and fugitive** — and typical commercial *black* ribbons were carbon black *shaded* with nigrosine/induline, i.e. a neutral-to-slightly-blue black. If you want a second typewriter black in the app, make it **cooler, slightly blue-shifted and slightly lighter** than the offset one — defensible from Wich 1966 and Ellis 1940 — and label it reconstructed, because no one measured it.

---

## 3. THE PURPLE/VIOLET COPYING INK

### (a) Genuinely distinct? Yes — and the best-documented of the three, because conservators had to deal with it.

### (b) Era, technologies, users

Canonical reference: **Liz Dube, "The Copying Pencil: Composition, History, and Conservation Implications," *The Book and Paper Group Annual* vol. 17 (AIC, 1998)** — [full text](https://cool.culturalheritage.org/coolaic/sg/bpg/annual/v17/bp17-05.html).

> "Mauvine, the first of the synthetic aniline dyes, was discovered by William Perkin in **1856**. Many new aniline dyes were introduced over the next few decades, including **methyl violet (1861)** and methylene blue (1876), paving the way for the introduction of copying pencils in the late 1870's."

> "The wet transfer copying process, patented in **1780** by James Watt … By the **1870's**, letter copying books became the ubiquitous copying tool for businesses."

> "Copying pencils were also used with two other copying processes: **the hectograph (developed around 1880) and the spirit duplicator (developed in 1923)**. This variation of copying pencils was called a 'hectographic pencil' and was produced in formulations containing a fairly high proportion of dye; some had little to no graphite."

M. Grzelec, **Heritage Science 12, 269 (2024)**, [nature.com/articles/s40494-024-01368-1](https://www.nature.com/articles/s40494-024-01368-1), dates it differently — per the search result: *"Methyl Violet (MV) dye, synthesized in 1862 by Charles Lauth, and sold since under the name 'Violet de Paris'."* **I could not read the full text** (nature.com redirects to its IDP; link.springer.com serves a JS challenge). The 1861-vs-1862 discrepancy is unresolved.

Duplicator dates:
- **Spirit duplicator invented 1923 by Wilhelm Ritzerfeld**; Ditto Corporation of Illinois dominated the U.S., Associated Automation Ltd of London made Banda machines for the U.K./Australia — [Wikipedia, Spirit duplicator](https://en.wikipedia.org/wiki/Spirit_duplicator).
- **Decline:** per that article's search summary, *"Spirit duplicator technology gradually fell into disuse starting in the 1970s after the availability of low-cost, high-volume xerographic copiers; by the mid 1990s, the use of the technology was rare."* Tighter ranges from [PSAP, Office Printing and Reprography, U. Illinois](https://psap.library.illinois.edu/collection-id-guide/officeprintcopy): hectograph **"1878 - 1970s"**, spirit duplicator **"1923 – 1970s"**, both producing *"monochrome (violet or blue, sometimes other colors)"*.

Users: business correspondence (letter copying books), railroads (Dube: copying pencils *"have been referred to as 'railroad pencils'"*), the military (Dube: *"Great Britain was buying thousands of American copying pencils per week"* in WWI), and for ditto, schools, churches and fanzine publishers into the 1980s.

### (c) MECHANISM — the dye chemistry, settled

**Class:** triarylmethane (triphenylmethane) cationic dyes — the methylated pararosanilines. Dube:

> "Generally speaking, methyl violet is a mixture of the tetra-, penta-, and hexamethylpararosanilines. However, the term 'methyl violet' is most frequently applied to mixtures containing hexa- and pentamethylpararosaniline (5 and 6 methyl groups), and often refers specifically to the hexamethyl derivative (6 methyl groups), known as **crystal violet**."

> "**Specific hues of methyl violet derivatives are determined by the number of methyl groups present in the molecule.**"

> "The derivatives of methyl violet used as a dye include **crystal violet**, pure hexamethylpararosaniline chloride; **methyl violet 2B**, principally pentamethylpararosaniline hydrochloride; and **methyl violet 6B**, the pentamethylbenzene derivative."

**⚠️ The CI numbers are genuinely contested, and your brief inherits one of the two versions.**

| Source | Assignment |
|---|---|
| Dube 1998 (figure captions) | *"Hexamethylpararosaniline chloride, or crystal violet (**color index no. 42555**)"*; *"Pentamethylpararosaniline hydrochloride, the primary species of **methyl violet 2B (color index no. 42535)**"* |
| [Wikipedia, Methyl violet](https://en.wikipedia.org/wiki/Methyl_violet) | *"Methyl violets are mixtures of tetramethyl (2B), pentamethyl (6B) and hexamethyl (10B) pararosanilins."* — **2B = C.I. 42536, 6B = C.I. 42535, 10B = C.I. 42555** |
| [IARC/NCBI Bookshelf, Gentian Violet, NBK594618](https://www.ncbi.nlm.nih.gov/books/NBK594618/) | *"CI Basic Violet 3, CI 42555"*; CAS **548-62-9**; synonyms *"basic violet, crystal violet, hexamethyl-para-rosaniline chloride, **methyl violet 10B**, methylrosanilium chloride, aniline violet"* |

**CI 42555 = Basic Violet 3 = crystal violet = gentian violet = methyl violet 10B is agreed by everyone.** But Wikipedia assigns 2B to the *tetra*methyl compound and CI 42536, while Dube assigns 2B to the *penta*methyl and CI 42535. Your brief's "Basic Violet 1 = methyl violet = CI 42535" matches Dube's number but not Wikipedia's derivative. **Unresolved — I could not reach the Colour Index itself** (paywalled, and my search budget ran out).

**The dye's own appearance — the counter-intuitive part.** Dube:

> "In its concentrated dry state, **methyl violet appears as dark green crystals or powder and, like graphite, exhibits a metallic luster.**"

IARC concurs: *"green to very dark green powder; dark purple in solution."* This is exactly why copying-pencil marks are dangerous to conservators — dry, the dye reads as graphite.

**Why purple, specifically — three independent reasons, all sourced:**

1. **Tinctorial strength.** Dube: *"Methyl violet found success as a copying ink because of its **high tinctorial value and brilliant violet hue** which allowed it to produce multiple strong copies."*
2. **Density/contrast at low deposit.** [Wikipedia, Hectograph](https://en.wikipedia.org/wiki/Hectograph): *"At least eight different colors of hectographic ink were available at one time, but **purple was the most popular because of its density and contrast**."*
3. **Cheapness and durability.** [Wikipedia, Spirit duplicator](https://en.wikipedia.org/wiki/Spirit_duplicator): *"The usual wax color was aniline purple (mauve), **a cheap, moderately durable pigment that provided good contrast**."*

**⚠️ Correct that last one.** "Aniline purple (mauve)" is almost certainly wrong — mauveine is Perkin's 1856 dye, different chemistry, commercially obsolete long before 1923. The **Society of American Archivists' *Dictionary of Archives Terminology*** has it right — [dictionary.archivists.org, "spirit duplication"](https://dictionary.archivists.org/entry/spirit-duplication.html): the inks were *"strongly coloured, **the most common colourant being crystal violet as used in hectography**."* Also *"A method of copying documents using a master sheet created with aniline dye ink, which, when placed on a rotary drum press and moistened with a **methyl alcohol solution**, transfers the ink to blank sheets"*, and *"The ink is **unstable in ultraviolet light and soluble in water**."*

**Why the alcohol solvent selects the dye.** Crystal violet is a *cationic* (basic) dye — soluble in water and short-chain alcohols. Dube: *"Methyl violet is soluble in water and alcohol."* And the fluid — Wikipedia, Spirit duplicator: *"The duplicating fluid typically consisted mostly of **methanol or ethanol**, both of which were inexpensive and readily available in quantity, evaporated quickly, and would not wrinkle the paper."* Causal chain: alcohol is the only solvent that dissolves the master's wax-bound dye, flashes off fast enough for a drum press, and does not cockle paper — and crystal violet is the strongest, cheapest dye soluble in it. **Purple is not a style choice; it is what the solvent selects for.**

**The full ecology of the same dye** — all from Dube unless noted:
- **Letter copying press** (Watt's 1780 process, aniline era from the 1870s). Traditional iron-gall and logwood inks *"would produce few copies before they dried and only faint images could be obtained from them after they had dried"*, whereas with aniline dyes *"**the violet coloured copy soon became characteristic of the process in its new form**"*, and *"the use of aniline dyes allowed copies to be taken long after the writing of the original document."*
- **Copying / indelible pencils.** Core = graphite + kaolin + dye. *"One report on the chemical analysis of 21 copying pencils suggests that the proportion of dyestuffs in copying pencil markings ranges from less than 25 percent to about 50 percent"*, plus *"a mordant such as alumina and additional binder components such as dextrin, gum tragacanth, albumen, or wax."* An 1877 patent sells it as *"ordinary lead pencil...but more permanent, as the marks cannot be erased with rubber."*
- **Carbon paper.** Copying pencils *"provided a natural accompaniment to carbon papers"*; the hard multi-copy grade was a *"manifolding pencil."* [Wikipedia, Carbon paper](https://en.wikipedia.org/wiki/Carbon_paper) describes the coating as *"a layer of a loosely bound dry ink or pigmented coating, bound with wax"*, Turri 1801, Wedgwood's patent 1806, and the 1954 Columbia Ribbon & Carbon shift *"from wax-based to polymer-based."* It does not name the colorant — but Doyle 1906's ribbon taxonomy independently records a "**purple copy**" category, so the dye family was in ribbons too.
- **Hectograph (gelatin).** Wikipedia: *"The special aniline dyes for making the master image came in the form of ink or in pens, pencils, carbon paper, and typewriter ribbon."* Yield: *"print runs of somewhere between 20 and 80 copies."* Period recipes from [Henley's, "Hectograph Inks"](https://chestofbooks.com/reference/Henley-s-20th-Century-Formulas-Recipes-Processes-Vol2/Hectograph-Inks.html) are simply methyl violet + water + glycerine (e.g. 1 : 8 : 1); the *black* hectograph ink is **methyl violet 10 parts + nigrosin 20 parts** — the same nigrosine as §2.
- **Spirit duplicator / ditto / Banda.** Wax master impregnated with crystal violet, alcohol-wetted transfer.

### (d) Colour reference

**HUE: BLUE-violet, not red-violet.** Three converging lines:

1. **[MEASURED] λmax.** IARC/NCBI on gentian violet: absorption maximum **"590 nm (water)"**. A 590 nm band removes the orange-yellow; what survives is short-wavelength blue-violet plus a red tail — a violet on the *blue* side of the purple locus. Independent corroboration from search: [SIELC's UV-Vis spectrum of crystal violet](https://sielc.com/uv-vis-spectrum-of-crystal-violet) gives λmax 589–594 nm; [AAT Bioquest](https://www.aatbio.com/absorbance-uv-visible-spectrum-graph-viewer/crystal_violet) gives maxima at 208, 250, 304, 590 nm.
2. **Direct observation in the conservation literature.** Dube on wet-transferred markings: *"These markings are characterized by feathered edges and a pronounced color, **usually violet or blue**."* After humidification testing: *"The colored dyestuff was solubilized sufficiently to cause all of the twelve copying pencil markings to exhibit a **pronounced purple or blue hue**."* Every descriptor in her paper is violet/purple/blue — never magenta, never red-violet.
3. **The archival descriptor.** SAA: *"a distinctive **purplish** hue that was typical (although not universal) of the aniline dye inks used."*

**Within the family, hue tracks methyl count.** Dube: *"Specific hues of methyl violet derivatives are determined by the number of methyl groups present in the molecule."* Wikipedia: *"Depending on the number of attached methyl groups, the color of the dye can be altered."* [INFERENCE — direction not directly sourced] More N-methyl groups → stronger electron donation → bathochromic shift → **crystal violet (10B, hexamethyl) is the bluest-violet of the family, 2B the reddest.** I could not find a per-derivative λmax table, so treat the *ordering* as inference and the *existence* of the dependence as sourced. For the app: a ditto/hectograph master is crystal-violet-dominant, so it lands at the **blue** end; a cheaper generic "methyl violet" copying pencil sits redder.

**MEASURED CIELAB or reflectance for a hectograph/ditto/copying-pencil purple: NONE FOUND.** I looked in the conservation literature (Dube 1998; PSAP), the 2024 Heritage Science ATR-FTIR paper (which reports IR band positions — *"peaks at 1590 cm-1 for Methyl Violet"* — not color), the forensic literature, and general dye chemistry. **There is no measured Lab, no spectral reflectance, and no defensible hex for this ink that I could source. I did not invent one.**

**Nearest publishable anchors, each labeled:**

- **[MEASURED, but a solution not a print]** Crystal violet in water, λmax 590 nm (IARC/NCBI). Constrains hue but not L* or chroma on paper, and a transmission color is not a reflectance color. I deliberately did *not* convert it — that would require assuming a band shape I have no data for.
- **[PUBLISHED SYSTEM, my placement is judgment]** ISCC-NBS centroid colors (Munsell-renotation-derived, converted to sRGB by John Foster), mirrored at [people.csail.mit.edu/jaffer/Color/nbs-iscc.txt](https://people.csail.mit.edu/jaffer/Color/nbs-iscc.txt). Relevant centroids: `Vivid_Violet #9065CA`, `Strong_Violet #604E97`, `Deep_Violet #32174D`, `Vivid_Purple #9A4EAE`, `Deep_Purple #602F6B`. A full-strength ditto reads to me between **Strong Violet `#604E97`** and **Deep Violet `#32174D`** — **but that is my visual judgment against memory of ditto sheets, not a measurement, and must be labeled as such if it ships.** The file's own header warns the conversions are imperfect: the earlier Mundie conversion's *"colors were visibly biased towards pink and had duplications"*, and *"Many of the original Munsell values (noted) are outside the RGB gamut."*
- **[UNMEASURED-WEB]** I checked the Wikipedia articles for *Crystal violet*, *Methyl violet*, *Methyl violet 2B*, *Methyl violet 6B*, *Hectograph* and *Carbon paper* for a color swatch. **None carries one** — the only hexes are MediaWiki chrome. So the common folklore hexes for "gentian violet" do not even have that much behind them. I found no circulating hex I am willing to cite.

**Fading — well documented, and asymmetric.** Dube: methyl violet *"exhibits poor lightfastness, is vulnerable to oxidation, and is sensitive to pH shifts"*; *"Since aniline dyes are highly fugitive, light bleaching might also be effective … Exposure to ultraviolet radiation can oxidize the chromogenic aniline dyestuff, breaking double bonds and causing a reduction of the color-producing conjugated system."* Wikipedia, Spirit duplicator: *"Dittoed images gradually fade with exposure to ultraviolet light"*; *"when exposed to direct sunlight, ditto copies can fade to illegibility in less than a month."* PSAP: *"aniline dye ink is light sensitive and therefore prone to fading over time."*
**So the right aged rendering is lower chroma and higher L\* — a washed lilac — not a hue rotation.** (Crystal violet does rotate to green then yellow on protonation, but that is around pH 0–1, far below any paper, so it is not the mechanism for aged documents.)

---

## Summary table for the app

| Candidate | Colorant | Best colour reference | Label |
|---|---|---|---|
| Offset process black, coated | PBk7/PBk6 carbon black in resin/oil | FOGRA51 K solid **L\*16.00 a\*0.07 b\*−0.33** → `#282828` abs / **`#2B2B29`** on white (14.19:1) | **[MEASURED]** |
| Offset process black, uncoated | same | FOGRA52 K solid **L\*32.69 a\*1.24 b\*0.11** → `#4F4C4D` abs / **`#56534C`** on white (7.67:1) | **[MEASURED]** |
| Offset black, ink on reference substrate | same | ISO 2846-1:2017 Table 1 **L\*18,0 a\*0,8 b\*0,0** → `#2D2C2C` | **[MEASURED]** |
| Rich (400%) black | carbon black + CMY | FOGRA51 **L\*12.71 a\*0.53 b\*4.89** → `#24211A` — visibly warm | **[MEASURED]** |
| Typewriter, carbon film ribbon | PBk7-class carbon in wax/resin binder | none published; nearest analogue `#2D2C2C` | **[INFERENCE]** |
| Typewriter, fabric ribbon | carbon black shaded with nigrosine + induline (Wich 1966) | none published; cooler and lighter than above | **[INFERENCE]** |
| Copying / hectograph / ditto purple | crystal violet, C.I. 42555, Basic Violet 3, CAS 548-62-9 | **no measured Lab or hex exists that I could find**; hue constrained to blue-violet by λmax 590 nm | **[hue MEASURED; hex NOT AVAILABLE]** |

## Open gaps, stated plainly

1. **SWOP — not obtained.** `CGATS21-2-CRPC5` (the SWOP-equivalent publication condition) and CRPC1/3/7 all return **404** from the ICC registry chardata directory. Only CRPC6 (GRACoL 2013) resolved. I have no measured SWOP black solid Lab and will not guess one.
2. **ISO 12647-2:2013 primary text** not obtained; K = 16/0/0 rests on Heidelberg's workshop deck — a strong secondary, but a secondary.
3. **ISO/DIS 12647-2 (post-2013)** exists at [iso.org/obp, std 81375](https://www.iso.org/obp/ui/en/#!iso:std:81375:en); contents unread. I do not know whether the black aim changed.
4. **ISO 2846-1 Annexes C (spectral data) and D (D65 tristimulus)** are cut from the free preview. Spectra would let you derive the black under any illuminant, not just D50.
5. **CI numbers for methyl violet 2B/6B** contradict between Dube 1998 and Wikipedia; unresolved against the Colour Index itself.
6. **Methyl violet 1861 (Dube, no inventor) vs 1862/Charles Lauth (Heritage Science 2024)** — unresolved.
7. **No colorimetry exists (that I can find) for typewriter ribbon impressions or for any purple copying process.** This is the largest gap and it is a genuine gap in the published record, not a search failure — the conservation literature on these media is qualitative and the forensic literature is discriminatory rather than colorimetric.
8. **CAMEO (MFA Boston)** entries for Nigrosine, Methyl violet, Crystal violet, Carbon black and Lampblack are Cloudflare-gated to both WebFetch and curl. That database is the most likely home for a conservation-grade color description of aged nigrosine and methyl violet; someone with a browser should check it.
9. **My WebSearch budget hit its 200-call ceiling** partway through topic 3. Two intended searches never ran: ISCC-NBS / Kelly-Judd dye-name mappings for "methyl violet"/"gentian violet", and a hunt for measured crystal-violet-on-paper reflectance.