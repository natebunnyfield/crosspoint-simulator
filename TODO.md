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

### [ST-007] The README no longer describes what this repo is
**scope: docs · opened 2026-08-15**

This fork has grown well past its README: an iOS target (135 firmware TUs + 20
sim TUs for `arm64-apple-ios`), the read-aloud page channel, host keyboard text
entry with the software-keyboard show/hide contract, pad contrast presets, panel
palette and dark-mode re-present, `SimulatorOverlay` chrome, and Mac App Store +
TestFlight packaging. It is also now **0 behind upstream** and 299 ahead — by a
wide margin the most developed simulator in the ecosystem, which the README does
not say.

A README that describes a smaller project than the one it ships is the first
thing a new contributor reads, and every stale line costs someone a session.

Paired with **T-016** in the firmware repo — the owner asked for both READMEs to
match what their repos actually provide, so neither is done until both are.

Check each claim against the tree before keeping it; no claim without a grep.

**Done looks like:** the README describes the desktop app, the iOS target and
the headless QA channels as they exist today, and lists nothing that is not
there.

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

**Second owner screenshot (2026-08-09, iPad portrait, light, Create Note,
iOS keyboard up) pins THREE repeated overlap areas:**

1. **Side-button hint brackets ↔ editor text.** The left `^` and right `v`
   hint brackets are drawn at the panel edges mid-height, and the note's text
   lines run straight through the left bracket. The editor reserves a right
   gutter for hints (`NoteEditorActivity` sideGutter) but the brackets render
   at panel-relative positions that cross the text column on the iPad aspect.
2. **iOS system keyboard ↔ the firmware's own key grid.** The system keyboard
   covers the grid's bottom rows (the dimmed shapes behind the suggestion bar
   are the buried pads/rows) — the panel does not move up. This is the core
   ST-005 clearance problem; the owner's note text in the screenshot says it
   verbatim.
3. **Harness pad buttons ↔ panel content.** The two pale rounded pads float
   mid-screen inside the panel's content area (left/right, ~mid-height) in
   this layout instead of sitting in reserved chrome, and a second pair is
   buried under the system keyboard.

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

### [ST-006] iOS keyboard Return must insert a newline, not press Select
**scope: iOS input · asked 2026-08-09**

In Create Note with the iOS keyboard up, Return acts as the Select button
instead of inserting a line break. Mechanism: while text entry is active the
host-keyboard channel suppresses the scancode→button map for letters, but
Return still reaches BTN_CONFIRM. The channel already defines `\n` as the
commit byte for single-line fields (Wi-Fi password, owner name), so the fix is
to route Return INTO the typed-text channel as `\n` during text entry and let
the consumer decide: single-line fields keep treating it as commit, the
multi-line note editor inserts a real newline. Touches HalGPIO (simulator) and
NoteEditorActivity's typed-text handling (firmware). Owner report with
screenshot (iPad, 2026-08-09).

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

**ROOT CAUSE, found 2026-08-08 after two wrong fixes: the container reported
zero children.** `CPAccessibilityOverlay` overrode `-accessibilityElements`,
which reads like the obvious thing and is silently useless — UIKit answers
assistive technology through the `UIAccessibilityContainer` methods, and UIView
derives those from the STORED property, not from an override of its getter. So
the container sat in the tree, front-most and correctly framed, reporting
`accessibilityElementCount = 0`. Every build said "no speakable content could be
found on the screen", with or without a page turn, because as far as iOS was
concerned there were no children.

Fixed by implementing `accessibilityElementCount` /
`accessibilityElementAtIndex:` / `indexOfAccessibilityElement:` explicitly AND
setting the stored property, so both paths work.

**What actually found it:** `CrossPointAccessibility_dumpTree()`, which walks
the hierarchy with the same public API an assistive technology uses. Before:
`CPAccessibilityOverlay children=0 … reachable labeled elements: 0`. After:
`children=22` with real book text on each. Two prior fixes were reasoned from
what UIKit "should" do and were both wrong; the traversal answered it in one
run. The dump is kept, one-shot per launch, because it is the fastest way to
tell on a device whether the page or the traversal is at fault.

**The earlier timing fix (below) was real but not the cause** — it was masking
nothing, since nothing was reachable either way.

**Build 42 reported "no speakable content could be found on the screen" —
first diagnosis, incomplete.** The container and the elements were fine; the
page never reached them. Capture was gated on (toggle OR assistive tech), and
the firmware publishes a page only when it RENDERS one — so switching Speak
Screen on while a page was already drawn flipped capture to wanted and then
published nothing until the next page turn. An owner who opens a book and then
swipes gets an empty container every time.

Three changes: capture is now UNCONDITIONAL on iOS (a display-list walk per
render is noise on a phone, and correctness beats it); the adapter republishes
its cached page whenever the container is empty but a page is in hand; and the
container is re-raised every frame, because accessibility traversal is
front-to-back and SDL rebuilds its views across a wake. Verified: elements now
build with ZERO page turns and with every assistive flag reading 0.

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

### [ST-001] `HalFrontlight` and `HalTiltSensor` mirror nothing — RULED KEEP
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

**Closed 2026-08-08 by doing what the close condition asked**: each file now
carries a header saying why it exists and that it is ruled KEEP, so the next
reader who greps for callers, finds none, and reaches for the delete key is
answered in place rather than having to find this file.

### [ST-002] The legacy web-server substitute looks dead and is not — RULED KEEP
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

**Closed 2026-08-08 by doing what the close condition asked**: each file now
carries a header saying why it exists and that it is ruled KEEP, so the next
reader who greps for callers, finds none, and reaches for the delete key is
answered in place rather than having to find this file.


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
