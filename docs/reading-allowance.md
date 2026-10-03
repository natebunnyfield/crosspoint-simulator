# The zen reading goal (was: the daily reading allowance)

**CURRENT SHAPE, owner 2026-09-24 (second ruling of the day):** *"change this to goal of read 5 minutes a day, no matter the book. it only applies in zen mode and zen mode starting up again restarts it."*

- **RULED 2026-09-25 (owner, asked "per zen session or a daily total?"):** *"Daily, reset by zen start"*. The zen restart wins, so the goal behaves per session, exactly as build 211 shipped it. Nothing is stored across sessions. Do not re-ask.
- **RULED 2026-09-25 (owner):** the dark decay gets the same treatment the light one did. Research how an overdriven tube actually fails, then take five render passes (*"Rework it"*).
- **RULED 2026-09-25 (owner, on the build 212 proof page):** *"yes to all"*. The overdriven-tube dark decay and the smooth-cell light decay are accepted as shipped in build 212.
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
  - A scene that resigns active and never returns (S-041) keeps the clock paused. It fails toward a clean page. **Still left, confirmed 2026-09-25**: `counts()` is false while `appInactive` is set, and only a forward edge clears it.
  - ~~Up to 1 s is counted after a background or sleep return (the step cap).~~ **Fixed 2026-09-25**, below.
  - ~~For one present at a navigation, the decay can land on the wrong screen.~~ **Fixed 2026-09-25**, below.

### The two review leftovers, fixed (2026-09-25)

**The second after a return.** `readingallowance::Session::resume()` makes the
next step's dt count nothing; the stall cap stays for gaps nobody announces.
It is called from `HalDisplay::setBackgrounded` on BOTH edges (iOS can stop
scheduling the process before the background edge arrives, so the foreground
edge is the one that must not miss), and from a `simreset::Registrar`, because
the iOS wake is a longjmp in which the clock's statics survive (the desktop
wake is `execvp`, whose fresh clock already starts at 0).
`tests/reading_allowance_test.cpp` pins it: the gap after `resume()` counts 0,
reading after it counts again, `resume()` is not a restart, it is one step and
not a latch, and an unannounced stall is still capped. Proven by the model
test and by reading the two call paths; no headless run times the gap, because
the clock logs nothing per step.

**The wrong screen for a present.** The cause, read from the firmware: every
screen announces itself BEFORE it paints. `EpubReaderActivity` publishes its
page identity beside the read-aloud capture and then renders
(`EpubReaderActivity.cpp:1702`); every other screen publishes in
`Activity::onEnter` (`Activity.cpp:33`). So at a navigation the live
`sheetIsReaderPage()` names the NEXT screen while `pixelBuf` still holds the
last one, and a present in that window decayed a menu. The pixel writers now
stamp `pixelBufIsBookPage` from that flag under `pixelBufMutex` as they write —
correct precisely because the announcement always lands first — and the decay
(the veil or glow, and the receding letterpress) is drawn only when the
painted page is a book page (`readingallowance::decayOnGlass`). The tick still
counts on the announced screen, which is right for the clock. The reverse
direction changed too: a book page still on the glass after a menu announced
itself keeps its decay until the menu paints, instead of flashing clean.

- Model: `reading_allowance_test.cpp` replays the firmware's order (announce,
  then paint) both ways; the live-flag keying decays the menu, the stamp never
  does.
- Headless (X3, light, zen, 5 min preset to 285 s, 12 round trips book →
  Select Chapter → book): the book decays, the menu is clean, and the
  `[allowance] decay … withheld` line — logged once per occurrence of the
  window — never fired. **The window is rare on the desktop**: it needs a present
  between a screen's announcement and its paint, and the goal only asks for one
  every half second of a decaying minute. So the headless run shows the fix
  costs nothing, not that it catches the case; the model test is the proof of
  the case.
- ON unchanged: the spent page at 4 s is byte-identical before and after
  (`6cc6ffd3…`, both builds). OFF unchanged: the dial at 0 draws nothing
  (md5 gates in `docs/speed-read-rsvp-2026-09-25.md`, same build).

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

## The spent page reaches the glass, and breathes (2026-10-02)

Owner, two asks in one line: *"apply effects like crt and paper ones to more
than just panel. also, ios app to animate them slightly when zen time is up."*

**What was panel-only, read from the code before touching it.** The
2026-08-26 whole-glass pass (`docs/whole-glass-crt.md`) had already moved the
sheet, the scanlines, the grain, the trail and the beam to output space; the
one family still clipped to the page was THIS decay, by its own comment
("the decay is a property of this page and not of the glass"). On the dark
page that clipped two things that are properties of the FACE: the lifted
black level (a raster lifts whole; on the iPad's black surround nothing lit
it at all) and the retrace lines (the flyback crosses the whole tube). The
halation ring also stopped dead at the page's edge.

**Dark, the glass half** (`simallowance::drawDarkGlass`, output space, drawn
where the grain and scanlines are drawn and before them):

- the lift is drawn AROUND the panel (four rects) at the schedule's alpha
  times the breath; the panel keeps its own lift under its blooms, because a
  lift over the blooms would dim the swell the owner accepted on build 212;
- the retrace lines are one plane at the output size / 4, over everything,
  weighted by `(1 - lift)` -- the panel pass used to draw them under the
  lift, which blended them down by exactly that, and the first glass cut
  drew them over it at 2.5x the accepted strength (seen on the desktop X3);
- the halation plane is padded by `kHaloPad` (8 texels at 1/8 = 64 page px
  at 1x) and drawn through `drawPanelPad`, which inflates the dst by the
  same fractions, so the ring crosses the edge.

**Light: nothing new reaches the glass.** The dry plate is a property of the
ink, and the sheet already covers the glass. Recorded rather than invented.

**The breath** (`readingallowance::picture::breath`, pure, tested). Once
`timeIsUp` (fraction 1, held) the picture moves a few percent about the
schedule: two sinusoids at 2.8 s and 0.37 of that rate, normalized, so it
never repeats exactly; lift 5%, halo 10%, defocus 8%, swell 4%; the retrace
family drifts one period per 9 s. Light: the veil's alpha mod runs 1 - 2a..1
(a mod cannot exceed 1 -- the first cut ran 1 +/- a and froze half of every
cycle, three of five desktop frames identical), and the impression breathes
faintly back as an ADDITIVE 0..8% (a factor on `pressLeft` at t = 1 is a
factor on 0). The clock requests a PLAIN present every 160 ms while spent
(`simallowance::breathDue`); plain because the glass does not change under
it, and a dirty present six times a second would feed the trail its own
breathing. Every factor is exactly 1 before the end, so the decaying and
clean pictures are untouched.

**Measured, desktop X3 at 1x, `CROSSPOINT_SIM_AS_SHIPPED=1`, grain seed 7,
frames 700 ms apart, spent dark page:** lift at 10% moved a mean of 11.6
levels between frames (84% of pixels by over 4) -- a pulse, not a breath --
so it was halved: now mean 6.1 / 2.1 / 3.7 / 1.7 between successive frames,
max 30 against frame 0. Spent light page: mean 0.47 / 0.04 / 0.30 / 0.06,
max 11. **Clean pages, both polarities, are byte-identical** to the
pre-change build (md5 `6280f6…` dark, `e5e4c7…` light, old and new binaries).
`reading_allowance` host test: the breath's bounds, that it is still before
the end, the frame-length floor at the 160 ms cadence, the drift's wrap.

**Measured on an iPhone Air simulator (iOS 26.5, dark, zen, preset 300 s):**
presents arrive every ~160 ms (`CROSSPOINT_SIM_LOG_PRESENTS=1`); the band
above the paper reads mean luma 97.5 where it was 0, the left margin 132, the
spent page 207. Successive 1 s screenshots differ by a mean of 1.4 and 0.9
levels (max 20). **On the light page the breath is under one level on the
phone** (mean 0.01, max 1): at t = 1 the veil has removed the ink, and 5% of
nothing is nothing. What should move on paper is an open question for the
owner. Device feel: SHIPPED -- UNCONFIRMED on device.

Two capture traps, recorded so they are not paid again: `xcrun simctl ui
<udid> appearance dark` is NOT seen by a running or freshly launched app on
this simulator -- the trait collection goes on reading light -- until the
simulator is shut down and booted with it set (then `appearance seed:
stored=light system=dark -> SEED`). And in zsh an unquoted `$extra` of env
assignments is ONE word: `env A=1 $extra cmd` sets `A` to the whole string
and the rest never reaches the binary (two full capture sets were identical
to the clean page before this was noticed).

### Ruling on the first render, same day: "only affect the non-black background"

The whole-glass lift had lit the black band above the paper (mean luma 97
where it was 0) and the zen black below it. The owner, from that render:
*"only affect the non-black background."* So the glass half now runs ONLY
where the composed glass is not black:

- `simallowance::refreshBlackMask` reads the glass back once per DIRTY
  present (keyed on the page seq and `glassDirtyGen`, the trail capture's
  own key), and builds an output-size plane: opaque black where no channel
  exceeds `kBlackMax` (4), clear elsewhere. The dark page's ground (23,27,27)
  and every phosphor paper clear it; the phone's bands and the iPad's margins
  are exactly 0.
- `drawDarkGlass` draws as before, then `restoreBlack` paints the plane over
  everything it put there. The breath frames (plain presents) reuse the mask.
- `kHaloPad` is 0 again: the halo is drawn in panel space before the glass
  is read, so a padded ring lit the band and the mask then read it as lit.
  The padding machinery stays, one number, for a surround that is never
  black.

What this means on each device: the iPhone's paper-toned surround out of
zen (the sheet bleeds to the glass) takes the lift and the lines; in zen the
paper ends at the line and the black below it stays black; on the iPad the
surround is black since 2026-09-30 and nothing outside the page moves.

### Second ruling on the render: "blur should not hit edge"

Every blurred layer of the overdriven tube (the HV-sag defocus, the three
fat-beam swells, the halation) is a plane the page's size, and a blur that
runs to the plane's border is cut off there -- the page's edge drew as a
hard line of light against the ground beyond it. `picture::edgeFeather`
multiplies each plane by a ramp, 0 on the border rising to 1 at
`kEdgeFeatherPx` (24 page px at 1x, scaled with the render scale) in, before
upload. Pure, tested (`featherPlane`, `featherPlaneRGB`). Measured on the
desktop X3 at 1x, spent dark page: the outermost 3 px ring fell from mean
145.3 to 125.3 (the lifted ground alone), 30 px in 159.2 -> 158.7, the
centre unchanged at 199.3.

### Third ruling, 2026-10-03: "the panel to not panel should be seamless"

The feather's first cut scaled the DEFOCUS plane's colour to black. That
plane is an opaque blurred picture (alpha 255, BLEND, alpha mod = the
schedule's defocus, 1.0 at t = 1), so the page's outer 24 px were painted
black and then lifted: 123.5 against the margin's ground-then-lifted
132.4 -- a step at the page's edge. `featherPlaneRGB` now fades the plane's
ALPHA and keeps its colour, so the page's own ground shows through at the
border, and that ground is the same tone the margin has (the pad's field is
the panel's paper). Measured on the desktop X3 at 1x: the outer 3 px ring
went 125.3 -> 137.9 against 159.3 at 30 px in; the phone figures are in the
section the build ships with.

## 60 fps, and the ink flickers back -- naturally (2026-10-03)

Owner, asked what should breathe on paper (the first cut's veil mod was
under one level on the phone): *"all effects need to be at 60fps and yes to
ink flicker but make it natural not immediate."*

- **60 fps.** `picture::kBreathFrameMs` is 1000/60; `breathDue` asks for a
  plain present at that cadence while the page is spent. The achieved rate
  is whatever one present costs on the device (measured below); the request
  side no longer caps it.
- **Natural, not immediate.** `picture::breathOnset` is a smoothstep from 0
  at the moment the goal is reached to 1 eight seconds later
  (`kBreathOnsetMs`), and every amplitude -- lift, halo, defocus, swell, the
  veil's depth, the impression, and the retrace drift's RATE -- is scaled by
  it. The first frames past the end are still; the picture begins to move
  over those eight seconds. Pinned: 50 ms past the end nothing has moved by
  more than 0.1%.
- **The ink flickers back.** The veil of step 72 (t = 0.6, where 23% of the
  page's ink is still printed -- measured on the desktop X3 against the
  clean page: 74% at t = 0.5, 49% at 0.6, 4% at 0.7, 0% from 0.8 on, so the
  first cut's step 108 flickered nothing) is baked once per page from the
  same byte planes
  and drawn UNDER the final veil; the final veil's alpha breathes from 1 at
  the crest down to 1 - `kBreathVeilDepth` (0.8) at the trough, times the
  onset. Where it thins, the last ink to dry shows again, in the places it
  was, and goes. Nothing is recomputed per frame: one extra texture per page,
  two draws, one alpha mod.

### Why 60 fps needed a change outside this file (2026-10-03)

The breath asked for a present every 16.7 ms and got one every ~77 ms on the
desktop and ~90 on the phone simulator, with a 2–20 ms compose. The
`[timing]` line now prints the main loop's pass period (`pass`), and it
said why: the firmware's `loop()` sleeps between input polls --
`delayWallClock(10)` at 100 Hz, `HalPowerManager::lightSleep`'s `delay(50)`
once idle -- and in the simulator those sleeps are on the MAIN THREAD, the
only thread SDL may present from. Every self-driving animation (the trail,
the beam, this breath) was capped at the firmware's idle cadence whatever it
asked for. `src/SimulatorIdle.h`: `delay()` on the main thread now pumps
`presentIfNeeded` about once a millisecond while it waits (installed in
`simulator_main` after `setup()`; never on another thread, never nested;
`tests/simulator_idle_test.cpp`). Measured after: desktop X3 at 1x, spent
page, **61 fps dark and 61.6 fps light** (presents counted over 10–15 s);
iPhone Air simulator, dark, **43 fps counted from os_log**, with a 2 ms
compose and a 1.1 ms pass -- os_log drops lines under load, so 43 is a
floor, not the rate. Clean pages byte-identical to the previous build in
both polarities (the pump moves WHEN a present lands, not what it draws).
Device: UNCONFIRMED.

The light flicker after this, desktop X3, frames 700 ms apart past the
onset: mean 0.7–1.6 levels, max 31–69, 4–5% of pixels moving by over 4 --
the last-dried patches coming and going.
