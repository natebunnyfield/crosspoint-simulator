# Page Sharpness — the iOS render-scale setting

*2026-08-15, branch `ios-render-scale`. The mechanism, the evidence for every
claim, and the negative results live in the firmware repo:
[`docs/render-scale.md`](../../crosspoint-reader/docs/render-scale.md). This
file is the simulator-side half: what the setting is, where each piece of it
lives, and what it costs.*

## The setting

`Settings > CrossPoint X3 > Page Sharpness`, one `PSMultiValueSpecifier`:

| Row | Stored | Framebuffer (X3) | On an iPhone Air |
|---|---|---|---|
| Fine (3x) — most detail, smoothed | `3` (default) | 2376x1584 | presented at 0.7955, bilinear |
| Exact (2x) — one page pixel per screen pixel | `2` | 1584x1056 | presented at 1.0, nothing resampled |
| Panel (1x) — what the e-ink hardware draws | `1` | 792x528 | presented at 2.0, nearest, blocky by design |

**It takes effect on the next launch, and the footer says so.** That is not a
shortcut: the factor sizes the SDL texture and selects which hi-res glyph tier
is registered, both before the first frame. See the firmware doc for why a
relaunch is the honest answer and why "live" is not available.

**Layout never moves.** Every setting breaks the same words on the same lines;
only the raster changes. Verified by capture at all three.

## Where the pieces are

| Piece | File |
|---|---|
| Owner-facing rows + footer | `ios/Settings.bundle/Root.plist`, group **Page Sharpness** |
| Reading the key | `ios/CrossPointPrefs.{h,mm}` — `CrossPointPrefs_renderScale()`, key `renderScale`, `registerDefaults` fallback `3` |
| The latch | `src/simulator_main.cpp` `latchRenderScale()`, first statement of `main()` |
| The variable | `crosspoint-reader/lib/GfxRenderer/RenderScale.h` — `cp::renderScale()` |
| Active framebuffer geometry | `src/HalDisplay.h` — `activeWidth()` / `activeHeight()` / `activeWidthBytes()` / `activeBufferSize()` |
| Both font tiers in the bundle | `ios/CMakeLists.txt`, the `foreach(_tier RANGE 2 ...)` seed-font loop |
| Both font tiers onto the card | `ios/CrossPointFsPrep.cpp`, the `for (int tier = 2; ...)` seed loop |
| The runtime switch itself | `crosspoint-reader/scripts/sim_render_scale.py` emits `CROSSPOINT_RENDER_SCALE_RUNTIME`; `ios/CMakeLists.txt` sets it PUBLIC on `crosspoint_core` |

`CROSSPOINT_RENDER_SCALE` still exists and still means what it always did on the
command line — it is now the **ceiling**, and `cp::renderScale()` is the factor
in use. Anything that sizes storage or gates a `#if` reads the ceiling; anything
arithmetic reads the active factor. Mixing them up at scale 2 on a ceiling-3
build reads 2.25x past the live picture.

## Driving it headlessly

The desktop simulator gets the same choice through an env var read at **run**
time, so one binary covers all three:

```bash
CROSSPOINT_RENDER_SCALE=3 pio run -e simulator_x3          # ceiling 3, runtime switch on
CROSSPOINT_SIM_RENDER_SCALE=2 .pio/build/simulator_x3/program   # same binary, renders 2x
```

Unset, it renders at the ceiling — byte-for-byte the behaviour from before the
switch existed. Set `CROSSPOINT_SIM_WINDOW_SCALE` to the same number to make a
`CROSSPOINT_SIM_SCREENSHOTS` capture 1:1 with the framebuffer.

`CROSSPOINT_RENDER_SCALE_RUNTIME=0` at BUILD time turns the switch off and makes
the scale a compile-time constant again. That is not nostalgia: it is how you
build a reference binary to diff a runtime build against, and diffing them is
the only way to know that all ~40 converted arithmetic sites read the active
factor rather than the ceiling. They do — the captures are byte-identical at 1,
2 and 3.

## What it costs

**About +53 MB of app bundle.** The six installed families' hi-res sets measure
16 MB (1x), 53 MB (2x) and 114 MB (3x); the app already carried 1x and 3x, and
supporting the 2x setting means carrying 2x as well. (A directory measurement —
`.cpfont` compresses, so the archived delta is smaller by an unmeasured amount.)
1x needs no companion set at all.

Also, per render: `drawPixel`'s block loop and the fill path's `MASK_PERIOD`
modulo are variables rather than constants on a host build. Per row for the
modulo, per pixel for the loop bound. Not measured; the device build is
untouched, where all of it still folds to literals.

## Status

**SHIPPED — UNCONFIRMED on device.** Nothing here has run on an iPhone or in the
iOS Simulator; the iOS CMake configure has not been run either (it needs the
gitignored 183 MB `ios/seedfonts/` tree). What HAS run: the desktop simulator at
all three scales with byte-identical output against fixed-scale references, the
ESP32-C3 device build, and `tests/run_all.sh` at 18/18. Full ledger, including
what to look at on the phone, in the firmware doc.
