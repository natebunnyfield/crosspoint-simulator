# Letterpress (light) and scanlines (dark)

Added 2026-08-22, owner order (verbatim): *"implement a variable letterpress
effect for light mode, as from here on out light mode will be paper and ink
emulation with letterpress experience, and dark mode will be crt emulation with
phosphors and mixed guns and fade persistence. replace mottled noise in dark
mode with hyperrealistic scanlines (variable and with variable mottled noise,
needs a lot of work and research and consideration)."*

Models: [`src/Letterpress.h`](../src/Letterpress.h) and
[`src/Scanlines.h`](../src/Scanlines.h), both pure and host-tested
(`tests/letterpress_test.cpp`, `tests/scanlines_test.cpp`). Composited in
`HalDisplay::presentIfNeeded`.

## THE DOCTRINE (standing model, 2026-08-22)

- **LIGHT MODE is paper and ink.** The page is pigment pressed into paper:
  letterpress emulation. No phosphor treatments apply.
- **DARK MODE is a CRT.** Phosphor palettes, gun mixes, fade persistence (all
  already shipped) — and now **scanlines** as the screen's spatial texture,
  replacing the mottled grain.

### The reversal this supersedes

[`docs/phosphor-grain.md`](phosphor-grain.md) carries the 2026-08-18 ruling
that **rejected** scanlines: *"a raster artifact, not a phosphor one (a vector
scope and a radar PPI have grain and no scanlines at all)"*, plus the ST-008
moire objection. **The owner's 2026-08-22 order supersedes that ruling for
dark mode.** The technical half of the old objection was correct and is
answered rather than ignored: the dark page is now declared a RASTER display
(the fiction is a monochrome raster monitor, not a scope), so line structure is
honest; and the moire hazard is engineered out by generating the line field at
OUTPUT size from a box-integrated continuous profile (below), never by
resampling a regular grid. The grain machinery is not deleted — it stays
compiled and env-reachable for A/B (turn the new dial off and set
`CROSSPOINT_SIM_GRAIN`).

## Research: what the eye actually sees in letterpress

No web-search tool was available in the implementing session; the following is
domain knowledge, labeled by confidence. None of it is measured off a press
here.

1. **Ink squeeze / squash ring** (high confidence — the printer's own term is
   "ink squash"; it is what distinguishes letterpress from offset at a glance).
   The press forces ink outward from under the face of the type, so ink pools
   at the stroke's *perimeter*: a darker rim around every glyph edge, with the
   stroke's center fractionally lighter. Digital-era "letterpress style"
   presses deliberately over-impress to exaggerate it.
2. **Deboss / impression** (high confidence). The type deforms the paper; under
   raking light the depression shows a shadowed wall on the side toward the
   light and a lit wall opposite. On screen that is a subtle edge-locked
   light/dark bias with a fixed light direction (top-left, the near-universal
   UI convention).
3. **Plate pressure / makeready variation** (medium-high). Impression is never
   perfectly even across a forme; poorly made-ready areas print lighter, heavy
   areas darker — a low-frequency field over the page, affecting the ink only.
4. **Ink coverage irregularity within strokes** (high). Solid ink on toothy
   paper is never flat: high-frequency, low-amplitude density variation inside
   the printed area.
5. **Paper tooth** (high). Unprinted paper has its own fine texture; laid or
   toothy sheets show it plainly.

### Which of these read at THIS app's scales

The page is supersampled 3x and presented at ~0.72–1.0 on the phone; a body
glyph stroke is ~4–8 device pixels wide.

| Component | Verdict | Why |
|---|---|---|
| Squeeze ring | **YES — the lead effect** | An edge-locked 1-device-pixel rim on a 4–8 px stroke is exactly resolvable; it is the letterpress signature. |
| Deboss shadow | **YES, shadow half only** | One edge-adjacent darkened line of paper reads at these scales. The HIGHLIGHT half is unrepresentable: the pass is darken-only (an additive lift is the page-flash bug class), and near-white paper has almost no headroom anyway. Shadow-only is what a deboss looks like under soft frontal light, so it stays honest. |
| Pressure field | **YES, faint** | Low-frequency; survives any scale by construction. Ink-only (light pressure = lighter ink is a *brightening*, unrepresentable, so the field is expressed as heavy-pressure areas darkening — half the phenomenon, the representable half). |
| In-stroke irregularity | **YES, very faint** | At 0.72 minification per-pixel noise partially averages out; kept at low amplitude as "the ink is not a fill". |
| Paper tooth | **YES, very faint** | Aperiodic noise, so it cannot ST-008-beat (that moire needs a *regular* lattice against a sampling lattice). Kept an order below the ring. |

### The letterpress dial: ONE ladder, everything scales together

Ring intensity, deboss depth, plate pressure and in-stroke irregularity scale
linearly on **one** dial; the paper's tooth rides its square root.
Justification: ring and deboss are the *same physical variable* — packing
pressure. A pressman adding packing gets more squash and a deeper bite
simultaneously; offering them separately would be two rows for one knob (and
the reduced-settings ruling allows exactly one row). Tooth is a property of
the paper, not the pressure, so it rides sub-linearly — a hard press does not
make the paper toothier.

Rungs (stored as the meaningful percent, house rule): **Off (0)** — bit-exact
off — **Subtle (50)**, **Standard (100)**, **Heavy (200)**. Default **Subtle**
in light mode (the doctrine makes it the mode's identity; subtle because it is
a reading page, not a poster). Precisely: ring, deboss, plate pressure and
in-stroke irregularity scale linearly with the dial; the paper's tooth rides
the square root of it, because a harder press does not make the paper toothier.
Measured on the shipped page at Heavy (Default palette, 2x): edge band −32.5
levels, flat ink −3.0, flat paper −5.9 — the effect is edge-locked, as the
test also pins on a synthetic glyph.

### Where it operates: PANEL space, present time, framebuffer edges

Letterpress is **edge-aware**: it acts where ink meets paper. Two candidate
homes were weighed:

- **Glyph compose** (firmware render path): rejected. It would touch shared
  firmware-visible code for a host-only effect, break the "canary renders what
  it always did" guarantee at the pixel source, and be invisible to a pure
  host test.
- **Present-time screen-space pass off the framebuffer's own luminance
  gradient**: chosen. `pixelBuf` (the palette-applied ARGB frame) already
  holds every edge; a 3x3 luminance window classifies edge band, ink side,
  paper side, and light-direction bias, cheaply and purely.

Unlike the grain, letterpress is drawn in **panel space** (a MOD texture at
framebuffer size, drawn through the same rotation/dst as the panel itself),
not at output size:

- It is a property of the **page**, not the glass. Ink squash on the bezel or
  the button pad would be wrong the way a grainy bezel was wrong in reverse.
- The ST-008 constraint does not bind: the field is edge-locked and aperiodic
  — there is no regular lattice to beat against the fractional presentation.
  It scales with the glyphs exactly as the glyphs do.
- Regenerated only when `pixelBufSeq` changes (a page turn), so a still page
  costs nothing.

Two accepted approximations, recorded: during a beam sweep the band still
showing the OLD frame briefly carries the NEW frame's ring (≤ the sweep
duration, ≤300 ms); and under a deep page fade the ring does not fade with the
page (MOD after alpha), so a nearly-faded page keeps faint edge ghosts. Both
are dark-mode-flavored dials unlikely to be combined with letterpress, and
neither can brighten anything.

## Research: hyperrealistic scanlines

Same confidence labeling as above.

1. **A raster line is the beam's spot dragged horizontally** (high). The spot's
   vertical profile is close to Gaussian; a scan line is bright at its center
   and falls off smoothly. The visible darkness between lines depends on spot
   size relative to line pitch.
2. **Bright content blooms** (high — this is the standard meaning of CRT
   "blooming"). Spot diameter grows with beam current: bright pixels *widen*
   the lit portion of their line, thinning the visible gap. This is the
   hyperrealism most fakes skip — a real tube's line structure is content-
   dependent, nearly closing up in bright areas and opening in dim ones.
3. **Slight phase/thickness irregularity** (medium-high). Scan geometry and
   focus are not perfect; individual lines sit fractionally off pitch and vary
   slightly in thickness, which is part of why real tubes do not read as a
   silkscreen overlay.
4. **The screen's coating unevenness still exists** (high — it is the same
   physics the grain modeled). The owner's "variable mottled noise" is
   implemented as the existing low-frequency mottle field modulating the
   **line depth** — the structure gets blotchy — not as a separate speckle
   layered on top.

### The honest pitch: one scan line per SOURCE row

Decision: the line pitch is tied to the **source raster** — one scan line per
logical page row (792 rows for the X3 portrait page; the current orientation's
logical height in general). In device pixels the pitch is exactly the panel's
presentation scale (~2.39 px on an iPhone at 3x·0.7955; 2.0 on the 2x Mac app;
1.0 at 1:1 desktop, where the structure correctly self-attenuates toward a
uniform dimming — which is also what a real tube looks like once you cannot
resolve its lines).

The alternative — emulating a fixed ~500-line tube and mapping those lines
onto the panel — was rejected because it *introduces* a second lattice: 500
tube lines against 792 content rows beat at their difference frequency, the
ST-008 failure class by construction. One-line-per-row is also historically
honest: high-resolution monochrome page displays existed and are the right
fiction for a portrait text page (the Macintosh Portrait Display was a 640×870
monochrome raster CRT; medium-high confidence on the exact figures).

### Why the field cannot moire (the ST-008 lesson, applied)

The field is generated at **OUTPUT size** and drawn 1:1, like the grain — but
that alone is not enough for a *periodic* pattern whose period is a
non-integer number of device pixels. Point-sampling a 2.39 px comb at pixel
centers aliases within the field itself. So each device-pixel row takes the
**box integral** of the continuous line profile over that pixel's extent
(a `std::erf` pair per nearby line), which is exact sampling: per-period energy
is stable to the integrator's tolerance, and there is no long-period beat.
`tests/scanlines_test.cpp` pins this: per-period mean transmission at the
fractional pitch varies under 1.5% across the panel height.

### The scanlines dial: intensity ladder with mottle folded in

One row (the reduced-settings ruling). Stored as the meaningful percent.
The mottle depth is **folded into the ladder** — `scanlines::mottleDepthFor
(percent)`, monotone in the dial — because the owner's "variable mottled
noise" varies *with* how visible the structure is: blotchiness of a structure
you can barely see is noise, and a deep structure with no unevenness is a
silkscreen. Folding keeps one integer round-tripping through Settings.app.

Rungs: **Off (0)** — bit-exact — **Subtle (50)** depth 0.20 / mottle 0.15,
**Standard (100)** depth 0.40 / mottle 0.30, **Deep (150)** depth 0.55 /
mottle 0.40. Default **Subtle** in dark mode.

### The inherited constraints, all honored

Same architecture as the grain (`docs/phosphor-grain.md`):

- **Present-time pass, device pixels, drawn last over the whole app surface**
  (one raster covers the glass; the pad and bezel sit under the same beam).
  Bloom is computed from the composed backbuffer (`SDL_RenderReadPixels` at
  regeneration time), so it sees the true light — palette, fade, accumulator
  and all; outside the panel the level is whatever the chrome actually is.
- **MOD blend, darken-only.** Transmission is normalized so a line's crest is
  at or near untouched (exactly untouched when a crest lands on a pixel row's
  center; when the fractional pitch straddles rows, the crest rows carry the
  small residual a real raster's do) and the gap darkens. Nothing can brighten
  — bloom works by darkening the gap LESS near bright content, never by
  lifting anything.
- **OFF is bit-exact off**, per mode, asserted in the tests.
- **Contrast floor**: the page's `phosphorgrain::darkeningBudget` (7:1 floor)
  caps the effective line depth, structurally — the same hard-ceiling shape
  the grain uses, swept in the test over the five palettes including the two
  tightest (P11 Blue 7.4:1, P22R).
- **Regenerated per app start** (seed shares the grain's per-launch roll and
  its `CROSSPOINT_SIM_GRAIN_SEED` pin), never per frame — a still page must
  not crawl. Content-triggered regeneration (for bloom) keys off
  `pixelBufSeq`, i.e. page turns, not frames.

## What replaced what (the resolved design)

| Mode | Before | Now |
|---|---|---|
| Light | phosphor grain (desktop seeded 1x Even; iOS 60%) | **letterpress**; grain pass **skipped whenever letterpress > 0** |
| Dark | phosphor grain incl. mottle (iOS 160%) | **scanlines** (mottle folded in); grain pass **skipped whenever scanlines > 0** |

The grain machinery stays compiled, its dials and env vars intact, for two
reasons: any mode whose new dial is OFF falls back to exactly the old grain
behavior (which is what keeps the desktop canary byte-identical, since the
desktop seeds both new dials OFF), and A/B against the old look is one env var
(`CROSSPOINT_SIM_SCANLINES=0 CROSSPOINT_SIM_GRAIN=100 ...`).

## Settings

Two rows, appended to the surviving Page Colors group (a preset persists as an
integer; rows append, never insert):

| Row | Key | Stored | Default |
|---|---|---|---|
| Letterpress | `letterpressPercent` | percent, 0/50/100/200 | 50 (Subtle) |
| Scanlines | `scanlinesPercent` | percent, 0/50/100/150 | 50 (Subtle) |

Both read through `-objectForKey:` (0 is a real choice, the
`-integerForKey:` missing-key trap). Desktop mirrors:
`CROSSPOINT_SIM_LETTERPRESS` / `CROSSPOINT_SIM_SCANLINES` (percent), seeded
through `SimulatorOverlay::setLetterpress` / `setScanlines` at init (ninth and
tenth dials to need that seed), plus the same keys in the desktop
`settings.json`. The desktop seeds both **0**: dials off = byte-identical
canary, proven by before/after capture md5.
