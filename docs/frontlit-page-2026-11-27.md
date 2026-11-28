# The Picco's Brightness and Warmth on the page (ST-012), 2026-11-27

Owner 2026-11-26, verbatim: *"future todo: for warmth setting on picco to
adjust paper warmth and crt warmth; brightness adjusts ink and crt specific
physics"*. Built 2026-11-27 on *"connect brightness and warmth as described in
the earlier todo"*. Status: **shipped in TestFlight build 14 at the owner's
go ("Menu fix + light rows", 2026-11-27); the look is still his to judge**.
Every number below is a tuning that the renders are meant to settle. Device
feel UNCONFIRMED.

## What moves

The firmware's two rows are `frontlightBrightness` and `frontlightWarmth`
(0..100, 0 the coolest; defaults 60 and 50, firmware
`src/CrossPointSettings.h:249-250`). The phone has no frontlight, so on a Picco
build they drive the simulated page instead.

| | Light page (Sanguine on India) | Dark page (the four-gun tube) |
|---|---|---|
| **Warmth** | The PAPER, as a warm or cool light tints it: India's tone times an illuminant, renormalized to India's luminance. Ink untouched | The GUNS: P38 amber (R) and P22R red (W) times *f*, P45 white (G) and P20 yellow-green (B) divided by *f*, with *f* = 3^((w-50)/50). The afterglow tail follows through the mixer |
| **Brightness** | The INK's Beer-Lambert depth, continuing the picker's density law past full strength | The BEAM: the trace's emission (linear light), the scanline bloom, the afterglow's length (times beam^0.5) |

Brightness is a three-point ramp, linear between the points: **0** is the
thinnest ink (or dimmest beam) that still clears 7:1 on that sheet (or glass),
**60** is the frozen page, and **100** is depth 1.6 (or beam 1.4).
The first version ramped from depth 0, which put Brightness 0 to about 35 on
one floor-clamped value. The anchored ramp is what makes every step move.

**The origin is the frozen page, byte for byte.** With the light off, or on at
60/50, every function returns `src/FrozenPage.h`'s own values, not a
recomputation. So an untouched Picco, and every other board, do not move.
`simfrontlight::current()` reports off on every board but the Picco.

**The light switch matters, and what it does depends on its binding.** The
page follows the HAL's light, whichever control turned it on or off
(`src/HalFrontlight.cpp`, `publish`). Which control that is comes from the
firmware's Slide Switch row (`slideSwitchAction`, default Frontlight, firmware
`src/CrossPointSettings.h:258-261`):

- **Bound to Frontlight, the default.** On iOS the light follows the pad's
  slide switch (stored, `CrossPointPrefs_piccoSlideSwitchOn`), as on the device
  (firmware `src/main.cpp:717-723`, the default case of `handleSlideSwitch`).
  **With the switch off, the page is the frozen page whatever the rows say.**
  That was a choice, not forced: the alternative is to ignore the switch.
- **Bound to Dark Mode.** The switch flips Dark Mode and does not touch the
  light (`src/main.cpp:710-716`). The light then follows the Settings rows that
  this binding reveals: Frontlight (`SettingsActivity.cpp:424`,
  `Frontlight.setOn`) and, at wake, Restore Light on Wake
  (`src/main.cpp:1074-1076`). So with the switch OFF the page is the LIGHT
  page, and it is LIT whenever the Frontlight row is On and Brightness or
  Warmth is away from 60/50. The switch does not freeze the page here.

The desktop simulator has no slide switch (`hasToggleSwitch()` is false), so
there the light follows the two rows whatever the binding says.

(Corrected 2026-11-27, review row R-25: this paragraph first gave the default
binding's rule as the only one. The page code was right; the doc was not.)

## Where it lives

- `src/FrontlitPage.h` -- the pure model. `src/FrontlitLight.h` -- the light's
  state and the simulator-only `simfrontlight` API.
- `src/HalFrontlight.cpp` -- `present()` is true on the Picco as well as the X4
  Pro (the hardware has a light). Publishes the Picco's state with a generation
  counter and an optional change hook.
- iOS: `ios/PanelPrefs.h` (both pairs), `ios/CrossPointIOSShim.cpp`
  `pollPanelGlow` (trail and tail, edge-triggered on the light's generation,
  overriding the mixer only when the light is not neutral) and `pollScanlines`
  (bloom). `sleepTick` makes the same reads while the firmware sleeps (the
  sleep section below).
- Desktop: `src/HalDisplay.cpp` `applyFrontlitPage`, installed as the change
  hook by the `CROSSPOINT_SIM_AS_SHIPPED` block on a `SIMULATOR_DEVICE_PICCO`
  build only.

## Measured

`tests/frontlit_page_test.cpp`, in `tests/run_all.sh` as `frontlit_page`.
The worst contrast over the grid (step 2 on both axes) is **7.00:1 light and
7.00:1 dark**. Warmth moves the sheet's luminance by at most **2.3%**. The
test was shown to fail against three broken models: a reversed gun ratio
(100 failures), no luminance renormalization (1), and no neutral early exit (2).

The model's tones (`w` warmth, `b` brightness):

| w | b | light ink on paper | dark trace on glass | beam | trail ms | bloom |
|---|---|---|---|---|---|---|
| 0 | 0 | 72483F on EFF4FE | 86B2AD on 162122 | 0.53 | 794 | 210 |
| 0 | 60 | 5C332B on EFF4FE | B4EDE7 on 162122 | 1.00 | 1095 | 400 |
| 0 | 100 | 2F0E0A on EFF4FE | D1FFFF on 162122 | 1.40 | 1296 | 400 |
| 50 | 0 | 72483F on F9F3E9 | A2A6A0 on 171B1B | 0.58 | 834 | 232 |
| **50** | **60** | **5C332B on F9F3E9** | **CFD4CC on 171B1B** | **1.00** | **1095** | **400** |
| 50 | 100 | 2F0E0A on F9F3E9 | F0F6ED on 171B1B | 1.40 | 1296 | 400 |
| 100 | 0 | 70463D on FFF1C2 | D48A7C on 190D0A | 0.74 | 939 | 294 |
| 100 | 60 | 5C332B on FFF1C2 | F39F8F on 190D0A | 1.00 | 1095 | 400 |
| 100 | 100 | 2F0E0A on FFF1C2 | FFB9A7 on 190D0A | 1.40 | 1296 | 400 |

Bloom ships at its maximum (400, `scanlines::kBloomMax`), so Brightness can
only lower it.

Rendered on the desktop `simulator_picco` with `CROSSPOINT_SIM_AS_SHIPPED=1`
from a scratch card (Alice, one page, the same `.crosspoint` restored before
every arm, `CROSSPOINT_SIM_GRAIN_SEED=7`, a `{}` `settings.json` beside the
binary): the dark renders' ground and trace match the table exactly. **Light
off at 100/100 is byte-identical to 60/50 in both polarities** (BMP md5).

One visible consequence worth knowing: at Brightness 0 the ink (light) or the
trace (dark) sits on the 7:1 floor, and every texture field spends only the
contrast above the floor, so both pages go flat there. Light: the sheet's
tooth, formation and letterpress have nothing to spend (`src/FieldSelection.h`);
the modal ground is the bare paper tone F9F3E9 at Brightness 0 against EFE9DF
at 60. Dark: the scanlines' depth is capped by the same headroom
(`params.budgetMeanDarkening` at `src/SurfaceTube.cpp:340-343`,
`scanlines::effectiveDepth` at `src/Scanlines.h:298-303`; the first citation
read `:310-313` until the partial refill of b59b6455 moved the block down). **At
Warmth 50** they fall to about 6% of their shipped depth at Brightness 0, about
80% at 5, and are full from 10 (adversarial review, 2026-11-27, probe).

**That is the mid-Warmth figure only.** Warmth moves the trace and the glass,
so the headroom that caps the depth moves with it, and warm settings stay
thinned further up the Brightness row. Re-run 2026-11-27 over the device's own
steps of 5 (percent of the frozen page's depth, shipped intensity 50; the probe
is in Method below):

| Warmth | b=0 | b=5 | b=10 | b=15 | b=20 | full from |
|---|---|---|---|---|---|---|
| 0 | 10% | 100% | 100% | 100% | 100% | 5 |
| 25 | 1% | 92% | 100% | 100% | 100% | 10 |
| 50 | 6% | 80% | 100% | 100% | 100% | 10 |
| 75 | 14% | 62% | 100% | 100% | 100% | 10 |
| 80 | 5% | 50% | 87% | 100% | 100% | 15 |
| 90 | 2% | 46% | 79% | 100% | 100% | 15 |
| 100 | 0% | 35% | 67% | 95% | 100% | 20 |

Over all 21 Warmth steps: full from Brightness 5 at Warmth 0, 5 and 20; from 10
at the other steps up to 75; from 15 at 80 to 95; from 20 at 100. Once full it
stays full to Brightness 100 at every Warmth. The Brightness 0 column does not
rise or fall steadily with Warmth; why was not traced.

## Method

```bash
# host test
tests/run_all.sh -k frontlit_page
# renders: from the firmware worktree's scratch card, per arm
CROSSPOINT_SIM_AS_SHIPPED=1 CROSSPOINT_SIM_DARK=<0|1> CROSSPOINT_SIM_GRAIN_SEED=7 \
CROSSPOINT_SIM_INPUT_SCRIPT='5500:QUIT' CROSSPOINT_SIM_SCREENSHOTS='5000:<out>.bmp' \
SDL_VIDEODRIVER=dummy <firmware>/.pio/build/simulator_picco/program
# with fs_/.crosspoint/settings.json = {frontlightBrightness, frontlightWarmth,
# frontlightOn, frontlightRestoreOnWake: 1, darkMode}
```

The scanline depth table (pure model, no render), from the repo root:

```cpp
// depth.cpp -- c++ -std=c++17 -Isrc -o depth depth.cpp && ./depth
#include <cstdio>
#include "FrontlitPage.h"
#include "FieldSelection.h"
#include "PhosphorGrain.h"
#include "Srgb.h"
int main() {
  using namespace frontlitpage;
  // The chain SurfaceTube.cpp runs for params.budgetMeanDarkening, then
  // Scanlines.h effectiveDepth, at the shipped intensity.
  auto depth = [](const panelpalette::Palette &p) {
    scanlines::Params sp;
    sp.intensityPercent = 50;
    sp.budgetMeanDarkening =
        fieldselect::kRasterBudgetShare *
        phosphorgrain::darkeningBudget(srgb::relativeLuminance(p.ink),
                                       srgb::relativeLuminance(p.paper));
    return scanlines::effectiveDepth(sp);
  };
  const double base = depth(frozenpage::darkPair());  // 0.2000
  for (int w = 0; w <= 100; w += 5)
    for (int b = 0; b <= 100; b += 5)
      std::printf("w=%d b=%d %.0f%%\n", w, b,
                  100 * depth(darkPair(Light{b, w, true})) / base);
}
```

## Not done

- iOS: the Picco app builds for the simulator. On an iPhone Air simulator,
  with the card at 100/100, light on, and `piccoSlideSwitchOn` true, the app
  logged `[glow] preset 0 -> 1296 ms trail`, which is the model's Brightness
  100 trail, so the light reaches the iOS polls. The glass itself was NOT
  captured: `simctl io screenshot` kept returning a stale home screen while the
  app ran. The page colors on iOS are UNCONFIRMED.
  (Later the same day: the app's own `CROSSPOINT_SIM_SCREENSHOTS`, pointed into
  its data container, does capture the glass on the iOS Simulator. At 100/100
  the light page's most common tones are ink 2D0E0A on paper FDF1C2 (brightest
  FFF3C4) and the dark page's are trace FFB9A7 on a card of 190D0A, against the
  model's 2F0E0A on FFF1C2 and FFB9A7 on 190D0A; the page carries its texture
  fields, so its tones sit a few code values around the pair. See the sleep
  section below for the method. An iPhone is still UNCONFIRMED.)
- The ink on the light page does not take the warmth (owner: warmth adjusts
  PAPER warmth). A real warm light would tint both.
- Scanline intensity, grain and corner defocus are not driven by the beam.
  Only emission, bloom and afterglow are. The scanlines still thin out at the
  very bottom of Brightness, through the contrast cap above.
- DESKTOP ONLY, latent: with `CROSSPOINT_SIM_AS_SHIPPED=1` and a
  `settings.json` that names `darkMode` or `panelPalettePreset`, the settings
  watcher (`src/SimulatorSettingsWatch.cpp:169-189`) and the light hook each
  repaint the page over the other: the next light change puts the frozen or
  lit page back, the next save of the file flips it again. Run as-shipped
  renders with a `{}` settings file, as above. The app has no watcher.
- Tube warmth checked at single steps has 68 one-code-value reversals (the
  test checks every 5, which is the device row's step).

## Adversarial review, 2026-11-27

Read-only, over d9c66408 and f096e97b; nothing blocking. Found: the dark
page's scanline loss at Brightness 0 (now documented above), the desktop
watcher fight (latent, above), four wrong comments (fixed). Checked and clean:
`present()` true on the Picco (the slide switch saves once per change, the
iOS switch is seeded before `Frontlight.begin()`, the rows it reveals match
the device rule); threading (the firmware loop and the polls share the main
thread; a torn read self-corrects); the per-thread cache (0 mismatches over
300 alternating settings); neutral identity (60/50 computed the long way gives
the frozen bytes); the 7:1 floor at every one of 10,201 settings (worst
7.0001 light, 7.0004 dark); the tail at every setting; bloom 208..400 fed
the shipped 400 on both platforms; the field caches rebuild on a palette
change; the pad and keyboard chip follow through `applyPanel`. Not measured:
the feel of holding the rocker on Brightness, where each step rebuilds the
light sheet (about 130 ms, per `CLAUDE.md`).

## Sleep: the light goes off and the iOS page follows (review row R-15), 2026-11-27

**The defect.** On the Picco the firmware draws the sleep screen and then
switches the light off (firmware `src/main.cpp:790` `goToSleep`, `:812`
`Frontlight.setOn(false)`), inside the `loop()` that ends in the sleep loop. On
iOS the page learns of a light change only from three per-frame polls
(`pollPanelPalette`, `pollPanelGlow`, `pollScanlines`), and
`CrossPointHarness_perFrame` does not run while the firmware sleeps. So the
sleep screen kept the lit tones until the wake, against the rule above that
with the light off the page is the frozen page.

**The fix**, in `ios/CrossPointIOSShim.cpp`: the host's sleep tick
(`sleepTick`, run from the foot of `HalGPIO::startDeepSleep`'s loop) now makes
the same three reads. The pair goes through `syncPanelPalette`, which is
`pollPanelPalette` without its firmware render request: the tones are applied
when the cached frame is converted, so the sleep screen needs no render, and
the request is a flag only the firmware's `loop()` reads
(firmware `src/activities/ActivityManager.cpp:99`). The reads are skipped while the power-off collapse
holds the glass (`collapseOwnsGlass()`), which is dark until the wake.
`tests/frontlit_page_sleep_test.py` is a source gate on that wiring.

**The desktop as-shipped path did not have it.** Its change hook
(`applyFrontlitPage`, `src/HalDisplay.cpp`) runs inside `setOn(false)`, before
`HalDisplay::deepSleep()` flushes the sleep frame. Run, not only read: the log
gives `frontlit page: light off` at 6097 ms, then `[power] sleep entry ...
trailMs=1095` (the frozen trail), then the flush; the sleep frame's paper is
FBF5EA at its brightest, against FFF2C3 awake.

**Measured on the iOS Simulator** (iPhone Air, iOS 26.5, a new simulator
device, a fresh install per arm, card at Brightness 100 / Warmth 100, light on,
POWER at 16 s, in-app capture at 14 s and 22 s). Brightest paper pixel and the
most common ink; the page carries its texture fields, so tones sit a few code
values around the pair:

| | awake | asleep, before | asleep, after |
|---|---|---|---|
| Light page: paper | FFF3C4 | FFF3C3 | FBF5EA |
| Light page: ink | 2D0E0A | 2B0D09 | 532E27 |
| Dark page: card around the page (most common tone) | 190D0A | 190D0A | 161A1A |

The model's lit pair at 100/100 is 2F0E0A on FFF1C2 and its frozen pair 5C332B
on F9F3E9. After the fix the first sleep tick logs
`[harness] panel palette (light) -> frozen, ink 5C332B, paper F9F3E9` and
`[glow] preset 0 -> 1095 ms trail`, one millisecond after
`[power] deep sleep loop entered`. A wake 5 s later restores the light
(`[SIM] Picco frontlight: on`, `[glow] ... 1296 ms trail`) and the page is back
on FDF1C2. Before the fix neither line appears between sleep and wake.

**On a dark page the sleep screen itself was never lit, and still is not
India.** A drawn sleep screen is always normal polarity
(`SleepActivity.cpp:535`), so it is painted from the LIGHT pair, and on iOS
only the pair for the appearance in force is ever written
(`applyPanel`, `setPanelPalette(g_dark, ...)`). In a dark-mode session the light
slot still holds the simulator's default (2D2D2D on FBFBF9): the dark arm's
sleep screen measured ink 292929, paper FDFDFA at its brightest, with the same
pixel counts before and after. What the fix moves there is the card around the
page, from the lit glass 190D0A to the frozen 171B1B. Two things follow and neither is
changed here, because both are the look:

- The dark-mode sleep screen on iOS is the default gray pair, not Sanguine on
  India. The desktop as-shipped path writes both pairs and so sleeps on India.
- By reading, not run: a session that was in light mode with the light on and
  then switched to dark keeps that lit pair in the light slot, so its sleep
  screen would be drawn on the lit paper whatever the light does later.
  Writing the other appearance's pair whenever the lamp moves would close it,
  and would also change the first item.

Not measured: an iPhone; the collapse-on dark arm (the reads are skipped there
by construction); a dark page asleep on Quick Resume, where the kept page is in
dark polarity and the dark pair's sync is the same call the light arm proved.

Method:

```bash
D=$(xcrun simctl create scratch com.apple.CoreSimulator.SimDeviceType.iPhone-Air \
    com.apple.CoreSimulator.SimRuntime.iOS-26-5); xcrun simctl boot $D
xcrun simctl install $D build/ios-sim-picco/ios/Release-iphonesimulator/CrossPointX3.app
C=$(xcrun simctl get_app_container $D com.natebunnyfield.crosspoint.picco data)
mkdir -p $C/Documents/.crosspoint
# Light arm. slideSwitchAction 1 binds the switch to Dark Mode, so the light
# follows the Frontlight row and no NSUserDefaults write is needed.
echo '{"frontlightBrightness":100,"frontlightWarmth":100,"frontlightOn":1,
  "frontlightRestoreOnWake":1,"slideSwitchAction":1,"darkMode":0}' \
  > $C/Documents/.crosspoint/settings.json
SIMCTL_CHILD_CROSSPOINT_SIM_LOG_POWER=1 SIMCTL_CHILD_CROSSPOINT_SIM_DARK=0 \
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='16000:POWER' \
SIMCTL_CHILD_CROSSPOINT_SIM_SCREENSHOTS="14000:$C/Documents/awake.bmp;22000:$C/Documents/asleep.bmp" \
xcrun simctl launch --console-pty $D com.natebunnyfield.crosspoint.picco > console.txt &
# ...27 s later: xcrun simctl terminate; read console.txt and the two BMPs.
# Wake arm: INPUT_SCRIPT='16000:POWER;21000:POWER' and SCREENSHOTS_AFTER_WAKE.
# Dark arm: slideSwitchAction 0, darkMode 1, and before the first launch a
# binary plist {piccoSlideSwitchOn: true} at
# $C/Library/Preferences/com.natebunnyfield.crosspoint.picco.plist (a fresh
# install's container is read; `[picco] slide switch present, on` confirms it).
# Desktop: a scratch directory with a '{}' settings.json and the same card
# keys, CROSSPOINT_SIM_AS_SHIPPED=1 CROSSPOINT_SIM_DARK=0
# CROSSPOINT_SIM_LOG_POWER=1 CROSSPOINT_SIM_LOG_PRESENTS=1
# CROSSPOINT_SIM_INPUT_SCRIPT='6000:POWER;9000:QUIT'
# CROSSPOINT_SIM_SCREENSHOTS='5000:awake.bmp;6180:asleep.bmp' (a capture due
# after the light-off line and before the sleep flush is served by the flush).
```

The firmware log tee (`diagnostics/firmware.log`) loses its last lines when the
app is terminated, which is the sleep entry; `--console-pty` has them.

## Brightness -100..300 in the app (2026-11-27)

Owner, verbatim: *"let brightness go from -100 to 300, keeping current 0 to 100
as is"*.

**Scope.** The Picco APP and simulator only. The device's Brightness row stays
0..100: it is a PWM duty on a real lamp, which has nothing past either end.

**Storage.** A settings byte cannot hold -100..300, so the app build stores the
step: shown = -100 + 5 x stored, 0..80, default 32 (= 60). Firmware:
`CrossPointSettings.h` (the default, `#if FREEINK_DEVICE_PICCO &&
defined(SIMULATOR)`), `SettingsList.h` (`{0, 80, 1}` + `withShown(-100, 5)`
under `#ifdef SIMULATOR`), `SettingInfo::shown()` (simulator builds carry the
two fields; the device gets a constexpr identity, so its SettingInfo copies do
not grow), used by the row text (`SettingRowUi.h valueText`) and the web
settings API (GET in shown units; POST accepts only a value the row can show).
Simulator: `FrontlitLight.h brightnessFromStored`, decoded in
`HalFrontlight.cpp publish()`; the X4 Pro byte is still a percent.

**The page.**
- 0..100: unchanged. Measured: all 3,528 (tube x brightness x warmth, by 5)
  pages, both pairs, tail, trail and bloom, byte-identical against the header
  before the change (a dump built twice, `cmp`).
- Above 100: the 60..100 slope continues (`rampFor`). At 300 the beam is 3.4x
  the frozen trace (channels clip, the overdriven whitening), the ink depth
  4.6, the afterglow sqrt(3.4) = 1.84x as long. Bloom stays capped at
  `scanlines::kBloomMax`. Still over 7:1 everywhere (tested).
- Below 0: the only settings that break the 7:1 floor, because the owner asked
  for less than the floor's 0. The mark fades toward the page in linear light
  (`fadeToContrast`, bisected) so that contrast falls log-evenly from 7:1 at 0
  to **1.5:1 at -100**, the same ratio on both pages at every step; beam,
  bloom and afterglow fade with the trace.
- **Rejected: fading to nothing at -100.** Built first and captured: the page
  went blank, and Settings is drawn on the same page, so the row that brings
  the text back would be unreadable. Also rejected: a linear-light fraction
  (1 at 0 to 0.1 at -100), which left the light page at 1.09:1 against the
  dark page's 1.6:1 at -100, because a small linear difference on a bright
  sheet is little contrast.

**Proof.** `tests/frontlit_page_test.cpp` section 6 (decode; every step below 0
dims both pages and moves only the mark; -100 is 1.5 +/- 0.05:1 on both pages
for every tube and warmth; above 100 the beam rises, the ink deepens, 7:1
holds, bloom capped). Desktop `simulator_picco` captures at -100, -50, 0, 60,
100, 200, 300, dark and light, Warmth 50 (card settings.json
`frontlightBrightness` = the stored step, `CROSSPOINT_SIM_AS_SHIPPED=1`,
screenshot at 3600 ms). Not captured: the Settings row's text reading "-100"
(the one `valueText` line), and the app on the phone, UNCONFIRMED.
