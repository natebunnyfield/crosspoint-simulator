# Open work

Things to do that are not defects. Defects live in [BUGS.md](BUGS.md); this file
is for work that was asked for, or found and ruled worth doing, and has not
landed.

It exists so this repo has the same two trackers the firmware does — `BUGS.md`
for what is broken, `TODO.md` for what is merely owed. Before it existed, the
non-defect findings from the 2026-08-06 audit had nowhere to go and sat in a
plan file on a branch that was later deleted.

Format: `### [ST-NNN] Title` then what it is, why, and what "done" looks like.
An item leaves this file when it ships or when it is ruled out — not when it is
started.

---

## OPEN

### [ST-001] `HalFrontlight` and `HalTiltSensor` mirror nothing
**scope: HAL surface · found 2026-08-06 · verified 2026-08-07**

`src/HalFrontlight.{h,cpp}` and `src/HalTiltSensor.{h,cpp}` have no counterpart
in the firmware's `lib/hal/`, which holds exactly six HAL classes — Clock,
Display, GPIO, PowerManager, Storage, System. Nothing in the firmware calls
either one, so neither is load-bearing today.

**They should not simply be deleted.** The frontlight is real X4 Pro hardware —
`CLAUDE.md` lists frontlight state among the X4 Pro capabilities, and the SDK
ships `freeink-sdk/libs/hardware/FrontlightManager/`. A simulator that drops it
will need it back the day the firmware grows a brightness control, and the
rebuild will be done by someone who does not know this file existed.

**Close by:** an owner ruling. Keeping them costs four small files; the honest
version of keeping them is a comment at the top of each saying it is a
placeholder ahead of the firmware, so the next reader does not mistake it for a
mirror of something that exists.

### [ST-002] The legacy web-server substitute looks dead and is not
**scope: cruft that must stay · found 2026-08-06 · verified 2026-08-07**

`src/CrossPointWebServer.cpp` is 1083 lines that current CrossPoint builds never
compile — they define `CROSSPOINT_SIMULATOR_PROJECT_WEBSERVER` and use the
firmware's own server against this library's `WebServer`/`WebSocketsServer`
shims instead.

Recorded here **because it reads as obvious cruft and is not.** The macro
disables only this reduced substitute; a downstream consumer that has not
adopted the firmware-owned server still links it. Deleting it breaks those
builds silently, at link time, in someone else's repo.

**Close by:** leave it, and add a header comment saying who still needs it.
Revisit only if every known consumer is confirmed to define the macro.

### [ST-003] Read-aloud TTS on the iOS harness
**scope: feature, two repos · asked for 2026-08-07**

Apple speech (`AVSpeechSynthesizer`) reading the open book aloud on the phone:
speak the page, auto page-turn at the bottom, per-word highlight, start from a
tapped word. Behind a default-off toggle in Settings > CrossPoint X3. The plan —
contracts, gates, work packages —
is [.claude/PLAN-tts-read-aloud.md](.claude/PLAN-tts-read-aloud.md).

Status: **WP-1 and WP-2 done; gate G0 PASSED 2026-08-08.** The channel, the
full `ReadAloudCore` state machine, `queueButtonTap`, the firmware capture
(fork branch `read-aloud-capture`: display-list walk with hyphen-split
reunification and soft-hyphen stripping), and the headless audit all verified
on Linux — desktop build green, 8 host tests green,
`tests/test_read_aloud_capture.sh` pins the loop end-to-end including a real
`queueButtonTap` page turn. WP-3 adapter scaffolding is written
(`ios/CrossPointReadAloud.mm`, toggle, shim wiring) but has never met a
compiler: it needs a Mac.

**Close by:** WP-3 compiling and the plan's on-glass acceptance passing on
iOS, and the owner-facing behaviour moving into ios/README.md.

---

## Carried over from the firmware's tracker

`T-004` in the firmware's [TODO.md](../crosspoint-reader/TODO.md) — "make the
simulator stop lying about the device" — is simulator work tracked there because
that is where it was raised. Its substance is `S-001` in this repo's
[BUGS.md](BUGS.md): six places where the simulator reports the opposite of the
hardware, of which the 1 MB free-heap constant is the one that matters, because
every graceful-degradation path on a 380 KB device is unreachable in the only
pre-device gate the project has.
