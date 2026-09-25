# The reading speedrun — a spike (2026-09-24)

The owner asked: *"spike a speed running demo"*.

Read as a speedrunner's timer laid over reading, in LiveSplit's vocabulary:

- **The run** is your time in this book this session.
- **Each page is a split.** Every split is compared with your best-ever time on that same page, the **gold split**.
- **The HUD** says whether you are ahead of yourself or behind, on this page and in total.

## What exists

- **`src/Speedrun.h`** holds the whole model, pure: splits, gold splits, the run delta and the file format. `tests/speedrun_test.cpp` covers it. The rules:
  - A page read for under **1 s** is a flip-through. It neither counts as a split nor sets a best, so a skim can't set a record nobody can beat.
  - A menu **pauses** the run; it does not end it.
  - A different book starts a new run.
  - A stall is capped at 1 s per pass.
  - Only time that counts as reading is counted: awake, in front, a book page up (`readingallowance::counts`, with zen not required).
- **`src/HalDisplay.cpp`**:
  - The run is stepped on every main-loop pass beside the zen goal's clock.
  - A present is requested only when the HUD's text changes, at most once a second.
  - The HUD is three lines of SDL3's built-in 8×8 debug font, in the page's own ink on a plate of its paper, at the page's top-right corner. It is drawn in output pixels with the overlay, so it sits under the whole-glass passes as the pad does.
- **Switch:** `CROSSPOINT_SIM_SPEEDRUN=1` turns it on, desktop and headless. It is off by default, so every existing capture is unchanged.
- **Bests file:** `CROSSPOINT_SIM_SPEEDRUN_FILE` names it; the default is `speedrun-bests.txt` beside `settings.json`, or in Application Support on iOS. It is plain text, one line per page: `<book key hex> <spine> <page> <seconds>`.

## Verified (headless, X3 at 1x, as shipped)

- **Run 1:** three page turns about 6 s apart set the bests: 5.37, 5.99, 6.01 s.
- **Run 2:** the same state, turning about every 4 s. The HUD read `RUN 00:14 −6.0`, `PG 00:02`, `SPLITS 3 GOLD 3`, and the file now holds 3.33 / 4.00 / 4.00.

## Not done — the next steps if it earns its keep

- **No phone switch yet.** It needs a Settings row and a dial row; the phone can't set an environment variable.
- **The HUD sits over the running head** at the page's top-right. The top margin is the better home.
- **At 1x the debug font is 8 px.** A real HUD should be drawn with the firmware's UI font or Albo.
- **Words per minute:** the read-aloud capture (`readAloudCaptureWanted`) already publishes each page's text, so words per split is one step away.
- **Ideas for a real version:**
  - a chapter-level run with a split table;
  - sum-of-best;
  - pace against a target reading speed;
  - a ghost run: the position you reached last time at this elapsed time, marked in the margin.
