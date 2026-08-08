# Known bugs and open defects — simulator

Running list for this repo, in the same format the firmware's `BUGS.md` uses.

It exists because simulator defects had nowhere to live. GitHub issues are
disabled on `natebunnyfield/crosspoint-simulator`, upstream
`crosspoint-reader/crosspoint-simulator` carries none, and the firmware's
`BUGS.md` is for firmware — so simulator findings survived only in `CLAUDE.md`
prose and agent memory. That is how `CLAUDE.md` accumulated the confidently
wrong claims it has since had to correct.

IDs are `S-NNN` so they never collide with the firmware's `B-NNN`.

A bug leaves OPEN only when there is evidence it is fixed. A passing build is
not evidence for anything you cannot observe headlessly — see the device-feel
rule in the project guide.

Format: `**[id] Title** — severity · where · status`, then what breaks, how it
was found, and what closing it requires.

---

## OPEN

### [S-003] Route handlers run on the accept worker, not the firmware task
**severity: high · scope: web server / threading · found 2026-08-07**

`WebServer::handleClient()` is an empty function (`src/WebServer.cpp:677`), so
the firmware's poll does nothing and every route handler runs on
`impl_->worker` instead (`:643`). Two consequences: unsynchronised mutation of
firmware state and the framebuffer against the render task, and — worse —
`ESP.restart()` reached from a handler calls `std::longjmp(gRebootJump, 1)` on
iOS (`src/SimulatorLifecycle.cpp:146`) against a `setjmp` taken on the **main**
thread (`src/simulator_main.cpp:101`). Longjmp across threads is undefined
behaviour, and `silentRestart()` is how every file transfer ends.

**Close by:** queueing handler invocations for `handleClient()` to drain on the
calling thread, which is what the device does.

### [S-002] Sleep/restart statics survive the iOS in-process reboot
**severity: medium · scope: iOS lifecycle · found 2026-08-07** · PARTIALLY FIXED 2026-08-07


`rebootAsPowerWake()` promotes the `*_AFTER_WAKE` schedules
(`src/SimulatorLifecycle.cpp:79`), but the consumers read the environment once
per *process* — `syntheticEventsInitialized` (`src/HalGPIO.cpp:186`) and
`screenshotEventsInitialized` (`src/HalDisplay.cpp:123`). Desktop re-execs, so
it works there; iOS longjmps into the same process, so the promotion is dead
code on the only platform that uses that path. `CLAUDE.md` states the promotion
unconditionally.

Two more of the same shape: `textEntryActive` survives a restart, leaving the
keyboard channel latched and the button map suppressed; and the jump skips
destructors, so a `RenderLock` held when `ESP.restart()` is called is never
released and the render task deadlocks on the first post-reboot frame.

**Close by:** resetting the process-scoped statics on the in-process reboot
path, and correcting the `CLAUDE.md` claim.


**Fixed for the statics half.** `src/SimulatorRebootResets.h` holds a registry
that `SimulatorLifecycle` runs immediately before both in-process jumps. HalGPIO
registers a reset for `syntheticEventsInitialized`, the pending
`syntheticEvents`, and `textEntryActive`; HalDisplay for
`screenshotEventsInitialized` and `screenshotEvents`. So the `*_AFTER_WAKE`
promotion now actually reaches its consumers on the phone, and a reboot taken
mid-text-entry no longer leaves the keyboard channel latched with the button map
suppressed.

`CLAUDE.md` no longer states the promotion unconditionally: it now says why the
desktop got it for free (`execvp` is a new process), and that anything caching
env-derived state behind a `static bool ...Initialized` must register a reset.

`tests/reboot_resets_test.cpp` pins the contract the lifecycle depends on —
everything registered runs, in registration order, and `runAll()` does not
consume the registry, because a process can reboot more than once.

**STILL OPEN, and why this entry stays:** the longjmp also skips destructors, so
a `RenderLock` held when `ESP.restart()` is called is never released and the
render task deadlocks on the first post-reboot frame. That is not a stale static
and a reset callback cannot fix it — it needs the lock either dropped before the
jump or made reentrant across it. Untouched here.

### [S-001] The simulator reports the opposite of the device in six places
**severity: medium · scope: fidelity · found 2026-08-07**

Not crashes — false confidence. Each makes a firmware path look exercised when
it never ran, and the simulator is the project's only pre-device gate.

| Reports | Device | What it hides |
|---|---|---|
| 1 MB free heap (`src/Arduino.h:41,51`) | ~380 KB, no PSRAM | every graceful-degradation gate: indexing pause, glyph prewarm, SD font streaming fallback, image/CSS/JPEG bailouts |
| `supportsAsyncRefresh()` false (`src/HalDisplay.cpp:603`) | supported | the overlapped page turn has never executed in a simulator run |
| no panic ever (`src/HalSystem.cpp:5-8`) | 225 lines of panic handling | `CrashActivity` compiles in and cannot be entered |
| battery 100%, USB always connected (`src/HalPowerManager.cpp:10`, `src/HalGPIO.cpp:930-931`) | real gauge + GPIO | charging bolt always drawn, plug/unplug repaint never fires |
| `esp_ota_get_next_update_partition()` null (`src/esp_ota_ops.h:6-8`) | valid | SD firmware update shows "Invalid firmware" before reading a byte |
| OTA pinned to NO_UPDATE (`src/simulator_ota.cpp:19-22`) | real check | the whole available→download→install flow is unreachable |

The heap constant is the worst of them: heap-constrained degradation is the code
most worth simulating and the code the simulator can least reach.

**Close by:** scoping this as its own piece of work — it is a project, not a
cleanup. A budgeted fake heap would reach most of the dead branches.

---

## FIXED

### [S-004] `getFrameBuffer()` can return null and five callers dereference it
**severity: high · scope: display · found 2026-08-07** · FIXED 2026-08-07


`HalDisplay::getFrameBuffer()` returns `nullptr` while the buffer is lent out
(`src/HalDisplay.cpp:784`), and every consumer assumes non-null:
`clearScreen` goes straight into `memset(getFrameBuffer(), …)`
(`:532`), `refreshDisplay` into `snapshotBwBase` (`:612-614`), plus `drawImage`
(`:537`), `drawImageTransparent` (`:560`) and `composeGrayscalePreview`
(`:275`).

`frameBufferLent` is a **plain `bool`** at file scope (`:114`), written by the
borrower and read by the render thread with no synchronisation, so the window is
not even deterministic.

Dormant today: nothing in this repo calls `lendFrameBufferStorage`. It arms the
moment the firmware's decode path does.

**Close by:** deciding the contract — either the callers check, or the loan
blocks/copies instead of handing back null — and making the flag an atomic
either way.


**Fixed.** All five dereferences now check. The behaviour on null is to skip,
not to substitute a buffer: whoever holds the loan owns those pixels, and the
lender's own refresh follows, so a skipped clear or blit repaints on the next
draw. `refreshDisplay` returning early matters most — converting a half-owned
buffer would have presented a torn frame rather than crashed, which is the worse
failure because it looks like a rendering bug somewhere else entirely.

`composeGrayscalePreview` keeps the last presented frame instead of compositing
from null.

### [S-010] `CROSSPOINT_NO_NETWORK` outlived the reason it existed
**severity: medium · scope: iOS features · FIXED 2026-08-07 · `d7e8b27`, firmware `f1459353`**

The flag excluded 16 TUs and gated Wi-Fi, File Transfer, font downloads and
Claude out of the iOS build. That was correct when it was written: the radio was
fake — `WiFi.scanNetworks()` returned a synthetic list and `localIP()` was
hardcoded to `127.0.0.1`, so File Transfer painted a QR code pointing at
loopback. That is B-008, the lying-control defect.

It stopped being correct at `4a98ba8`, which gave the target a real radio:
`CrossPointWiFi.mm` over NetworkExtension, in-process HTTP, Bonjour, and servers
bound to all interfaces on iOS. From then on the flag was suppressing features
that work — the mirror image of the defect it was introduced to fix.

Split into `CROSSPOINT_NO_DEVICE_FLASH`, which gates only OTA and SD Firmware
Update. Those write firmware to an ESP32 partition; no phone has one. The
exclusion list went from 16 TUs to 4.

Two conflations surfaced while mapping the guard sites, both accidental:
Bluetooth keyboard pairing sat inside the network guard (so Pair/Forget BT were
unavailable on iOS for no reason), and Download Fonts sat inside the OTA guard
(so it went out with firmware flashing rather than with networking). Both now
follow the surface they belong to.

**Verified:** `crosspoint_core` AND the `CrossPointX3` app target both link for
`arm64-apple-ios` with the network TUs restored — the app-target link is the
gate that matters, since a static library can hide unresolved symbols and that
is exactly where build 30 died. The two flash activities' absence is proven by
the same link: their rows and switch cases must be compiled out, or
`OtaUpdateActivity` could not resolve. Home renders all seven rows including
File Transfer and Claude; Settings shows Wi-Fi Networks. Device `gh_release` and
the desktop canary both build; 215/215 firmware tests, 6/6 simulator tests.

**Not confirmed on hardware:** that a transfer actually completes from another
machine. Linking is not the same as working.

**Depended on B-004.** Editing `platformio.ini` used to wipe every environment's
build directory, which is why this kind of change was avoided.

### [S-009] The pad contrast dial had its resolution in the wrong place
**severity: medium · scope: iOS settings · FIXED 2026-08-07 · `258bb14`**

Two reports, one cause: "missing all the steps between default and invisible",
and "I can't select black for dark".

Nine of the nineteen rows bought nothing, and the shim's own comment said so:
on the light side the paper is 4 levels off white, so `+1..+9` spanned
`FBFBF9 -> FFFFFD` — 1.00:1 to 1.03:1, several rows pixel-identical. Meanwhile
the two rows an owner most wants to choose between, the default (`-1`, 1.36:1)
and invisible (`0`), were **adjacent integers with nothing in between**. All the
resolution sat where nobody could see it and none where it mattered.

Those rows were spent on the gap instead. Light `+1..+9` now give 1.3 / 1.24 /
1.2 / 1.15 / 1.11 / 1.08 / 1.05 / 1.04 / 1.02; dark `-1..-8` give 1.38 / 1.29 /
1.22 / 1.16 / 1.11 / 1.08 / 1.04 / 1.02.

**Black was already reachable in dark** — level `-9` is field `121212` plus a
`-18` delta, i.e. `000000` — but its row read "Darker than the field — 1.12:1",
which names a ratio and never says black. Undiscoverable, not absent. It is
labelled `1.12:1 — black` now, and kept last because 1.12:1 against the field
really is low contrast; what earns it a row is that it vanishes into a
true-black page on OLED.

Ratios are computed from sRGB relative luminance rather than estimated, because
the delta tables and Root.plist's row labels have to agree — the standard the
existing comment sets. Root.plist is reordered strongest -> invisible, which is
display order only: `Titles` and `Values` are parallel arrays, so the stored
integers are unchanged and an existing selection still means what it meant.

**Verified:** the `+/-1` default rows are untouched, so a pad left alone is
pixel-identical; all six `static_assert`s (which pin the defaults and the 3:1,
black and white rungs) still hold, confirmed by compiling the shim rather than
by reading it; `plutil -lint` passes; every specifier still offers its own
DefaultValue. Both group footers, which described the old dead zone, were
rewritten — they were about to become false documentation.

### [S-008] `vTaskDelete` left the registry pointing at the handle it freed
**severity: high · scope: FreeRTOS shim · FIXED 2026-08-07 · `7370b10`**

`xTaskCreate` dedupes by task name on purpose — the iOS in-process reboot
re-runs `setup()` without tearing the process down, and a second `"render"`
task would orphan the first, leaving two threads writing one framebuffer. But
`vTaskDelete` freed the handle and left the registry entry behind, so the
create/delete/create sequence that reboot performs took the dedupe branch and
returned freed memory. The next `xTaskNotify()` is a use-after-free.

**Verified RED first** by `tests/task_registry_test.cpp`: without the erase only
one of two task bodies ran, because the stale dedupe returned early and never
spawned a thread. The assertion is behavioural rather than `new != old` — an
earlier version asserted pointer inequality and failed against the *fixed* code,
because the allocator reuses the just-freed block.

### [S-007] `String::toInt()` threw where Arduino returns 0
**severity: high · scope: Arduino shim · FIXED 2026-08-07 · `6f15ec6`**

It was `std::stoi`, which throws `invalid_argument` on empty or non-numeric
input and `out_of_range` past `INT_MAX`. Arduino's returns 0 and never throws,
so no firmware call site has a `try` — an uncaught exception took the whole
process down. `server.arg("page").toInt()` on a missing query arg reaches it
directly, since `argByName()` returns `String("")`.

Confirmed all three inputs throw under the old implementation. `strtol` matches
Arduino across six cases including `"12abc"` → 12.

### [S-006] `HalFile` leaked a `DIR*` for every directory it opened
**severity: medium · scope: storage · FIXED 2026-08-07 · `6f15ec6`**

`~HalFile` and `operator=(HalFile&&)` inlined only the fd half of `close()`, so
every `HalFile` holding a directory — `openNextFile()`, and `HalStorage::open()`
on a directory — leaked the handle. The SD font registry walks two roots and
Manage Files recurses, so a long session drifts toward `EMFILE`, which surfaces
as books that stop loading with an innocent file named in the log. Both now
delegate to `close()`, which already released both handles.

### [S-005] Long-press power-off fired while typing
**severity: medium · scope: input · SHIPPED 2026-08-07 · `fb49742` · UNCONFIRMED on device**

The text-entry suppression was implemented in `isPressed()` — with a comment
explaining why — and skipped in `getHeldTime()` and `getPowerButtonHeldTime()`.
POWER's host scancode is `p`, so with a text field open those two still read it
held. `buttonPressTime[]` compounded it: cleared only by `clearButtonState()` at
sleep entry, never on key-up, so a POWER press minutes earlier left a live
timestamp and the first `p` typed into a Wi-Fi password returned a hold of tens
of seconds — past the power-off threshold.

**Not headlessly verifiable, and not verified on device.**
`SDL_GetKeyboardState` is only written by the real-input path, so a synthetic
script cannot reproduce this at all. Compiles clean, desktop canary builds and
boots, six host tests pass — none of which is evidence the phone stops sleeping
mid-password.

**Close by:** on a build ≥ 33, tap POWER, open Settings > Device owner, and type
a word containing `p`. It should not sleep.

### [S-000] The deploy guard could not catch the bug it was written for
**severity: medium · scope: iOS deploy · FIXED 2026-08-07 · `94bd6a4`**

`ios/testflight.sh` regex'd every `GCC_PREPROCESSOR_DEFINITIONS` block in the
generated pbxproj and passed if **any** mentioned `SIMULATOR_DEVICE_X3`, with no
way to tell which target a block belonged to. Its own comment claimed "the
library's Release block is the one that governs", but no code selected that
block — so a define set `PRIVATE` on the app target alone still satisfied it,
which is exactly the split-brain build it exists to stop. That build shipped in
1–27.

Replaced with `xcodebuild -target crosspoint_core -showBuildSettings`, which is
scoped to the target and reports what the compiler is handed. Now also checks
`CROSSPOINT_RENDER_SCALE=2`, the other half of the same incident table.

**Verified** against the build-30 project: the two real defines report present,
while `SIMULATOR_DEVICE_X4_PRO` and `CROSSPOINT_RENDER_SCALE=1` report missing —
so the check reads real data rather than passing vacuously.
