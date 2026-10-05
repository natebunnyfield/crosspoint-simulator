# Landscape for turned pages on the phone: the plan, built from the owner's answers (2026-10-04)

Owner, 2026-10-04: *"when a landscape view is active (viz wide table is
rendered), the ui and gestures need to be rotated as well. ask me questions to
develop a plan then proceed after my okay"*.

**Status: SHIPPED 2026-10-04, built on the owner's okay ("yes").** TestFlight build 304 had the DIRECTION mixed up; it is corrected in the build after it (see "The direction, corrected" at the foot).
- **The direction:** the table is turned CLOCKWISE on the page (header down the right edge), so the reader turns the phone COUNTER-clockwise, and the phone rotates on that turn only (`UIInterfaceOrientationLandscapeRight`). Owner, correcting build 304: *"the iphone would need to be turned ccw not clockwise, you've mixed things up"*.
- Two adversarial reviews, every finding handled; both are at the foot of this doc. They describe the code as it then stood, with build 304's flip in it.
- Verified in the iOS Simulator (iPhone Air and iPad Pro 13). The direction is verified by the Simulator's own screen capture, which is in DEVICE coordinates.
- The firmware commits are LOCAL. The firmware fork's `main` was 26 commits behind, and pushing it is not covered by the standing push rule. The TestFlight build compiles from the local checkout.
- Device feel UNCONFIRMED until tried on the phone.

## What exists (verified 2026-10-04)

- **The turned page.** The firmware's wide-table page ([T-021] in
  `~/src/crosspoint-reader/TODO.md`, shipped 2026-08-19) draws a table too wide
  for the upright page on a page of its own, TURNED (`PageRotatedText`,
  `PageVerticalRule` in `lib/Epub/Epub/Page.h`; the parser's
  `emitBufferedTableRotated`). The page itself is an ordinary portrait page;
  only its content is turned: the TABLE turned clockwise, header down the
  page's right edge, so the reader turns the device COUNTER-clockwise. (This
  line once said "so the reader turns the device CLOCKWISE". That reading of
  the ruling is what build 304 shipped and the owner corrected.)
- **Clockwise only.** Standing ruling 2026-08-19
  (`~/src/crosspoint-reader/docs/ui-conventions.md`): never offer a
  counter-clockwise rotation; he is right-handed. "Clockwise" names the
  table's rotation on the page; the device's turn is the opposite one.
- **The phone is portrait-only.** Owner ruling 2026-08-17, recorded in
  `ios/Info.plist.in`: landscape on iPad only. A phone landscape attempt put the
  panel in a corner and stacked the pad as a column down one edge. The iPad's
  landscape layout puts the pad BESIDE the panel
  (`ios/CrossPointIOSShim.cpp`, around line 776). `SDL_HINT_ORIENTATIONS` is set
  per device class in `src/simulator_main.cpp` (around line 330).
- **The app cannot tell a turned page is showing.** Nothing crosses from the
  firmware to the host about it today; it needs a new host-capability channel,
  the same pattern as the reader text insets.

## Rulings so far

1. **Mechanism: ROTATE THE APP WITH THE PHONE** (Q1, 2026-10-04; the first
   answer, "follow the phone's tilt", was a misclick, and the question was
   re-asked). While a turned page is showing, the app accepts landscape.
   Turning the phone (counter-clockwise; see the direction section at the foot)
   rotates everything, status bar included, the
   table is shown upright, and the pad moves beside the page as on the iPad.
   Gestures follow on their own because touches arrive in the rotated frame.
   This reopens the 2026-08-17 portrait-only ruling FOR THESE PAGES ONLY, and
   the phone landscape layout gets designed with mockups before any building.

2. **Leaving: SNAP BACK TO PORTRAIT** (Q2, 2026-10-04). When the next page is
   upright and the phone is still sideways, the app returns to portrait at
   once; an upright page is never shown in a landscape window.

3. **The pad: BESIDE THE PAGE when zen is off** (Q3, 2026-10-04; recommended
   was zen-only in landscape). Landscape shows the pad beside the page, as on
   the iPad, whenever zen is off; in zen there is no pad either way. The phone
   landscape pad layout is designed from mockups before anything is built.

4. **The pad's place: G3, SPLIT, AND PAPER ON THE PANEL ONLY** (Q3b,
   2026-10-04, from mockups https://claude.ai/artifact/D2m4zmimWGaZrvLd4MzseU):
   *"G3 but only the panel gets paper treatment"*. Today's pad split down the
   middle: its left half (Back/Select, Power) in the left margin, its right
   half (Left/Right, Up/Down) in the right margin, the page centered between,
   about 15% smaller than full height. Only the panel is drawn as paper; the
   surround the pad sits on is NOT the sheet (the mockup had the sheet bleeding
   to the glass, as the phone's portrait does).

5. **Zones: FOLLOW THE PAGE** (Q4, 2026-10-04). In landscape the three zone
   overrides are measured from the landscape page's own edges, by the portrait
   rule: above it, below it, left of it. The left margin becomes the whole left
   side (in zen; with zen off the pad's left half takes taps there first). The
   bands above and below are thin, so hold-above-the-paper is harder to hit in
   landscape -- accepted.

6. **Scope: PHONE AND iPAD** (Q5, 2026-10-04). On the iPad, which already
   rotates freely, a turned page in landscape also shows upright, with the
   iPad's existing landscape layout around it; same signal, same snap-back.

## The plan (complete 2026-10-04; okayed and built the same day)

1. **The signal (firmware + HAL).** The reader publishes whether the page on
   screen is turned (it holds a `PageRotatedText`) through a new host channel
   on `HalGPIO`, the reader-insets pattern: an inline no-op in the firmware's
   `lib/hal/HalGPIO.h` (nothing changes on the X3), a real atomic here, read
   through `SimulatorOverlay`. Cleared on every upright page and when the
   reader exits. Host test: publish, read, clear.
2. **Orientation (iOS).** The phone's `Info.plist.in` gains the ONE landscape
   orientation the reader's turn produces: counter-clockwise, as corrected
   after build 304 (the plan said clockwise, misreading the 2026-08-19 ruling). The harness widens `SDL_HINT_ORIENTATIONS` to that landscape while
   the signal is up, narrows it back to portrait when it drops, and asks UIKit
   to re-read (`setNeedsUpdateOfSupportedInterfaceOrientations`). SDL3 re-reads
   the hint on every query (`SDL_uikitwindow.m`, `UIKit_GetSupportedOrientations`),
   so this is the supported path; it is the first thing to prove in the iOS
   Simulator. The decision ("which orientations now?") is a pure function,
   host-tested.
3. **Presentation.** In a landscape window with the signal up, the panel is
   drawn with one more quarter turn, so the table reads upright, centered.
   Paper treatment only on the panel: the sheet does not bleed into the
   surround, which stays dark. Zen: the page at full height. Zen off: G3, the
   pad's left half (Back/Select, Power) in the left margin and its right half
   (Left/Right, Up/Down) in the right, the page sized to fit between them. A
   new phone-landscape branch of `layoutPad`, with the rects host-tested at
   the phone sizes. iPad: its own landscape layout, with only the quarter turn
   added.
4. **Gestures.** Touches arrive in the rotated frame, so the swipes follow by
   themselves. The three zones are recomputed from the landscape page's edges
   (above, below, left of it), the portrait rule; the boundaries the zones
   already read (`g_cardTopPx`, `g_zenRowTopPx`, `panelLeftPx`) are published by
   the landscape layout too. Truth-table test in `gesture_bindings_test`.
5. **Snap back.** The signal dropping narrows the orientations at once, so
   iOS returns the app to portrait even with the phone still sideways.
6. **Verification.** Desktop canary build green; host tests; the iOS Simulator
   with `test_wide_table.epub` -- rotate, capture, compare against the G3
   mockup; the firmware's device build green. Device feel is UNCONFIRMED until
   it is tried on the phone.
7. **Ship.** Firmware and simulator commits, TestFlight at 0.1.1, push to the
   forks (never upstream). Adversarial review before the build.

Risks named up front: SDL3's runtime orientation change is unproven here until
step 2 is tried; the 2026-08-17 failure (the pad stacked as a column) came from
enabling landscape with no layout for it, which step 3 exists to prevent; and
the firmware change touches the reader and the HAL header, so the device build
is part of the check.

## Open questions

(each is asked one at a time; the answers land in "Rulings so far")

none -- the plan is complete.

## As built (2026-10-04)

**Firmware** (`~/src/crosspoint-reader`): `lib/hal/HalGPIO.h` gains
`publishTurnedPage(bool)`, an inline no-op (nothing changes on the X3).
`EpubReaderActivity` publishes it once per displayed page in `renderContents`
(true when the page holds a `PageRotatedText`) -- since the review, AFTER the
page's first `displayBuffer` rather than before the render -- and false on the
end-of-book screen, on a build error, in `onExit`, and (since the review) on the
Empty chapter, Out of bounds and Page load error screens and before every
Indexing popup.

**Simulator** (this repo):
- `src/HalGPIO.cpp` over `src/TurnedPageChannel.h`: the channel, one atomic, a
  change requests a present; cleared by the reader, by every non-reader screen
  (`publishScreenIdentity`) and on the iOS in-process reboot. Read through
  `SimulatorOverlay::turnedPageShowing()`.
- `src/HalDisplay.cpp`: `SimulatorOverlay::setPresentLandscapeUpright` substitutes
  `LandscapeCounterClockwise` for the renderer's orientation in every
  presentation decision: on a turned page the framebuffer's native landscape
  frame IS the table the right way up, in either landscape window. Build 304
  alone, with the page flipped, substituted `LandscapeClockwise`.
  `setSideInsets` bounds the fit horizontally as the top and bottom bands do
  vertically; in this mode the panel is centered vertically too.
- `src/TurnedPageLandscape.h` (pure; `tests/turned_page_landscape_test.cpp`, in
  `run_all.sh`): the orientation hint and the G3 geometry, phone and iPad, at six
  window sizes.
- `ios/CrossPointOrientation.mm`: polled each frame; on a change of the wanted
  hint, `SDL_SetHint` plus `setNeedsUpdateOfSupportedInterfaceOrientations`. The
  phone gains `LandscapeRight` (a counter-clockwise turn; build 304 had
  `LandscapeLeft`) only while a turned page shows, and dropping it is the
  snap-back. `ios/Info.plist.in` must declare it, because SDL bounds the hint
  by the plist's orientations.
- `ios/CrossPointIOSShim.cpp`: `layoutTurnedLandscape` (the split pad, the insets,
  the zone boundaries from the landscape page's edges), the black surround with
  paper on the page only, and transparent pad faces on black, as the iPad's.

**Measured in the iOS Simulator** (`CROSSPOINT_SIM_FORCE_TURNED_LANDSCAPE=1`, a QA
hatch that makes a turned page force the rotation, since a script cannot turn
the Simulator; `test_wide_table.epub`):
- iPhone Air: the page 1416 x 944 px at scale 0.894, centered between the pad's
  halves (side insets 220 pt = safe 68 + band 152).
- iPad Pro 13: 1584 x 1056 at its whole-number scale 1, centered, the front pairs
  on the tablet's thumb row (448 pt up), POWER and the rocker at half height
  along the bottom.
- Snap-back: the turned page dropped, the hint went back to "Portrait", and the
  window was portrait again 0.28 s later, the page back at 1056 x 1584 px, scale 1.

**Found while building, and handled:**
- MID-ROTATION SAFE AREA: for one frame the window is landscape but its safe area
  is still portrait's (R 560, B -472 pt on an iPhone Air), which fitted the page
  into a 6 x 4 px box. A safe area that cannot belong to the window is now
  treated as none for that frame.
- SNAP-BACK FRAMES: for the ~0.3 s iOS takes to turn back, the window is
  landscape with an upright page, which no layout is for (the portrait layout drew
  it 288 x 432 px in a corner). The phone shows black for those frames.
- THE iPad keeps its own placement (Q5): its front pairs sit on the tablet's
  thumb row rather than the phone's bottom rows.

**Found and NOT changed (not named):**
- READ-ALOUD SKIPS A TURNED PAGE AT ONCE: the capture finds no speakable line on
  it (the table is `PageRotatedText`), so read-aloud queues a page turn
  immediately. With this feature the app flicks into landscape and straight back
  out. Seen in the Simulator with read-aloud on; the fix is the capture learning
  rotated lines, which is firmware work nobody asked for.
- A HARNESS QUIRK: after `CROSSPOINT_SIM_IMPORT_FILE`'s document-open reboot, a
  `CROSSPOINT_SIM_INPUT_SCRIPT` press never reaches the reader on iOS, in
  portrait as well as landscape (control run). `*_AFTER_WAKE` is promoted only by
  the power-wake reboot. Verification therefore reached the table page from
  saved progress instead.

## Adversarial review (2026-10-04), and what was done about each finding

One read-only agent, briefed to refute and to report what it checked and found
clean, over the build commits (firmware `5f0dc54e5`, simulator `0248ea1`). It
reported eight findings. All eight are answered below: six fixed, two recorded
and deliberately not changed. Each fix is verified by a test or a Simulator
capture, and where a "before" was only inferred, the entry says so. Captures
are from the iPhone Air and iPad Pro 13 Simulators with
`CROSSPOINT_SIM_FORCE_TURNED_LANDSCAPE=1`, booted into the book by pinning
`readerActivityLoadCount` to 0 (docs/headless-qa.md).

1. **The phone accepted only the turn that showed the table upside down**
   (would-ship-a-visible-bug). The firmware drew the page with
   `drawTextRotated90CCW`, putting the header down the page's RIGHT edge, so the
   page read after a COUNTER-clockwise turn. The phone accepted only
   `LandscapeLeft`, which is a clockwise turn. The force hatch hid this, because
   the page is upright in either landscape window.
   **REVERSED THE SAME DAY.** The resolution below flipped the page to read
   after a clockwise turn and shipped as build 304. The owner then corrected
   the premise: *"the iphone would need to be turned ccw not clockwise, you've
   mixed things up"*. The page is restored and the phone rotates on a
   counter-clockwise turn; see "The direction, corrected" at the foot. What
   follows records what was done at the time.
   **Owner ruling, asked in turn terms:** *"Clockwise: fix the page"*.
   **Fixed in the firmware** (`lib/Epub/Epub/parsers/RotatedTablePlacement.h`):
   every line and the header rule sit at the old spot turned 180 degrees and
   are drawn with `drawTextRotated90CW`. `SECTION_FILE_VERSION` is 63, so every
   cached section rebuilds. `test/rotated_text` checks the turn pixel for pixel:
   three line placements and the rule. It fails on a one-pixel placement error,
   which was checked by mutating the header and watching both tests fail. The
   app's substitution is now `LandscapeClockwise`.
   **Verified:** in the portrait capture the header runs up the LEFT edge and
   each run climbs. In landscape the table is upright, header on top, text left
   to right.
   **Not changed: Portrait Orientation Lock.** With the lock on, iOS keeps the
   app portrait whatever the mask says. The turned page then reads as it does on
   the X3, by turning the phone. That is the lock doing its job.
   **One conflict in the record:** `tools/table_preview` built the 2026-08-19
   renders as the page that needs a counter-clockwise turn. Recorded in the
   firmware's TODO.md [T-021] and docs/ui-conventions.md.
2. **Screens pushed over a turned page were shown sideways**
   (would-ship-a-visible-bug). A push (the chapter list on Select, Find) never
   runs the reader's `onExit`, so the flag outlived the page.
   **Fixed:** `HalGPIO::publishScreenIdentity` clears the latch
   (`src/TurnedPageChannel.h`, host-tested). The firmware also publishes false
   before the Empty chapter, Out of bounds and Page load error screens and before
   every Indexing popup.
   **Verified:** Select on the turned page logged
   `[orient] turned page down -> hint "Portrait"`, and the chapter list came up
   upright in portrait. The channel test also covers the gap the review named,
   that plan step 1 had promised a test for the signal and none existed.
3. **iPad: after a turned page, zen blacked out the bottom of every later
   page** (would-ship-a-visible-bug, iPad with zen on). `g_zenRowTopPx` kept the
   landscape page's bottom edge.
   **Fixed:** it is zeroed on the non-turned path before the tablet layout.
   **Verified:** on the iPad with zen on, the turned page landscape, then RIGHT
   to an upright page with snap-back to portrait. The page reads as paper from
   its top down to its own bottom (y 1550-1960 px: mean 236, 0% black). The old
   cut line would have sat at y 1543. The "before" is the review's reading of
   the code, not a measurement.
4. **Phone: sleeping from a turned page left the glass black for the whole
   sleep.** The terminal sleep loop never returns to `perFrame`, so the
   snap-back hint was never applied.
   **Fixed:** `SimulatorOverlay::setSleepTick`. The sleep loop calls the host's
   tick on every iteration. The iOS tick follows the orientation, runs the
   settle repaint and presents whatever is owed. `presentIfNeeded`'s own veto
   still keeps a power-off collapse's dark glass dark. The desktop installs
   nothing.
   **Verified:** Power on the turned page, then deep sleep. The hint was
   "Portrait" within a few milliseconds; the firmware's clock and the host log's
   clock differ, so there is no finer figure. The window was portrait 29 ms
   after that, on one clock, with the panel re-presented at scale 1. The Simulator's own screen capture shows the sleep
   screen in portrait. The three desktop sleep-loop tests (`test_sleep_wake`,
   `test_foreground_wake`, `test_queued_tap_wake`) pass.
   **Side effect, inferred and not measured:** any window change during sleep
   is now presented. An iPad rotated while asleep used to keep its last frame.
5. **The turned flag was published before the page was drawn** (cosmetic).
   **Fixed:** it is published after the page's first `displayBuffer`, including
   the image-placeholder pass. Not separately measured; it is a one-frame
   artifact on an iPad held landscape.
6. **A stale safe area during rotation could stick** (latent).
   **Fixed:** `SDL_EVENT_WINDOW_SAFE_AREA_CHANGED` now relayouts exactly as a
   size change does. Every landscape entry logged here shows a zero-safe-area
   pass followed within a millisecond by the real one (L68 R68).
7. **The phone can launch in landscape** (cosmetic, inferred). **Not
   changed.** SDL's app delegate does not implement
   `application:supportedInterfaceOrientationsForWindow:`, so SDL bounds the
   runtime mask by the plist (`SDL_uikitwindow.m:405-452`). Dropping
   `LandscapeLeft` from the plist would make the rotation impossible.
8. **Tilt gestures and the raking light do not know the screen turned**
   (latent; both ship unbound or off). **Not changed** (not named). If a tilt
   is ever bound to a page turn, the clockwise turn itself fires Tilt Right.

**Not a defect, recorded for the owner:** on a phone the split pad makes the
landscape page smaller than the portrait one. Scale 0.894 against 1.0 on an
iPhone Air; the review computed ~0.77 against ~0.95 on a 13 mini and ~0.44
against ~0.52 on an SE.

**Checked and found CLEAN by the review** (so the next pass need not re-read it):
- Portrait is byte-identical. With the side insets 0 and the flag off, the
  placement maths matches the old code (`HalDisplay.cpp`). The setters skip
  unchanged values, and the first orientation poll matches the startup hint.
  The desktop never calls the new setters.
- Every consumer of the substituted orientation handles it: page draws, the
  sheet's ink mapping, the lamp field, the collapse, the scanline pitch, the
  speedrun overlay, speed read, the beam, glass capture. Re-checked for
  `LandscapeClockwise` after the fix: each consumer enumerates all four
  orientations (`SurfaceSheet.cpp`, `SurfacePower.cpp`, `SurfaceSpeedRead.h`,
  `RakingLight.h`, `HalGPIO.cpp`).
- Threading: one atomic flag. The landscape flag and side insets are written
  after both reads in a present.
- Snap-back leftovers are reset: insets, pad rects, chip, card top, bezel, zen
  shift. The one exception was finding 3.
- The iOS orientation call: the window and root view controller exist before
  the first poll. The 26.0 deployment target covers the API, and
  `LandscapeLeft` is the clockwise turn.
- Firmware publish: sleep and going home both run `onExit`. The gaps were
  findings 2 and 5.
- Gesture zones: the left-margin boundary is the landscape page's left edge.
  The one exception was finding 3.

## Second adversarial review (2026-10-04), over the fixes above

A fresh read-only agent reviewed the two fix commits (firmware `1c55af44b`,
simulator `23e5110`) under the same brief. It found one visible bug, one CI
break and two cosmetic issues.

1. **With Power-Off Collapse on, sleeping from a turned page garbled the
   collapse.** This is visible, but only with that dial on (it ships off) and
   a dark page.
   **Cause:** the new sleep tick polled the orientation in the first sleep
   pass. The window turned portrait about 29 ms into the 1,020 ms collapse.
   The collapse draws from the geometry of the last real present, and
   `presentIfNeeded` is vetoed for the whole sleep, so nothing re-fitted it.
   The line and dot landed off the glass.
   **It was wrong before the tick too, just invisibly:** the phone stayed
   landscape, and the snap-back's black fill covered every collapse frame.
   **Fixed with one predicate,** `SimulatorOverlay::collapseOwnsGlass()`: the
   veto's own condition, now one definition read by the veto and by the iOS
   host. While it holds:
   - the sleep tick does not turn the window;
   - `layoutPad` keeps the turned page's landscape layout, since
     `presentLandscapeUpright()` is still set from the last real present.

   So the collapse draws the turned page in landscape, as it was on the glass,
   and the snap-back happens on the wake. Verified below.
2. **CI break: clang-format.** The firmware commit's new lines did not match
   the repo's `.clang-format` under clang-format 21 (CI runs it on every push).
   **Fixed:** formatted with 21.1.8, touching only the include's position, the
   placement lines, one comment column and a trailing blank line. Two
   violations that were already in `GfxRenderer.h/.cpp` before this work were
   left alone.
3. **Comments that had gone wrong.** The presentation comments in
   `SimulatorOverlay.h` and `layoutTurnedLandscape`; the
   `drawTextRotated90CCW` comments in `GfxRenderer.h/.cpp`, which still called
   it the clockwise page's call, the wording that produced the original
   direction bug; and every "the sleep loop never presents" sentence
   (`CLAUDE.md`, `docs/power-off-collapse.md`, `HalDisplay.cpp`,
   `SurfacePower.cpp`). All corrected; the behavior behind each was already
   guarded.
4. **Cosmetic: the turned page is the old one turned 180 degrees inside the
   VIEWPORT, not on the panel.** The X3's margins are uneven (top 9, the rest
   3) and the page is drawn at the body font's cap-ink trim, so the first
   column starts some 6-12 px further from the panel edge than before. At 2x,
   text sits one device pixel off an exact device-space mirror. Nothing clips.
   The placement header now says so, and also that decomposed accents differ:
   the old counter-clockwise path set them off center with unmirrored anchor
   arithmetic, and the clockwise path sets them correctly.

**Checked and found CLEAN by the second review:**
- **The placement maths,** against `renderCharImpl`:
  - at 1x it is an exact 180-degree turn in viewport coordinates;
  - every line keeps at least 2 px inside the viewport (rows bounded by the
    one-page check, columns by the reading axis);
  - band culling for clockwise glyphs in tiled grayscale is correct;
  - the 2x clockwise path exists and is tested.
- **The direction, derived by hand:** `LandscapeClockwise` in a
  `LandscapeLeft` window puts the header on top, text left to right, glyphs
  upright. The firmware's orientation is fixed at Portrait.
- **`SECTION_FILE_VERSION` 63:**
  - nothing checks for 62;
  - the partial-build marker derives from the version without collision;
  - no other cache holds rotated positions;
  - page counts are unchanged, so saved progress and book notes are
    unaffected.
- **The firmware publish order:**
  - no return between the turned decision and `publishTurned()`;
  - every popup and error path publishes false first;
  - every popup is followed by a render that republishes.
- **`publishScreenIdentity` clearing the flag:**
  - only `Activity::onEnter` calls it, for non-reader screens;
  - every screen pushed over the reader is a non-reader screen;
  - a pop always re-renders through `renderContents`, with no
    restore-the-old-framebuffer path.
- **The sleep tick otherwise:**
  - nothing asks for frames during sleep;
  - a call with nothing owed costs a few atomic reads;
  - the wake reboot cannot race a present;
  - the desktop installs none.
- **`SDL_EVENT_WINDOW_SAFE_AREA_CHANGED` cannot loop.** Nothing the handler or
  the layout does changes the safe area.
- **The iPad `g_zenRowTopPx` fix and `TurnedPageChannel`:** both behave as
  described.

## The direction, corrected (2026-10-04, after build 304)

**Owner, on build 304:** *"the iphone would need to be turned ccw not
clockwise, you've mixed things up"*.

**The mix-up.** The 2026-08-19 ruling ("never offer a counter-clockwise
rotation"; crosspoint-reader `docs/ui-conventions.md`) names the TABLE's
rotation on the page. A page whose table is turned clockwise has its header
down the page's right edge, and the reader reads it by turning the device
counter-clockwise. The evidence for that reading was already in the record:
- the 2026-08-19 renders he ruled on were built that way (`tools/table_preview`);
- the mockup he rejected that day was the other page, called "a
  counter-clockwise mockup" for its content;
- T-021 shipped the clockwise-content page.

`docs/ui-conventions.md`, though, said "a page the reader turns clockwise", an
agent's paraphrase. The first review took that sentence at its word. The
direction question that followed was asked in prose, in device-turn terms, with
no picture, and its answer flipped the page. The conflict was noticed and
flagged after the fact, and the flip shipped anyway.

**What changed:**
- **Firmware:** the page is restored (`RotatedTablePlacement.h` back to the
  original placement, drawn with `drawTextRotated90CCW`), with
  `SECTION_FILE_VERSION` 64. `test/rotated_text` now pins the direction itself:
  the header is the band nearest the page's right edge, and every run descends
  from the top. Both tests fail on a flipped placement (checked).
  `docs/ui-conventions.md` now says which direction a word means, and the
  paraphrase is struck with the owner's correction beside it.
- **App:** the phone accepts only `UIInterfaceOrientationLandscapeRight`, the
  home edge on the right, which is the counter-clockwise device turn (hint and
  plist). The presentation is back to `LandscapeCounterClockwise`, the native
  frame. The sleep tick, the collapse latch, the channel and every other review
  fix stand unchanged.

**Verified in the iPhone Air Simulator**, and the second item is the check that
was missing before build 304:
- the in-app portrait capture shows the header down the RIGHT edge, each run
  descending;
- the Simulator's own screen capture (`xcrun simctl io ... screenshot`, which
  is in DEVICE coordinates) of the forced landscape shows the table's top along
  the phone's RIGHT edge. So the app's landscape is reached by turning the phone
  counter-clockwise, the same turn the portrait page asks for.

The in-app landscape frame is upright. `CROSSPOINT_SIM_FORCE_TURNED_LANDSCAPE`
now forces `LandscapeRight`.

**The rule this leaves:** when a direction is in question, say whether it is
the content's rotation or the device's turn, and settle it with a picture, not
a sentence. They are always opposite, and one word ("clockwise") was read both
ways inside a single day.

