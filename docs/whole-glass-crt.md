# One sheet of glass: persistence and the beam stop being panel-only

2026-08-26. Measured on this machine against `68c73fb`, X3, SDL's **software**
renderer, dark page, `CROSSPOINT_SIM_AS_SHIPPED=1`,
`CROSSPOINT_SIM_GRAIN_SEED=7`, card reseeded per run, `settings.json` parked.
Render scale 2 for every timing and trail figure; render scale 1 (the default
build) for the still-page gate, because that is what its published hashes are
from. Nothing below is inferred from source unless it says so.

The owner's ruling that framed the work, verbatim:

> *"apply persistence and other crt effects equally to paper and panel"*

It is the 2026-08-18 grain ruling restated. That one said the screen is **one
sheet of glass** and that texturing only the page left a grainy rectangle on a
clean ground, which no physical screen has. The same sentence applies word for
word to a phosphor: a tube's whole face is coated, and there is no arrangement
in which the page glows and the surround beside it does not.

---

## 1. Where each CRT effect actually drew, before this

Established by reading each draw site and confirming by measurement, not by
assuming the table in the brief was complete. "Panel space" means the pass is
drawn through `drawPanel()` — rotated with the orientation, scaled by the
panel's own dst rect, so it can only ever cover the page's rectangle. "Output
space" means it is drawn 1:1 in device pixels with logical presentation
disabled, so it covers the page, the surround, the button pad and the reserved
bands alike.

| Effect | Space, before | Space, after | Where |
|---|---|---|---|
| Phosphor persistence (the accumulator) | **panel** | **output** | `HalDisplay.cpp`, the accumulator block |
| Beam paint (the sweep) | **panel** | **output** | `HalDisplay.cpp`, `beamSweeping` |
| Page fade | panel | panel (unchanged) | `HalDisplay.cpp`, `pageAlpha` on the panel texture |
| Letterpress ring/deboss | panel | panel (unchanged) | `SurfaceSheet.cpp`, `letterpressField()` |
| Scanlines (+ the bloom) | output | output | `SurfaceTube.cpp`, `ensureScanlinesField(outW, outH)` |
| Corner defocus | output (folded into the scanline field) | output | `CornerDefocus.h` |
| The sheet — tooth, formation, laid, show-through, marks | output | output | `SurfaceSheet.cpp`, `ensureSheetField(outW, outH)` |
| Phosphor grain | output | output | `SurfaceTube.cpp`, `ensureGrainField(outW, outH)` |
| Power-off collapse, BZZT THONK warm-up | output already | output | `SurfacePower.cpp` — both paint the surround explicitly (`around[4]`) |

So the brief's table was right about persistence and right to suspect the beam,
and the enumeration turned up nothing else: every other CRT-side pass was
already whole-glass, and the two that are still panel-space are the two that are
**properties of the page rather than of the screen**. The page fade is the
paper's own legibility dial. The letterpress is ink squashed into a sheet; its
whole-glass half (the tooth, over the card and the pad) has been a separate
output-space pass since 2026-08-22 precisely so the paper texture cannot seam at
the page's edge.

Two notes about the light half, since "paper" is in the ruling: the light page's
sheet fields already cover the whole glass, and persistence is dark-only by
construction (`accumLive` requires `panelIsDarkGround()`; adding light to white
paper draws grey, which is the build-90 bug the code still carries a paragraph
about). So the light page needed nothing and got nothing.

## 2. What now glows out there, and what does not

The panel-space accumulator deposited the page's own pixels. In output space
the surround and the pad are *painted colour* rather than emitted content, so
"what glows" had to be decided rather than inherited. **The deposit is the
composed glass** — the whole frame as it stood, page, letterpress, pad, surround
and reserved bands — captured once per new picture, before the accumulator
itself is drawn over it.

Three consequences, in the order they matter:

1. **The ghost stays where the light was emitted.** A panel-space accumulator
   was drawn through the CURRENT panel rect, so when the page moved — zen mode
   placing the panel within the sheet, a keyboard coming up and relayouting it —
   the ghost of the old page teleported and rescaled to the new position with
   it. Measured proof in §5: with the page refitted 60 ms into a trail, the old
   page's light now lingers in the newly-exposed surround and decays there,
   where before that region went flat black on the frame the page left it.
2. **The pad and the surround leave afterglow when they change.** A pressed
   button's highlight decays like everything else on the face.
3. **A static surround costs nothing on the shipped page, and NOT on every
   palette.** This is where an earlier draft of this document was wrong, and the
   correction is worth more than the claim was. Under MAXIMUM the deposit is
   `max(r,g,b)` and the composite multiplies by the ink, so a paper pixel comes
   back as `max(paper) × ink[c]/255`. That is `≤ paper[c]` only when the paper
   lies on the ink's hue ray. **Where it does not, the trail LIFTS the ground**,
   per channel, and the lift is not small. Computed over all 52 presets as they
   are defined in `src/PanelPalette.h`:

   | preset | dark paper | worst channel lift | trail |
   |---|---|---|---|
   | Cascade | `#000327` | **+29 R, +27 G** | 2828 ms |
   | Blue TV | `#000027` | +26 R, +26 G | 283 ms |
   | Red Projector | `#270100` | +24 G, +25 B | 283 ms |
   | Blue Fast | `#030527` | +23 R, +22 G | 20 ms |
   | Solarized | `#002B36` | +27 R | 0 ms (no trail) |
   | Blue | `#00061A` | +14 R, +8 G | 126 ms |
   | Green | `#001A00` | +5 R, +5 B | 400 ms |
   | **as shipped** | `#171B1B` | **−2, −5, −6 (none)** | 1095 ms |

   42 of the 52 lift by at least one code value; the worst is 29. **The page the
   app actually ships is not one of them** — every channel of `CFD4CC` on
   `171B1B` comes back below the paper, so what the owner sees by default is
   unaffected.

   **This is not new and it is not caused by this work**: the same deposit has
   always been composited over the page's own background, so on those presets a
   dark page turn has always washed the page. What this change does is spread it
   from the page's rectangle to the whole face. Which of those is worse is a
   genuine question — a uniform wash has no seam in it, and a rectangle-shaped
   one does.

   **The underlying model error, and the fix, costed but NOT shipped.**
   Unexcited phosphor emits nothing, so the paper tone is the tube's dark state
   and not light: depositing it as light is wrong at the root. The fix is one
   line in `captureGlass` — deposit the EXCITATION,
   `clamp((max(r,g,b) − max(paper)) / (max(ink) − max(paper)), 0, 1) × 255`,
   instead of the absolute intensity. A paper pixel then deposits 0 and the lift
   disappears on every preset; an ink pixel deposits 255 and the composite's mod
   returns exactly the ink, which also makes the trail's peak the ink itself
   rather than today's `max(ink) × ink/255` (0.878× on the shipped pair). It is
   left as a proposal because it changes how the trail LOOKS on every preset,
   including the shipped one, and the owner tuned that effect by eye.

   **On a renderer that has no MAXIMUM none of the above holds anyway** — see
   §6, which is a finding in its own right.

### The road not taken

The alternative was to keep the deposit as the PAGE's own ink, merely
re-rendered at output resolution — which is enhancement item 3 of
`trail-cost-2026-08-26.md` on its own, pure GPU, no readback, and strictly
cheaper than what shipped.

**It was rejected because it is invisible.** An output-space accumulator fed
only by the page covers exactly the same pixels the panel-space one did; the
surround still never glows, the pad still never glows, and the only thing that
changes is the trail's own resampling. It would have satisfied the enhancement
list and not the ruling. What it would look like: exactly what shipped, minus
§5's ghost — the page's afterglow vanishing the instant the page moves, and a
button pad that stays dead under a glowing page.

The second alternative, re-rendering the composition into the accumulator
instead of reading it back, cannot reach the pad at all: the overlay hook paints
colour straight onto the output and there is no intensity form of it to draw.

## 3. How the capture works, and the three rules that make it safe

`captureGlass()` in `HalDisplay.cpp`. One `SDL_RenderReadPixels` of the whole
output, one CPU pass to `max(r,g,b)`, two uploads — into `glassPrevTexture`
(colour, for the beam's old picture) and `glassIntensityTexture` (the phosphor
deposit).

1. **Taken before the accumulator is drawn.** A capture that included the trail
   would deposit the trail back into itself and nothing would ever decay.
2. **Taken once per `pixelBufSeq`, and NOT while the beam is sweeping.** During
   a sweep the glass is old below the beam line and new above it, so a capture
   on the content-change present itself records mostly the OLD page and hands it
   back as if it were the new one. Waiting for the first present after the sweep
   costs nothing, because the trail is driving presents anyway.
3. **Deposited once per captured glass, not once per content change.** An
   antialiased page is written TWICE — a 1-bit base pass, then the composed one
   13–22 ms later — so the seq moves twice per page turn and the second write
   lands inside the sweep, before a new capture exists. Without this rule the
   same picture is deposited twice. Measured: two runs of the same binary
   differed in integrated trail energy by **4×** (173 vs 764 luma·ms) depending
   on where the second write fell; with the rule they agree to 3% (173 vs 168).

Three things the rules do NOT cover, found by adversarial review and recorded
rather than fixed:

- **Below the beam line, the old picture wears the NEW page's coverage.** The
  capture is taken before the scanlines, the sheet and the grain, and those
  passes run unclipped over the whole output — so during a sweep the un-swept
  region is *previous picture + current coverage*. If the sheet identity
  promoted with the page turn, the previous page is briefly shown under the new
  leaf's tooth and formation. Bounded by `beamMs` (55 ms as shipped, 300 ms at
  the longest dial) and cosmetic. There is no better option that keeps rule 1:
  capturing after the coverage would feed the coverage back into itself.
- **The scanline bloom's beam-current map is baked from a frame that is ~0%
  swept.** `ensureScanlinesField` keys its cache on `pixelBufSeq` and derives
  its brightness buckets from a readback of the composed frame; the sweep starts
  on the same present the seq advances on, so the readback sees the previous
  picture and the map is then cached for the whole page. Pre-existing — the old
  panel-space ghost put the old page under that readback too — and this change
  widens it from the panel rect to the whole output. The comment above
  `simpower::compositeWarmUp` warns about exactly this failure mode for the
  warm-up and the same guard was never applied to the beam.
- **A resize or rotation mid-sweep** used to starve the capture (rule 2 held it
  back, and the deposit requires a matching size, so that page's phosphor was
  dropped and the beam stretched a stale-sized glass). Fixed while writing this:
  a size mismatch now captures immediately and abandons the sweep with it.

Rule 3 is also the more honest model. The 1-bit pass is never presented at all —
the present hold coalesces it, which is what the page-turn-flash work bought —
and a frame that never reached the glass cannot have left phosphor on it.

### What the capture cost, and what it removed

It replaced a framebuffer-sized copy (`ghostPixels.assign`), a framebuffer-sized
intensity pass and two framebuffer-sized uploads. On the canary at 2x the
framebuffer is 1584×1056 and the output is 528×792, so the new work is over
**four times fewer pixels** even including the readback: measured `glass BUILD
3.34 ms`, once per page turn, against a page turn that costs 434 ms. The whole
`ghostTexture` / `ghostPixels` / `ghostIntensityTexture` apparatus is gone.

On a phone in portrait the ratio runs the other way (framebuffer 1584×1056 at
2x, output ~1206×2622), so the capture there is roughly twice the pixels of what
it replaced — still once per page turn, still against a page turn costing
hundreds of ms. **UNCONFIRMED on device.**

It is not free on the plain desktop default either, and the honest figure is
small: at render scale 1 with no dials seeded (where the resolved palette still
carries a 283 ms trail, so the capture is live), the FIRST present of a page
went from 30.10 ms to 31.80 ms, three runs each — `glass BUILD` costs 3.2 ms and
the flip gives 2.7 ms of it back, for a net **+1.7 ms per page RENDER**. Nothing
is paid on any present after it.

## 4. The beam sweeps the whole face

It was panel-only: the old picture below the sweep line was `drawPanel(ghost)`
and the clip band was the panel rect, so the pad was painted afterwards,
unclipped, and arrived all at once. A tube has one gun and one raster. The old
picture is now the composed glass drawn 1:1 and the band spans the output; the
overlay re-states the same band in device pixels so the pad is swept too, and
the letterpress moved INSIDE the clip (the old picture already carries its own,
so an unclipped pass would print the squeeze twice below the line).

**The accumulator is deliberately NOT swept away.** It is clipped to the swept
band while the beam runs, exactly as it was before: below the line the glass
still holds the previous frame, which already showed whatever trail it showed at
the time, and compositing this present's accumulator over it lights the old
picture a second time. On the ADD-fallback renderer that brightened the whole
un-swept region by up to **18%** for the length of the sweep — measured, the
band came back as the previous page's exact pixel histogram with every level
scaled by 1.175. Clipping it removed that outright.

### The beam's old picture used to be the wrong picture

Found on the way and worth its own line. With a 600 ms sweep, the un-swept
region, mean luminance by band:

| | before the turn | during the sweep |
|---|---|---|
| before this work | 48.7 / 50.3 | **44.4 / 46.3** |
| after | 48.7 / 50.3 | **48.7 / 50.3** |

The old ghost was the raw previous FRAMEBUFFER, resampled to the window by a
different path from the one the live panel takes — a different filter and a
different lattice. Its histogram differed too (7057 pixels at level 115 against
1887 in the frame it was replacing). So for the length of every sweep the
un-swept half of the page was a blurrier, ~9% darker copy of the page that was
standing there a frame earlier. It is now bit-identical, because the capture is
the pixels themselves.

## 5. The proof that persistence reached the paper

The desktop window is exactly panel-sized, so the surround does not exist there
and none of this could be photographed. Two env vars now give the canary the
bands a phone reserves — see §8 — and with them the demonstration is direct: a
dark page turn with a 200 px bottom band that grows to 420 px 60 ms later, so
the panel is refitted from 394×592 to 248×372 and a strip of glass that was page
becomes surround while the phosphor is still lit.

Mean and peak luminance of the region below the NEW panel but inside the OLD
panel's footprint (x 67–461, y 372–592 device px), same seed, same card:

| after the refit | before: mean / max | after: mean / max |
|---|---|---|
| (pre-turn, page still there) | 50.25 / 210 | 50.25 / 210 |
| the refit | 26.15 / 26 | **29.16 / 42** |
| +70 ms | 26.15 / 26 | 29.16 / 42 |
| +90 ms | 26.15 / 26 | 26.98 / 33 |
| +210 ms | 26.15 / 26 | 26.73 / 31 |
| +310 ms | 26.15 / 26 | 26.45 / 29 |
| +510 ms | 26.15 / 26 | 26.27 / 27 |
| +710 ms | 26.15 / 26 | 26.15 / 26 |

Before, that strip goes flat on the frame the page leaves it: max 26 against a
ground of 26 — the crop's content coverage is **0.0%**, a picture of nothing.
After, **16.1%** of its pixels are away from the modal ground and the previous
page's text is legible in it, decaying to nothing over about 0.7 s. Effect delta
between the two crops at the same instant: 100% of pixels changed, mean |Δ|
3.11, max 17, **15.4% of pixels move more than 4 levels**.

The values plateau between rows because the trail's presents are ~18 ms apart
and the capture grid is finer than that: two rows showing the same number are
two photographs of one frame, not a stalled decay.

Figures: the two whole frames at native pixels (528×792), and the crop above as
a 2× NEAREST magnification — lossless PNG throughout, no scaling other than the
stated integer factor. They live in
<https://claude.ai/code/artifact/4e204e6a-41f2-45cc-90cb-a19ebc625813> (that
page is the view, this file is the record) and are not checked in, because they
are reproducible from the recipe: build both arms at render scale 2, then

```bash
CROSSPOINT_SIM_AS_SHIPPED=1 CROSSPOINT_SIM_GRAIN_SEED=7 \
CROSSPOINT_SIM_BOTTOM_INSET='200;5290:420' \
CROSSPOINT_SIM_INPUT_SCRIPT='5000:QTAP:RIGHT;7000:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS='5340:shot.bmp' \
SDL_VIDEODRIVER=dummy .pio/build/simulator_x3/program
```

on a card seeded to `darkMode: 1` and `readerActivityLoadCount: 0`, with the
desktop `settings.json` parked. The crop is x 67–461, y 372–592.

## 6. The desktop composites the trail with ADD, not MAXIMUM

Measured, not inferred, and it explains a decade of small disagreements between
what this machine shows and what the phone shows:

```
[accum] deposit blend: ADD fallback (no MAXIMUM here)
[accum] composite blend: ADD fallback (no MAXIMUM here)
```

SDL's **software** renderer — the desktop canary and all three packaged Mac apps
— cannot compose `SDL_BLENDOPERATION_MAXIMUM`, so both the deposit and the
composite take the documented ADD-at-alpha-96 fallback. The phone's Metal
backend takes MAXIMUM. That is not cosmetic: ADD *brightens* a pixel that the
old frame and the new one both lit, MAXIMUM leaves it alone. **Every
trail-brightness figure ever measured on this machine is the fallback path**, a
page that brightens under a trail on the desktop is expected rather than a bug,
and S-016's "the physics were wrong, not the arithmetic" argument only actually
takes effect on the phone.

The two one-shot log lines above now say which is live, because without them the
two platforms look like the same code disagreeing about arithmetic.

### The one visible consequence on a Mac

Because the desktop is on the ADD path, dropping the second deposit per page
turn (§3, rule 3) makes the desktop trail dimmer. Integrated excess luminance
over the settled page, ages 150–900 ms, two runs per arm:

| | run 1 | run 2 |
|---|---|---|
| before | 260 | 294 |
| after | 173 | 168 |

**On the phone the arithmetic says this is nil**: under MAXIMUM the second
deposit is the NEW 1-bit page, which is already on screen at full brightness, so
`max(dst, src)` is `dst` and it contributes nothing. What the desktop lost is
therefore the old flash of the new page adding to itself — the desktop-only
residue of the artifact the page-turn-flash work was about. **UNCONFIRMED on
device**; what to look for on an iPhone is whether a dark page turn's trail
looks any different at all, and the prediction is that it does not.

## 7. What it costs

Controlled A/B, three runs each, software renderer, X3 at 2x, dark, as-shipped
dials, card reseeded to the same page and polarity before every run. The metric
is the one `trail-cost-2026-08-26.md` used.

| | trail presents | ms per present | CPU per dark page turn |
|---|---|---|---|
| `2edbe25` | 43.7 | 12.46 | **544 ms** |
| with this work | 52.3 | 8.30 | **434 ms** |
| | +20% | **−33%** | **−20%** |

The enhancement list predicted a saving and there is one. Where it comes from,
from the `[timing]` stations on a steady trail present:

| | before | after |
|---|---|---|
| `accum` (fade + deposit, a render-target pass) | 3.2 | 5.5 |
| `flip` | 8.5 | 1.7 |
| total | 11.7 | 7.2 |

The accumulator's own station going UP while the total halves is a bookkeeping
artefact and worth stating so nobody chases it: `SDL_SetRenderTarget` flushes
the command queue, and the pass now runs after the panel and the overlay have
been queued rather than before, so the flush pays for their draws and the cost
lands in `accum` instead of in `flip`. The real saving is that the accumulator
is drawn as an axis-aligned 1:1 blit of a 528×792 texture instead of
`SDL_RenderTextureRotated` on a 1584×1056 one — which is enhancement item 4's
argument arriving early, for the trail's draw only.

**Presents go UP, and that is not a cost.** The trail's wall-clock length is
unchanged; the loop is self-driven at whatever rate a present costs, so a
cheaper present simply fits more of them into the same window. Twenty percent
more frames for twenty percent less CPU is the shape the owner asked for
(*"keep refresh as high possible… while preserving or lowering resource
usage"*).

Re-measured interleaved (base, then this, three times) while the machine was
busy, because §5 of the trail-cost doc's item 5 warns that machine load weights
every trail mean: 737 ms before against 428 ms after, −42%. The direction is the
same under both conditions; the magnitude is not, so **−20% is the figure to
quote** and it is the quiet-machine one.

## 8. The bands the desktop never had

Two env vars, desktop QA only, both unset by default and both no-ops when unset:

| Variable | Effect |
|---|---|
| `CROSSPOINT_SIM_TOP_INSET` | reserve N device pixels at the top, as the phone does for the status bar and the Island |
| `CROSSPOINT_SIM_BOTTOM_INSET` | the same at the bottom, as the phone does for the button pad |

Each value is a **schedule**: `"120"` reserves 120 px from boot;
`"200;5290:420"` reserves 200 and grows it to 420 at 5290 ms on the
`SDL_GetTicks` clock. The schedule is what §5 needed, and it is the only way
this machine can photograph what a live trail does when the PAGE MOVES under it.

They exist because the desktop takes the plain letterbox path, where the window
is exactly panel-sized and there is no surround at all — which makes the canary
the platform on which anything about the surround cannot be reproduced. That is
this repo's recurring failure mode stated as a fact about geometry.

Note what they do NOT give you: there is no overlay painter on the desktop, so
the reserved band is empty field colour and no button pad appears in it.

The schedule is parsed at file scope with a `simreset::Registrar`, not behind a
function-local `static bool …Parsed` in `main()`. That is not tidiness: the
desktop reboot is execvp and re-initialises everything, iOS longjmps back into
`setup()` in the same process, and a consumed schedule guarded by a latched flag
would never replay there — the exact failure `src/SimulatorRebootResets.h`
exists for.

## 9. The gate

- **The still page is byte-identical.** `tools/capture_arm.sh` on the default
  (scale 1) build: dark `53aaf43c38cc834f501525b5973d2566`, light
  `3f4773ed9d77fac0da90d6d2fb4aba72`, both unchanged, checked after each stage
  of this work and ten more times at the end.
- **The gate harness had a hole, and it is now a gate.** One of those runs came
  back with a light arm rendering a DARK page — which reads exactly like a
  rendering regression and was chased as one. It was the desktop
  `settings.json` being read despite the park: measured at **3 of 7 pairs**, and
  still ~1 arm in 10 after adding a settle for a straggling restore. The tell
  was a log line `capture_arm.sh` sent to `/dev/null`; it now keeps the log,
  greps for `applied N keys from ./settings.json`, and **exits 3 with a message**
  rather than printing a plausible wrong hash. Nothing about this repo's surface
  code was involved — but a gate that can return the wrong answer quietly is
  worse than no gate, and this one had already done it once.
- **The trail's own interior is NOT gateable by hash** and reading one as a
  regression would be a false positive — two runs of the unmodified binary
  give different mid-trail frames at every instant, because the rendered decay
  depends on how many truncating fade steps the present cadence happened to fit.
  What was run instead: 68 captures per arm at 25 ms spacing, two arms per
  build, aligned on the first changed frame. Both builds pass through the same
  number of distinct frames (29–31 before, 29–30 after), settle on the SAME
  final frame (`b546d7fd…`), and take the same time to get there (800/850 ms
  before, 750/825 ms after — the run-to-run spread within one binary is larger
  than the difference between binaries). The decay ENVELOPE differs only by
  §6's ADD-path deposit count.
- **The 7:1 contrast floor is untouched on a settled page**, because a settled
  page has no trail: `accumLive` is false and nothing is composited. The pad's
  printed ratios are therefore exactly what `pad-outline-black-and-white.md`
  says. What is new is that a trail can now land ON the pad for the length of a
  page turn; it is darken-safe under MAXIMUM by §2's arithmetic and transient
  under ADD.
- `tests/run_all.sh`: 57 passed, 0 skipped.
- Both desktop envs build (`simulator`, `simulator_x3`); the iOS app target
  builds (`CrossPointX3`, arm64 simulator SDK).

## 10. What is still unconfirmed

Everything about how this looks on a phone. The desktop cannot show a button
pad, cannot show MAXIMUM compositing, and cannot show the 2x minification a
phone applies to the panel. Specifically, on device:

- does a pad button's afterglow read as phosphor or as a smear;
- does the whole-face beam sweep look right crossing from the page into the pad;
- is the trail visibly unchanged, as §6 predicts;
- what the capture's readback actually costs on Metal, once per page turn.
