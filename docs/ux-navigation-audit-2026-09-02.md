# UI/UX navigation audit — iOS harness (2026-09-02)

**Read-only. Nothing in this file has been changed in code.** Owner asked for
a finding pass ("take a pass at finding ui/ux bugs, especially around
navigation"); which get fixed is a separate ruling. The firmware half of the
same pass is `crosspoint-reader/docs/ux-navigation-audit-2026-09-02.md`
(16 findings, six of them one root cause: the SDK's `getHeldTime()` is one
global chord timer, not a per-button hold).

Surveyed at `beda69c` (main). One read-only hunting agent over `ios/**`,
`src/HalGPIO.cpp`, `src/HostKeyboardState.h`, `src/TextEntryKeyRouting.h`,
`src/SimulatorOverlay.h`; every VERIFIED finding was then re-read
independently at the cited lines before it was written here. Two of the
agent's findings were downgraded on that re-read (P1-3, P2-7 below) — the
disproof is recorded so the next pass does not re-raise them.

## Findings, ranked

### 1 — P1 — Two of the offered one-finger Tap actions can never fire. VERIFIED

The one-finger tap is NOT a UIKit recognizer (`CrossPointZenRecognizers.mm:692`
skips `fingers < 2`); it is the SDL deliberate-tap classifier, dispatched at
`ios/CrossPointIOSShim.cpp:3155-3181`. That dispatcher knows `ToggleZen`,
`FontFamilyStep` and anything `gesturebind::buttonFor()` maps to a button
(`GestureBindings.h:200-211`); everything else logs
`[zen] tap -> %s is not handled on the SDL tap path` and returns. `Root.plist`
offers 12 (`FontFamilyStepBack`, appended 2026-08-29) and 13
(`OpenActionMenu`, 2026-09-01) on `gestureTap`, `gestureTapAbove`,
`gestureTapBelow` (decoded: `[1..10, 12, 13]` / `[11, 1..10, 12, 13]`). Bind
the tap to either → silent no-op on the gesture a reader uses most. The
comment at `:3170-3178` predicted exactly this ("if a twelfth Action is ever
appended, that is the other place to teach") and both appends missed it.
Fix: the SDL tap branch calls `performGestureAction`
(`CrossPointZenRecognizers.mm:229`) instead of keeping a second, smaller
dispatcher. Six of 29 rows affected.

### 2 — P1 — Every zen toggle drops the software keyboard, and zen has no way back. VERIFIED (mechanism; UIKit first-responder semantics assumed, not run)

`CrossPointZenRecognizers.mm:857`: `[g_shake becomeFirstResponder]` on EVERY
`CrossPointZenRecognizers_setEnabled` call (unconditional since 2026-08-29,
comment `:850-856` says why). Callers: `CrossPointIOSShim.cpp:3380` (gesture
toggle), `:1694` (Settings.app apply), `:1664` (first poll), `:3547`
(begin/wake). The keyboard is up only while SDL's hidden `UITextField` is
first responder (`CrossPointKeyboardBar.mm:18-24, 298-303`); one first
responder per window, so the keyboard resigns, and the bar rides it away
(`:246-256`). In zen nothing can raise it again — see finding 5. Trigger:
Wi-Fi password, chip, typing, rest a finger in the top ~68 pt for 0.75 s
(`HoldAbove` → ToggleZen, always on). Keyboard gone mid-password; only exit
is a second blind hold to leave zen. Fix: skip the re-assert while
`gpio.isTextEntryActive() && gpio.isHostKeyboardVisible()`, re-assert on
`SDL_EVENT_SCREEN_KEYBOARD_HIDDEN`.

### 3 — P2 — iPad portrait: the always-on zen-toggle band is the top ~194 pt. VERIFIED — an owner call, not a defect

`PadTopBand.h:60-68`: `unit = (outHpx - panelHpx)/3`, `cardTopPx = max(unit,
max(safeTop, 16pt)*scale)`; `CrossPointIOSShim.cpp:555` publishes it as
`g_cardTopPx`; `zoneFor` (`GestureBindings.h:333-338`) makes everything above
it `AbovePaper`; `HoldAbove` defaults to ToggleZen and fires outside zen
(`:707-709`); the hold is not hit-tested against anything narrower. iPad Pro
13 portrait: (2752−1584)/3 = 389 px = 194.5 pt — `PadTopBand.h:25`'s own
"~194 pt". Landscape 80 pt. Phone 68 pt. So on the tablet a thumb resting in
the top 14% of the glass for 0.75 s toggles zen either way. This is the ruling
("hold above the paper") applied to a geometry where "above the paper" is a
fifth of the screen — the owner has twice reported margin gestures firing by
accident (`GestureBindings.h:72-76`). Fix if wanted: cap the tablet's hold
band at the phone's safe-area strip.

### 4 — P2 — One-finger SWIPE zones are judged at the recognition point; the README says landing point. VERIFIED, and DELIBERATE in code

`CrossPointZenRecognizers.mm:215-222` `zoneOf()` reads `locationInView` when
the recognizer fires (~50 pt of travel in). The comment directly above it
(`:204-214`) says so on purpose: "a VERTICAL swipe is judged where UIKit
recognized it, which is the honest answer … for a gesture that crosses zones
by definition." The SDL tap uses the finger-down y (`CrossPointIOSShim.cpp:3025`
→ `:3137`) and the hold reads at `.began` (drift ≤ 10 pt). `ios/README.md:537`
states "THE ZONE IS JUDGED FROM THE LANDING POINT" — false for the four
swipes. Practical consequence worth knowing: on a phone `g_cardTopPx` is 68 pt,
so `Above the Paper → Swipe Down` is nearly unreachable (the finger has
crossed the boundary before UIKit recognizes) and a Swipe Up started ~40 pt
below the card top answers as `SwipeUpAbove`. NOT filed as a bug — the code
chose it — but the README and the code must say the same thing, and the
Swipe Down row is offered for a zone it cannot practically be performed in.

### 5 — P2 — In zen a firmware text field can never raise the iOS keyboard. VERIFIED

`paintPad` returns at `CrossPointIOSShim.cpp:2790` before `paintKeyboardChip`
(`:2906`); `padWatch`'s `FINGER_DOWN` breaks at `:3038` (`if (g_zen) break;`)
before the tap candidate is armed, so `hitKeyboardChip` (`:2911`) is
unreachable. `hostkbd::State` opens every field suppressed
(`HostKeyboardState.h:84, 114`) — the chip is the only way up.
`ios/README.md:1415` promises the chip "whenever a field is open". Enter
Wi-Fi / rename / Device Owner while in zen (2-finger tap = Confirm, 2-finger
swipe up = Back, both live) → daisywheel only. Not stuck; the promised
affordance is absent. Fix: paint and hit-test the chip in zen under
`gpio.isTextEntryActive()`, or leave zen on the text-entry rising edge.

### 6 — P3 — `shipsInert(Gesture::Count)` is true, so the simultaneity delegate says YES to any recognizer it did not install. VERIFIED, low impact

`GestureBindings.h:543-544` `kNoRow` has `zone = Neither`, `def = Nothing`;
`:631-633` `shipsInert = !isZoneRow && def == Nothing` → true for `Count`.
`CrossPointZenRecognizers.mm:197-202` `rowOf()` returns `Count` for a foreign
recognizer; `:561-564` returns `shipsInert(rowOf(a)) || shipsInert(rowOf(b))`.
Low impact because SDL installs no gesture recognizers on its view and the
hidden text field is off-screen — no foreign recognizer exists today. One
line: `shipsInert` answers false for `Count`.

### 7 — README drift, four statements. VERIFIED

| `ios/README.md` | code |
|---|---|
| `:485` shake "zen only" | `GestureBindings.h:708` fires outside zen since 2026-08-29 |
| `:515` "**One** row fires outside zen" | two: `HoldAbove` and `Shake` (`:707-709`) |
| `:537` "judged from the landing point" | false for the four swipes (finding 4) |
| `:539-540` both boundaries "published by `layoutPad` … in BOTH modes" | `layoutPadTablet` (`CrossPointIOSShim.cpp:429-628`) never assigns `g_zenRowTopPx` (only `:947`, phone path); the tablet relies on `zenPaperBottomPx()`'s panel-bottom fallback (`:260-263`). `docs/zen-mode.md` was corrected, the README was not |

Also `PadTopBand.h:25` / `CrossPointIOSShim.cpp:522` say "~194 pt" while the
log at `:551` prints `unit=%.1fpx` — both true (389 px = 194 pt at 2x), reads
as a discrepancy.

## Disproved — do not re-raise

- **"A queued 60 ms tap stretches to a whole slow present and reads as a
  hold."** Mechanism is real (`gpio.queueButtonTap(btn, 60)` at
  `CrossPointZenRecognizers.mm:286`; the up fires only in a later `update()`,
  `HalGPIO.cpp:900-918`), but the reader's side-button hold gate is
  `SKIP_HOLD_MS = 700` (`crosspoint-reader/src/activities/reader/EpubReaderActivity.cpp:581`)
  and the worst present on record is ~305 ms (`docs/zen-mode.md`, letterpress
  cache miss). Not reachable at current numbers; becomes real the day any
  firmware hold threshold drops under the worst present. The edge PLACEMENT
  is correct: a recognizer action fires inside `SDL_PollEvent`'s run-loop
  pump within `update()`, so the tap lands at the top of the NEXT `update()`,
  before `loop()`, as `HalGPIO.h:341-348` requires.
- **Coordinate-space mismatch between `zoneOf` (points × `contentScaleFactor`)
  and the layout (`g_ptScale`).** They agree because the window is
  `SDL_WINDOW_HIGH_PIXEL_DENSITY` (`HalDisplay.cpp:1823`). Was a candidate P0.

## Checked and CLEAN

- `ios/GestureBindings.h`: `zoneFor` degenerate-bottom collapse (`:333-338`);
  `resolve`/`isOffered` fall back to the row default for 0, out-of-range and
  stray `Inherit` (`:636-657`); `oneFingerAction`'s layered rule incl. the
  explicit-Nothing-vs-Inherit split (`:736-750`); `firesOutsideZen(k, z)`
  keys the gate on the ZONE row while the action comes from global;
  `rowsAreInEnumOrder` static_assert.
- `ios/Settings.bundle/Root.plist`: decoded, 29 gesture rows, 12 values on
  global rows, 13 (`Inherit` first) on zone rows, every `DefaultValue`
  matches `kRows`; no 3-/4-finger keys.
- `ios/CrossPointPrefs.mm`: `CrossPointPrefs_gestureBinding` (`:804-813`)
  reads NSUserDefaults live per dispatch; `ensureDefaults` (`:193-268`)
  registers the Root.plist domain once, unreadable-plist branch does not
  restate gesture keys (0 → row default, never Nothing);
  `gestureBindingIsExplicit` uses `persistentDomainForName:`.
- `ios/ZenPrefSync.h` / `pollZenMode`: `decide()` total; `envForced` early
  return (`CrossPointIOSShim.cpp:1685`) keeps `CROSSPOINT_SIM_ZEN` from being
  reverted; no echo loop.
- `src/HostKeyboardState.h`: Start/Restart/Stop ordering, suppression
  re-armed on both field edges, `forceRestart_` consumed only by `poll()`;
  `pumpHostTextInput` (`HalGPIO.cpp:1224-1262`) checks for a window before
  polling.
- `src/TextEntryKeyRouting.h`: `enterOwner` truth table matches both recorded
  bugs; `enterClaimedByButton` cleared on both field edges (`HalGPIO.cpp:1159`).
- `ios/ZenHoldRouting.h`: `begin()` scrubs `poisoned_` and `fired_`;
  `claim()` asked only when an action exists; poisoning traced through
  `hold:`'s `.began`/`.changed`/`.cancelled`.
- Sheet touch gate: both `_present` entry points set the flag before
  `presentViewController` and re-assert in `viewDidAppear`; the push case
  holds the gate.
- Backgrounding / rotation (`CrossPointIOSShim.cpp:3266-3279`, `:3295-3336`):
  candidate spoiled, queued taps cleared, classifier reset, pad slots released;
  pad rects zeroed on size change so `padHitTest` answers `kNoSlot`. Phone is
  portrait-only.
- Sleep: a gesture bound to Power is recoverable — `startDeepSleep` pumps
  `SDL_PollEvent`, and `HalGPIO.cpp:1688-1701` turns a queued tap into a wake
  edge.
- `pendingButtonTaps` threading: recognizer actions, `padWatch`, read-aloud's
  `applyActions` and `update()`'s drain are all main-thread; the no-lock
  comment (`HalGPIO.cpp:126-128`) holds.
- `g_holdFired` two-finger latch: worst case one swallowed hold right after a
  zen toggle disables the recognizer; self-heals on the next gesture.

Deliberately not reported, already ruled in `docs/zen-mode.md`: pad-hold /
zen-hold overlap out of zen; the tablet's below-the-paper zone from the
panel-bottom fallback; the beam arming on a palette-only reconvert; read-aloud
turning pages with `BTN_RIGHT` under the firmware's nav-swap setting.
