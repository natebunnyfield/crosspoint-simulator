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
| Exact (2x) — one page pixel per screen pixel | `2` (default) | 1584x1056 | presented at 1.0, nothing resampled |
| Panel (1x) — what the e-ink hardware draws | `1` | 792x528 | presented at 2.0, nearest, blocky by design |

**Fine (3x) is RETIRED as of 2026-08-23** — owner: "drop 3x support for now".
The row is gone from the picker and the default moved from 3 to 2. A store
written by build 129 or earlier answers `3`, which most installs will, so
`CrossPointPrefs_renderScale()` maps it to 2 the way `panelpalette::resolve`
maps a retired preset: a retired row behaves like an unknown one rather than
falling through. That mapping is deliberately NOT left to
`cp::setRenderScale()`'s ceiling clamp, which lands on the same 2 today and
would silently mean something else the moment the ceiling moved.

**Panel (1x) is back in the picker**, having been trimmed on 2026-08-21 when the
choice was 1x/2x/3x. It costs no bundle at all — the 1x tier is structural,
since the hi-res companions carry bitmaps only and take their metrics from the
1x tables — and without it the row would offer exactly one value.

### Putting 3x back

Everything the engine needs is still here; nothing was deleted. The whole
re-enable is:

1. `set(CROSSPOINT_IOS_RENDER_SCALE 3 ...)` in [ios/CMakeLists.txt](../ios/CMakeLists.txt).
   That one number re-arms all four gates at once: `all.h`'s
   `#if CROSSPOINT_RENDER_SCALE >= 3` include block, `main.cpp`'s matching
   registration block, the seed loop's `<family>/3x/` glob, and
   `CrossPointFsPrep`'s tier loop. `ios/testflight.sh` reads the same number, so
   its pre-archive gate follows.
2. Add the `Fine (3x)` row back to `ios/Settings.bundle/Root.plist` — **appended,
   with value 3**, never inserted, because the choice persists as an integer.
   Restore the paragraph in the group's `FooterText`.
3. Drop the `raw == 3 ? 2 : raw` retirement map in `ios/CrossPointPrefs.mm`, and
   decide whether the default goes back to 3 (`registerDefaults` and the plist's
   `DefaultValue` must agree).
4. Nothing to rebuild: `build/seedfonts/<Family>/3x/` still holds the full 3x
   tier (195,420,632 bytes across 7 families), and `build-sd-fonts.py --scale 3`
   still works. Excluding the tier at bundle time rather than deleting it is
   exactly what makes this step free — a rebuild is a ~40 minute rasterisation
   run, and Heros needs `--drop-codepoints 0x2E3B` at 3x.

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
| Reading the key | `ios/CrossPointPrefs.{h,mm}` — `CrossPointPrefs_renderScale()`, key `renderScale`, `registerDefaults` fallback `2`, retired `3` mapped to `2` |
| The latch | `src/simulator_main.cpp` `latchRenderScale()`, first statement of `main()` |
| The variable | `crosspoint-reader/lib/GfxRenderer/RenderScale.h` — `cp::renderScale()` |
| Active framebuffer geometry | `src/HalDisplay.h` — `activeWidth()` / `activeHeight()` / `activeWidthBytes()` / `activeBufferSize()` |
| Which font tiers reach the bundle | `ios/CMakeLists.txt`, the `foreach(_tier RANGE 2 ${CROSSPOINT_IOS_RENDER_SCALE})` seed-font loop |
| Which font tiers reach the card | `ios/CrossPointFsPrep.cpp`, the `for (int tier = 2; tier <= CROSSPOINT_RENDER_SCALE; ...)` seed loop |
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

Measured 2026-08-23 on the shipped seven-family tree, from the build-129 IPA's
own `unzip -lv` figures — not a directory estimate:

| tier | installed (bytes) | in the IPA (bytes) |
|---|---:|---:|
| 1x | 26,979,496 | 10,361,498 |
| 2x | 90,675,364 | 23,844,577 |
| **3x** | **195,420,632** | **38,841,265** |

So dropping 3x is **−195,420,632 installed and −38,841,265 of the download**
from the seed fonts alone, before the builtin 3x glyph tables the same ceiling
change removes from the binary. 1x needs no companion set at all — at 1x the 1x
face already matches the framebuffer — which is why the loop starts at tier 2.

Also, per render: `drawPixel`'s block loop and the fill path's `MASK_PERIOD`
modulo are variables rather than constants on a host build. Per row for the
modulo, per pixel for the loop bound. Not measured; the device build is
untouched, where all of it still folds to literals.

## Status

**2x default: SHIPPED — UNCONFIRMED on device.** Verified in the iOS Simulator
(a page renders in a bundled card family at 2x, `[BUILD]` agreement logged) and
on the desktop canary; not yet on a phone.

**The 2026-08-15 entry below stands as written.**

**SHIPPED — UNCONFIRMED on device.** Nothing here has run on an iPhone or in the
iOS Simulator; the iOS CMake configure has not been run either (it needs the
gitignored 183 MB `ios/seedfonts/` tree). What HAS run: the desktop simulator at
all three scales with byte-identical output against fixed-scale references, the
ESP32-C3 device build, and `tests/run_all.sh` at 18/18. Full ledger, including
what to look at on the phone, in the firmware doc.

## The row itself is gone, 2026-08-23

Dropping 3x left the picker with one value, and the owner ruled a one-value
control worse than no control: *"2x only — remove the row."* Sharpness and its
group left `Root.plist` the same day the doctrine dials did.

So render scale is no longer a preference. It is **2**, returned as a constant
by `CrossPointPrefs_renderScale` without consulting `NSUserDefaults` — the same
discipline the frozen page dials use, and for the same reason: a store written
by build 129 or earlier holds 3 (it was both an offered row and the default),
and reading it would let an old value re-point something the owner can no
longer see or change. 1 was already retired on 2026-08-21.

Putting the CHOICE back therefore means restoring the row, the registration,
and the getter's read — not only rebuilding the tier. The checklist above still
covers the tier half.
