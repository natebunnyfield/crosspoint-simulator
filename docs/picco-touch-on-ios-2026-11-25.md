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
