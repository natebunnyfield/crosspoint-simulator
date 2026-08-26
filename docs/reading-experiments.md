# Reading experiments — the ledger, the outcomes, and how long it would take

2026-08-25. Owner's ask, verbatim:

> *"Usage tracking into the iOS app that tracks which font, color, and other
> settings I used the most and got the most reading done with and got the least
> reading done with. We wanna be able to empirically base what actually worked
> for me, period. We can even do this as randomized session variables, so that I
> don't have to pick what works. It's derived, and there's a range that works,
> and we can figure out which one, given enough data, works the best."*

**Read §6 before §2.** §6 is the honest arithmetic on how much reading it takes
before this can distinguish anything, and it changes what the tool is for. The
short version: a 10% difference is reachable in a few weeks of ordinary reading;
the 2–4% that separates two well-set faces is out of reach on any timescale that
matters. That is not a reason not to build it — it is a reason to know which
question you are asking it.

**Phase 1 is built and shipped in this commit. Phase 2 is designed, tested, and
deliberately not wired.**

---

## 0. Standing rulings — read before proposing a change here

**Phase 1 only. The randomizer stays wired to nothing.** Owner, 2026-08-25,
asked directly whether to wire it now so the same weeks would produce causal
rather than observational data: *"Phase 1 only — observe first."* Nothing about
his reading changes; the ledger records what he already does. **Do not wire
Phase 2, and do not add its Settings row, without a new ruling.**

The argument that was made FOR wiring it, so it is not re-made from scratch:
observational logs cannot establish cause, because settings are chosen for
reasons tangled with mood, book and time of day, so any correlation found in
them is uninterpretable. That is true and it was heard. What it buys instead is
the **within-book variability** — the single number the whole power estimate
rests on (§6 assumes a cv of 0.15 and says plainly that it is a guess). Measured
first, it says whether any experiment here can resolve anything at all before
the reading experience is disturbed to run one. If the variability comes back
high, no arm was ever going to resolve, and that is learned for free.

It is also reversible in the useful direction: the lines written now stay valid
as baseline when the randomizer is switched on later.

**Colour cannot be an arm.** Same day, same reasoning: `src/FrozenPage.h` holds
both appearances frozen (2026-08-24) and lifting that freeze is a separate
ruling. Asked whether to lift it for a trial, the answer was *"Not yet — measure
your variability first."* `ink` and `paper` are recorded in every `cfg` line
regardless, so the day it lifts, every line already written says which side of
the change it was on.

## 1. What is built

| | Phase 1 — instrumentation | Phase 2 — the randomizer |
|---|---|---|
| Status | **shipped** | designed, host-tested, **not called by anything** |
| Changes what the reader sees | no | yes — that is the point |
| Needs an owner decision first | no | yes, two of them (§7) |
| Files | `src/ReadingLog.h`, `src/ReadingChannel.h`, firmware `lib/hal/HalGPIO.h` + `src/activities/reader/PageTextMetrics.h`, `tools/reading_report.py` | `src/ReadingArm.h` |
| Tests | `tests/reading_log_test.cpp`, `tests/reading_report_test.py`, firmware `test/page_text_metrics` | `tests/reading_arm_test.cpp` |

Phase 1 is useful on its own and costs nothing in reading experience. It also
does the thing that decides whether Phase 2 is worth switching on at all:
**it measures the variance**, which is the number every power estimate in §6 is
currently guessing at.

---

## 2. The channel, and why it is a new one

The firmware already tells this repo which page is on glass —
`HalGPIO::publishReaderPageIdentity(bookKey, spineIndex, pageInSpine)`, called
once per displayed page from `EpubReaderActivity::renderContents`, which *is* the
commitment that this page is the one being shown. That channel exists to seed
the paper, and it was tempting to hang the ledger off it.

It is a separate channel, `publishReadingPage(const ReadingPageSample&)`, for
three reasons that are not stylistic:

1. **Different lifetime.** The identity is a latch consumed on the *present*
   path and superseded rather than cleared. The ledger is an append: every call
   must produce a record, and a superseded one is a lost page.
2. **Different payload.** The ledger needs the typography — family, size,
   spacing, grid, justify threshold, ligatures, line-break mode, margin — which
   the paper has no business knowing.
3. **Different cost profile.** The identity is three integers. The ledger walks
   the laid-out page to count its text (§3), which is cheap but not free, and
   that walk is compiled out on device (`#ifndef SIMULATOR`).

Same host-capability split as the read-aloud and keyboard channels: an inline
no-op in the firmware's `lib/hal/HalGPIO.h`, a real sink here. The POD is
mirrored in `src/ReadingChannel.h` under the shared
`CROSSPOINT_READING_PAGE_SAMPLE` guard, exactly as `readerBookKey()` is, and
`tests/reading_log_test.cpp` reads the firmware's declaration **as text** and
fails on a reordered or retyped field — the two cannot share a header, and such
a divergence would compile cleanly on both sides and simply write wrong numbers.

Three more boundaries need no firmware change at all, because all three already
reach this repo:

| Boundary | Seam |
|---|---|
| launch | `simulator_main.cpp`, right after `CrossPointHarness_prepareFilesystem()` and before `setup()` |
| left the reader | `HalGPIO::publishScreenIdentity` — called on entry to every non-reader screen |
| went to sleep | `HalGPIO::startDeepSleep`, before the terminal loop |

The sleep line has to be written *before* the loop, not after: `startDeepSleep`
never returns.

---

## 3. The denominator, which is the crux

"Got the most reading done" needs a unit, and **pages per minute is the wrong
one the moment font size is a variable**. A larger face puts less text on a
page, so it turns more pages per minute while reading the same book at the same
speed. Pages/minute would find a large, confident, entirely spurious effect of
font size, in the direction of "bigger is better".

So each page line carries how much text was on it. The count happens in
`src/activities/reader/PageTextMetrics.h` (firmware, pure, host-tested), one walk
of the already-laid-out `Page::elements` — no measurement, no allocation, no
string building. That is the same walk `captureReadAloudPage` does, minus its
expensive half, and it is skipped entirely on device.

**Characters, not words.** A word the line breaker *splits* across two lines is
two tokens, and which breaker runs (`SETTINGS.hyphenationEnabled`, the Line
Breaks row) is itself one of the things being compared. A word count is
therefore biased in a direction that lines up exactly with a treatment arm — the
worst possible shape for a confound, because it would look like an effect. A
character count has no such bias: a split word contributes the same characters
either way, provided the soft hyphens the splitter inserts are excluded, which
they are. Codepoints rather than bytes, so a page of accented text is not scored
as 1.2 pages of English.

The word count is published anyway, because it is free and because it is what a
human reads a report in. The report's rates are per character and the word
column is labelled approximate.

**Read-aloud capture was considered and rejected as the source.** It would give
exact spoken words, but it measures every token's rendered advance and builds
the full text plus a rect per word — it is the expensive path, and turning it on
to count words would be paying a page-render's worth of work per page for a
number a subtraction can approximate.

**TXT and XTC publish 0/0/0** — those readers have no laid-out `Page` to walk.
The report reads that as "no denominator" and excludes those pages from every
rate rather than treating them as empty pages, which would drive any rate that
touched them toward zero.

---

## 4. The schema

An append-only JSONL file. Three line kinds. Unknown keys must be tolerated by
every reader, so a field can be added without a version bump; `v` bumps only
when a line's *meaning* changes.

### `cfg` — the settings in force

Written when they change, and once after every launch (so a reader starting at a
launch boundary can always resolve the `cfg` a page names).

```json
{"t":"cfg","ts":1787681603,"ms":2193,"id":2167091952,"fam":"Caledonia","pt":15,
 "slot":1,"ls":1,"grid":0,"jt":40,"lig":1,"ligoff":"","lb":0,"marg":5,
 "dev":"X3","scale":2,"pw":792,"ph":528,"dark":0,"ink":"5C332B","paper":"F9F3E9",
 "exp":"","arm":"","armseed":0}
```

| key | meaning |
|---|---|
| `id` | FNV-1a over every field below that changes what the page looks like. Never 0. |
| `fam` `pt` `slot` | reading font family (SD card name, `""` = built-in), resolved point size, S/M/L/XL slot |
| `ls` `grid` `jt` `lig` `ligoff` `lb` `marg` | line spacing, line grid, justify threshold, ligature master switch, per-pair spec, line-break mode, screen margin |
| `dev` `scale` `pw` `ph` | device profile, render scale, logical panel geometry |
| `dark` `ink` `paper` | polarity and the published panel pair (see §7 — frozen today, recorded anyway) |
| `exp` `arm` `armseed` | Phase 2. Empty in Phase 1. |

### `page` — one displayed page

```json
{"t":"page","ts":1787681606,"ms":4675,"cfg":2167091952,
 "bk":"c74f943fd94b9751","fmt":"epub","sp":1,"pg":1,"w":104,"c":544,"ln":21}
```

`bk` is `readerBookKey()` — FNV-1a of the book's path — as sixteen hex digits.
**The ledger names no titles.** That is a privacy property as much as a
compactness one: a log copied off the phone does not carry a reading list with
it. Nothing is lost, because `tools/reading_report.py --books <dir>` rehashes
the paths on the card and puts the names back locally.

`sp`/`pg` are the spine index and the page within it — the reader has no
book-cumulative page number, and this pair is exact where `pageCount` is only a
watermark. `w`/`c`/`ln` are words, characters and lines (§3).

### `evt` — a boundary

```json
{"t":"evt","ts":1787681584,"ms":0,"k":"boot","why":"","v":1}
{"t":"evt","ts":1787681584,"ms":382,"k":"screen","why":"1391791790","v":1}
{"t":"evt","ts":1787681990,"ms":406012,"k":"sleep","why":"deep","v":1}
```

`why` for a `screen` event is the FNV-1a of the activity name — the same key
`SheetIdentity.h` uses, so it is resolvable without recording screen names.

### Both clocks, on every line

`ts` is unix seconds and is the only thing that can put a session at a time of
day or order two launches. `ms` is milliseconds since this launch and is the
only thing that is monotonic. A phone's wall clock moves — timezone, NTP, the
owner setting it — and a dwell computed across such a step is a negative number
or an eight-hour page. The report groups by `ts` and can see when the two
disagree; `split_runs` treats a backwards gap as a run boundary rather than
producing a negative minute, which would flip the sign of a rate.

---

## 5. Outcomes — computed offline, and more than one

**The device computes nothing.** An outcome definition baked into the logger is
one that cannot be revised when it turns out to be wrong, and the first few will
be. Everything below lives in `tools/reading_report.py`.

A **run** is a maximal stretch of consecutive page lines in the same book whose
gaps are all at or under `--idle-cap` seconds (default 120). Runs rather than
sessions: a book left open on a table is not reading, and the only evidence the
device has that reading stopped is that pages stopped turning.

A run's **active time** is last-page-time minus first-page-time. The last page's
dwell is unknown — nothing says when he stopped looking at it — so **that page's
text is not counted**. Counting it would inflate every rate, and inflate short
runs most, which means it would favour whichever arm produced more
interruptions.

From that, four outcomes, all derivable from the same stream:

| Outcome | Definition | What it is good for |
|---|---|---|
| **rate** | characters ÷ active minutes | the classic reading-speed question; lowest signal-to-noise (§6) |
| **volume** | total active minutes per configuration per day | closest to his actual phrase, "got the most reading done" |
| **run length** | active minutes per run | engagement — does this setting keep him reading? |
| **abandonment** | gap that ended a run, and whether he came back | the most sensitive to something being *wrong* with a setting |

**Volume and run length are probably the better questions.** A typography effect
on reading *speed* is small (§6). A typography effect on whether he keeps going
for another twenty minutes could easily be large, and it is what he asked about.
The report prints rate as the headline because it is the one with a clean
denominator, but the run-length distribution is in the same data and does not
need a different log.

Two rules the report enforces that are decisions rather than plumbing:

- **A run spanning two configurations is dropped, not split.** The settings
  changed mid-run, which means he stopped to change them, and a rate across that
  belongs to neither.
- **The comparison is weighted by minutes.** An unweighted mean of run rates
  lets a two-minute noisy run outvote a forty-minute steady one.

The report always prints its answer at three idle caps (60/120/300 s). A
conclusion that survives only at one cap is a conclusion about the cap.

---

## 6. The power estimate, and the part that is unwelcome

This is an n-of-1 experiment and **the confounds are larger than the effects.**
Reading speed varies more between a dense non-fiction chapter and a novel than
any font will ever move it. Time of day, fatigue, how gripping the book is, and
interruptions all swamp typography.

### The arithmetic

For a two-arm comparison at α = 0.05 two-sided and 80% power, the runs needed
per arm is

    n ≈ 2 (1.96 + 0.84)² · cv² / δ²   =   15.7 · cv² / δ²

where `cv` is the coefficient of variation of the run-level rate *within* a
book, and `δ` is the effect as a fraction of the mean. Two things about that
expression, since both are easy to get wrong:

- It is the **two-sample, equal-n** form, so `n` is per arm and the total is
  `2n`. The leading 2 is that, not a fudge.
- It is **unpaired**, so it is *conservative* for a design that blocks within
  book. The blocking buys some of it back, by however much two runs in the same
  book are correlated — which is unknown until there is data, and is exactly why
  it is not assumed here.

The honest position on `cv`: **nobody here has measured it, and Phase 1's first
job is to.** The report prints both the pooled and the **within-book** figure
(the pooled one includes between-book variance, which the design blocks out, so
quoting it would overstate the runs needed by a lot) and re-derives the table
below from the measured within-book value the moment there is data. Until then,
using `cv = 0.15`, which is a plausible within-book, run-level figure and is
*optimistic* — page-level variation is far worse, and aggregating to a run is
what buys it down:

| Effect | Runs per arm | Reading hours (at ~25 min/run) | Calendar, at 1 h/day |
|---|---|---|---|
| 3% | ~392 | ~330 h | ~11 months |
| 5% | ~142 | ~120 h | ~4 months |
| 10% | ~36 | ~30 h | ~4–5 weeks |
| 20% | ~9 | ~8 h | ~1 week |

Published typography effects on reading speed between two *reasonable* settings
are typically in the 2–5% band. So:

> **A few weeks of reading can tell you if a setting is actively bad for you.
> Distinguishing two good fonts would take the better part of a year, and by
> then the thing you were measuring has probably drifted.**

That is the sentence to argue with before trusting any output of this tool. It
also says clearly what to point Phase 2 at: **large contrasts, not fine ones.**
Two font sizes two slots apart, not adjacent. Tight versus wide spacing, not
normal versus wide. Two genuinely different faces, not two serifs.

### Why the confounds do not simply average out

Randomization does eventually neutralise time-of-day and fatigue — over *many*
sessions, and "many" at this data rate is the whole problem. The design's job is
to remove what it can rather than average it:

- **Block within book.** The book is the largest single confound by a wide
  margin. Comparing arms only *inside* one book removes it entirely, and
  `permutation_test` permutes labels within book for exactly this reason. A book
  that carries only one arm is dropped, as a paired test drops unpaired
  observations. `tests/reading_report_test.py` has a case where the books differ
  enormously and the arms do not differ at all, and asserts it produces no
  significant arm effect — that is the test the whole file exists for.
- **Randomize at a chapter boundary.** A natural pause, so a changed face is not
  sprung mid-paragraph, and re-pagination lands at the top of a chapter where
  position is not lost.
- **Log the confounders you cannot remove.** Book, chapter, page ordinal,
  wall-clock time (so time of day and session ordinal are recoverable), device,
  polarity. Nothing conditions on them today. They are recorded so that
  something *can*, later, without needing a year of new data.
- **Few arms.** Two. Eight never converges.

---

## 7. Phase 2 — the randomizer, and the two decisions it waits on

`src/ReadingArm.h` is written and tested. Nothing calls it.

**The unit is a chapter.** Session-level randomization aligns the arms with
everything that varies by session; chapter-level compares inside one book,
usually inside one sitting, over prose of nearly the same difficulty.

**It is blocked, not independent.** Consecutive chapters are grouped into blocks
of `armCount`, and each block gets a random *permutation* of the arms — so every
complete block contains every arm exactly once. Independent coin flips would let
six chapters in a row land on one arm, and a book abandoned at chapter seven
would then contribute a lopsided comparison. Abandonment is itself an outcome,
so that imbalance is not random with respect to what is being measured.

**It is a pure function of `(seed, bookKey, spineIndex)`, not a draw.** Two
consequences, both load-bearing:

1. Turning back to chapter 4 renders it the way chapter 4 was rendered before. A
   drawn-and-cached assignment would re-roll it — jarring, and a
   correlated-measurement bug: the re-read would score as a fresh observation.
2. **The whole assignment is re-derivable from the log.** The seed is written
   into every `cfg` line, so an analysis can recompute every arm from scratch
   and check that the recorded ones match, rather than trusting the device. An
   experiment whose assignment cannot be audited is one whose results cannot be
   defended.

**A washout.** The reader meeting a changed face at the top of a chapter is
slower for a while for reasons that have nothing to do with which face is
better — and the switch happens at exactly the block boundary, so that transient
is perfectly confounded with the arm. `readingarm::countsTowardOutcome` drops
the first N pages of a chapter. It is applied in the *report*, not on the
device, so N can be varied afterwards and the answer checked for sensitivity to
it.

### Decision 1 — the gate

Phase 2 must ship behind an explicit setting that defaults **off**. That is a
new Settings.app row, and the standing ruling of 2026-08-23 is that a new row
has to earn itself against the nine that were removed that day. This one plausibly
does — it changes what the reader sees and he must be able to stop it — but it
is his call, not mine. **Not built.**

### Decision 2 — the page palette is frozen, and that is an owner question

He asked for **color** to be one of the variables. It cannot be, today.
`src/FrozenPage.h` (owner ruling 2026-08-24) freezes both appearances: Sanguine
ink on India paper for light, a named four-gun blend for dark, with the drawers
removed. So `ink` and `paper` are constants and a colour arm is not
possible without lifting that freeze.

**Reported rather than acted on.** Unfreezing the page is exactly the kind of
change that reverses a shipped decision, and reversing one costs far more than a
question does. The two fields are recorded in every `cfg` line *anyway*,
precisely so that the day the freeze lifts, every line already says which side
of that change it was on — a field that starts being recorded on the day it
starts varying is a field whose "before" is missing.

The question for him, when he wants it asked: *the page colour is currently
frozen at Sanguine/India and the CRT blend. A colour experiment needs that
freeze lifted for the two arms under test. Do you want it lifted, and for which
pair?*

### What Phase 2 should be pointed at first

Given §6, one factor at a time, two arms, chosen far apart:

| Rank | Experiment | Arms | Why first |
|---|---|---|---|
| 1 | font size | slot S vs slot L | the largest plausible effect, and the one where "more text per page" and "easier to read" genuinely trade |
| 2 | line spacing | tight vs wide | large contrast, one setting, no re-pagination surprises |
| 3 | font family | two genuinely different faces | what he asked about, but see §6 — needs the biggest sample |
| — | colour | blocked on Decision 2 | |

---

## 8. Where the file lives, and why not where you would expect

**Nothing leaves the device. No endpoint, no upload, no analytics.** That is a
constraint, and the place it has teeth beyond good intentions is the *path*.

On iOS the app's Documents directory **is** the emulated SD card
(`ios/CrossPointFsPrep.cpp` — rooted at Documents itself so `books` appears at
the top level of the Files app). The firmware's file-transfer screen serves that
card over HTTP/WebDAV, **bound to all interfaces on iOS**. A ledger written into
the card would therefore be published on the LAN every time he moved a book
across.

So it is not written there:

| Platform | Path |
|---|---|
| iOS | `~/Library/Application Support/CrossPointReading/reading.jsonl` — not exposed by `UIFileSharingEnabled`, unreachable by the web server |
| desktop | beside the simulated card, next to `settings.json`, exactly where a host artifact the firmware should never see belongs |
| anywhere | `CROSSPOINT_SIM_READING_LOG=<path>` overrides (tests, headless QA) |

`TargetConditionals.h` is included for that `#if`, and its absence would be a
silent selection of the *desktop* branch on a phone — which is the one place the
paragraph above says the file must never be.

**Getting it off the phone is a deliberate act.** Drop an empty file named
`EXPORT-READING-LOG` into the card root from the Files app, relaunch, and every
generation is copied into `<card>/reading-log/` where Files can share it; the
marker is removed so it happens once. A Settings.app row would be the obvious
alternative and is the wrong one — an export that runs twice a year does not
earn a row, and this costs no UI, no stored preference and no NSUserDefaults key.

### Retention

4 MiB per generation, twelve generations, **48 MiB hard ceiling**. Rotation is a
rename chain, never a truncate: the question a ledger answers is usually about a
month that already ended. Rotation happens *before* the write that would cross
the ceiling, so the bound is real rather than a bound plus one line.

At ~150 bytes a page line and a page turn every 30 s, an hour of reading a day is
**~430 KB a year**. Twelve generations is therefore on the order of a century of
his reading, and the cap exists for the pathological case (a stuck re-render
loop) rather than the ordinary one.

---

## 9. What it costs

Measured, not asserted.

| | |
|---|---|
| one page line — built, config-hashed, and appended with `fopen`/`fwrite`/`fclose` | **41–44 µs** (`tests/reading_log_test.cpp` prints it every run) |
| against a page turn's composite | 30–130 ms |
| share | **0.03 – 0.15%** |
| the firmware-side text walk | one pass over ~20–40 `PageLine`s, no measurement, no allocation; compiled out on device |

**Not batched in memory, deliberately.** A phone killed while backgrounded would
lose the buffer, and the entire value of the file is that it is complete. 44 µs
is not worth a correctness risk.

Everything is logged at boundaries — page commit, screen entry, sleep, launch —
and nothing is per frame.

---

## 10. Verified

Desktop canary green (`pio run -e simulator`). Headless run against a real book,
`CROSSPOINT_SIM_READING_LOG` pointed at a scratch file:

```
{"t":"evt","ts":1787681601,"ms":0,"k":"boot","why":"","v":1}
{"t":"evt","ts":1787681601,"ms":321,"k":"screen","why":"930363637","v":1}
{"t":"cfg","ts":1787681603,"ms":2193,"id":2167091952,"fam":"","pt":14,...}
{"t":"page","ts":1787681603,"ms":2193,"cfg":2167091952,"bk":"c74f943fd94b9751","fmt":"epub","sp":1,"pg":0,"w":79,"c":380,"ln":16}
{"t":"page","ts":1787681606,"ms":4675,"cfg":2167091952,"bk":"c74f943fd94b9751","fmt":"epub","sp":1,"pg":1,"w":104,"c":544,"ln":21}
```

One `cfg` line, then one `page` line per turn, ~110 words and ~540 characters per
page at 14 pt — plausible for the geometry, which is the only check available
before there is a corpus.

---

## 11. What was deliberately not built

Written down so the next session does not pay for the reasoning again.

- **No on-device statistics, summary screen or dashboard.** Every outcome is
  offline (§5). A number computed on the phone is a number that cannot be
  revised.
- **No read-aloud capture for word counting.** It is the expensive path; §3.
- **No in-memory batching of log lines.** §9.
- **No Settings.app row for anything here.** Phase 1 needs no control (it changes
  nothing the reader sees), and Phase 2's gate is an owner decision (§7).
- **No TXT/XTC text counting.** Those readers have no laid-out `Page` to walk;
  they publish 0/0/0 and are excluded from rates rather than counted as empty.
- **No unfreezing of the page palette.** §7, Decision 2.
- **No conditioning on time of day or session ordinal in the report.** The data
  is logged; nothing uses it yet. Adding it before there is enough data to fit
  anything would be fitting noise.
- **No per-page dwell in the log.** It is `ts[i+1] − ts[i]`, derivable, and
  storing a derived value is how a derived value goes stale.
