# Landscape for turned pages on the phone: the plan, built from the owner's answers (2026-10-04)

Owner, 2026-10-04: *"when a landscape view is active (viz wide table is
rendered), the ui and gestures need to be rotated as well. ask me questions to
develop a plan then proceed after my okay"*.

**Status: QUESTIONS IN PROGRESS -- nothing built.** Building starts only after
the owner okays the finished plan.

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

## Open questions

(each is asked one at a time; the answers land in "Rulings so far")

- Q2: when the next page is upright and the phone is still held sideways -- snap
  back to portrait, or stay landscape until the phone is turned upright?
- Q3: the phone landscape layout: where the pad goes beside the page (mockups
  first, then the question).
- Q4: anything else that should rotate or stay put (to be asked once Q2 and Q3
  are settled).
