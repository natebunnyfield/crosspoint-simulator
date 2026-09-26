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

**Non-X3 builds.** The X4 (SSD1677) runs OTP sequences: `0xD7` for HALF and
`0xF7` for FULL. No file here holds their frames — searched for on 2026-09-25,
§2a below. On those builds the simulator uses the X3 `_full` program for both
requests. This stand-in is **not measured**, and `tests/eink_panel_test.cpp`
pins it so a real X4 transcription has to change it on purpose.

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

## 2a. The X4's waveform: searched for, not found (2026-09-25)

Searched, read-only, at the firmware checkout's `freeink-sdk` and on the web:

| Where | What is there | BW refresh frames? |
|---|---|---|
| `freeink-sdk/.../src/lut/Ssd1677Luts.h` | `lut_grayscale` and `lut_grayscale_sticky` (the X4's 4-level AA waveform, relocated "verbatim from the upstream EInkDisplay monolith"), `lut_factory_quality` (the OEM factory 4-level gray, 50 frames, used only for standalone wallpapers and covers) | **No.** All three are grayscale. The file says the stock X4 has no revert waveform. |
| `.../driver/Ssd1677Driver.cpp` | Sequences only: `0xF7` full, `0xFC` fast, `0xD7` half, loaded from the panel's OTP with a temperature read | **No.** Line ~413: the OEM firmware's only clean primitive in normal use is the **single-pass HALF** (`0xD7`); the multi-flash OTP full (`0xF7`) is "a dead fallback branch there". |
| `.../driver/Uc8179Driver.cpp`, `Uc8279X4Driver.cpp` (the X4 Pro's two controller batches) | External AA grayscale banks; BW refreshes run the OTP (`PSR REG` cleared) | **No.** |
| `.../lut/Uc8279X3Luts.h` | `BW_GC` / `BW_DU` banks, command-prefixed, reverse-engineered from stock X3 firmware | **Yes — but for the X3's newer UC8279d batch, not the X4.** See below. |
| `freeink-sdk/docs/display-driver-references.md` | X4 = SSD1677 + GDEQ0426T82; points at GxEPD2's GDEQ0426T82 driver | GxEPD2 drives it from OTP too. The doc also rules "waveforms are panel-specific. Never copy them" between panels. |
| Web: "GDEQ0426T82 SSD1677 waveform LUT OTP" | Good Display's product page (full refresh 1.5 s, partial 0.42 s); papyrix-reader `docs/ssd1677-driver.md` (LUT *layout* only, "full refresh ~1600 ms"); the SSD1677 datasheet (OTP can hold per-temperature LUTs) | **No bytes anywhere.** The panel's OTP contents are not published. |

So the fallback stays. Two things the search did establish, recorded for the
owner rather than acted on:

- **The X4's periodic HALF is single-pass, not a multi-inversion flash**
  (`Ssd1677Driver.cpp`, the comment above). The simulator currently runs the X3
  `_full` — which inverts — for an X4 HALF, so an X4 build flashes where the
  device probably scrubs. Switching the X4 HALF to the X3 scrub would be closer
  on that evidence, but it is still a borrowed shape, so it is a proposal.
- **Durations.** The documented X4 full refresh is 1.5 s (Good Display) to
  ~1.6–1.7 s (papyrix; the Sticky comment in `Ssd1677Driver.cpp`), against the
  borrowed program's 1.24 s at 20 ms a frame.
- **The X3's own UC8279d batch is ALSO borrowing.** `SIMULATOR_DEVICE_X3` with
  `SIMULATOR_DISPLAY_UC8279` still runs the UC8253 tables, while
  `Uc8279X3Luts.h` holds that batch's real `BW_GC` (clearing) and `BW_DU`
  (partial) banks. Transcribing them is the same job as §1.2 and was not done
  here (outside the X4 ask). Which controller the owner's X3 carries is not
  recorded anywhere this search looked.

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

1. **Calibrate against the real X3.** The procedure and the tool now exist
   (§7); what is left is taking the photographs. The frame period and τ need a
   video (§7.4).
2. **The X4's OTP waveforms** (`0xD7`, `0xF7`). Searched for and not found
   (§2a); the simulator still substitutes the X3 `_full` program.
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

## 7. Calibrating the ghost against a real X3 (procedure, 2026-09-25)

The three ghost constants in `src/EinkPanel.h` — `residueToWhite()` 0.030,
`kResidueToBlack` 0.015, `kKeep` 0.92 — are tuned. This is how to replace them
with numbers read off the owner's own panel. Tool: `tools/eink_calibrate.py`
(its `--selftest` runs in `tests/run_all.sh`: a synthetic panel with known
residues, exposure drift, noise and a 1 px misregistration, all three recovered).

### 7.1 Setup

- The X3 on a table, the phone on a tripod or propped **square to the glass**,
  so the page fills the frame. Do not move either between shots.
- **Lock exposure and focus** (long-press in the Camera app until
  *AE/AF LOCK*), flash off, room light steady, no window light moving across
  the page. The tool normalizes each photo to its own paper and ink, which
  absorbs a small drift, not a cloud passing.
- Stock reading settings, the reader's refresh frequency at its default (15):
  the HALF every 15 pages is what clears the ghost, so count page turns.
- Three pages **A, B, C** with plenty of text and different line breaks — three
  consecutive pages of prose do. The ghost is measured where A had ink and B
  has paper, so they must not line up.

### 7.2 Shots (one set measures all three constants)

1. Go to page A and force a clean refresh (the reader's own HALF: turn to a
   page just after one, or sleep and wake). Photograph: **`prev.jpg`**.
2. Turn forward once to B. That is ONE partial. Photograph immediately:
   **`ghosted.jpg`**.
3. Turn forward to C and back to B, `M` times (each round trip is two
   partials, so `M` = 2 × round trips; 4 is a good number). Stop on B.
   Photograph: **`later.jpg`**. Do not cross a HALF while doing this — keep the
   count below the refresh frequency.
4. On B, force a clean refresh (sleep and wake). Photograph: **`clean.jpg`**.
5. Go to C, clean refresh, photograph: **`third.jpg`** (it keeps pixels C
   re-inked out of the keep measurement).

### 7.3 Run it

```bash
tools/eink_calibrate.py prev.jpg clean.jpg ghosted.jpg \
    --later later.jpg --later-partials 4 --third third.jpg \
    [--crop x,y,w,h]     # the text block only, same box for every photo
```

It prints each residue as a fraction of the full ink-to-paper swing and in
levels, and the three lines to paste into `src/EinkPanel.h`. Read before
pasting:

- **Fractions are in the photo's encoded (gamma) space**, which is also the
  space the model's levels live in (0–255 code values through the palette
  LUT), so they transfer directly. Shoot every frame in the same format;
  mixing RAW and JPEG breaks that.
- **A negative residue** means the "ghosted" photo is cleaner than the clean
  one: the photos are out of order or the exposure moved.
- **Masks are eroded 2 px.** At a photo of roughly 4× the panel's pixels a
  stroke is ~8 px wide, so this is safe; a far-away photo (strokes under 5 px)
  fails with "only N pixels", which is the tool refusing rather than guessing.
- **The 7:1 cap still wins.** A measured residue larger than the palette's cap
  (18 levels on the frozen page) is drawn at the cap; the cap is a legibility
  rule, not a physics claim, and a measurement does not lift it.
- After pasting, re-run `tests/run_all.sh -k eink` — the floor test runs 14
  partials on both palettes against the new constants.

### 7.4 What photographs cannot measure: the frame period and τ

`kFramePeriodMs` (20, assumed) and `kTauFrames` (4, assumed) need time, so they
need **video**: iPhone slow-motion (240 fps) of the X3 through one HALF (the
scrub, 25 frames) and one host-requested FULL (62 frames), same tripod.

- **Frame period**: count video frames from the first visible change to the
  last, divide by the bank's frame count (25 or 62). A full that takes 1.24 s is
  20 ms a frame; 1.5 s would be 24 ms.
- **τ**: on the FULL, pick a paper pixel region and plot its brightness through
  the first segment (24 frames driving black). The fall to 1/e of the swing,
  in panel frames, is τ. Set `kTauFrames`.

No tool for the video yet: a per-frame mean over a crop (`ffmpeg -vf crop,...`
into PNGs, then a mean per frame) is all it needs, and it should be written
when there is a video to test it on.
