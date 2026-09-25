# The zen reading goal (was: the daily reading allowance)

**CURRENT SHAPE, owner 2026-09-24 (second ruling of the day):** *"change this to goal of read 5 minutes a day, no matter the book. it only applies in zen mode and zen mode starting up again restarts it."*

- **RULED 2026-09-25 (owner, asked "per zen session or a daily total?"):** *"Daily, reset by zen start"*. The zen restart wins, so the goal behaves per session, exactly as build 211 shipped it. Nothing is stored across sessions. Do not re-ask.
- **RULED 2026-09-25 (owner):** the dark decay gets the same treatment the light one did. Research how an overdriven tube actually fails, then take five render passes (*"Rework it"*).
- **One clock, whatever the book.** There is no per-book or per-day record any more; the ledger file (`reading-allowance.txt`) is no longer read or written. An old one left on a device is inert.
- **Counted only in zen**, with a book page on the glass. The device must be awake and the app active.
- **Zen starting restarts it.** Every off→on edge of zen restarts the clock, and so does a launch into zen. Leaving zen stops the count and shows the page clean at once.
- **5 minutes, the last one decaying.** The Settings row is **Zen Reading Goal › Minutes**: Off, 5, 10, 15, 20, 30, 45 or 60, default **5**. The pictures are unchanged: on the light page the ink runs dry (G); on the dark page the tube overdrives (I).
- **Where zen comes from.**
  - The iOS harness publishes its live `g_zen` every frame (`pollReadingAllowance` → `SimulatorOverlay::setZenActive`). That catches all three of its writers: the launch seed, Settings, and the hold gesture.
  - The desktop has no zen of its own and takes `CROSSPOINT_SIM_ZEN`.
- **Model:** `readingallowance::Session`, where `step(zen, reading, dt)` returns true on a restart. `counts(zen, …)` is false outside zen. Both are pinned in `tests/reading_allowance_test.cpp`.
- **QA hatch:** `CROSSPOINT_SIM_READING_ALLOWANCE_USED=<s>` now seeds every zen start.
- **Verified headless** (X3 at 1x, as shipped, light page, preset 285 s of 5 min):
  - With `CROSSPOINT_SIM_ZEN=1` the page decays.
  - Without it, the frame is **byte-identical** to the un-preset page (md5 `87a81473…` both arms).

## The dark decay, v2: the overdriven tube (2026-09-25 — five passes)

The owner ruled: *"Rework it"*, the way the light decay was reworked.

### The research

- **Blooming.** Beam current rises with brightness, and a high-current beam is a wider, harder-to-focus spot (repairfaq.org TV FAQ, "blooming or breathing").
- **Breathing.** The anode voltage sags under load: the beam loses stiffness and focus, and the raster expands on bright content.
- **Brightness past cutoff.** The black level lifts to grey and the retrace lines show.
- **Phosphor saturation.** Highlights clip toward white.
- **Faceplate halation.** Light scattered inside the glass returns as a ring around bright areas.
- **An overloaded video amplifier** smears bright content along the scan line.

### The model

`picture::darkSchedule` in `src/ReadingAllowance.h` says how much of each failure is on at t. Its ordering is pinned by the test:

- nothing at t = 0;
- every failure only grows;
- the fat beam comes before the defocus.

`simallowance::drawDark` builds, once per page:

- **Fat beam:** the strokes' coverage at ½ resolution, at three dilation radii (0 / 1 / 2 half-px × scale), each softened. The two heavier levels carry a one-sided video-amp trail along the presented scan line.
- **Halation:** a ring (wide blur − 0.7 × narrow) at ⅛ resolution.
- **HV-sag defocus:** the v1 layer.
- **Retrace lines:** twelve faint diagonals.

Per step only alphas and a color mod move. The swell layers are baked white and tinted from the phosphor toward white by `0.15 + 0.55t`.

### The passes

1. **The first schedule was far too early.** The page was swollen past reading at 4:22, and the retrace lines were loud and thick.
2. **The swell spread over the minute,** smaller radii, retrace a late faint ghost (0.45 max, after t = 0.5). The frames now read: glow, then halation and lift, then thickening, then heavy, then blobs, then unreadable.
3. **Video-amp smear.** A diff against pass 2 shows it lands on the right edges of strokes, the scan direction.
4. **Checked at the phone's 2x:** the radii scale correctly and the look matches 1x. The present costs 75–90 ms, most of it the existing phosphor trail accumulator.
5. **Phosphor saturation grows with the overdrive.** It was a fixed 45%, so the first swell was already bleached.

## Pass 6 and the pre-ship review (2026-09-24)

**The owner:** *"take a pass at improving the jagged pixelated look of light ink effect."*

The cause was the print/no-print decision:
- It was made pixel by pixel against white-noise hashes: the split field had a 20% per-pixel hash, and the tooth lane was a raw per-pixel hash.
- The threshold was hard (slope 28).
- The result was single-pixel salt with stair-stepped edges.

The fix:
- **The split field** is two octaves of smooth value noise (2.2 and 1.1 device px).
- **The tooth the plate feels** is the `'TOOT'` lane smoothed to 1.3 device px (`smoothToothAt`).
- **The threshold is slope 5**, with no offset term. The blob's range is 0.06–0.80, so t → 0 stays exactly clean and t → 1 exactly empty.
- **Where ink prints, it prints solid,** with edges about half a pixel wide. Judged at the phone's 2x (`CROSSPOINT_RENDER_SCALE=2` build, `CROSSPOINT_SIM_WINDOW_SCALE=2` capture): the strokes break into soft-edged ink cells.

The pre-ship adversarial review found no ship-blockers. Its should-fixes:

- **Memory and CPU at 2x.** The first version kept 32-byte samples, 53 MB of them, and evaluated noise on every pixel. Now:
  - it keeps four byte planes (mask, robbed, contact, blob), 4 bytes a pixel;
  - it evaluates noise only near ink;
  - the per-step pass skips bare paper and computes `pow` once per step;
  - the float scratch is freed after each page, and the page copy is freed when the decay ends.
  - `printedRaw` / `robbedOf` / `contactOf` in the model.
- **Zen was published a frame late** from Settings. `setZenActive` is now called right after `pollZenMode`.
- **Nits fixed:** the render target restores the draw color, the glows rebuild on a size change, and the dead branch is gone.
- **Left as is, and recorded:**
  - A scene that resigns active and never returns (S-041) keeps the clock paused. It fails toward a clean page.
  - Up to 1 s is counted after a background or sleep return (the step cap).
  - For one present at a navigation, the decay can land on the wrong screen.

## The light decay, v2: viscous, incidental, physical (2026-09-24, fourth ruling — five passes)

The owner: *"incorporate more physical ink and paper and plate simulation. it shouldn't be this faint, it should be incidental and viscous. research how and take five passes at getting this right."*

### The research

What a starved letterpress sheet actually shows:

- **Salty print.** Coverage follows the Walker–Fetsko transfer model: covered fraction = 1 − e^(−kx) in the film thickness x, with k scaled by the paper's contact. A thin film misses the sheet's valleys and leaves white pinholes in the solids.
- **Ink is a stiff paste.** It prints at full body or not at all. Too viscous an ink causes skip-out and mottle (luminite.com's defect catalog).
- **Light print ghosts.** The form rollers are robbed by elements just ahead of them, so a line under a heavy line starves (the-print-guide.blogspot.com, "Ghosting"; briarpress.org/31453).
- **Roller bands.** The rollers' own circumference leaves bands.
- **Film splitting.** Ink splits into filaments and cells, not white noise (the filament-separation literature on ink transfer).
- **Edge pressure.** The sheet wraps the type's shoulder, so a stroke's edge bites harder than its middle.

### The model

`picture::PressSample` / `printedFraction` / `blobAt` / `pressLeft`, in `src/ReadingAllowance.h`. Per pixel:

- **Film supply:** `(1−t)^1.25 · (1 − t·(0.55 band + 0.60 depletion + 0.60 skip))`.
  - The **depletion** is the mean ink the roller met in the 28 device px before this row, along its travel (page-down, which is +x on the landscape framebuffer).
  - The **band** is the roller's circumference, about 0.37 page height per turn.
  - The **skip** is word-sized patches (`'SKIP'`, 40 device px cells).
- **Contact:** `0.40 tooth + 0.15 formation + 0.25 plate + 0.20 edge`, using the letterpress lanes `'TOOT' 'FORM' 'PLTE'` off the page's sheet seed.
- **Coverage:** Walker–Fetsko with k = 4·(0.35 + contact), normalized to the full film so t = 0 is exactly clean.
- **Printing:** a sharp print/no-print decision (slope 28) against a clustered split field (`'VISC'` cells 2.2 device px, 80% coherent, 20% fine). What prints keeps at least 90% of its body.
- **The impression holds** (`pressLeft = 1 − t³`): a starved plate still bites. It goes only at the close.

### The five passes

1. **Transfer at k = 14** held the page clean until 4:50, then it vanished. That was the "cut, not a minute" failure again.
2. **k = 4, normalized:** the right kind of dark, salty, viscous break-up, but uniform across the page.
3. **Incidental terms roughly doubled, plus skip-out patches and supply ^1.25:** lines and words now starve unevenly. Late fragments went pale grey.
4. **The print decision sharpened (slope 12 → 28, body ≥ 0.9):** fragments stay dark and dwindle in number. Letters hold their outlines with salty middles.
5. **Split cells 1.5 → 2.2 px, 65/35 → 80/20 coherent:** the salt reads as cells and threads, not pixel noise.

`tests/reading_allowance_test.cpp` pins:

- clean at t = 0 and gone at t = 1;
- ink only ever leaves;
- a stroke's edge holds longer than its middle;
- every incidental term starves earlier, never later;
- the impression holds until late;
- the split field belongs to the sheet.

The v1 functions (`kissAt`, `starvedRetained`, the private tooth) are retired.

## The light decay, redone on the page's own simulation (2026-09-24, third ruling) — SUPERSEDED by v2 above

The owner: *"redo the decay in light mode to take full advantage of the letterpress and ink and paper simulation, it seems lacking currently."*

The first light decay starved the ink against a private noise field. The break-up therefore had nothing to do with the paper the page is drawn on or the plate that printed it. The model is now `picture::kissAt` / `starvedRetained` / `pressLeft` in `src/ReadingAllowance.h`, and it reads the letterpress model's own lanes, seeded by the page's sheet identity (`pageSheetSeed()`):

- **The paper's tooth** (`'TOOT'`, per panel pixel, weight 0.60): a starved plate kisses the high spots first.
- **The sheet's formation** (`'FORM'`, 3 cells, 0.15): the cloudy, thicker regions of the sheet print longer.
- **The plate pressure** (`'PLTE'`, 4 cells, 0.25): ink survives longest where the press bears down heaviest.
- **The stroke's interior** (the page's ink box-blurred one device pixel): edges go before cores.
- **The film thins by 40%** over the minute, in the ink's own hue.
- **The impression recedes.** The letterpress field is re-composited at `pressLeft(t) = (1-t)^1.5` through a render target, so the squeeze rim and the deboss go with the ink (`simallowance::drawFadedField`).

The measurements that shaped it (`CROSSPOINT_SIM_ZEN=1`, 5 min, X3 1x, as shipped):

1. **The veil left a ghost.** Weighting the veil by the pixel's own ink fraction left `ink*(1-ink)` of every antialiased edge pixel, and the spent page read p5 214 against paper 241. The veil now removes `1 - retained` of whatever is there, masked to the ink plus one device pixel. Spent: p5 223, paper 241, blank.
2. **The first ramp read as a cut.** It had slope 5 and a threshold running −0.3→1.3: nearly clean at 4:24, blank by 4:50. It is now slope 2.5, −0.4→1.4.
3. **The 55% film fade swallowed the break-up.** The surviving ink went uniformly faint. It is now 40%, so the fragments stay dark.

The frames: 4:12 and 4:22 are slightly thinned. At 4:30 the ink is paler. At 4:38 the strokes are speckled by the tooth, with their cores holding. At 4:46 the text is a broken ghost, and at 5:00 it is blank. `tests/reading_allowance_test.cpp` pins all of these:

- clean at t=0 and gone at t=1;
- ink only ever leaves;
- a stroke's edge goes before its interior;
- the impression recedes to nothing;
- the break-up belongs to the page's sheet seed.

The dark decay is unchanged.

Everything below is the record of the first shape (per book, per day, 10 minutes, persisted). The pictures, the review findings and the measurements still apply; the counting rules do not.

---

# (history) The daily reading allowance

A book that can only be read for so long a day. The owner designed it on
2026-09-24, one question at a time:

1. *"I think I want a timer on the book that makes it harder and harder to read
   as time passes, ultimately making it unreadable at the end."*
2. The clock is **per book, reading time** (picked from options).
3. *"10 minutes every day."*
4. *"emulate the ink being pressed down poorly, too much and not enough, and
   too much and not enough emission for the dark"*. That produced six more
   mock-ups (F–K) beside the first five (A–E):
   https://claude.ai/artifact/WbZSuzqzTrLhW4mcBmyaBq
5. *"make 10 minutes an ios app setting. starting at last minute, do too much
   emission for dark and for light, do too light of ink"*. That picks
   **G** (pressed too lightly) for the light page and **I** (too much
   emission) for the dark page.

## What it does

| | |
|---|---|
| Counted | Only while a BOOK PAGE is on the glass: `sheetIsReaderPage()`. The clock stops when the device is asleep, when the sleep screen is up, or when the app is in the background. |
| Keyed by | The reader's `bookKey` (`readerPageIdentity`), per local calendar day (YYYYMMDD). It refills at local midnight. |
| Decay | None until one minute of the allowance remains. Over that minute the fraction runs 0 → 1, and the page stays spent until midnight. An allowance of a minute or less decays over the whole allowance. |
| Light page | "Pressed too lightly". A paper-colored veil covers the page. Its alpha is the ink LOST at each pixel, from a fixed tooth field. |
| Dark page | "Too much emission". The glyphs swell (a tight glow that peaks mid-minute). Then the whole picture defocuses, the ground lifts toward the phosphor, and two wide halations wash it out. |
| Setting | iOS Settings.app has a **Daily Reading › Minutes per Book** row: Off, 5, 10, 15, 20, 30, 45 or 60; ships **10**. The desktop uses `CROSSPOINT_SIM_READING_ALLOWANCE` / `readingAllowanceMinutes` in settings.json, and ships **0 (Off)**. |
| Record | `reading-allowance.txt` sits beside `settings.json` on the desktop, and in `Application Support/CrossPointReading/` on iOS. It is plain text (`day N`, then `<hex book key> <seconds>`), so deleting a line gives that book its minutes back. It is saved every 5 counted seconds and whenever counting stops. Writes go to a temporary file and then replace the record, so a kill mid-write cannot leave half a record. |

## Where it lives

- `src/ReadingAllowance.h` is the pure model: the window, the ledger and its file format, the stall cap, the "is this reading" predicate and the quantizer. `tests/reading_allowance_test.cpp` covers it.
- `src/SurfaceAllowance.h` is the clock, the persistence and both pictures. It is header-only for the reason `ReadingLog.h` is: `cmake/CrossPointSources.cmake` is generated.
- `src/HalDisplay.cpp` runs the clock tick on EVERY `presentIfNeeded` pass, before the pending-present test, because an e-ink firmware presents once per page and the minute has to run while the reader sits on one. A quantized step (120 over the minute) raises a present. The decay is drawn right after the letterpress, inside the beam clip, over the panel only, with the page's own rotation.
- `src/SimulatorDials.h` holds the row `ReadingAllowanceMinutes`. `tests/dial_table_test.cpp` pins its shipped 10 against both the `Root.plist` default and the getter's absent-key fallback.
- On iOS: `CrossPointPrefs_readingAllowanceMinutes` (absence reads as 10, not Off) and `pollReadingAllowance` in `CrossPointIOSShim.cpp`.

## Decisions a reviewer should know

- **The desktop ships Off, on purpose.** A headless capture run against the same book all day would otherwise accumulate nine minutes and start decaying its own screenshots. Every md5 gate would then drift, with nothing to say why. With the dial at 0 no file is read or written and nothing is drawn.
- **A stall is capped at one second.** iOS does not always deliver the background edge before it stops scheduling the process, and the sleep loop never calls `presentIfNeeded`. The first pass after either one therefore sees a long gap. That gap was not reading, so it counts for at most one second.
- **The light veil's ink is dilated by 2 device pixels.** The first render weighted the veil by each pixel's own ink. That left the letterpress rim and deboss shadow, which sit just OUTSIDE the stroke, printing a ghost of every letter on a spent page: measured p5 214 against paper 241, and the text was still legible at 10:00. The dilation fixed it: p5 223, paper 241, and the render at 10:00 is blank.
- **The dark swell peaks mid-minute and then gives way.** It is built from the sharp page. Held at full strength to the end, it reprinted crisp letter shapes over the defocus, and the spent page still read (second render). The defocus — "the spot grows" — is what makes the end unreadable.
- **The QA hatch never writes the owner's file.** `CROSSPOINT_SIM_READING_ALLOWANCE_USED=<seconds>` starts every book opened in that run at least that far in, and suppresses saving. `CROSSPOINT_SIM_READING_ALLOWANCE_FILE` overrides the path.

## Measured (2026-09-24, desktop X3 at 1x, `CROSSPOINT_SIM_AS_SHIPPED=1`)

Text band of the resumed book: 5th / 95th percentile luminance at each used second.

| used s | light p5 / p95 | dark p5 / p95 |
|---|---|---|
| 0 | 61 / 241 | 29 / 213 |
| 548 | 77 / 241 | 33 / 233 |
| 562 | 101 / 241 | 53 / 236 |
| 575 | 212 / 241 | 87 / 234 |
| 588 | 223 / 241 | 134 / 232 |
| 600 | 223 / 241 (blank) | 178 / 225 (washed out) |

Each capture is taken about 2.3 s after the book opens, so a `used` value of N renders roughly N+2 s.

## Adversarial review, 2026-09-24

It found no correctness bug. Four findings, three fixed before commit:

1. **The veil rebuild ran under `pixelBufMutex`** — the reviewer measured 19.5 ms for the dilation alone at 2x — and it ran on every step. Fixed: the page is copied under the lock once per page and worked on outside it, and the dilation is cached per page. Only the alpha pass runs per step.
2. **The "untouched" page jumped when the minute began.** 4.6% of ink pixels lost up to 59% of their ink at t = 0. Fixed: the threshold now starts below the lowest tooth. `reading_allowance_test` fails the old curve.
3. **Decay steps did not mark the glass dirty,** so a page turn swept in over the page as it looked at its first present. Fixed: `requestDirtyPresent()`.
4. **For one present, the veil or glow could be built from the NEXT page.** Mostly closed by the copy in fix 1. What is left is at most one frame of a mismatch on a page turn.

It checked and found clean:

- **What counts as reading.** Menus, the sleep screen, the sleep loop and the background are all excluded, and coming back from a menu re-publishes the page. The reviewer flagged one edge: foreground-inactive time counted. It was closed the same day (see below).
- **Dial at 0.** Nothing is drawn, written or presented.
- **Threading.**
- **The iOS longjmp reboot.** The renderer and the static textures survive it.
- **Texture state.**
- **Decay math and presents.** The decay only increases, presents stop at step 120, midnight refills, and a polarity switch rebuilds the glows.
- **iOS absent vs Off.**
- **Privacy.** The record holds book-path hashes and seconds, in Application Support, which file transfer cannot reach.

## Foreground-inactive time does not count (2026-09-24, after the owner's note)

The owner, on the review's edge: *"notification banners should not be possible in app"*.

- The clock now also stops while the scene is foreground-INACTIVE. The shim sets `SimulatorOverlay::setAppInactive(true)` at `SDL_EVENT_WILL_ENTER_BACKGROUND` (resign-active). Either forward edge clears it, the same edges that resume presents.
- So whatever resigns active cannot run the clock: Control Center or Notification Center pulled down, an incoming call, or a banner if one ever did.
- Presents still run while inactive, as S-041 requires. Only the clock pauses.
- Not measured on a device: which of those actually resigns active on current iOS.

## Not measured

- **The cost at the phone's 2x, after the fix.** Each page now costs one dilation plus one glow build. Each step costs one alpha pass over 1584×1056 and one texture upload, neither under the lock. No one has timed this on the device.
- **Device feel.** SHIPPED — UNCONFIRMED on device.
