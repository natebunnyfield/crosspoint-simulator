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
