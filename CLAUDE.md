# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A simulator for [CrossPoint](https://github.com/crosspoint-reader/crosspoint-reader) firmware. On the desktop it is **not** a standalone app: it ships as a PlatformIO library that downstream firmware adds as a `lib_dep` (named `simulator`) and builds with `platform = native` and `-DSIMULATOR`. The result is the firmware compiled as a host binary, with the e-ink display rendered into an SDL3 window.

There is no desktop build target inside this repo. Desktop build and run happen in the consuming firmware project. See [README.md](README.md) for end-user setup, and [.claude/CONTEXT-sim-notes.md](.claude/CONTEXT-sim-notes.md) for the deep architecture notes and bug-fix history (read this before non-trivial changes).

**There is also a native iOS target**, driven by CMake over the same source set — see [ios/README.md](ios/README.md). It compiles the firmware plus this HAL for `arm64-apple-ios` and presents the panel on an iPhone with an on-screen button pad. One source set, two toolchains; the desktop PlatformIO build stays the canary, so keep it green.

**SDL3, not SDL2.** Both toolchains build against SDL3 so the shared sources need no per-platform SDL shim. The desktop env gets its flags from `!pkg-config --cflags --libs sdl3`.

## Build and run (from the consuming firmware repo)

```bash
pio run -e simulator -t run_simulator   # build + launch
pio run -e simulator                    # build only, then .pio/build/simulator/program
rm -rf ./fs_/.crosspoint/               # clear stale on-disk caches after storage/cache changes
```

**Render scale is an env var, not a build flag.** [src/HalDisplay.h](src/HalDisplay.h)'s `CROSSPOINT_RENDER_SCALE` defaults to 1 (mirror the device) and consumers opt in to supersampling. CrossPoint's desktop simulator envs keep that default — a plain `pio run -e simulator_x3` is device-exact — and `scripts/sim_render_scale.py` reads the env var to opt in:

```bash
CROSSPOINT_RENDER_SCALE=2 pio run -e simulator_x3 -t run_simulator
```

It must be an env var rather than `PLATFORMIO_BUILD_FLAGS="-DCROSSPOINT_RENDER_SCALE=1"`, because PlatformIO *appends* that variable: with a `-D` in `platformio.ini` the compiler saw both definitions and warned `-Wmacro-redefined` in every translation unit, which buried the real warnings. Prepending `-UCROSSPOINT_RENDER_SCALE` does not help — SCons parks unrecognised flags in `CCFLAGS`, and `CCCOM` expands `$CCFLAGS` *before* `$_CPPDEFFLAGS`, so the undef is consumed before either `-D` is seen. The pre-script picks the value once, so exactly one definition ever reaches the command line. An explicit `-D` still wins if you pass one. iOS is unaffected: [ios/CMakeLists.txt](ios/CMakeLists.txt) sets the macro directly.

`CROSSPOINT_SIM_DEVICE_PIXELS=1` (runtime env) sizes the window in DEVICE
pixels — point size divided by the display content scale — so one panel pixel
lands on one screen pixel instead of a 2×2 Retina block. Opt-in because the
full-panel-point window is the deliberate desktop default; the packaged Mac
apps set it through `LSEnvironment`, composed with
`CROSSPOINT_SIM_WINDOW_SCALE=2` for the double-size app.

To confirm which scale a binary actually got, count hi-res font loads (1 = 2x, 0 = 1x) — do not use the screenshot dimensions, since the window is sized in *logical* panel pixels and tracks `CROSSPOINT_SIM_WINDOW_SCALE`, not the render scale:

```bash
CROSSPOINT_SIM_INPUT_SCRIPT='5000:QUIT' SDL_VIDEODRIVER=dummy .pio/build/simulator_x3/program 2>&1 | grep -c 'hi-res'
```

For local dev against this repo, the firmware's `platformio.ini` should reference it as `simulator=symlink://../crosspoint-simulator` instead of the git URL.

There is no linter and no per-file build commands; most changes are "tested" by running the simulator and exercising the affected feature. Host tests exist in `tests/` (44 passing, 0 skipped as of 2026-08-23), run them when touching input, text entry, sleep, network, restart, task lifetime, read-aloud, palettes, the dial table, device-fidelity flags, the compressed-font container, or build-configuration paths. `tests/run_all.sh` builds and runs the host tests in one go (`-k <substring>` to filter) and exits non-zero on the first failure — the individual commands below are what it runs, kept here because they are also how you debug one in isolation. The four shell tests are not in the runner: all need a firmware checkout and use exit 2 for SKIP, which a pass/fail runner would misreport. All four PASS as of 2026-08-18, verified against a clean firmware worktree at `f80b140b6` with a seeded `fs_`; S-011 and S-015 are both closed and this sentence used to claim otherwise long after they were fixed. They need a card: with no `fs_/.crosspoint/settings.json` they SKIP with exit 2, which a casual run reads as "not failing" rather than "not run".

```bash
tests/run_all.sh
```


```bash
c++ -std=c++17 -Iios tests/pad_core_test.cpp ios/PadCore.cpp -o /tmp/pad_core_test && /tmp/pad_core_test
c++ -std=c++17 -Iios tests/pad_palette_test.cpp -o /tmp/pad_palette_test && /tmp/pad_palette_test ios/Settings.bundle/Root.plist
c++ -std=c++17 -Isrc tests/panel_palette_test.cpp -o /tmp/panel_palette_test && /tmp/panel_palette_test ios/Settings.bundle/Root.plist
c++ -std=c++17 -Isrc tests/dial_table_test.cpp -o /tmp/dial_table_test && /tmp/dial_table_test
c++ -std=c++17 -Isrc -Iios tests/panel_source_test.cpp -o /tmp/panel_source_test && /tmp/panel_source_test
python3 tests/panel_source_test.py   # one editor per polarity; run from the repo root
c++ -std=c++17 -Isrc tests/phosphor_grain_test.cpp -o /tmp/phosphor_grain_test && /tmp/phosphor_grain_test
c++ -std=c++17 -Isrc tests/letterpress_test.cpp -o /tmp/letterpress_test && /tmp/letterpress_test
c++ -std=c++17 -Isrc tests/scanlines_test.cpp -o /tmp/scanlines_test && /tmp/scanlines_test
c++ -std=c++17 -Isrc tests/show_through_test.cpp -o /tmp/show_through_test && /tmp/show_through_test
c++ -std=c++17 -O1 -Isrc tests/corner_defocus_test.cpp -o /tmp/corner_defocus_test && /tmp/corner_defocus_test
c++ -std=c++17 -Isrc tests/power_off_collapse_test.cpp -o /tmp/poc_test && /tmp/poc_test
c++ -std=c++17 -Wno-deprecated -Isrc -DCPZ_REPO_ROOT='"'"$PWD"'"' $(python3 tools/fw_include_flags.py) \
  tests/cpz_container_test.cpp <firmware>/lib/miniz/src/InflateStream.cpp \
  <firmware>/lib/Memory/BuildScratch.cpp <firmware>/lib/miniz/src/miniz_impl.c \
  -o /tmp/cpz_container_test && /tmp/cpz_container_test
c++ -std=c++17 -Isrc tests/laid_structure_test.cpp -o /tmp/laid_structure_test && /tmp/laid_structure_test
c++ -std=c++20 -Isrc -DCROSSPOINT_SIM_HOST_WIFI=1 tests/wifi_host_test.cpp -o /tmp/wifi_host_test && /tmp/wifi_host_test
c++ -std=c++20 -Isrc -DCROSSPOINT_SIM_HOST_HTTP=1 tests/http_dispatch_test.cpp -o /tmp/http_dispatch_test && /tmp/http_dispatch_test
c++ -std=c++20 -Isrc tests/restart_semantics_test.cpp src/SimulatorLifecycle.cpp -o /tmp/restart_test && /tmp/restart_test
c++ -std=c++20 -Isrc tests/task_registry_test.cpp -o /tmp/task_registry_test && /tmp/task_registry_test
c++ -std=c++20 -Isrc tests/read_aloud_channel_test.cpp -o /tmp/read_aloud_channel_test && /tmp/read_aloud_channel_test
c++ -std=c++20 -Isrc tests/device_truth_test.cpp -o /tmp/device_truth_test && /tmp/device_truth_test
c++ -std=c++20 -Isrc tests/sha256_test.cpp -o /tmp/sha256_test && /tmp/sha256_test   # add -lcrypto on Linux
c++ -std=c++17 -Iios tests/read_aloud_core_test.cpp ios/ReadAloudCore.cpp -o /tmp/read_aloud_core_test && /tmp/read_aloud_core_test
python3 tests/gen_cmake_sources_test.py   # the source-set generator; builds its own throwaway trees
tests/test_sleep_wake.sh <firmware-checkout>   # needs the desktop binary built
tests/test_text_entry.sh <firmware-checkout>   # host keyboard into a firmware text field
tests/test_read_aloud_capture.sh <firmware-checkout>  # capture + QTAP page turn, generated fixture book
tests/test_note_editor_repaint.sh <firmware-checkout>  # a note repaints while a HOST keyboard types
c++ -std=c++17 -DSIMULATOR -DSIMULATOR_DEVICE_X3 -DCROSSPOINT_RENDER_SCALE=2 -Isrc \
  $(python3 tools/fw_include_flags.py) \
  tests/build_identity_test.cpp src/SimulatorBuildIdentity.cpp -o /tmp/build_identity_test \
  && /tmp/build_identity_test
```

**The three `-D` tests exist because the code they cover is iOS-only.** `ios/*.mm`
cannot be compiled anywhere but a Mac and there is no paired device, so
`CROSSPOINT_SIM_HOST_WIFI`, `CROSSPOINT_SIM_HOST_HTTP` and
`CROSSPOINT_SIM_REBOOT_IN_PROCESS` are all overridable specifically to let the
phone's branches be exercised on a host. Keep that escape hatch when adding
another platform backend, or the branch ships with no coverage at all.

`pad_core_test` covers the iOS pad's finger→button passthrough (PadCore is pure and clock-free by design — do not add timers to it). `pad_palette_test` covers the pad's contrast ladder and its Current/Accessible/Transparent presets (`ios/PadPalette.h`, pure for the same reason): it recomputes every rung's sRGB contrast ratio, pins the Current preset to the exact shipped tones, proves −9/+9 reach #000000/#FFFFFF in both appearances and both roles, and — the part no `static_assert` can do — reads the shipped `ios/Settings.bundle/Root.plist` and fails when a row's printed ratio disagrees with the tone that row selects. Every failure mode there is silent: a rung equal to the field paints nothing, a mislabelled row lies. It is one of two tests that take a path argument (defaulted to the repo-relative plist), so run it from the repo root. `panel_palette_test` is the other, and covers the PAGE's two tones (`src/PanelPalette.h`, pure for the same reason): that the default ink/paper pair is byte-for-byte what this repo hardcoded before the dial existed, that every road not involving typing arrives back at it, that the 0..255 ramp between them stays integer-truncated and non-degenerate (this is the 2-bit gray handling -- the intermediate levels are LERPED, never tabulated), that every way a Settings.app hex field can be wrong falls back per-field rather than blanking the page, that no named preset drops under 7:1 or duplicates another, and -- reading the shipped `Root.plist` -- that each preset row's printed contrast figure matches the tones that row actually selects. Every failure mode here is a wrong COLOR, which no compiler and no other test in this repo can see. `panel_source_test` covers WHERE each polarity's tones come from (`src/PanelSource.h`, pure for the same reason `panel_palette_test`'s subject is), and it exists because `chip_tint_source_test.py` guarded that area and passed straight through the owner's P1 of 2026-08-23 -- it asserts a delegation CHAIN and never a tone, and one reader over a store with two writers is still one reader. So this one asserts BYTES: that a named preset owns both appearances whatever stale hex the fields hold, that Custom takes each polarity's own two fields independently, that a light-mode ink pick leaves the dark page's tones AND its phosphor alone, that a gun moved in dark mode leaves the light page's chosen ink alone (the reported bug, which moved a page from 323D47 to 6E0500), that both hold across load, four appearance switches and a relaunch in either editor order, that the claim which freezes the other polarity is ONE-SHOT, and that a frozen phosphor follows `migratePreset` rather than reviving a retired row. Its companion `panel_source_test.py` is source-level and pins what no byte can see -- that the two editors still write only their own polarity's keys and still take the shared claim before the shared preset integer moves. Both fail against the pre-fix tree (3 and 20 failures); together they also pin the pad's Accessible ladder at BOTH of its resolution points, which is S-021. `phosphor_grain_test` covers the screen-grain field (`src/PhosphorGrain.h`, pure for the same reason): that OFF is BIT-EXACT off rather than nearly-off on every coverage, that the field can only ever darken (a multiplier above 1 is the additive lift that produced both the page-flash and the gray-background reports), that the cell stays `kCellPx` square, that the dial is linear across the offered strengths, that Vignette is a no-op at the exact center and still leaves a readable corner at the top of the dial, and that Mottled carries real low-frequency structure without adding a net dimming -- measured on BLOCK means, since per-pixel spread cannot tell a blotchy field from an even one. It also pins the three things added after the owner started tuning it: that a mottle DEPTH of 0 is bit-exact Even at every cell count (and leaves Vignette+Mottled exactly Vignette), so the bottom of that dial is off rather than a silent floor; that every offered depth and cell count differs from its neighbour, or a settings row is decoration; and that no offered strength drops any page below the 7:1 contrast floor, swept against five palettes including the two tightest -- which is exactly what the old global sigma shipped at the since-removed 10x, where P11 Blue and P22R Red fell to 5.6:1. `letterpress_test` and `scanlines_test` hold the 2026-08-22 doctrine dials (`src/Letterpress.h` light, `src/Scanlines.h` dark, both pure for the same reason) to the same bar: OFF bit-exact per mode, darken-only, ladder monotone with every rung distinct, and the 7:1 floor swept on five palettes including the tightest (Latte light 7.06:1 for letterpress -- the paper-budget clamp is what holds it -- and P11/P22R dark for scanlines). Letterpress additionally pins edge-band correctness on a synthetic glyph (the squeeze ring darkens the ink rim well below the stroke interior, flat ink and flat paper beyond the band stay untouched but for their own noise terms, and the deboss shadow falls on the top wall only); scanlines additionally pin that the box-integrated field has no long-period beat at the phone's fractional 2.39 px pitch (the ST-008 lesson), that the structure self-attenuates to near-uniform at 1:1, that bloom only ever SPARES a row, that the folded mottle carries block-mean structure without net brightening, and that `combine(rowTransmission)` is exactly `multiplierAt` -- the cache split HalDisplay ships. `test_text_entry.sh` drives Settings > Device owner and asserts the persisted `settings.json`, so it covers the host-keyboard channel end to end; what it cannot cover is the suppression that keeps typed letters off the button map, because it injects below SDL — that half is verified on the phone and written up in [ios/README.md](ios/README.md). `test_note_editor_repaint.sh` is its sibling for the MULTI-line case and asserts something a file cannot show: it compares the FRAME before a `TYPE` with the frame after it, in a fresh Create Note, with `CROSSPOINT_SIM_HOST_KEYBOARD` at both 0 and 1. It exists because firmware B-028 was invisible to every file-contents assertion — the note editor drained the typed text into its buffer and saved it perfectly while never repainting once, because its debounced `requestUpdate()` sat below an `if (panelHidden) return;` that is taken exactly when a phone's software keyboard is up. Two byte-identical BMPs were the only observable. `test_sleep_wake.sh` pins the deep-sleep wake edge-latch: a 1 ms synthetic POWER tap during sleep must relaunch the process (the sleep loop consumes an edge set by `injectButtonDown`, because a fast tap's down and up can both land in one pump burst and leave no level to poll). `build_identity_test` proves the split-brain guard aborts — see "One device macro, one definition" below. `wifi_host_test` covers the branch `WiFiClass` takes when a real radio is behind it — the iOS path — and guards that the desktop env-var fakes are unchanged by the hook's presence. `http_dispatch_test` pins that the mock-root and `file://` fixture paths still beat the network, and in that order, now that a second transport exists. `restart_semantics_test` pins the two silent ways `ESP.restart()` can go wrong: claiming a POWER press it never received, and leaving an input script in place so an automated run restarts forever. `read_aloud_channel_test` pins the read-aloud page channel's hand-off contract (one consume per publish, latest wins, `publish(nullptr)` is the stop-speech clear); `read_aloud_core_test` covers every transition of the read-aloud state machine — most load-bearing: a canceled utterance never turns a page, and highlight/tap offsets are UTF-8 bytes (the test page has curly quotes and accents precisely so a character-counting regression fails it). `test_read_aloud_capture.sh` pins the firmware capture end-to-end against a tiny GENERATED two-chapter EPUB (the seed book's mono-file chapter takes tens of seconds to paginate, which made it timing-flaky here): boot page published, a `QTAP` page turn reaches a different page, multibyte survives, exit clears, and the channel stays silent without the env var. `task_registry_test` pins the FreeRTOS shim's name dedupe against `vTaskDelete`: the registry used to keep pointing at a freed handle, so the create/delete/create sequence the iOS in-process reboot performs handed the caller freed memory. It asserts behaviourally (did a thread actually spawn?) because the allocator reuses the freed block, so pointer identity does not distinguish the two. `gen_cmake_sources_test.py` exists because `cmake/CrossPointSources.cmake` is the only thing telling the iOS build which firmware sources to compile: the generator resolved the compile database's relative `file` paths against the process cwd instead of each entry's own `directory`, so running it from anywhere but the firmware checkout filed all 125 firmware TUs as simulator sources, wrote an empty `CROSSPOINT_FW_SOURCES`, and exited 0. The test pins cwd-independence plus every refusal (empty, zero-firmware, zero-simulator, wrong tree, stale, partial, no include dirs, malformed JSON) and that a refused run leaves the existing file byte-identical. `device_truth_test` covers S-001's last four reversals (`src/SimulatorDeviceTruth.h`, pure for the same reason PadPalette is): the flag spellings, that anything unrecognised falls back to the HISTORICAL answer rather than inventing a state, the panic report's field order against the firmware's own writer, and — the one that matters most — that the panic latch is ONE-SHOT. It consumes `CROSSPOINT_SIM_PANIC` on first read, because the desktop reboot is `execvp` and hands `environ` to the child, so without that a single injected panic would route every boot into `CrashActivity` forever and the crash screen would have no exit. `cpz_container_test` covers the CPZ1 container the HAL's file layer opens transparently (`src/SimCompressedFile.h`, the writer being `tools/compress_seed_fonts.py`), and it drives the REAL writer through `std::system` rather than reimplementing its packing -- two implementations of one layout that agree with each other and not with the spec is the drift worth catching. Byte-exact sequential round trip at six chunk sizes that straddle block boundaries, 400 random `(offset, length)` reads, a payload shorter than one block, reads at and past EOF, five ways a header can be internally inconsistent (each of which must fail the OPEN, because falling back to the raw bytes hands container headers to the font loader as glyph data), a non-monotonic index, and a damaged block -- which must come back as -1, never as a short read, because a short read looks like end of file to `SdCardFont`. Every failure mode here is a font that does not load, which is a blank page with successful renders in the log. `sha256_test` pins the mbedtls shim to the published FIPS-180-4 vectors, including the million-'a' case and a chunked digest matching the one-shot; that shim WAS a fake (`digest[i % 32] ^= input[i]`, returning success), and nothing but a known-answer vector can see such a thing — the signature, the length and the determinism are all indistinguishable from a real digest.

## Architecture

The simulator is a collection of host-side reimplementations of the firmware's hardware abstraction layer (HAL) and its Arduino/ESP-IDF dependencies. Each `Hal*.cpp/.h` here corresponds to a `Hal*` class in the firmware's `lib/hal/`, and **must keep the same public surface** or the firmware will not link.

**The HAL stub rule.** When the firmware adds a new method to a HAL class and calls it, the simulator fails to link until a matching stub is added to the corresponding `Hal*.cpp` here. Most additions are one-line no-ops. This is the single most common reason a simulator build breaks after pulling firmware updates.

It runs the other way too, and that direction costs a firmware change: a capability the *host* has and the device does not (the keyboard channel — `setTextEntryActive` / `consumeTypedText`) has to exist on both sides, as a real implementation here and an inline no-op in the firmware's `lib/hal/HalGPIO.h`. Simulator-only methods the firmware never calls (`injectButtonDown/Up`, `injectTypedText`, `pumpHostTextInput`) need no counterpart and must not gain one.

**Why the simulator's design has the shape it does** (the non-obvious parts):

- **SDL on main thread.** macOS requires all SDL calls to come from the main thread, but firmware drives rendering from a FreeRTOS render task. The split lives in [src/HalDisplay.cpp](src/HalDisplay.cpp): `refreshDisplay` (background thread) converts the 1bpp framebuffer to ARGB and sets an atomic `pendingPresent` flag. `presentIfNeeded` (called from `simulator_main` on the main thread) does the actual SDL upload and present. Do not call SDL render functions from anywhere else.
- **Orientation rotation lives in two places.** The firmware's renderer rotates content into the landscape framebuffer (90 CCW for `Portrait`). The simulator undoes that with `SDL_RenderTextureRotated`. If you change one, change the other. The dst rect is landscape-shaped and center-offset because the rotation happens around the dst center.
- **HiDPI / dithering.** `SDL_WINDOW_HIGH_PIXEL_DENSITY` plus `SDL_SetRenderLogicalPresentation`, and a scale mode set on the texture (SDL3 replaced the global `SDL_HINT_RENDER_SCALE_QUALITY` hint with a per-texture setting, so it must come *after* `SDL_CreateTexture`). Without these, Bayer-dithered grays render as harsh black/white stripes on Retina.
- **Presentation policy is keyed on intent, not platform — and on DIRECTION.** `CROSSPOINT_SIM_PIXEL_EXACT` selects `INTEGER_SCALE` + `SCALEMODE_NEAREST`; without it the build gets letterbox + linear filtering. Linear is right at 1:1, where Bayer dither averaging to gray is what e-ink actually looks like; exact pixels are right wherever the panel is scaled **up**, because a fractional scale or a linear filter greys the dither and every rendering judgment made against it is a lie. **Below 1x that argument inverts**, and the code applied it in both directions by omission until 2026-08-15. A 3x render scale does not fit any iPhone's width (1584 framebuffer px against 1260 on an iPhone Air), so the phone MINIFIES — nearest-neighbour then simply does not draw 324 of every 1584 columns, the panel's four grey levels stay four instead of blending into the ~17,000 the geometry could give, and the selection dither's regular grid beats against the sampling lattice at a 21-device-pixel period. That beat is ST-008, and it is one reason the 3x tier was cheap to give up when it was dropped on 2026-08-23. `panelScaleModeFor()` now returns `SDL_SCALEMODE_LINEAR` below 1x and the unchanged `kPanelScaleMode` at or above it; the `[panel]` log line prints which is live. Measured beat amplitude on the `LightGray` fill at 0.7955: nearest 8.14 levels, bilinear 1.55, an exact box filter 0.37, and 0 at 1:1 — which is also why build 75 (2x, presented at exactly 1.0) could not show it and build 76 (3x) must.
- **`SimulatorOverlay` for chrome outside the panel.** [src/SimulatorOverlay.h](src/SimulatorOverlay.h) is a free hook `presentIfNeeded` calls, deliberately *not* a `HalDisplay` method — the HAL's public surface must mirror the firmware's, and on-screen chrome has no analog on real hardware. The callback runs with logical presentation disabled and receives the real output size, so it can paint the letterboxed margins the panel's logical space cannot reach. `requestPresent()` exists because an e-ink firmware presents rarely, so overlay state changes would otherwise not appear until the next page render.
- **Panel palette + reserved pad band.** The 1bpp/AA framebuffer presents as tinted ink on tinted paper. The pair is a **dial**, not a constant: definitions, presets, hex parsing and the interpolation live in [src/PanelPalette.h](src/PanelPalette.h), the live pair is two atomics in [src/HalDisplay.cpp](src/HalDisplay.cpp), and hosts set it through `SimulatorOverlay::setPanelPalette` (the iOS Settings app; `CROSSPOINT_SIM_PANEL_{INK,PAPER}_{LIGHT,DARK}` on desktop). Both polarities default to what this repo always hardcoded — 2D2D2D-on-FBFBF9 light, E0E0DE-on-121212 dark — so a build that never calls the setter is pixel-identical. The dark ramp's ink→paper direction IS the inversion (no separate 255−level flip), and every intermediate gray is LERPED from the two ends, so the 2-bit gray targets need no table and a custom pair still grades — do not hardcode an intermediate. The pad's field is the paper tone (`padpalette::makePaletteOn`), so the pad follows a custom paper and its printed contrast ratios become approximate. `SimulatorOverlay::setBottomInset` reserves a bottom band for chrome: the panel then fits TOP-ALIGNED above the band (manual placement, integer scale preserved under `CROSSPOINT_SIM_PIXEL_EXACT`) and publishes its bottom edge via `panelBottomPx()` — the iOS pad anchors to it. Desktop keeps inset 0 and the plain letterbox path.
- **The sleep loop draws, and that is where an animation can run without
  delaying sleep.** `HalGPIO::startDeepSleep` is the firmware's terminal loop,
  and `SimulatorOverlay::stepPowerOffCollapse()` is stepped from the bottom of
  it: the firmware has already handed over, every wake check runs first, and a
  wake mid-animation abandons it on the same iteration. Anything else that wants
  to draw *after* the app is asleep belongs there and nowhere else --
  `presentIfNeeded` is never called again. Note it also has to run its own
  due-screenshot check, or the moment it exists for is the one moment headless
  QA cannot photograph.
- **The sleep screen is drawn in LIGHT polarity even when the reader was dark**
  (measured 2026-08-23: `inverted=0`, paper F9F9F8, on a run whose every page
  turn built a scanline field). So "is the page dark" asked at sleep time
  answers about the sleep screen, not about the tube. `lastReadingDarkGround` is
  latched on every non-sleep present for exactly this reason.
- **Screen grain is a PRESENT-TIME pass, in device pixels, drawn last.** The
  page's flatness is not a palette problem -- a real tube's screen is a settled
  layer of phosphor crystals with uneven coverage. [src/PhosphorGrain.h](src/PhosphorGrain.h)
  is the model (pure, host-tested, for the same reason PanelPalette is: every
  failure mode is a wrong picture). Three things about the placement are
  load-bearing. It is generated at the OUTPUT size and drawn 1:1, not baked into
  the 1bpp->ARGB conversion, because the panel is minified to 0.7955 on a phone
  and a regular field written into the framebuffer beats against that resample
  -- the ST-008 moire, measured at 8.14 levels. It composites with
  `SDL_BLENDMODE_MOD` and can only DARKEN, because coverage variation is a
  deficit against an ideal screen and because an additive pass over a dark
  ground is exactly the page-flash and gray-background bug class. And it goes on
  LAST -- after the OVERLAY as well, over the whole app surface rather than just
  the page (owner 2026-08-18: it is one sheet of glass, and texturing only the
  panel left a grainy rectangle on a clean ground, which no physical screen
  has). Everything under it -- the beam's swept band, the accumulator's trail,
  the pad, the bezel -- is light the coverage then gates. Owner
  ruling 2026-08-18 rules out the alternatives: no bloom or halation (costs
  legibility), no scanlines (a raster artifact, not a phosphor one). Full
  writeup: [docs/phosphor-grain.md](docs/phosphor-grain.md).
- **Inversion changes re-present from a cached frame.** `setInverted` posts an atomic reconvert request that `presentIfNeeded` (main thread) services from the cached BW base and grayscale AA planes — inversion applies at 1bpp→ARGB conversion time, and e-ink firmware refreshes rarely, so without this a dark-mode flip would wait for the next page turn. `SimulatorOverlay::setPanelDark` is the single polarity entry point: the iOS harness follows the system appearance through it, and `CROSSPOINT_SIM_DARK=1/0` forces either state for headless runs. Book covers/images render as negatives in dark mode; accepted for now.
- **POSIX fds, not std::fstream, in [src/HalStorage.cpp](src/HalStorage.cpp).** This was a deliberate rewrite. fstream's separate get/put pointers, eofbit-blocks-seek behavior, and write-only seek restrictions caused several silent-corruption bugs. Do not reintroduce fstream here. All paths are prefixed with `./fs_` so the simulated filesystem stays sandboxed under the binary's working directory; `/books/` on the SD card maps to `./fs_/books/`. Directory iteration skips only `.` and `..` — dotfiles ARE returned, matching SdFat on device (an earlier version of this file claimed all dot-entries were skipped; the firmware does its own hidden-file filtering, and the Manage Files screen deliberately lists them).
- **Seed fonts are block-compressed, and `HalFile` is where that is hidden.**
  `.cpfont` stores 2-bit glyph bitmaps raw, so the iOS bundle installed 118 MB
  of the 1x+2x tiers that its own zip had squeezed to 34 MB for the download.
  [tools/compress_seed_fonts.py](tools/compress_seed_fonts.py) rewrites each file
  as a CPZ1 container and [src/SimCompressedFile.h](src/SimCompressedFile.h)
  sniffs its magic on every READ-ONLY open, serving `size()`, the seeks,
  `position()`, `available()` and `read()` from the payload's logical space and
  inflating one 32 KB block at a time. Measured: 117,654,860 -> 34,837,381
  installed, download +1.4 MB. It sits at the file layer and NOT in the format
  because `.cpfont` is random-access (prewarm seeks per glyph run, the overflow
  ring per glyph), because `HalFile` is host-only by definition, and because the
  filename survives -- `SdCardFontRegistry` still finds the family, WebDAV still
  serves the real bytes at the real length. A container whose header will not
  parse FAILS THE OPEN and a block that will not inflate returns -1, never a
  short read: the alternative is a blank page with successful renders in the log.
  `-DCROSSPOINT_IOS_COMPRESS_SEED_FONTS=OFF` bundles the raw tree, which is what
  the desktop canary keeps exercising. Full writeup, including the three
  alternatives that were priced and rejected:
  [docs/seed-font-compression.md](docs/seed-font-compression.md).
- **FreeRTOS shim.** [src/freertos/](src/freertos/) maps `xTaskCreate` to `std::thread`, task notifies to a condvar + counter, and `SemaphoreHandle_t` to `std::recursive_mutex`. A `thread_local SimTaskHandle*` lets each task thread find its own handle.
- **`_exit(0)` not `return 0`, on desktop.** [src/simulator_main.cpp](src/simulator_main.cpp) ends with `_exit(0)` after `SDL_Quit()` to skip C++ global destructors. The render task is `[[noreturn]]`, so running destructors while it is mid-render races and produces a "quit unexpectedly" dialog. Keep this. iOS is the one exception — it reports a self-terminating process as a crash, so that build returns normally.
- **Time uses `steady_clock`.** `millis()` / `micros()` in [src/Arduino.h](src/Arduino.h) deliberately use `steady_clock`, not `system_clock`, so wall-clock changes do not perturb timing.

**Host-specific code paths:**

- MD5: [src/MD5Builder.h](src/MD5Builder.h) is a thin dispatcher that auto-selects the implementation via `#ifdef __APPLE__` / `#elif __linux__`. [src/MD5Builder_mac.h](src/MD5Builder_mac.h) uses CommonCrypto; [src/MD5Builder_linux.h](src/MD5Builder_linux.h) uses OpenSSL. No downstream swapping is needed - just include `MD5Builder.h`.
- Web server shims: [src/WebServer.cpp](src/WebServer.cpp), [src/WebSocketsServer.cpp](src/WebSocketsServer.cpp), and [src/NetworkClient.cpp](src/NetworkClient.cpp) expose firmware port 80 as `http://127.0.0.1:8080/` and port 81 WebSockets as `ws://127.0.0.1:8081/`. `CROSSPOINT_SIM_HTTP_PORT` moves the pair together when either port is occupied. Current CrossPoint builds compile their firmware-owned `CrossPointWebServer.cpp` and `WebDAVHandler.cpp` against these shims; `CROSSPOINT_SIMULATOR_PROJECT_WEBSERVER` disables only the legacy reduced substitute in this library. Both servers bind **loopback on desktop and all interfaces on iOS** — a phone's file-transfer screen exists to be reached from another machine, a developer's laptop should not publish a file browser to the office — and `CROSSPOINT_SIM_BIND_ALL` forces either way.
- `ESP.restart()` reboots rather than doing nothing, which is how the firmware's `silentRestart()` (every file transfer and font download ends in one) gets exercised at all. On iOS that is the in-process `longjmp` reboot, so the firmware's `RTC_NOINIT` globals survive exactly as RTC memory does on hardware; on desktop the reboot is `execvp` and those globals do NOT survive, so it is **opt-in** via `CROSSPOINT_SIM_FIRMWARE_RESTART=1` until someone verifies it. It deliberately does not reuse `rebootAsPowerWake()`, which would have the firmware believe POWER was pressed.
- Build flags: macOS gets architecture-correct SDL compiler and linker flags
  from `pkg-config --cflags --libs sdl3`, so the same sample works on Intel and
  Apple Silicon.
  Linux/WSL additionally links OpenSSL with
  `-lssl -lcrypto -Wno-deprecated-declarations` (OpenSSL 3.x deprecates
  `MD5_*`). See
  [sample-platformio-macos.ini](sample-platformio-macos.ini) and
  [sample-platformio-linux-wsl.ini](sample-platformio-linux-wsl.ini). Keep
  both in sync when build flags change. Native Windows is not supported, WSL
  is.
- Mac App Store packaging: [packaging/macos/Info.plist.in](packaging/macos/Info.plist.in)
  is the single source of truth for the bundle's privacy purpose strings, and
  [packaging/macos/package_macos_app.py](packaging/macos/package_macos_app.py)
  builds, patches, and verifies bundles against it (also exposed as the
  `package_macos_app` PlatformIO target). The `NS*UsageDescription` keys are
  required even though the simulator only calls `SDL_Init(SDL_INIT_VIDEO)`:
  Apple's static scan sees the camera and Bluetooth APIs referenced by the
  linked SDL2 library and rejects the upload with ITMS-90683. Removing them
  breaks the next App Store submission. If a future upload flags another key,
  add it to the template and to `REQUIRED_PRIVACY_KEYS` so `verify` catches it.
  **The app icon is generated, not checked in.**
  [packaging/macos/make_icns.py](packaging/macos/make_icns.py) derives the
  `.icns` from the iOS artwork
  (`ios/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png`) at build time, so
  the two platforms cannot drift apart — and it is not a straight copy, because
  iOS ships a full square that the OS masks while macOS must ship its own
  rounded, inset shape with transparent corners. It is pure Python (no `sips`
  or `iconutil`) so a Linux CI box builds the same icon a Mac does. `verify`
  now fails on a bundle with no icon, for the same reason it fails on a missing
  purpose string: App Store review rejects both.
- **"deploy mac apps"** means all THREE local bundles, rebuilt and installed
  into `/Applications`: `CrossPointX3`, `CrossPointX3-2x` (the same X3 binary
  with `CROSSPOINT_SIM_WINDOW_SCALE=2` in `LSEnvironment`) and `CrossPointX4`
  (the `simulator` env). Owner's phrase, 2026-08-19.
  [packaging/macos/deploy_mac_apps.sh](packaging/macos/deploy_mac_apps.sh) does
  it, and refuses to install a bundle that builds but does not boot. This is NOT
  the App Store path -- these are unsigned, for this Mac. The reason it exists:
  those three sat at build 1 from 2026-08-07 for twelve days while every palette,
  the grain and the shortlist landed, and the Mac was being judged against them.
- TestFlight deploys: [packaging/macos/deploy.sh](packaging/macos/deploy.sh)
  runs build → bundle → verify → embed dylibs → sign → `productbuild` →
  `altool` → tag, and must run on macOS from a GUI Terminal session.
  `codesign` needs the login keychain, so firing it from a sandboxed agent
  shell fails with `errSecInternalComponent` — route through
  [packaging/macos/deploy.applescript](packaging/macos/deploy.applescript),
  which hands the command to Terminal.app. Build numbers auto-bump from the
  last `macos-build-N` tag because Apple silently rejects a duplicate. A
  sandboxed build cannot spawn `/usr/bin/curl`, so `SimHttpFetch`-backed
  network flows do not work on TestFlight.
- A `.app` launched from Finder starts with its working directory at `/`, so
  [src/HalStorage.cpp](src/HalStorage.cpp) resolves the simulated SD card to
  `~/Library/Application Support/<AppName>/fs_` when the executable sits inside
  a bundle. Command-line dev builds are unaffected and keep using `./fs_`.
- Linker stubs: [src/firmware_link_stubs.cpp](src/firmware_link_stubs.cpp) provides symbols the firmware expects from other translation units (uzlib checksums, HWCDC Serial shim, LUT stubs). When the firmware adds a new global-extern symbol with no simulator counterpart, add its stub here.

## Device profiles and input mapping

[src/BoardConfig.h](src/BoardConfig.h) selects X4 by default,
`SIMULATOR_DEVICE_X3` for X3, `SIMULATOR_DEVICE_X4_PRO` for X4 Pro, and
`SIMULATOR_DEVICE_STICKY` for Seeed Sticky.
`SIMULATOR_DISPLAY_UC8179` and `SIMULATOR_DISPLAY_UC8279` select per-batch
controller revisions without changing a device's geometry or capabilities.
Keep the reported board and controller aligned with the firmware SDK. X4 Pro
uses the same 800x480 display geometry as X4 but adds touch, a capacitive Home
key, frontlight state, inversion, and an RTC. Sticky also uses 800x480 and adds
touch, RTC, and tilt without a Home key or frontlight.

**One device macro, one definition — and it goes on the LIBRARY.** The iOS
build is two CMake targets: `crosspoint_core` (firmware + HAL, ~155 TUs) and
`CrossPointX3` (the harness, 7). The X4 default in `BoardConfig.h` is *silent*,
so a device macro that reaches only one target produces a binary whose halves
disagree, compiles clean, and fails somewhere far away. It has happened twice:

| Define | Set only on the app target | What shipped |
|---|---|---|
| `CROSSPOINT_RENDER_SCALE=2` | ~15 TestFlight builds | 1x glyphs while the pbxproj read 2x |
| `SIMULATOR_DEVICE_X3` | builds 1–27 | firmware built an X4: no RTC, so every calendar sleep screen fell back to the stock logo screen; 800x480 panel under a harness laying out 792x528 |

Every cross-cutting define therefore belongs on
`target_compile_definitions(crosspoint_core PUBLIC ...)`, never `PRIVATE` on
the app target. Three guards enforce it, and none of them is a reviewer
remembering this paragraph:

1. **Configure time** — [ios/CMakeLists.txt](ios/CMakeLists.txt) `FATAL_ERROR`s
   if the app target carries any define the core does not. A genuinely
   harness-only define goes in `CROSSPOINT_HARNESS_ONLY_DEFINES` *with its
   reason*.
2. **Boot** — the harness calls `verifyBuildIdentityMatchesCore()`
   ([src/SimulatorBuildIdentity.h](src/SimulatorBuildIdentity.h)), comparing
   device, logical geometry and render scale across the target boundary, and
   aborts on any difference. A healthy launch logs
   `[BUILD] iOS harness and firmware core agree: X3, 792x528 logical, 2x render scale`.
   That log line is the fastest way to confirm what a build actually is.
   `tests/build_identity_test.cpp` proves the abort fires per field.
3. **Deploy** — [ios/testflight.sh](ios/testflight.sh) greps the generated
   project for `SIMULATOR_DEVICE_X3` before archiving, so a wrong-device build
   cannot reach TestFlight.

The silent `#else` default in `BoardConfig.h` stays (owner ruling 2026-08-06):
making an unnamed device an `#error` would break the firmware's `[env:simulator]`
and every upstream consumer that never named a board.

`HalGPIO::update` owns the SDL event pump for the whole simulator, do not poll SDL events elsewhere. If another layer needs to observe events (the iOS harness does), use `SDL_AddEventWatch` — it sees events as they are queued without consuming them, so neither side steals from the other. Scancodes map to button indices `BTN_BACK=0` through `BTN_POWER=6`. `SDL_EVENT_QUIT` sets the `quitRequested` atomic that `HalDisplay::shouldQuit()` reads.

**"Side buttons" vs "front buttons" — get this straight before moving any
button UI; it was mixed up four separate times over 2026-07-31→08-01.** The
vocabulary is the firmware's (`MappedInputManager`): the FRONT cluster is the
remappable Back/Confirm/Left/Right pad, and the SIDE pair is the physical
up/down rocker that page-turns in the reader (`Button::PageBack`/`PageForward`,
swappable via `SETTINGS.sideButtonLayout`). Whether that side pair is actually
on the device's EDGE differs per board — `HalGPIO::hasEdgeSideButtons()`
(`src/HalGPIO.cpp:784`) is the authority: TRUE for X3/X3-UC8279/X4 Pro, FALSE
for X4. So an on-glass button pad must not draw an edge rocker for an X4
profile, and "up/down" in a prompt usually means the page-turn side pair, not
front-cluster arrows. When a layout ask says "move the buttons", confirm which
cluster and which board profile before touching geometry.

**`SDL_PushEvent` cannot drive `SDL_GetKeyboardState`** — measured, not assumed. A pushed key event reaches the queue, so edge reads (`wasPressed`/`wasReleased`, which `update()` sets straight from the event) work; but SDL's internal keyboard state array is only written on the real-input path, so level reads (`isPressed`, `anyButtonHeld`, `powerHoldDuration`) stay false for injected keys. `powerHoldDuration()` returns 0 at its early exit, so long-press power-off never fires. Anything driving the simulator synthetically must either use the `CROSSPOINT_SIM_INPUT_SCRIPT` path (which writes `syntheticButtonDown[]` directly) or extend `HalGPIO` with a live injection API. See [ios/README.md](ios/README.md).

**Host keyboards reach the firmware's text fields.** The X3 has no keyboard, so
firmware text entry pecks characters out of an on-screen grid; `HalGPIO` also
carries a real host keyboard into that same field — the Mac's, an iPhone's
on-screen keyboard, a Bluetooth keyboard paired to the phone. The firmware
opens and closes the channel (`setTextEntryActive`, a no-op on device), and
while it is open the scancode→button map is suspended for everything except
Escape and the arrows — without that, typing a Wi-Fi password would press POWER
on every `p` and sleep the device on every `s`. `TYPE:<text>` in
`CROSSPOINT_SIM_INPUT_SCRIPT` is the scripted typist (`\b` backspace, `\n`
commit, `\e` cancel; `;` cannot appear in the text). Full behavior table and
what was verified where: [ios/README.md](ios/README.md).

**The software keyboard can be put away, and asked back.** The firmware raises
it by opening a field and lowers it by closing one; nothing else could, and on
iPhone — unlike iPad — the system keyboard carries no dismiss key, so a field
open meant ~40% of the screen gone with no way out but leaving the screen.
`HalGPIO::setHostKeyboardVisible` is the owner's override on top of the
firmware's flag, simulator-only and with no device counterpart. The decision
lives in [src/HostKeyboardState.h](src/HostKeyboardState.h) (host-tested) rather
than as an if-ladder in `pumpHostTextInput`, because all three of its failure
modes are silent: suppression that outlives its field is an invisible
preference, a lower done behind `pumpHostTextInput`'s back can never be undone,
and a raise issued while SDL already believes text input is active is a no-op.
Suppression clears on **both** text-entry edges, so it can never go sticky.

The controls are iOS-side: a dismiss bar riding on the keyboard
([ios/CrossPointKeyboardBar.mm](ios/CrossPointKeyboardBar.mm), attached to SDL's
hidden `SDLUITextField` — SDL has no accessory API, so the field is found by
public traversal from the `SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER` window), plus a
wordless one-cell chip centred in the pad's bottom row, drawn whenever a field
is open. ONLY the chip toggles it -- an off-pad tap does nothing, however empty
that part of the screen looks.
`SDL_EVENT_SCREEN_KEYBOARD_HIDDEN` feeds iPad's own dismiss key into the same
state. **`SDL_HINT_RETURN_KEY_HIDES_IME` must stay unset** — it makes Return
call `SDL_StopTextInput`, which would dismiss the keyboard on every line break
in a multi-line field.

**The keyboard OVERLAPS the page; it does not shrink it** (owner ruling
2026-08-10, replacing the panel half of the 2026-08-09 clearance band).
Reserving the keyboard's height out of the panel cost it an integer scale —
about 40% of the page on a phone — to uncover a lower edge not worth that much
text. The tablet's bottom row still lifts clear, because its pad sits in the
margins beside the page rather than in a band below it.

**An overlay state change needs `SimulatorOverlay::requestPresent()`.** Learned
again here: `CrossPointIOS_setKeyboardHeight` stored the new height and
presented nothing, so the keyboard-clearance relayout only took effect on
whatever page the firmware happened to render next — the panel did move, just
never when the keyboard did. Anything that changes what the overlay draws has to
ask for a present, because an e-ink firmware may not render for minutes.

**Return is the exception, and it is decided per field.**
[src/TextEntryKeyRouting.h](src/TextEntryKeyRouting.h) holds the whole rule: in
a single-line field Return is `BTN_CONFIRM` (Select on the on-screen keyboard,
the key that types the highlighted character) and Cmd/Ctrl+Return commits; in a
multi-line editor it is the other way round, so Return breaks the line and
Cmd/Ctrl+Return still reaches the panel's pick. The activity says which it
opened — `setTextEntryActive(true, HalGPIO::TextEntryLines::Multi)`. Both
inversions of this have shipped as bugs; there is a truth-table test
(`tests/text_entry_enter_test.cpp`) precisely so the next fix to one of them
does not silently reintroduce the other.

**A scripted pass is not evidence about input routing.** `TYPE` and the button
actions write the typed queue and `syntheticButtonDown[]` directly — they enter
*below* SDL and never meet the scancode gate, so both Return bugs above passed
every scripted run while a human pressing the same key got the wrong thing. Use
`RAWKEY:<NAME>[:<holdMs>]` to push a real `SDL_EVENT_KEY_DOWN`/`UP`
(`RAWKEY:RETURN`, `RAWKEY:CMD+RETURN`, also `ESCAPE`/arrows/`BACKSPACE`/`P`).
It is the only script action that exercises the gate. It still cannot fake a
*level*: per the `SDL_PushEvent` note above, a pushed key produces edges but no
`SDL_GetKeyboardState` entry, so long-press behavior needs `injectButtonDown`
or a human.

**Read-aloud page channel.** The same host-capability split as the keyboard
channel, pointed the other way: `readAloudCaptureWanted()` /
`publishReadAloudPage()` are firmware-facing (inline no-ops on device — the
reader captures the displayed page's text and word rects only when asked, and
publishes `nullptr` on exit), while `setReadAloudCaptureWanted()` /
`consumeReadAloudPage()` are the simulator-only consumer half. One consumer
per build: `CROSSPOINT_SIM_READALOUD_LOG=1` turns on an env-gated logger in
`simulator_main.cpp` (desktop only) that both requests capture and prints
every publish — the headless way to audit the firmware's capture quality
(`=2` additionally dumps full text and every rect). The capture-wanted flag
must be set BEFORE the first `loop()` iteration — a fast book renders its
first page inside it, and a lazily applied flag misses that page (both
consumers were bitten; both now seed the flag pre-loop). The
iOS harness is the real consumer (`ios/CrossPointReadAloud.mm` speaks pages
via AVSpeech). `HalGPIO::queueButtonTap` exists for this feature and any
future harness automation: it schedules a synthetic press/release that fires
inside `update()`, because an edge injected from the per-frame hook lands
after `loop()` and is wiped by the next `beginFrame()` unseen.
`QTAP:<BUTTON>[:<holdMs>]` in `CROSSPOINT_SIM_INPUT_SCRIPT` drives that exact
API from a script, which is how `tests/test_read_aloud_capture.sh` pins the
page-turn loop headlessly. Page-forward on this firmware is the RIGHT front
button (`ReaderUtils::detectPageTurn`), not DOWN. Design and
work-package status: [.claude/PLAN-tts-read-aloud.md](.claude/PLAN-tts-read-aloud.md).

**The desktop has a settings file, and it is the Mac's Settings app.**
`settings.json` sits BESIDE the simulated card -- `./settings.json` for a
command-line build, `~/Library/Application Support/<AppName>/settings.json` for
a Finder-launched `.app` -- written with the shipped defaults on first run,
using the SAME KEYS as iOS, and re-read about once a second so an edit applies
without a relaunch (`src/SimulatorSettingsFile.h` for the model and its test,
`src/SimulatorSettingsWatch.cpp` for the watcher, compiled to nothing on iOS).
Owner ruling 2026-08-19: a packaged `.app` could otherwise only take these
through `LSEnvironment` baked in at build time, so changing the page color meant
rebuilding the bundle. It resolves the palette through `panelpalette::resolve`
and derives the glow from the preset exactly as `pollPanelGlow` does on the
phone, so the two platforms cannot disagree about what a CRT palette implies.

**`CROSSPOINT_SIM_AS_SHIPPED=1` seeds the dials the iOS app actually ships
with**, in one switch, and it is the right way to start any attempt to reproduce
an owner report. The desktop seeds every dial at its HISTORICAL value --
deliberately, so the canary and every headless capture stay byte-identical to
what this repo always drew -- while the app ships CRT White with letterpress and
scanlines on, a heavily textured sheet, and a 55 ms beam. Rebuilding that by hand
from a dozen env vars is what went wrong twice inside one bug hunt on 2026-08-19.
It changes no default (unset, every line is a no-op), an explicit env var still
wins because each setter reads its own var last, and it is seeded LAST -- the
first version sat above the ordinary seeds and they overwrote it, so the log said
as-shipped while the grain was still Even/0.10.

**Its numbers are no longer written out by hand, and that is the fix for the way
it kept drifting.** They are `shippedValue` in
[src/SimulatorDials.h](src/SimulatorDials.h) -- one row per dial (name, env var,
settings key, clamp, desktop default, shipped value, flags) driving the desktop
boot seed, the settings watcher and this block from a single definition --
checked against the app's own frozen constants by `tests/dial_table_test.cpp`,
which reads the shipped `ios/` sources as text. Before the table this paragraph
itself was one of the stale records: it said 5 min fade / 67 ms beam / 8 x 0.30
grain while the app had moved to Off / 55 ms / 5 x 0.90, and the seed's own code
said something different again. Adding a dial now means one table row plus one
`case` in `applyDialGroup`, not three hand-synced lists. Full writeup:
`docs/surface-roadmap.md` section 4e.

For repeatable QA, `CROSSPOINT_SIM_INPUT_SCRIPT` schedules synthetic key and
touch-device edges through the same `HalGPIO` state as real SDL input, and
`CROSSPOINT_SIM_SCREENSHOTS` captures renderer output on the SDL main thread.
Keep synthetic held-time timestamps on the `SDL_GetTicks()` clock used by real
keyboard events; the firmware's `millis()` clock has a different origin. The
deep-sleep loop must also process synthetic input. A reboot promotes the
optional `*_AFTER_WAKE` schedules and clears the pre-sleep ones, so automation
cannot enter an infinite sleep/relaunch cycle.

That promotion used to be true only on the desktop. The desktop reboot is
`execvp`, a fresh process, so every static re-initialises for free; iOS cannot
exec in the sandbox and longjmps back into `setup()` in the SAME process, where
`syntheticEventsInitialized` and `screenshotEventsInitialized` were still set and
the promoted schedules were never re-read. **Anything that caches env-derived
state behind a `static bool ...Initialized` must register a reset in
[src/SimulatorRebootResets.h](src/SimulatorRebootResets.h)**, which
`SimulatorLifecycle` runs immediately before the jump — otherwise it works on the
desktop, is dead on the phone, and nothing says so.

**Navigating to a screen from a headless script.** Work these out by watching
`[ACT] Entering activity:` log lines — that is the reliable way to confirm where
a script actually landed, because a screenshot of the wrong screen looks a lot
like a screenshot of a screen that never changed.

- The app boots into **Home**, not the reader. Under the Lyra Six theme Home
  renders the current book's page, so a startup screenshot looks exactly like
  the reader. Do not read that as "the reader is open."
- **But it does not always boot into Home**, and this is the single biggest
  time-sink in scripting these runs. Depending on the state the previous run
  left behind, a launch either lands on Home or resumes straight into the book
  (`Boot -> Reader -> EpubReader`, all within ~5 ms, before any input). The two
  need opposite openings: from Home the first key must be a `DOWN`, while from
  the reader it must be a `BACK` to get to Home first — and a `BACK` sent while
  already on Home *opens* the most recent book instead, landing you in the wrong
  place with a script that looks correct. Do not write the script blind and
  trust it: run it, grep `[ACT] Entering activity:`, and only believe the
  screenshot once the log shows the activity you meant to reach. Four
  consecutive runs were burned on this on 2026-08-03.
- **Open every script with `2000:HOME`, not `BACK`.** This is the fix for the
  above, found on 2026-08-04 after four more wasted runs. `HOME` reaches Home
  from either starting state and is a no-op when already there, so the rest of
  the script can assume Home. `BACK` cannot: it means "up" from the reader and
  "open the last book" from Home, so with a boot path that alternates run to
  run it lands you somewhere different every other time.
- `rm -rf ./fs_/.crosspoint/` does **not** force the Home path — an earlier
  version of this file claimed it did. Verified 2026-08-04: with the directory
  deleted the sim still went `Boot -> Reader -> EpubReader` within 500 ms. It
  clears caches; it does not decide the boot destination.
- **To force a Home boot, set `readerActivityLoadCount` to 1 in
  `fs_/.crosspoint/state.json`.** Booting into the last book is deliberate —
  `main.cpp`'s comment is "The device IS the current book" — and Home exists only
  as an escape hatch for the two cases that need it: holding BACK during boot, or
  a non-zero `readerActivityLoadCount` (the crash-recovery counter). Setting that
  counter is the only lever a headless script has, since it cannot hold a button
  during boot. Clearing `openEpubPath` or `lastSleepFromReader` does NOT work —
  both are checked, then the branch opens the book anyway unless one of those two
  escape conditions holds.
- `HOME` is **not** handled by the reader. It reaches Home from Home (a no-op)
  and does nothing from `EpubReader`, so it is not the state-independent opener
  an earlier version of this file suggested. Force the boot state with the
  counter above and script from Home; do not try to normalise at runtime.
- On Home, **Back** opens the most recently read book and **Confirm/ENTER**
  activates the selected row. Home lists the recent books followed by the menu
  items — on the bunnyfield fork as of 2026-08-04: Browse Files, Recents,
  File Transfer, Manage Files, Settings (no OPDS), Settings last, with no
  wrap-around. Update Library sits ABOVE Settings as of 2026-08-21, so the
  menu is six rows: `DOWN` x16 then `ENTER` reaches Settings regardless of how
  many books are listed, `DOWN` x16 then `UP` then `ENTER` reaches Update
  Library, and x16 `UP` x2 reaches Manage Files. (The old x15 counts predate
  the Update Library row and land one item short.)
- **Scripts that list ALL files (Manage Files) shift by one after the first
  run**: the firmware creates `.crosspoint/` on the test card during boot, and
  in a show-everything list it sorts to row 0 of the root. A DOWN-count written
  against a fresh card acts on the wrong rows in every later run. Recount
  against the current card (`find fs_ -print`) or grep the activity's log
  before trusting the script — this burned a debugging cycle on 2026-08-04
  (the "wrong file moved" was the script, not the firmware).
- Inside the reader **Confirm does nothing** — there is no reader menu. Sending
  `ENTER` while still on Home opens a book, which logs a page render; that is
  the only thing ENTER does on either screen.
- In Settings, `ENTER` on the first row cycles the category tab, so repeated
  `ENTER` + screenshot walks every tab.

```bash
CROSSPOINT_SIM_INPUT_SCRIPT='2000:DOWN;2200:DOWN;…;4800:DOWN;5400:ENTER;6800:ENTER;11500:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS='6300:./qa/tab1.bmp;7700:./qa/tab2.bmp' \
  .pio/build/simulator/program
```

Screenshots are BMP; convert with `sips -s format png in.bmp --out out.png` to
view them.

**Fonts come from two roots.** `SdCardFontRegistry` scans both `fs_/.fonts/`
(hidden) and `fs_/fonts/` (visible) and dedupes by family name, so an installed
set is routinely split across the two. Check both before concluding a family is
missing, and take both when copying a set out. The log line
`SD font system ready (N families discovered)` is the quickest confirmation that
a card layout is well-formed.

## When making changes

- Adding a new HAL method? Mirror the firmware signature exactly and stub it (usually no-op) in the matching `Hal*.cpp/.h`. Do not invent new public methods that don't exist in the firmware HAL.
- Adding a new host-side surface dial? Add ONE row to [src/SimulatorDials.h](src/SimulatorDials.h) and one `case` to `applyDialGroup` in [src/HalDisplay.cpp](src/HalDisplay.cpp). Do NOT add a line to the desktop boot seed, the settings watcher's dial block or the `CROSSPOINT_SIM_AS_SHIPPED` block — all three are generated from the table, and hand-keeping them in sync is exactly what drifted twice on 2026-08-23. `tests/dial_table_test.cpp` reads the shipped `ios/` sources and fails when the table's shipped value is not the one the app pushes.
- Adding a new Arduino/ESP-IDF symbol? Add the minimum stub to the corresponding header in [src/](src/) (e.g. [src/WiFi.h](src/WiFi.h), [src/Arduino.h](src/Arduino.h)). Match the upstream signature, return a sensible default.
- Touching storage or caching code? After the change, `rm -rf ./fs_/.crosspoint/` in the firmware project before re-running, otherwise stale caches built by the old code will mask the fix.
- Touching display, threading, or shutdown? Re-read the "Why the simulator's design has the shape it does" section above first. Several of those decisions undo subtle bugs that will resurface if reverted.
- Adding, removing, or renaming a firmware translation unit? The iOS source set is generated, not hand-written — regenerate it, or the CMake configure step fails with the exact command:
  ```bash
  cd <firmware> && pio run -e simulator -t compiledb
  python3 <simulator>/tools/gen_cmake_sources.py --firmware-dir . --compile-db compile_commands.json
  ```
- Changing anything shared? Build the desktop env first. Green desktop + red iOS means the iOS harness is wrong; both red means the HAL drifted.

## The color dials, and the one rule they all share

Three settings now decide what the page and the pad look like, all host-side —
**none of this reaches device firmware**, which has no Settings.app to expose it:

| Dial | Lives in | Docs |
|---|---|---|
| Page palette — 52 named presets plus Custom, chosen from the Presets button in either drawer (`ios/CrossPointPresetList.mm`) | `src/PanelPalette.h`, resolved by `ios/PanelPrefs.h` | `ios/README.md`, `docs/crt-phosphor-presets.md` |
| Button pad outline/fill | `ios/PadPalette.h` | `docs/pad-outline-black-and-white.md` |
| Render scale 1x/2x — **3x dropped 2026-08-23** ("drop 3x support for now"); the tier machinery, the seed trees and `build-sd-fonts.py --scale 3` all still work, so re-enabling is one number | `lib/GfxRenderer/RenderScale.h` (firmware), ceiling in `ios/CMakeLists.txt`, latched in `simulator_main.cpp` | `docs/ios-render-scale.md` |
| Phosphor mixer — Blend / Parts / Cascade into the Custom slot; premixes (P4 P6 P7 P14 P17 P18 P23 P40) are preset mixes, never ingredients | `src/PhosphorMix.h`, UI `ios/CrossPointPaletteMixer.mm`, opened by the page-color chip (tap or hold) | `docs/phosphor-mixer.md` |
| Screen grain — strength 0/0.3/1/3x, four coverages, blotch size 8/16/32 and depth 0/0.03/0.1/0.3, amplitude scaled PER PALETTE — SKIPPED while letterpress (light) or scanlines (dark) is on | `src/PhosphorGrain.h`, composited over the whole app surface in `HalDisplay::presentIfNeeded` | `docs/phosphor-grain.md` |
| Sheet-to-sheet drift — LIGHT pages only, a per-page paper tone offset off the SAME page identity the tooth, wires and marks use (so a leaf is the same leaf across a relaunch); +/-2 code values at dial 100, paper only, never the ink. Bit-exact off at dial 0, which is still the MODEL's default (`kPaperDriftDefault`) and the desktop's — but the iOS app FREEZES it at 100 (2026-08-23), so on the phone every leaf differs. It rides `livePanelPalette` -- the one read every consumer of the page's color goes through -- and the drift dial is threaded through `floorDensityPct`/`maxPaperStrengthPct`, so the 7:1 floor is the DARKEST leaf's rather than the nominal sheet's | `src/LightInkPalette.h`, applied in `HalDisplay.cpp`; `CROSSPOINT_SIM_PAPER_DRIFT`, `paperDriftPercent` in settings.json | `docs/surface-roadmap.md` section 1c |
| Letterpress — LIGHT pages only (doctrine 2026-08-22: light is paper and ink), Off/Subtle/Standard/Heavy, ink-squeeze rim + deboss shadow + pressure + tooth, panel-space, darken-only. The pressure part's mapped range is WIDENED above 100% (`pressAmpScale`, 200% = 8x standard) — the 2026-08-22 audit found the dial near-dead, eaten by both the pixel math and a cache key that omitted the part percents | `src/Letterpress.h`, composited over the panel in `HalDisplay::presentIfNeeded`; `CROSSPOINT_SIM_LETTERPRESS` | `docs/letterpress-and-scanlines.md` |
| The light page's SHEET — paper strength 100, tooth 300%, formation 80%, defects 0, drift 100, press 100/100/100 — FROZEN 2026-08-23, no control on the phone reaches any of it; the drawer keeps only the ink list, Density and the stock grid | frozen in `ios/CrossPointLightInkPicker.mm` and `ios/CrossPointPrefs.mm`, seeded by `CROSSPOINT_SIM_AS_SHIPPED` in `src/HalDisplay.cpp`; the desktop's `CROSSPOINT_SIM_PAPER_*` vars and settings.json keys are unchanged | `docs/light-ink-picker.md` §8 |
| Laid structure — chain + laid lines for a laid PAPER stock (`lightink::Paper::laid`; Laid Antique today), rides the paper slider, output-space box-integrated (the ~1.9 px laid pitch is ST-008 territory), darken-only, per-page seed | `src/LaidStructure.h`, folded into the sheet field in `HalDisplay::presentIfNeeded`; `CROSSPOINT_SIM_LAIDLINES` | `docs/letterpress-and-scanlines.md`, `docs/paper-colorimetry-sources.md` §3c |
| Scanlines — DARK pages only (doctrine 2026-08-22: dark is CRT; supersedes the 2026-08-18 no-scanlines ruling), Off/Subtle/Standard/Deep with the mottle depth folded in, one line per source row, bloom off the composed frame, output-space, darken-only | `src/Scanlines.h`, composited over the whole app surface in `HalDisplay::presentIfNeeded`; `CROSSPOINT_SIM_SCANLINES` | `docs/letterpress-and-scanlines.md` |
| Show-through — the previous leaf, MIRRORED (in presented space; the framebuffer is landscape) and heavily blurred, faintly visible through this one. LIGHT only, folded into the sheet field, darken-only, fourth consumer of the paper budget. FROZEN at 100; the STOCK's ISO 2471 opacity is what varies it (India 3.0x, Kozo 3.7x, vellum 0.25x) | `src/ShowThrough.h`, per-stock factor `lightink::showThroughScaleFor`; `CROSSPOINT_SIM_SHOW_THROUGH` | `docs/show-through.md` |
| Corner defocus — the beam spot grows and turns ELLIPTICAL off-axis, so the raster softens at the corners and not at the left/right edges. DARK only, modulates the scanline field rather than drawing one, mean-preserving (it cannot lift a corner). FROZEN at 100 (TG18 caps the corner astigmatism ratio at 1.5; shipped 1.23) | `src/CornerDefocus.h`, folded into `ensureScanlinesTexture`; `CROSSPOINT_SIM_CORNER_DEFOCUS` | `docs/corner-defocus.md` |
| Power-off collapsing dot — at sleep the picture squeezes to a bright line, the line closes to a dot, the dot fades. DARK only, and the glass then stays dark for the whole sleep. **The one surface dial that is an iOS Settings row**, default OFF | `src/PowerOffCollapse.h`, drawn by `SimulatorOverlay::stepPowerOffCollapse` from `HalGPIO::startDeepSleep`; `CROSSPOINT_SIM_POWEROFF_COLLAPSE` | `docs/power-off-collapse.md` |
| Beam paint (0/17/33/67/150/300 ms) | `src/HalDisplay.cpp`, set via `SimulatorOverlay::setBeamPaint` | `docs/crt-beam-and-flash.md` |
| Phosphor trail + cascade afterglow | `panelpalette::trailMsForPreset`, `setPanelGlow`/`setPanelGlowTail` | `docs/crt-phosphor-presets.md`, `docs/crt-beam-and-flash.md` |

**Three dials are frozen and one is a row, and that split is the 2026-08-23
ruling in miniature.** Show-through and corner defocus each have one obviously
right value -- one is gated by a stock the owner already picks, the other by a
published TG18 bound -- so they are frozen constants with no control. The
collapsing dot has a genuine TRADE (the glass stays dark for the whole sleep
instead of holding the sleep screen), so it is a Settings.app row and it ships
OFF. Every surface dial that reached Settings.app before that date was removed
on it; a new appearance row has to earn itself against that.

**A/B captures of the SCANLINE field must pin `CROSSPOINT_SIM_GRAIN_SEED`.** Its
phase jitter, thickness jitter and mottle all hang off `grainSeed()`, which is
re-rolled every launch, so two runs of identical dials differ by ~2.2 code
values before any dial moves -- larger than corner defocus. And **every arm of a
page-content A/B must restore the same `fs_/.crosspoint/`**: a run leaves its
final page position behind, so the next arm starts somewhere else and the
"effect delta" measures the book. Both cost a wrong reading on 2026-08-23.

**The page-turn flash is COALESCED by default, and is now an owner setting**
(`Page Turn Flash`, off by default, owner 2026-08-19 — "make that page-turn
flash an option in ios settings"; the desktop keeps
`CROSSPOINT_SIM_PRESENT_FLASH`, which still overrides). Turning it ON is not a
bug being reinstated: it is what the panel itself does, and someone may want the
device's process rather than only its result. Note the flag used to be a
`static const bool` latched from the env on first call, which is precisely the
shape that cannot become a setting. An
antialiased page is painted twice -- 1-bit, then composed 13-22 ms later -- and
both used to reach the screen. A present is now held 30 ms and released early by
the compose, so only the composed frame lands; a frame with no second pass is
never dropped, only delayed. `CROSSPOINT_SIM_PRESENT_FLASH=1` restores the old
behaviour, and `CROSSPOINT_SIM_LOG_PRESENTS=1` counts presents and tags which
pass wrote each one -- the only way to see this headlessly, since a due
screenshot deliberately overrides the hold. See `docs/crt-beam-and-flash.md`.

**A plane flag beats the base, in BOTH polarities** (`src/GrayscalePreview.h`).
The firmware's base pass paints every coverage level as ink in light mode but
only full ink in DARK mode, so in dark mode every glyph edge arrives base-WHITE
and flagged. The decode used to discard exactly those, and dark-mode text had no
antialiasing at all -- 28,550 computed AA pixels per page, all rendered as
paper. `CROSSPOINT_SIM_LOG_AA=1` prints the flagged count and the levels the
compose actually produces, which is the only thing that separates "the AA looks
bad" from "the AA is not there". Note the firmware picks its masks from its OWN
`darkMode` setting, not from `CROSSPOINT_SIM_DARK`.

**Settings.app is now four rows.** Owner ruling 2026-08-23, from a screenshot
of his own chosen values: *"make these settings the default and remove them from
ios app settings as options."* The whole **Page Colors** and **Paper Defects**
groups left `Root.plist`; Sharpness followed the same day when 3x was
dropped, leaving Zen toggle / Screen / Read Aloud.
The frozen values are page fade **Off**, fade depth **fully transparent**,
letterpress **Standard**, scanlines **Subtle** at **Fine** pitch with **Extreme**
bloom, defects **0**.

All seven getters in `ios/CrossPointPrefs.mm` now return a constant
**without consulting NSUserDefaults**, which is the part that matters: an install
that stored a different value before the row was removed must not keep rendering
it, and with the row gone there would be no way to change it back.
`paperDefectsPercent` held out for part of that day, because the light picker's
Defects slider still wrote it; it froze at 0 with the rest when that slider went
(below), and `CrossPointPrefs_setPaperDefectsPercent` and the key itself were
deleted.
`CROSSPOINT_SIM_AS_SHIPPED` was moved to match, since its whole job is to be the
complete list of what the app's dials actually are.

**The light page-color drawer is no longer the paper instrument.** Owner ruling
the same day, sent with a screenshot of the values he had settled on: *"set
Paper, tooth, formation, defects and press to these parameter values, then
remove sliders and option to set this in app."* Seven sliders and the PRESS
group header left the drawer — Paper strength, Tooth, Formation, Defects, Sheet
drift and the three press parts — frozen at **100 / 300% / 80% / 0 / 100 /
100 / 100 / 100**. The drawer keeps the ink list, **Density**, the paper STOCK
grid (choosing the stock is not the strength slider), Done and the readout. Same
freeze discipline as the Settings rows, same reason. The paper strength is
RE-DERIVED from the frozen 100 on every change rather than carried, because its
clamp is a ceiling that moves with the ink and a value once lowered could never
be raised again. Drift at the top of its range is now every page rather than a
worst case, so `tests/light_ink_test.cpp` sweeps the 7:1 floor there: worst
measured 7.001:1 (model) and 7.000:1 (with tooth and formation on the darkest
leaf). Details: `docs/light-ink-picker.md` §8.

**A preset persists as an INTEGER.** Rows therefore APPEND and never insert —
re-pointing one silently changes what a saved choice selects. The display order
in `Root.plist` is independent of that integer, which is what lets the picker be
grouped and sorted without touching a single stored value.

**The test's "unknown preset" sentinel has to stay ahead of the enum.** It has
been walked ten times (7 → 11 → 13 → 14 → 16 → 17 → 19 → 24 → 26 → 56) and
caught the collision every time rather than shipping one. Whoever appends the
next preset moves it again.

**Two palette rows MAY paint the same page, if they decay differently** (owner
ruling 2026-08-17, "be sure to include all possible phosphors"). The whole JEDEC
registry ships -- 42 phosphor rows -- and some of them are the same emission:
P19/P26/P33/P38 are all 590-595 nm fluoride:Mn. Persistence is what separates
them, and the glow is what renders it. The duplicate check is driven off
`kPresetInfo` and allows a shared page only between two phosphors with different
trails; exactly one true twin pair (P19/P38) is exempt BY NAME in the test.
New phosphor rows are derived by `tools/derive_phosphors.py`, not by hand.

**One resolver, two consumers.** `crosspoint::panelForPrefs()` is the single
definition of "what tones did the owner pick": the SDL side paints the page, the
pad and the SHOW chip from it, and the UIKit side paints the HIDE chip in the
keyboard bar. They diverged once — hardcoded hex in the keyboard bar meant Green
CRT made one chip phosphor and left the other gray — and
`tests/chip_tint_source_test.py` exists to stop the literals coming back.

**...but one READER over a store with two WRITERS is not one source.** Owner P1
2026-08-23, "ink is not being picked up ... fix sourcing for light and dark to be
more accurate on load, switch etc." Reproduced and fixed the same day; the
decision now lives in [src/PanelSource.h](src/PanelSource.h) (pure,
host-tested by `tests/panel_source_test.cpp`) and `ios/PanelPrefs.h` only
fetches. **ONE EDITOR PER POLARITY, and neither writes the other's fields:** the
light-mode historical-ink picker owns `panelInk/PaperLight`, the dark-mode gun
mixer owns `panelInk/PaperDark`. The mixer wrote all four until this landed, so a
gun moved in dark mode replaced the chosen ink — measured, an applied Payne's
Gray went from `323D47` (page text 30,37,43) to `6E0500` (64,3,0) on one slider
move, with `lightInkIndex` still reading 15.

The shared `panelPalettePreset` integer is why any of this is delicate: it names
one preset for BOTH appearances, so pointing it at Custom for one polarity's sake
changes the other. `CrossPointPrefs_claimCustomFor(editingDark)` is the single
protocol — freeze the other polarity's currently-rendered pair, **and its
phosphor**, then move the preset — and it is one-shot, because after that both
polarities hold owner choices and re-freezing is how one editor eats the other's
work. Freezing the phosphor is the second half of the same bug: `pollPanelGlow`
read the preset integer raw, Custom names no phosphor, so a light-mode ink pick
turned a 283 ms White CRT trail into 0 ms reflective and kept it that way across
relaunches. It asks `crosspoint::glowPresetForPrefs()` now, and
`panelDarkSnapshotPreset` is where the frozen phosphor lives (append-only, 0 =
none, which is what every install predating it reads).

`tests/chip_tint_source_test.py` passed through this entire bug, because it
asserts a delegation CHAIN and never a tone. `tests/panel_source_test.cpp`
asserts BYTES for both polarities across load, switch and both editor orders;
`tests/panel_source_test.py` pins that the two editors still write only their own
polarity. Both fail against the pre-fix tree.

**And there is a road BACK, because the claim is one-way.** Owner ruling
2026-08-23, "add a Presets row back to the pickers": the claim only ever points
the shared integer AT Custom, and Settings.app's palette row left with the other
page rows on 2026-08-22 — so the first ink pick or gun move made all 52 named
presets unreachable AS presets. `panelsource::releaseCustom` is the inverse
protocol and `CrossPointPrefs_selectPanelPreset` performs it: both polarities go
back to the preset, and the two keys that only speak while the slot is Custom —
`phosphorMixActive` and `panelDarkSnapshotPreset` — are **cleared, not left**.
The mix flag is the one that bites: `glowPreset` asks it BEFORE the frozen
phosphor, so a stale blend would decide the decay of a preset chosen after it,
and only from the NEXT claim onward — invisible at the moment of the mistake.
The four hex fields are deliberately left, since a named preset ignores them.
Both drawers reach it through ONE list
([ios/CrossPointPresetList.mm](ios/CrossPointPresetList.mm), a Presets bar
button opposite Done), previewing the appearance that drawer renders and
offering every preset in both — a preset defines both appearances, so filtering
either list would remove a choice Settings.app used to offer. Round trip proven
in bytes on an iPhone Air simulator and pinned in `panel_source_test.cpp`, whose
naive arm models the wrong implementation so the protocol has to earn itself.

**The pad's Accessible pin also had two resolution points**, found the same day
and a separate bug: `CrossPointIOSShim.cpp`'s `currentLevels()` pinned
`kPresetAccessible` (−4/−5 light, +4/+5 dark) while `PanelPrefs.h`'s
`padPaletteForPrefs` went on handing the raw stored contrasts to
`makePaletteOn`, so the UIKit HIDE chip drew the Current preset's ±1 hairline
beside an SDL pad drawn at Accessible's ±4 — the two halves of one gesture, 4–5×
apart in contrast, under a header comment promising one definition. Both call
`padpalette::shippedLevels()` now.

**A palette change raises no trait change, and a CGColor never re-resolves.** A
UIKit control built once keeps the tones it was built with, so
`applyPanel()` pushes `CrossPointKeyboardBar_refreshTint()` at it. Same shape as
the appearance path: `requestPresent()` only re-pushes the framebuffer, so
`applyTheme()` also calls `crosspointRequestRender()` or the firmware's own
Settings screen keeps painting the value it was drawn with.

## Proof figures: three mechanical checks, and where they go

Owner rulings 2026-08-22, in the order he found each failure. A figure that is
EVIDENCE (its subject is fine structure -- scanlines, grain, tooth, dither,
antialiasing, letterpress edges, defects) must pass all three before it ships;
a figure that is CONTEXT (layout, geometry, an overview) is exempt but must be
labelled as context in its caption.

1. **Lossless.** PNG at native pixels. Never JPEG. Integer-factor NEAREST if it
   must be scaled, stated on the page, with `image-rendering: pixelated`.
2. **Not shrunk past the effect.** One figure per row at full column width, a
   native-pixel CROP of the region under judgment -- never a 3-up grid of whole
   pages. "do better at not reducing images like this. it's a miss, as is."
3. **The crop must contain the thing.** Measure before publishing: content
   coverage (fraction of pixels away from the modal background -- under ~10% is
   a picture of empty paper) AND effect delta against the figure's own baseline
   (mean, max, % of pixels changed by more than 4 levels). For SPARSE subjects
   -- defects, flecks, a single hairline -- a page band always fails: diff the
   renders to LOCATE the feature, crop tight around it, magnify by an integer
   factor, and say the magnification in the caption. "I don't think you're
   intending to show a mostly empty example here."

DELIVERY, ruled 2026-08-22: repair figures IN PLACE at the artifact's existing
URL. Do not publish a fresh gallery to carry corrections -- he tracks these
pages by their links.

## Proof images are lossless, always

Owner P0, 2026-08-22: "all proof images need to be losslessly shared or we're
defeating the whole purpose of proofing." Every image in an artifact, a file
send, or any channel he judges by eye is **PNG at native pixels**. Never JPEG.
If a set will not fit the artifact cap, scale by an INTEGER factor with NEAREST
resampling (and say so on the page), split across two artifacts, or crop to the
region under judgment at 1:1 -- never compress. Add `image-rendering: pixelated`
so the browser does not smooth it back. The subjects here are tone, dither,
grain, scanlines and antialiasing: the exact things a lossy codec eats first.
The simulator captures BMP; convert to PNG, never to JPEG.

## The 2026-08-22 channels and hooks (quick index)

Grown in one day; each is documented at its definition, this is the map:

- **Reader text-block insets**: the firmware publishes its final insets
  (framebuffer px) through the HAL keyboard-channel pattern; the sim stores
  them (`SimulatorOverlay::readerTextInsetsPx`) and the zen placement consumes
  them, with 60/35 device px as the documented pre-first-render fallback.
- **Zen placement**: in zen the panel is PLACED within the sheet (band pixels
  trade bottom→top so the fit box, and therefore the page's scale, never
  changes). The shift is snapshotted per layout pass — band and top inset must
  consume the same value or the page resizes (shipped once, build 123).
- **`CROSSPOINT_SIM_MIX_GUNS="r,g,b[,w]"`** drives the mixer's own apply
  function headlessly. **`CROSSPOINT_SIM_TAP_PAD=<BUTTON>`** synthesizes a real
  SDL finger tap through padWatch (~590 ms hold — too slow for the zen
  deliberate-tap gate, whose ceiling is 400 ms; `CROSSPOINT_SIM_TAP_CHIP=1`
  pushes a same-frame tap that passes it). **`CROSSPOINT_SIM_OPEN_MIXER=1`**
  presents the mixer with no finger.
- **`CROSSPOINT_SIM_LOG_POWER=1`**: [power] stations across sleep entry / wake
  source / reboot boundary / first update-refresh-present.
- **`CROSSPOINT_SIM_LOG_TIMING=1`**: one `[timing]` line per present --
  every field pass tagged BUILD / cache / off with its wall time, the
  scanline readback and the flip apart, and the total. The env read is
  LATCHED once, not read per present: an instrument that added a getenv and
  a clock read to each pass it measures could not report those passes
  honestly. Measured page-turn costs and what they overturned:
  `docs/surface-roadmap.md` section 4c -- shortest version, at the phone's
  3x an OUTPUT-space field costs ~30 ms per page turn and a PANEL-space one
  ~490 ms, and the GPU readback everyone assumed was the expensive item is
  2-6%.
- **`CROSSPOINT_SIM_IMPORT_FILE=<path>`**: drives the book-import path (copy
  to card, then open) exactly as an incoming Files/share-sheet epub does.
- **Zen zones fire only for deliberate taps**: single finger, ≤28 px travel,
  ≤400 ms, zone judged from the LANDING point. Swipes, drags, holds, and
  multi-finger do nothing.

## Driving it headlessly

Read [docs/headless-qa.md](docs/headless-qa.md) BEFORE writing a screenshot
script. Four of its five points cost a wrong diagnosis first, and the worst is
that lists navigate on the FRONT pair: scripting `DOWN` at a menu does nothing,
correctly, because the side buttons page by a screenful and a one-screen menu
has no next screenful. Script `RIGHT`. It also records that Home starts on a
book COVER rather than a menu row (an off-by-two), that presses need ~900 ms
between them or half are swallowed, that launch resumes the last book so the
starting screen is not fixed, and that captures are BMP whatever you name them.
