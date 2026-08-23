# The Speak Screen chain, and how to measure it

Status: 2026-08-23. Written because "No speakable content could be found on the
screen" has now cost **two** investigations — the 2026-08-09 arc that burned
~12 TestFlight builds (v42–v54) and the 2026-08-23 one this document records.
The standing rule is that a second failure in the same area gets
instrumentation, not another plausible patch. This is the instrument, the
measurement it produced, and the list of links that were checked and found
**healthy** — which is the half a chat summary always drops and the half that
stops the same candidates being re-proposed forever.

---

## 1. The chain

| # | Link | Where | How to see it |
|---|---|---|---|
| 1 | The firmware captures the displayed page's text + per-word rects | `EpubReaderActivity::captureReadAloudPage`, firmware `src/activities/reader/` | `[A11Y-FILE] CHAIN ... page=<N>B rects=<N>` |
| 2 | The channel carries it | `src/ReadAloudChannel.h`, drained by `CrossPointReadAloud_perFrame` | same line |
| 3 | The adapter holds it | `ios/CrossPointReadAloud.mm` (`g_pageUtf8` / `g_rects`) | same line |
| 4 | Panel geometry maps logical px to screen points | `src/ReadAloudGeometry.h` (pure), called from `ios/CrossPointAccessibility.mm` | `geo=1(x0,y0 xSCALE)` |
| 5a | Per-**line** `UIAccessibilityElement`s — VoiceOver, Braille, Switch Control | `CPAccessibilityOverlay` | `elements=<N>` |
| 5b | The **`UITextInput`** page view — **the only thing Speak Screen consumes** | `ios/CrossPointPageTextInput.mm` (`CPPageTextInputView`) | `view=1 frame=(...) inWindow=1` |

Speak Screen reads **5b and nothing else**. That was established by measurement
in 2026-08-09 against six other exposure mechanisms (synthetic element
containers, the explicit container protocol, `UIAccessibilityReadingContent`,
elements vended from the window, a hidden real `UITextView`, and a sentinel
matrix whose fully visible `UILabel` went unread). VoiceOver read every one of
them; Speak Screen read none. The recipe that works is WWDC26 session 219,
"Enhance the accessibility of your reading app": the protocol adopted **in its
entirety** on the accessibility element itself.

---

## 2. The instrument

One line answers all five links at once. It is throttled to changes of its
*shape* plus one line per five seconds, so it costs nothing in an ordinary
session.

```
CHAIN wants=1 page=765B rects=142 geo=1(34,124 x0.667) view=1 \
      frame=(34,124 352x528) inWindow=1 host=SDL_uikitmetalview elements=21
```

- `wants` — `wantsReadingPage()`: Speak Screen on, or the override.
- `page` / `rects` — what the adapter is holding, i.e. links 1–3.
- `geo` — link 4; `0(0,0 x0.000)` means the panel has not presented yet, which
  is normal for the first ~600 ms and self-heals.
- `view` / `frame` / `inWindow` — link 5b.
- `elements` — link 5a.

It is written by `CrossPointAccessibility_logChain` and goes through
`CrossPointDiag_log`, so it lands in `diagnostics/a11y.log` on the card (Files
app → On My iPhone → CrossPoint X3 → diagnostics) and mirrors to `SDL_Log`.

**Diagnostics are OFF by default** (owner ruling 2026-08-09). Two doors:

- On a phone: **Settings.app → CrossPoint X3 → Diagnostics Log**.
- Headless: **`CROSSPOINT_SIM_DIAGNOSTICS=1`**. Added 2026-08-23 — a sandboxed
  app's `NSUserDefaults` live in its data container, so `simctl spawn defaults
  write <bundleid>` writes a store nothing reads (see `ios/README.md`), and
  before this there was no way to turn the instrument on for a scripted run.
  It can only ENABLE; the owner's Off is never overridden by anything but an
  explicit run.

---

## 3. **Speak Screen CAN be tested in the simulator.** It was never true that it could not.

`ios/README.md` recorded, and every session since believed, that
"Speak Screen cannot be tested in the simulator — its Spoken Content pane
offers only Speak Selection, so `UIAccessibilityIsSpeakScreenEnabled()` reads 0
there." That belief is a large part of why the 2026-08-09 arc had to be run on
TestFlight, twelve builds at a time.

The pane is named *Speak Screen*; the preference behind it is not. From
`libAccessibility.dylib`'s own strings the key is **`SpeakThisEnabled`**
(`_AXSSpeakThisEnabled`, `com.apple.accessibility.SpeakThisEnabled`) — Speak
Screen shipped as "Speak This" internally. Writing it to the **system** domain
(not the app's container — this one really is a system preference) makes the
API return true:

```bash
xcrun simctl spawn <udid> defaults write com.apple.Accessibility SpeakThisEnabled -bool true
```

Measured 2026-08-23, iPhone Air simulator, iOS 26.5:

```
[A11Y-FILE] assistive tech: speakScreen=1 voiceOver=0 switchControl=0
```

with the full chain following. `SpeakScreenEnabled` — the obvious guess — is
accepted by `defaults` and read by nothing.

What still cannot be done in a simulator is **invoking** Speak Screen (the
two-finger swipe down from the top edge) and hearing it speak. `simctl` cannot
synthesize a two-finger swipe and XCUITest has no public multi-finger swipe. So
the *exposure* is fully testable off-device; the *speech* is not.

---

## 4. What the 2026-08-23 measurement found

Instrumented build, iPhone Air simulator (`663B0B14`), X3, render scale 2, zen
mode on (the shipped default), English Fairy Tales.

### Healthy — every link, on a page with text

```
CHAIN wants=1 page=520B rects=94  geo=1(34,132 x0.667) view=1 frame=(34,132 352x528) inWindow=1 elements=16
CHAIN wants=1 page=765B rects=142 geo=1(34,124 x0.667) view=1 frame=(34,124 352x528) inWindow=1 elements=21
CHAIN wants=1 page=814B rects=139 geo=1(34,132 x0.667) view=1 frame=(34,132 352x528) inWindow=1 elements=22
```

Confirmed through **Apple's real out-of-process AX channel** (`tools/axprobe`,
XCUITest — the same channel Speak Screen uses, not the app's in-process dump):

```
AXPROBE staticTexts count: 22
AXPROBE [0] label="applies to the collection of the"    frame=(39.3, 136.7, 271.3, 23.3)
AXPROBE [1] label="Brothers Grimm and to all the other" frame=(39.3, 160.0, 316.7, 23.3)
AXPROBE page-textinput exists: true frame=(34.0, 132.0, 352.0, 528.0)
```

The frames were checked against the rendered screenshot: the element for
`"By Anonymous"` reported `(139,137 142x23) pt` and the glyphs measure
`(137..283, 141..153) pt` on the 1260×2736 capture. The mapping is right.

Also verified healthy, each of which had been proposed as a suspect:

| Checked | Result |
|---|---|
| `CrossPointAccessibility.mm` / `CrossPointPageTextInput.mm` compiled into the app | yes — `ios/CMakeLists.txt` :49/:53 and :78/:80, and the AX runtime serves the view |
| The render-scale change 3 → 2 (`f549b4c`) | **not implicated.** The scale is derived from the *presented* panel width, so it is render-scale independent by construction. Pinned by `tests/readaloud_geometry_test.cpp` |
| Zen placement / panel moved (`79b4fc8`, zen default on) | **not implicated.** Zen moves the panel, `panelBottomPx`/`panelLeftPx` follow, geometry tracks: `[zen] panel 1056x1584 at 102,396` → `geo=1(34,132 x0.667)` |
| The preset-list push (`525c768`) and the removed drawer sliders (`a7d256d`) | **not implicated.** Neither is in the hierarchy unless presented |
| Frozen getters / removed keys in `CrossPointPrefs.mm` | **not implicated.** `readAloudEnabled`, `readAloudRatePercent` and `diagnosticsEnabled` all still read `NSUserDefaults` and all three rows are still in `Settings.bundle/Root.plist` |
| `CPXShakeCatcher` (zen, 2026-08-22) burying the page view | no — the page view is added last to the host and `inWindow=1` throughout |
| Backgrounding and returning to the foreground | survives; `view=1` unchanged across the cycle |
| 24 consecutive page turns | every page published a non-empty capture (20–143 rects). **No hole in the firmware capture path** |
| `UIAccessibilityIsSpeakScreenEnabled()` | not deprecated in the iOS 26.5 SDK; returns true off `SpeakThisEnabled` (§3) |

### The one condition that reproduces the message

**The displayed page genuinely has no text.** The firmware then publishes an
empty capture, the adapter clears, and the container is correctly empty:

```
[ERS] Loading file: OEBPS/wrap0000.xhtml, index: 0
CHAIN wants=1 page=0B rects=0 geo=1(34,124 x0.667) view=0 frame=(0,0 0x0) inWindow=0 elements=0
```

`wrap0000.xhtml` is the book's **cover wrapper** — an `<img>` and nothing else.
Two things follow, and both matter:

1. It renders as an **entirely blank panel**. Measured: the whole panel area is
   three adjacent code values, no ink at all. The cover image is dropped (one
   of the fourteen "book notes" the firmware now raises is *images dropped*).
2. It is **the page a book opens on**, and the page a reader resumed at
   `spine=0 page=0` lands on. So the very first thing an owner sees after
   opening a book is a blank page on which Speak Screen says, accurately,
   that there is nothing to speak.

Per the 2026-08-09 scope ruling ("only EPUB text is speakable; Home, menus and
`.txt`/`.xtc` publish nothing, and *no speakable content* there is correct
behavior") this is working as designed. From the owner's chair it is
indistinguishable from the bug that ruling was written after.

### One minor defect found, NOT fixed (a proposal, not a change)

The page view's frame is set when `setPage` runs, and nothing re-frames it
afterwards. A zen relayout that moves the panel between publishes therefore
leaves the frame one step stale — measured at 8 pt on the run above:

```
CHAIN ... geo=1(34,132 x0.667) view=1 frame=(34,124 352x528) ...
```

It self-corrects on the next publish (the very next page turn logged
`frame=(34,132 ...)`), and 8 pt inside a 352x528 element cannot produce "no
speakable content". It is recorded rather than patched because the level-
triggered self-heal in `CrossPointAccessibility_modeChanged` watches the MODE
and the element count, not the geometry, and adding geometry to it is a change
to working code that no measurement here demands. If a device report ever
describes the reading highlight sitting slightly off the words after a layout
change, this is the first thing to look at.

### What is NOT explained

If the report was made on a **body page** — a page with visible prose — nothing
found here explains it. Every link was populated on every one of 24 such pages,
and Apple's own channel served both element sets. The remaining differences
between this measurement and an owner's phone are:

- **Invocation.** The two-finger swipe cannot be synthesized, so "iOS asked and
  got nothing" versus "iOS never asked" is still device-only.
- **Release codegen.** Measured in Debug; TestFlight ships Release. No
  mechanism is known by which `-O2` would change Objective-C accessibility
  behavior, and it was not measured — stated so the next session does not
  assume it was.

---

## 5. Running it

```bash
# Build (see ios/README.md for the first-configure recipe)
cmake --build build/ios-app --config Debug --target CrossPointX3

D=<udid>
xcrun simctl install $D build/ios-app/ios/Debug-iphonesimulator/CrossPointX3.app
xcrun simctl spawn $D defaults write com.apple.Accessibility SpeakThisEnabled -bool true

# The chain, live. QTAP:BACK opens the book from Home; each QTAP:RIGHT is one
# page forward. Page PAST the cover or you are measuring a blank page.
SIMCTL_CHILD_CROSSPOINT_SIM_DIAGNOSTICS=1 \
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='4000:QTAP:BACK;10000:QTAP:RIGHT;14000:QTAP:RIGHT' \
  xcrun simctl launch --console-pty $D com.natebunnyfield.crosspoint.x3

# Apple's real AX channel
cd tools/axprobe && xcodegen generate
xcodebuild test -project AXProbe.xcodeproj -scheme AXProbe -destination "id=$D"

# The pure geometry, on the host
tests/run_all.sh -k readaloud
```

`CROSSPOINT_SIM_FORCE_SPEAKSCREEN=1` still forces `wantsReadingPage()` for runs
that do not want to touch the system preference. Prefer `SpeakThisEnabled`: it
exercises the branch a phone actually takes.

### Traps that cost time on 2026-08-23, in the order they were hit

1. **The build failed on a firmware TU the source set did not know about**
   (`XmlEncodingSupport.cpp`, added uncommitted by a concurrent session).
   `cmake/CrossPointSources.cmake` is generated and pinned to a firmware
   commit; regenerate it rather than believing the link error.
2. **`cmake --build` after a source-set change needs a second invocation.**
   The first regenerates the `.xcodeproj`; `xcodebuild` in that same run uses
   the project it was handed at the start, so it links against the old object
   set and fails with the same undefined symbol.
3. **The firmware's own log goes to stdout, not `os_log`.** `simctl spawn log
   show` shows the `SDL_Log` half and none of the `[ACT]`/`[ERS]`/`[SCT]`
   lines. Launch with `--console-pty` or the activity trail is invisible.
4. **The reader opens on a blank page** (above). Four consecutive runs read as
   "the chain is dead" when they were measuring a cover wrapper.
5. **The tree dump used to fire on the first publish**, which is always that
   same empty cover page — so every dump ever collected for this bug was of an
   empty container over a page with nothing in it. Fixed 2026-08-23: it fires
   on the first page that has text.

---

## 6. Tests that now hold this

| Test | Holds |
|---|---|
| `tests/readaloud_geometry_test.cpp` | `src/ReadAloudGeometry.h`: not answerable before the first present (the level-triggered self-heal depends on it), the iPhone Air's measured numbers, `panelBottom` as an EDGE not an origin, a scale-less screen meaning 1x rather than a NaN frame, a strictly positive scale, and that `DISPLAY_HEIGHT` in place of `LOGICAL_HEIGHT` produces a detectably wrong answer. Mutation-checked: three separate breakages of the header each fail it |
| `tools/axprobe` `testSpeakScreenIsServedThePageWithASaneFrame` | through Apple's real out-of-process channel: the `crosspoint.page-textinput` element exists, carries non-empty text, and is framed over the screen rather than collapsed or off it |
| `tools/axprobe` `testRealSpeakScreenFlagReachesThePageView` | the same on the SHIPPED branch (`SpeakThisEnabled`), not the override. Skips, rather than fails, on a simulator where the flag was not set |

All three pass as of 2026-08-23 against the instrumented build:

```
AXPROBE page-textinput value: 715 chars -- "proceeded to climb over. Up came the dog and ran off with th"
AXPROBE page-textinput frame=(34.0, 132.0, 352.0, 528.0) screen=(0.0, 0.0, 420.0, 912.0)
AXPROBE real-flag page-textinput value: 705 chars
** TEST SUCCEEDED **
```

The middle line is the one that matters most: the SHIPPED branch — real
`SpeakThisEnabled`, no override — builds the page view and hands 705 characters
of the displayed page to Apple's own out-of-process channel.
| `tests/test_read_aloud_capture.sh` | links 1–2 end to end against a generated EPUB |
| `tests/read_aloud_channel_test.cpp`, `tests/read_aloud_core_test.cpp` | the channel's hand-off contract and every state transition |

None of these can see whether iOS *speaks*. That remains device-only.
