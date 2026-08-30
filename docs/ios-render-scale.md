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

## Which displays 3x would actually fit — arithmetic, 2026-08-24

Owner question: *"would 3x work at native res on ipad pro or macbook pro?"*
Recorded rather than measured; the numbers below are arithmetic from published
native panel resolutions, NOT a run on hardware. Nothing here is a claim about
how it looks.

3x makes the X3 framebuffer **1584 x 2376** (portrait) or **2376 x 1584**
(landscape). The fit factor is `min(displayW/panelW, displayH/panelH)`. **At or
above 1.00 the panel is not minified**, which is the whole question: below 1.00
the presentation resamples and the selection dither beats against the sampling
lattice, which is ST-008 and is why the tier was dropped for the phone.

| Device | Native px | Fit | |
|---|---|---:|---|
| iPhone SE (3rd gen) | 750 x 1334 | 0.47 | minifies |
| iPhone 15 / 16 | 1179 x 2556 | 0.74 | minifies |
| iPhone 16 Pro | 1206 x 2622 | 0.76 | minifies |
| iPhone Air | 1260 x 2736 | **0.80** | minifies — the measured ST-008 case |
| iPhone 16 Pro Max | 1320 x 2868 | 0.83 | minifies |
| iPad mini (A17) | 1488 x 2266 | 0.94 | minifies |
| iPad 10.9 / iPad Air 11" | 1640 x 2360 | 0.99 | minifies, barely |
| iPad Pro 11" (M4) | 1668 x 2420 | **1.02** | fits, barely |
| iPad Air 13" | 2048 x 2732 | 1.15 | fits |
| iPad Pro 13" (M4) | 2064 x 2752 | **1.16** | fits |
| MacBook Air 13" | 2560 x 1664 | 1.05 | fits |
| MacBook Air 15" | 2880 x 1864 | 1.18 | fits |
| MacBook Pro 14" | 3024 x 1964 | **1.24** | fits |
| MacBook Pro 16" | 3456 x 2234 | **1.41** | fits |
| Studio Display | 5120 x 2880 | 1.82 | fits |
| Pro Display XDR | 6016 x 3384 | 2.14 | fits |

So the answer is **yes for both, and for every Mac** — no iPhone fits and no
iPad below the Pro/Air 13" does.

**Three caveats, and the first two decide the marginal rows.**

1. **These are RAW panel dimensions.** The usable area is smaller: safe areas
   and the button pad on iOS, window chrome and the menu bar on macOS. On a
   tablet the pad sits in the margins BESIDE the page rather than in a band
   below it, so it eats WIDTH — which is exactly the dimension the iPad Pro 11"
   has 2% of headroom in. Expect the 11" to fall under 1.00 in practice. The
   13" and every Mac have real margin.
2. **Height is the binding constraint on every iPad**, width on every Mac,
   because the panel is presented portrait on one and landscape on the other.
3. **The cost is not small.** A compose at 3x measures **115-271 ms** against
   ~30 ms at 2x (`src/HalDisplay.cpp:675`), because it is 2.25x the pixels.
   Fitting is necessary, not sufficient.

**STANDING RULING, owner 2026-08-24: the 3x assets STAY.** Asked whether to
delete the 62 generated 3x builtin font headers (495,933 lines, 44 MB) as the
largest item in `docs/refactor-plan-2026-08-24.md`, he chose to keep them, on
the ground this table establishes: 3x has a future on the tablets and the Mac,
and these are the assets such a build needs. **Do not re-propose deleting them
as dead code.** They are dormant assets for a tier that fits every display in
the lower half of the table, not leftovers.

**What this does NOT change.** 3x stays retired: the ruling was "drop 3x support
for now" and the shipped app is a phone app, where the arithmetic above says it
cannot fit on any model. This section exists so that a future decision to
re-enable it for tablets or the Mac starts from numbers instead of from scratch,
and so that `docs/refactor-plan-2026-08-24.md` Tier 1 is read with its
correction: the 3x builtin font headers are NOT dead in every configuration,
because `CROSSPOINT_RENDER_SCALE=3` remains a supported desktop opt-in
(`src/main.cpp:93`) and every display in the lower half of that table fits it.

## The tablet question came back, 2026-08-29 — and is being MEASURED this time

Owner, on seeing the new iPad band work: *"isnt 3x possible on ipad pro?"* The
table above already said yes for the 13" (1.16) and barely for the 11" (1.02).
Asked whether to build the iPad grid at 2x, go to 3x, or produce both, he ruled:
**"Build both, render them side by side."**

So the section above is about to stop being arithmetic. Two arms of the SAME
page, same book, same content, captured at native pixels on an iPad Pro 13:

| Arm | Panel (portrait) | Left for the 1+2 band construction |
|---|---|---|
| 2x — the shipped ceiling | 1056 x 1584 | roomy; the unit is large |
| 3x — ceiling raised for the build only | 1584 x 2376 | ~376 px of height, ~480 px of width; unit ~125 px / 62 pt |

**This is a comparison build, not a ship.** The working tree must come back with
`CROSSPOINT_IOS_RENDER_SCALE` at 2 and `CrossPointPrefs_renderScale()` returning
2. What shipping it would actually take is the part worth having on the record
before anyone is tempted: per-idiom runtime selection (the machinery exists --
`cp::setRenderScale()` already clamps to the compiled ceiling), and the 3x font
tier landing on iPhone installs too, because it is one bundle.

Two numbers this arm will produce that nothing here has: whether the panel truly
presents at or above 1.00 on the device rather than on paper, and whether the
recorded 115-271 ms compose cost holds. Until those come back, every 3x figure
in this file is arithmetic and should be read as such.

**~~Panel (1x) is back in the picker~~ — SUPERSEDED, and it was stale for six
days.** That was true when written (2026-08-21, restoring the row after the
1x/2x/3x trim), and false from 2026-08-23, when the whole Sharpness row went
with 3x because a one-value control was judged worse than none. Verified
2026-08-29: `renderScale` does not appear in `ios/Settings.bundle/Root.plist`
(37 rows), and `tests/panel_palette_test.cpp:453` asserts it ABSENT, so a
re-add is a conscious act.

The half of it that is still TRUE and is the reason 1x stays in the codebase:
**the 1x tier is structural and costs no bundle at all** — the hi-res
companions carry bitmaps only and take their metrics from the 1x tables. 1x
cannot be deleted without deleting the metrics every other tier reads.

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

## STANDING RULING, owner 2026-08-29: 1x and 3x both STAY

Asked, while a render-scale guard was being added, whether removing all 1x and
3x code would help: **"keep 1x and 3x."** This reaffirms and widens the
2026-08-24 ruling above, which covered the 3x assets only.

The reasons are on the record so this is not re-proposed a third time:

- **1x is not a legacy tier.** `CROSSPOINT_RENDER_SCALE` defaults to 1 in
  `src/HalDisplay.h` to MIRROR THE DEVICE, and consumers opt in to
  supersampling -- a plain `pio run -e simulator_x3` is device-exact. Deleting
  1x would delete the mode in which the simulator shows what the e-ink hardware
  actually draws, which is the reason this repo exists.
- **3x is dormant, not dead.** The table above says it fits every display in its
  lower half, and on 2026-08-29 an arm-B build rendered a real iPad Pro 13 page
  at 3x (`panelH=2376px`) to compare against 2x. The choice is open.
- **Neither tier caused the incident that prompted the question.** An agent
  hardcoded `CrossPointPrefs_renderScale()` to 3 for that comparison build and
  left a comment saying it must be reverted. The comment was accurate and
  stopped nothing. Both existing guards watch the COMPILE-TIME macro --
  `ios/testflight.sh` greps the generated project, `build_identity_test` checks
  the compiled core -- and the CMake ceiling was still 2, so both would have
  passed while the app rendered every page at 3x.

**The actual fix, and where it lives:** `tests/dial_table_test.cpp` now reads
`ios/CrossPointPrefs.mm` as text and fails when `CrossPointPrefs_renderScale()`
returns anything but 2, in the same shape it already pins the frozen surface
dials. Proven both ways on 2026-08-29 -- PASS on the good tree, FAIL against the
exact `return 3;` state, with a message naming both the ceiling and the test
that must move together for a real tier change.
