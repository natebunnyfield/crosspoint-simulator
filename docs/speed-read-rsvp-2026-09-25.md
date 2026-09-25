# Speed read (RSVP) — one word at a time, cut from the page itself

Spike, 2026-09-25, surveyed at `acc7ca2`. Owner: *"speedrun was supposed to be
that one word speed read so queue that up too"*. The earlier reading
**speedrun** timer (`src/Speedrun.h`, `docs/speedrun-spike.md`) came from
misreading that word. It stays in place. This is the mode he actually asked for.

**Status: SHIPPED ON A BRANCH, device feel UNCONFIRMED.** Everything below was
verified headlessly on the desktop. None of it has been read on a phone: the
pause tap, the size at arm's length, and whether 300 wpm feels like 300 wpm.
On the device, check that a tap pauses and resumes, that the word sits still
on the marks as it changes, and that the page turns by itself at the last word.

## What it is

RSVP is *rapid serial visual presentation*: the text is shown one word at a
time in one fixed spot, at a set rate. Spritz (2014) is the best-known version.
It places each word so that its **optimal recognition point** (ORP), a letter a
little left of the word's centre, always lands on the same focal mark. The eye
then never makes a saccade.

In this simulator:

- **The words are the page's own pixels.** The read-aloud channel already
  publishes each displayed word's rect (`ReadAloudWordRect`, in logical
  portrait panel pixels). Each RSVP frame is that rect cut out of the landscape
  framebuffer, magnified 2.25× (linear filtering), and placed so its pivot
  letter sits on the focal ticks. So the frame shows the book's own font and
  antialiasing, in the owner's ink on the owner's paper. No font renderer is
  involved, so nothing can disagree with the page.
- **The frame** fills the page rect with its paper color. It draws two rules
  with a notch (Spritz's "redicle") in the ink color, with the focal point at
  38% of the page width and 42% of its height. Below that, a small readout
  shows `300 wpm  12/108` (plus `paused` or `end`).
- **The page turns itself.** After the last word, speed read queues a tap of
  the RIGHT front button (`HalGPIO::queueButtonTap(BTN_RIGHT, 60)`, which
  CLAUDE.md names as page forward). It continues when the new page's capture
  and pixels have arrived.
- **Pause and resume** come from a tap on the glass: the zen deliberate tap, or
  an off-pad tap out of zen. Both go through `SimulatorOverlay::speedReadTakeTap()`,
  which takes the tap only while a word is up. Otherwise the tap goes where it
  always did.

## Controls

| Where | What |
|---|---|
| Settings.app → **Speed Read** | `Speed Read (Experimental)`, a toggle that ships OFF (`speedRead`). `Speed` is a multi-value row: 200/250/300/350/400/500/600/800 wpm, registered default 300 (`speedReadWpm`). |
| Desktop | `CROSSPOINT_SIM_SPEED_READ=1`, `CROSSPOINT_SIM_SPEED_READ_WPM=<100..1000>`, or `speedRead` / `speedReadWpm` in `settings.json` |
| Desktop instrument | `CROSSPOINT_SIM_SPEED_READ_LOG=1` logs one `[speedread] t=… word i/n "…"` line per word, with ` PARA` on paragraph ends |

Both rows use the dial-table pattern: two rows in `src/SimulatorDials.h`, cases
in `applyDialGroup`, getters in `ios/CrossPointPrefs.mm`, and three pins in
`tests/dial_table_test.cpp`. The pins cover the toggle's default, the WPM's
plist default, and the WPM getter's absent-key fallback of 300. The fallback
matters because an absent key read as 0 would mean one word per forever.

## Where each decision lives

| File | Role |
|---|---|
| `src/SpeedRead.h` | Pure and host-tested. It builds the words and their paragraph ends from a capture, sets durations and the ORP, finds the pivot's x from column ink, runs the reader's clock, page turn, pause and step back. |
| `src/SurfaceSpeedRead.h` | Header-only, included by `HalDisplay.cpp` only, main thread only. It reads the channel, waits for the page to be painted, cuts the crop, and draws the frame. It is header-only because a new `.cpp` would leave the generated iOS source list stale. |
| `src/ReadAloudChannel.h` | The fan-out (`peek`, `setPeekerWanted`, `publishedAtMs`). |
| `src/HalDisplay.cpp` | About 50 lines. It stamps `pixelBufWriteMs` on the two pixel writers, adds one `step()` call beside the speedrun's, one `draw()` call after the HUD, the two setters and two `applyDialGroup` cases. |
| `ios/CrossPointIOSShim.cpp` | `pollSpeedRead()`, plus the two tap hooks. |

### The rules

- **ORP.** The table is OpenSpritz's `bestLetter` switch (fetched 2026-09-25,
  quoted below): word length 1 → 1st letter, 2–5 → 2nd, 6–9 → 3rd, 10–13 → 4th,
  longer → 5th. The length counts letters only. Leading punctuation shifts the
  pivot glyph right, and trailing punctuation does not count toward the length.
- **Duration.** The base is 60000 / wpm. A sentence end (`. ! ? …`, looking past
  closing quotes and brackets) multiplies it by 2.0. A clause end (`, ; :` or a
  dash) multiplies it by 1.5. Each letter past 8 adds 0.1, up to +0.8. A
  paragraph end adds +1.5. OpenSpritz simply shows a word twice (×2) if it
  contains `, : - (` or has more than 8 letters. Spritz never published its own
  pauses.
- **Paragraph ends are inferred from the layout**, because the capture carries
  no markers. A word ends a paragraph if it is the last on its line and one of
  these holds:
  - the break was **not forced**: the next word, plus a space, would have
    fitted on this line;
  - the next line is indented;
  - the next line is more than 1.4 line heights below.

  The first cut used "the line stops more than a line height short of the right
  edge". On this ragged-right book that misfired mid-sentence on "pricing" and
  "your", each pausing +300 ms at 300 wpm. It was measured, replaced, and is now
  pinned by a test.
- **The pivot's x** is found in two ways:
  - If the crop's inked columns fall into exactly as many runs as the word has
    glyphs, the pivot is the centre of its run. That is exact.
  - Otherwise touching letters have merged runs. The inked extent is then
    shared out by Adobe Times-Roman AFM advance widths, and the pivot is the
    centre of its share.

  A hyphen-split word (two rects sharing one byte range) is drawn as its two
  fragments side by side. The hyphen the rejoined text lacks is inserted at the
  split, which is estimated from the fragment widths.
- **Clock.** The reader advances at most one word per step, so a stall does not
  flash through the missed words. The next word's clock starts when the
  previous word was **due**, not when the loop noticed. A late main loop
  therefore does not slow the page. A stall longer than a whole word restarts
  the schedule from the current time.
- **Page turn.** A page with no words (a cover or an image) dwells 1.5 s and
  then turns. A turn that gets no answer within 4 s is treated as the end of
  the book, and the readout shows `end`.

## The channel fan-out

CLAUDE.md said *"One consumer per build"*. That is still true for the channel's
**drain**: `consume()` clears `hasNew_`, and exactly one consumer per build
(the iOS read-aloud adapter, or the desktop logger) may call it. A second
drainer would take pages from read-aloud, and read-aloud would go quiet on
every page speed read saw first. That failure is silent.

The fan-out adds three things and changes nothing that existed:

- **`peek(uint32_t &lastSeenGeneration, ReadAloudPage &out)`.** It never
  touches `hasNew_`. It hands the latest page to a caller once per generation,
  and each peeker keeps its own cursor.
- **`setPeekerWanted(bool)`.** This flag is OR'd into `wanted()` and never
  written over the drainer's `setWanted()`. So read-aloud turning itself off
  cannot switch speed read's capture off, and the reverse is also true.
  `drainerWanted()` exposes the drainer's own flag.
- **`publishedAtMs`.** `HalGPIO::publishReadAloudPage` stamps the page with
  `SDL_GetTicks()`. `EpubReaderActivity` captures *before* it paints, and an
  antialiased page is written twice 13–22 ms apart. So speed read takes a
  page's words only once a pixel write newer than the publish has landed and
  the buffer has then been quiet for 60 ms. As fallbacks, a same-text
  re-render is accepted at once (it may write no pixels), and anything is
  accepted after 1.5 s.

A re-render of the same page, with the same text and rects, **keeps the
position**. The firmware re-publishes on every render, not only on a page turn.

**Capture timing:** the phone captures always (`CrossPointReadAloud_perFrame`),
so turning speed read on mid-page shows that page at once. The cursor is reset
on enable, so the page the channel already holds is re-read. On the desktop,
`setSpeedRead(true)` sets the peeker flag, and the env var is applied by the
dial seed in `HalDisplay::begin()`, before the first `loop()`. A desktop toggle
made mid-page through `settings.json` starts at the **next page render**.

Asking the firmware to re-render (`crosspointRequestRender`) was tried and
refused:

- Upstream firmware has no `SimulatorRenderRequest.cpp`. Checked with
  `gh api` against `crosspoint-reader/crosspoint-reader@develop`: 404.
- A weak *reference* does not link on Mach-O. Measured: `Undefined symbols`.
- A weak *definition* here could keep the strong one from being pulled out of
  the iOS static archive, which would silently break the appearance re-render
  that relies on it.

### Proof that read-aloud still works

- `tests/run_all.sh`, full run against a scratch firmware copy: **97 passed, 0
  failed**. That includes `read_aloud_channel`, `read_aloud_core`, the four
  `readaloud_*` tests and `test_read_aloud_capture.sh`. The first run SKIPped
  the three wake tests because no `simulator` (X4) binary existed. They were
  built and re-run, and all three pass.
- A live run with both consumers on
  (`CROSSPOINT_SIM_READALOUD_LOG=1 CROSSPOINT_SIM_SPEED_READ=1`, 800 wpm, speed
  read turning the pages) showed that the drainer and the peeker each saw every
  generation:

  ```
  [READALOUD] page gen=1 ... words=109    [speedread] page gen=1: 108 words
  [READALOUD] page gen=2 ... words=14     [speedread] page gen=2: 14 words
  [READALOUD] page gen=3 ... words=112    [speedread] page gen=3: 111 words
  ```

  The word counts differ by one because read-aloud counts rects and speed read
  counts words: a hyphen-split word is two rects and one word.
- `tests/speed_read_test.cpp` pins these properties: a peek does not steal a
  consume, a consume does not hide a page from a peek, two peekers are
  independent, the flag is OR'd and not overwritten, a clear reaches the
  peeker, and a reboot leaves nothing stale.

## Measurements (desktop, X3 profile, `ai-engineering-from-zero.epub`, dark card)

- **Rate.** At 300 wpm nominal, page 1 (108 words) took 24,698 ms from word 2
  to word 108. The model's own sum for the same 106 words, with their
  punctuation and paragraph flags, is 24,700 ms. The page total therefore
  matches the model to within 2 ms. **The effective rate is 257.5 wpm**, the
  nominal rate less the punctuation and length pauses. The per-word error runs
  from −23 ms (p10) to +40 ms (p90), because on the desktop a present on
  SDL's software renderer costs up to about 100 ms. The schedule-keeping clock
  absorbs it. Before that fix, the same page ran about 15% slow.
- **Page turn.** From the turn request to the new page's first word took
  **132 ms**: the firmware's render, plus the 60 ms settle.
- **Pivot placement, measured on the rendered frame:**
  - At 2x, light: `model.` inked into 6 runs for 6 glyphs, so the exact path
    applied. The `o` spans x 371–430 (centre 400.5), and the focal tick is at
    x 401.
  - At 1x, dark: `pricing` gave 6 runs for 7 glyphs, so the width-share path
    applied. The target `i` spans x 193–208 (centre 200.5), and the tick is at
    x 201.
- **A skipped ORP check.** OpenSpritz shows each word as text in its own font,
  and this mode shows the page's pixels. So no comparison against OpenSpritz's
  pixel placement was attempted.

## Proof figures

All of these are lossless PNG at native pixels, with no scaling. Each is
context and evidence together, because the subject is placement and not fine
structure.

- `docs/speed-read-rsvp-2026-09-25/seq-1x-dark-6-frames.png`: six consecutive
  frames at 1x, 150 wpm ("the / pricing / model. / Keep / the / stable"). Each
  is a 528×255 band cropped from a full 528×792 capture, separated by gray
  4 px gutters. Each word's pivot letter sits under the same tick (x 201).
- `docs/speed-read-rsvp-2026-09-25/frame-2x-light.png`: one frame at 2x
  render and 2x window (`CROSSPOINT_RENDER_SCALE=2`,
  `CROSSPOINT_SIM_WINDOW_SCALE=2`, light), "model.". It is a 700×520 crop of a
  1056×1584 capture.
- `docs/speed-read-rsvp-2026-09-25/ios-sim-iphone-air-zen.png`: the iOS app on
  an iPhone Air simulator, in zen, 200 wpm, "never". It is a 700×520 crop at
  native pixels of the 1260×2736 simulator screenshot.
- `docs/speed-read-rsvp-2026-09-25/frame-2x-dark.png`: the same at 2x in dark,
  "pricing". The CRT passes (scanlines, grain) sit over the frame, because it
  is chrome under the whole-glass passes.

## What was checked and found clean

- **The glass and the phosphor trail.** A word change asks for a **plain**
  present, so it neither re-reads the glass nor deposits into the trail. That
  is the speedrun HUD's lesson from before build 212. Consecutive captures of
  one word are byte-identical: 2 to 7 identical md5s per word in the sequence
  run.
- **The desktop canary is unchanged with the dial off.** This is REASONED from
  the code, not md5-gated against a main build. `setEnabled(false)` is
  the default, `step()` returns false at once, `draw()` is gated on
  `showing()`, and the peeker flag stays false, so capture is not even asked
  for. The one unconditional addition is the `pixelBufWriteMs` store, which is
  an atomic store with no effect on pixels.
- **Portrait rotation.** The crop uses the firmware's own `rotateCoordinates`
  formulas (`GfxRenderer.cpp:236`) for all four orientations, in device space.
  Only Portrait was exercised.
- **The iOS target builds and runs.** It was configured with CMake/Xcode for
  the iphonesimulator SDK from this worktree, and `CrossPointX3` built with
  exit 0. It was then installed on a fresh iPhone Air simulator (iOS 26.5),
  created for this check and deleted afterwards. With `speedRead=YES` and
  `speedReadWpm=200` written through `defaults`, and a book opened through
  `CROSSPOINT_SIM_IMPORT_FILE`, the app logged `[speedread] on` and
  `[speedread] page gen=4: 54 words`. The screenshot shows the frame in zen on
  the frozen Sanguine-on-India page. The `e` of "never" spans roughly x 322–385
  in the crop, and the tick is at x 353. This proves the Settings key, the
  poll, the dial and the draw. It does NOT prove the pause tap, because no
  synthetic tap was sent.

## What is left

- **Device feel: UNCONFIRMED.** That covers the tap, the size (2.25× of the
  reading size), the frame's position (38%/42%), and the readout's size.
- **Step back a word or a sentence** exists in the model and is tested, but no
  gesture or button is bound to it. Ask which gesture before binding one.
- **Swipes and pad buttons still reach the firmware** while words are up. A
  page turn by hand restarts the reader at the new page's first word, and
  Back leaves the book, which hides the frame.
- **The hyphen split point** is estimated from the fragment widths, so the
  pivot can land one glyph off on a split word.
- **Landscape orientations** have not been run.
- **The TXT and XTC readers** publish no capture, so speed read shows nothing
  there and the page stays visible.
- **No reboot reset is registered.** On an iOS longjmp reboot the channel drops
  its page, and the next render's new generation resets the reader. That is
  reasoned, not run.
- **The phone's WPM row** offers 200–800. The dial clamps 100–1000 for the
  desktop.

## Sources

- **OpenSpritz**, `spritz.js`, Rich Jones (Miserlou), 2014.
  github.com/Miserlou/OpenSpritz. **Fetched 2026-09-25.** The ORP switch
  (`case 1: bestLetter = 1; case 2..5: 2; 6..9: 3; 10..13: 4; default: 5`) and
  the delay rule (a word containing `, : - (` or longer than 8, and without a
  `.`, is spliced in twice) are quoted from it.

The following are **from memory and were NOT re-fetched this session.** Verify
them before quoting outside this repo:

- Spritz Inc., "The Science" (spritzinc.com, 2014): the ORP and the fixed
  "redicle" frame.
- O'Regan, J. K. (1981), the convenient/optimal viewing position; Brysbaert, M.
  & Nazir, T. (2005), "Visual constraints in written word recognition:
  evidence from the optimal viewing-position effect", *Journal of Research in
  Reading* 28(3). Words are recognized fastest when fixated slightly left of
  centre, which is the basis of the ORP table.
- Forster, K. I. (1970), *Perception & Psychophysics*; Potter, M. C. (1984):
  the origin of the RSVP paradigm.
- Rayner, K., Schotter, E. R., Masson, M. E. J., Potter, M. C. & Treiman, R.
  (2016), "So much to read, so little time: How do we read, and can speed
  reading help?", *Psychological Science in the Public Interest* 17(1). Its
  review conclusion: RSVP apps trade comprehension for speed, and removing
  regressions (re-reading) is part of the cost.
- Schotter, E. R., Tran, R. & Rayner, K. (2014), "Don't believe what you read
  (only once)", *Psychological Science* 25(6). When regressions are prevented,
  comprehension drops for sentences that need them. That is the reason to bind
  step back.
- Benedetto, S., Carbone, A., Pedrotti, M., Le Fevre, K., Bey, L. A. Y. &
  Baccino, T. (2015), "Rapid serial visual presentation in reading: The case of
  Spritz", *Computers in Human Behavior* 45. It reported comparable literal
  comprehension to normal reading, with more visual fatigue: fewer blinks under
  RSVP.
