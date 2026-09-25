# The daily reading allowance

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
