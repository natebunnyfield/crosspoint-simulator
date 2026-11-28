# Picco-style touch on the iOS app: mapping and options (2026-11-25)

Owner, 2026-11-25: *"let's make the ios app for crosspoint touchscreen like picco"*.
Surveyed at simulator `main` (after a fast-forward pull) and firmware `origin/main`
(read through `git show origin/main:`; the primary firmware checkout is 1 ahead /
172 behind and dirty, so it was not touched. Its one local commit, 2730016ae, is
already upstream as cd080ee08 (`git range-diff`: only the test/CMakeLists.txt
context differs)). Not built or run. Every finding below was read from source.

## What the Picco does with touch (firmware, all under `FREEINK_DEVICE_PICCO`)

Rulings live in `crosspoint-reader/docs/picco-port-2026-11-05.md`.

- **Outside keyboards:** gestures become synthesized buttons with the iOS
  defaults (tap = Right, swipe left = Right, swipe right = Left, swipe up = Back,
  swipe down = Confirm, hold 750 ms = Confirm). `MappedInputManager::synthesizeGesture`
  + `src/components/PiccoInput.h`. The Picco copied these from this iOS app
  (ruling 2026-11-06: *"adopt the norms from cross-point simulator. and the
  default iOS app settings"*), so outside keyboards **the phone already
  behaves like the Picco**.
- **Left-edge swipe = Back on every screen** (start x <= 25%, rightward, more
  across than down; `edgeswipe::isLeftEdgeBack`). The phone does not have
  this; there, a rightward swipe anywhere is Left.
- **Inside keyboards, a tap types the key under the finger.** The full-screen
  grid/QWERTY (`KeyboardEntryActivity`), the daisy wheel, the note editor and
  the Claude chat strip call `setKeyboardTouch(true)` while their keys are up.
  A tap in the text field moves the cursor; a touch hold on Del deletes one
  character; a finger on a key stands the buttons down
  (`KeyboardEntryActivity.cpp` Picco blocks around `loop()` and `touchKeyProps`).
- The firmware's own tap rows, reader tap zones and Home/menu swipes stay
  gated off.

## What the iOS app does today

- It runs the X3 profile. `BoardConfig::hasTouch()` is false
  (`src/BoardConfig.h:173`), so `HalGPIO::beginTouch` returns at once
  (`src/HalGPIO.cpp:483`) and no coordinate reaches the firmware.
  `ios/README.md` "The model" states that as a design rule.
- The simulator HAL already has a complete touch model (tap, hold, swipe,
  suppress; `src/HalGPIO.cpp:1817-1895`), fed today only by desktop mouse
  events for the Sticky and X4 Pro profiles (`src/HalGPIO.cpp:1228-1254`).
- The HAL has no `setKeyboardTouch`, `readTouchContact` or `isKeyboardTouchOn`,
  which the firmware's Picco path calls, so the Picco blocks cannot simply be
  turned on for the iOS build.
- Inside a keyboard the zen tap is Right (it moves the selection one key).

## Options put to the owner

- **A. Keyboards take touch, like the Picco (recommended).** A firmware
  capability macro replaces `FREEINK_DEVICE_PICCO` at the keyboard-touch sites
  and is on for the Picco and the iOS simulator build. X3/X4 device images
  stay +0. The simulator gains `setKeyboardTouch` and a gate that answers touch
  queries only while it is on. While it is on, the harness sends panel touches
  to `beginTouch`/`moveTouch`/`endTouch` and not to the zen tap. Every other
  screen stays as it is today.
- **B. Build the app as a Picco.** A new `SIMULATOR_DEVICE_PICCO` profile:
  800x480 panel (the X3 is 528x792), rocker mapping, and the firmware's own
  gesture decoder fed raw touches. This is the most faithful copy, but every
  page changes size and the zen gestures the Picco lacks (two-finger, pinch,
  shake, tilt) would need re-plumbing or would be dropped.
- **C. Touch everywhere** (`hasTouch()` true). This turns on the upstream tap
  rows, tap zones and edge swipes that the Picco deliberately gates off, so it
  is not "like the Picco".

A second question follows whichever option is chosen: should the phone adopt
the left-edge swipe = Back (it would take that swipe away from page-back)?

## Rulings

- **2026-11-25, scope:** none of A/B/C as put. Owner, verbatim: *"make the
  picco or x3 -n ios option in settings of app settings , so touch is for
  picco only and x4 and x3 are gesture based"*. So the app gets a device choice
  in Settings.app. Picco takes touch; X3 (and X4) stay gesture-based as today.

## What a device switch costs (read 2026-11-25)

- **X3 and X4 are a RUNTIME choice in the firmware.** At `origin/main` only two
  compile-time gates name them (`lib/hal/HalGPIO.cpp`,
  `src/network/FirmwareBoardTag.cpp`), and the device image detects the board
  at boot. The simulator's `BoardConfig::ACTIVE` is a runtime profile with
  `selectDevice()` (`src/BoardConfig.h:150`). The iOS core is still pinned to
  X3 at compile time (`ios/CMakeLists.txt:669`, plus the three build-identity
  guards in CLAUDE.md), and the pad is drawn for the X3's buttons.
- **The Picco is a COMPILE-TIME board.** Its touch, rocker, light and
  slide-switch code sits behind `#if FREEINK_DEVICE_PICCO` (about 140 lines
  over about 30 files), so an X3 binary does not contain it. One app binary
  cannot switch into a real Picco at runtime unless those gates become runtime
  checks, and that edit touches the device firmware. On iOS a second firmware
  core means a second app: iOS cannot exec, and two firmware cores cannot be
  linked into one binary.

- **2026-11-25, how:** owner chose **"Full Picco as a second app"**: no
  firmware gate rewrite and no Settings switch. Each app is its own configure,
  bundle and card. The X3 app is unchanged.

## What was built (worktree pair `picco-app`, 2026-11-25)

Firmware branch `picco-app` from `origin/main` 008f7da80; simulator branch
`picco-app` from `origin/main` 54987d81.

### Firmware (one file)

- `platformio.ini`: `[env:simulator_picco]` = `env:simulator` +
  `-DSIMULATOR_DEVICE_PICCO -DFREEINK_DEVICE_PICCO=1`. The desktop canary for
  the Picco app.

### Simulator

- `src/BoardConfig.h`: a Picco profile (`Board::Picco`, SSD1677, 800x480,
  touch, frontlight, RTC; rocker on the up/down slots), `isPicco()`, and
  `hasTouch()` true for it. **Gate:** a `SIMULATOR_DEVICE_PICCO` build without
  `-DFREEINK_DEVICE_PICCO=1` on the command line is an `#error`. Found by the
  first link: `notes/KeyboardPanel.cpp` tests the macro before anything
  includes `BoardConfig.h`, so with the macro defined only in the header its
  Picco definitions compiled out while the callers' declarations stayed in
  (undefined `KeyboardPanel::routeTouch`, `resetTouch`, `selectTouched`).
- `src/HalGPIO.{h,cpp}`: the firmware HAL's Picco block mirrored
  (`lib/hal/HalGPIO.cpp:276-401`). Every touch query reads "no touch" unless a
  keyboard has called `setKeyboardTouch(true)`. `wasSwipe` is always false.
  `readTouchContact` is ungated and reports "now" for a finger that is down:
  SDL sends no event for a still finger, and without that the decoder's
  200 ms freshness rule (`HOLD_REPORT_GAP_MS`) refuses every hold. Also
  `injectButtonTap` (one-frame synthesized press, released on the next
  `update()`), `isTouchContactDown`, `lastTouchReportMs`, the slide switch
  (present, host-settable through `setToggleSwitchForHost`, default off),
  `isUsbPowerPresent` (= `isUsbConnected`), and `isUsbConnectedCached`.
  New simulator-only `injectTouchDown/Move/Up` (logical 0..1 page
  coordinates) is the harness's way in.
- `CROSSPOINT_SIM_INPUT_SCRIPT` `SWIPE` now emits a move every 16 ms between
  its ends. Before this a scripted swipe was a down and an up with nothing
  between them, and a decoder that reads only the live contact (the Picco's)
  saw a tap. The start/end-based swipe classifier of the other touch boards
  reads the same result as before.
- `src/HalStorage.h` `prepareForDeepSleep()` and `src/HalPowerManager.h`
  `holdWhileUsbPowered()` (returns false: the host has no charger to watch,
  and its deep-sleep loop is the sleep) plus `startDeepSleep(gpio, bool)`.
  `src/esp_heap_caps.h` maps `heap_caps_*` to malloc.
- iOS (`ios/CMakeLists.txt` `-DCROSSPOINT_IOS_DEVICE=PICCO`): bundle id
  `com.natebunnyfield.crosspoint.picco`, display name "CrossPoint Picco"
  (`Info.plist.in` now takes the name). Configure refuses PICCO with the X3
  bundle id. Settings page generated by `tools/gen_picco_settings_plist.py`:
  the X3 page minus Zen, the four gesture groups, the three zone groups and
  Zen Reading Goal. 19 groups, 24 rows.
- Harness (`ios/CrossPointIOSShim.cpp`, all under `FREEINK_DEVICE_PICCO`): a
  finger that lands on the page goes to `injectTouch*`. Single touch; a cancel
  ends the contact with nothing fired. No zen (forced off, not read from the
  pref). No UIKit recognizers (`CrossPointZenRecognizers_setEnabled` returns),
  because an installed recognizer would cancel SDL's touches when it
  recognized. The pad keeps only the rocker (UP/DOWN slots) and Power; Back,
  Left, Right and Confirm retire with a zero rect. The volume buttons are the
  rocker (`CrossPointVolumeButtons.mm`: up = `BTN_UP`, the upper end; down =
  `BTN_DOWN`), always armed.

### Measured on the desktop `simulator_picco` (headless, 2026-11-25)

- Boots to Home on a 480x800 portrait page.
- Taps at the page center moved the Home selection one row each (tap = next).
- A swipe up from Home opened the recent book: Back on Home is
  "open recent book" (`HomeActivity.cpp:331`), so swipe up = Back.
- Five taps then a 1000 ms hold on Home opened **NoteEditor** (hold = Confirm).
- In the note editor, taps at the `h` and `i` keys typed **"hi"**, with the
  last key drawn pressed.

### Measured on the iOS Simulator (iPhone 17, iOS 26.5, Debug, 2026-11-25)

- Boot log: `[BUILD] iOS harness and firmware core agree: Picco, 800x480
  logical, 2x render scale`; `[picco] zen off; page touches go to the
  firmware's touch model`; `[VOLUME] armed`.
- Fingers driven with the new `CROSSPOINT_SIM_PAGE_FINGER` hatch, which pushes
  real SDL finger events through `padWatch` (a script `TAP` enters below the
  harness). First launch resumed the seed book (English Fairy Tales), so the
  taps landed in the reader. Five taps at the page center turned pages, and a
  1100 ms hold opened `EpubReaderChapterSelection` (hold = Confirm). Captures
  in the session scratchpad, not kept.
- Not reached on iOS: touch typing (the run never left the reader). Typing is
  proved only on the desktop build above. The volume rocker, the pad capsules
  and real fingers are device feel: UNCONFIRMED.
- Regression: the desktop `simulator_x3` builds clean with every shared change.
  Host tests `build_identity`, `pointer_touch_hints`, `zen_keyboard_chip`,
  `gesture_plist` and `tap_candidate` pass.

### Open

- TestFlight for the Picco app needs its own App Store Connect app record for
  `com.natebunnyfield.crosspoint.picco`, and `ios/testflight.sh` is X3-only
  (bundle id, the `SIMULATOR_DEVICE_X3` gate). Not done.
- The turned-page landscape layout was not exercised in the Picco app; the
  page-point mapping assumes the portrait present.
- E-Ink Mode stays on the Picco Settings page but models the X3's UC8253
  waveforms, not the Picco's SSD1677.

## Adversarial review, 2026-11-25 (read-only agent, on 125e705e + c1891509a)

No X3 regression found. Findings, most severe first, and what was done:

1. **`tests/freeink_macro_include_test.py` was red.** Seven sites tested
   `FREEINK_DEVICE_PICCO` without including `BoardConfig.h`. These were not
   wrong builds, since the macro comes from the command line. FIXED: each file
   includes `BoardConfig.h`, and the gate passes.
2. **An in-process reboot left the keyboard touch gate open.**
   `piccoKeyboardTouch` is a static that survives the iOS longjmp. A reboot
   from inside a keyboard (a book shared in from Files) runs no `onExit`, so
   every page tap of the next boot would count as inside a keyboard and turn
   nothing. FIXED: cleared in the reboot reset registrar. Verified by reading
   only; the desktop reboot is `execvp`, so no headless run can show it.
3. **A tap inside one 50 ms idle slice was lost.** Down and up landed in one
   event pump, and the decoder never sampled a live contact. REPRODUCED on the
   old build: three 5 ms taps after idle moved the Home selection 1 row in one
   run and 0 in another. FIXED: the Picco HAL holds a lift down until
   `readTouchContact` has reported the contact since its last change (its start
   or its suppression), then lands it on the next `update()`. A 250 ms safety
   valve covers a loop that never samples. After the fix, the same script moved
   3 rows in each of 2 runs. 80 ms taps, a 1000 ms hold, 5 ms key taps and a
   left-edge Back swipe inside a keyboard all behave as before.
4. **A cancelled touch still fired a gesture.** Suppress-then-up in one callback
   meant the decoder next saw "no contact" and classified a release. FIXED by
   the same hold: the decoder now sees the contact down and not live, and ends
   it with nothing fired. The shim's cancel, no-geometry and resign-active
   paths share `piccoAbandonFinger()`. The last of those resolves the
   reviewer's open question: a page finger no longer outlives a background.
5. **The slide switch was present but could never move.** Bound to Dark Mode,
   it forced `darkMode` off at every boot and hid the Dark Mode row. FIXED:
   `hasToggleSwitch()` is false on the host until a host control exists. The
   frontlight rows stay hidden because `HalFrontlight::present()` is X4
   Pro-only, which the default binding hides on the device too.
6. Scripted `SWIPE` moves change Sticky's long-press and held-point reads along
   a swipe path, and `wasSwipe` is unchanged. No test or doc uses `SWIPE`.
   Kept; the path is what a finger does. Also: `simulator_x4_pro` never
   selects the X4 Pro profile in `HalGPIO::begin()`, so desktop X4 Pro has no
   touch. Pre-existing, not touched.

Minor, not changed: the turned-page landscape mapping (Open, above). The Picco
app's volume buttons are always the rocker and cannot be unbound. Reconfiguring
a Picco build dir as X3 keeps the Picco bundle id; testflight.sh's device gate
still fails closed. A five-number `CROSSPOINT_SIM_PAGE_FINGER` entry is
ignored silently.

**Checked and found clean** (reviewer's list):
- `BoardConfig.h` guards. `HalGPIO.h` including `BoardConfig.h`: no `#ifdef`
  flip, no layout change.
- `piccoTouchGated()` folds to false off the Picco. `wasTouchActivity`
  reduces to its original expression for X3 and X4.
- The Picco HAL against firmware `lib/hal/HalGPIO.cpp`: every gate, `wasSwipe`,
  synthesized press lifecycle, `getHeldTime`, `readTouchContact`,
  `lastTouchReportMs`.
- Shim finger ownership. The page mapping matches read-aloud's panel geometry
  on phone and tablet. Retired pad slots are zeroed after every layout path.
- Forced zen off: no recognizer or shake catcher is reached unguarded.
- Volume up maps to `BTN_UP`, the rocker's upper end, which is next.
- The settings generator drops only zen, gesture and reading-goal keys.
- The X3 CMake, Info.plist and bundle id are unchanged.
- The `PAGE_FINGER` hatch is inert when unset.
- Stub signatures match the firmware call sites.
- 12 of 13 Python catalog tests passed at review time; all 13 pass after fix 1.

## TestFlight build 1 on the owner's iPhone Air (2026-11-25)

Build 1 (`picco-build-1`, simulator e38c9440, firmware c1891509a) drew three
reports. Fixes are in simulator 441badf4.

1. **"picco buttons seem backwards."** Mechanism found and fixed. The pad's
   rocker is a side-by-side pair with the `UP` slot on the LEFT
   (`layoutPadImpl`, `place(kPadUp, rightX, ...)`). On the X3 that is right:
   `BTN_UP` is page back. The Picco firmware maps `BTN_UP` to Right, i.e. NEXT
   (`MappedInputManager::mapButton`, `piccoinput::rockerRoute`), so the left
   half went forward and the right half back. The Picco block in `layoutPad`
   now swaps what the two halves press. Measured on an iPhone Air simulator,
   Release, real UIKit taps: right half -> `Page turn fwd`, left half twice ->
   `Page turn back` twice. The volume buttons were NOT changed: volume up is
   the rocker's upper end, which is next, the same as the X3 app's default
   (`VolumePageTurn.h`, `Verdict::Next` -> `VolumeUp`).
2. **"albo does not load as a font on initial load."** Mechanism found and
   fixed. The firmware's default reader family is `""`, the built-in face
   (`CrossPointSettings::sdFontFamilyName`), so a fresh install opened its
   first book in that, although the registry had found Albo
   (`[SDREG] Found family: Albo`). `seedFirstRunReaderFamily()` in
   `ios/CrossPointFsPrep.cpp` writes `{"sdFontFamilyName":"Albo"}` to a card
   with no `settings.json`, before `setup()`, and only when Albo was seeded
   onto the card. Applies to fresh installs of BOTH apps; an existing
   settings file is never touched. Measured on a fresh iPhone Air simulator
   install: `Loaded SD card font family: Albo`, 14 pt with the 2x companion,
   and the firmware rewrote the full file itself.
3. **"touchscreen does not work."** NOT reproduced; no mechanism found.
   - Real UIKit touches (an XCUITest that taps the installed app by
     coordinate; the Simulator GUI app is not installed on this Mac, so
     `cliclick` had no window to click) reach `padWatch` as `direct-touch`
     and do what the firmware decoder says, on an iPhone 17 and an iPhone
     Air simulator, Debug and Release: 3/3 taps turned pages, 2/2 left
     swipes turned pages, a 1.2 s hold opened chapter selection.
   - The earlier verification pushed SDL events from inside the app
     (`CROSSPOINT_SIM_PAGE_FINGER`), which skips UIKit. This round closes that
     gap; the device itself still differs.
   - Checked and found clean: no UIKit recognizer is installed on the Picco
     (`CrossPointZenRecognizers_setEnabled` returns first); every overlay view
     (`CPAccessibilityOverlay`, the page text input, the volume view, the
     appearance probe) is `userInteractionEnabled = NO`; the shim's Picco
     branch uses the same coordinates as the pad, which works on the device.
   - Instrumented instead of guessed: every page-finger decision is now
     logged (`[picco] page finger ... down/up`, `DROPPED: finger ... is still
     down`, `at ... px: off the page / <pad slot>` with the page rect,
     `abandoned`) and every button the decoder fires (`[picco] gesture ->
     button N`). With Settings > CrossPoint Picco > Diagnostics Log on, they
     land in `diagnostics/firmware.log`. Diagnostics stay off by default
     (owner ruling 2026-08-09).
   - One untested hypothesis: the Picco branch is single touch, so a contact
     that never lifts (a resting thumb, a lift iOS never reports) would drop
     every later page tap while the pad keeps working. The X3 app's one-finger
     recognizers would fail the same way, which argues against it. The new log
     line `DROPPED` would show it.

Method, for a re-run: build `-DCROSSPOINT_IOS_DEVICE=PICCO` for
`iphonesimulator`, install fresh with `xcrun simctl`, then a scratch XcodeGen
project with a host app and a `bundle.ui-testing` target whose test does
`XCUIApplication(bundleIdentifier: "com.natebunnyfield.crosspoint.picco")`,
sets `CROSSPOINT_SIM_DIAGNOSTICS=1` in `launchEnvironment`, and taps
`app.coordinate(withNormalizedOffset:)`; read
`Documents/diagnostics/firmware.log` from `simctl get_app_container`.

**Adversarial review of 441badf4** (read-only agent, 2026-11-25): no
findings. Checked and found clean: every reader of `g_pad[...].button`
(`applyActions` is the only consumer) and the swap's position after
`layoutPadImpl`, so the phone, iPad and turned-landscape layouts all get it;
the X3 app untouched (`#if FREEINK_DEVICE_PICCO`); `loadFromFile` key-by-key
defaults for a partial file; the appearance seed reads `settings.json` in a
static initializer, before `CrossPointHarness_prepareFilesystem`, so the new
file cannot change it; the iOS reboot's `setjmp` sits after
`prepareFilesystem`, so the seed runs once per process; the nine new
`SDL_Log` format specifiers. One reviewer statement was wrong and is
corrected here: the X3 bundle DOES carry Albo, so fresh X3 installs also
start in Albo (intended, see 2 above). The X3 desktop canary
(`simulator_x3`) builds clean with the change.

## TestFlight build 2 (2026-11-25): "not working and no diagnostics were made when enabled"

Second device failure, so build 3 is instrumentation-first, and the instrument
cannot depend on the log the owner found missing. Three lines of counters are
drawn in the black band above the page (SDL debug font, `paintPiccoTouchDbg`,
run from a scope guard at the end of `paintPad` because the painter's
surround fill covered a first-drawn version):

    ios <SDL finger downs> ptr <pointer downs> gated <stopped before the Picco branch>
    page <accepted>/<lifted> 2nd <dropped> off <off page> pad <pad> ab <abandoned>
    fw <HAL contacts> read <first reads> gest <decoder buttons> diag <switch>/<armed>

Measured on an iPhone Air simulator, Release, real UIKit taps: one page tap
and one rocker tap read `ios 2 ... page 1/1 ... pad 1`, `fw 1 read 1 gest 1`.
The Diagnostics switch, written as Settings.app writes it
(`simctl spawn defaults write <bundle id> diagnosticsEnabled -bool YES`),
armed the log and created `diagnostics/firmware.log` on the simulator, so the
missing log on the device is itself unexplained; `diag a/b` on the device
answers which half failed.

## TestFlight build 3 (2026-11-25): the counters answered it

The owner's screenshot read `ios 49 ... page 28/28 ... fw 28 read 28 gest 27`:
every touch reached the firmware and the decoder fired. Touch "not working"
was the Picco's tap = Right on menus (the 2026-11-06 ruling kept the
firmware's row taps gated), reported as *"touching a menu item does not select
it"*. Ruled the same day: *"picco and ios tap should be select row"* --
firmware side in `crosspoint-reader/docs/picco-port-2026-11-05.md`.

Making that work found a simulator bug that had been there all along:
`logicalToPanelNormalized` (`src/HalGPIO.cpp`) put a touch in 1x logical
pixels and divided by the 2x FRAMEBUFFER (`HalDisplay::activeWidth/Height`),
so on the iOS app every touch reached the firmware at half its position (a
tap on Home's Settings row read 66,303 for 133,609). Tap = Right ignores
position, which hid it; the left-edge Back zone was effectively the left
half. Now divided by the 1x panel (`EInkDisplay::DISPLAY_WIDTH/HEIGHT`), as
are the tap-slop and swipe distances. At 1x (every desktop build) nothing
changes. `diag 0/0` on the device was the switch reading off, not a failure
of the log.

**Adversarial review of 519af2e9d (firmware) + dde9ce3d (simulator)**, three
findings, none held on checking:
- "Stale page areas leak on the split Home": the covers page records NO
  area (its taps go through `wasTapInRect`, which records nothing), and the
  menu page computes `showMenuPage` after the rocker handlers, so the areas
  are always the page on screen. Left as LATENT: a rocker press and a tap in
  the same ~10 ms frame would judge the tap against the menu and then turn
  to the covers.
- "Row areas are not orientation-aware": the decoder's point comes from
  `GfxRenderer::tapToLogical`, which applies the orientation; the areas are
  logical too. Not a bug.
- "Hardcoded 800x480 in `logicalToPanelNormalized`":
  `EInkDisplay::DISPLAY_WIDTH/HEIGHT` is per simulated board
  (`src/EInkDisplay.h`: 792 on X3, 800 otherwise), and `activeWidth()` is that
  times the render scale. Not a bug.
Reviewer's clean list: the Picco gate on `wasScreenTapped`, the area dedupe,
`claimScreenTaps` once per loop, `tapToLogical` unaffected.

## 2026-11-26: every Picco control on the pad

Owner: *"add all hardware switches and buttons on picco to ios app."*

The Picco's controls, from the firmware SDK's board profile
(`freeink-sdk/libs/hardware/BoardConfig/include/BoardConfig.h`, `PICCO`):

| Control | Pin | Firmware role | On the iOS pad before | Now |
|---|---|---|---|---|
| Power | GPIO2 | Power (sleep/wake) | yes, bottom left | unchanged |
| Rocker upper | GPIO21 (`BTN_UP`) | Right / next | yes, right half of the bottom-right capsule | unchanged |
| Rocker lower | GPIO9 (`BTN_DOWN`) | Left / previous | yes, left half | unchanged |
| Third key | GPIO5 (`BTN_CONFIRM`) | Confirm (`mapButton` shared path, `SETTINGS.frontButtonConfirm`) | no, its slot was zeroed | the Confirm capsule, its old slot |
| Slide switch | GPIO6 | a level, bound to Frontlight or Dark Mode (`main.cpp handleSlideSwitch`) | no; the HAL answered `hasToggleSwitch() == false` | a two-position switch in the slot Back left |

GPIO5's physical place on the device is recorded nowhere (the profile says its
role is unconfirmed), so the capsule stays where the pad already put Confirm.

**How the switch is modeled.** `HalGPIO::hasToggleSwitch()` (simulator) now
answers whether a host has given the switch a control: the first
`setToggleSwitchForHost()` makes it present. Only the iOS Picco build calls it,
from `CrossPointHarness_seedSlideSwitch()` in `simulator_main.cpp`, after
`prepareFilesystem` and before `setup()`, so the boot's `handleSlideSwitch()`
reads the stored position as the device reads its physical one. The desktop
never calls it, so on the desktop the switch is still absent, which keeps the
2026-11-25 review's finding 5 closed there. The position persists in
NSUserDefaults (`piccoSlideSwitchOn`, no Settings.app row). A touch landing on
the switch flips it (`[picco] slide switch -> on|off` in the log); the finger
then goes on as an off-page finger so the classifiers see its down and its lift.

**A pad bug this found.** `paintPad`'s pair loop marked both halves of a pair
as drawn BEFORE its zero-rect guard, so a pair with one retired half (Back gone,
Confirm kept) was skipped by both the pair loop and the single loop: Confirm
hit-tested but was never drawn. Marked after the guard now. X3 is unaffected:
its pairs are whole, and a fully retired pair is still skipped by both loops.

**What the switch does on a phone.** Its default binding is Frontlight, and the
simulator's `HalFrontlight::present()` is false on the Picco profile (true on
X4 Pro only), so with the default binding a flip changes nothing on screen,
exactly as `handleSlideSwitch()` does on a Picco with no light. Bound to Dark
Mode (Settings > Slide Switch) it drives dark mode, and the Dark Mode row hides
as switch-owned, as on the device.

**Verified on the iPhone Air simulator, Release, real UIKit taps** (scratch
XCUITest `Tapper`), from a card with `slideSwitchAction=1`, `darkMode=0`:
the switch tap logged `[picco] slide switch -> on` and the firmware's
`[SWITCH] Slide switch on`, the page went dark and the knob moved right; a
relaunch came back with the knob right and the page dark; a tap on the Confirm
capsule on Home logged `CONFIRM down/up` and entered `EpubReader`. Desktop
canaries `simulator_picco` and `simulator_x3` build. Device feel UNCONFIRMED.

**Review of the controls (2026-11-26), and what was done.** A read-only
adversarial pass found:
1. iPad and the turned landscape put the switch in the left margin, level with
   the page, where the left-margin clamp also made its finger a page finger:
   one tap flipped the switch and turned the page. Fixed: a finger that flipped
   the switch is never a page finger.
2. Bound to Dark Mode, the system-appearance seed in `applyTheme` overwrote
   `SETTINGS.darkMode` (at launch after `setup()`'s `handleSlideSwitch`, and on
   any appearance change), so the knob said on over a light page. Fixed: the
   seed is skipped while the switch owns Dark Mode.
3. A window resize zeroed the pad's slots but not the switch (latent; the same
   gap the keyboard chip has). Fixed for the switch.
4. With the default binding (Frontlight) a flip changes nothing on screen
   (no frontlight on the Picco host). Kept: that is the device's own behavior
   without a light.
Checked and found clean by the same pass: the link on both devices
(`CrossPointHarness_seedSlideSwitch` defined unconditionally, C linkage,
called only under `CROSSPOINT_SIM_IOS`); the in-process reboot (seed runs
before the setjmp, state survives the longjmp); zen (the Picco forces it off,
and zen zeroes the switch); the mixer/ink-picker gate; drags and second
fingers; layout staleness on every `layoutPadImpl` path; the pair-loop change
leaves X3 pixels unchanged.

## 2026-11-27: zen, the X3's gestures, and Up/Down in the Picco app

Owner, verbatim: *"add ios app settings for volume and all other possible
gestures from crosspoint x3; put zen mode in"* and *"add the option for up and
down buttons to be in there (for font size and selection)"*. Simulator
`key-paste` worktree (base afb15923), firmware `key-paste` worktree (base
66b5f0ebc, firmware commit 4b019d933).

### What changed

**Zen.** No longer forced off. `pollZenMode` reads the pref exactly as the X3
does; the Picco page ships the switch OFF (`gen_picco_settings_plist.py`), so the
app still opens on the pad. In zen the pad, the rocker, Confirm and the slide
switch are hidden as on the X3 (`padSlot` is -1 in zen, the switch already
required `!g_zen`), the page is placed in the sheet, and the S-039 rule (a
finger on the sleeping glass is POWER in zen) applies unchanged because it sits
above the Picco branch in `padWatch`.

**The page touch stays the firmware's, in and out of zen.** Three rules in
`ios/CrossPointIOSShim.cpp` (Picco finger branch) and one in the recognizers:
- A one-finger touch that lands on the page (or level with it in the left
  margin, the edge-Back clamp) goes to `injectTouch*` and breaks before the SDL
  tap classifier, so the deliberate-tap path never sees it.
- `g_piccoTouchIsFirmwares` latches whether the FIRST finger of the current
  touch went to the firmware; it is held until the next touch's first finger,
  so a recognizer that fires on the lift reads the right answer whichever of
  UIKit and SDL saw the lift first. The one-finger swipe and hold handlers
  (`CrossPointZenRecognizers.mm` `oneFinger:at:`, `hold:`) step aside for it
  through `CrossPointZen_piccoTouchIsFirmwares()` and log `began on the page ->
  the firmware's`.
- In zen, a second finger while the page finger is down ends the firmware's
  contact with nothing fired (`piccoAbandonFinger`, the existing cancel path)
  and is fed to nothing; a finger landing on the page while an off-page finger
  is down is not a page finger. Out of zen the two-finger recognizers are off
  and the single-touch rule stands (second finger dropped).
- A zen toggle abandons a page finger too (the page moves under it).

**Recognizer coexistence, checked rather than assumed.** The Picco app now
installs the same 12 recognizers as the X3. The old reason for installing none
("an installed recognizer would cancel SDL's touches when it recognized") does
not hold: `tameRecognizer()` sets `cancelsTouchesInView`, `delaysTouchesBegan`
and `delaysTouchesEnded` to NO on every object, so SDL's view gets every touch
undelayed and uncancelled. The simultaneity delegate only arbitrates recognizer
against recognizer (`shipsInert`); it has no say over the view's touches. What
keeps the page touch the firmware's is ownership (above), not UIKit.

**The gesture rows.** One table (`ios/GestureBindings.h`) with a `Device`
parameter; `ios/GestureDevice.h` answers `kThisDevice` from `BoardConfig.h` so
the table stays pure. Three differences, all pinned in
`tests/gesture_bindings_test.cpp` `testPicco`:
- **Keys.** `buttonFor(a, Device::Picco)`: Right -> `BTN_UP` (rocker upper,
  next), Left -> `BTN_DOWN` (rocker lower, previous), Up -> slot 2, Down ->
  slot 3 (the X3 side pair, below), Back/Confirm/Power unchanged. Physical slots
  2 and 3 did nothing on the Picco before this, so any Right/Left binding on the
  Picco would have been dead.
- **Offered.** Everything except the six one-finger GLOBAL rows. On the Picco
  that layer is fixed at its defaults, which are exactly what the firmware's own
  decoder fires for a page touch (tap and swipe left Right, swipe right Left,
  swipe up Back, swipe down Confirm, hold Confirm). A zone row left on Inherit
  therefore does what a touch on the page would, and its label reads "Same as
  on the page".
- **Out of zen.** The X3's two (hold above the paper, shake) plus the two
  volume rows, which were the Picco's rocker in every mode and must stay so.

**Volume.** `CrossPointVolumeButtons.mm` no longer hard-wires the rocker; it
fires `gestureVolumeUp` / `gestureVolumeDown` like the X3. Their defaults
(Right / Left) press the rocker's upper / lower end on the Picco, in and out of
zen, so nothing changes until the owner rebinds them; both Nothing releases the
audio session as on the X3.

**Up and Down as the X3's side pair.** Firmware: in the Picco APP build only
(`FREEINK_DEVICE_PICCO` + `SIMULATOR`), `MappedInputManager::mapButton` sends
Up, Down, ScreenUp/Down and the four page buttons to the X3's side pair instead
of nowhere (`piccoinput::rockerRoute(button, hostSidePair)` -> `HostSidePair`,
then the pure `hostSideKey()` restating the X3 table with `sideButtonLayout`).
The device passes `kHostSidePair = false` and the case body is compiled only
under `SIMULATOR`, so `pio run -e picco` still routes them to None. Simulator:
`HalGPIO::BTN_HOST_SIDE_UP` / `_DOWN` are slots 2 and 3 (the front Left/Right
slots, which the Picco has no keys for and its firmware never reads), so the
hold timer, the activity-swap swallow and every `0..BTN_POWER` loop cover them
with no firmware change; a ninth and tenth slot would not fit the firmware's
`uint8_t` button masks. Consequences, all intended:
- Host page turns that pressed `BTN_RIGHT`/`BTN_LEFT` (read-aloud, speed read,
  the accessibility scroll, the page text input) now press
  `BTN_HOST_NEXT`/`_PREV`: the front pair on the X3 (unchanged), the rocker on
  the Picco. On the Picco those four were DEAD before this (slot 3 was read by
  nothing); now they turn pages.
- Desktop arrow keys Left/Right and the script's `LEFT`/`RIGHT` press the side
  pair on a Picco build (`QTAP:LEFT` = X3 side Up).
- Reachability on the Picco: `longPressButtonBehavior` is the constexpr
  `FONT_SIZE_STEP`, `sideButtonLayout` the constexpr `PREV_NEXT`, and no Picco
  guard skips the reader's side-button block (`EpubReaderActivity.cpp` ~660-700),
  so a side tap steps size and a 700 ms hold steps family as on the X3.

**New QA hatch.** `CROSSPOINT_SIM_FIRE_GESTURE="<ms>:<key>;..."` fires a gesture
row by its Settings key through `CrossPointZenRecognizers_fireGesture`, the call
the volume adapter and tilts make (live binding, zen gate, sleep rule, this
build's keys). It skips only the sensing (KVO, CoreMotion, UIKit recognition).

### The Picco gesture page (26 groups, 58 rows; X3 27 / 64)

| Row | Default | Picco key / effect |
|---|---|---|
| Zen Mode | Off | (X3 ships On) |
| 2-finger Tap | Confirm | `BTN_CONFIRM` (zen) |
| 2-finger Swipe Left / Right | Down / Up | side pair: bigger / smaller text (zen) |
| 2-finger Swipe Up / Down | Back / Confirm | (zen) |
| 2-finger Hold | Next Reading Font | host font-family channel (zen) |
| Pinch / Spread | Up / Down | side pair: smaller / bigger text (zen) |
| Shake | Toggle Zen | either mode |
| Volume Up / Down | Right / Left | rocker upper / lower, either mode |
| Tilt Left / Right / Forward / Back | Nothing | (zen) |
| Above the Paper: Tap, Swipe L/R/Up | Same as on the page | (zen) |
| Above the Paper: Hold | Power | either mode |
| Below the Paper: all six | Same as on the page | (zen) |
| The Left Margin: all six | Same as on the page | (zen); see below |

No X3 default does nothing on the Picco, so none ships as Nothing in its place.
**The Left Margin rows are nearly unreachable on the Picco**: beside the page
the margin is clamped onto the page's edge for the firmware's left-edge Back
swipe (2026-11-25), so a touch there is the firmware's. The rows answer only
where the margin runs above or below the page's own height. Kept, as asked, and
said so in the group's footer.

### Measured (2026-11-27)

- Host tests: `gesture_bindings` (incl. `testPicco`), `gesture_plist`,
  `picco_settings_plist` (new), `freeink_macro_include`, `volume_page_turn`,
  `tilt_gestures`, `speed_read`, `speedrun`, `test_speed_read_live`,
  `zen_verbs`, `zen_hold`, `zen_pref_sync`, `zen_keyboard_chip`,
  `sleep_touch`, `dial_table`, `frozen_page`: all PASS. Firmware
  `PiccoInputTest` 40/40 (three new tests written first, failed to compile,
  then passed). The X3 `Root.plist` is byte-identical (`git diff` empty).
- Builds: `pio run -e picco`, `simulator_picco`, `simulator_x3` from the
  firmware worktree; the iOS Picco app (Debug, iphonesimulator).
- Desktop `simulator_picco`, reader: `QTAP:LEFT` twice, `QTAP:RIGHT` once,
  then `QTAP:LEFT:1200`: three repaginations, `fontSizeSlot` saved 2 (3 -> 2 ->
  1 -> 2), and the hold loaded the next family (`Loaded SD font family:
  Almendra`, ~730 ms after the press).
- iOS Simulator, iPhone Air, iOS 26.5, scratch device, out of zen
  (`CROSSPOINT_SIM_PAGE_FINGER`, `CROSSPOINT_SIM_FIRE_GESTURE`):
  `recognizers attached: 12 objects`; page taps `page finger 98 down/up` ->
  `gesture -> button 4` -> pages 0/8 -> 1/8; `volume up -> right (button 4)`
  twice (pages 1 -> 2 -> 3), `volume down -> left (button 5)` (3 -> 2);
  `pinch -> nothing` (zen-only).
- Same, in zen through the pref (`-zenModeEnabled YES` launch argument):
  `[zen] seed: pref=1 env=unset -> on`, `verb recognizers enabled`; page tap
  still the firmware's (2 -> 3); `pinch -> up (button 2)` twice and
  `spread -> down (button 3)`, each a repagination, `fontSizeSlot` 3 -> 2 -> 1
  -> 2 (saved 2); screenshots show the pad gone and the title set smaller;
  `volume up -> right` in zen (page 3); a tap below the paper `-> right`
  (page 4).
- Real UIKit touches (scratch XCUITest, `xcodebuild test`): out of zen, two
  page taps turned pages through the firmware with all 12 recognizers
  installed; a 1.2 s page hold logged `hold began on the page -> the
  firmware's` and the firmware's own `gesture -> button 1` opened chapter
  selection (one action, not two). In zen: `2-finger tap -> confirm`, `pinch ->
  up` (fingers off the page: two fingers to the classifier, no tap fired); a
  spread that started on the page logged `joins page finger ... the firmware's
  contact ends` and only `spread -> down` fired; a later one-finger page tap
  was the firmware's (`gesture -> button 4`).
- Observed, not explained: in the XCUITest's second launch nothing was
  appended to `diagnostics/firmware.log` although `a11y.log` was written; the
  unified log (`simctl spawn log show`) carried every line. Not investigated.

### Unconfirmed

Device feel, all of it: real fingers on an iPhone, the volume rocker (KVO is not
driven by the hatch), shake, tilts, the 2-finger hold, and whether a thumb
resting off the page during a page swipe is common enough to matter (in zen
it now makes that swipe a two-finger gesture). Zen Reading Goal was kept and
not exercised on the Picco. The turned-page landscape and iPad layouts were not
run.

### Checked and found clean

- X3: every Device argument defaults to X3; `buttonFor(a, X3) == buttonFor(a)`
  for all actions (test); `BTN_HOST_NEXT/PREV` are `BTN_RIGHT/LEFT`;
  `CrossPointZen_piccoTouchIsFirmwares()` is false; the Picco shim blocks are
  under `FREEINK_DEVICE_PICCO`; the X3 Root.plist is unchanged.
- Device firmware: `kHostSidePair` false, the HostSidePair body compiled only
  under `SIMULATOR`; `rockerRoute(b, false)` is the old table (test).
- `tameRecognizer` covers every installed object (`install()` is the only
  attach path); the shake catcher and tilt/volume adapters dispatch through
  `performGestureAction`, which now uses the Picco keys.
- Slots 2 and 3 on the Picco: no firmware reader (`grep BTN_LEFT|BTN_RIGHT`:
  only the shared mapping for logical Left/Right, which the Picco never reaches,
  `mapFrontLabels`, and `getPressedFrontButton`, which has no caller); every
  simulator page-turn writer of `BTN_RIGHT`/`BTN_LEFT` moved to
  `BTN_HOST_NEXT/PREV`. Still on slots 2/3, deliberately: the desktop
  scancode map and the text-entry arrow keys (`src/HalGPIO.cpp` ~727), so a
  hardware keyboard's Left/Right arrows are the side pair on a Picco build, and
  the script names `LEFT`/`RIGHT` (the iOS Picco build's `TAP_PAD` names for
  slots 2/3 are `SIDE_UP`/`SIDE_DOWN` since 3f58875b).

### 2026-11-28: the X3's Up/Down buttons on the Picco pad (setting, off by default)

Owner, asking "where is up down button group in picco app?", then verbatim:
*"just match x3 app and make it an ios app setting (default off)"*.

**What it is.** Settings > **Buttons** > **Up/Down Buttons** (Picco page only,
straight after Zen, ships OFF; injected by `tools/gen_picco_settings_plist.py`,
the X3 `Root.plist` unchanged). On, the Picco pad shows the X3 pad's Up|Down
pair in the X3 pad's own place for it -- the row the rocker vacated when it
moved up into the arrows' slot -- in every layout the X3 has one. It presses
the X3 side pair (`HalGPIO::BTN_HOST_SIDE_UP` / `_DOWN`, slots 2/3), so a tap
steps the font size and a hold the family in a book, and it is Up/Down
elsewhere, exactly like the Up/Down gesture actions. Up is the LEFT half, as on
the X3 pad (not the rocker's swapped halves). Hidden in zen with the rest of
the pad.

**Design.** `ios/CrossPointIOSShim.cpp` `layoutPad`, Picco block: the X3
place is read from `layoutPadImpl`'s `kPadUp`/`kPadDown` rects BEFORE the
rocker moves into the arrows' slot, and the pair goes on the two arrow slots
the block retires (`kPadLeft`/`kPadRight`). Reusing them rather than growing
`g_pad` keeps `kPadCount`, PadCore's slot count, `paintPad`'s pairs table
(they already pair and paint as one capsule) and every loop over the pad as
they are, and their buttons are already slots 2/3; in the Picco build their
table entries are named `SIDE_UP`/`SIDE_DOWN`. Off, they stay zero rects:
today's pad. The decision is pure in `ios/PiccoPad.h` (`sidePair`): off places
nothing; a collision with POWER, the slide switch, the keyboard chip, Select or
the rocker refuses the pair and names the control instead of moving anything
(`[picco] up/down pair NOT placed: ...`); Up is the left rect.
`tests/picco_pad_test.cpp` (failing first: it did not compile before the
header existed). The setting is read live (`pollPiccoUpDown`, every frame,
like `pollZenMode`); an edge releases any held pad slot, relays the pad out and
presents.

**Measured** (iOS Simulator, iPhone Air and iPad Air 11-inch, iOS 26.5, Debug;
captures in the session scratchpad `updown/`, not kept in the repo):
- Phone portrait, off vs on: the two glass captures differ in exactly 1186 px,
  all inside the new capsule (x 728-1115, y 2411-2602); nothing else on the
  glass moved. The pair sits at 728,2411 + 922,2411, 194x192 px each, the
  bottom-right row, matching the X3 app's pair in the same place (compared
  against an X3 build of 2026-10-11 already on a shared simulator).
- iPad, off vs on (warm install): differ in exactly 604 px, all inside the pair
  (1334,1556, 2 x 120x64), below the rocker in the right margin, the X3 tablet
  pad's place.
- Real UIKit taps (scratch XCUITest) in a book: Up, Up, Down -> three
  repaginations, `fontSizeSlot` 3 -> 2 -> 1 -> 2 (saved 2); log `[picco]
  finger ... at 825,2507 px: SIDE_UP`, `[harness] SIDE_UP down/up`.
- Hold: a 1.2 s SDL finger on SIDE_UP stepped the family (Albo -> Almendra,
  ~730 ms after the press).
- Live: app running with it off, sent to the background, the pref flipped,
  brought back: same process (pid 5732 before and after), `[picco] up/down
  buttons on (setting)`, the pad relaid out and the pair placed.
- `CROSSPOINT_SIM_TAP_PAD` and `CROSSPOINT_SIM_PAGE_FINGER` reach the pad but a
  pad TAP they make does not reach the firmware: both push their events from the
  per-frame hook, after `loop()`, so the press and release edges are wiped by
  the next `beginFrame()` (the hatch's own comment says so); only a held level
  survives. Real touches (XCUITest) are the proof of a tap.
- Found, harmless: on each relayout one pass runs with a 960x1600 output (not
  the 1260x2736 window); there the X3 place (470,1306..816,1474) overlaps the
  slide switch (341,1378 149x96) by 20 px and the pair is refused for that pass,
  logged. Every window-sized pass places it; no capture shows the refused pass.

**Unverified:** the turned landscape (needs a book on a wide-table page; the
same code path places the pair from `layoutTurnedLandscape`'s rects), device
feel, and how the X3 pad of TODAY compares pixel for pixel (the X3 capture is
an older build; the Picco pair's rects come from today's `layoutPadImpl`, the
X3's own code).

### 2026-11-28: "for picco, is the optical layout 1u of space above text and 2u below text?"

Measured on the Picco app, iPhone Air (1260x2736 px, 3x; one unit = 24 pt =
72 px, one circle = 32 pt = 96 px), light, English Fairy Tales spine 1 page
17, a body page; Albo, size slot 3. Page (panel) 960x1600 px. Paper edges read
down the page's centre line, text ink = rows with a pixel 70 levels darker than
the paper (`measure.py`, scratchpad). Captures: scratchpad
`updown/spacing/picco-zen-off-body.png`, `picco-zen-on-body.png`.

| | zen OFF (S1/W2) | zen ON (C32) |
|---|---|---|
| paper top / bottom | 307 / 2123 | 294 / 2148 |
| page top / bottom | 379 / 1979 | 382 / 1982 |
| paper top -> page top | 72 px = **1.00 u** | 88 px = 0.92 circle |
| page bottom -> paper bottom | 144 px = **2.00 u** | 166 px = 1.73 circle |
| paper top -> first text ink | 95 px = 1.32 u | 111 px = 1.16 circles |
| last text ink -> paper bottom | 179 px = 2.49 u | 201 px = 2.09 circles |
| glass above paper / below paper | 307 / 613 px = 1 : 2.00 | 294 / 588 px = 1 : 2.00 |

The pad's first row starts at y 2171 (zen off), 48 px below the paper.

- **Zen off** follows S1 exactly: the paper is one unit above the PAGE and two
  below it, and the glass bands are 1:2. S1 is defined on the page, not the
  text, so the text has 1.32 u above and 2.49 u below.
- **Zen on** follows C32 exactly as the code defines it: `[zen] circle 96px
  ink=8.0/26.0 paper 294-2148` puts the paper one circle above and two below
  the PUBLISHED text block (382 + 8 - 96 = 294; 1982 - 26 + 192 = 2148), the
  2026-10-11 ruling (measured to the published insets, not to ink). Against
  the actual ink it is 1.16 circles above and 2.09 below, because the first
  line's ink starts 15 px below the published top inset (ink at 405, block top
  at 390); at the bottom the ink ends 9 px inside the block. Whether the X3
  shows the same 15 px was not measured here.
- `[zen] ink insets (published): top=8.0px bottom=26.0px`, from
  `[zen] published ink insets 8/26 fb-px`: source published.
- **The mapping is right on the Picco.** `fbPortraitH = HalDisplay::activeWidth()`
  assumes a landscape framebuffer whose WIDTH is the portrait height. The
  Picco panel is 800x480 landscape-native (SSD1677), so at 2x
  `activeWidth() = 1600` is the portrait page's height in framebuffer px, and
  the presented page is 1600 px tall: factor 1.000, fb 8/26 -> device 8.0/26.0.
  The transient 3.8/12.2 lines are passes with a 760 px presented height
  (760/1600 = 0.475), consistent with the same mapping. Nothing to fix.

**Review of the Up/Down pair (2026-11-28, read-only, 3f58875b).** Found and fixed:
a cold launch with the setting on could lay the pad out before the first poll
seeded the setting, leaving the pair absent until a resize (`pollPiccoUpDown`
now relays out on a seed that is on; the same race `pollZenMode` guards).
Found and NOT fixed: on a 320 pt wide window (Display Zoom on an iPhone SE or
mini) the X3's Up/Down place overlaps the slide switch on the 5-column grid,
so `piccopad::sidePair` refuses the pair on every pass and the setting does
nothing there (a log line only). Not the owner's phone (an iPhone Air is 420
pt); fixing it means moving another control, which this change was told not
to do. The 960x1600 pass seen at every relayout is a 320 pt layout (960 / 3),
which is why it refuses; its refused/placed log lines alternate each relayout
(cosmetic). Checked and found clean: the X3 app (every edit inside
`#if FREEINK_DEVICE_PICCO`, X3 `Root.plist` untouched); off is today's pad;
zen hit-testing and painting; turned landscape and iPad placement; toggling
with a held press; the chip collision at every common width but 320; the
per-frame pref read; the reboot longjmp; the plist generator and its gate;
font-size direction (Up smaller, Down bigger). Neither app gives pad slots
VoiceOver labels, so none were lost.
