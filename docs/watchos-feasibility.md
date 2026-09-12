# Can this simulator run on an Apple Watch?

Feasibility assessment, 2026-09-11, against `17e47e4` on
`feature/dtl-romulus-trial`. Owner's question: *"can an apple watch app be made
for this simulating this? at 1x or not? what limits are a challenge?"* This is
a reading of the repo plus platform facts; nothing here was built or measured
on a watch. Each item says whether it was verified against source or inferred.

## Verdict

Possible. Not at 1x. The firmware core ports; the harness does not. The work is
a new display/input backend and a new board profile, not firmware changes.

## 1x is dead on arrival — the panel does not fit any watch

X3 panel is 792x528 logical, presented portrait as 528x792
(`docs/ios-render-scale.md:16`, verified). Watch screens (Apple published
sizes, not measured here):

| Watch | px | scale to fit 528x792 |
|---|---|---|
| Ultra 2 | 410x502 | 0.63 |
| Series 10 46 mm | 416x496 | 0.63 |
| Series 10 42 mm | 374x446 | 0.56 |
| Series 9 41 mm | 352x430 | 0.54 |

Minifying to 0.55–0.63x is ST-008 territory made worse: the four-level
dither beats against the sampling lattice (measured 8.14 levels on the
`LightGray` fill at 0.7955 nearest; `CLAUDE.md`, presentation policy), the
8 px Noto chrome becomes 5 px, and reading text roughly halves. Unreadable.

**The route is a new board profile, not a smaller window.** `BoardConfig.h`
already selects geometry per device (X3 792x528, X4/X4 Pro/Sticky 800x480), so
a fake ~496x416 landscape framebuffer would make the firmware re-paginate to
the watch. UNVERIFIED: how many firmware UI sites hardcode X3/X4 pixel
constants rather than reading the board macros. Grep the firmware repo before
promising this.

## Limits, ranked by cost

1. **SDL3 has no watchOS backend (platform fact; inferred from SDL3's
   supported-platform list, not tested).** The whole HAL rides SDL: 130
   distinct `SDL_*` symbols across 40 files in `src/` and `ios/` (counted
   2026-09-11 with `grep -rhoE "SDL_[A-Za-z]+" src ios | sort -u`). watchOS
   also has no UIKit, so every `ios/*.mm` (pad, recognizers, keyboard bar,
   sheets, prefs) is gone. Needed: `HalDisplay` hands its ARGB buffer to
   Swift and SwiftUI paints it; `HalGPIO`'s event pump rewritten from
   Crown/tap events. Saving grace: an e-ink firmware presents rarely, so a
   1–4 fps blit is enough. This is the biggest item.
2. **Memory.** watchOS per-app RAM is tight and Apple does not publish it
   (tens of MB; unmeasured). The firmware side is already ESP32-budgeted and
   the simulator can enforce a budget (`CROSSPOINT_SIM_HEAP=380000`, S-001,
   `src/SimulatorHeap.h`). Fonts stream through `SimCompressedFile` one 32 KB
   block at a time (verified). Unknown: resident size of `libcrosspoint_core.a`
   on a watch. Measure before committing.
3. **App size cap.** Apple's rule: a watchOS app must be under 75 MB
   uncompressed (platform fact). The seed tree is 117,654,860 bytes raw and
   34,837,381 as CPZ1 (`docs/seed-font-compression.md`, verified). A watch
   would bundle the 1x tier only (no 2x) and fewer families. Fits.
4. **Surface passes cannot run.** A sheet rebuild costs 126–133 ms per screen
   entry on iPhone Metal (`CLAUDE.md`, measured 2026-08-24); the watch SiP is
   far slower. Palette only, every dial off. Cheap: the dials are already
   constants and env vars.
5. **Lifecycle.** watchOS suspends the app on wrist-down within seconds.
   `millis()` keeps running while suspended and the firmware's inactivity
   timer would sleep the device on resume: the S-037 shape again, which the
   iOS harness already handles via `SDL_EVENT_DID_ENTER_FOREGROUND`. The
   `longjmp` in-process reboot is the iOS path and ports; the desktop's
   `_exit(0)` and `execvp` do not.
6. **Input.** Seven buttons on 40 mm of glass. Digital Crown → page turn,
   tap → confirm, hold → back. Text entry maps onto the existing keyboard
   channel (`setTextEntryActive` / `injectTypedText`) fed by WatchKit
   dictation or scribble.
7. **Books in.** No Files app, no WebDAV (a listening socket on a watch is
   impractical; the `WebServer.cpp` shims are dead code there).
   WatchConnectivity from an iPhone companion, or Update Library over
   URLSession (the iOS fetch path is native; `docs/library-sync-on-ios.md`).
8. **Threads and C++.** The FreeRTOS shim is `std::thread` plus a condvar
   (`src/freertos/`, verified); pthreads exist on watchOS. Fine.
9. **Toolchain.** `ios/CMakeLists.txt` hardcodes arm64-apple-ios and links
   `SDL3::SDL3` (verified). A new CMake target reuses the generated
   `cmake/CrossPointSources.cmake`; the build-identity gate
   (`src/SimulatorBuildIdentity.h`) needs the new device enum.

## What to measure before deciding

- Count of firmware UI sites that hardcode panel pixel constants.
- Resident memory of the core library running one book on a watch.
- Size of a 1x-only seed tree at the family count a watch would carry.

## Not done

Nothing built, nothing measured on a watch. Battery was not considered:
reading is foreground and short, so it is not the limiting item.
