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

### [ST-005] Move the panel clear of the keyboard, and mock up the larger devices
**scope: iOS layout · asked 2026-08-08 · MOCKUPS NEED APPROVAL BEFORE CODE**

Two related pieces.

**1. The panel should sit clear of where a full keyboard lands, in portrait.**
Today the on-screen keyboard covers the bottom of the screen — the button pad
and the lower rows of the firmware's own grid — and the panel deliberately does
NOT move or rescale under it (`ios/README.md`, verified: panel geometry is
identical with and without the keyboard up). That was the right call when the
only thing that mattered was keeping the text field visible, and it is now the
wrong one: with Create Note and Claude raising a keyboard (crosspoint-reader
`daf014be`), typing is a first-class activity and the pad disappearing under the
keyboard is a real loss.

The mechanism already exists: `SimulatorOverlay::setBottomInset` reserves a
bottom band and top-aligns the panel above it, publishing `panelBottomPx()` for
the pad to anchor to. So this is reserving a keyboard-sized band rather than
inventing placement. Watch out for: the panel must not rescale on every
keyboard show/hide (that would re-lay-out the firmware's page and could churn
the reader), the read-aloud highlight geometry reads the same accessors and must
follow, and the keyboard height is not a constant — it varies by device, by
language, and with the predictive bar.

**Evidence, from a real iPad in portrait, dark, keyboard up:**
[ios/mockups/keyboard-clearance/ipad-portrait-keyboard-dark.png](ios/mockups/keyboard-clearance/ipad-portrait-keyboard-dark.png)
(owner-supplied 2026-08-08, 2048x2732). It shows three things the simulator
testing missed:

- the iOS keyboard takes the bottom **25%** of the screen and **cuts off the
  bottom rows of the firmware's own key grid** — the OK / backspace row is
  simply gone, so the owner cannot reach the key that commits the entry;
- there is a large band of dead black space ABOVE the panel. The panel does not
  need to shrink to clear the keyboard on an iPad; it needs to move up;
- the pad capsules are nearly invisible against a black field in dark mode,
  which is a separate contrast question worth answering while the layout is
  being touched anyway.

**2. Mockups for iPhone Air and iPad Pro, for approval.**

**The app is portrait-only today** — `Info.plist.in` lists exactly
`UIInterfaceOrientationPortrait`, plus `UIRequiresFullScreen`. So landscape is
not a layout tweak; it is enabling an orientation the harness has never run in,
and the geometry contract (`.claude/PLAN-tts-read-aloud.md`) says "portrait
only" in as many words. Mock it before building it.

Cover: iPhone Air and iPad Pro, portrait and landscape, each with and without
the keyboard up, showing where the panel, the pad and the text field sit. An
iPad in landscape is mostly empty either side of a 528x792 panel — what goes
there is the actual design question, and "nothing" is a legitimate answer.

**How to present them for approval** (this has gone wrong before): put the
mockups INTO the decision surface — `AskUserQuestion` option previews carrying
the rendered image, or an inline widget — rather than sending a file chip or a
link and asking a question in the same turn. A sent link does not count as the
owner having seen it. If that is impossible, the turn that delivers the visual
ends with "say seen", and the decision questions come in a LATER turn.

**Close by:** approved mockups, then the portrait keyboard-clearance change;
landscape only if the mockups earn it.

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

### [ST-004] The page as UIAccessibility elements — SHIPPED, unverified on device
**scope: accessibility · asked 2026-08-08 · in build-41**

The panel is one opaque GPU texture, so VoiceOver, Speak Screen, Braille and
Switch Control saw nothing at all. [ios/CrossPointAccessibility.mm](ios/CrossPointAccessibility.mm)
publishes the page the read-aloud channel already carries as accessibility
elements over a transparent, non-interactive container above the SDL view.

**Per LINE, not per word.** Speak Screen reads elements in sequence and
concatenates them; per-word elements would put a pause after every word. Word
rects sharing a `y` are merged, and the label is the text slice from the first
to the last byte offset on that line.

**Not a second channel consumer** — the contract is one per build. The read-aloud
adapter's existing drain hands the page over, so there is still exactly one
reader on iOS.

**Independent of the read-aloud toggle.** Capture is wanted when the toggle is
on OR an assistive technology is running, but SPEECH still follows the toggle
alone: turning VoiceOver on must not start the app talking over it. The two
edges are tracked separately for that reason.

**Verified in the simulator:** 125–140 word rects collapse to 20 line elements
per page, labels are whole lines ("off exactly at midnight. The little"), frames
land in the right place in points, elements rebuild on every page turn, and the
overlay does not steal touches — the pad still opens a book.

**NOT verified, and it cannot be here: Speak Screen does not exist in this
simulator.** Its Spoken Content pane offers only Speak Selection and
Pronunciations — no Speak Screen row — so `UIAccessibilityIsSpeakScreenEnabled()`
reads 0 and the two-finger gesture does nothing. This needs a phone.

**Close by, on the device:** Settings > Accessibility > Spoken Content > Speak
Screen on, open a book, two-finger swipe down from the top. The log line
`[A11Y] assistive tech: speakScreen=1` confirms detection; `[A11Y] N word rects
-> M line elements` confirms the page reached it. Worth judging at the same
time: whether per-line is the right granularity for VoiceOver's swipe-to-next,
or whether it should be per-word there and per-line for Speak Screen.

---

## Carried over from the firmware's tracker

`T-004` in the firmware's [TODO.md](../crosspoint-reader/TODO.md) — "make the
simulator stop lying about the device" — is simulator work tracked there because
that is where it was raised. Its substance is `S-001` in this repo's
[BUGS.md](BUGS.md): six places where the simulator reports the opposite of the
hardware, of which the 1 MB free-heap constant is the one that matters, because
every graceful-degradation path on a 380 KB device is unreachable in the only
pre-device gate the project has.

---

## DONE

### [ST-003] Read-aloud TTS on the iOS harness — DONE
**scope: feature, two repos · asked 2026-08-07 · shipped 2026-08-08**

Apple speech reading the open book on the phone: page spoken in the owner's
Spoken Content voice, auto page-turn, per-word highlight, start from a tapped
word, behind a default-off toggle. Plan, contracts and gates:
[.claude/PLAN-tts-read-aloud.md](.claude/PLAN-tts-read-aloud.md).

WP-1 and WP-2 landed on Linux with gate G0; WP-3 (the AVSpeech adapter) had
never been compiled until 2026-08-08. It compiled and linked on the first real
build — the two defects were both GEOMETRY, and both were invisible everywhere
except on the phone:

- **The highlight scale used `HalDisplay::DISPLAY_HEIGHT`**, which is multiplied
  by `CROSSPOINT_RENDER_SCALE`. Desktop runs at 1x, where that constant equals
  the logical height and the code reads correct; iOS runs at 2x, so every
  highlight came out half-width at half the x-offset. `LOGICAL_HEIGHT` is the
  right constant. This is risk R5 in the plan, and it can only ever appear on
  the 2x build.
- **The firmware capture subtracted the font ascender from `PageLine::yPos`**,
  treating it as a baseline. It is the line's TOP (it is handed straight to
  `block->render()`), so every rect sat a full line high — the highlight lit the
  word above the one being spoken. On the first line it clamped to 0, which hid
  it. Measured against the rendered panel: yPos 0/54/90/126 put ink at
  15/68/104/137, i.e. `yPos + yOffset` plus a few px of leading.

The second one is now pinned by an ink-containment assertion in
`tests/test_read_aloud_capture.sh` — for each rect, the word's own ink band must
sit INSIDE the rect. An overlap test was tried first and was useless: a 26 px
shift against a 35 px line box still clips the word, so it passed on the broken
build.

**Verified on the iOS Simulator:** page spoken; hands-free across 8 consecutive
pages; manual page turn stops and re-speaks; BACK stops and clears; the Settings
toggle turns it off on the first frame after returning; tapping a word jumps to
it (`byteOff=543`, no page turn); the highlight sits exactly on the spoken word.

**NOT verified, and deliberately left so** (owner ruling 2026-08-08 — deferred
to the device pass rather than chased in the simulator):

| Gap | Why it is still open |
|---|---|
| Dark appearance highlight | reachable in the simulator; not run |
| A hyphen-split word lighting BOTH lines | reachable in the simulator; not run. The multi-rect path it exercises is covered by `read_aloud_core` host tests, but not on glass |
| End-of-book timeout | reachable in the simulator; not run |
| Ring/silent switch still audible | needs a physical phone — this is what `AVAudioSessionCategoryPlayback` is for (R6) |
| The owner's downloaded enhanced/Siri voice | needs a physical phone |

The first three are cheap and should ride along with the device pass, since the
phone has to come out for the last two regardless.
