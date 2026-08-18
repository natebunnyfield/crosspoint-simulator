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

There is no linter and no per-file build commands; most changes are "tested" by running the simulator and exercising the affected feature. Host tests exist in `tests/` (25 passing, 0 skipped as of 2026-08-18), run them when touching input, text entry, sleep, network, restart, task lifetime, read-aloud, palettes, device-fidelity flags, or build-configuration paths. `tests/run_all.sh` builds and runs the host tests in one go (`-k <substring>` to filter) and exits non-zero on the first failure — the individual commands below are what it runs, kept here because they are also how you debug one in isolation. The four shell tests are not in the runner: all need a firmware checkout and use exit 2 for SKIP, which a pass/fail runner would misreport. (`test_sleep_wake.sh` currently fails against firmware `main` — pre-existing drift, filed as S-011 in BUGS.md. `test_text_entry.sh` fails too, and for a similar reason: its Home/Settings navigation is stale, so it never reaches the field it tests — S-015.)

```bash
tests/run_all.sh
```


```bash
c++ -std=c++17 -Iios tests/pad_core_test.cpp ios/PadCore.cpp -o /tmp/pad_core_test && /tmp/pad_core_test
c++ -std=c++17 -Iios tests/pad_palette_test.cpp -o /tmp/pad_palette_test && /tmp/pad_palette_test ios/Settings.bundle/Root.plist
c++ -std=c++17 -Isrc tests/panel_palette_test.cpp -o /tmp/panel_palette_test && /tmp/panel_palette_test ios/Settings.bundle/Root.plist
c++ -std=c++17 -Isrc tests/phosphor_grain_test.cpp -o /tmp/phosphor_grain_test && /tmp/phosphor_grain_test
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

`pad_core_test` covers the iOS pad's finger→button passthrough (PadCore is pure and clock-free by design — do not add timers to it). `pad_palette_test` covers the pad's contrast ladder and its Current/Accessible/Transparent presets (`ios/PadPalette.h`, pure for the same reason): it recomputes every rung's sRGB contrast ratio, pins the Current preset to the exact shipped tones, proves −9/+9 reach #000000/#FFFFFF in both appearances and both roles, and — the part no `static_assert` can do — reads the shipped `ios/Settings.bundle/Root.plist` and fails when a row's printed ratio disagrees with the tone that row selects. Every failure mode there is silent: a rung equal to the field paints nothing, a mislabelled row lies. It is one of two tests that take a path argument (defaulted to the repo-relative plist), so run it from the repo root. `panel_palette_test` is the other, and covers the PAGE's two tones (`src/PanelPalette.h`, pure for the same reason): that the default ink/paper pair is byte-for-byte what this repo hardcoded before the dial existed, that every road not involving typing arrives back at it, that the 0..255 ramp between them stays integer-truncated and non-degenerate (this is the 2-bit gray handling -- the intermediate levels are LERPED, never tabulated), that every way a Settings.app hex field can be wrong falls back per-field rather than blanking the page, that no named preset drops under 7:1 or duplicates another, and -- reading the shipped `Root.plist` -- that each preset row's printed contrast figure matches the tones that row actually selects. Every failure mode here is a wrong COLOR, which no compiler and no other test in this repo can see. `phosphor_grain_test` covers the screen-grain field (`src/PhosphorGrain.h`, pure for the same reason): that OFF is BIT-EXACT off rather than nearly-off on every coverage, that the field can only ever darken (a multiplier above 1 is the additive lift that produced both the page-flash and the gray-background reports), that the cell stays `kCellPx` square (a regression to 1 drops below acuity and renders as the flat fill the feature exists to replace), that the dial is linear from 0x to 10x, that Vignette is a no-op at the exact center and still leaves a readable corner at 10x, and that Mottled carries real low-frequency structure without adding a net dimming -- measured on BLOCK means, since per-pixel spread cannot tell a blotchy field from an even one. `test_text_entry.sh` drives Settings > Device owner and asserts the persisted `settings.json`, so it covers the host-keyboard channel end to end; what it cannot cover is the suppression that keeps typed letters off the button map, because it injects below SDL — that half is verified on the phone and written up in [ios/README.md](ios/README.md). `test_note_editor_repaint.sh` is its sibling for the MULTI-line case and asserts something a file cannot show: it compares the FRAME before a `TYPE` with the frame after it, in a fresh Create Note, with `CROSSPOINT_SIM_HOST_KEYBOARD` at both 0 and 1. It exists because firmware B-028 was invisible to every file-contents assertion — the note editor drained the typed text into its buffer and saved it perfectly while never repainting once, because its debounced `requestUpdate()` sat below an `if (panelHidden) return;` that is taken exactly when a phone's software keyboard is up. Two byte-identical BMPs were the only observable. `test_sleep_wake.sh` pins the deep-sleep wake edge-latch: a 1 ms synthetic POWER tap during sleep must relaunch the process (the sleep loop consumes an edge set by `injectButtonDown`, because a fast tap's down and up can both land in one pump burst and leave no level to poll). `build_identity_test` proves the split-brain guard aborts — see "One device macro, one definition" below. `wifi_host_test` covers the branch `WiFiClass` takes when a real radio is behind it — the iOS path — and guards that the desktop env-var fakes are unchanged by the hook's presence. `http_dispatch_test` pins that the mock-root and `file://` fixture paths still beat the network, and in that order, now that a second transport exists. `restart_semantics_test` pins the two silent ways `ESP.restart()` can go wrong: claiming a POWER press it never received, and leaving an input script in place so an automated run restarts forever. `read_aloud_channel_test` pins the read-aloud page channel's hand-off contract (one consume per publish, latest wins, `publish(nullptr)` is the stop-speech clear); `read_aloud_core_test` covers every transition of the read-aloud state machine — most load-bearing: a canceled utterance never turns a page, and highlight/tap offsets are UTF-8 bytes (the test page has curly quotes and accents precisely so a character-counting regression fails it). `test_read_aloud_capture.sh` pins the firmware capture end-to-end against a tiny GENERATED two-chapter EPUB (the seed book's mono-file chapter takes tens of seconds to paginate, which made it timing-flaky here): boot page published, a `QTAP` page turn reaches a different page, multibyte survives, exit clears, and the channel stays silent without the env var. `task_registry_test` pins the FreeRTOS shim's name dedupe against `vTaskDelete`: the registry used to keep pointing at a freed handle, so the create/delete/create sequence the iOS in-process reboot performs handed the caller freed memory. It asserts behaviourally (did a thread actually spawn?) because the allocator reuses the freed block, so pointer identity does not distinguish the two. `gen_cmake_sources_test.py` is the one Python test, and it exists because `cmake/CrossPointSources.cmake` is the only thing telling the iOS build which firmware sources to compile: the generator resolved the compile database's relative `file` paths against the process cwd instead of each entry's own `directory`, so running it from anywhere but the firmware checkout filed all 125 firmware TUs as simulator sources, wrote an empty `CROSSPOINT_FW_SOURCES`, and exited 0. The test pins cwd-independence plus every refusal (empty, zero-firmware, zero-simulator, wrong tree, stale, partial, no include dirs, malformed JSON) and that a refused run leaves the existing file byte-identical. `device_truth_test` covers S-001's last four reversals (`src/SimulatorDeviceTruth.h`, pure for the same reason PadPalette is): the flag spellings, that anything unrecognised falls back to the HISTORICAL answer rather than inventing a state, the panic report's field order against the firmware's own writer, and — the one that matters most — that the panic latch is ONE-SHOT. It consumes `CROSSPOINT_SIM_PANIC` on first read, because the desktop reboot is `execvp` and hands `environ` to the child, so without that a single injected panic would route every boot into `CrashActivity` forever and the crash screen would have no exit. `sha256_test` pins the mbedtls shim to the published FIPS-180-4 vectors, including the million-'a' case and a chunked digest matching the one-shot; that shim WAS a fake (`digest[i % 32] ^= input[i]`, returning success), and nothing but a known-answer vector can see such a thing — the signature, the length and the determinism are all indistinguishable from a real digest.

## Architecture

The simulator is a collection of host-side reimplementations of the firmware's hardware abstraction layer (HAL) and its Arduino/ESP-IDF dependencies. Each `Hal*.cpp/.h` here corresponds to a `Hal*` class in the firmware's `lib/hal/`, and **must keep the same public surface** or the firmware will not link.

**The HAL stub rule.** When the firmware adds a new method to a HAL class and calls it, the simulator fails to link until a matching stub is added to the corresponding `Hal*.cpp` here. Most additions are one-line no-ops. This is the single most common reason a simulator build breaks after pulling firmware updates.

It runs the other way too, and that direction costs a firmware change: a capability the *host* has and the device does not (the keyboard channel — `setTextEntryActive` / `consumeTypedText`) has to exist on both sides, as a real implementation here and an inline no-op in the firmware's `lib/hal/HalGPIO.h`. Simulator-only methods the firmware never calls (`injectButtonDown/Up`, `injectTypedText`, `pumpHostTextInput`) need no counterpart and must not gain one.

**Why the simulator's design has the shape it does** (the non-obvious parts):

- **SDL on main thread.** macOS requires all SDL calls to come from the main thread, but firmware drives rendering from a FreeRTOS render task. The split lives in [src/HalDisplay.cpp](src/HalDisplay.cpp): `refreshDisplay` (background thread) converts the 1bpp framebuffer to ARGB and sets an atomic `pendingPresent` flag. `presentIfNeeded` (called from `simulator_main` on the main thread) does the actual SDL upload and present. Do not call SDL render functions from anywhere else.
- **Orientation rotation lives in two places.** The firmware's renderer rotates content into the landscape framebuffer (90 CCW for `Portrait`). The simulator undoes that with `SDL_RenderTextureRotated`. If you change one, change the other. The dst rect is landscape-shaped and center-offset because the rotation happens around the dst center.
- **HiDPI / dithering.** `SDL_WINDOW_HIGH_PIXEL_DENSITY` plus `SDL_SetRenderLogicalPresentation`, and a scale mode set on the texture (SDL3 replaced the global `SDL_HINT_RENDER_SCALE_QUALITY` hint with a per-texture setting, so it must come *after* `SDL_CreateTexture`). Without these, Bayer-dithered grays render as harsh black/white stripes on Retina.
- **Presentation policy is keyed on intent, not platform — and on DIRECTION.** `CROSSPOINT_SIM_PIXEL_EXACT` selects `INTEGER_SCALE` + `SCALEMODE_NEAREST`; without it the build gets letterbox + linear filtering. Linear is right at 1:1, where Bayer dither averaging to gray is what e-ink actually looks like; exact pixels are right wherever the panel is scaled **up**, because a fractional scale or a linear filter greys the dither and every rendering judgment made against it is a lie. **Below 1x that argument inverts**, and the code applied it in both directions by omission until 2026-08-15. A 3x render scale does not fit any iPhone's width (1584 framebuffer px against 1260 on an iPhone Air), so the phone MINIFIES — nearest-neighbour then simply does not draw 324 of every 1584 columns, the panel's four grey levels stay four instead of blending into the ~17,000 the geometry could give, and the selection dither's regular grid beats against the sampling lattice at a 21-device-pixel period. That beat is ST-008. `panelScaleModeFor()` now returns `SDL_SCALEMODE_LINEAR` below 1x and the unchanged `kPanelScaleMode` at or above it; the `[panel]` log line prints which is live. Measured beat amplitude on the `LightGray` fill at 0.7955: nearest 8.14 levels, bilinear 1.55, an exact box filter 0.37, and 0 at 1:1 — which is also why build 75 (2x, presented at exactly 1.0) could not show it and build 76 (3x) must.
- **`SimulatorOverlay` for chrome outside the panel.** [src/SimulatorOverlay.h](src/SimulatorOverlay.h) is a free hook `presentIfNeeded` calls, deliberately *not* a `HalDisplay` method — the HAL's public surface must mirror the firmware's, and on-screen chrome has no analog on real hardware. The callback runs with logical presentation disabled and receives the real output size, so it can paint the letterboxed margins the panel's logical space cannot reach. `requestPresent()` exists because an e-ink firmware presents rarely, so overlay state changes would otherwise not appear until the next page render.
- **Panel palette + reserved pad band.** The 1bpp/AA framebuffer presents as tinted ink on tinted paper. The pair is a **dial**, not a constant: definitions, presets, hex parsing and the interpolation live in [src/PanelPalette.h](src/PanelPalette.h), the live pair is two atomics in [src/HalDisplay.cpp](src/HalDisplay.cpp), and hosts set it through `SimulatorOverlay::setPanelPalette` (the iOS Settings app; `CROSSPOINT_SIM_PANEL_{INK,PAPER}_{LIGHT,DARK}` on desktop). Both polarities default to what this repo always hardcoded — 2D2D2D-on-FBFBF9 light, E0E0DE-on-121212 dark — so a build that never calls the setter is pixel-identical. The dark ramp's ink→paper direction IS the inversion (no separate 255−level flip), and every intermediate gray is LERPED from the two ends, so the 2-bit gray targets need no table and a custom pair still grades — do not hardcode an intermediate. The pad's field is the paper tone (`padpalette::makePaletteOn`), so the pad follows a custom paper and its printed contrast ratios become approximate. `SimulatorOverlay::setBottomInset` reserves a bottom band for chrome: the panel then fits TOP-ALIGNED above the band (manual placement, integer scale preserved under `CROSSPOINT_SIM_PIXEL_EXACT`) and publishes its bottom edge via `panelBottomPx()` — the iOS pad anchors to it. Desktop keeps inset 0 and the plain letterbox path.
- **Screen grain is a PRESENT-TIME pass, in device pixels, drawn last.** The
  page's flatness is not a palette problem -- a real tube's screen is a settled
  layer of phosphor crystals with uneven coverage. [src/PhosphorGrain.h](src/PhosphorGrain.h)
  is the model (pure, host-tested, for the same reason PanelPalette is: every
  failure mode is a wrong picture). Three things about the placement are
  load-bearing. It is generated at the PRESENTED RECT's size and drawn 1:1, not
  baked into the 1bpp->ARGB conversion, because the panel is minified to 0.7955
  on a phone and a regular field written into the framebuffer beats against that
  resample -- the ST-008 moire, measured at 8.14 levels. It composites with
  `SDL_BLENDMODE_MOD` and can only DARKEN, because coverage variation is a
  deficit against an ideal screen and because an additive pass over a dark
  ground is exactly the page-flash and gray-background bug class. And it goes on
  LAST, over the beam's swept band and the accumulator's trail, since all of
  those are light leaving the phosphor that its coverage then gates. Owner
  ruling 2026-08-18 rules out the alternatives: no bloom or halation (costs
  legibility), no scanlines (a raster artifact, not a phosphor one). Full
  writeup: [docs/phosphor-grain.md](docs/phosphor-grain.md).
- **Inversion changes re-present from a cached frame.** `setInverted` posts an atomic reconvert request that `presentIfNeeded` (main thread) services from the cached BW base and grayscale AA planes — inversion applies at 1bpp→ARGB conversion time, and e-ink firmware refreshes rarely, so without this a dark-mode flip would wait for the next page turn. `SimulatorOverlay::setPanelDark` is the single polarity entry point: the iOS harness follows the system appearance through it, and `CROSSPOINT_SIM_DARK=1/0` forces either state for headless runs. Book covers/images render as negatives in dark mode; accepted for now.
- **POSIX fds, not std::fstream, in [src/HalStorage.cpp](src/HalStorage.cpp).** This was a deliberate rewrite. fstream's separate get/put pointers, eofbit-blocks-seek behavior, and write-only seek restrictions caused several silent-corruption bugs. Do not reintroduce fstream here. All paths are prefixed with `./fs_` so the simulated filesystem stays sandboxed under the binary's working directory; `/books/` on the SD card maps to `./fs_/books/`. Directory iteration skips only `.` and `..` — dotfiles ARE returned, matching SdFat on device (an earlier version of this file claimed all dot-entries were skipped; the firmware does its own hidden-file filtering, and the Manage Files screen deliberately lists them).
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
  wrap-around — so `DOWN` x15 then `ENTER` reaches Settings regardless of how
  many books are listed, and `DOWN` x15 then `UP` then `ENTER` reaches Manage
  Files.
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
| Page palette — 15 named presets plus Custom | `src/PanelPalette.h`, resolved by `ios/PanelPrefs.h` | `ios/README.md`, `docs/crt-phosphor-presets.md` |
| Button pad outline/fill | `ios/PadPalette.h` | `docs/pad-outline-black-and-white.md` |
| Render scale 1x/2x/3x | `lib/GfxRenderer/RenderScale.h` (firmware), latched in `simulator_main.cpp` | `docs/ios-render-scale.md` |
| Screen grain — strength 0x..10x, four coverages | `src/PhosphorGrain.h`, composited in `HalDisplay::presentIfNeeded` | `docs/phosphor-grain.md` |
| Beam paint (0/17/33/67/150/300 ms) | `src/HalDisplay.cpp`, set via `SimulatorOverlay::setBeamPaint` | `docs/crt-beam-and-flash.md` |
| Phosphor trail + cascade afterglow | `panelpalette::trailMsForPreset`, `setPanelGlow`/`setPanelGlowTail` | `docs/crt-phosphor-presets.md`, `docs/crt-beam-and-flash.md` |

**The page-turn flash is COALESCED, and it is not optional by default.** An
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

**A palette change raises no trait change, and a CGColor never re-resolves.** A
UIKit control built once keeps the tones it was built with, so
`applyPanel()` pushes `CrossPointKeyboardBar_refreshTint()` at it. Same shape as
the appearance path: `requestPresent()` only re-pushes the framebuffer, so
`applyTheme()` also calls `crosspointRequestRender()` or the firmware's own
Settings screen keeps painting the value it was drawn with.

## Driving it headlessly

Read [docs/headless-qa.md](docs/headless-qa.md) BEFORE writing a screenshot
script. Four of its five points cost a wrong diagnosis first, and the worst is
that lists navigate on the FRONT pair: scripting `DOWN` at a menu does nothing,
correctly, because the side buttons page by a screenful and a one-screen menu
has no next screenful. Script `RIGHT`. It also records that Home starts on a
book COVER rather than a menu row (an off-by-two), that presses need ~900 ms
between them or half are swallowed, that launch resumes the last book so the
starting screen is not fixed, and that captures are BMP whatever you name them.
