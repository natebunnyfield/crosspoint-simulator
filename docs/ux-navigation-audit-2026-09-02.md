# UI/UX navigation audit — iOS harness (2026-09-02)

Owner asked for a finding pass ("take a pass at finding ui/ux bugs, especially
around navigation"), then ruled the same day on which get fixed: **"Chord timer
+ iOS P1s"** — the two P1s here, plus the firmware's chord-timer family. The
firmware half of the same pass is
`crosspoint-reader/docs/ux-navigation-audit-2026-09-02.md` (16 findings, six of
them one root cause: the SDK's `getHeldTime()` is one global chord timer, not a
per-button hold).

**Status, 2026-09-02** — both fixes are host-tested and build; neither has been
run on a phone, so each is SHIPPED — UNCONFIRMED on device:

| # | Status | Where |
|---|---|---|
| 1 | **FIXED** | the SDL tap branch (`ios/CrossPointIOSShim.cpp`) now hands the action to `CrossPointZenRecognizers_performAction`, a C entry that forwards to `performGestureAction` — one dispatcher, no second switch to teach. Pinned by `tests/tap_dispatch_source_test.py` (fails seven ways against the pre-fix tree). |
| 2 | **FIXED** | `ios/ShakeFirstResponder.h` — `shakeresp::shouldClaim(textEntryActive, hostKeyboardVisible)` gates the claim; `claimShakeFirstResponder()` in `CrossPointZenRecognizers.mm` reads the two HAL flags and logs which way it went; `CrossPointZenRecognizers_reassertShake()` runs on `SDL_EVENT_SCREEN_KEYBOARD_HIDDEN` (the chip, iPad's dismiss key, and the field closing all arrive there), so the shake takes the responder back the moment the keyboard is gone. Pinned by `tests/shake_first_responder_test.cpp` (four-state truth table). What to observe on device: open the Wi-Fi password field, toggle zen with a hold above the paper — the keyboard must stay up; dismiss it — a shake must then step the font. |
| 3 | open — owner call | unchanged |
| 4 | open — deliberate in code | unchanged |
| 5 | open | unchanged |
| 6 | open | unchanged |
| 7 | open — **proposal**, not a diff | the four README statements stand as written; correcting them was not in the chosen fix set, so they are not silently rewritten here. None of the four is about the tap path, so fixing 1 changes none of them. |

Surveyed at `beda69c` (main). One read-only hunting agent over `ios/**`,
`src/HalGPIO.cpp`, `src/HostKeyboardState.h`, `src/TextEntryKeyRouting.h`,
`src/SimulatorOverlay.h`; every VERIFIED finding was then re-read
independently at the cited lines before it was written here. Two of the
agent's findings were downgraded on that re-read (P1-3, P2-7 below) — the
disproof is recorded so the next pass does not re-raise them.

Line citations below were re-pointed at the post-fix tree on 2026-09-02
(`CrossPointZenRecognizers.mm` grew ~17 lines, `CrossPointIOSShim.cpp` ~8);
grep the symbol if one has moved again.

**Adversarial review of the fix, same day** (read-only refuting agent over
the diff). No P1 survived. Taken: the note this table carried claiming fix 1
made a README statement true (it did not — none of the four concerns the tap
path); the stale citations; and the tap path's lost "unhandled action" log
line — `performGestureAction`'s `kNoButton` fallthrough now logs, for both
callers, so the next appended `Action` that reaches neither a named case nor a
button announces itself instead of reproducing finding 1 silently. Recorded,
not changed: `tests/tap_dispatch_source_test.py` pins the historical shape (a
five-string blocklist inside a regex window) rather than the invariant, so a
re-added second dispatcher written with a new name would pass it; and
`shakeresp::shouldClaim`'s `textEntryActive` argument is dead against the real
accessors (`isHostKeyboardVisible()` already ANDs it), which the test says is
deliberate. Checked and found CLEAN by that review: the tap path's threading
(SDL runs event watchers synchronously at push time, on the main thread on
iOS; `performGestureAction` touches no UIKit); behavior parity of the old
switch against `performGestureAction` (same `queueButtonTap(btn, 60)`, same
`CrossPointZen_toggleFromRecognizer("deliberate tap")`, the palette-sheet gate
unreachable from this site, no zen re-gate); ToggleZen re-entrancy
(`setEnabled` is a `dispatch_async`); `reassertShake` ordering (FIFO on main,
both re-read the live flags); `SDL_EVENT_SCREEN_KEYBOARD_HIDDEN` coverage in
the vendored SDL (`stopTextInput` and `keyboardDidHide:` both send it); the
field-close ordering (`textEntryActive` flips before the Stop that emits the
event); every hide path either sets suppression or closes the field, so no
permanently-dead-shake state exists; `run_all.sh` wiring; the header's purity.

## Findings, ranked

### 1 — P1 — Two of the offered one-finger Tap actions can never fire. VERIFIED — FIXED 2026-09-02

The one-finger tap is NOT a UIKit recognizer (`CrossPointZenRecognizers.mm:709`
skips `fingers < 2`); it is the SDL deliberate-tap classifier, dispatched at
`ios/CrossPointIOSShim.cpp:3157-3178`. That dispatcher knows `ToggleZen`,
`FontFamilyStep` and anything `gesturebind::buttonFor()` maps to a button
(`GestureBindings.h:200-211`); everything else logs
`[zen] tap -> %s is not handled on the SDL tap path` and returns. `Root.plist`
offers 12 (`FontFamilyStepBack`, appended 2026-08-29) and 13
(`OpenActionMenu`, 2026-09-01) on `gestureTap`, `gestureTapAbove`,
`gestureTapBelow` (decoded: `[1..10, 12, 13]` / `[11, 1..10, 12, 13]`). Bind
the tap to either → silent no-op on the gesture a reader uses most. The
comment that stood at that branch predicted exactly this ("if a twelfth Action is ever
appended, that is the other place to teach") and both appends missed it.
Fix: the SDL tap branch calls `performGestureAction`
(`CrossPointZenRecognizers.mm:230`) instead of keeping a second, smaller
dispatcher. Six of 29 rows affected.

### 2 — P1 — Every zen toggle drops the software keyboard, and zen has no way back. VERIFIED (mechanism; UIKit first-responder semantics assumed, not run) — FIXED 2026-09-02

`CrossPointZenRecognizers.mm:645` (now inside `claimShakeFirstResponder`, `:638`): `[g_shake becomeFirstResponder]` on EVERY
`CrossPointZenRecognizers_setEnabled` call (unconditional since 2026-08-29,
comment `:870-881` says why). Callers: `CrossPointIOSShim.cpp:3380` (gesture
toggle), `:1702` (Settings.app apply), `:1672` (first poll), `:3547`
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
max(safeTop, 16pt)*scale)`; `CrossPointIOSShim.cpp:563` publishes it as
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

`CrossPointZenRecognizers.mm:216-223` `zoneOf()` reads `locationInView` when
the recognizer fires (~50 pt of travel in). The comment directly above it
(`:205-215`) says so on purpose: "a VERTICAL swipe is judged where UIKit
recognized it, which is the honest answer … for a gesture that crosses zones
by definition." The SDL tap uses the finger-down y (`CrossPointIOSShim.cpp:3039`
→ `:3145`) and the hold reads at `.began` (drift ≤ 10 pt). `ios/README.md:537`
states "THE ZONE IS JUDGED FROM THE LANDING POINT" — false for the four
swipes. Practical consequence worth knowing: on a phone `g_cardTopPx` is 68 pt,
so `Above the Paper → Swipe Down` is nearly unreachable (the finger has
crossed the boundary before UIKit recognizes) and a Swipe Up started ~40 pt
below the card top answers as `SwipeUpAbove`. NOT filed as a bug — the code
chose it — but the README and the code must say the same thing, and the
Swipe Down row is offered for a zone it cannot practically be performed in.

### 5 — P2 — In zen a firmware text field can never raise the iOS keyboard. VERIFIED

`paintPad` returns at `CrossPointIOSShim.cpp:2798` before `paintKeyboardChip`
(`:2914`); `padWatch`'s `FINGER_DOWN` breaks at `:3046` (`if (g_zen) break;`)
before the tap candidate is armed, so `hitKeyboardChip` (`:2919`) is
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
`CrossPointZenRecognizers.mm:198-203` `rowOf()` returns `Count` for a foreign
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
| `:539-540` both boundaries "published by `layoutPad` … in BOTH modes" | `layoutPadTablet` (`CrossPointIOSShim.cpp:437-636`) never assigns `g_zenRowTopPx` (only `:955`, phone path); the tablet relies on `zenPaperBottomPx()`'s panel-bottom fallback (`:268-271`). `docs/zen-mode.md` was corrected, the README was not |

Also `PadTopBand.h:25` / `CrossPointIOSShim.cpp:525` say "~194 pt" while the
log at `:551` prints `unit=%.1fpx` — both true (389 px = 194 pt at 2x), reads
as a discrepancy.

## Disproved — do not re-raise

- **"A queued 60 ms tap stretches to a whole slow present and reads as a
  hold."** Mechanism is real (`gpio.queueButtonTap(btn, 60)` at
  `CrossPointZenRecognizers.mm:287`; the up fires only in a later `update()`,
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
  return (`CrossPointIOSShim.cpp:1690`) keeps `CROSSPOINT_SIM_ZEN` from being
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
- Backgrounding / rotation (`CrossPointIOSShim.cpp:3260-3279`, `:3296-3338`):
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
