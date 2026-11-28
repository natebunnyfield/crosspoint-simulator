# The full CRT gamut on the Picco's dark page: a plan, 2026-11-27

Owner, verbatim, 2026-11-27: *"let's plan out how to get the full gamut of
blue, green, yellow and red crt colors with warmth and maybe an new additional
setting or brightness"*. Then, while this was being written: *"be sure to use
actual crt emulation per the md file research"*.

**Status: PLANNING. No product code was changed.** Everything below was measured
from the code at simulator `0aa4996b` (branch `picco-layout`) and firmware
`ab0096a87`, by a probe that includes the simulator's own pure headers, and
rendered by the real desktop `simulator_picco` binary. The owner decides from
the pictures; the picture set is listed under **Renders**. Device feel and the
iOS app are UNCONFIRMED for every option (nothing was built).

Starting point: [frontlit-page-2026-11-27.md](frontlit-page-2026-11-27.md)
(ST-012). Today the Picco's two firmware rows, `frontlightBrightness` and
`frontlightWarmth` (0..100, defaults 60/50, firmware
`src/CrossPointSettings.h:249-250`), drive the simulated page. On the dark page
Warmth multiplies the warm guns, P38 amber and P22R red, by
*f* = 3^((w-50)/50), and divides the cool guns, P45 white and P20 yellow-green,
by *f* (`src/FrontlitPage.h:100`, `:229` `reweightedMix`, gun weights
19/88/17/36 at `src/FrozenPage.h:76`). Brightness is the beam
(`computeDarkPage`, `:254`).

## Owner rulings

- **2026-11-27: "B wins".** He saw the renders first (artifact M3UADdLvnVrymEUpmK3XQC). A Tube row, app and simulator builds only, picks the phosphor; Warmth keeps its meaning. Sub-rulings follow; the ones still open are listed last. Open: blue and red dimming, the warm tilt's afterglow, and the Tube with the light off.
- **2026-11-27, Yellow and Amber: "Keep both".** Six tubes: Mixed, Blue, Green, Yellow (P28), Amber (P3), Red.

## 1. Today's gamut, measured

Every one of the 441 settings (Warmth and Brightness 0..100 by 5, light on)
was put through `frontlitpage::darkPage` and the trace converted to CIE 1931 xy
and CIELAB (D65).

| | today, over all 441 settings |
|---|---|
| CIE x | 0.280 .. 0.412 |
| CIE y | **0.329 .. 0.348**: one thin horizontal line |
| trace luminance Y | 0.336 .. 0.952 |
| CIELAB chroma C* | **3.6 .. 37.4** |
| CIELAB hue | 36° (salmon, Warmth 100) .. 199° (pale cyan, Warmth 0), through near-neutral (C* 5) at Warmth 50 |
| afterglow | 794 .. 1296 ms, amber tail (P38's share) everywhere |
| worst contrast | 7.003:1 (Warmth 35, Brightness 0) |

The Warmth row at Brightness 60, trace on glass:

| Warmth | 0 | 25 | 50 | 75 | 100 |
|---|---|---|---|---|---|
| trace | B4EDE7 | BDE6DF | **CFD4CC** | E4B9AE | F39F8F |
| glass | 162122 | 171F20 | **171B1B** | 181413 | 190D0A |
| C* / hue | 19 / 189° | 15 / 184° | 5 / 133° | 18 / 40° | 36 / 36° |

The real phosphors, as the emulation renders them (dark trace from
`src/PanelPalette.h`, measured CIE point from
[crt-phosphor-presets.md](crt-phosphor-presets.md) §1 where one is published),
and how close today ever gets (CIELAB ΔE76 to the nearest of the 441):

| color | phosphor | trace on glass | contrast | C* / hue | measured CIE | nearest today | ΔE |
|---|---|---|---|---|---|---|---|
| blue | P11 | 8B92FF on 00061A | 7.35 | 61 / 294° | 0.147, 0.076 | A2A6A0 | **64** |
| blue | P22B | AFB0FF on 000027 | 10.18 | 43 / 294° | 0.148, 0.062 | A6B1AB | **47** |
| blue | P47 | B0B4FF on 030527 | 10.26 | 40 / 292° | 0.170, 0.103 | B7BBB4 | **44** |
| green | P1 | 33FF33 on 001A00 | 13.50 | 112 / 137° | 0.208, 0.704 | C5F9F1 | **101** |
| green | P22G | 00FF97 on 00190A | 13.78 | 81 / 154° | none | C0FCF6 | **66** |
| green | P31 | 3DFF6F on 03270A | 12.12 | 93 / 144° | 0.287, 0.521 | BCF7F1 | **80** |
| green | P39 | 00FF00 on 002700 | 11.86 | 120 / 136° | none | C5F9F1 | **109** |
| yellow-green | P20 | 7CFF00 on 071900 | 14.08 | 110 / 129° | none | C5F9F1 | **101** |
| yellow | P28 | FFC600 on 191100 | 11.88 | 84 / 85° | none | FFAD9B | **66** |
| amber | P3 | FFB000 on 1A1000 | 10.25 | 83 / 77° | none | FDA695 | **60** |
| amber | P38 | FFA472 on 190800 | 10.04 | 49 / 54° | none | FDA695 | 18 |
| red | P22R | FF6F6C on 1A0300 | 7.33 | 62 / 28° | 0.647, 0.343 | F19D8E | **28** |
| red | P27 | FF9BA5 on 190002 | 10.06 | 40 / 16° | none | F19D8E | 13 |
| red | P56 | FFA5A4 on 270100 | 10.24 | 36 / 23° | 0.650, 0.346 | FBAB9C | 8 |
| white | P45 | B6EFFF on 182327 | 12.82 | 20 / 223° | (0.269, 0.311) | C7FFFF | 10 |

**Confirmed: blue, green and yellow are unreachable today, and so is P3 amber.
Red is reachable only as the pale P56/P27 salmon, not as P22R.** Why, from the
code: Warmth is ONE number moving ONE ratio between two FIXED pairs of guns, so
everything it can make lies on a line between two blends. Taken to an infinite
ratio, the warm pair alone (P38:P22R, 19:36) is FF846E (C* 56, hue 37°) and the
cool pair alone (P45:P20, 88:17) is AEF2EC (C* 23, hue 190°). At the shipped
ratio of 3 each end still carries a ninth of the other pair, which is why the
ends are F39F8F and B4EDE7. None of the four guns is blue, the only green gun
(P20) carries 17 of 160 weight and is swamped by P45 white, and yellow sits on
no line between those two ends. Brightness cannot help: it scales the trace's
emission, which keeps the chromaticity (and, past 1.0 per channel, whitens it).

Picture: `gamut.png` (CIE xy, every setting of today and of options A, B, C,
the rendered phosphors as stars and the measured CIE points as rings).

## 2. What the research fixes before any option is drawn

Each option below is built only from things these docs already establish:

- **Colors are JEDEC phosphors from the emulation's own table**
  (`src/PanelPalette.h` `kPresetInfo`, derivation in
  [crt-phosphor-presets.md](crt-phosphor-presets.md) §5 and §10, "derived by
  script, not by hand"). No new hex is typed anywhere.
- **In-between colors are powder blends, mixed the mixer's way**: weighted
  average in LINEAR light of the components' inks and glasses, trail = the
  slowest component, tail = the survivors' share
  ([phosphor-mixer.md](phosphor-mixer.md) "The three modes";
  `phosphormix::mixBlend`). Premixes (P4, P6, P7, P14, P17, P18, P23, P40) are
  never ingredients ("Premixes are recipes, not ingredients"). None is used.
- **Full-purity blue and red cannot meet 7:1 at all**
  ([crt-phosphor-presets.md](crt-phosphor-presets.md) §2: 611 nm red at sRGB's
  limit is 5.41:1 against pure black; §6: P11 blue is 3.01:1). The table's P11
  and P22R rows are already pulled 25.8% and 14.9% toward D65 to reach 7.35 and
  7.33. Any "blue" or "red" option inherits those rows and their tight margin.
- **A saturating beam loses purity, not hue** (same doc, §2 and §6). That is the
  emulation's own justification for those rows, and it rules out any mapping in
  which MORE beam means MORE saturation (section 5).
- **Which greens and ambers the owner chose**:
  [phosphor-shortlist-2026-08-18.md](phosphor-shortlist-2026-08-18.md), the
  VALID runoff (Kendall 0.843). P3 Amber first (10/11), the P12/P19/P33/P38
  orange second, **P22G TV Green third (9/11)**, P11 Blue sixth, P22R Red 2/11,
  and **P1 Green last (0.5/11)**, carrying P39 and P20. So the green used below
  is P22G, not P1. The same runoff clustered **P28 yellow under P3 amber** (one
  page within ΔE 25): Yellow and Amber are near-duplicates to his eye.
  ([phosphor-ranking-2026-08-18.md](phosphor-ranking-2026-08-18.md) is VOID and
  is not cited for any preference.)
- **The glow is always on for a tube, derived from the phosphor**
  (shortlist doc, "SETTLED"), and **the raster is glass**: scanlines never fade
  and are drawn over the ghost ([letterpress-and-scanlines.md](letterpress-and-scanlines.md)
  "The raster is GLASS"). Nothing below changes either.
- **Texture is paid for out of contrast above 7:1.** Scanline depth
  (same doc, "The inherited constraints": the 7:1 budget caps line depth) and
  grain amplitude ([phosphor-grain.md](phosphor-grain.md) "The amplitude is
  per-palette": P11 clamped to 0.35x) shrink on a tight page.
- **The afterglow is the whole glass** ([whole-glass-crt.md](whole-glass-crt.md)
  §2, §11): every option's trail and tail feed the same output-space
  accumulator, ink-scaled deposit; nothing new is needed there.

Measured consequences for the colors the options use (scanline depth as a
percentage of the frozen page's, the depth chain in
[frontlit-page-2026-11-27.md](frontlit-page-2026-11-27.md) Method):

| page | contrast at beam 1 | Brightness 0 beam (the 7:1 floor) | scanline depth at Brightness 60 | at Brightness 0 |
|---|---|---|---|---|
| frozen four-gun | 11.53 | 0.58 | 100% | 6% |
| P11 blue | 7.35 | **0.95** | **58%** | 9% |
| P22G green | 13.78 | 0.48 | 100% | 11% |
| P28 yellow | 11.88 | 0.56 | 100% | 2% |
| P3 amber | 10.25 | 0.66 | 100% | 4% |
| P22R red | 7.33 | **0.955** | **54%** | 10% |
| P22B blue (alternative) | 10.18 | | 100% | |

**Blue and red have almost no room to dim.** At Brightness 0 the beam can only
fall to 0.95, so the lower 60% of the Brightness row moves the P11 trace from
888FF9 to 8B92FF and does nothing visible; and the raster runs at about half
depth even at the default. That is the 7:1 floor, not a tuning. The way out,
if the owner wants it, is the less saturated row of the same chemistry: P22B
(AFB0FF, 10.18:1, full raster) for blue, P56 (FFA5A4) or P27 for red.

## 3. The options

All three keep the frozen page at 60/50 byte-identical, keep the light page
exactly as today (Warmth = the paper's warmth, Brightness = the ink's depth;
the doctrine, [letterpress-and-scanlines.md](letterpress-and-scanlines.md):
light is paper and ink, no phosphor), and hold ≥ 7:1 everywhere through the
existing beam-floor search. Worst contrast over the grid, from the probe:
**7.000:1** for each. Every in-between color is a blend of at most seven
real phosphors in the mixer's own math; the probe's N-component blend
reproduces `mixBlend` and `darkPage` byte-for-byte at all 440 non-neutral
settings.

### Option A: Warmth walks real phosphors (no new row)

**Mapping** (Warmth, dark page only; Brightness keeps the beam ramp on top):

| Warmth | 0 | 0..25 | 25 | 25..50 | 50 | 50..70 | 70 | 70..85 | 85 | 85..100 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| phosphor | **P11** | P11+P22G blend | **P22G** | P22G + the four guns | **frozen tube** | four guns + P28 | **P28** | P28+P3 | **P3** | P3+P22R | **P22R** |

Linear-light blend weights run linearly with Warmth inside each leg. Warmth 50
takes today's code path itself, so the whole Warmth-50 column (every
Brightness) is byte-identical to today; every other Warmth value moves, on
purpose.

| Warmth | 0 | 10 | 20 | 25 | 40 | 50 | 60 | 70 | 85 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|
| trace | 8B92FF | 6EC7DD | 40EEB2 | 00FF97 | A4E7B9 | CFD4CC | E9CD95 | FFC600 | FFB000 | FF6F6C |
| glass | 00061A | 001015 | 00160E | 00190A | 101A16 | 171B1B | 181611 | 191100 | 1A1000 | 1A0300 |
| contrast | 7.35 | 10.03 | 12.57 | 13.78 | 12.45 | 11.53 | 11.73 | 11.88 | 10.25 | 7.33 |
| afterglow ms | 126 | 126 | 126 | 63 | 1095 | 1095 | 1095 | 283 | 322 | 283 |

- **Contrast**: ≥ 7.000:1 at all 441 settings. At Warmth 0 (blue) and 100
  (red) the beam floor is 0.95, so Brightness 0..60 is flat there (section 2).
- **Afterglow**: the blend rule. The legs that touch the four guns carry P38's
  1095 ms and its amber tail; a pure phosphor dims in its own color (P11 126 ms,
  P22G 63, P28 283, P3 322, P22R 283). **The trail jumps from 63 ms at Warmth
  25 to 1095 ms at 30**, where P38 re-enters.
- **The neutral notch**: Warmth 50 is the shipped near-white tube, so the walk
  goes green, then pale, then yellow (C* 81, 34, 5, 32, 84 at 25, 40, 50, 60,
  70). That is the price of keeping 50 as the frozen page.
- **Light page**: unchanged. So Warmth means two things: a warm or cool PAPER on
  the light page, a PHOSPHOR on the dark one. The ends agree (cool/blue,
  warm/red); Warmth 25 is a slightly cool sheet beside a green tube.
- **Firmware**: none. Same row, same key, same web API.
- **Simulator**: `FrontlitPage.h` `reweightedMix` replaced by the walk; an
  N-component blend (or `kMaxComponents`, `src/PhosphorMix.h:74`, raised from 4
  to 5, since the legs touching the four guns need five);
  `tests/frontlit_page_test.cpp`'s gun-direction checks rewritten; the
  iOS polls and the desktop hook need nothing new (they already ask
  `darkPage`).
- **Other boards**: nothing moves (`simfrontlight::current()` is off off the
  Picco, `src/HalFrontlight.cpp:23`).
- **Risks**: overloads a row whose name is "Warmth"; moves every Warmth value
  the owner may already have set; the 63 → 1095 ms trail jump; the colors
  exist only while the light is on (off, and on the default slide-switch
  binding the switch off, the page is the frozen page).

Picture: `option-A.png`.

### Option B: a Tube row picks the phosphor; Warmth tilts it

**Mapping**: a new Picco row, **Tube** (enum): **Mixed** (default; today,
untouched), **Blue** P11, **Green** P22G, **Yellow** P28, **Amber** P3,
**Red** P22R. At Warmth 50 each family IS its JEDEC row, byte for byte (a
one-component blend is `resolve()` of the preset, phosphor-mixer.md "Selecting a
preset seeds the guns"). Warmth keeps the meaning it ships with, the same four
guns: above 50 it adds the warm pair (P38:P22R, 19:36), below 50 the cool pair
(P45:P20, 88:17), at weight 0.25·(f−1) or 0.25·(1/f−1), so Warmth 0 or 100 is
one third tilt gun, two thirds family. Brightness is the beam as today.

| | Blue | Green | Yellow | Amber | Red |
|---|---|---|---|---|---|
| Warmth 50 | 8B92FF on 00061A, 7.35 | 00FF97 on 00190A, 13.78 | FFC600 on 191100, 11.88 | FFB000 on 1A1000, 10.25 | FF6F6C on 1A0300, 7.33 |
| Warmth 0 | 98B9F9 on 09131D, 9.48 | 69FBB9 on 091C15, 13.55 | E8D690 on 181811, 12.27 | E8C990 on 191711, 11.25 | E8AAA6 on 191211, 9.45 |
| Warmth 100 | BC8EDC on 0B0614, 7.66 | 9CE08B on 0B1407, 12.04 | FFB441 on 190E00, 10.74 | FFA341 on 1A0D00, 9.59 | FF776D on 1A0400, 7.64 |

- **Contrast**: ≥ 7.000:1 at every family × 441 settings (worst 7.000, Blue at
  Warmth 95, Brightness 0). Blue and Red: Brightness 0..60 nearly flat at 12 of
  21 Warmth steps (beam floor > 0.9).
- **Afterglow**: the blend rule again. A family at Warmth 50 dims in its own
  color at its own speed. **Any warm tilt brings P38: 1095 ms and the amber
  tail (5F3A26 at Warmth 100) from Warmth 55 up; any cool tilt brings P20,
  400 ms.** A tuning choice worth a ruling: tilt with P22R alone (warm) and P45
  alone (cool), both 283 ms "Medium", and the tilt stops changing the trail.
- **Frozen page**: Tube = Mixed is today's code path; nothing moves until the
  row is moved.
- **Light off**: recommended that the Tube applies with the light off too (the
  tube is not the lamp); the probe's light-off rows are the bare JEDEC pages.
  The owner's call.
- **Firmware**: `uint8_t tubeColor = 0` in `CrossPointSettings.h`; one
  `SettingInfo::Enum(STR_TUBE, ..., {STR_TUBE_MIXED, STR_BLUE, STR_GREEN,
  STR_YELLOW, STR_AMBER, STR_RED}, "tubeColor", STR_CAT_DISPLAY)` in the Picco
  block of `src/SettingsList.h` (`:776-801`), `PICCO_ENTRY_COUNT` (`:345`) +1;
  admitted by `isPiccoDeviceRow` (`SettingsActivity.cpp:71`); seven new
  `tr()` strings (none exist today) in `english.yaml` and `spanish.yaml`, append
  only (the index is the stored value). The settings.json key and the web
  settings API come free: both walk `getSettingsList()`
  (`CrossPointSettings.cpp:36`, `:144`; `/api/settings`,
  `CrossPointWebServer.cpp:317-318`). **Compile all of it under `#ifdef
  SIMULATOR`** (section 4), the pattern `CrossPointSettings.h` already uses.
  The host learns the value through a call the firmware makes only under
  `SIMULATOR` (on change and after settings load), so the device HAL needs no
  counterpart (CLAUDE.md, "Simulator-only methods the firmware never calls need
  no counterpart").
- **Simulator**: `FrontlitPage.h` takes the family; the publish in
  `HalFrontlight.cpp` (or a sibling) carries it with the generation counter so
  `pollPanelGlow` / `pollPanelPalette` / `pollScanlines` and the sleep tick
  re-read on a change; the desktop hook likewise; the test sweeps 6 families ×
  441 settings for 7:1 and the tail.
- **Other boards**: the row is in the Picco block; X3/X4 never see it. It could
  later serve every board, since it needs no light.
- **Risks**: Yellow and Amber may read as one choice (shortlist clustering);
  blue and red have no dimming room and a half-depth raster unless P22B/P56
  replace them; the P38 trail jump on the warm tilt.

Picture: `option-B.png`.

### Option C: a continuous Phosphor row; Warmth tilts it

**Mapping**: a new Picco row, **Phosphor** (value 0..100 by 5, default 50,
stepped by the rocker like Brightness and Warmth, `isRockerStepped`,
`SettingsActivity.cpp:50`). Phosphor walks option A's path (P11, P22G, the
four guns at 50, P28, P3, P22R); Warmth adds option B's tilt on top; at
Phosphor 50 Warmth is exactly today's.

| Phosphor | 0 | 10 | 20 | 30 | 50 | 60 | 70 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|---|
| Warmth 50 | 8B92FF | 6EC7DD | 40EEB2 | 63F7A3 | CFD4CC | E9CD95 | FFC600 | FF9E3F | FF6F6C |
| Warmth 0 | 98B9F9 | 88D7E2 | 74EFC8 | 82F5C0 | B4EDE7 | D7DAB8 | E8D690 | E8BF98 | E8AAA6 |
| Warmth 100 | BC8EDC | B0B4C1 | A3D3A0 | ADDA94 | F39F8F | F0B98A | FFB441 | FF9652 | FF776D |

- **Contrast**: ≥ 7.000:1 over 11 Phosphor × 441 settings. Same blue/red floor.
- **Afterglow, frozen page, light page, other boards**: as A (at Warmth 50) and
  B (the tilt). Default 50 is today's page byte for byte.
- **Firmware**: as B, but a Value row `{0, 100, 5}` and one string
  (`STR_PHOSPHOR`), plus the rocker-stepping list.
- **Simulator**: as A plus B; blends of up to seven components.
- **Risks**: the in-betweens are mostly washed blends (C* 28 at Phosphor 10, 34
  at 40, 7 at Phosphor 10 / Warmth 100); a number is a poorer name for a color
  than "Green"; two rocker rows to reach one tube.

Picture: `option-C.png`.

## 4. On the real Picco (the panel cannot show color)

How the rows drive the device today: Warmth and Brightness call
`Frontlight.setWarmth` / `setBrightness` live from the rocker
(`SettingsActivity.cpp:380-384`) and at boot (`main.cpp:1077`), down to
`FrontlightManager::applyPicco` (freeink-sdk
`libs/hardware/FrontlightManager/src/FrontlightManager.cpp:324`), which reads a
10 × 10 vendor table of cool/warm PWM and current (`PICCO_FL_LUT`, `:184`):
Brightness picks the step on a perceptual curve (`:338`), Warmth interpolates
the row, 0 = the cool LED string alone, 100 = the warm string alone (`:353`).
The web settings POST stores the values; no `Frontlight` call was found in
`handlePostSettings` (`CrossPointWebServer.cpp:1708`), so the LEDs take a web
change at the next boot (read, not run).

- **Option A**: on the device Warmth stays exactly the LED mix; nothing in the
  firmware changes. The simulator reads the same number as a phosphor. The ends
  line up physically (Warmth 0: the cool white LED and a blue tube; 100: the
  warm LED and a red one); the middle does not (Warmth 25 is a mostly cool lamp
  on the device and a green tube in the app).
- **Options B and C**: a Tube or Phosphor row would do nothing on an e-ink
  panel, so it must not exist there. Compiled under `#ifdef SIMULATOR`, the
  device, its settings.json and its web page never see it; the iOS Picco app
  and the desktop `simulator_picco` do. Brightness and Warmth keep their LED
  meaning on the device and their beam and tilt meaning in the app. A Settings.app
  row in the Picco's `Root.plist` is the other place it could live, but it would
  have to earn itself against the 2026-08-23 ruling that removed every surface
  dial from there, and it could not be stepped with the rocker.
- **Brightness**, in every option: the LED intensity on the device and the beam
  in the app, as today.

## 5. Checked and found not viable

- **Brightness above 60 as purity** (a first draft of a 2-D Brightness ×
  Warmth map: Warmth the hue, Brightness 60..100 blending toward the pure
  phosphor). Contradicts the emulation's own physics, a brighter beam
  DESATURATES ([crt-phosphor-presets.md](crt-phosphor-presets.md) §2, §6), and
  would tie "more light" on the device to "more saturated tube" in the app. It
  also left Brightness 60..100 dead at Warmth 50. Dropped.
- **Afterglow-only hue** (the page stays today's; a cascade's persistence
  layer takes the color, like P7/P14/P17, crt-phosphor-presets.md §9).
  A persistence layer has to outlast the flash, and the table has no
  long-persistence BLUE or YELLOW phosphor: the Long and slower rows are P2
  blue-green, P34/P39 green, P12/P19/P26/P33/P38 orange, P21 red and the
  premixes (`kPresetInfo`). Blue and yellow afterglows would be invented.
  Dropped. (A green, orange or red afterglow is possible, but it is not the ask.)
- **Widening today's warm/cool pairs**: any one-ratio balance between two fixed
  blends makes a line, not an area, so it cannot reach four corners; measured
  limits FF846E and AEF2EC (section 1).
- **Full-purity blue and red**: 3.01:1 and 5.41:1 maximum against black
  (crt-phosphor-presets.md §6, §2). The P11 and P22R rows are already as pure
  as 7:1 allows.
- **Hue rotation or sRGB interpolation**: not used anywhere, by ruling; every
  in-between above is a linear-light powder blend.
- **The `isLowContrastByDesign` exemption** as a way to get purer blue/red:
  an owner ruling (crt-phosphor-presets.md §2 "Open"), and the test allows
  exactly one exemption. Not proposed.

## 6. Recommendation

**Option B**, with the Tube row compiled only into the simulator builds.

- It is exactly the four colors asked for, named, plus amber, each one the
  emulation's own JEDEC page byte for byte, with that phosphor's own
  persistence.
- Warmth keeps the one meaning it already has on both pages and on the device
  (the same four guns; the LED mix), so no existing setting moves and the
  frozen page is untouched until the row moves off Mixed.
- On the real Picco nothing changes and nothing appears that cannot work.

A costs no firmware and is the cheapest to build, but it turns a row named
Warmth into a color wheel in the app while it stays a lamp on the device, and
moves every Warmth value already in use. C adds in-between blends B does not
have, but most of them are washed (C* 25-35) and it doubles the rocker work.

Decisions B needs from the owner, one at a time: (1) P11/P22R, or the
full-range P22B/P56 for blue and red; (2) keep both Yellow and Amber, or one;
(3) the warm tilt with P38 (1095 ms amber tail) or P22R alone (283 ms);
(4) does the Tube apply with the light off.

## Renders

Real captures of the desktop `simulator_picco` (firmware worktree build of
2026-11-27 18:56): `CROSSPOINT_SIM_AS_SHIPPED=1`, dark, a reader page of
`measure.epub`, window scale 2 with `CROSSPOINT_SIM_PIXEL_EXACT=1` (nearest,
so 1x text is pixel-doubled and the raster is 2 px per source row; the phone is
2x render at about 2.39 px), grain seed 7, the same `.crosspoint` restored
before every arm. The whole emulation is drawn: beam, scanlines, bloom,
whole-glass accumulator. Each arm shows the steady page and the glass 150 ms
after a page turn (the old page's afterglow under the new one). Today's arms
run the shipped model; option arms force the option's trace and glass
(`CROSSPOINT_SIM_PANEL_{INK,PAPER}_DARK`), trail (`_GLOW_MS`) and tail
(`_GLOW_TAIL`; a pure phosphor's tail pinned to its own ink, per the trap in
[whole-glass-crt.md](whole-glass-crt.md) §11). **Every one of the 43 arms'
brightest tone equals the model's trace exactly**, and the modal glass is one
code value under the model's glass (the scanline gaps).

Files (scratchpad, not committed): `today.png`, `option-A.png`,
`option-B.png`, `option-C.png`, `gamut.png`.

Limits of the renders: the tail ONSET cannot be forced by environment, so the
option arms keep today's onset at that Warmth/Brightness; the scanline bloom
follows today's beam rather than the option's (equal at Brightness ≥ 60); the
desktop composites the trail with ADD, the phone with MAXIMUM
(whole-glass-crt.md §6); a still cannot show a trail's motion.

## Method

```bash
SIM=<simulator worktree>; FW=<firmware worktree>; S=<scratch>/crt-gamut
# 1. the model: today and A/B/C over the grid, self-checked against darkPage
c++ -std=c++17 -O2 -I$SIM/src -o $S/probe/gamut $S/probe/gamut.cpp
$S/probe/gamut > $S/probe/grid.csv
#   stderr must read: beamOver mismatches 0 / 440, blendF(today) mismatches 0 / 440
python3 $S/probe/analyze.py $S/probe      # xy, CIELAB, worst contrast
c++ -std=c++17 -O2 -I$SIM/src -o $S/probe/depth $S/probe/depth.cpp   # scanline depth
# 2. the renders: one run per arm, from a scratch card
#    card: fs_/books/measure.epub, .fonts/fonts symlinked, state.json
#    openEpubPath=/books/measure.epub readerActivityLoadCount=0, '{}' settings.json
#    beside the binary, fs_/.crosspoint restored from a pristine copy per arm
CROSSPOINT_SIM_AS_SHIPPED=1 CROSSPOINT_SIM_DARK=1 CROSSPOINT_SIM_GRAIN_SEED=7 \
CROSSPOINT_SIM_WINDOW_SCALE=2 CROSSPOINT_SIM_PIXEL_EXACT=1 SDL_VIDEODRIVER=dummy \
CROSSPOINT_SIM_INPUT_SCRIPT='4000:UP;5600:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS='3600:steady.bmp;4150:ghost.bmp' \
[CROSSPOINT_SIM_PANEL_INK_DARK=.. CROSSPOINT_SIM_PANEL_PAPER_DARK=.. \
 CROSSPOINT_SIM_PANEL_GLOW_MS=.. CROSSPOINT_SIM_PANEL_GLOW_TAIL=..] \
$FW/.pio/build/simulator_picco/program
#    card settings.json: frontlightBrightness/Warmth = the arm, frontlightOn 1,
#    frontlightRestoreOnWake 1, darkMode 1
python3 $S/probe/arms.py; python3 $S/probe/compose.py; python3 $S/probe/plot.py
```

Two traps found doing it. On the Picco the page turns on **physical UP** (the
rocker's upper end, mapped to logical Right, firmware
`MappedInputManager.cpp:65-77`); scripted `RIGHT` and `QTAP:RIGHT` press
nothing the reader reads. And at window scale 1 the shipped scanlines are one
device pixel per source row and do not show at all in a capture (four tones
only); scale 2 shows them.

The probe's options live only in the probe (`gamut.cpp`: `optionA`, `optionB`,
`optionC2`); its `blendF` is `mixBlend` with float weights and no four-component
cap.
