# Historical ink research: sumi, India ink, iron gall, ballpoint, and the duplicators

Research pass 2026-08-22 for the light-mode ink table, with a provenance key on
every claim (FETCHED / SNIPPET / MEASURED / UNMEASURED-WEB / DERIVED). Preserved
here because the sub-agent that produced it could not reach its parent, and
because the NEGATIVE results are the half that stops these searches being
repeated: there is no published CIELAB for sumi, none for any blue-black
fountain pen ink, none for ballpoint blue, and ISO 2846-2's newsprint numbers
were not obtainable.

Two rules of thumb this pass established, both load-bearing for the renderer:

1. Every colour claim here is a **b\* shift at near-neutral a\***, never an RGB
   hue rotation.
2. **The regime flips the sign of the particle-size effect.** Fine carbon reads
   BLUE in masstone and BROWN in dilute tint; coarse carbon does the opposite.
   So a single hardcoded warm/cool constant per ink is wrong half the time --
   tie it to the rendered ink density.

# Historical ink research — findings

**Provenance key.** `[FETCHED]` = I retrieved and read the page/PDF. `[SNIPPET]` = real URL and title from search results, body not retrieved. `[MEASURED]` = colorimetry, standard, or instrumental analysis. `[UNMEASURED-WEB]` = a hex circulating without measurement behind it. `[DERIVED]` = my inference, flagged as such.

## Three corrections to the brief, up front

**(a) The particle-size mechanism in the brief is INVERTED.** The brief proposes "smaller particles scatter blue, which would be the actual mechanism." For the *absorbing* (carbon) particle in a scattering ground, published industry colorimetry says the opposite — and the opposite is what agrees with the calligraphy tradition. Orion Engineered Carbons, *Technical Information 1464, "Coloristic properties of specialty carbon blacks in full tone and tinting applications for coatings"* (2023), §4.2 `[FETCHED]` `[MEASURED]`:

> "Hue dG is fundamentally influenced by the scatter and absorption behaviour of small particles. **Coarse specialty carbon black particles in the white mixture create a blue undertone, while fine particles produce a red or brown hue.** In fact, the opposite effect is demonstrated between full shade application and white reduction."

§4.5: "In tinting applications, **bigger sized particles give a bluish undertone due to the anisotropic scattering of light.**"

The "small particles scatter blue" rule does hold — but for the **white** pigment (TiO₂; paper filler and fiber play that role), not the black: "smaller particles scatter blue light more efficiently than the red light. This means a shorter path and less absorption for the blue light… As a consequence, the reflected hue appears bluer" (§4.5).

**The regime dependency is the crux**, and almost every popular account garbles it. PCI Magazine, "Black — The Fine Details" `[FETCHED]`:

> "Finer particles usually result in a higher black value with a blue undertone in covering coats. Coarser particles result in a lower blackness value and a brownish undertone." … "the effect on the undertones is precisely the opposite with transparent colorings and grey blends. Carbon blacks with finer particles result in brown undertones, and carbon blacks with coarser particles in blue undertones."

So: **masstone → fine = blue; dilute/tint → fine = brown.** Sumi's hue distinction is asserted in *dilute* ink (淡墨), i.e. the tint regime. Everything is consistent once the regime is kept straight. **Any single hardcoded "warm/cool" constant will be wrong half the time.**

**(b) DIN 51452 has nothing to do with ink.** Verified: *"Testing of lubricants; determination of the soot content in used Diesel engine oils; infrared spectrometry"*, 1994-01 `[SNIPPET]` (sis.se, dinmedia.de, ANSI webstore). Delete it from the brief.

**(c) BS 3484 is real and the number in the brief is correct.** See §4.

---

## 1. Japanese sumi — pine soot vs oil soot

### (a) Distinct? YES. And the warm/cool claim is REAL, with the brief's direction CORRECT

**松煙墨 shōen/matsuen-boku (pine soot) = COOL, blue-black = 青墨 seiboku/aoboku.**
**油煙墨 yuen-boku (oil soot) = WARM, brown/red-black = 茶墨 chaboku.**

Musashino Art University, *MAU Art & Design Glossary*, "Inksticks (Sumi)" `[FETCHED]`:
> Pine soot ink "displays a bluish tinge" and has "coarse" particles "that vary in size." It "does not have a glossy character, and its color changes to a blue-black as time progresses."
> Oil soot ink "is made from the soot of vegetable oils such as canola oil, tung oil, or sesame oil," "takes on a brownish hue when diluted," and has carbon particles "particularly small," giving "gloss and purity."

PIGMENT TOKYO, "Exploring Sumi Ink and Their Unique Features" `[FETCHED]`:
> "Sumi ink that has reddish color is called *Chaboku*, and the one that has bluish color is called *Seiboku*."
> "soot of burnt lamp oil is formed by a smaller partical, and soot of burnt pinewood is formed by a larger particle."

Japanese Wikipedia 墨 `[FETCHED]` — **numbers**:
> 「煤の一次粒子径の大きさは油煙では30nm前後だが」…「松煙では50nm以上と大きい」 (~30 nm oil soot; ≥50 nm pine soot)
> 「松煙を用いて作られる墨は墨色が薄いとわずかに薄青を呈する」 (pine-soot ink shows faint pale blue **when the tone is thin**)

書遊Online, 「墨の原料と種類」 `[FETCHED]` — the sentence that settles the regime question:
> 油煙墨:「濃墨では黒色ですが、淡墨では赤味を帯びた茶系」 (black in *dark* ink, reddish-brown cast in *dilute* ink)
> 松煙墨:「古くなるほど黒系から青系に変化」 (the older it gets, the more it shifts from black toward blue)

**⚠ Folklore inversion in the wild.** urchinshome.com, "Sumi Ink: The Living Pigment of Brush Arts" `[FETCHED]` states the exact opposite — pine-soot "black runs warm with brown or reddish undertones," oil-soot "tips… toward blue." Wrong against every Japanese-language and museum source. It ranks well in English search.

**⚠ Commercial caveat — shop "seiboku" is often not pine soot.** Kobaien (古梅園, Nara, founded 1577), 青墨 page `[FETCHED]`: 「本藍を使用し、鮮やかな青みを出す青墨もあります」 ("there are also *seiboku* that use genuine indigo to produce a vivid blueness"), with the soot named as 「菜種油から採煙した油煙」 — **oil** soot from rapeseed. Japan's most famous ink house sells its flagship blue as *oil soot + indigo*, a dyed ink and a different mechanism. Decide which you're emulating.

### (b) Era and users

JAANUS (Columbia University) `[FETCHED]`:
> "true ink, made from pine soot mixed with glue and formed into sticks, was produced in China during the **1st–2nd century BCE**"
> Japan: "earliest manufacture of ink is recorded in the **7th-century *Nihon shoki***"
> Plant-oil soot in Japan: "**early 15th century** by a monk at Kōfukuji"
> Centers: Nara, Kyoto, Tanba, later Kii and Awaji, by the 12th–14th c.

MAU `[FETCHED]`: inksticks "brought to Japan via the Goguryeo kingdom in Korea during the reign of the Empress Suiko." Users: calligraphy, ink painting, and the manuscript/woodblock book tradition.

### (c) Mechanism

- **Colorant:** elemental carbon soot. Pine = incomplete combustion of resinous red pine wood/resin; oil = vegetable-oil lamp soot (rapeseed 菜種, sesame, tung).
- **Binder:** 膠 *nikawa*, collagen. 書遊Online `[FETCHED]`: 「牛皮・馬皮・鹿皮のニベ…や骨などを煮詰めてコラーゲンなどのタンパク質を抽出」.
- **Hue:** a particle-size effect in the tint regime, not a colorant difference — exactly what Orion §4.2/§4.5 measures for coarse lamp black vs fine gas black.
- `[DERIVED]` gloss: fine carbon well below the Rayleigh limit acts as a near-isotropic absorber whose cross-section rises toward short wavelengths, eating blue and leaving a warm residue; ~100 nm particles enter the Mie regime, scatter anisotropically and remit some blue. The industry text asserts "anisotropic scattering" but does not spell this out.
- **Waboku vs tōboku:** MAU `[FETCHED]`: Japanese ink "contains substantial glue, reducing page absorption," Chinese ink has less and "spread[s] more smoothly."

### (d) Aging — REAL, and it moves TOWARD BLUE

Mechanistically consistent: aging grows the particles, and growing particles go blue. Japanese term **青墨化** *seiboku-ka*.

PIGMENT TOKYO, "Vintage Sumi Ink: Kogaboku" `[FETCHED]`:
> "The aging process of the animal glue and the natural agglomeration of the carbon powder (pine and oil soot) give the ink a deeper and richer color."
> "during 3 to 5 years since it is made, its viscosity changes drastically"

PIGMENT TOKYO, sumi-ink-basic `[FETCHED]`:
> "as the fixing power of animal glue weakens, the particle tries to return to the shape of a bunch. It creates a change in the particle size and the color changes accordingly."

ja.wikipedia 墨 `[FETCHED]`: 「墨は成長する」, sticks of 20–50 years prized.

**⚠ The two aging directions in this set are opposite.** Sumi *stick* → cooler/bluer. Iron-gall *writing* → warmer/browner (§4). Do not merge them.

### Color reference

**No spectrophotometric study of sumi exists that I could find** — I searched for one specifically. Saying so rather than inventing.

Best available is a **measured proxy with the right physics** — Orion TI-1464 Table 7 `[FETCHED]` `[MEASURED]`: coarse LAMP BLACK 101 (95 nm, made by the **lamp black process** = burning oil in open pans, the closest industrial analog to a soot lamp) vs fine COLOUR BLACK FW 2 (13 nm gas black), same white, **matched lightness**:

| Sample | L\* | a\* | b\* | sRGB (my D65 Lab→sRGB) |
|---|---|---|---|---|
| **LB 101 (coarse) + TiO₂ 174 nm, PVC 20 %** | 41.49 | −1.79 | **−10.91** | `#546474` |
| LB 101 + TiO₂ 276 nm, PVC 20 % | 40.54 | −1.78 | −6.83 | `#56616B` |
| **FW 2 (fine) + TiO₂ 174 nm, PVC 20 %** | 41.22 | −1.07 | **−4.45** | `#5C6268` |
| LB 101 + TiO₂ 276 nm, PVC 5 % | 40.69 | −1.36 | −3.81 | `#5A6166` |
| FW 2 + TiO₂ 174 nm, PVC 5 % | 45.52 | −0.85 | −1.90 | `#696C6F` |
| **FW 2 (fine) + TiO₂ 276 nm, PVC 5 %** | 44.67 | −0.30 | **+1.64** | `#6A6A67` |

Rows 1 and 3 are the money pair: same white, **ΔL\* = 0.27, Δb\* = 6.46** — coarse soot measurably bluer at equal lightness.

**`[DERIVED]` emulation rule:** apply **Δb\* ≈ −6 for pine/aoboku, +1 to +3 for oil/chaboku, a\* essentially neutral (|a\*| < 2)**, magnitude scaling with how light the wash is; the effect vanishes at full masstone. **It is a b\*-axis shift at near-constant a\*, not an RGB hue rotation.**

The circulating hex for 墨色 is `#000A02` (irocore.com) `[FETCHED]` `[UNMEASURED-WEB]` — no Munsell, no JIS, near-black to the point of uselessness. Ignore it.

---

## 2. Chinese ink stick (墨) and the Hui (徽墨) tradition

**Distinct?** Same soot + collagen technology; sumi is its Japanese branch. Actionable differences: **less glue** (tōboku "spread more smoothly," MAU `[FETCHED]`) and additives — Li Tinggui's ink used "light pine soot and high-quality glue, with added ingredients such as jade dust and borneol" `[SNIPPET]` (chiculture.org.hk).

**Era** `[SNIPPET]`: earliest ink material, late Warring States (306–221 BCE); a cylindrical inkstick 1.2 × 2.1 cm from a Hubei tomb, Qin (221–206 BCE); **pine soot ink appears in the Han (206 BCE–220 CE)**; **oil soot ink appears in the Song (960–1279)** — note the ~400-year lag before it reaches Japan. **Hui ink:** Xi Chao, late Tang; **Li Tinggui** (d. 967) moved to Shezhou and used Huangshan pine soot; the Southern Tang ruler granted him the imperial surname and made him ink official; the Song court used his ink for edicts with 1,000 *jin* annual tribute; Huizong (r. 1100–1125) renamed the prefecture **Huizhou**; peak under the Ming Huizhou merchant houses.

**Color reference:** none found. Use the same Δb\* rule. If one emulated stick must differ from the Japanese one, the defensible lever is *lower glue → more spread, less gloss*, not hue.

**Analytical literature that exists but I could not open:** Giaccai et al., "Differentiation of pine and oil-based soots in East Asian inks using Raman spectroscopy," *J. Raman Spectrosc.* **55**(9):939 (2024), DOI 10.1002/jrs.6682 — Wiley **403**. This is the direct instrumental confirmation; worth institutional access. Also "Characterization of the materials used in Chinese ink sticks by pyrolysis-GC–MS" (ScienceDirect) and Qi/Sun/Chen 2025 on the Fan Xiaochong Northern Song inkstick (Research Square DOI 10.21203/rs.3.rs-6364938/v1, confirmed to exist via Europe PMC `[FETCHED]`; no open PDF).

---

## 3. India ink

**Distinct by BINDER, not colorant.** Fine carbon in **shellac** + **borax emulsifier**, alcohol-soluble `[SNIPPET]` (MFA CAMEO — I attempted the fetch and got 403, so this is snippet-level). The borax saponifies shellac into a water-dispersible soap; once the water leaves, the film is water-insoluble. That is the entire waterproofing trick.

**Name:** a European misattribution — a Chinese product that reached Europe via Indian Ocean trade routes by the mid-17th century `[SNIPPET]`.

**Modern anchor** `[SNIPPET]` (en.wikipedia Charles M. Higgins; higginsinks.com/about-us): Charles Michael Higgins (1854–1929), born Co. Leitrim, raised in Brooklyn; experimented in his sister-in-law's Brooklyn Heights kitchen; **1880** selling agreement, **1885** partnership as Charles M. Higgins & Co.; made in Brooklyn early 1880s–late 1960s, now Chartpak, Leeds MA. "Micro-pulverized black carbon is suspended in a shellac solution."

**Users:** drafting, engineering drawing, comics inking, technical pens, map-making, and the steel-nib line-plus-wash tradition.

**Standard / color:** **none exists.** It is a trade description, not a specification. `[DERIVED]`: its distinguishing optic is **jetness and gloss, not hue** — this is the *full-tone* regime, where fine carbon reads blue-ish, not brown (Orion §3.1 `[FETCHED]`: "Finer pigments give a blue undertone and coarser ones appear brown in mass tone applications"; finest grade FW 255 at 11 nm reaches jetness MY = 300), and the shellac film is glossy, which lowers measured jetness under a closed gloss trap (§3.2). **India ink = the coldest, densest, glossiest black in the set**, and that is exactly the right contrast against sumi (matte, glue-bound, mid-loading).

---

## 4. Blue-black iron gall fountain pen ink

**The one ink here that changes color after you write it.**

**Era:** dominant in Europe from the Middle Ages to the 20th century; German Wikipedia `[FETCHED]` notes official documents used it **until the 1960s**. Users: registrars, notaries, banks, ministries, parish and court record-keepers.

**Mechanism** — en.wikipedia *Iron gall ink* `[FETCHED]`:
> Iron(II) sulfate + tannic acid gives "a water-soluble ferrous tannate complex," pale-grey and nearly colorless because "the ferro-gallic compound hasn't undergone oxidation yet." "When exposed to air, it converts to a ferric tannate, which is a darker pigment" (Fe²⁺ → Fe³⁺ by atmospheric oxygen).
> The added dye "functions as a temporary colourant to make these inks clearly visible whilst writing." The ferro-gallic compounds then "cause an observable gradual colour change to grey/black whilst these inks completely dry."

The brief's account is exactly right: **the blue is a sighting dye, the black arrives later.**

### Which blue dye — three eras

| Era | Colorant | Source |
|---|---|---|
| pre-19th c. | **indigo, logwood, brazilwood** as "provisional colorants… to obtain a dark color as soon as it flowed from the pen"; indigo also "imparting a preservative effect" | irongallink.org `[SNIPPET]` (page 404'd on fetch) |
| mid-19th c. on | **aniline dyes** | ibid. `[SNIPPET]` |
| 1930s US | **"Soluble blue (C.I. 707)", 3.0 g/L** | **`[FETCHED]` `[MEASURED]`** |
| BS 3484 (1962, as circulated) | "blue dye, aniline blue, water soluble", 0.3 g/100 ml | FPN `[FETCHED]`, secondhand |
| modern German | **Methylblau** — methyl blue, a triarylmethane | de.wikipedia `[FETCHED]` |

**Strongest primary source: Elmer W. Zimmerman, "Iron Gallate Inks — Liquid and Powder," *Journal of Research of the National Bureau of Standards*, Research Paper RP807, Vol. 15, July 1935** `[FETCHED, full text]`:

- **Federal Specification TT-I-563, Ink; Writing** — Table 1 footnote: "Standard ink is similar to this formula, excepting that 12.5 g of dilute U.S.P. hydrochloric acid is substituted for tartaric acid, and **3.0 g of dye and 1 g of phenol are added**," over 11.7 g tannic acid + 3.8 g gallic acid + 15 g FeSO₄·7H₂O per liter.
- Table 3 names the dye: **"Soluble blue (C. I. 707) — 3.5 g"** per liter.
- "The standard writing ink contains **3 g of iron per liter**."
- Lineage: "The formula for standard record ink is almost identical with the one recommended by **O. Schluttig and G. S. Neumann**" — *Die Eisengallustinten*, Dresden (1890) — whose final ink was **23.4 g tannic + 7.7 g gallic + 30 g ferrous sulphate/L**.
- Aging: **"In the standard ink, the color is likely to fade toward a greenish shade."**

C.I. 707 is the old (pre-1924) Colour Index number for **Soluble Blue / Water Blue**, a sulfonated triphenylmethane in the aniline-blue family. **I could not confirm its modern CI equivalent** — do not let anyone assert a modern CI 42xxx for it.

⚠ German Wikipedia `[FETCHED]`: *"Damit die Tinte beim Schreiben besser sichtbar ist, wird noch ein Farbstoff wie **Methylblau** hinzugegeben, der später verblasst."* — **methyl blue (CI 42780, a triarylmethane), NOT methylene blue.** The machine translation I received said methylene; flagging because that error propagates.

### The standards, verified one at a time

**✅ BS 3484 — REAL, number confirmed, two parts.**
- **BS 3484-1:1991, "Record inks — Specification for blue-black inks."** Published **31 January 1992**, **WITHDRAWN 18 January 2019**. Abstract: *"Performance and certain features of the composition of inks used for archival purposes."* Contents: Scope; Definitions; Ink description; Ink requirements; Packaging; **Appendices A–E — A: Standard reference ink; B: iron content; C: sediment; D: stability; E: ink performance**; one table, one figure. Descriptors: paper chromatography, atomic absorption spectrophotometry, volumetric analysis, iron content. Sources: knowledge.bsigroup.com `[FETCHED]`, intertekinform.com `[FETCHED]`.
- **BS 3484-2:1994, "Record inks — Specification for permanent inks"** — inks "intended for documents with a very long working and storage life," also withdrawn `[SNIPPET]`.
- **Does it specify a color?** **Unknown.** Appendix A defines a "Standard reference ink," which is how such standards normally pin color — by comparison, not a Lab coordinate. The descriptor list is entirely chemical/chromatographic. `[DERIVED]` read: composition + permanence spec, color by reference ink. **Do not assume numeric colorimetry.**

**✅ ISO 11798 — REAL, specifies NO color.** *"Information and documentation — Permanence and durability of writing, printing and copying on paper — Requirements and test methods."* 1999 ed. (iso.org/standard/20031.html), revised by **ISO 11798:2023** (iso.org/standard/83118.html), DIS in progress `[SNIPPET]`. Accelerated ageing, lightfastness, waterfastness. A permanence standard.

**✅ German "dokumentenecht" — and the fountain-pen gap.** de.wikipedia *Dokumentenechtheit* `[FETCHED]`: **ISO 12757-2** (ballpoint refills), **ISO 14145-2** (rollerball), **ISO 27668-2** (gel). Title verified as **ISO 12757-2:1998, "Ball point pens and refills — Part 2: Documentary use (DOC)"** (en.wikipedia ISO list `[FETCHED]`). And the killer sentence: *"Für Füllhaltertinten gibt es keine entsprechende Norm"* — **there is no corresponding standard for fountain pen inks.** Any product marketing DIN-certified *dokumentenecht* fountain pen ink is trading on the ballpoint standards.

**✅ "Urkundentinte" is an imperial decree, not a DIN.** de.wikipedia / dewiki `[FETCHED]`: Reichskanzleramt *Grundsätze für die amtliche Prüfung von Tinten*, **1888**, supplemented **1912**; Klasse I (Urkundentinten) vs Klasse II. Klasse I requires *"mindestens 27 g Gerbsäure und Gallussäure sowie mindestens 4 g metallisches Eisen"* per liter, iron **not above 6 g/l**. Performance clauses `[SNIPPET]`: no layering, wall-coating or sediment after 14 days in glass; eight-day-old writing must stay deep dark after washing with water and alcohol; must flow easily and not go sticky.

**Circulating BS 3484 (1962) recipe** — FPN `[FETCHED]`, **secondhand: a forum poster's summary, the thread does NOT reproduce standard text**: per 100 ml — gallic acid 0.64 g, tannic acid 1.95 g, H₂SO₄ (s.g. 1.84) 0.3 g, FeSO₄·7H₂O 2.5 g, phenol 0.1 g, "blue dye, aniline blue, water soluble" 0.3 g, water to 100 ml; "not less than 5 g and no more than 6 g of iron per litre"; "The colour change is a very dark blue black."

### Real examples

Pelikan 4001 Blue-Black, Montblanc, Waterman, Diamine Registrar's, Rohrer & Klingner Salix/Scabiosa, KWZ. **I could not fetch a single product page** — diamineinks.co.uk 404, cultpens 404, jetpens 403, thepelikansperch 403, rohrer-klingner 404, pelikan.com returned no document-ink content, archive.pelikan.com had an expired certificate. **Zero verified primary text on any modern formulation.**

### Color reference

**No measured Lab for any blue-black ink was findable.** What you can defensibly emulate is the **trajectory**:
1. **Wet/fresh** — the sighting dye alone: a saturated triarylmethane blue, slightly violet (Soluble Blue / aniline blue / methyl blue are all violet-shaded), over a near-colorless ferrous-tannate ground.
2. **Hours to days** — ferric tannate develops: "gradual colour change to grey/black whilst these inks completely dry" `[FETCHED]`. The dye is still present, so this is *blue over black* — the classic dark navy-black.
3. **Years to decades** — the fugitive dye fades (*"der später verblasst"* `[FETCHED]`), leaving ferric tannate alone, which degrades toward **brown**; Zimmerman 1935 `[FETCHED]` notes the chloride-containing standard ink fades "toward a greenish shade."

That violet-blue → navy-black → brown/green arc is unique in this set and is the strongest argument for including the ink.

---

## 5. Modern standard ballpoint blue

**Era** — en.wikipedia *Ballpoint pen* `[FETCHED]`: "Bíró filed for a British patent on **15 June 1938**"; 1941 to Argentina, "filed a new patent in **1943**"; Reynolds Rocket "Debuting at Gimbels department store in New York City on **29 October 1945**, for US$12.50 each… the first commercially successful ballpoint pen." *Bic Cristal* `[FETCHED]`: "launched in **December 1950**," designed by "the Décolletage Plastique design team at Société PPA," "the **100 billionth sold in September 2006**," "roughly 57 are sold per second." The brief's "most-seen ink color of the 20th century" claim is defensible on those numbers.

**Mechanism** — *Ballpoint pen* `[FETCHED]`:
> "Ballpoint pen ink is normally a paste containing around **25 to 40 percent dye**. The dyes are suspended in a mixture of solvents and fatty acids."
> "The most common of the solvents are **benzyl alcohol or phenoxyethanol**."
> "Common dyes in blue (and black) ink are Prussian blue, Victoria blue, methyl violet, crystal violet, and phthalocyanine blue."

Díaz-Santana et al., *Molecules*, 2023, PMC10490468 `[FETCHED]`: "solvents (~50%), dyes (~25%), resins, and additives (~25%)" and **"CV is a widely used colorant that is used in 99.9% of ballpoint pen ink formulations for any color (black and blue)."**

### Why it is that particular violet-leaning blue — I found the answer

Kiran, "Analysis of Commonly Used Blue Ballpoint Pen Ink in India by Planar Chromatography," *International Journal of Advanced Research* **5**(7), 981–988 (July 2017), DOI 10.21474/IJAR01/4806 `[FETCHED, full text]` `[MEASURED]` — 10 samples, 5 brands, TLC in two solvent systems against reference dyes:

> "The colour of spots were found to be blue and purple, where **purple spot was due to presence of crystal violet dye and blue colour was due to presence of copper phthalocyanine blue dye**, after compared with the acquired reference sample."
> **"It was found that concentration of crystal violet dye was more in comparison of copper phthalocyanine blue dye in all the 10 (ten) Samples."**

**Blue ballpoint is a two-dye mixture in which the violet dye dominates.** Crystal violet = **C.I. 42555** (confirmed via the Denman et al. 1996 *Dyes and Pigments* citation in that paper's bibliography), plus copper phthalocyanine as the true-blue component. CV is violet, tinctorially very strong, cheap, and highly soluble in glycol/benzyl-alcohol vehicles — so the economical formulation lands at a blue pulled toward violet. Not an aesthetic choice; it is what you get when a violet dye carries most of the tinting load.

**Forensic field** is large: HPLC-DAD for dyes, GC-MS for solvents, ToF-SIMS with multivariate statistics, HPTLC, and CV-degradation dating (demethylation to penta/tetra/tri/di/mono-PRS and pararosaniline; breakdown to Michler's ketone and NNAPH), with dye evolution running "months to years (even decades)" `[FETCHED]`. Wilmer Souder, "Composition, Properties and Behavior of Ball Pens and Inks," *J. Crim. L. Criminology & Police Sci.* **45** — the foundational paper; **Northwestern returned 403.**

**Standard / color:** **no color standard.** ISO 12757-2 is permanence only. No public Lab for BIC Cristal blue exists — measuring one would be a genuine contribution. `[DERIVED]` rendering note: CV absorbs ~590 nm, CuPc ~670 nm, so a CV-dominant mix is **strongly negative b\* with moderately positive a\***. **Do not render ballpoint blue as a cyan-leaning blue.** And it is a *dye*, therefore transparent and low-density — thin strokes look weak, color saturates only where the ball deposits paste. That is the streaky, glossy-in-the-groove look.

---

## 6. Other inks with a reading-legibility case

**Mimeograph / stencil duplicator black** — strong candidate. en.wikipedia *Mimeograph* `[FETCHED]`: "a low-cost duplicating machine that works by forcing ink through a stencil onto paper"; invented **1885**, common through the **1980s**. The ink "originally had a **lanolin base** and later became an **oil in water emulsion**" using "**turkey-red oil (sulfated castor oil) which gives it a distinctive and heavy scent**." vs the spirit duplicator: mimeography "produced a darker, more legible image," "hundreds of copies," from "a replenishable supply of ink through the stencil master." Visual signature: ink pushed through a perforated stencil — slightly bled, uneven edges, occasional flooding, soft matte black.

**Spirit duplicator ("ditto") purple** — the brief is right that this is a *different machine*, and it earns its place as the contrast. en.wikipedia *Spirit duplicator* `[FETCHED]`: invented **1923**, used "for most of the 20th century." "The usual wax color was **aniline purple (mauve)**, a cheap, moderately durable pigment that provided good contrast." Copies "gradually became lighter over the course of some dozens of copies" and "**can fade to illegibility in less than a month**" in direct sun. Wikipedia does not name it as crystal violet — but note the coincidence with §5: the century's two most-seen colorants are both cheap triarylmethane violets. **Include ditto as the deliberately *bad* legibility case.**

**Xerographic / laser toner black** — the one that is not an ink. en.wikipedia *Toner (printing)* `[FETCHED]`: polymer "can be a styrene acrylate copolymer, a polyester resin, a styrene butadiene copolymer"; early formulations used "carbon powder and iron oxide"; modern adds "polypropylene, fumed silica, and various minerals for triboelectrification." Particles "averaged **14–16 μm** or greater" originally; "for the perfect reproduction of dots and print features at 600 dpi, a particle size of about **5 μm** is required and, at 1200 dpi, about **3 μm**." "Toner particles are melted by the heat of the fuser." Emulation-relevant: **fused plastic, glossier than paper, sitting on top of the sheet — no bleed, hard edges**; early coarse toner is visibly rough at glyph edges.

**Newspaper web offset news ink** — conceptually the strongest addition (genuinely the low-density, greyish, low-contrast case everyone has read), but **I have no numbers for it.** I established that **ISO 2846** exists, titled *"Graphic technology — Colour and transparency of printing ink sets…"* `[SNIPPET]`, and that **ISO 2846-1:2006** is real and referenced by SWOP (en.wikipedia SWOP `[FETCHED]`: "The specifications make reference to, but are not identical to, the ISO standard ISO 2846-1:2006"). **I could NOT retrieve ISO 2846-2's title, scope, or any CIELAB values**, nor ISO 12647-3's newsprint solid-ink targets — iso.org 403s to WebFetch, my search budget was exhausted, and DuckDuckGo/Bing/Mojeek/iTeh all failed. en.wikipedia *Newsprint* `[FETCHED]` has no colorimetry, only "it usually has an off-white cast and distinctive feel." **Do not let ISO 2846-2 Lab values into the codebase without opening the standard.** Honest options: buy ISO 12647-3, or measure a newspaper.

**Typewriter-ribbon black** — I found no source in this session. A suggestion, not a finding.

---

## Summary table

| # | Ink | Distinct? | Era | Colorant | Binder/vehicle | Color reference status |
|---|---|---|---|---|---|---|
| 1a | Shōen-boku (pine soot) | Yes | China 1st–2nd c. BCE; Japan 7th c. | Coarse carbon ≥50 nm | Nikawa (collagen) | No sumi CIELAB exists. **Proxy MEASURED:** Δb\* ≈ −6.5 vs fine soot at matched L\* |
| 1b | Yuen-boku (oil soot) | Yes | Song China; Japan early 15th c. | Fine carbon ~30 nm | Nikawa | Same, warm end, b\* → 0/+ |
| 2 | Chinese 墨 / Hui ink | Same family, less glue | Han (pine) → Song (oil); Huizhou peak Ming | Carbon + borneol/musk/mineral | Collagen glue | None found |
| 3 | India ink | Yes — binder | Chinese origin; European name mid-17th c.; Higgins 1880 | Fine lampblack, high loading | **Shellac + borax**, alcohol-soluble | No standard, no CIELAB. Jettest + glossiest |
| 4 | Blue-black iron gall | Yes — changes after writing | Medieval → 1960s official use | Ferrous→ferric tannate + fugitive blue (indigo/logwood → aniline → C.I. 707 → methyl blue) | Gum arabic / aqueous | **BS 3484-1:1991 REAL** (withdrawn 2019), App. A "Standard reference ink"; ISO 11798 = permanence only; **DIN 51452 is diesel soot**; no fountain-pen ISO exists; no measured Lab |
| 5 | Ballpoint blue | Yes — dye paste | Bíró 1938/1943, Reynolds 1945, BIC Cristal Dec 1950 | **Crystal violet CI 42555 (dominant) + Cu phthalocyanine** | Benzyl alcohol/phenoxyethanol + fatty acids + resin; 25–40 % dye | ISO 12757-2 = permanence only; **no color standard, no public Lab** |
| 6a | Mimeograph black | Yes | 1885–1980s | Carbon in emulsion | Lanolin → oil-in-water w/ turkey-red oil | None found |
| 6b | Ditto purple | Yes | 1923–late 20th c. | "Aniline purple (mauve)" wax | Wax + alcohol solvent | None found; fades in <1 month in sun |
| 6c | Toner black | Yes — not an ink | 14–16 μm early → 3–5 μm modern | Carbon + iron oxide in polymer | Styrene-acrylate/polyester, heat-fused | None found |
| 6d | News ink | Yes | 20th c. | CMYK/black news ink | Coldset offset | **ISO 2846-1:2006 confirmed; Part 2 and ALL CIELAB values NOT retrieved** |

---

## What I could not find — explicitly

1. **Any spectrophotometric study of sumi ink.** No CIELAB, no reflectance spectra for shōen vs yuen. Likely only in Japanese 製墨/conservation literature that is not web-indexed.
2. **The text of BS 3484-1:1991.** Metadata and contents list only. Cannot say whether it specifies numeric color.
3. **Any measured Lab for any named blue-black fountain pen ink.**
4. **Any modern iron-gall product page** — all 403/404. Zero verified primary text on modern formulations.
5. **ISO 2846-2's title, scope or CIELAB values**, and ISO 12647-3's newsprint solid-ink values.
6. **Giaccai et al. 2024** (Wiley 403) and the Fan Xiaochong ink-stick analysis (Nature IdP redirect; Research Square no PDF).
7. **Wilmer Souder's 1954 ballpoint paper** (Northwestern 403).
8. **Maerz & Paul, *A Dictionary of Color* (1930)** — never reached an indexed entry for any of these inks; search budget exhausted before I could pursue it.
9. **The modern Colour Index equivalent of "C.I. 707" (Soluble Blue).**

## Two rules of thumb for the design

- Every color claim here is a **b\*-axis shift at near-neutral a\***, never an RGB hue rotation.
- The **regime (masstone vs dilute) flips the sign** of the particle-size effect, so a single hardcoded warm/cool constant per ink will be wrong half the time. Tie it to the rendered ink density.

## Sources actually fetched

[pigment.tokyo — sumi basics](https://pigment.tokyo/en/blogs/article/sumi-ink-basic) · [pigment.tokyo — kogaboku](https://pigment.tokyo/en/blogs/article/sumi-ink-koboku) · [Musashino Art University — Inksticks (Sumi)](https://art-design-glossary.musabi.ac.jp/inksticks-sumi/) · [JAANUS (Columbia) — sumi](https://projects.mcah.columbia.edu/jaanus/node/915) · [ja.wikipedia 墨](https://ja.wikipedia.org/wiki/%E5%A2%A8) · [書遊Online 墨の原料と種類](https://syoyu-e.com/article/column/tools_article/sumi_genryo) · [古梅園 青墨](http://www.kobaien.jp/seiboku.html) · [urchinshome (inverted claim)](https://urchinshome.com/blogs/stories/sumi-ink-living-pigment-brush-arts) · [irocore 墨](https://irocore.com/sumi/) · [Orion Engineered Carbons TI-1464 (PDF)](https://orioncarbons.com/wp-content/uploads/2024/02/21_03_23_ti_1464_coloristic_properties_emea_web.pdf) · [PCI Magazine — Black, The Fine Details](https://www.pcimag.com/articles/110097-black-the-fine-details) · [en.wikipedia Iron gall ink](https://en.wikipedia.org/wiki/Iron_gall_ink) · [de.wikipedia Eisengallustinte](https://de.wikipedia.org/wiki/Eisengallustinte) · [dewiki Eisengallustinte](https://dewiki.de/Lexikon/Eisengallustinte) · [de.wikipedia Dokumentenechtheit](https://de.wikipedia.org/wiki/Dokumentenechtheit) · [NBS RP807, Zimmerman 1935 (PDF)](https://nvlpubs.nist.gov/nistpubs/jres/15/jresv15n1p35_A1b.pdf) · [FPN — Iron Gall Blue Black B.S.3484 1962](https://www.fountainpennetwork.com/forum/topic/331541-iron-gall-blue-black-bs3484-1962/) · [BSI Knowledge — BS 3484-1:1991](https://knowledge.bsigroup.com/products/record-inks-specification-for-blue-black-inks) · [Intertek Inform — BS 3484-1:1991](https://www.intertekinform.com/en-us/standards/bs-3484-1-1991-1991-249939_saig_bsi_bsi_581120/) · [en.wikipedia List of ISO standards 12000–13999](https://en.wikipedia.org/wiki/List_of_ISO_standards_12000%E2%80%9313999) · [en.wikipedia SWOP](https://en.wikipedia.org/wiki/Specifications_for_Web_Offset_Publications) · [en.wikipedia Ballpoint pen](https://en.wikipedia.org/wiki/Ballpoint_pen) · [en.wikipedia Bic Cristal](https://en.wikipedia.org/wiki/Bic_Cristal) · [Díaz-Santana et al., Molecules 2023 (PMC10490468)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10490468/) · [Kiran, Int. J. Adv. Res. 5(7):981–988, 2017 (PDF)](https://www.journalijar.com/uploads/2017/07/68_IJAR-18633.pdf) · [en.wikipedia Mimeograph](https://en.wikipedia.org/wiki/Mimeograph) · [en.wikipedia Spirit duplicator](https://en.wikipedia.org/wiki/Spirit_duplicator) · [en.wikipedia Toner (printing)](https://en.wikipedia.org/wiki/Toner_(printing)) · [en.wikipedia Newsprint](https://en.wikipedia.org/wiki/Newsprint)

Snippet-only (real URLs, body not retrieved): [ISO 11798:2023](https://www.iso.org/standard/83118.html) · [ISO 11798:1999](https://www.iso.org/standard/20031.html) · [Giaccai et al., J. Raman Spectrosc. 55:939 (2024)](https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/jrs.6682) · [MFA CAMEO — India ink](https://cameo.mfa.org/wiki/India_ink) · [Academy of Chinese Studies — Hui inkstick](https://chiculture.org.hk/en/china-five-thousand-years/2659) · [Higgins Inks — About](https://www.higginsinks.com/about-us) · [Blick — History of India Ink](https://www.dickblick.com/learning-resources/how-to/the-history-of-india-ink/) · [en.wikipedia Charles M. Higgins](https://en.wikipedia.org/wiki/Charles_M._Higgins) · [irongallink.org](https://irongallink.org/) · [BS 3484-2:1994](https://webstore.ansi.org/standards/bsi/bs34841994) · [DIN 51452 (diesel soot)](https://www.dinmedia.de/en/standard/din-51452/2206834)

**Note per repo policy:** this investigation cost substantial tool calls and belongs in a versioned `.md` in the repo, not only in chat. I was instructed not to write files, so I have not — but the caller should land it somewhere like `docs/ink-palette-research.md`, including the negative results (no sumi CIELAB, no blue-black Lab, no ISO 2846-2 numbers), since those are exactly the findings that stop the same searches being repeated.