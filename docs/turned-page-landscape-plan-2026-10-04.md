# Landscape for turned pages on the phone: the plan, built from the owner's answers (2026-10-04)

Owner, 2026-10-04: *"when a landscape view is active (viz wide table is
rendered), the ui and gestures need to be rotated as well. ask me questions to
develop a plan then proceed after my okay"*.

**Status: PLAN COMPLETE, AWAITING THE OWNER'S OKAY -- nothing built.**

## What exists (verified 2026-10-04)

- **The turned page.** The firmware's wide-table page ([T-021] in
  `~/src/crosspoint-reader/TODO.md`, shipped 2026-08-19) draws a table too wide
  for the upright page on a page of its own, TURNED so the reader turns the
  device CLOCKWISE to read it (`PageRotatedText`, `PageVerticalRule` in
  `lib/Epub/Epub/Page.h`; the parser's `emitBufferedTableRotated`). The page
  itself is an ordinary portrait page; only its content is turned.
- **Clockwise only.** Standing ruling 2026-08-19
  (`~/src/crosspoint-reader/docs/ui-conventions.md`): never offer a
  counter-clockwise rotation; he is right-handed.
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
   Turning the phone clockwise rotates everything, status bar included, the
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

## The plan (complete 2026-10-04, AWAITING THE OWNER'S OKAY)

1. **The signal (firmware + HAL).** The reader publishes whether the page on
   screen is turned (it holds a `PageRotatedText`) through a new host channel
   on `HalGPIO`, the reader-insets pattern: an inline no-op in the firmware's
   `lib/hal/HalGPIO.h` (nothing changes on the X3), a real atomic here, read
   through `SimulatorOverlay`. Cleared on every upright page and when the
   reader exits. Host test: publish, read, clear.
2. **Orientation (iOS).** The phone's `Info.plist.in` gains the ONE landscape
   orientation a clockwise turn produces (clockwise only, per the 2026-08-19
   ruling). The harness widens `SDL_HINT_ORIENTATIONS` to that landscape while
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
