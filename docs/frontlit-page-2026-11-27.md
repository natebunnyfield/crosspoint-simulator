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

**The light switch matters.** On iOS the light follows the pad's slide switch
(stored, `CrossPointPrefs_piccoSlideSwitchOn`), as on the device. **With the
switch off, the page is the frozen page whatever the rows say.** That was a
choice, not forced: the alternative is to ignore the switch.

## Where it lives

- `src/FrontlitPage.h` -- the pure model. `src/FrontlitLight.h` -- the light's
  state and the simulator-only `simfrontlight` API.
- `src/HalFrontlight.cpp` -- `present()` is true on the Picco as well as the X4
  Pro (the hardware has a light). Publishes the Picco's state with a generation
  counter and an optional change hook.
- iOS: `ios/PanelPrefs.h` (both pairs), `ios/CrossPointIOSShim.cpp`
  `pollPanelGlow` (trail and tail, edge-triggered on the light's generation,
  overriding the mixer only when the light is not neutral) and `pollScanlines`
  (bloom).
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
(`src/SurfaceTube.cpp:310-313`, `src/Scanlines.h:298-302`), so they fall to
about 6% of their shipped depth at Brightness 0, about 80% at 5, and are full
from 10 (adversarial review, 2026-11-27, probe). The device rows step by 5.

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

## Not done

- iOS: the Picco app builds for the simulator. On an iPhone Air simulator,
  with the card at 100/100, light on, and `piccoSlideSwitchOn` true, the app
  logged `[glow] preset 0 -> 1296 ms trail`, which is the model's Brightness
  100 trail, so the light reaches the iOS polls. The glass itself was NOT
  captured: `simctl io screenshot` kept returning a stale home screen while the
  app ran. The page colors on iOS are UNCONFIRMED.
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
