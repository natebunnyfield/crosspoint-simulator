# Surface-emulation roadmap — what is missing, what is weak, and what I would never build

2026-08-22. Owner order (verbatim): *"add more papers and inks and make
suggestions on where there are gaps to be filled, enhancements to be made or
anything else that I should consider."*

The first half of that order is
[light-ink-picker.md](light-ink-picker.md). This file is the second half: a
survey of the whole surface-emulation system — light mode's paper-and-ink and
dark mode's CRT — ranking what the model does NOT do, with evidence from the
code on one side and from what real paper and real tubes actually do on the
other.

**Read the ranking, not the inventory.** A list of everything a page could
possibly do is worthless; the value is in which three things are worth doing
next and which two are traps. Those are §6 and §7. Everything before them is
the evidence.

## 0. What exists today, so the gaps are measured against something

The doctrine is [letterpress-and-scanlines.md](letterpress-and-scanlines.md):
**light mode is paper and ink, dark mode is a CRT.** As of this file the
shipped model is:

| Layer | Light | Dark |
|---|---|---|
| Tone | 17 inks x 12 papers, two Beer–Lambert dials, 7:1 clamped ([light-ink-picker.md](light-ink-picker.md), sources in [ink-colorimetry-sources.md](ink-colorimetry-sources.md) and [ink-palette-research.md](ink-palette-research.md)) | 56 phosphor presets + a 3-gun mixer ([crt-phosphor-presets.md](crt-phosphor-presets.md), [phosphor-mixer.md](phosphor-mixer.md)) |
| Structure | letterpress: squeeze ring, deboss shadow, plate pressure, in-stroke irregularity (`src/Letterpress.h`) | scanlines: box-integrated Gaussian raster, content-dependent bloom, mottle folded in (`src/Scanlines.h`) |
| Sheet / glass | paper tooth (per-stock, output-wide) + formation clouding | phosphor grain (fallback when scanlines are off, `src/PhosphorGrain.h`) |
| Marks | 6 paper defects, per-page deterministic seed (`src/PaperDefects.h`) | — |
| Leaf | sheet-to-sheet tone drift off the same page seed, +/-2 code values, off by default (`src/LightInkPalette.h`) | — |
| Motion | **nothing** | beam sweep, phosphor trail, cascade afterglow, page fade |

Every one of those passes obeys the same four invariants, and any new item on
this roadmap has to as well:

1. **Darken-only.** A multiplier above 1 is the page-flash bug class.
2. **Off is bit-exact off**, per dial, asserted by test.
3. **The 7:1 floor is structural**, not advisory — a shared `paperBudget` /
   `darkeningBudget` caps the whole stack.
4. **Generated at OUTPUT size and drawn 1:1** whenever the field is *regular*,
   because the panel is minified to ~0.7955 on a phone and a regular lattice
   written into the framebuffer beats against that resample (ST-008).

Item 4 is the one that kills most naive ideas on this list, and it is why the
cost column below is sometimes surprising.

## 1. Light mode — what a real printed page does that the model does not

The surface model is genuinely good: two-dial Beer–Lambert tone, edge-locked
ink squash, deboss shadow, plate-pressure field, in-stroke irregularity,
per-stock tooth, sheet formation, six defect types, and a per-page deterministic
seed so a leaf is the same leaf forever. What follows is what is still absent,
each rated on what it *is*, whether it *matters*, cost, and risk.

### 1a. Show-through from the other side of the leaf — **SHIPPED 2026-08-23**

**Built as specified, with four corrections, and the full writeup is
[show-through.md](show-through.md).** What changed against the design below:

1. **`ghostPixels` is the wrong source, and it was checked rather than
   assumed.** It still exists, but it is maintained only while the phosphor
   trail or the beam is on (both dark-mode ideas, both off on a paper page), it
   is ARGB that would need re-projecting onto the ink/paper axis, and it holds
   the previous FRAME rather than the previous PAGE — and an antialiased page
   produces two frames. The letterpress pass's own inkness plane is the right
   source and is already computed per page, in light mode, for free.
2. **The mirror has to be applied in PRESENTED space, not the framebuffer.** The
   framebuffer is landscape and the page is rotated into it, so a mirror about
   its x axis is a mirror about the page's *vertical* axis.
3. **The per-stock gate is a ratio of TRANSMISSIONS, not of opacities** —
   `(1 - opacity) / (1 - reference opacity)`, off a new ISO 2471 `opacity` field
   on the stock table. India 3.0x, Kozo 3.7x, calfskin vellum 0.25x.
4. **The budget is now split four ways**, and show-through takes its share
   *before* the marks are generated, so a sheet with the dial at 0 keeps
   byte-identical marks.

Measured: **+1.5 ms** per page turn at the reference stock and **+3.2 ms** at a
bible paper, on a 0.42 Mpx output; **+10.7 ms** at 1.67 Mpx. Output-space, so it
scales with output pixels — roughly **+22 ms** on a phone's 3.4 Mpx, which is
the cheap class this section predicted. Effect delta off vs on, whole frame:
mean 0.37 / max 6.0 code values on Bright White, mean 1.14 / max 17.0 on an
India-class stock, **signed negative at every pixel**. Frozen at 100 in the app;
the stock is the dial.

*The original entry, kept because its reasoning is the design:*

### 1a (original). Show-through from the other side of the leaf — **the biggest single gap**

**What it is.** Paper is not opaque. On any stock under about 90 gsm the ink on
the *verso* is faintly visible from the recto: not readable, but a soft mottling
that follows the text block's shape, strongest in the line band and absent in
the margins. On Bible/India paper it is the defining characteristic — the reason
that stock is famous.

**Why it matters.** It is the one paper phenomenon that carries INFORMATION
rather than texture. Every other pass on this page is stationary noise; this one
is a picture of another page. It is also the thing that most reliably makes a
mock page read as *paper* rather than as *a texture over a screen*, because no
screen does it.

**Cost — and the surprise.** Lower than it looks, because half the machinery is
already there. `HalDisplay.cpp` already keeps `ghostPixels`, a full copy of the
previous frame's framebuffer, maintained whenever the trail or the beam is on
(`src/HalDisplay.cpp:110`, `:2578`). A show-through pass is: mirror it
horizontally, blur it hard, attenuate it to a few percent, and fold it into the
sheet field as another darken-only multiplier — the same slot the defects use.
Call it 150 lines plus a test.

**The honesty problem, stated plainly.** What shows through page N is page
**N+1**, and `ghostPixels` is page **N−1**. A book read forwards means the
ghost is the page you just left, not the page behind the leaf. Three options,
in order of my preference:

1. **Ship it with the previous page and say so in the doc.** Show-through is
   never legible; nobody can tell which page it is. The *statistics* are right
   (same font, same measure, same line grid, same paragraph rag) and that is
   all the eye is reading. Cost: near zero. Risk: a purist objection, and a
   comment that has to be honest.
2. Ask the firmware to render N+1 into a scratch buffer. Correct, and expensive:
   a second pagination and a second render per page turn on a device whose
   whole design is "render rarely".
3. Synthesize plausible line bars at the current line height. Fake, and it will
   look fake the first time the real page has a chapter opening.

**Risk.** Low, with one real trap: show-through must be gated on the paper's
own opacity, or India paper and press gray get the same amount, which is
exactly backwards. That means a **new per-stock field** — the natural sibling
to `tooth` — which is the sort of thing to add while the table is already
being extended (§ below, and see [light-ink-picker.md](light-ink-picker.md)).

### 1b. Ink spread / dot gain by stock — **cheap, and the model is already asking for it**

**What it is.** Ink laid on an absorbent sheet spreads into the fibre. On
newsprint a printed rule is measurably fatter than the plate; on coated stock it
is not. The printing trade calls the tonal consequence *dot gain*, and it is
routinely 25–30% on uncoated stock against 12–15% coated (TVI curves, ISO
12647).

**Why it matters.** It is the second half of the tooth story and the model has
only the first. A stock's tooth already varies (`lightink::toothScaleFor`), but
the *ink* behaves identically on every sheet: a glyph on Bright White and the
same glyph on Kozo have byte-identical edges. That is visibly wrong at 3x
supersampling, where a body stroke is 12–24 framebuffer pixels and a
half-pixel spread is resolvable.

**Cost.** Low. The letterpress pass already classifies every pixel as ink,
paper, or edge band from a 3x3 luminance window; spread is a one-line change to
what the edge band does — currently it darkens (squeeze ring), and it would
additionally *bias the edge toward ink* by a per-stock fraction. Reuses the
whole existing machinery. ~60 lines plus test.

**Risk.** Medium, and specific: spread makes text *heavier*, which means it
**raises** contrast (more ink coverage). That direction is safe for the 7:1
floor. But at high spread on a rough stock, counters (the holes in e, a, o) can
close at small sizes — a legibility failure the contrast floor cannot see. Needs
a coverage cap tied to the stroke width, not a free dial.

### 1c. Sheet-to-sheet color drift through a book — **SHIPPED 2026-08-22**

**Status.** Built. `Sheet drift` in the light picker's Paper group, off by
default and bit-exact off; model in `src/LightInkPalette.h`
(`paperDriftOffsets`, `paperWorstDrift`), applied at the single read that
decides what tones the page is painted in (`livePanelPalette` in
`src/HalDisplay.cpp`); `paperDriftPercent` in `settings.json`,
`CROSSPOINT_SIM_PAPER_DRIFT` on the desktop; swept by
`tests/light_ink_test.cpp`. What follows is the original entry, kept because
its reasoning is what the build was measured against, with the outcome noted
per paragraph.

**What it is.** A book is printed on many sheets from several reams and, more
importantly, ages unevenly: the block's edges yellow faster than its middle
(the same humidity/oxygen gradient the foxing model already uses for its edge
bias). No two leaves of a 40-year-old paperback are the same color.

**Why it matters.** Every page in this app is *exactly* the same tone. That is
the single most machine-like property the light page still has, and it is
invisible on any one page and obvious across a reading session.

**Cost.** Trivial — nearly free. The per-page seed already exists and is already
deterministic across relaunches (`src/PaperDefects.h`, and `readerPageIdentity`
at `src/SimulatorOverlay.h:97`). Drift is: hash the seed to a small signed
offset, apply it to the resolved paper tone before `panelForPrefs` publishes it,
and clamp so the 7:1 floor holds at the extreme. Perhaps 40 lines.

*Outcome.* Two corrections to that plan, both found by building it. **It does
not go where `panelForPrefs` publishes the tone**: that resolver runs on iOS
only, so putting the offset there would leave the desktop and the phone free to
disagree about what page 47 looks like. It goes at `livePanelPalette`, the one
read every consumer of the page's color already goes through — the
framebuffer conversion, both contrast budgets, the grain's amplitude, the fade
floor and every field cache key. And **the clamp cannot be "clamp so the floor
holds at the extreme"** as a separate step: both existing sliders stop exactly
AT 7.0, so a leaf two code values darker sits under it by construction and no
bound is small enough to be safe. The drift dial is threaded through
`floorDensityPct` and `maxPaperStrengthPct` instead, so the boundary itself
moves and the floor is the DARKEST leaf's. That is exact rather than
probabilistic, and it costs a point or two of density at the top of the dial.
The 7:1 floor survives it with room: the worst pair at full density on the
darkest leaf is Van Dyke Brown on Laid Antique at 7.53:1, against 7.68:1
undrifted.

*Why the wash is not recomputed on the drifted sheet, which matters.* The
picker publishes the wash computed on the NOMINAL sheet and only the paper then
drifts. Holding the numerator fixed is what makes the all-negative leaf
provably the darkest — the ratio is then monotone in the ground's luminance.
Recomputing the wash on each leaf (one draft did) breaks that: byte
quantization in the wash puts a ripple in that made the −2/−2/0 leaf measure
0.004 below −2/−2/−2 on eleven ink x paper pairs, and the clamp would have had
to take a 125-way minimum. It is also not what ships.

**Risk.** Low but not zero, and it is worth naming: the paper tone reaches the
letterbox clear color and the pad field byte-for-byte (pinned by
`tests/light_ink_test.cpp`), so a per-page drift moves the *whole app chrome*
by a code value or two on every page turn. That is either delightful (the whole
book is one object) or a flicker. It must be **small** — ±2 code values, not
±8 — and it must be a dial with an off position.

*Outcome.* ±2 at the top of the dial, exactly, clamped rather than left to the
arithmetic, and off by default. The chrome question resolved the other way and
deliberately: the letterbox clear comes from `SimulatorOverlay::clearColor`
(host-published) and the pad from `padPaletteForPrefs`, and both keep the
PUBLISHED tone. The sheet drifts; the device around it does not. Measured on
six page-matched consecutive leaves at dial 100, offsets +2/+2/+1, +2/+2/+2,
+2/+2/+1, 0/0/+1, +1/+1/+1, −2/−2/−1 against a byte-identical FBFBF9 on every
drift-0 frame; no pixel anywhere moves more than 2 levels, and the six frames
are byte-identical across a relaunch.

### 1d. Deckle edges — **wanted, awkward, and probably not worth it**

**What it is.** A hand-made or mould-made sheet has a feathered, irregular edge
where the pulp thinned against the deckle frame. A trimmed trade book does not:
only untrimmed edition-bound books, hand-made stock and art papers show it.

**Why it does not matter as much as it sounds.** The panel occupies almost the
whole screen and its edge is where the page meets the bezel. A deckle there is a
**silhouette** change, not a texture change: the field would have to eat into
the panel's rectangle, and the panel rectangle is load-bearing geometry
(`panelBottomPx`, `panelLeftPx`, the pad anchoring, the zen paper band). Cutting
an irregular bite out of it means either an alpha-masked panel edge (a new
blend path in the one place the code is most careful) or a fake deckle painted
*inside* the page, which reads as a stain rather than an edge.

**Cost.** Medium-high, mostly in the geometry, not the noise.
**Risk.** High: it touches the panel rect, which four other subsystems anchor to.
**Verdict.** Only pair it with the Laid Antique / Kozo stocks, where it is
historically correct, and only as a per-stock property. Not on its own.

### 1e. Page curvature and the gutter shadow — **wrong world; do not build**

**What it is.** In a bound codex the leaf curves into the spine and a soft
gradient shadow sits along the gutter edge.

**Why it does not apply here.** This is a **one-page** device. There is no
gutter, no facing page, no binding — the margins are a single symmetric scalar
added to all four edges
(`crosspoint-reader/src/activities/reader/EpubReaderActivity.cpp:1005-1009`;
there is deliberately no inner/outer distinction because there is no recto and
verso). A gutter shadow on a single unbound page is a picture of a book, not a
page: it is the skeuomorphic page-curl of 2010 iBooks, and it is exactly the
fetishism the owner's question invited me to separate out. **Never build.**

The *one* defensible relative: a very slight overall vignette from the sheet
not lying perfectly flat. That is one line in the existing tooth field. It is
also indistinguishable from the phosphor grain's Vignette coverage, which
already exists and is deliberately skipped in light mode. If wanted, reuse it
rather than write it.

### 1f. The fetishism list — named, so it is not re-proposed

Recorded as **decided against**, with the reason:

| Idea | Verdict |
|---|---|
| Paper smell, page-turn sound, haptic "thump" | Sound and haptics are a different question from surface emulation and belong to a motion review, not here. Smell is not addressable. |
| Fingerprints, thumb wear at the corner | The defect layer can already do this (`wax spots` is sebum). A *positional* wear pattern is a per-page seed away — but it would be identical on every page in the same place, which real wear is not. Low value. |
| Dog-ears, bookmarks, marginalia, previous-owner pencil | These are *content*, not surface. They would sit over text and cost legibility with no reading benefit. No. |
| Torn/repaired edges, tape shadows | Same. No. |
| Watermarks and chain lines from a laid mould | **This one is real and I would build it** — see §7. It is a regular low-frequency line field, which is exactly the ST-008 hazard, so it must be generated at output size like every other regular field. Bundled with the Laid Antique stock. |
| Simulated paper thickness at the screen edge (a stack of leaves) | Chrome, not surface. It is the iBooks page-stack. No. |

## 2. Light mode — the typography half

Surveyed against the firmware at `~/src/crosspoint-reader`, every claim cited to
file:line. This is where the page composition actually lives, and it is
**further along than the surface model** — which is worth saying, because it
changes what is worth doing next.

### Already there (do not re-propose)

| Feature | Where |
|---|---|
| Hanging punctuation, **right edge**, justified LTR — full hang for `.` `,`, half for `; : ! ? - ' " ‘ ’ “ ”`, measured in the word's own style, and it does not change line breaks | `lib/Epub/Epub/ParsedText.cpp:255-289`, applied `:1274-1284` |
| Widow/orphan control, keep-2/2, with a three-line holdback buffer and an all-or-nothing rule for 3-line paragraphs | `lib/Epub/Epub/parsers/ChapterHtmlSlimParser.cpp:2509-2606` |
| Baseline/line grid, snapping lines and block spacing — **implemented but OFF by default** (`lineGridEnabled` defaults to 0), which is worth knowing before anyone reports the page as ungridded | `ChapterHtmlSlimParser.cpp:2489-2495`, default at `src/CrossPointSettings.h:347` |
| Chapter sinkage, viewport/5 snapped down to whole lines, first page of a section only | `ChapterHtmlSlimParser.cpp:2450-2458` |
| Real Knuth–Liang hyphenation with generated tries | `lib/Epub/Epub/hyphenation/LiangHyphenation.cpp` |
| Real pair kerning from `kern` + GPOS, baked to a class matrix at font-build time | `lib/EpdFont/EpdFont.cpp:104-118`, built by `scripts/fontconvert_sdcard.py:143-166` |
| Real ligatures from GSUB `liga`/`rlig`, with a presentation-vs-lexical filter | `EpdFont.cpp:118-131`, built `fontconvert_sdcard.py:230-263` |
| A total-fit DP paragraph optimizer minimizing Σ(remaining space)² | `ParsedText.cpp:805-1002` |
| Em-dash line-initial protection, NBSP/NNBSP, soft hyphen, NFC, CJK/JLReq break tables, ruby overhang | `ParsedText.cpp:291-303`, `ChapterHtmlSlimParser.cpp:1883-1939`, `ParsedText.cpp:62-144`, `:709-800` |

### The four real gaps, ranked

**T1. The total-fit optimizer is dead code in the shipping configuration.**
`computeLineBreaks()` is a Knuth–Plass-shaped DP over the whole paragraph
(`ParsedText.cpp:805-1002`). But hyphenation is `static constexpr 1`
(`src/CrossPointSettings.h:356`), and when hyphenation is on the code takes
`computeHyphenatedLineBreaks()` (`:1005-1089`), which is **greedy first-fit with
mid-word splitting**. So the good line breaker never runs on a shipping build.
This is the highest-value typography item on the page and it is a *merge*, not a
new algorithm: put hyphens into the DP as candidate breaks with a demerit, which
is what Knuth–Plass does. Cost: high (it is the paragraph engine, and every
change repaginates — `ReaderRenderSpec` keys the section cache). Risk: high, and
it is a firmware change, not a simulator one. But it is the difference between
"a machine broke these lines" and "a typesetter did".

**T2. Justification has no word-space limit — by explicit decision.** PARTLY OVERTAKEN 2026-08-23 by automatic justification (firmware `7b75aa06d`): the measure now decides justified vs ragged at Bringhurst's 40-character threshold, so the worst case this item describes -- a short justified line with few gaps -- can no longer arise from a NARROW measure. It can still arise inside a wide measure on a short last-line-but-one, so the stretch limit remains a real item, at lower value.

ORIGINAL ITEM: 
`computeJustifyExtra()` (`ParsedText.cpp:200-208`) distributes spare space
evenly across the gaps and the comment says it **deliberately does not cap the
stretch**. There is no minimum/maximum word space, no glue shrink, and no
letterspacing fallback. That means a short justified line with few gaps opens
them arbitrarily wide — rivers, and the classic "one word and a mile of space".
Every serious justification engine has a stretch limit that, once exceeded,
either hyphenates harder or gives up and sets the line ragged. Cost: medium.
Risk: medium (it changes measure-fit, so pagination moves). This and T1 are the
same conversation.

**T3. ~~Optical margins are right-edge only.~~ SHIPPED 2026-08-23** (firmware `bdfe5f663`). One table with a leading column rather than a parallel table; trailing values byte-identical. Measured on X3 at 18 px: opening double quote -5 px, single -3, open paren -2, em dash -10, ordinary lines 0, line bands unchanged. Dashes hang a QUARTER not a half -- half an em measured 14 px, wider than the whole left margin at Screen Margin 0. The build also found a clipping bug the item did not anticipate: an uncapped hang walks off the panel edge rather than into a margin, so it is clamped to the real gutter. Section cache 42 -> 43, because a hang is break-neutral but its painted x lives in the cached blocks.

ORIGINAL ITEM:  The opening quote, the opening
parenthesis, and a capital `T`/`W`/`A` at the start of a line should also hang
*left* — that is what "optical margin alignment" means in a proper setter, and
the left edge is the one the eye reads down. Half the feature is missing and it
is the more visible half. Cost: low-medium (the machinery and the character
table already exist at `ParsedText.cpp:255-289`; it needs a *leading* twin and
a negative x-offset at paint). Risk: low — it does not change line breaks, by
the same argument the trailing hang already uses (`:1265-1273`).

**T4. The SD-font measurement path drops kerning that the paint path applies.**
Recorded as P0 in the firmware's own audit
(`crosspoint-reader/docs/punctuation-kerning-audit-2026-08-22.md:230`): the
advance-table fast path measures SD reading faces *without* kerning while the
glyph cursor draws *with* it. Every on-card family therefore lays out to a
measure it does not paint. This is a bug, not a feature gap, and it belongs to
the firmware repo — listed here because it silently degrades every other
typography item above it.

### Explicitly closed, and staying closed

Small caps (real or faked), drop caps/versals, and running heads/folios are all
absent and all **declined by owner ruling** —
`crosspoint-reader/docs/punctuation-kerning-audit-2026-08-22.md:299-300` for the
first two, and the reading page paints only `page->render(...)` with no header
or folio (`EpubReaderActivity.cpp:1582-1750`). I am not re-proposing them.
Two notes for the record, though: **optical letterspacing of caps runs** (§12 of
that audit) is absent and is the *one* piece of small-caps-adjacent work that is
worth having on its own — an all-caps run set at the body tracking always looks
tight — and **first-line indent is dead code**: `resolveFirstLineIndent()`
(`ParsedText.cpp:605-619`) returns the CSS indent only when negative once
`extraParagraphSpacing` is on, and that flag is `static constexpr 1`
(`src/CrossPointSettings.h:288`), so the 3-space default at `:616` is
unreachable. The app is space-between-paragraphs, permanently, whatever the
publisher's CSS says. That is a defensible house style but it is currently an
accident of a constant rather than a decision, and it should be one or the
other.


## 3. Dark mode — what a real CRT does that the model does not

The stated fiction (from [letterpress-and-scanlines.md](letterpress-and-scanlines.md))
is a **monochrome raster page display** — one gun, one continuous phosphor
coating, a portrait text screen of the IBM 5151 / Macintosh Portrait Display
class. That choice does more work than it looks, because **it disqualifies
several of the most famous CRT artifacts outright**, and the disqualification is
sourceable rather than a matter of taste. So the negatives come first: four of
the items the order named are things I would not build at all, and the evidence
says so.

Sources for this section are primary where they exist: **AAPM TG18**
(*Assessment of Display Performance for Medical Imaging Systems*, Report OR-03,
[PDF](https://www.aapm.org/pubs/reports/OR_03.pdf)) is the standards backbone,
because medical imaging is the one field that specified monochrome CRTs to a
tolerance; **ISO 9241-3/-7** for ergonomics; the **IBM 5151 Options and Adapters**
manual for the device itself; and the libretro shader corpus read as source for
what emulation practice actually does.

### Ruled out by the fiction — do not build these

| Artifact | Why it does not apply |
|---|---|
| **Convergence error** (color fringing at the corners) | Convergence is the alignment of THREE beams onto three phosphor sets. A monochrome CRT uses a single electron beam; there is nothing to converge, and the artifact is *made of color*, so it would render as color fringes on a one-phosphor display. It is also the single most commonly faked CRT effect. The correct monochrome analogue is spot **astigmatism** — see D3. |
| **Shadow mask / aperture grille**, and blooming into it | A monochrome tube has neither; the phosphor is a continuous coating. That is *why* mono tubes out-resolved color tubes of the same size — mono resolution is limited by beam focus, color resolution by phosphor pitch. It also deletes mask moire, dot crawl and the whole `mask_amplify`/`autodim` machinery every color shader needs. |
| **Interlace / interline twitter** | Page displays were progressive, emphatically. The IBM 5151 runs 18.432 kHz horizontal against 50 Hz vertical — 368.6 lines per field against 350 active, one progressive frame. TG18 §2.3.1.1 describes medical displays addressing up to 2000 lines "in noninterlaced (i.e., progressive) mode". Interlace on computer displays was a cost hack people bought hardware ("flicker fixers") to undo. |
| **The degauss swirl** | Degaussing demagnetizes the *shadow mask*, and the visible swirl is misregistered color. Monochrome tubes "don't have anything inside to get magnetized"; the earth's field produces at most a slight position or rotation shift, which some mono monitors trimmed with a tilt coil. The coil's mechanical thump is real; the picture does not swirl. |

Four of the order's suggestions ruled out on evidence, which is the useful half
of asking.

### The uncomfortable one: scanlines may be wrong for a PAGE display

Recorded because it is load-bearing and because the doc it contradicts is this
repo's own. TG18 specifies the **resolution–addressability ratio** — the spot's
50%-luminance diameter divided by the pixel pitch — at **0.9 to 1.1** for a
primary-class display (§2.4.10, §4.5). RAR ≈ 1 means adjacent lines *overlap*:
a 640x870 or 1152x870 monochrome page monitor has **no visible gap between scan
lines**. Visible line structure is a low-resolution-console artifact — a 240-line
signal on a 480-line tube — not a page-display one.

**This is not a call to remove the dial**, and it must not be read as one. The
scanline model is the owner's standing order, it is well-built, its moire hazard
is genuinely engineered out, and someone may want the *look* of a raster
independent of which tube it came from. What it changes is the **justification**:
the honest framing is "a coarser raster than a page display had, because the
structure is wanted", not "this is what a page display looked like". If the
fiction is ever revisited, the cheap reconciliation is to say the tube is a
lower-resolution monitor scaled up, which is exactly what the Scanline Size
ladder already offers (Fine 100 through Chunky 300) — Chunky is closest to
honest, and Fine is the least. TG18 also independently justifies something else
this repo already ships: the blended white phosphors (P4, P104) that most
monochrome monitors used "generate a **fixed spatial noise pattern**" in the
image (§2.4.8). The grain field is more defensible than the line field is.

### Genuinely missing, and genuinely applicable

**D1. Diffusion in the faceplate — the biggest real gap, and it is NOT halation.**
The research changed this item's name, which matters because the two words are
used interchangeably in shader-land and not in physics.

- **Blooming** is *electron-optical*: more cathode current uses more cathode
  area and defocuses the beam. It happens before any light exists. This is what
  `scanlines::` bloom already models.
- **Halation**, strictly, is total internal reflection at the outer glass/air
  boundary: light returns to the phosphor and re-emerges displaced by roughly
  twice the glass thickness — a *ring* offset by centimetres on a 10 mm
  faceplate.
- **Diffusion** is bulk and surface scatter in that same thick glass: a
  monotonic halo, not a ring.
- **Veiling glare** is none of those three; it is the *metric* — how much a
  bright surround lifts a dark region's luminance.

TG18 §4.7.1 decomposes veiling glare in a **monochrome** CRT into three
contributors — electron reflection off the aluminium backing, secondary
electrons, and light scattering in the glass faceplate — and names the third
**dominant**. So for this fiction the thing to build is **diffusion**, unmasked,
over everything, and the ring-shaped halation is the *less* important half.
CRT-Royale's own defaults agree from the other direction: `diffusion_weight
0.075`, `halation_weight 0.0`.

*Why it matters:* it is what makes white text on a dark tube feel like it is
*inside* something, and it is why a real CRT's blacks lift near dense copy and
stay deep in the margins. The dark page currently has bloom (electron optics)
and no glass at all.

*Cost:* medium, with one hard structural cost. Diffusion is **additive light**
and every pass in this repo is darken-only because "an additive lift is exactly
the page-flash and gray-background bug class" (`docs/phosphor-grain.md`). It
therefore cannot be another MOD field: it has to be a separate additive draw of
a heavily blurred panel copy, composited before the darkening passes, and gated
by a budget running the *other* way — diffusion lifts the dark ground toward the
ink, so the 7:1 floor becomes its ceiling. That new budget is the main cost.

*And the magnitude has to be a fraction of the truth, which is a real finding.*
Measured glare ratios: **89 for a monochrome monitor and 138 for a medical
imaging CRT without AR coating**, against TG18's own *minimum acceptable* of
**400** for primary-class reading and an ideal of 1000. Authentic monochrome-CRT
glare is an order of magnitude worse than the threshold at which the diagnostic
community declared CRTs unfit to read from. Ship a small fraction, and say in
the doc that the physically correct setting is worse than the shipped one and
that this is deliberate.

*Risk:* medium-high. First pass that can brighten, so the darken-only invariant
is carved deliberately rather than broken accidentally.

**D2. Geometry — barrel/pincushion and the curved faceplate. Still no.**
Two separable causes that shaders conflate: the **yoke** sweeps equal angles
across unequal distance (corrected by the S-correction capacitor; the residual
is the published linearity error), and the **glass** is a spherical or
cylindrical cap. TG18 accepts **≤ 2%** geometric distortion for primary class,
and the commercial spec line it quotes is 10% non-linearity with 0.5% HV-driven
size change. The shader corpus offers four genuinely different models — cgwg's
CRT-Geom does a true ray/sphere intersection with arc-length mapping,
CRT-Royale adds a cylindrical Trinitron mode, CRT-Lottes uses a cheap separable
quadratic (`warpX 0.031`, `warpY 0.041`), MAME uses a Brown–Conrady radial
polynomial.

**I would still not build it, and I want to record that the research disagrees
with me at low amplitude** (its verdict was "keep very small, using a physical
model rather than a cheap warp"). My reason is specific to this app rather than
general: a warp is a resample, and this repo has a *measured* ruling on what
resampling does to its own page — ST-008, 8.14 levels of beat on a Bayer-dithered
fill under the phone's 0.7955 minification. The shader corpus never faces a
1-bit dithered source at a fractional presentation scale; this app always does.
A curvature pass puts that hazard back on purpose, on every page, permanently,
and bows the baselines while it does it. The representable fraction — **corner
luminance falloff with no geometric change** — is real, citable (TG18 §2.4.12:
up to **15%** centre-to-edge for a monochrome faceplate at 34% transmittance,
against 7% for a color tube at 55%) and already available for free as the
grain's Vignette coverage. Take that half; leave the warp.

**D3. Corner defocus — SHIPPED 2026-08-23.** Built as specified, including the
research's ellipticity refinement. Full writeup: [corner-defocus.md](corner-defocus.md).
Two things this entry did not anticipate, both measured:

- **The mean-preserving normalization must divide out the DEFOCUS and not the
  BLOOM.** Both scale the same sigma, so the tempting economy is one table axis
  over their product; it is arithmetically identical inside the integrator and
  wrong at the normalization, and it softened the raster by 27% AT THE CENTRE.
- **The effect is sub-code-value at the raster depths this app ships.** The
  corner's raster peak-to-peak falls 41% (1.79 → 1.05 levels) and the centre's
  falls exactly 0%, which is the model working — but the whole-frame delta is
  `max |d| = 1.0` code value, so no honest native-pixel figure can show it. Cost
  is **+10.3 ms** per dark page turn at 0.42 Mpx and **+23.5 ms** at 1.67 Mpx,
  extrapolating to ~+42 ms on a phone. Whether that trade is worth making is a
  live question and the doc states it rather than burying it; turning
  `cornerDefocusPercent` to 0 costs nothing and keeps the work banked.

*The original entry:*

**D3 (original). Corner defocus — the cheapest real item on this list.**
*Mechanism:* the corner is further away and the beam lands obliquely, so the
spot is both larger and **elliptical**. Correction circuits drive focus from a
signal proportional to **X² + Y²**, which is exactly the shape of the error. The
best tubes added dynamic astigmatism on top.

*Magnitudes, all TG18:* "it is normal for the performance at the center to be
better than that at any corner due to natural deflection distortions" (§4.5.3.2);
"the corners always yield lower values than the center" (§4.5.4.2.1); and the
one hard number — **astigmatism ratio (long axis / short axis of the corner
spot) must be < 1.5** for primary class. No datasheet giving spot size in mm at
centre versus corner was found, and the widely-repeated "0.1–0.2 mm centre vs
0.3–0.5 mm corner" figure is about *color convergence*, not mono spot size —
treat it as unsourced.

*Why it is cheap here:* the scanline field already computes a per-pixel sigma as
`kSigmaFrac · pitch`. Growing it as **σ(r) = σ₀·(1 + k·r²)** — the parabola the
correction circuits themselves use, not a linear ramp — is a small change to an
existing pure model plus a test. And the research's refinement is worth taking:
apply it as **ellipticity** (radial vs tangential) rather than isotropic blur.
An elliptical spot reads as character; an isotropic blur reads as the corner
text being worse. *Risk:* low — it only softens, never resamples, never
brightens.

**D4. HV sag — the raster breathes. I had this in "never build" and the
measurements moved it.**
*Mechanism:* a bright frame draws more beam current, the EHT supply droops, the
beam gets less stiff, and the same yoke current deflects it further: the picture
is physically **larger and slightly dimmer**. The repair literature's own
threshold is that "a slight change in size is unavoidable but if it is greater
than 1 or 2 percent from a totally black image to a full white one, this is
either an indication of a defective TV or one that is badly designed"; TG18's
commercial spec line is **HV regulation 0.5% max size change**.

*Why I changed my mind:* my objection was that a scale change is D2's resampling
hazard in time-varying form, and that a page which breathes is motion sickness
rather than nostalgia. Both still hold — for a *steady-state* effect. But the
real magnitude is **0.5–2%**, not the 20% the shader dials offer, the mean
coverage of a page is known for free, and **the effect is exactly zero while a
page is static.** It manifests only in the instant a page turns, which is
already a moment this app spends 30–300 ms on. A resample that persists is
ST-008; a resample that lasts a page turn is a page turn. Two shaders give a
usable formulation off a whole-frame average luminance, and cgwg's
`crt-geom-deluxe` does the right thing by driving **both** the sampling rect and
the output brightness from one scalar (`rbloom = 1.0 - rasterbloom * (avgbright
- 0.5)`).

*Condition on shipping it:* it must return to exactly 1.0 when the page settles,
bit-exactly, or it is a permanent resample wearing a transient's clothes.

**D5. Video-amplifier band limit — and the asymmetry nobody models.**
The IBM 5151's video path is **16.257 MHz at −3 dB** for 720 pixels per line: a
real horizontal band limit, so horizontal edges are physically softer than
vertical ones. TG18 states the same structurally — "the vertical height of a
pixel is controlled by electron optics, while the horizontal width is controlled
by the video amplifier" — and the measured result on a monochrome medical CRT is
sharper than that: the **rising and falling horizontal MTFs were remarkably
different, while the vertical ones were practically identical**, attributed to
the amplifier's ability to transition between command levels. So the honest
artifact is a *horizontal-only, direction-dependent* edge response: the left
edge of a stem does not look like its right edge.

Nothing in the shader corpus models this. It is also the closest cousin the dark
page has to a pass it already owns — the letterpress squeeze ring is an
edge-locked, direction-aware field, and the code shape would transfer nearly
directly from the other mode. **Sub-pixel is character; visible is the
"sharpness set too high" halo, which is fatiguing over an hour.** Cap it hard or
leave it.

**D6. Burn-in — real, correctly understood, and I would not ship it on.**
The direction is the part fakes get wrong: burn-in is **dark**. It is a
permanent loss of phosphor efficiency (color-center formation, dead-layer
growth, activator oxidation), so a burned area emits *less* and shows as a dim
negative of the persistent furniture on a bright field. A bright ghost is
persistence, not burn, and it decays. TG18 is deliberately unquantified — "hours
of use reading one type of image or displaying a menu bar will ultimately affect
the phosphor" — and the circulated "10,000 h / 100 C/cm²" figure could not be
verified in its source, so treat the timescale as unknown.

The trap that is fatal to the naive version: burn is in the **screen's**
coordinates, not the content's. A burn that follows the text is a bad drop
shadow. The honest artifact is a stationary ghost of the page furniture, seeded
once per install and *persisted* — a genuinely new kind of state here, where
everything else is per-launch or per-page. And for a reading app the verdict is
the research's: a persistent second image is a distractor by construction. Fine
as a one-shot "vintage" screenshot mode; wrong as a default.

**D7. The curved-glass room reflection — no.**
Real, and quantified: untreated glass reflects **~4%** at normal incidence,
rising to **~35% at 80° incidence**; etching halves it to ~2% at the cost of
blurring the emitted image too; multilayer AR coatings reach 0.1–0.5% but cut
transmission to 60–90%. NIST's measured BRDF puts a CRT's specular peak at
~100 sr⁻¹, "roughly a factor of ten greater than the maximum haze peak observed
for the FPDs", because the thick faceplate forbids strong surface treatments.

None of that helps, because **there is no room**. Synthesizing a reflection means
inventing a window and a lamp and painting them on the page — a picture of a
photograph of a monitor. The two shaders that try (`vt220.slang`,
cool-retro-term) both use static gradients that do not move with the viewer,
which is the entire physical point. The phone's actual glass already reflects
the actual room, correctly and for free.

**D8. The power-off collapsing dot — SHIPPED 2026-08-23**, and it is the one
item of the three that became a Settings.app row rather than a frozen value:
turning it on trades the sleep screen for the shutdown, and that is a trade only
the owner may make. Default OFF. Full writeup:
[power-off-collapse.md](power-off-collapse.md). The place it goes is not
`presentIfNeeded` — it is `HalGPIO::startDeepSleep`'s terminal loop, which is
the only place an animation can run *after* the app is asleep without delaying
sleep by a millisecond. One measured surprise: **the firmware draws its sleep
screen in LIGHT polarity even when the reader was dark**, so the obvious
"is the page dark" gate answers about the sleep screen and the artifact never
fires; a `lastReadingDarkGround` latch on every non-sleep present is the fix.
Measured at 1028 ms end to end, and zero cost to a page turn because it never
runs during one.

**D8b. BZZT THONK, the tube coming back — SHIPPED 2026-08-23**, on the SAME row
(owner: *"show crt powering on animation if power off animation is enabled"*,
refined to *"only when there's a dot there, then do the 'bzzt thonk' screen
warmup animation"*). The trigger is a recorded STATE -- the collapse having
actually switched the tube off -- not a wake event, so a cold launch, a wake with
the dial off and a firmware restart all miss it. 395 ms: the dot relit at the
collapse's own width, an electrical flicker with the line punching out sideways
in four steps, the raster slamming open past the panel and bouncing back, then a
6% sag under the finished page and exactly nominal. It composites in
`presentIfNeeded` rather than owning its frames, because the firmware is booting
underneath it. Two measured surprises: the wake path does NOT have the mirror of
the sleep screen's polarity trap (the `Boot` activity exits without presenting),
and a gate finer than one frame is never drawn at all -- the first bzzt had four
bursts of 1.6-4 ms and rendered as no flicker whatsoever. Full writeup:
[power-off-collapse.md](power-off-collapse.md).

*The original entry:*

**D8 (original). The power-off collapsing dot — the one delight I would ship.**
The sweeps collapse before the cathode is cut off, so the beam concentrates at
the centre and leaves a bright stationary spot that fades over about a second;
there are patent families devoted to protecting the phosphor from it. It is
bounded, one-shot, and this app has an exact place to put it — the **sleep
transition**, which already has a beam-sweep-aware path (`HalDisplay.cpp:3519`).
It never appears while reading and it cannot cost legibility, because there is
nothing left to read.

### Verified negatives — checked, already right, do not re-derive

- **The trail deposits with MAX, not a blend.** Five of the six shaders surveyed
  combine persistence as `max(new, decayed)` rather than `mix()`, and the reason
  matters: with `mix` every page turn looks like text fading *in* and every glyph
  edge is permanently soft. This repo already gets it right —
  `src/HalDisplay.cpp:2696` uses `depositMax` with an additive fallback. Nothing
  to do.
- **The scanline field cannot moire against the mask**, because there is no mask.
  The app's real moire exposure is the *resampling* beat, ST-008, and
  `panelScaleModeFor()` already treats it. Do not add a "CRT moire" pass on top.
- **Retrace lines are a fault condition**, not normal appearance — they mean G2
  is too high or blanking has failed. Not a period detail.
- **Flyback whine is period-dependent and probably wrong here.** The famous
  15.734 kHz is NTSC; the IBM 5151's 18.432 kHz would be audible to young ears,
  but Apple's page displays ran ~68.85 kHz, far above hearing. A 1990s page
  display is silent.
- **Brightness is a DC bias on the cathode drive, not a normalized curve.** If a
  brightness control is ever added, the black floor must move with it; contrast
  is the gain. Getting this backwards is the standard mistake.

## 4. Cross-cutting

### 4a. Motion — light mode has none, and that is the asymmetry

Dark mode has four time-varying dials: beam paint (0/17/33/67/150/300 ms),
phosphor trail, cascade afterglow, and page fade
([crt-beam-and-flash.md](crt-beam-and-flash.md)). Light mode has **zero**. A
page turn in light mode is an instantaneous swap, held 30 ms by
`kPresentHoldMs` purely to coalesce the two-pass compose
(`src/HalDisplay.cpp:519`).

**What is authentic per world?** This is the question worth answering before
any code:

- **Dark mode / CRT.** The beam sweep is right and is already there. What is
  *missing* is that a CRT does not clear before it paints — the old frame is
  still glowing when the new one is drawn over it, top to bottom. The current
  sweep reveals the new frame progressively, which is the correct shape. Good
  as is.
- **Light mode / paper.** A printed page does not animate; a *page turn* does.
  The honest options are (i) nothing, which is what ships, (ii) an **e-ink
  flash**, and (iii) a paper turn animation. Option (iii) is the iBooks curl
  and is out on the same grounds as the gutter shadow (§1e).

  Option (ii) is the interesting one and it is *already half-built*. The device
  this simulates **is an e-ink reader**, and a real e-ink panel's full refresh
  inverts the page once before settling — that is the black flash every Kindle
  owner knows. `CROSSPOINT_SIM_PRESENT_FLASH` and the `Page Turn Flash` setting
  already exist and are already "what the panel itself does" (per CLAUDE.md).
  But they are a *presentation* artifact, not an emulated refresh waveform: the
  real thing is a several-hundred-millisecond sequence of inversions, and a
  faithful version would be a small state machine over the panel texture.

  **My view: this is a THIRD doctrine, not a light-mode feature** — see §4d. The
  paper page should not flash, because paper does not. The e-ink page should.

### 4e. The plumbing — one dial table, and why it is the root cause

**Added 2026-08-23, owner ruling: "yes — it is the root cause."**

Adding one surface effect used to touch this many places:

| Site | What it carried |
|---|---|
| `src/SimulatorOverlay.h` | the setter's declaration |
| `src/HalDisplay.cpp` | the atomic |
| `src/HalDisplay.cpp` | the setter, with its own hand-rolled `strtol` env parser |
| `src/HalDisplay.cpp` | a line in the desktop boot seed |
| `src/HalDisplay.cpp` | a line in the `CROSSPOINT_SIM_AS_SHIPPED` block |
| `src/HalDisplay.cpp` | the use in the render path |
| `src/SimulatorSettingsFile.h` | a template entry |
| `src/SimulatorSettingsWatch.cpp` | a `dial()` line |
| `ios/CrossPointPrefs.{h,mm}` | a getter |
| `ios/CrossPointIOSShim.cpp` | a poll |
| `tests/run_all.sh` | a line, if the model gets its own test |

Three of those — the boot seed, the watcher's `dial()` line and the as-shipped
block — were **parallel lists of the same numbers, kept in sync by hand**. They
drifted twice in one day:

- the **beam** sat at 67 ms after the app hard-set 55 (a 21% longer sweep on
  every desktop reproduction of a beam or page-turn report);
- the **grain** had three of its four arguments wrong — 100/8/30 against the
  app's 160/5/90.

Both were found by a person reading two files side by side. Nothing failed,
and nothing *could* fail: the app's values live in Objective-C that no host
test can compile, and the seed's live in a C++ block no phone runs.

**[`src/SimulatorDials.h`](../src/SimulatorDials.h) is now the one list.** One
row per dial — name, env var, settings key, clamp bounds, desktop default,
shipped value, flags — and the seed, the watcher and the as-shipped block are
all generated from it. `SimulatorOverlay::applyDials` /`applyDialGroup`
(defined in `HalDisplay.cpp`, beside the atomics) are the only thing that turns
a row into a setter call; the table itself holds no function pointers, so it
stays pure and host-testable.

Three dials genuinely do not share the others' shape, and each is a **flag**
rather than a special case at three call sites:

| Flag | Dial | Why |
|---|---|---|
| `kMultiArg` | the grain's four rows | `setPhosphorGrain` takes four arguments together; the rows share a group, so the watcher's absent-key rule is all-or-nothing across them |
| `kReconverts` | sheet drift | it moves the page's own tones, so the cached frame must be re-converted, not just re-presented |
| `kNoPresent` | power-off collapse | nothing about a live page changes, and it is read only once the firmware is asleep |

A fourth turned up while converting the env parsers: the grain's **coverage,
cell count and mottle depth accept a NEGATIVE env value** and let the pure model
clamp it, while the strength beside them refuses one. Preserved as
`envPercentOr(..., kAcceptAnyValue)` rather than quietly normalized — a refactor
is not the place to decide which of the two is right.

**[`tests/dial_table_test.cpp`](../tests/dial_table_test.cpp) is the point of
the exercise.** It reads the shipped `ios/` sources as text — the frozen
getters in `CrossPointPrefs.mm`, the paper constants in
`CrossPointLightInkPicker.mm`, `kBeamPaintMs` in `CrossPointIOSShim.cpp`, the
toggle defaults in `Root.plist` — and fails when what `CROSSPOINT_SIM_AS_SHIPPED`
seeds is not what the app pushes. Both historical drifts were replayed against
it: the beam produces one failure naming both numbers, the grain produces
exactly three.

That test deliberately does **not** solve the problem by making
`CrossPointPrefs.mm` return `simdials::kDials[].shippedValue`. That would leave
one record, and a test comparing a value to itself proves nothing. Two
independent records, mechanically compared, is the design.

What a new dial costs now: the same four irreducible sites (declaration,
atomic, setter, render use), **one table row** in place of the three
hand-synced value lines, and one `case` in `applyDialGroup` — which has no
`default:` label, so a row added without one is a `-Wswitch` warning rather
than a dial that ships doing nothing.

### 4b. Accessibility — one part is exemplary, one part is untouched

**The page is fine, and better than fine.** `ios/CrossPointAccessibility.h`
installs a real `UIAccessibilityElement` container over the SDL view, and
`ios/CrossPointPageTextInput.h` adopts the WWDC26-219 `UITextInput` pattern so
VoiceOver's rotor, Speak Screen, Braille displays and Switch Control all get
granular navigation of the page text — fed by the read-aloud capture channel.
The surface passes cannot interfere with any of that, because they are
composited at present time in the renderer and the accessibility tree is built
from the *captured text*, not from pixels. **No surface dial can break
VoiceOver.** That is a genuinely good architectural outcome and it should be
stated so nobody worries about it.

**The controls are not fine.** There is no `accessibilityLabel`,
`accessibilityValue`, `accessibilityHint` or trait anywhere in the harness's
UIKit code — a grep for `accessibilit` across `ios/` returns only the page
container and the read-aloud plumbing. Concretely, in the page-color drawer:

- The **ink rows** are `UIButton`s whose visible text lives in two *child*
  `UILabel`s (`_inkName`, `_inkEra`) rather than in the button's title
  (`ios/CrossPointLightInkPicker.mm:441`, `:448`). A `UIButton` with no title
  has no default accessibility label, so VoiceOver announces an unlabeled
  button. With 8 inks that was 8 unlabeled buttons; with 17 it is 17.
- The **paper cells** do set a title (`:505`), so they announce — but as a bare
  name with no indication of which is selected.
- **Every slider** — density, paper, tooth, formation, defects, and the three
  press dials — announces as "N percent" with no name, because none sets a
  label. Eight anonymous percentages.
- Selection state is carried entirely by a border/checkmark, with no
  `UIAccessibilityTraitSelected`.

Cost to fix: **very low** — a label, a value and a selected trait per control,
perhaps 40 lines total, and it is the sort of thing that is embarrassing to
leave once the row count doubles. Risk: none.

**Dynamic Type.** The harness uses fixed point sizes and manual frames
throughout (`ios/CrossPointLightInkPicker.mm:667-758`), so the drawer does not
respond to the system text size at all. That is a fixed cost of the
manual-frames decision and it is defensible for a tuning panel; it is *not*
defensible if the drawer becomes the primary picker. Worth a note, not a
project. Note that the *reading page's* type size is the firmware's own setting
and is unaffected.

**Reduce Transparency / Reduce Motion / Increase Contrast.** None is consulted.
The two that matter: **Increase Contrast** should arguably push the 7:1 floor
up (the machinery is a constant, `lightink::kContrastFloor`, so this is a
one-line change plus a re-derivation of every clamp), and **Reduce Motion**
should zero the beam sweep and page fade. Both are cheap and both are the kind
of thing an App Store reviewer notices.

### 4c. Power and thermal on a phone

The measurable costs, **as this section originally ranked them** — kept because
the measurement below overturns two of the three, and the wrong ranking is
worth being able to see:

1. **`SDL_RenderReadPixels` of the whole output.** The scanline pass reads the
   composed backbuffer back to the CPU to compute its bloom level map
   (`src/HalDisplay.cpp:2429`), and the screenshot path does the same
   (`:3456`). A GPU→CPU readback stalls the pipeline; at ~1260x2736 that is
   ~13 MB per readback. It happens on **page turns**, not frames, which is what
   makes it affordable — a still page costs nothing.
2. **Field regeneration.** The sheet field is output-sized (~3.4 Mpx) and, since
   paper defects landed, rebuilds **once per page**. The defect marks are
   rasterized over their own bounding boxes only, so the marks are cheap; the
   tooth is the per-pixel cost.
3. **The letterpress panel field** is framebuffer-sized (2376x1584 at 3x on an
   X3 page = 3.8 Mpx) and regenerates on `pixelBufSeq`, i.e. up to twice per
   page (1-bit pass, then AA compose).

So a page turn currently costs roughly: one to two panel-field builds, one
sheet-field build, one full readback, and several texture uploads, all on the
main thread inside `presentIfNeeded`.

### Measured, 2026-08-22 — `CROSSPOINT_SIM_LOG_TIMING=1`

This section used to say "nobody has measured this". It is measured now. The
instrument is `CROSSPOINT_SIM_LOG_TIMING=1` (`src/HalDisplay.cpp`): one
`[timing]` line per present, reporting each pass as **BUILD / cache / off**
with its wall time, the readback separately, the flip separately, and the
total. The env read is **latched once** rather than read per present, and every
station is a branch on a `false` bool when it is unset — an instrument that
added a `getenv` and a clock read to each pass it measures could not report
those passes honestly.

Conditions: Mac, Metal renderer, real window, X3 profile, six consecutive page
turns of a real EPUB driven by `QTAP:RIGHT`. Medians over the six; the cold
first build is excluded. Idle = a present where every pass is served from
cache.

| Arm | Render scale | Page turn, total | Panel letterpress field | Sheet field | Scanline field | Readback | Idle present |
|---|---|---|---|---|---|---|---|
| Light, letterpress 100 + tooth 180 + formation 55 + defects 30 | 1x | **99.0 ms** (66–148) | 56.8 ms | 31.9 ms | off | none | **0.41 ms** |
| Light, same dials | 3x | **697 ms** (574–727) | 489 ms | 29.8 ms | off | none | **2.38 ms** |
| Dark, scanlines 50 | 1x | **42.6 ms** (40–52) | off | off | 35.8 ms | 1.77 ms | **0.42 ms** |
| Dark, scanlines 50 | 3x | **115 ms** (49–153) | off | off | 38.6 ms | 2.51 ms | **2.85 ms** |

Six things in there are worth naming, and three of them contradict what this
section assumed (items 1, 2 and 3; items 4 and 5 confirm it).

1. **The readback is not the expensive item — it is the cheapest thing on the
   list.** It was ranked first here. Measured, it is 1.8–2.5 ms of a 43–115 ms
   dark page turn: 2–6%, and it barely moves with the render scale because it
   is output-sized. The GPU→CPU stall that the ~13 MB figure implies does not
   materialise on this renderer.
2. **The letterpress panel field dominates absolutely everything, and it is
   the one pass that scales with the render scale.** 57 ms at 1x, **489 ms at
   3x** — 8.6x for 9x the pixels, so it is purely per-pixel work. At the
   phone's 3x that is half a second of main-thread time per page turn from one
   field.
3. **The panel field does NOT rebuild twice per page as a rule.** Measured: 9
   builds across 7 rendered pages, 1.3x per page. The present coalescing
   (`kPresentHoldMs`) usually suppresses the 1-bit pass's present, so the
   second build happens only when a frame escapes the hold — and when it does,
   the page turn costs about double. That is exactly where the 148 ms outlier
   at 1x and the 727 ms one at 3x come from. The structural win named below is
   therefore worth ~490 ms on roughly a third of page turns rather than half of
   every one.
4. **The sheet field is render-scale independent**, ~30 ms at both scales,
   because it is generated at OUTPUT size — and it rebuilds exactly once per
   page, which is the page-identity keying working as designed. The scanline
   field is the same shape (35.8 → 38.6 ms).
5. **A still page really is free**: 0.4 ms at 1x, 2.4–2.9 ms at 3x with every
   field served from cache. The 3x idle cost is not a field at all; it is the
   ~15 MB panel texture upload.
6. **So the cost of a new pass is decided by which space it lives in.** At 3x,
   a new PANEL-space field is in the ~490 ms class and a new OUTPUT-space field
   is in the ~30 ms class. Show-through (§1a) is specified as a fold into the
   *sheet* field, which puts it in the cheap class — the question this
   measurement existed to answer, answered: **show-through is affordable, and
   the letterpress panel field is the thing that is not.**

Caveat, stated rather than buried: this is a Mac, not a phone. The phone's CPU
is slower, so the 3x column is a lower bound for the device it describes.

One cheap structural win regardless: the panel field rebuilding **twice** on
the page turns where a frame escapes the present hold is a consequence of
`pixelBufSeq` incrementing on both passes — the paper-defects work already
recorded this as a negative result and routed the *sheet* field around it via
the page identity. The *panel* field still pays it, and at 3x that is 490 ms
of duplicated work on about a third of page turns.

### 4d. Is there a third mode wanted?

The doctrine is two worlds: paper and CRT. Three candidates for a third, ranked.

**E-ink paper-white — YES, and it is the strongest idea in this document.**
The thing being simulated *is an e-ink reader*. That is the whole premise of the
repo, and it is the one surface with a genuine claim to be here that neither
current mode covers: light mode is a *printed page* (letterpress, ink squash,
paper defects) and an e-ink panel is emphatically not that. A real Carta panel
has its own unmistakable signature, and every element of it is within the
existing machinery:

| E-ink property | How the existing model covers it |
|---|---|
| Four (or sixteen) gray levels, hard-quantized | Already true — the framebuffer is 1bpp + AA planes; the *dither* is already there |
| A slightly warm, slightly gray-green paper-white with low reflectance — never `#FFFFFF` | A paper row (a cool, low-luminance one) |
| Bayer dither visible as texture at 1:1 | Already visible; CLAUDE.md's ST-008 note documents it in detail |
| **Ghosting** — the previous image faintly retained until a full refresh | `ghostPixels` already holds it, and the trail machinery already composites a decaying previous frame. This is the *same code path as the phosphor trail*, with a different decay: e-ink ghosting does not decay, it persists until a full refresh. |
| **The refresh flash** — a full inversion before settling | `CROSSPOINT_SIM_PRESENT_FLASH` is the seed of it |
| No emission at all; ambient-lit | `setPanelEmissive(false)` already exists (`src/SimulatorOverlay.h:161`) |

So an e-ink mode is mostly *re-wiring existing passes with different constants*,
plus one genuinely new thing (the refresh waveform). It would also be the only
mode that is a picture of the actual device rather than a fiction. **This is my
top third-mode pick by a wide margin.**

**Teletext — no.** Teletext is a 40x25 character grid with a fixed bitmap face
and block graphics. Applying it to a proportional reflowable page means either
re-typesetting the book into 40 columns (a firmware change of enormous scope, on
a device whose whole value is font quality) or drawing a teletext-looking
*palette* over normal type, which is a costume rather than an emulation. It also
has no reading argument: teletext type is famously hard to read at length.

**Thermal receipt — no, and it is worse than teletext.** A thermal receipt is
low-resolution, low-contrast, fading dot-matrix on a curled, shiny 55 gsm strip.
Every one of those is a *legibility deficit*, deliberately reproduced, in a
reading app. The one interesting sub-idea — thermal paper's characteristic
*fade*, where old receipts go blank — is directly opposed to the 7:1 floor this
repo enforces everywhere. If the fascination is the look of a dot-matrix
impact-printer page, that is a *font* question, not a surface one.

**One more that was not on the list and should be considered: microfilm /
microfiche reader.** Negative or positive, a projected image with a hot-spot
vignette from the lamp, dust on the platen, and slight focus falloff. It is a
real reading surface with a real archive romance, it is a *third* physics
(projection, not print and not emission), and — unlike teletext — it needs no
change to typesetting. Cost is genuinely low: a vignette (exists), grain
(exists), and a defect layer (exists). I would rank it second behind e-ink.



## Standing rulings, 2026-08-23

Recorded here because a decision that lives only in a transcript gets
re-proposed by the next session.

- **Font compression STAYS ON.** The device-side question -- fewer SD bytes to
  read against inflate cost on a 160 MHz core -- is still unmeasured, and the
  ruling is to keep the 70% install cut while it stays that way. Turning it off
  is one build flag.
- **The laid-paper wires STAY**, despite meeting the words of the
  no-long-straight-lines ruling that deleted the crease and clipping-burn
  defects. They are the Laid Antique stock's defining structure rather than
  something that happens TO a page, and they render only when that stock is
  chosen.
- **The measure overrides a book's own CSS alignment**, and the reader is told
  so: the Select Chapter screen carries a verbose notice naming every
  book-specific decision the firmware has made. The general form of that ruling
  is the part to remember -- when the app silently works around something in a
  book, say so somewhere the reader can find it.
- **The whole queue below is approved**, as iOS settings where taste genuinely
  varies and frozen where one value is obviously right. Note the context: the
  same day removed nine Settings.app rows, so a new row has to earn itself.
- **The named presets stay reachable, from inside the drawers.** "Add a Presets
  row back to the pickers." Removing the Settings.app palette row left the claim
  protocol as the only writer of `panelPalettePreset`, and it can only point at
  Custom — so one ink pick retired all 52 names. The answer is a Presets bar
  button in BOTH page-color drawers opening ONE shared list
  (`ios/CrossPointPresetList.mm`), not a returning Settings.app row: the drawer
  is where page color is chosen now, and the page behind an undimmed sheet is
  the preview a Settings row cannot be.
  Selecting one is `panelsource::releaseCustom`, the exact inverse of the claim,
  and it CLEARS `phosphorMixActive` and `panelDarkSnapshotPreset` rather than
  leaving them; see docs/phosphor-mixer.md for why the stale mix flag is the
  dangerous half.
- **Each list offers only its OWN page's presets**, which SUPERSEDES the sentence
  that stood in the bullet above for about four hours the same day ("both lists
  offer every preset ... filtering either would remove a choice that used to be
  offered"). Owner: *"only show presets available in that mode."* The dark-mode
  mixer offers the 42 phosphors, the light-mode ink picker the 10 papers, and the
  partition is `panelpalette::presetOfferedInDark` = `trailMsForPreset > 0` -- a
  preset with a decay IS a tube -- so it restates the 2026-08-22 doctrine instead
  of adding a second source of truth. It filters the OFFERING and never the
  definition: choosing Green CRT in the mixer still sets the light page. The test
  pins the partition as TOTAL and non-empty on both sides, because a preset
  offered by neither list would be unreachable -- which is exactly how the presets
  were lost before this list existed. Homes: `docs/phosphor-mixer.md`,
  `docs/light-ink-picker.md`.
- **Corner defocus ships OFF (0), and the reason is a lesson about proof.** It
  was shipped as a Settings row so the owner could judge it on glass; he looked
  and reported "nothing is being rendered in any corners", which is the correct
  observation and not a missed one. The field it modulates is the scanline field,
  and at the shipped 2 px pitch that field is 5 code values deep at the centre and
  0 at the corner -- the box-integrated structure self-attenuates to nearly flat
  when a scan line is two device pixels tall. The 41% corner-versus-centre figure
  `docs/corner-defocus.md` quoted throughout was 41% of a quantity that is itself
  5/255: a ratio reported without checking the magnitude of what it was a ratio
  OF, when the honest whole-frame figure of one code value was available from the
  start. The model, its host test and its doc all stand, so re-enabling is one
  number, and returning 0 gives back ~42 ms per dark page turn. Full writeup:
  `docs/corner-defocus.md`.
- **Render scale is FROZEN at 2 and is no longer a preference.** 1 retired
  2026-08-21, 3 retired 2026-08-23 ("drop 3x support for now"), and a one-value
  control is worse than no control -- so the Sharpness row left Settings.app with
  the rest. `CrossPointPrefs_renderScale()` returns 2 WITHOUT reading
  NSUserDefaults, because most installs stored a 3 and must not keep re-pointing
  something the owner can no longer see or change. Re-enabling 3x is one number in
  `ios/CMakeLists.txt`; the tier machinery, the seed trees and
  `build-sd-fonts.py --scale 3` were never removed. Home:
  `docs/ios-render-scale.md`.
- **The Speak Screen underline is CLOSED -- it is iOS's own, and it is kept.**
  Owner: *"consider it resolved."* No code changed for it and none should. The
  next report of an underline under spoken text starts at Accessibility > Spoken
  Content > Highlight Content, not at our selection rects, which were measured and
  are correct. Home: `docs/speak-screen-chain.md`.


## 5. The whole list, ranked

Value is what it buys the page. Cost is engineering effort including the test
this repo would demand. Risk is the chance it makes something worse — mostly
legibility, and mostly through resampling.

| # | Item | § | Value | Cost | Risk |
|---|---|---|---|---|---|
| 1 | ~~Show-through from the verso~~ **SHIPPED 2026-08-23** | 1a | **high** | med-low | low |
| 2 | Faceplate diffusion (the glass, not the beam) | D1 | **high** | med | med-high |
| 3 | ~~Sheet-to-sheet color drift~~ **SHIPPED 2026-08-22** | 1c | med-high | **trivial** | low |
| 4 | ~~Present-path timing instrumentation~~ **SHIPPED 2026-08-22** | 4c | (enabling) | **trivial** | none |
| 5 | ~~Corner defocus as ellipticity, sigma(r)=sigma0(1+kr^2)~~ **SHIPPED 2026-08-23** | D3 | med | ~~trivial~~ med (a second table axis; +10-24 ms) | low |
| 6 | Accessibility labels on the drawer | 4b | med | **trivial** | none |
| 7 | HV sag, 0.5-2%, **transient only** | D4 | med-high | low | med (see the condition) |
| 8 | Ink spread / dot gain per stock | 1b | med | low | med |
| 9 | Left-edge optical margins | T3 | med | low-med | low |
| 10 | E-ink as a third mode | 4d | **high** | high | med |
| 11 | Justification stretch limit | T2 | med-high | med | med |
| 12 | Video-amp horizontal asymmetry, sub-pixel | D5 | med | low | med (fatiguing if visible) |
| 13 | ~~Power-off collapsing dot at sleep~~ **SHIPPED 2026-08-23** | D8 | low (delight) | low | none |
| 14 | Corner luminance falloff, 15% (vignette only) | D2 | med-low | **trivial** | none |
| 15 | Total-fit breaker with hyphen demerits | T1 | **high** | **high** | high |
| 16 | Laid chain lines + watermark | 1f | med-low | low-med | med (regular field → ST-008) |
| 17 | Microfilm as a third mode | 4d | med | med | low |
| 18 | Burn-in, opt-in "vintage" only | D6 | low | med | low (high as a default) |
| 19 | Deckle edges | 1d | low | med-high | **high** (panel rect) |
| 20 | Increase Contrast / Reduce Motion support | 4b | low-med | low | low |
| 21 | Teletext mode | 4d | very low | high | high |
| 22 | Thermal receipt mode | 4d | very low | med | **high** |
| 23 | CRT geometry WARP / curvature | D2 | negative | med | **very high** |
| 24 | Gutter shadow / page curl | 1e | negative | med | high |
| 25 | Room reflection on the faceplate | D7 | negative | med | med |
| — | Convergence, shadow mask, interlace, degauss swirl, mask moire, retrace lines | 3 | **n/a** | — | wrong fiction; see the tables |

Two entries moved after the sources came in, and both moves are worth naming:
**D1 was called "halation" and is really diffusion** (TG18 §4.7.1 names glass
scattering the dominant contributor in a monochrome tube, and halation proper is
a ring displaced by the glass thickness — a different and lesser effect); and
**D4 (HV sag) was in the "never build" list and came out of it** when the real
magnitude turned out to be 0.5–2% rather than the 20% the shader dials offer,
and when it became clear the effect is exactly zero on a static page.

## 6. Do these three next

**1. ~~Show-through from the other side of the leaf (§1a).~~ SHIPPED
2026-08-23** — see §1a for what the build changed against this design and for
the measurements. The biggest single
thing a printed page does that this one does not, and the only paper phenomenon
that carries *information* rather than texture. `ghostPixels` already holds a
whole previous framebuffer, the sheet field already takes darken-only
multipliers, and the per-stock opacity it needs is a natural sibling of the
`tooth` field that exists. Ship it with the previous page and be honest in the
doc; nobody can read a show-through. It also gives India paper — the new row
whose entire identity is thinness — something to be.

**2. Faceplate diffusion (D1).** The dark page has bloom, which is electron
optics, and no glass at all. That is why it reads as a sharp raster rather than
as a lit tube behind a thick window, and it is the one dark-mode item where the
*absence* is what you notice. It costs a real argument, because it is the first
pass that would brighten and the darken-only invariant has to be carved
deliberately rather than quietly broken — and having that argument on the record
is worth something either way. Ship a small fraction of the physical magnitude
and say so: real monochrome tubes measure a glare ratio of 89–138 against
TG18's minimum acceptable 400, so the authentic setting is worse than any
setting a reading app should offer.

**3. ~~Sheet-to-sheet color drift (§1c).~~ SHIPPED 2026-08-22.** Cheapest thing
on the list by a wide margin, and it removes the single most machine-like
remaining property of the light page: every leaf being byte-identical in tone.
Built as described, with the two corrections recorded in §1c: the offset rides
`livePanelPalette` rather than the iOS-only resolver, and the drift dial is
threaded through the two existing 7:1 clamps rather than checked beside them.

**~~Before all three: instrument the present path (§4c).~~ SHIPPED
2026-08-22**, as `CROSSPOINT_SIM_LOG_TIMING=1`, with the measured table in
§4c. The headline for the two items still open above it: at the phone's 3x, a
new OUTPUT-space field costs ~30 ms per page turn and a new PANEL-space field
costs ~490 ms. Show-through (§1a) folds into the sheet field, so it is in the
cheap class. The readback this section ranked as the top cost is 2–6% of a page
turn and can be forgotten.

**Two honorable mentions that cost almost nothing.** Corner defocus (D3) is
roughly a two-line change to a model that already computes a per-pixel sigma,
and applying it as *ellipticity* rather than isotropic blur is the difference
between "character" and "the edge text is worse". And the accessibility labels
(§4b) are perhaps forty lines: with seventeen ink rows now, VoiceOver announces
seventeen unlabeled buttons and eight anonymous percentages.

## 7. Do not build these two

**1. CRT geometry warp / screen curvature (D2).** Every shader emulator does it,
and it would be actively harmful here. A warp is a resample, and this repo has a
*measured* ruling on what resampling does to its own page — ST-008, 8.14 levels
of beat on a Bayer-dithered fill under the phone's 0.7955 minification. The
general shader corpus never faces a 1-bit dithered source at a fractional
presentation scale; this app always does. A curvature pass reintroduces that
hazard deliberately, on every page, forever, and bows the baselines while doing
it. **I am overruling the research here and recording that I am**: its verdict
was "keep very small, with a physical model rather than a cheap warp", and that
would be right for an emulator whose source is not dithered. The representable
half — **corner luminance falloff, up to 15% for a monochrome faceplate at 34%
transmittance (TG18 §2.4.12)** — is real, free, and already available as the
grain's Vignette coverage. Take that; leave the warp.

**2. The gutter shadow and page curvature at the spine (§1e).** This is a
**one-page** device. There is no facing page, no binding and no gutter — the
firmware adds a single symmetric margin to all four edges and deliberately has
no inner/outer distinction, because there is no recto and verso
(`crosspoint-reader/src/activities/reader/EpubReaderActivity.cpp:1005-1009`). A
gutter shadow on an unbound single page is a picture of a book rather than a
page: it is 2010-era iBooks skeuomorphism, and it is the clearest example on
this list of the fetishism the question asked me to separate out.

Three runners-up, for completeness. The **room reflection** (D7): the phone's
own glass already reflects the actual room, correctly and for free, and every
shader that synthesizes one uses a static gradient that does not move with the
viewer — which is the entire physical point. **Teletext and thermal-receipt
modes** (§4d): both are deliberate legibility deficits in a reading app, and
teletext additionally requires re-typesetting the book into 40 fixed columns on
a device whose whole value is font quality. And **burn-in as a default** (D6):
a persistent second image is a distractor by construction, however good the
physics.

## 8. The one thing to consider that was not asked about

Everything above is a *pass*. The system has eleven of them now, each with its
own dial, and they are composited in a fixed order with three separate budget
mechanisms (`letterpress::paperBudget`, `phosphorgrain::darkeningBudget`, and
`paperdefects`' derived `remaining`). The budgets are correct — the paper-defects
work in particular proved its bound analytically rather than asserting it — but
**there is no single place that says what the composite is**, and the next pass
added will be the one that gets the composition wrong.

The cheap insurance is a **composition test**: one host test that walks every
dial to its maximum simultaneously, for every palette, and asserts the final
7:1. Each pass tests its own floor today; nothing tests all of them at once,
and "individually safe and jointly over" is the exact failure the defect layer
had to be rescued from once already. That test costs an afternoon and it is the
thing that makes items 1, 2 and 3 above safe to add.

