# E-ink mode — spike, 2026-09-25

Owner ruling 2026-09-25: the next spike is "E-ink mode". The real e-paper
panel's refresh behavior, simulated on the phone:

- the full-refresh **flash**,
- **ghosting** that builds up across partial refreshes,
- a **shake** that clears the ghosts with a full refresh.

Where the idea came from: `docs/research-novel-reading-interfaces-2026-09-24.md`,
entries **M8** (e-ink paper-white) and **F16** (shake the snow globe), and spike
plan 2. `docs/surface-roadmap.md` §4d ranks it the top third-mode candidate.

**Status: SPIKE. Device feel is UNCONFIRMED.** Everything below was measured on
the desktop simulator, at render scale 2, with a headless X3 build. None of it
has been seen on a phone. On the phone, watch for three things:

- the ghost's strength after about 8 page turns;
- the full-refresh flash when you shake (the shake has to be bound to Full
  Refresh first);
- whether the reader's periodic refresh reads as a clean-up or as nothing.

Built on branch `worktree-agent-af956acd4be87f3dd`, which was fast-forwarded to
`acc7ca2`.

## 1. The design

### 1.1 Keyed on the firmware's real refresh requests

The simulator does not invent a schedule. The firmware already chooses a refresh
mode on every paint. `HalDisplay::refreshDisplay(mode, …)` used to discard that
argument, and now reads it:

| Firmware request | Where it comes from | E-ink mode does |
|---|---|---|
| `FAST_REFRESH` | Every ordinary page turn, menu move and `displayWindow`. | A **partial** refresh. It is not animated. The page it replaced leaves a residue in the ghost plane. |
| `HALF_REFRESH` | `ReaderUtils.h displayWithRefreshCycle`: every N pages (`SETTINGS.getRefreshFrequency()`, default 15). Also the sleep screen, BMP viewer and image pages. | The panel's **clearing** waveform, animated frame by frame. The ghost plane is cleared. |
| `FULL_REFRESH` | Rare: the driver's first sync, or a forced sync. | The **full** waveform, animated. The ghost plane is cleared. |
| Compose, AA planes, polarity reconvert | The same page, painted again. | No transition. If a waveform is running, the new levels become its target. |

A page's AA compose follows its base pass. The compose is not a refresh, so the
next partial measures its residue against the **composed** page.

### 1.2 The waveforms are the X3's own, decoded

The source is `freeink-sdk/libs/display/FreeInkDisplay/src/lut/Uc8253X3Luts.h`.
These are the UC8253 banks that `Uc8253X3Driver.cpp` actually loads.

Each LUT group is laid out as:

```
[level byte, TP_A, TP_B, TP_C, TP_D, repeat]
```

The level byte holds four 2-bit codes:

- `00` = hold;
- `01` = drive **black** (every white→black table carries it);
- `10` = drive **white**.

The tables are indexed by the (old, new) pixel pair: WW, WB, BW, BB.

**FULL** (`_full`, 62 frames). The WW table is `4A`: black for 24 frames, hold
for 4, then white for 14 + 10. The WB table is `04`: hold for 28, black for 14,
hold for 10, then black for 10.

The driver fills DTM1 with **white** before the write
(`Uc8253X3Driver.cpp:183-186`). So every pixel is either WW or WB, and during
phase A:

- every pixel that will be paper goes black;
- every pixel that will be ink holds its old state.

The glass shows the new page **in negative**, merged with the old ink, and then
the page arrives. This is the classic e-ink flash.

**HALF** (`_half`, 25 frames). WW and BW are both `AA`, so they drive white for
19 + 5 frames. WB and BB are both `55`, so they drive black. Then 1 frame of
hold. **The X3's clearing refresh is a SCRUB, not an inversion.** Every pixel is
pushed to its own target, and nothing goes black first. So on the X3, the
reader's periodic "full" refresh does not flash black. It wipes out the ghosts
over about half a second. The owner's brief expected an inversion flash here.
The decoded tables say otherwise, and the simulator follows the tables.

**FAST** (`_fast`, 19 frames). A changed pixel is driven for 14 + 4 frames. An
unchanged pixel gets a 2-frame touch.

**Non-X3 builds.** The X4 and X4 Pro (SSD1677) run OTP sequences: `0xD7` for
HALF and `0xF7` for FULL. No file here holds their frames. On those builds the
simulator uses the X3 `_full` program for both requests. This stand-in is
**not measured**.

### 1.3 Optics

A pixel's level moves exponentially toward the rail it is driven at, with
`kTauFrames = 4`. A hold leaves it where it is. So for each of the four
transition classes, every frame is an **affine** function of the pixel's
starting level. A frame is therefore a table of 4 × 256 entries plus one lookup
per pixel.

**Frame period: 20 ms (50 Hz). This is ASSUMED, not decoded.** The PLL value
(`0x30 = 0x09`) was not mapped to a rate. A measured number does bound it from
above. `Uc8253X3Driver.cpp:147` records a warm FAST refresh at 435 ms, and the
fast bank is 19 frames long. So one frame takes at most 22.9 ms, because the
435 ms also includes the SPI transfer.

At 20 ms per frame:

- the full refresh lasts 1240 ms;
- the scrub lasts 500 ms.

### 1.4 Ghosts

First-order optics alone would draw **no visible ghost**. After the fast bank's
18 drive frames, a pixel keeps exp(−18/4) = 1.1 % of a full swing. That is about
3 levels.

Real panels accumulate **remnant**, which is why the firmware schedules clearing
refreshes at all. So the ghost plane is **phenomenological**, and says so. On
every partial:

```
ghost = ghost * 0.92 + residue(old -> new)
```

- A pixel that got **lighter** keeps 3 % of the ink it lost. That is the gray
  ghost of the previous page's text.
- A pixel that got **darker** keeps 1.5 % of the paper. That leaves a slightly
  light stroke.

**These numbers are TUNED, NOT MEASURED.** With them, a spot turned over four or
five times reaches the cap. That matches the owner's "builds up over a few
pages".

### 1.5 The ghost is held under the 7:1 floor by construction

The cap is computed from the **live palette** on every write. It is the largest
symmetric `g` (at most 26 levels) for which level `g` (the lightest ghosted ink)
against level `255 − g` (the darkest ghosted paper) still measures ≥ 7:1. The
live palette includes sheet drift, so the darkest leaf is the one checked.

A palette that is already under the floor gets a cap of 0, which means no ghost
at all. Solarized is one.

| Page | Cap |
|---|---|
| Frozen page (Sanguine on India) | **18 levels** |
| `kDefaultLight` | 26 levels |
| Solarized | 0 |

The cap is only honest if nothing else spends the paper's headroom. So in e-ink
mode, `FieldSelection.h` selects **no surface field on a light page**: no
letterpress sheet (tooth, formation, show-through, marks, wires) and no grain.
This is the roadmap's "third doctrine": an e-paper panel is not a printed sheet.

Ink rounding and ink spread still run. They reshape the type itself. They are
not a field over the page.

For the same reason, the **beam and the phosphor trail** are treated as off on
an e-ink light page (`einkQuiet` in `presentIfNeeded`). A reflective panel has
no gun, and a sweep over the flash frames would mean two machines driving one
page.

### 1.6 The dark page

E-ink mode draws **nothing** on a dark page. The dark page is the CRT, under the
2026-08-22 doctrine, and the phosphor trail already carries its persistence.
Leaving a light page drops the panel's memory, so coming back starts from a
clean panel.

This is a decision, and it is open. The alternative would be to model the X4
Pro's inverted panel, with light ghosts on a dark ground.

### 1.7 Controls

| Surface | What |
|---|---|
| Settings.app | New group **E-Ink Mode**, toggle `einkMode`. Ships **OFF**. |
| Dial table | `simdials::EinkModeOn`, pinned in `tests/dial_table_test.cpp`. |
| Desktop | `CROSSPOINT_SIM_EINK_MODE=1`, or `"einkMode": 1` in `settings.json`. |
| Gesture action | **Full Refresh** = `Action::FullRefresh = 14`, APPENDED and offered in both the global and zone lists. **No row defaults to it.** The shake keeps `ToggleZen`: moving that default would change what a shake does on every existing install. The owner binds it himself (Settings → Gestures — The Device → Shake → "Full Refresh — E-Ink Mode only"). With e-ink mode off, the action logs that it did nothing. |
| Headless | The `EINKFULL` verb in `CROSSPOINT_SIM_INPUT_SCRIPT`. |
| Logs | `[eink] mode on/off` and `[eink] firmware HALF refresh -> X3 _half (scrub)`. With `CROSSPOINT_SIM_LOG_TIMING=1`, also `[eink] FAST write N ms` and `[eink] flash frame: build/upload`. |

The host full refresh is **host-side**, and the firmware is not asked. On the
device, a manual full refresh is the same waveform over the same page. With old
and new identical, the WB class holds ink and WW goes black. So the glass goes
fully dark, as the second row of the proof figure shows, and the page returns.

## 2. Measurements

All on the desktop, with a `simulator_x3` build at `CROSSPOINT_RENDER_SCALE=2`,
built from a scratch copy of the firmware repo pointed at this worktree.
Headless runs use `SDL_VIDEODRIVER=dummy` and `CROSSPOINT_SIM_AS_SHIPPED=1`, a
light page with the frozen palette, and the card state restored before every
arm.

**OFF is byte-identical.** The spike build with e-ink mode unset was compared
against an `acc7ca2` baseline build. Two captures, one at book open and one
after two page turns, have identical md5s:

- `9e8627b6…`
- `909484a1…`

**Cost at 2x.** The desktop build sets no `-O` flag, so these are unoptimized
figures, and iOS release builds will be faster.

| Where | Cost | Thread |
|---|---|---|
| Partial page write (accumulate + ghosted write), 17 turns | median 23.6 ms, range 22.7–34.2 ms | render |
| Compose, same page, 8 turns | 48–84 ms with e-ink on, against 37–57 ms off: **about +12 ms** | render |
| Firmware HALF/FULL write | 35–36 ms | render |
| Waveform frame build | 5.9–6.6 ms | main |
| Waveform frame upload | 0.2–0.4 ms | main |
| Present total during the 25-frame scrub | median 10.2 ms | main |

The waveform frame was **14 ms** before the per-class lookup table replaced
doubles per pixel. The main thread presents every loop pass while a waveform
runs, for 500 ms (the scrub) or 1240 ms (the full refresh), and a frame is
rebuilt only when the panel's frame index moves.

**Effect, measured on the proof crops** (ghosted page against the same page
after a full refresh):

- 340 × 700 crop: mean Δ 1.11 levels, max 16, and 7.5 % of pixels move more than
  4 levels.
- ×4 crop: mean Δ 1.68, 17.5 % of pixels over 4 levels.

## 3. Proof figures

Lossless PNG at native 2x pixels, each at most 700 px wide. They live in
`docs/eink-mode-spike-2026-09-25/`.

| File | What it shows |
|---|---|
| `eink-full-refresh-sequence.png` | A 220 × 260 native crop through the host full refresh, after 8 partial turns. Frames at before, +40, +250, +470, +560, +640, +720, +820 and +1300 ms: paper darkens to ink, a dark hold with only the AA edge pixels showing, then white returns and the page is clean. |
| `eink-ghosts-vs-cleared.png` | The same page after 8 partial refreshes (left) and after the full refresh (right). The ghost lines of earlier pages sit between the lines of text. |
| `eink-ghost-x4.png` | ×4 nearest, the gap between two lines: the ghost words above, the same gap cleared below. |
| `eink-x3-half-scrub-sequence.png` | The reader's own HALF refresh, at turn 15. The page before is 14 partials of ghosts; the scrub drives the new page in within about 120 ms and the ghosts are gone. |

## 4. Checked, and found clean

- **OFF path.** `writePixelsFromLevels` takes the original loop unchanged. The
  mode argument is read only inside the e-ink branch. The md5 match above
  proves it.
- **The 7:1 floor, on rendered output.** `tests/eink_panel_test.cpp` runs 14
  random partials on both the frozen page and the default page. Worst ink
  against worst paper stays ≥ 7:1. The darkest paper reached is 237 on the
  frozen page.
- **Clearing.** After a HALF, a FULL or a host full refresh, the ghost plane is
  zero and the settled page is exactly `lut[level]`.
- **Transcription.** The waveform tables were checked against the SDK file,
  frame counts included (62 and 25). The affine form was checked against
  frame-by-frame stepping.
- **Sleep.** The sleep screen is a HALF, so it starts a waveform, and the sleep
  loop never presents. `deepSleep`'s settling present calls `endFlash()`, so the
  glass does not freeze mid-inversion.
- **Gestures.** The shake's default is unchanged, and this is pinned. The plist
  was regenerated with `tools/gen_gesture_plist.py`, and `--check` passes.
- **iOS files.** `CrossPointZenRecognizers.mm`, `CrossPointPrefs.mm` and
  `CrossPointIOSShim.cpp` pass a syntax-only compile against the iOS Simulator
  SDK. This is not a full iOS build and not a TestFlight build.

## 5. Found, and not fixed (outside this spike)

**`supportsAbsoluteGrayscale()` probably answers `true` on X3 builds.**
`HalDisplay.cpp` guards it with `#if FREEINK_DEVICE_X3`. That macro is defined in
`src/BoardConfig.h`, and `HalDisplay.cpp` does not include that header. This
spike's first X3 run hit the same trap: its `#if FREEINK_DEVICE_X3` branch
evaluated false, and the log printed `_full` for a HALF request. The e-ink code
now keys on `SIMULATOR_DEVICE_X3` instead.

The fix to that other function was not made, because it was not asked. CLAUDE.md
states that the stub "returns false when the build is X3". Evidence level:
**inferred** from the same preprocessor context. That function's own output was
not measured.

## 6. Left to do

1. **A photograph of the X3 mid-refresh.** It would calibrate three things
   against the real panel: the frame period, the ghost strengths (0.03, 0.015,
   0.92) and τ. This is the 2AFC in the research plan.
2. **The X4's OTP waveforms** (`0xD7`, `0xF7`). They are unknown, and the
   simulator substitutes the X3 `_full` program.
3. **Partial refreshes are not animated.** A real FAST refresh takes about
   400 ms with visible settling. Animating every page turn would change the
   feel of every turn, so it was not included.
4. **The paper tone.** E-ink mode keeps the frozen Sanguine-on-India palette. The
   roadmap's "cool, low-reflectance e-paper white" would be a new paper row, and
   that is a ruling for the owner.
5. **The dark page** (§1.6): nothing, or a model of the inverted panel.
6. **Photosensitivity.** The full refresh is one dark excursion of about 0.5 s.
   It fires only on a host request or a firmware FULL. The periodic HALF on the
   X3 is a scrub and does not flash. So the default cadence adds no flashes.

## RULED 2026-09-25 (owner)

- **E-ink mode is LIGHT PAGE ONLY.** The dark page stays the tube, per the 2026-08-22 doctrine: light is paper and ink, dark is CRT.
- **Shake stays bound to zen.** Full Refresh stays available in Settings to bind to any gesture. The shipped default does not change.
