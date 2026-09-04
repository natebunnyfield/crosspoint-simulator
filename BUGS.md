# Known bugs and open defects — simulator

Running list for this repo, in the same format the firmware's `BUGS.md` uses.

It exists because simulator defects had nowhere to live. GitHub issues are
disabled on `natebunnyfield/crosspoint-simulator`, upstream
`crosspoint-reader/crosspoint-simulator` carries none, and the firmware's
`BUGS.md` is for firmware — so simulator findings survived only in `CLAUDE.md`
prose and agent memory. That is how `CLAUDE.md` accumulated the confidently
wrong claims it has since had to correct.

IDs are `S-NNN` so they never collide with the firmware's `B-NNN`.

A bug leaves OPEN only when there is evidence it is fixed. A passing build is
not evidence for anything you cannot observe headlessly — see the device-feel
rule in the project guide.

Format: `**[id] Title** — severity · where · status`, then what breaks, how it
was found, and what closing it requires.


## Where the rest of the work lives

Four trackers across two repos. Run the firmware repo's
`scripts/tracker-check.sh` for all of them with open counts and the next free
id — do not hand-pick an id.

| Tracker | Ids | Holds |
|---|---|---|
| `../crosspoint-reader/TODO.md` | `T-` | Firmware work that is owed |
| `../crosspoint-reader/BUGS.md` | `B-` | Firmware defects |
| **TODO.md** / [BUGS.md](BUGS.md) | `ST-` / `S-` | This repo, owed / broken |

Each tracker holds only its own prefix. Some items are paired across repos —
`ST-007` and the firmware's `T-016` are one job, and neither is done alone.

---

## OPEN

### [S-031] A theme flip re-arms the CRT beam sweep and splits the page's polarity for one frame — DEPOSIT HALF AND SWEEP-IN-FLIGHT FIXED 2026-09-04
**severity: high (visible, screen-wide, matches a repeated owner report) · scope: ios present pipeline (`src/HalDisplay.cpp`) · reported 2026-08-30, root-caused and reproduced — GUARD LANDED 2026-08-31 (`d4c59bb`), the standalone page-turn trigger never reproduced**

Owner, verbatim: *"Be sure not to flash from Zen mode to out of Zen mode for
any reason, period. Right now, switching from dark mode to light mode,
changing pages, things like that are causing, uh, Zen mode, disabled,
reenabled jump."* Investigated against the two hypotheses given (a real
`pollZenMode()` toggle; the `layoutPad` shift-guard race from [S-020]
below) on the booted iPad Pro 13 simulator. Both are CLEAN on this device:
zero `[zen] ... (setting)` / `(gesture -> settings)` log lines during
either trigger, and 279 combined frames across two recorded runs never
showed a non-black pixel in the bottom band or outer top margin (which
would mean the on-screen pad chrome reappeared). `layoutPad`'s phone-only
shift block (the code [S-020] patched) is dead code on iPad in the first
place -- `layoutPad` returns into `layoutPadTablet` before reaching it.

**What actually reproduces, twice, independently.** `applyTheme()`
(`ios/CrossPointIOSShim.cpp:1403`) calls `SimulatorOverlay::setPanelDark`
(:1455) -> `HalDisplay::setPanelDark` (`src/HalDisplay.cpp:1086`) ->
`HalDisplay::setInverted` (:1956), which sets `pendingReconvert` and
returns. `presentIfNeeded` services it (:2704-2708) via
`reconvertLastFrame()` (:965), which rewrites the cached planes to the NEW
palette and bumps `pixelBufSeq` -- already documented in place (:2856-2858)
as "a polarity reconvert ... is a change like any other." Further down the
SAME function, the beam-paint trigger (:2812-2821) reads that bump as
`contentChanged` and does `beamStartedAt = SDL_GetTicks()`, arming a fresh
CRT beam sweep with no exception for a reconvert that carries no new page
content. The sweep (`beamProgress`, :3250-3261) then composites the OLD,
fully-old-palette glass under the NEW, fully-new-palette one, revealed
top-down over the sweep's 55 ms (the shipped `CROSSPOINT_SIM_AS_SHIPPED`
beam value) -- so for a handful of frames mid-sweep the top of the panel is
already the new palette while the rest is still the old one, in the same
frame.

**Captured, not inferred.** Two independent `xcrun simctl io <udid>
recordVideo` runs (one appearance-only, one appearance + page turns) each
caught it one present after `xcrun simctl ui <udid> appearance light`.
Sampled down a column inside the panel: `y=390..495` reads the new light
palette (`~229-247,`225-241,`217-233), `y=500` onward reads the old dark
one (`~20-22,25-27,25-28`) -- a hard cut partway down the page. One capture
caught it on real book text: the paragraph's first line renders dark-on-
cream (new/light) while every line below it is still light-on-dark
(old/dark), in one frame. The zen sheet's geometry (card bounds, corner
radius, both black margins) is unchanged in this frame versus its
neighbors -- this is a palette race, not a layout race.

**Why it reads as "zen disabled, reenabled."** A screen-wide, self-
correcting-a-moment-later split between two entirely different color
schemes is a jarring discontinuity that does not require `g_zen` to move
to be described that way by someone watching it happen, especially
combined with the two flicker fixes shipped the same day ([S-020] below,
and the 2026-08-29 zen-toggle flicker in `docs/zen-mode.md`) training the
expectation that any zen-adjacent flash IS a zen toggle.

**Page turns tested separately, found CLEAN of this mechanism.** A genuine
page turn also bumps `pixelBufSeq` and also arms the sweep, by the same
path -- but old and new page share one palette, so the sweep composites two
frames of the same polarity and produces no visible split. Four
`QTAP:RIGHT` page turns (a real firmware button edge via
`HalGPIO::queueButtonTap`, which works under zen because page-forward is a
firmware button, not iOS overlay chrome) produced no split-palette frame.
**"Changing pages" as a standalone trigger was NOT reproduced this
session** -- recorded as unreproduced, not ruled out; it may need a page
turn landing inside an in-flight sweep from something else, or may
describe the same appearance-triggered mechanism from a different moment
of noticing it.

[As of 2026-08-31 the guard is in; see the Addendum.] **Not fixed.** The natural repair -- do not arm the beam for a
reconvert-only `pixelBufSeq` bump -- touches `presentIfNeeded`, the file
this repo's own history warns cost two build races in one day from
concurrent edits, and every downstream CRT pass (`glassPrevTexture`, the
accumulator capture, S-016's saturating blend) reads
`beamStartedAt`/`beamProgress`. Needs the nine-render byte-identical-md5
discipline the 2026-08-25 refactor used before landing, not a one-line
patch. Full account, including the exact pixel samples and both capture
recipes: `docs/zen-mode.md`, "2026-08-30: re-reported."

**Addendum, 2026-08-31 -- the status line above is stale, kept as written
rather than edited, because the fix it predates landed as its own commit.**
`d4c59bb` ("fix(crt): don't sweep the beam for a polarity reconvert",
2026-08-31 19:12:39) added the `reconvertOnly` guard this entry describes as
the needed repair, and its own message says its detector (252 frames across
an in-foreground appearance toggle) could not catch the bug either with or
without the fix -- "a detector that cannot catch the bug says nothing about
the fix." [S-033], filed the same day from an unrelated investigation into
foreground-resume reliability, supplies that missing detector: a REAL
`mobilesafari` background -> appearance flip while backgrounded -> resume,
captured on video. It caught the split on the pre-fix binary on the first
attempt (pixel-sampled, y-band cut matching this entry's own signature) and
did NOT catch it after rebuilding against `d4c59bb` and repeating the exact
recipe. Still device-unconfirmed, and still only one direction and one
recipe -- see [S-033] for the caveats -- but this is the first evidence
either way that the fix works, and it came from a stronger detector than the
one the fix shipped with.


#### Addendum, 2026-09-04: the flip DID still flash, through the trail, not the beam

Adversarial review (`docs/adversarial-review-2026-09-04.md`, finding 1)
reproduced a whole-glass flash on every light→dark flip that `d4c59bb`'s guard
could not stop, because the guard covered only the BEAM: the trail DEPOSIT
still keyed on `contentChanged`, and a reconvert bumps the sequence, so the
light page's glass — captured at absolute intensity — was deposited into the
accumulator and composited bright over the new dark ground, decaying over the
1095 ms trail. Measured on the desktop: +23 luma on 100% of pixels on the flip
frame, then 14 self-driven trail presents. Fixed the same day: `reconvertOnly`
now gates the deposit too (`glasscapture::shouldDeposit`), a sweep already in
flight is abandoned on a reconvert (finding 3 — the remaining frames were this
entry's split-palette picture), and the reconvert's sequence is reported by
the writer from under its own lock (finding 2). Post-fix the flip frame IS the
settled dark page (35.5 vs 35.5 mean luma). Ships in the next build; the
"changing pages" standalone trigger is still unreproduced.

## FIXED

### [S-034] Reader text insets were four separate atomics, not one — a torn read across a font-size change or a page turn fed the zen layout a geometry that matches no real page
**severity: high (matches a repeated owner report, mechanism proven and measured, NOT confirmed by render) · scope: cross-thread channel (`src/HalGPIO.cpp`), consumed by `ios/CrossPointIOSShim.cpp`'s zen layout · found and fixed 2026-08-31, render evidence UNOBTAINED this session (tooling failures, documented below)**

Owner, verbatim: *"there is a persistent issue after ios app reactivation then
font size change and page turn, where the page updates at full height then
immediately becomes single-finger mode. look into presentation logic and
address what should be assumed are multiple complicated issues underlying why
poorly laid out flashes happen at all."*

**What was already known before this investigation, from three prior entries
in this same family: [S-031], [S-032], [S-033].** All three describe the same
general shape — a present reaching the glass before some piece of layout state
has finished converging — and each was fixed at its own specific site
(`d4c59bb` withholding the CRT beam for a reconvert-only bump; the `g_zen &&`
guard on the shift block; the settle window covering resume). None of the
three is a data race; each is a *timing* bug, fixed by doing the relayout
before the present rather than after. This entry is a fourth, structurally
different mechanism in the same neighborhood: **a genuine cross-thread data
race**, not a timing race, and no amount of "pre-warm the layout call earlier"
can fix it, because the thing that is unsound is the READ itself.

**The mechanism, file:line.** `HalGPIO::publishReaderTextInsets`
(`src/HalGPIO.cpp`, pre-fix) stored four independent `std::atomic<int>`
fields — top, right, bottom, left — one `.store()` each, called from
`EpubReaderActivity` on the firmware's render task on every page render.
`SimulatorOverlay::readerTextInsetsPx()` read the same four fields back with
four independent `.load()`s, called every frame from `pollReaderInsets()`
(`ios/CrossPointIOSShim.cpp:1608`) on the **main thread** — a different
thread, with nothing coupling the four stores to the four loads as one unit.
The comment beside the old fields argued this was safe: *"a torn read across
two publishes of the SAME layout is harmless."* True, and beside the point —
the case that matters is a torn read across two publishes of **different**
layouts, and that is exactly what a font-size change or a page turn produces:
different top and bottom insets, because the reflowed text block ends
somewhere else. A reader can observe the NEW top from one publish paired with
the OLD bottom from the publish before it, a combination that corresponds to
no real page.

That combination is not inert. `ios/CrossPointIOSShim.cpp:1006-1024`'s
zen-shift arithmetic reads top and bottom straight into
`visTotal = slack + inkTopPx + inkBottomPx`, then
`aboveVis = visTotal / (1 + mult)`, then
`panelTopWant = paperTopPx + aboveVis - inkTopPx` — a torn pair feeds a `want`
shift that can land larger OR smaller than either the old or the new page's
correct target. `pollReaderInsets()`'s own edge trigger
(`if (t == s_top && b == s_bottom) return;`) then treats the torn value as a
real change, relayouts against it, and requests a present — one wrong-geometry
frame, followed by a second, corrective relayout on the very next poll once
the tear has passed (the next read is very likely to land on the fully
up-to-date pair). **That is a mechanism for "the page updates at full height
then immediately becomes single-finger mode":** one frame computed from an
impossible top/bottom combination, self-corrected a frame later — which is
exactly the two-frame shape a torn read produces and a timing race does not.

**Why "reactivation" widens the window.** `CrossPointHarness_perFrame()`
(hence `pollReaderInsets()`) runs every loop iteration with **no background
gate of its own** ([S-033] already established this for `pollAppearance()`;
the same is true here, same call site, same absent gate). Confirmed directly
this session: launching with a scripted font-size step and page turn
timed to land *while the app was still backgrounded* (an earlier, mistimed
repro attempt — see below) produced two full page renders, complete with
`[zen] published ink insets ... -> relayout` log lines, entirely inside the
`[DISPLAY] backgrounded` / `[DISPLAY] foregrounded` window — i.e. the
firmware's render task keeps running and keeps publishing while backgrounded,
and the main thread keeps consuming while backgrounded too. Reactivation does
not itself cause the tear; it is what puts the app in a state where several
publishes can queue up in quick succession right as the reader resumes acting
on the device, which is exactly when a font-size change and a page turn in
short order give the writer thread the most opportunities to publish while a
read is in flight.

**Fixed** by replacing the four independent atomics with one packed
`std::atomic<uint64_t>` (`src/ReaderInsetsChannel.h`, new file): 16 bits per
field, one `.store()`, one `.load()`. A load can now only ever return a value
this class actually stored, whole — never a mix of two stores.
`src/HalGPIO.cpp` was reduced to owning one `ReaderInsetsChannel` instance;
`publishReaderTextInsets` and `SimulatorOverlay::readerTextInsetsPx` are now
thin forwards to it. No signature changed on either the firmware-facing or the
host-facing side, so this is a drop-in.

**Proven, not asserted.** `tests/reader_insets_channel_test.cpp` round-trips
publish/read, checks the "never published" vs "published zero" distinction,
and checks clamping on out-of-range fields — then runs a concurrency case
built specifically to fail against the shape this replaces: a writer thread
alternates between two layouts (every field different between them, so a torn
mix is detectable in every field) as fast as it can for two million
iterations, while a reader thread polls concurrently and asserts every
successful read matches one whole layout. Checked BOTH ways, per the
project's mutation-verification habit: run against a throwaway copy of the
pre-fix four-atomic class, this exact test fails at **roughly a 50% torn-read
rate** (three runs: 147915/163296, 91381/63459, 14404/107107 torn/good — the
variance itself is what a genuine race looks like). Run against
`ReaderInsetsChannel`, it cannot fail: a single atomic cannot return a value
it never stored in full. `tests/run_all.sh` carries the new `run
reader_insets_channel` entry with this same accounting inline.

**A second, related site fixed for symmetry, lower confidence it is
load-bearing for this report.** `ios/CrossPointIOSShim.cpp`'s
`SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED` handler was the one geometry-invalidating
site (of four: this one, the zen toggle, Settings.app's `ApplyToLive`, and
`pollReaderInsets`) that cleared `g_padLaidOut` and requested a present
**without** calling `zenPreWarmLayout()` first — the exact asymmetry the other
three sites exist to avoid (see `zenPreWarmLayout()`'s own comment, and the
2026-08-29 zen-toggle flicker fix it generalizes). Without the pre-warm, the
very next panel fit reads the OLD topInset/bottomInset (published for the OLD
window size) against the NEW window dimensions — a real mismatch mechanism,
just not one this session observed firing from an ordinary
background/foreground cycle (see "Checked and CLEAN" below). Fixed by adding
the same `zenPreWarmLayout()` call the other three sites already have,
immediately after the defensive rect-zeroing that already existed there.

**Checked and CLEAN this session — the window-resize path specifically did
NOT fire during an ordinary background/foreground cycle.** Two clean
repro runs (`mobilesafari` launch to background CrossPoint, `simctl ui
appearance` unchanged, then relaunch CrossPoint's own bundle id to resume —
confirmed same PID both times, a real resume) showed no `[pad] tablet...`
relayout log between the `[DISPLAY] backgrounded` and `[DISPLAY] foregrounded`
lines, which is what a window-size-triggered relayout would have produced.
So the window-resize fix above is a real, symmetry-motivated repair, but it is
UNCONFIRMED to be the (or a) trigger for the owner's specific report; the
reader-insets race is the mechanism with actual evidence behind it (the
measured torn-read rate, and the confirmed sequence below).

**What WAS confirmed by direct reproduction, and what was not.** Built HEAD
(`c6ed882` at investigation start) for the iPad Pro 13 simulator
(`0E5288ED-A466-4750-9FDC-BEA83FE9531A`), zen forced on
(`CROSSPOINT_SIM_ZEN=1`), and drove the owner's exact recipe headlessly: enter
`EpubReader` (`QTAP:CONFIRM` from Home), background via `simctl launch
com.apple.mobilesafari`, foreground via `simctl launch
com.natebunnyfield.crosspoint.x3` (same PID both times), then a font-size step
(`QTAP:DOWN` — the side/rocker button, which this fork binds to
`stepReaderFontSize` via `longPressButtonBehavior = FONT_SIZE_STEP`; see
`docs/zen-mode.md`'s "On `BTN_UP`/`BTN_DOWN`" section) and a page turn
(`QTAP:RIGHT`), scheduled generously after the observed foreground time. The
log confirms the intended sequence landed in the intended order: `foregrounded`
at 23:03:03.450, `[zen] published ink insets 10/16 fb-px -> relayout` (the
font-size step's relayout) at 23:03:07.947, the page-turn's render completing
around 23:03:10.7 — reactivation, then font-size change, then page turn, each
producing a real relayout, exactly as reported. **What this session could NOT
obtain is a pixel capture of the bad frame itself.** `xcrun simctl io
recordVideo` entered a stuck "Host recording is already in progress" state
after an earlier attempt was killed uncleanly (fixed by `killall
CoreSimulatorService`, which also force-rebooted the simulator, costing the
run); a follow-up burst of 40 concurrent `simctl io screenshot` calls
congested the same daemon badly enough that all 40 came back byte-identical
(same md5), meaning the daemon serialized and serviced every request long
after the transition had already settled, and a `2m` background-command
timeout was hit waiting on it. Per this project's own doctrine (`docs/
headless-qa.md`, "a capture of the wrong screen looks a great deal like a
capture of a screen that never changed") and this repo's device-feel rule: the
mechanism is proven by code and by the concurrency test's measured torn-read
rate, and the trigger recipe is confirmed to produce the reported sequence of
real relayouts — but the specific claim "this produces the exact full-height-
then-single-finger-mode frame the owner saw" is **UNCONFIRMED by render**, not
proven. Closing that requires either a working `recordVideo` session on a
future attempt, or a device confirmation from the owner.

**Rejected: a generation/epoch gate across all layout inputs.** The task
brief that opened this investigation asked for exactly that as a candidate
architectural fix — tag layout inputs with a generation, compose a present
only when drawn content and consumed layout agree, defer rather than drop a
mismatched present. It was considered and set aside for this entry, because
it does not address the mechanism actually found: an epoch counter attached
to `pollReaderInsets()`'s edge-trigger would itself be read via the same kind
of unsynchronized cross-thread access this entry fixes, and a torn read of a
generation number is exactly as unsound as a torn read of the geometry it was
meant to guard. The fault here is not "a present ran before layout finished
converging" (every one of [S-031]/[S-032]/[S-033] is that shape, and each was
correctly fixed by re-ordering); it is "the read of one piece of published
state was not atomic." The fix that actually closes it is making that read
atomic, which is narrower, smaller, and directly testable — not a framework
the evidence here does not call for. If a FUTURE investigation finds a genuine
present-vs-layout ordering bug that survives all four `zenPreWarmLayout()`
call sites now in place, an epoch gate is worth revisiting then, against that
evidence.

**Checked and found CLEAN: the reader PAGE identity channel next to this one
in `src/HalGPIO.cpp` (`readerBookKeyValue`/`readerSpineIndex`/
`readerPageInSpine`) has the identical four(ish)-independent-atomics shape and
was NOT changed.** Its own comment makes the same "torn read across two
publishes of the SAME thing is harmless" argument the reader-insets comment
made — but unlike the insets, nothing downstream feeds a torn page-identity
read into arithmetic that produces a geometry: it seeds a paper-sheet random
seed (`sheetid::sheetForPage`), and the documented failure mode of a torn read
there is "one frame of the previous page's paper," a cosmetic, self-correcting
degradation with no analog to a `want` shift landing out of range. Left as is;
flagged here so a future investigation does not have to re-derive this
distinction from scratch.

Close by: obtaining a render (device, or a working `recordVideo` session) of
the reported sequence and confirming absence of the full-height/single-finger
frame post-fix.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; the packed channel (`4cd50c4`) shipped in build-163 and was never re-reported. The render evidence this entry wanted was never captured; the channel is host-tested and, since 2026-09-04, signed.

### [S-033] Returning to the foreground is unreliable when the system appearance changed while backgrounded — the S-031 split-palette frame reproduces on a REAL resume; rebuilding against the `d4c59bb` fix stopped it in the one recipe tried
**severity: high (visible, matches the owner's "make reactivate more reliable" ask) · scope: ios resume path (`ios/CrossPointIOSShim.cpp`, `src/HalDisplay.cpp`, `src/simulator_main.cpp`) · investigated 2026-08-31 on the booted iPad Pro 13 simulator (`0E5288ED-A466-4750-9FDC-BEA83FE9531A`) · pre-fix binary REPRODUCED AND CAPTURED, post-fix binary CLEAN on the same recipe, both UNCONFIRMED on device**

Owner: *"making reactivate on ios app more reliable"* — clarified as the app
returning to the foreground (background/lock/interrupt), not font
reactivation or sleep/wake. A prior investigation of this exact ask was lost
when its agent was killed before writing to this file; this entry redoes it
from scratch, per instruction.

**The trace, end to end, file:line, all read against the tree at commit
`d4c59bb` (HEAD as of this entry):**

1. `src/simulator_main.cpp:344` — `CrossPointHarness_perFrame()` runs inside
   the render task's `while (!display.shouldQuit())` loop (:318), once per
   `loop()` iteration, **with no `g_backgrounded` gate of its own.** It is
   compiled out on non-iOS (`#if CROSSPOINT_SIM_IOS`) but nothing inside it
   checks background state.
2. `ios/CrossPointIOSShim.cpp:3553` `CrossPointHarness_perFrame()` calls
   `pollAppearance()` first, every frame, backgrounded or not.
3. `ios/CrossPointIOSShim.cpp:1542-1568` `pollAppearance()` is edge-triggered
   on `systemIsDark()` vs. a function-local static, and separately on
   `SETTINGS.darkMode` vs. `g_appliedDark`. **If the phone's system appearance
   changed while the app was backgrounded, this edge fires on the very first
   frame back — and that frame runs before the app is visually foregrounded,
   because step 1 has no background gate.** It calls `applyTheme()`
   (`ios/CrossPointIOSShim.cpp:1403`).
4. `applyTheme()` → `SimulatorOverlay::setPanelDark(g_dark)` (:1455) →
   `setPanelDark()` (`src/HalDisplay.cpp:1141`) → `display.setInverted(dark)`
   (:1158) → `HalDisplay::setInverted()` (:2011) → `pendingReconvert.store(true)`
   (:2017). This runs, and completes, **while `g_backgrounded` is still true.**
5. `HalDisplay::presentIfNeeded()` (`src/HalDisplay.cpp:2679`) is the ONE place
   that gates on background state: `if (g_backgrounded.load()) return;` at
   :2679-2680, so nothing from step 4 reaches the glass yet — correct, by
   design (comment at :2679: "the frame stays owed and lands on the way back
   in").
6. On the real `SDL_EVENT_DID_ENTER_FOREGROUND`, `presentationWatch()`
   (`ios/CrossPointIOSShim.cpp:1504-1507`) calls `HalDisplay::setBackgrounded(false)`,
   which itself calls `SimulatorOverlay::requestPresent()` (`src/HalDisplay.cpp:2049-2057`),
   then `armSettleRepaint()` and a second `requestPresent()`
   (`ios/CrossPointIOSShim.cpp:1505-1506`) — this is S-027's settle window,
   confirmed present and wired for the ordinary case (see "Checked and CLEAN"
   below).
7. The FIRST `presentIfNeeded()` call after backgrounding clears services the
   reconvert queued in step 4 (:2762 `pendingReconvert.exchange(false)` →
   `reconvertLastFrame()`, which bumps `pixelBufSeq` and records
   `reconvertSeq`, :2762-2769).
8. The beam-arm check (:2846-2848) has a guard added by commit `d4c59bb`
   ("fix(crt): don't sweep the beam for a polarity reconvert", authored
   2026-08-31 19:12:39 -0500) that is supposed to withhold the sweep exactly
   for this case: `reconvertOnly = reconvertSeq != 0 && pixelBufSeq ==
   reconvertSeq`, and skip arming `beamStartedAt` when true.

**What I actually captured is the pre-fix failure, on video, with a pixel
trace — and it is the S-031 defect reached via resume, not via the
in-foreground appearance toggle S-031 was filed against.**

The device's installed binary
(`.../Bundle/Application/0941EE5A-7A96-4235-BBB3-25B643978344/CrossPointX3.app/CrossPointX3`)
is dated **2026-08-30 23:35**, roughly 20 hours before `d4c59bb` landed
(2026-08-31 19:12:39). So step 8's guard was NOT in the binary under test —
this reproduction is against the pre-fix build, and says nothing yet about
whether the fix holds. It is still worth recording in full, because:

- **This is a genuine background → foreground cycle**, not the appearance
  toggle S-031 used (`xcrun simctl ui ... appearance` while the app stayed
  foregrounded). Recipe: `xcrun simctl launch <udid> com.apple.mobilesafari`
  (backgrounds CrossPoint — confirmed via `[DISPLAY] backgrounded -- GPU
  presents suspended` in the log), then `xcrun simctl ui <udid> appearance
  light` while backgrounded, then `xcrun simctl launch <udid>
  com.natebunnyfield.crosspoint.x3` to resume (same PID, a real resume, not a
  relaunch), captured with `xcrun simctl io <udid> recordVideo` running
  throughout.
- **`d4c59bb`'s own commit message says its detector could not catch the bug
  at all**: *"252 frames across a dark/light switch found no split-palette
  frame WITH the fix, and the control with the fix reverted found none
  either. A detector that cannot catch the bug says nothing about the fix."*
  My detector (a real background/foreground cycle) DID catch it, on the
  pre-fix binary, on the first attempt — which is exactly the missing
  detector that entry asked for.
- The log confirms the mechanism fired exactly as traced: `[harness]
  SETTINGS.darkMode -> 0 (system appearance)` and `[harness] appearance ->
  light (system)` both timestamped 19:20:24.00x — **1.94 seconds BEFORE**
  `[DISPLAY] foregrounded -- GPU presents resumed` at 19:20:25.947. The
  theme flip is fully processed while the app is still backgrounded, exactly
  as traced in steps 3-5 above.

**Pixel evidence, extracted from the recorded video
(`xcrun simctl io <udid> recordVideo`, frames pulled with `ffmpeg -vsync 0`,
no scaling, no recompression before sampling).** Frame `t_0064` (video
timestamp 5.178s) reads uniformly dark; frame `t_0066` (5.390s) reads
uniformly light; the frame between them, `t_0065` (5.240s — a 62 ms window,
consistent with the documented 55 ms beam), is split:

| x | y=408-544 | y=612-1904 |
|---|---|---|
| 516 | (230,223,216) / (236,229,222) / (231,222,215) — new LIGHT | (19-22,24-27,25-28) — old DARK, matches frozen dark ground `171B1B` |
| 619 | (218,212,205) / (223,216,209) — new LIGHT | (16-25,21-30,20-29) — old DARK |

Top of the panel already reads the new light palette; everything below
y≈580 is still the pre-switch dark ground — the same top-down cut S-031
documented (their sample: y=390-495 new, y=500+ old). Same mechanism, new
trigger.

**Distinguishing what kind of "unreliable" this is.** It is not a hang and
not a dead channel — the app recovers and lands on the correct (light)
palette within about 2 seconds of the foreground event, matching
`kForegroundSettleMs`. What is unreliable is the FRAME ITSELF during that
recovery: for one ~60 ms window mid-transition, the glass shows two
palettes in the same picture, which is a jarring, screen-wide visual defect
right at the moment a returning reader is looking at the device — worse
optically than a blank screen because it looks broken rather than merely
slow. Whether an iPhone user would actually notice a 60 ms split frame the
way this frame-by-frame capture did is UNCONFIRMED on device; it is not
UNCONFIRMED as a mechanism — it is captured, sampled, and traced to file:line.

**Ordinary resume (no appearance change while backgrounded), checked and
found CLEAN.** A control run — background via the same `simctl launch
mobilesafari` swap, no appearance change, foreground via `simctl launch
com.natebunnyfield.crosspoint.x3` — showed no blank hang and no stale frame:
the app-switcher zoom shows the pre-background snapshot (expected iOS
behavior, not this app's concern) and by the time our own rendering resumes
the content is already correct. This does not confirm S-027's fix works on
a real device — the S-027 entry itself notes "no host reproduces a Metal
surface discarding a present" — but it rules out a second, independent
failure mode on THIS host for the plain case.

**Done: rebuilt against `d4c59bb` and re-ran the exact resume recipe. The
fix holds against this detector, on this host, this session — still
UNCONFIRMED on device, but this is the first evidence for it at all.** No
source in `ios/`, `src/`, or `tests/` was edited to do this — only
`cmake --build build/ios-app --config Debug --target CrossPointX3` against
the tree as the other agent left it, then `xcrun simctl install`. Binary
timestamp 2026-08-31 19:27, after the fix commit (19:12:39).

Two runs, both with a real `mobilesafari` background → `simctl ui appearance`
flip while backgrounded → relaunch of `com.natebunnyfield.crosspoint.x3` to
resume, `recordVideo` running throughout, log-confirmed theme-flip-while-
backgrounded exactly as traced above (`[harness] SETTINGS.darkMode -> 1
(system appearance)` / `appearance -> dark (system)` at 19:30:29.59x, 1.84 s
BEFORE `[DISPLAY] foregrounded` at 19:30:31.434 — same 1-2 s lead as the
pre-fix run). The first attempt raced its own setup (launched the app, then
immediately backgrounded it before `CrossPointHarness_begin()` had finished
— the app's global `decideSeedDarkFromSystem()` initializer ran AFTER the
appearance flip had already landed, so it silently seeded correctly and
proved nothing; caught by reading `[harness] appearance seed: stored=X
system=X -> keep setting` in the boot log rather than assuming a `sleep 3`
was enough). Waiting for `[harness] button pad installed` before
backgrounding fixed the race.

Pixel-sampled the two frames bracketing the flip
(`frames_postfix2/p_0074.png`, video t=4.913s, and `p_0075.png`, t=5.078s —
a 165 ms gap, comparable resolution to the 212 ms gap that caught the
pre-fix split): `p_0074` reads uniformly light down the whole panel column
(x=516,619, y=400-1900, all ~(222-246,213-240,207-233)); `p_0075` reads
uniformly dark (~(22,26,28), matching `171B1B`) at every sampled y, no band,
no partial row. Compare this to S-033's own pre-fix sample above, which was
a clean split at identical sampling resolution. Consistent with the fix
working, not merely with the sweep landing between frames — the pre-fix
run's sweep did NOT hide between frames at similar spacing, so the absence
here is evidence, not just a miss.

**Caveat, stated plainly: this is one clean transition, not a proof.** A
55 ms sweep can still fall inside a wider gap on a slower device, and only
two directions (dark→light pre-fix, light→dark post-fix) and one resume
recipe were tried. It is exactly the "device-confirm only" situation the
project's own doctrine calls for — mark it SHIPPED, UNCONFIRMED on device,
not "fixed."

**Checked and CLEAN, this session — not the cause of anything reported
here:**
- `HalDisplay::presentIfNeeded()`'s background gate (`src/HalDisplay.cpp:2679-2680`)
  is unconditional and correct: no GPU work is attempted while backgrounded,
  and `pendingPresent` is left set so the frame is not lost, only deferred.
- `HalDisplay::setBackgrounded()` (`src/HalDisplay.cpp:2049-2057`) only calls
  `requestPresent()` on the false-going edge (`was == backgrounded` returns
  early otherwise), so it cannot double-fire.
- The text-entry / keyboard channel (`ios/CrossPointKeyboardBar.mm`,
  `gpio.isTextEntryActive()`) has no background/foreground-specific code at
  all — neither a bug nor a fix; it simply is not wired to either lifecycle
  event, so a field left open across a backgrounding is unexamined by this
  session and not confirmed either way.

Full account of the appearance-only version of this defect: [S-031]. Full
account of the blank-screen-on-resume defect this shares a settle-window fix
with: [S-027].

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; the guard (`d4c59bb`) and the detector (`26e8c0f`) shipped in build-162 and the resume was never re-reported. The trail-deposit half of the flip flash was found and fixed 2026-09-04 (S-031 addendum) and ships in the next build.

### [S-032] The paper resizes for a frame on a page turn, with zen OFF
**severity: medium · scope: ios layout · reported 2026-08-30, fix landed UNPROVEN against the symptom**

**Filed as S-020 and renumbered to S-032 on 2026-08-30**, which is the id
that entry has always meant: `[S-020]` was already taken by the dark-mode gun
/ light-ink bug below, fixed 2026-08-23. Two live entries under one id made
`scripts/tracker-check.sh` exit 1, so neither was counted honestly.

Owner, from the phone: *"there is still a flash on page change after disabling
[zen] mode"*, clarified as *"it's an odd quick resizing to the paper"* — a
GEOMETRY flicker, not the luminance flash of [S-016].

**What was found by reading, and is certain.** In `layoutPad`, the block that
computes the zen page shift was gated on geometry alone:

```cpp
if (panelHPx > 0 && g_zenRowTopPx > paperTopPx + panelHPx) {   // no g_zen
```

Its inputs are the firmware's published ink insets, which move on **every page
turn** — each page's text block ends somewhere different. When the computed
`want` moves more than 0.5 px it sets `g_padLaidOut = false` and calls
`SimulatorOverlay::requestPresent()`, forcing a full relayout and an extra
present. Sixty lines later the result is thrown away outside zen:

```cpp
g_zenShiftThisPass = g_zen ? g_zenPanelShiftPx : 0.0f;
```

So with zen off, every page turn paid for a relayout whose only product was
discarded — and a relayout re-derives the pad band, which is the term the panel
fit depends on. That is a mechanism for exactly the reported symptom, and it is
dead work regardless.

**Fixed** by adding `g_zen &&` to that condition (2026-08-30). In zen nothing
changes: same condition, same arithmetic, same shift. The zen-only pre-warm
that exists to stop unconverged frames reaching the glass — `pollReaderInsets`,
itself `if (!g_zen) return;` — could never have covered the non-zen path, which
is why the 2026-08-29 flicker fix did not reach this.

**NOT PROVEN AGAINST THE OWNER'S SYMPTOM, and that is the honest status.** The
attempted before/after on an iPad Pro 13 simulator did not produce a control:
the pre-fix run landed in chapter selection rather than the reader, and the
`[zen]` layout logs are suppressed once a layout settles, so "0 shift lines"
after the fix is consistent with the fix working AND with the log never firing.
What is proven: 70/70 sim tests, and the code path above, read end to end.

**Close by** confirming on the phone. If the resize survives this, the cause is
NOT this block and the search should move to the panel fit itself
(`HalDisplay`'s scale selection) rather than to the pad layout — which is a
useful elimination either way.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; `c25448b` (`g_zen &&` on the shift block) shipped in build-162 and the resize was never re-reported.

### [S-025] The CRT page fade stalls and resumes when a redraw runs
**severity: medium (the effect reads as broken) · scope: page fade / present loop · filed 2026-08-27 from the device · NOT YET REPRODUCED**

Owner: *"there's a stutter lag hold on redraw for crt fade (the fade does not
account for time spent redrawing and it pauses and resumes in a visibly awkward
way)."*

**FIRST HYPOTHESIS CHECKED AND WRONG, 2026-08-27 — recorded so it is not
re-derived.** The obvious guess is that the fade is an accumulator advanced once
per frame, which a slow present would starve. It is not. `HalDisplay.cpp:3224`
[was `:3120-3121`, re-grepped 2026-09-04; before that `:3039`] computes `age = SDL_GetTicks() - lastInteractionMs` and derives alpha from that
age, so the fade is ALREADY a pure function of wall time, evaluated at present.
A late present therefore lands on the correct alpha for the wall clock, not a
stale one, and the fix "make it wall-clock" has nothing to do.

**The surviving lead is COST PER FADE STEP, not the clock.** The fade wakes once
per QUANTIZED alpha step (`pagefade::nextStepAgeMs`, `pageFadeStepDueMs`) and
each wake sets `pendingPresent` — so every visible step of the fade pays a full
present. With the as-shipped dials a present is not cheap: measured 51–53 ms of
panel field even with the sheet served from cache, and ~130 ms when the seed
moves and the sheet rebuilds. A fade whose every step costs 50 ms cannot look
smooth, and a step that coincides with a real redraw costs both.

That also explains the shape of the complaint precisely — "pauses and resumes"
rather than "runs at the wrong speed". The VALUES are right (wall clock); the
DELIVERY of them is lumpy.

**SECOND HYPOTHESIS ALSO WRONG - MEASURED 2026-08-28.** The cost theory above
is disproved by the instrument this repo already has.
`CROSSPOINT_SIM_LOG_TIMING=1`, as-shipped dials, dark ground, a 3 s fade:

```
[timing] #51 total 14.25 ms | accum cache 11.43 | panel off | sheet off | scanlines off | grain cache 0.00
[timing] #57 total  2.64 ms | accum cache  1.99 | panel off | sheet off | scanlines off | grain cache 0.00
```

**Every field reads `cache` or `off` on every fade present - nothing rebuilds**
- and a present costs **2.6-14.7 ms**, not the ~50 the cost theory needed. The
sheet is not rebuilt per fade step, so there is nothing there to make cheaper.
The dominant line is the trail accumulator, and it is a cached draw.

**What the data DOES show is the step SCHEDULE.** Present-to-present intervals
across one fade, in ms:

```
64  194  133  192  191  188  301  344  474  772  2083
```

They lengthen, and they must: alpha follows 10^(-age/fade), so the time to the
next QUANTIZED step grows as the curve flattens. `nextStepAgeMs` is correct and
doing exactly its job - but late in a fade the picture changes once every two
seconds, and each change is one code value.

The remaining question is PERCEPTUAL rather than mechanical, and reading the
code again will not answer it: whether the awkwardness is those late sparse
steps, the unevenness of the early ones (194/133/192 is not a smooth cadence),
or something that appears only on Metal at 120 Hz. Recorded as measured rather
than guessed a third time.

**Two hypotheses are now disproved and must not be re-proposed**: it is not a
per-frame accumulator (the age is wall-clock), and it is not field rebuild cost
(everything is cached). Related: S-019, whose fix - waking once per quantized
step instead of every frame - is what produced this schedule.

### The step SIZES, measured 2026-08-28 -- and they are minimal

The interval data above says when steps land, not how big they are, so a jump
of several code values every two seconds was still a live theory. It is not
what happens. `CROSSPOINT_SIM_LOG_PRESENTS=1`, same run:

```
age 3033 ms -> alpha 0.774      age 4362 ms -> alpha 0.759
age 3281 ms -> alpha 0.770      age 5144 ms -> alpha 0.755
age 3581 ms -> alpha 0.766      age 7271 ms -> alpha 0.751
age 3929 ms -> alpha 0.762
```

Every delta is **0.003-0.007 of alpha -- about ONE code value** -- for the whole
fade. So the late steps are not jumps. They are the smallest change the panel
can express, arriving up to two seconds apart, and a single code value is not
individually visible.

**What is left in the data is JITTER, not size or cost.** Identically-sized
steps land 194, 133, 192, 191, 188 ms apart early on: the due time is computed
exactly by `nextStepAgeMs`, but it is serviced when the main loop next looks, so
delivery varies by up to a loop period while the change per step is constant.

### ...and it is not jitter either. THIRD hypothesis disproved, same day.

The uneven intervals looked like late delivery: a due time computed exactly and
serviced whenever the loop next looked. That was worth one more check, because
if true it could be fixed by ending the loop's sleep AT the due time -- the same
number of wakes, better timed -- which would have dissolved the battery trade
this entry had just handed to the owner.

**The loop polls at ~1 kHz.** `simulator_main.cpp` ends each pass with
`SDL_Delay(1)`, so a due time is serviced within about a millisecond. A 194 ms
gap next to a 133 ms gap is not delivery slipping by 60 ms; it is where the next
code-value boundary actually falls on the decay curve. The schedule IS the
curve.

## Nothing mechanical is wrong. Four measurements say so.

1. The age is **wall-clock**, so a late present lands on the right alpha.
2. Every field is **cached** during a fade; presents cost 2.6-14.7 ms.
3. Every step is **one code value**; there are no jumps.
4. Steps are **delivered within ~1 ms** of when they are due.

A model that is correct, cheap, minimal and punctual has no defect left to find
by reading it. So either the awkwardness is something this instrument cannot
see, or it is not the fade.

**The one difference this measurement cannot cover** is the platform: it ran on
the SOFTWARE renderer at scale 1, and the phone is Metal at 2x with a 120 Hz
display. If the report survives, that gap is the only place left to look -- and
the useful next capture is a video of the glass, not another log, because every
number the log can produce is now in this entry.

Closed 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix: four measurements found nothing mechanical (2026-08-28), builds 158 through 169 shipped since, and the stall was never re-reported. Reopen on a new report, with a video of the glass as the entry asks.

### [S-019] The app averages 50% of a core for minutes at a stretch on the phone
**severity: medium (battery) · scope: iOS present loop · filed 2026-08-22 from the device's own diagnostics · HALF FIXED 2026-08-25, BOTH LOOPS BOUNDED (corrected 2026-09-02)**

**STATUS, corrected 2026-09-02 -- BOTH LOOPS BOUNDED; the 2026-08-29
re-confirmation below was wrong.** Loop 2 was closed on 2026-08-26 by
`a8def02` (refined by `9a01abd` on 08-29): `accumLive` is bounded by
`accumPeakBound > trailInvisibleAtOrBelow()` (`src/TrailLifetime.h`,
`src/HalDisplay.cpp` beside the `2.4f`), which ends the live window the
moment the MAXIMUM-composited trail can no longer alter a pixel over the
paper floor -- the "shrink to measured ~1.10 trails" lever, exactly. The
flat `trailMs * 2.4f` the 08-29 note cited as "unchanged since the filing"
is still there, as a BACKSTOP `&&`ed after the bound so the rule can only
shorten the loop (a pure-black paper makes the bound zero and would
otherwise never end). The re-confirmation grepped the backstop line and
missed the bound on the line above it. The owner, asked on 2026-09-02
between the two levers, chose this one -- which is the one already in the
tree, so nothing moves. Measured at the fix: dark page turn 1788 -> 955 ms
of CPU (the re-upload half of that commit) and the last 15 byte-identical
presents of a 2628 ms trail no longer drawn. Frame-rate cap: NOT taken,
by the owner's standing constraint ("keep refresh as high possible, 120hz
is best. never shorten the window so that it drops frames").
`tests/trail_lifetime_test.cpp` sweeps the bound. Still open and
measurement-only: the ~35% of a core figure in the table below predates
both fixes and has not been re-measured on a phone.

The record as it stood: two separate
render loops were behind the original report. **Loop 1 (the page fade re-arm)
is FIXED** (2026-08-25): `presentIfNeeded` now schedules the next present at
the wall-clock instant the quantized fade alpha actually changes
(`pagefade::nextStepAgeMs`, `src/PageFade.h:148`, consumed via
`pageFadeStepDueMs` in `src/HalDisplay.cpp:108,2733-2735,3154-3159`
[re-grepped 2026-08-29 — this citation had drifted to 108,2652-2654,3059-3078,
which is now unrelated composited-field code], instead of
re-arming `pendingPresent` on every present regardless of whether the visible
alpha moved. **Loop 2 (the phosphor-trail live window) was ALSO CLOSED, 2026-08-26 — see the STATUS above; the paragraph that follows is the 2026-08-25 record.**
`accumLive`'s window is a flat `trailMs * 2.4f` (`src/HalDisplay.cpp:3587`
[was `:3505`, re-grepped 2026-08-29]), unchanged since the filing [Superseded: bounded by `accumPeakBound > trailInvisibleAtOrBelow()` at `src/HalDisplay.cpp:3711`, with the 2.4f as an `&&` backstop at `:3712`.], and it is what a dark page turn's ~84 presents /
2.63 s actually cost. [Ruling taken 2026-09-02, see STATUS.] Closing it needs an owner ruling between the two levers
below — cap the present loop's frame rate (fewer intermediate frames, same
trail duration and end state), or shrink the live window to the measured
~1.10 trails the MAXIMUM-blend accumulator can still alter a pixel within
(a 54% shorter window, provably bit-identical, but wants a pixel A/B in the
tail before it ships). Do not close this entry on the fade fix alone.

**2026-08-25: reproduced, measured, and split in two.** Everything below the
original entry is the 2026-08-22 filing and stands as the report. What the
measurement found is that there were two separate render loops behind it, one
of which is now fixed and the other of which is a design cost the owner has to
price. Method: desktop `simulator_x3`, `SDL_VIDEODRIVER=dummy` (software
renderer, render scale 1), `CROSSPOINT_SIM_AS_SHIPPED=1`, `/usr/bin/time -l`
for CPU and `CROSSPOINT_SIM_LOG_PRESENTS=1` for the present count. A software
renderer at 1x overstates the per-present cost against the phone's Metal and
understates its pixel count; the present COUNTS are the platform-independent
half and they are what is quoted.

**The shell does not idle-spin, and that lead is dead.** An idle as-shipped
dark reader presents **once in 30 seconds** and sits at **0.1% of a core**.
`sample` on the main thread puts 5922 of 6103 samples in `nanosleep`, under
`loop() -> HalPowerManager::lightSleep -> delay(50)`: the FIRMWARE's own loop
blocks for 50 ms at a time, so `simulator_main.cpp`'s `SDL_Delay(1)` never sets
the pace when nothing is happening, and its "~1 kHz" comment describes a rate
the loop only reaches when the firmware asks to spin. The simulator's
`lightSleep()` (`src/HalPowerManager.h:42`) is unconditional -- always
`delay(50)`, always true -- so it never takes the firmware's WiFi/USB decline
branches and the idle cadence is IDENTICAL on desktop and iOS. Also ruled out:
`EpubReaderActivity::skipLoopDelay()` was not spinning in any of these runs
(present intervals were 15-16 ms, which is `delayWallClock(10)` plus a present,
not the ~6 ms a 1 kHz spin gives), and the phosphor accumulator does terminate
(`accumLive` is bounded, and an idle page logs `live=0`).

**LOOP 1 -- THE PAGE FADE. Fixed 2026-08-25.** With a fade set (the owner's own
`settings.json` carries `pageFadeSeconds: 300`, `pageFadeDepthPercent: 75`) an
idle app presented **507 times in 30 seconds and burned 10.3% of a core**, on a
page nobody was looking at, for the whole length of the fade. `HalDisplay.cpp`
re-armed `pendingPresent` on every present while `pagefade::stillMoving`. But
what reaches the glass is `round(alpha * 255)`, and over a 300 s fade that curve
moves **0.008 of a code value per 60 Hz frame** -- so about 127 of every 128 of
those frames were bit-identical to the one before. Fixed by scheduling the next
present at the wall-clock instant the QUANTIZED alpha actually changes
(`pagefade::nextStepAgeMs`, parked in `pageFadeStepDueMs` and woken by a new
gate at the top of `presentIfNeeded`). A fade of any length now costs at most
255 presents in total, which `tests/page_fade_test.cpp` asserts.

| 30 idle seconds, fade at 300 s / depth 75 | presents | user CPU |
|---|---|---|
| before | 507 | 3.12 s (10.3% of a core) |
| after | 23 | 1.12 s |
| no fade at all, for scale | 1 | 0.96 s |

The fade's own cost is 2.16 s per 30 s before and 0.16 s after: **13.5x**.
Pixel proof, same script and same card, against the pre-fix binary: captures at
8,000 ms and 30,000 ms are BYTE-IDENTICAL; the one at 15,000 ms differs by a
maximum of **1** code value on 9.7% of bytes, which is one alpha step -- the
schedule rounds up to whole milliseconds, so a capture between two steps can
sit one step behind. The two `tools/capture_arm.sh` gate baselines
(`53aaf43c38cc834f501525b5973d2566` dark, `3f4773ed9d77fac0da90d6d2fb4aba72`
light) are unchanged, and 54/54 host tests pass.

**This is the loop that fits build 107**, whose report is dated 2026-08-20 --
inside the window where Page Fade was a row in Settings.app (it landed 1514fe0
on 08-17 and was frozen OFF by bc74bd8 on 08-23). Commit f7a0b5f, 2026-08-20,
records the symptom in passing without recognising it: *"presents run
continuously at ~15 ms."* Note the phone CANNOT hit this today --
`CrossPointPrefs_pageFadeSeconds()` returns 0 without consulting NSUserDefaults
-- so for iOS this half was already fixed in passing by the freeze, and what is
fixed here is the desktop, and the loop itself for whenever the row comes back.
The four reports from 2026-08-15 (builds 76-79) predate the fade entirely and
are NOT explained by it.

**LOOP 2 -- THE PHOSPHOR TRAIL. Live on the phone, and an owner decision.** (2026-08-25 record; closed 2026-08-26, ruled 2026-09-02)
A dark page turn costs **84 presents spread over 2.63 seconds**. Present #2
builds the scanline field (39 ms); #3 through #84 are all cache hits whose cost
is the composite itself, 4-12 ms each on this renderer. The window is
`accumLive`'s `trailMs * 2.4` (`src/HalDisplay.cpp:3587`) -- 2628 ms at the
shipped 1095 ms trail -- and
during the first second the firmware polls at 100 Hz, so the app composites the
whole surface about 62 times before dropping to the 20 Hz light-sleep cadence.
Measured end to end: a page turn every 3 seconds for a minute is **38% of a
core** (24.25 s of CPU over 64 s, ~1.2 s per page turn). That is the shape of
the report, and it is untouched by the fade fix (1575 presents after, 1576
before). Two levers (lever 2 was taken, `a8def02`/`9a01abd`):

- **Cap the animation's frame rate.** The accumulator's decay is TIME-based
  (`dt` since `accumLastFadeMs`), so a cap changes neither the trail's duration
  nor its end state -- only how many intermediate frames are drawn. 30 Hz would
  take 84 presents to about 53.
- **Bound the live window by when the trail can no longer alter a pixel,**
  instead of a flat 2.4 trails. The accumulator composites with MAXIMUM under a
  colour mod of the ink, so its ceiling is `decay x ink`; once that is at or
  below the paper tone it cannot change any pixel, because every pixel under it
  is at least paper. For the shipped `E0E0DE` on `121212` that is 18/224, i.e.
  **1.10 trails, not 2.4** -- a 54% shorter window, worth about 22 of the 84
  presents. Provably bit-identical, but it needs a pixel A/B inside the tail
  before it ships.

**iOS DOES NOT DIFFER HERE, and that is measured rather than argued.** The same
page-turn session was run on the iOS Simulator (iPhone 13 mini, Metal renderer,
`simctl launch` with `SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT` driving one
`QTAP:RIGHT` every 3 s for a minute) against a fresh `build-simsdk` build:

| one page turn every 3 s, dark, 60 s | presents/turn | CPU |
|---|---|---|
| desktop, software renderer, render scale 1 | 83 | 24.25 s / 64 s = **38% of a core** |
| iOS Simulator, Metal, render scale 3 | 65 | 20.8 s / 60 s = **35% of a core** |

Nine times the pixels on a GPU lands within three points of the software
renderer at 1x, which says the cost is carried by the NUMBER OF PRESENTS and
not by what each one paints -- so the lever is the count, not the resolution.
(That tree's CMake cache is stale at 3x where the app ships 2x, so the iOS
figure if anything overstates the shipped cost; it was not reconfigured because
a render-scale define is PUBLIC on `crosspoint_core` and would rebuild
everything.) Idle on the same iOS build is **0.6% of a core** and effectively
no presents, matching the desktop exactly -- as it must, because
`HalPowerManager::lightSleep` is this repo's own header and is unconditional on
both platforms.

**Close by:** re-measuring the ~35% figure on a phone (the only residue, per the STATUS above).

**THE ORIGINAL FILING, 2026-08-22, unchanged:**

King's crash-report store (pulled over pymobiledevice3, Developer Mode
enabled 2026-08-22) holds five `CrossPointX3.cpu_resource` reports — builds
76, 78, 78, 79 (all 2026-08-15) and **107** (2026-08-20):

```
Event:  cpu usage
CPU:    90 seconds cpu time over 179 seconds (50% cpu average),
        exceeding limit of 50% cpu over 180 seconds
Action taken: none
```

The heaviest stack is the main run loop into app code (unsymbolicated —
release build, dSYM not to hand), which is the shape of the SDL
present/compose loop repainting every frame whether or not anything changed.
iOS only diagnoses at this rate ("action: none"), but half a core for the
length of a reading session is battery, and the phone was at 9% when it came
in for this checkup.

**Close by** symbolicating one report against the build-107 archive's dSYM to
confirm the loop, then making the present loop event-driven when the screen
is static — the firmware's e-ink model already knows when nothing repaints;
the shell should idle with it. Re-verify with a fresh cpu_resource-free week
on the phone.

The same pull's full disposition, for the record: five real crash reports,
all build 110, all the SAME `objc_retain(0x1)` in `-[UIViewController
setTitle:]` — the palette-mixer crash already found on-device and sidestepped
in build 111 (`CrossPointPaletteMixer.mm` carries the note); and seventeen
JetsamEvent appearances, every one `long-idle-exit` housekeeping, zero
memory-pressure kills. No unknown crashes.


---

Closed 2026-09-04 under the 2026-09-02 ruling: both loops bounded (`a8def02` / `9a01abd`, build-138 and later), the lever ruled 2026-09-02, and the CPU figure never re-raised. The ~35% re-measurement on a phone is a measurement, not a defect; take it if a battery report returns.

### [S-026] The bottom-right rocker flashes when a DIFFERENT button is pressed — TWO CANDIDATE FIXES SHIPPED, chase dropped 2026-08-28

> **Owner 2026-08-28: stop following this up.** Two candidate fixes shipped in
> build 156 (the painter's missing retired-slot guard, and the hit test walking
> stale geometry after a resize) and neither is proven to be the cause, because
> nothing here reproduces the report. Rather than keep asking him to watch for
> it, the entry stands as filed: if the flash recurs he will say so, and the two
> remaining suspects are named at the foot. Not closed — unproven and unchased.
**severity: medium (visible, wrong) · scope: iOS pad overlay · filed 2026-08-27 from the device · NOT YET REPRODUCED**

Owner: *"bottom right rocker switch is flashing on a subsequent press of another
button."*

So pressing button A repaints button B's pressed state. Two candidates, both
cheap to distinguish once reproduced:

1. **A stale pressed-index.** The pad draws a highlight for whichever index it
   believes is down; if the release path clears the *drawn* state later than it
   clears the *logical* state (or not at all), the next press repaints the
   previous button for one frame. The bottom-right cell being the one that shows
   it is a hint: it may simply be the last cell in the draw order.
2. **The synthetic-tap path.** `queueButtonTap` schedules a press/release pair
   inside `update()`; a tap whose release lands in a later frame than the next
   press begins would overlap two highlights.

Note this is a PAD-OVERLAY bug, not a firmware one -- the device has physical
buttons and nothing to repaint. Reproduce with `CROSSPOINT_SIM_TAP_PAD` and
`CROSSPOINT_SIM_LOG_PRESENTS=1`, looking for a present whose pad state does not
match the button that caused it.

## Checked and CLEAN, 2026-08-28 -- the state model is not the cause

Read rather than reproduced, so this narrows the search rather than closing it.
Recorded because the next pass would otherwise start here too.

**`PadCore` (ios/PadCore.h, ios/PadCore.cpp) does not carry a stale press.**
Candidate 1 above was a pressed-index cleared later than the logical state, and
it is not what this model does:

* `isDown(slot)` reads `down_[slot]` directly -- there is no separate "drawn"
  state that could lag it, so the painter cannot show a press the model has
  released;
* `slotHeldBy()` requires `down_[i] && finger_[i] == fingerId`, so a slot is
  never attributed to a finger that is not holding it. This also neutralises the
  one thing that looked dangerous: `finger_` initialises to 0, and if SDL ever
  delivered fingerID 0 a match on the id alone would have found the first
  UNPRESSED slot. The `down_[i]` conjunct makes that unreachable;
* `fingerUp()` releases exactly the slot that finger held and returns no action
  when it held none, so a lift cannot release someone else's press;
* `fingerLeftSlot()` and `reset()` both clear unconditionally, and `reset()` is
  documented idempotent.

So a press cannot outlive its finger in the model. **What is NOT yet checked**
is the adapter above it -- which slot the hit test returns, and whether the
fused-pair painter can shade a half that is not down. That painter has had
exactly this class of defect before: the `pairs` table once declared three rows
while listing two, and the zero-initialised third row painted a phantom capsule
over the Back half of the left rocker. The bottom-right cell being the one that
shows it is consistent with an index or bounds slip of the same kind, and that
is where the next pass should look.

## A real defect found in the painter, 2026-08-28 -- not confirmed as the cause

The narrowing above pointed at the fused-pair painter, and there is something
wrong there: **the pair loop had no retired-slot guard, and the single-button
loop always has.**

```c
if (b.rect.w <= 0.0f || b.rect.h <= 0.0f) continue;   // single loop, always present
```

A retired slot has a ZERO rect -- the side-rocker ruling retires the pair on
X4 (`hasEdgeSideButtons()` is false there), and `g_padLaidOut` is cleared on
every window size change, so the rects are momentarily zero after a resize too.
The single loop skipped those. The pair loop went on to compute a union and two
inner halves from them, and on a zero rect `a.w - hairline` is NEGATIVE, as is
`a.h - 2 * hairline`. So what reached `SDL_RenderFillRect` was a negative-extent
rect -- and `fillHalf`'s `patch` carried a POSITIVE width beside a negative
height, at the origin corner of the pad.

Guarded now, with the same compare the other loop uses.

**Whether this is S-026 is UNPROVEN and the entry should not be closed on it.**
The report is a flash on the bottom-right rocker following a press elsewhere,
and this is a degenerate-geometry fill, so the shapes are not obviously the
same. What makes it worth fixing anyway: it is a defect on its own terms, it
sits in the exact code that has already shipped one phantom capsule (the
pairs-table row that declared three while listing two), and the fix costs a
compare.

Still not reproduced: no headless path produces the report, since
`CROSSPOINT_SIM_TAP_PAD` synthesises one tap at a time and the report is about
a press that follows another.

## The hit test WAS the next suspect, and it had a real defect, 2026-08-28

Checked the suspect named above rather than leaving it, and found a mechanism
that fits the report:

**`padHitTest()` walked stale geometry after a resize.** It returns the first
slot whose rect contains the point, with no check that the geometry is current
-- and `SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED` cleared `g_padLaidOut` **without
touching the rects**. The relayout that flag schedules happens in the PAINT
path, while finger events arrive through `HalGPIO::update` on a different
cadence. So between the resize and the next present, a touch hit-tested against
the OLD rects: it pressed whichever button used to be at that point, and the
painter then shaded THAT button rather than the one under the finger.

A press appearing on a control the finger is not on is exactly the report.

**It also links this entry to S-027.** A video call resizes the window twice --
banner in, banner out -- so "the screen went blank coming back from a call" and
"a rocker flashes when I press something else" may be one event observed twice.

**Fixed by zeroing the rects with the flag**, so `padHitTest` answers `kNoSlot`
and a tap during the resize window does NOTHING. That is the right failure:
pressing the wrong button is worse than dropping one tap in a window that lasts
a frame. Only the SIZE-change site invalidates geometry -- the zen toggle and
the band change also clear `g_padLaidOut` but do not move the output, so their
rects stay valid and their taps must keep working.

**Still unproven as the cause.** Nothing here reproduces it: the synthetic tap
path lays the pad out first, so it never sees the stale window. What is certain
is that the old behaviour was wrong, and that this is the second defect found in
this code path today -- the painter's missing retired-slot guard was the first.

Moved out of OPEN 2026-09-04: the owner dropped the chase on 2026-08-28 and the two candidate fixes have shipped in every build since; never re-reported.

### [S-035] A stale beam-sweep progress can collapse the zen panel and pad to a sliver on the FIRST content change of a session — root-caused, reproduced, FIXED
**severity: high (visible, screen-wide, matches a repeated owner report) · scope: ios present pipeline (`src/HalDisplay.cpp`'s `presentIfNeeded`) · reported 2026-09-01, root-caused and reproduced same session, a first fix attempt tried and reverted (made it worse), a second fix landed and proven the same session**

Owner, verbatim: *"bug after shaking for going to zen mode then selecting next
book on home screen does the buggy tall redraw flash still"* — corrected the
same session to: *"not opening a book on home, selecting the next one"*. So the
sequence is HOME → shake toggles zen ON (not entering a reader at any point) →
press RIGHT to move the Home selection to the next item, staying on Home → a
badly laid out frame reaches the glass. Asked whether [S-034]'s fix (below)
covers this path.

**It does not, and cannot — proven by reading, not assumed.** `HalGPIO::
publishReaderTextInsets` has exactly one call site, inside `EpubReaderActivity`'s
render (`../crosspoint-reader/src/activities/reader/EpubReaderActivity.cpp:1051`),
and this sequence never enters a reader at all. `pollReaderInsets()`
(`ios/CrossPointIOSShim.cpp:1608`) returns on its very first line every single
time on Home (`if (!SimulatorOverlay::readerTextInsetsPx(...)) return;`), so
S-034's packed-atomic fix has literally nothing to read a torn value FROM on
this path. This is a different mechanism — the eighth in `docs/zen-mode.md`'s
catalog — and it was found by reproducing the owner's corrected sequence rather
than by re-patching S-034.

**Checked and found CLEAN, so not re-investigated:**
- `layoutPadTablet` (`ios/CrossPointIOSShim.cpp:429`) — the ONLY layout
  function ever invoked for `s_isPad` (`layoutPad` returns into it before
  reaching any of the phone's `g_zenRowTopPx`/shift code) — reads no
  reader-insets channel at all; its placement is a pure function of the window
  size and safe area. Confirmed by log: the panel rect (`1056x1584 at
  504,389`) was byte-identical before and after a REAL zen OFF→ON toggle
  (`defaults write ... zenModeEnabled -bool true`, picked up by
  `pollZenMode()`'s `ApplyToLive` branch) in this session's own testing on the
  iPad Pro 13 simulator.
- A plain Home selection-repaint (the RIGHT press) does not re-invoke
  `layoutPad`/`layoutPadTablet` at all: `paintPad`'s relayout gate
  (`ios/CrossPointIOSShim.cpp` ~:2590, `if (!g_padLaidOut || panelBottom !=
  s_layoutPanelBottom || ...)`) never re-opens across the press in any capture
  taken this session — no new `[pad] tablet...` / `[zen] panel...` /
  `[bezel]` log line follows it. So [S-020]'s phone-only shift block, and the
  whole zen-band-placement system, is not implicated in this defect at all;
  the bug is downstream of the pad/band layout, in the shared present
  pipeline both platforms share.

**The mechanism, proven by temporary instrumentation (added, used, then
reverted — `git diff --stat src/HalDisplay.cpp` is clean at the time of
filing).** `beamStartedAt`/`beamProgress`/`beamSweeping`
(`src/HalDisplay.cpp` ~:3320, inside `presentIfNeeded`) are computed ONCE,
early in the function, from `SDL_GetTicks() - beamStartedAt` against the
shipped 55 ms beam duration. Between that computation and the point where
`beamProgress` is actually used to build the sweep's clip rect, the function
does an EXPENSIVE, SYNCHRONOUS field rebuild —
`simsheet::ensureLetterpressField()` — which is a cache MISS (240-265 ms,
measured by its own `"... in NNN.N ms"` self-log) on the first real content
change of a session, because nothing has needed the letterpress field before
that point. A diagnostic line placed immediately after `beamSweeping` is
computed logged `beamProgress=0.073` (7.3%) on the SAME `presentIfNeeded()`
call whose own terminal `[present]` log fired **305 ms later**, with a
`[letterpress] field ... in 265.1 ms` line sitting between the two — five
times the entire 55 ms beam budget elapses between sampling `beamProgress`
and drawing with it.

The clip built from that stale progress (`swept = sweep.h * beamProgress`,
where on the manual-placement/iPad path `sweep = {0, 0, gw, gh}` — the WHOLE
OUTPUT, not just the panel rect) comes out far shorter than the panel's own
top offset: measured clip heights of 127-350 px against a panel that starts
at device-pixel row 389. So the panel, and its letterpress pass, draw
**nothing at all** for that present — only the zen top bezel band (drawn
separately, in the reserved band above the panel, and NOT gated on this same
clip) falls inside the swept region, which is the horizontal cream-colored
sliver visible in every repro screenshot, floating over an otherwise blank
field.

**The un-swept region: FOUND and fixed 2026-09-01 — the glass held a BLACK
frame, captured on the session's first present, and nothing re-captured it.**
Instrumented on the pre-fix tree with an 8-band luma profile read back after
every stage of the present (5 runs, 5/5 identical): present #1 of a session
reads `after-clear 244…`, `after-panel 228 206 204 234 245…` (panel drawn,
letterboxed through logical presentation because the harness has not set the
bottom inset yet), then `after-overlay 0 0 0 0 0 0 0 0`. The iOS overlay's zen
painter fills BLACK from `line` to the bottom of the screen, and on that first
present `g_zenPanel` is `0x0 at 0,0`, `panelBottomPx()` is 0 and
`g_zenRowTopPx` is 0 (logged: `[s035] zen paint: q=0,0 0x0 rowTop=0 line=0
… panelBottom=0`), so `line = 0` and the fill is the whole glass.
`captureGlass` then reads that frame back — `capture … 0 0 0 0 0 0 0 0` —
and it is the only capture the gate allows: the pad's own layout inside that
present calls `setBottomInset` → `requestPresent`, present #2 lands ~100–180 ms
later with the correct frame (`after-overlay 0 97 107 124 125 91 0 0`), but it
carries the SAME `pixelBufSeq`, and the capture gate was `glassSeq !=
presentedSeq`. So the first content change of every session drew
`glassPrevTexture` full-screen exactly as instrumented (`ok=1`, dimensions
matching) and it was black — `after-glass 0 0 0 0 0 0 0 0` on the sweep
present, before any later pass ran, which rules candidate (b) out. The one
white repro was the same hole with a different first frame. Candidate (a) was
right in effect and wrong in mechanism: the readback was neither incomplete
nor wrongly scoped; it was a correct readback of a frame that the harness
composes black.

The fix is the capture gate, not the harness: the glass has to be the LAST
composed picture, and the overlay repaints the composition without the page
moving (a keyboard, a zen toggle, a pad relayout — the first frame is only the
case that made it visible). `src/GlassCapture.h` decides now, purely:
capture on a new seq, a stale size, no picture, OR a **request generation**
that moved — `glassDirtyGen`, bumped by every present request except the
sweep's, the trail's and the page fade's self-driving re-arms, and sampled at
the TOP of the present so a request made from inside the overlay's layout is
consumed by the NEXT present, not this one. Verified on the same iPad recipe
with `CROSSPOINT_SIM_LOG_TIMING=1` + `LOG_SCREEN=1`: present #2 now reports
`glass BUILD 96 ms` (the re-capture), and the first sweep present reads back
`whole 63.56 page 110.59` — the previous frame's exact figures — where the
pre-fix tree read `whole 0.00`. Cost: one readback per overlay-driven present
(96–125 ms at 2064×2752 on the iPad, measured 2–6% of a page turn on a
phone); trail-decay presents are unaffected because they do not move the
generation. `tests/glass_capture_test.cpp` pins the seq-only gate as wrong on
exactly this two-present case.

**The black first frame itself, ruled out 2026-09-02** (owner picked the fix
over leaving it). The zen painter now draws nothing while `g_zenPanel` has no
geometry (`ios/CrossPointIOSShim.cpp`, the guard at the top of the zen block),
so the session's first present is the paper-toned clear instead of black.
Same iPad recipe: `[screen] #1 whole 227.15` where it read `0.00`; frames
#2–#5 identical to the pre-guard run in both `[present]` (232.2 → 237.0) and
`[screen]` (63.56/110.59 → 64.79/113.04) figures, so nothing past the first
frame moved. The top bezel needed no guard — `paintTopBezel` already returns
on an unpublished band height. UNCONFIRMED on device.

**A first fix was attempted and reverted — it did not help, and it introduced
a worse bug of its own.** Re-deriving `beamProgress`/`beamSweeping` from a
fresh `SDL_GetTicks()` immediately after the letterpress rebuild, before its
later uses (the chrome/pad sweep clip, the glass-capture gate), did not
resolve the symptom across repeated testing. Worse: the panel's own clip,
set earlier using the ORIGINAL `beamSweeping=true`, is only CLEARED later
behind `if (beamSweeping)` (`src/HalDisplay.cpp` ~:3471); recomputing
`beamSweeping` to `false` in between desyncs that set/clear pairing, so the
stale clip rect is left permanently active for the rest of the frame instead
of being cleared at all — a regression, not a fix. Reverted in full rather
than shipped partially-working.

**Reproduction — external, OS-level, independent of the app's own pixel
readback (`xcrun simctl io screenshot`, not the in-app BMP capture, so the
finding does not depend on trusting the code under investigation).** On the
booted iPad Pro 13 simulator (`0E5288ED-A466-4750-9FDC-BEA83FE9531A`,
`com.natebunnyfield.crosspoint.x3`, built from this session's HEAD):

```bash
xcrun simctl spawn "$UDID" defaults write "$BUNDLE" zenModeEnabled -bool true
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='200:QTAP:BACK:2500;3550:QTAP:RIGHT' \
  xcrun simctl launch "$UDID" "$BUNDLE"
sleep 5.5
xcrun simctl io "$UDID" screenshot out.png
```

`QTAP:BACK:2500` lands on Home (no reader ever entered — confirmed by the
`[ACT] Entering activity:` log, which shows only `Boot` then `Home`);
`QTAP:RIGHT` moves the Home selection from the single recent-book cover to
the "Recent Books" menu row, an ordinary content-only repaint. Across roughly
a dozen raw attempts this session (some with diagnostics attached, which
measurably changes the odds without reliably preventing it — the race still
fired 3 of 8 attempts with `CROSSPOINT_SIM_LOG_PRESENTS=1` and `--console`
attached), a majority showed the collapsed sliver; a matched zen-OFF control
of the identical sequence, and a matched zen-ON control with NO `RIGHT` press,
both rendered correctly every time — isolating the trigger to "zen on, a
genuine Home content change, zen's letterpress field not yet built this
session," not to zen or to Home individually. A proper controlled hit-rate
was not established in the time available; this is reported as a real,
reproduced, non-deterministic race, not a precisely quantified one.

**FIXED, same day — by moving the arm point, not by re-sampling.** The
reverted attempt above kept `beamStartedAt`'s write where it was (early,
before `ensureLetterpressField()`'s rebuild) and added a SECOND read of
`SDL_GetTicks()` after the rebuild, which is what desynced the clip's
set/clear pairing. The fix instead moves the ONE write, so there is still
only one read of `beamProgress` and no pairing to desync:

- **What changed to earn "READY to sweep."** `src/HalDisplay.cpp:2875-2899`
  (the `contentChanged` block, under `pixelBufMutex`) no longer writes
  `beamStartedAt` — it now sets a local `beamShouldArm` bool under the exact
  same `contentChanged && glassHasPicture && !reconvertOnly` condition
  (S-031's reconvert exception untouched). `src/HalDisplay.cpp:3311-3331`
  (immediately before `beamProgress` is first computed, and immediately
  after `fields.letterpress` — `:3282` — is already known) now does two
  things in order: `if (fields.letterpress) simsheet::ensureLetterpressField();`
  as a prewarm, THEN `if (beamShouldArm) beamStartedAt = SDL_GetTicks();`.
  The 240-265 ms cache-miss rebuild this entry is about now lands BEFORE the
  arm, not after it — so `beamProgress`'s first (and only) read is fresh
  against a clock that has already paid for the rebuild, and the later call
  at the original draw site (`:3448` area, unchanged) is a cache hit that
  costs nothing.
- **Why this dodges the reverted attempt's trap.** There is exactly one
  write site and one read site for `beamStartedAt`/`beamProgress` in the
  frame that arms a sweep, same as before the whole investigation — the fix
  is WHEN the one write happens, not an extra one. The panel's clip
  set-then-clear (`:3382` / `:3434`, both still gated on the same
  `beamSweeping` computed once at `:3331`) never sees two different values
  of `beamSweeping` within one frame, so nothing to desync.
- **Reproduced pre-fix, absent post-fix, same session, same recipe.**
  Stashing only `src/HalDisplay.cpp` back to the pre-fix tree and rebuilding
  reproduced the exact symptom this entry describes — black screen plus the
  cream bezel sliver — in 6 of 10 runs of the BUGS.md recipe above
  (`xcrun simctl io screenshot`, matched `zenModeEnabled -bool true`, same
  UDID/bundle). With the fix restored and rebuilt, 20 consecutive runs of
  the identical recipe (two batches, 8 then 12) all rendered the correct Home
  menu — no sliver, no black field. `log stream` on one of the clean runs
  caught the exact scenario this entry names: present #3 (the RIGHT press)
  logged `panel BUILD 243.21` inside a 290 ms present, i.e. the letterpress
  rebuild really did cost ~243 ms on this exact frame, and the frame still
  rendered correctly — proving the fix works BECAUSE of the reordering, not
  because the expensive rebuild happened not to fire that run.
- **The sweep still sweeps.** The same log shows present #3 (243 ms rebuild,
  arm) followed immediately by presents #4-#6 at 8.0/2.6/0.7 ms — fast,
  cache-hit continuations of the same sweep — then present #7 does the
  deferred glass capture (`glass BUILD 67.39`, correctly held back until
  `beamSweeping` goes false). This is the sweep completing its 55 ms reveal
  over several quick frames, not a sweep that got silently disabled to make
  the symptom go away.
- **Settled frame proven byte-identical pre/post fix, on the desktop
  canary, per the 2026-08-25 discipline — twice, having caught and rejected
  a false positive first.** A first attempt (scripted `QTAP:RIGHT` at a
  fixed wall-clock offset) produced DIFFERENT md5s pre/post fix, but the
  `[ACT]` log showed the two builds had landed on different activities
  (`EpubReader` "End of book" vs. `Home` menu) — an artifact of the two
  builds' different per-frame costs shifting where a wall-clock-scheduled
  `QTAP` lands, not a rendering difference. Re-run with `[ACT]`-verified
  matching navigation and a wider timing margin: no-beam settle
  (`CROSSPOINT_SIM_BEAM_MS=0`) is byte-identical pre/post fix
  (`777aaf3d40af4cb270f25fc85e48752e`); beam-on settle
  (`CROSSPOINT_SIM_BEAM_MS=55`, same navigation, `[ACT]` chains matching) is
  also byte-identical pre/post fix (`6cb8abad0dd0e4664a455bc37a3cc916`).
  Lesson for the next person timing a cross-build comparison with
  `CROSSPOINT_SIM_INPUT_SCRIPT`: verify `[ACT] Entering activity:` matches
  before trusting an md5 diff between two builds of differing speed.
- **`tests/run_all.sh`: 72 passed, 0 skipped**, matching baseline (touching
  the firmware repo's `fs_/.crosspoint/` during the above A/B testing
  transiently broke `test_text_entry` and `test_note_editor_repaint` to SKIP
  by deleting `settings.json`; regenerated by one simulator run that reaches
  Settings and presses Back, which is the firmware's own save path — not a
  code issue, noted here so a future session doesn't chase it as one).
- **The second half (black un-swept region) was chased and fixed
  2026-09-01** — see the paragraph above the reverted first attempt. It was
  never unreachable: with the arming fix alone, the first sweep present of
  every session still drew its un-swept region from a black glass for the
  length of the sweep (55 ms shipped); the sliver made it visible, the
  arming fix made it brief. `src/GlassCapture.h`, `tests/glass_capture_test.cpp`.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; shipped in builds 164, 166 and 167 (`f0bdfaa`, `3bda355`, `a8dea75`, from `git tag --contains`; the entry names no build).

### [S-030] Booting while the phone is dark came up light — FIXED 2026-08-28, unconfirmed on device
**severity: medium (visible every launch) · scope: iOS appearance · reported and fixed 2026-08-28**

Owner: *"when booted into system dark mode, be in dark mode."*

`g_seedDarkFromSystem = firstEverLaunch()` — the system appearance wrote into
`SETTINGS.darkMode` only on the **first launch ever**, and after that only when
the appearance changed **while the app was running**. `pollAppearance`
initialises its `s_lastSystem` from the system itself, so on the first tick of
any later launch nothing has changed and the stored setting wins.

Install in light, switch the phone to dark with the app closed, reopen: light.

**This is not a careless rule — it is the fix for the opposite bug**, and that
is why the repair had to be more than deleting it. Seeding from the system on
every launch used to overwrite the in-app Dark Mode toggle, so the control did
not survive a relaunch; the comment above `applyTheme` records that report in
the owner's words. Neither "always seed" nor "seed once" satisfies both, because
both answer from the CURRENT system alone.

The question they cannot answer is **did the system change since we last
looked**, and that needs the previous answer remembered across launches,
separately from the owner's setting. `CrossPointPrefs_lastSeenSystemDark` now
persists it, `ios/AppearanceSeed.h` holds the rule, and the running-app poll
keeps it in step so the next launch never compares against a stale answer.

Two details that are easy to get wrong and are pinned:

* **An install that predates this rule does NOT seed.** Nothing was recorded, so
  a stored `darkMode` may be a deliberate choice, and seeding over it on the
  upgrade launch would be the toggle-overwrite bug reintroduced one release
  later. The value is recorded on that launch anyway, so the NEXT change is
  caught.
* **The remembered value is written on every launch, seeded or not.** Writing it
  only when seeding leaves the case above stuck at "never recorded" for ever.

`lastSeenSystemDark` is deliberately absent from the defaults registration:
"never recorded" has to be distinguishable from "recorded as light", and a
registration-domain value makes `-integerForKey:` answer 0 for both. Read with
`objectForKey:` for the same reason.

Mutation-verified: making the upgrade launch seed fails two named cases, and
never following a change made while closed fails two more.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; shipped in build-158 (`db03944`, from `git tag --contains`; the entry names no build).

### [S-029] A textless page kills hands-free read-aloud — FIXED 2026-08-28, unconfirmed on device
**severity: high (the feature does not start) · scope: read-aloud · found and fixed 2026-08-28**

Owner: *"check that tts turns the page as expected, not repeat or stall."* This
is the stall, and it fires on the FIRST page of every book.

`ReadAloudCore.cpp` collapsed two different things into one branch:
`if (page.cleared || page.utf8.empty())` set state `Off` and returned no
`StartUtterance` and no `TurnPageForward`. But `cleared` means *the reader
exited*, while an empty page means *there is nothing here to read* — and a book
opens on a cover wrapper that captures no words. Measured on the book the iOS
app itself seeds: the first publish of a fresh boot is `bytes=0 words=0`.

**So with read-aloud enabled, opening a book left speech dead until a page was
turned by hand.** Not a rare path — it is every book, every time.

The same conflation had already been fixed one layer up and the core never got
the repair: `CrossPointReadAloud.mm:745` computes a title-and-author fallback
for exactly this case, with a comment citing the 2026-08-23 ruling, and routes
it only to VoiceOver.

**Owner ruled: skip it silently.** A textless page now emits
`TurnPageForward`, so hands-free reading walks past covers and plates without a
word. The bound (`kMaxConsecutiveSkips`) stops a run of illustrations turning
for ever, and it **latches** — cleared only by a page with words, never at the
limit. Resetting it at the limit made the counter oscillate, twelve turns then
one stop then twelve more, which is the runaway it exists to prevent wearing a
bound's clothes; the 40-blank-page test caught that.

End of book cannot loop here: that screen returns before `renderContents` and
publishes nothing at all rather than publishing an empty page.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; shipped in build-158 (`6aae088`, from `git tag --contains`; the entry names no build).

### [S-028] Read-aloud restarts the page from its first word on any re-render — FIXED 2026-08-28, unconfirmed on device
**severity: high (audible, on an ordinary action) · scope: read-aloud · found and fixed 2026-08-28**

The repeat half of the same owner report. `ReadAloudCore::pageArrived` never
compared the incoming page to the one it held, so a byte-identical republish
was treated as a new page: stop, clear the highlight, start again at offset 0.

The reader republishes without moving. `ActivityManager.cpp:143` requests an
update on EVERY subactivity pop — its comment says so — which re-renders and
re-captures. Measured across one chapter-selection round trip: publishes #3 and
#4 byte-identical.

**So opening chapter selection and coming back re-spoke the page from its first
word.** Also reachable with no button press at all: `applyTheme()` and
`applyPanel()` both end in `crosspointRequestRender()`, so a system light/dark
switch mid-page forces the same republish — that path is code-read, not run.

Fixed by holding the page's text and returning NO actions when an identical
page arrives while Speaking or Paused. Rects are replaced rather than kept: the
text identifies the page, while the geometry can legitimately move under it (a
palette change re-dithers the same layout). Different text is still a new page
and still restarts.

**`.claude/PLAN-tts-read-aloud.md` records "a same-page re-render restarts its
speech" as an ACCEPTED NON-GOAL.** That decision was made without knowing it
fires on an ordinary chapter-select round trip; the measurement is why it was
relitigated.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; shipped in build-158 (`6aae088`, from `git tag --contains`; the entry names no build).

### [S-027] Returning from a video call leaves the screen blank for a long time — FIXED 2026-08-28, unconfirmed on device
**severity: high (looks like a hang) · scope: iOS present · filed 2026-08-27 from the device · fixed 2026-08-28**

Owner: *"while on a video call, returning to app takes a while to get out of
blank screen."*

Unverified mechanism, written down so the next session starts from a hypothesis
rather than from zero. An e-ink firmware presents RARELY — that is the whole
shape of this codebase — so anything that loses the drawable and then waits for
the firmware's next natural render will show blank for as long as the reader
happens to sit still, which on a page of text is unbounded. A video call is the
strong case for it: iOS resizes for the call banner, and the app is a
`SDL_uikitmetalview` whose layer is re-created.

Where to look first, in order:
- whether `UIApplicationDidBecomeActiveNotification` (or SDL's
  `SDL_EVENT_WILL_ENTER_FOREGROUND` / `SDL_EVENT_DID_ENTER_FOREGROUND`) reaches
  anything that calls `SimulatorOverlay::requestPresent()`. This repo has been
  bitten by exactly this three times already — the keyboard height, the palette
  change, and the appearance flip all stored new state and presented nothing.
- whether the panel texture survives the layer re-creation, or whether it needs
  re-uploading from `pixelBuf` rather than re-presenting a dead texture.
- the call banner changes the safe-area insets, so the zen/pad layout recomputes;
  if that path early-returns on an unchanged inset it may also skip the present.

**Do not fix this by polling.** The fix is a present on the foreground edge, not
a timer.

## The filed hypothesis was WRONG, and the right answer was next door

The guess above — that nothing calls `requestPresent()` on the foreground edge —
is false. `SDL_EVENT_DID_ENTER_FOREGROUND` has both a present AND a
**settle window**: `repaintAfterForeground()` re-asks every 200 ms for 2 s,
with constants measured against timed screenshots, because a present issued
while the surface is still settling returns success and is then DISCARDED on
Metal. That reasoning was already written down; what was missing is who else
needs it.

**A video call never backgrounds the app.** The call banner RESIZES the window —
once when it appears, once when it goes — and `SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED`
asked for exactly ONE present each time. One present is the thing the
foreground path already knew was not enough. An app that draws only when the
panel changes has no second frame coming, so the discarded frame is the only
frame there was, and the stale or blank image stood until something else forced
a redraw.

So: same failure, same fix, previously reachable from only one of its two
causes. Both now call `armSettleRepaint()`. The budget is reused rather than
re-derived — it was measured for the foreground case and the size case has no
measurements of its own, so inventing a second number would be inventing device
feel.

Device-confirm only: no host reproduces a Metal surface discarding a present.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; shipped in builds 154 and 156 (`197bd7e`, `2bd00d2`, from `git tag --contains`; the entry names no build).

### [S-016] The whole screen flashes on some CRT palettes — FIXED 2026-08-19, unconfirmed on the phone
**severity: medium · scope: ios display · reported 2026-08-19**

Owner, from the phone: "there's still a bug with the full screen flashing on
some crts." SOME, not all — which was the whole clue. Narrowed by the owner on
2026-08-19 to "the long persistence ones", and that identifies the mechanism
exactly.

**CAUSE: the DEPOSIT into the accumulator was `SDL_BLENDMODE_ADD`.**

The composite to screen was changed to MAXIMUM back when the page-turn flash was
fixed, with an explicit argument — a pixel lit in two frames is one phosphor
being re-excited, not two emitters stacked, so it cannot exceed full emission.
That argument applies word for word to the deposit and was never carried across.
The deposit kept summing, unbounded.

The bound that mattered was the DECAY, which is why only long trails showed it.
A short trail drains the buffer to near black before the next deposit lands, so
the sum never builds. At P7's 2828 ms with content changing every 100 ms, `keep`
is 10^(-100/2828) = 0.92 per frame and the running sum tends toward roughly 12x
a single page; at P45's 283 ms it settles near 1.8x.

**Fixed** by depositing with the same saturating MAXIMUM blend, with the same
ADD-at-reduced-strength fallback the composite uses. Measured on P7 with content
changing every 200 ms, before and after, same script and same binary otherwise:

| | peak | mean |
|---|---|---|
| ADD (before) | 35.53 | 23.09 |
| MAXIMUM (after) | 31.04 | 17.85 |

Peak down 12.6%, mean down 22.7%. The desktop understates it — it cannot drive
content changes as fast as a finger can, and the theoretical 12x needs sustained
rapid change — so treat those figures as the direction confirmed rather than the
magnitude.

**UNCONFIRMED on the phone.** The flash is a thing the owner sees; nothing here
has seen it.

**Why the first hunt missed it, kept because the metric was the mistake.** With the phone's own settings forced by env — glow at the preset's
trail, beam 67 ms, page fade 5 min at Dim, grain 1x Vignette+Mottled — across
P45, P19, P7, P22G and P11:

| | |
|---|---|
| worst single-frame excursion above BOTH neighbours | **1.26 levels** (P45) |
| the same with glow and beam off | 0.00 |

A first pass reported ratios of 1.6x to 2.8x and that was a MEASUREMENT ERROR:
min/max across a run spans different SCREENS, and Home with book covers is
simply brighter than a reader page. A flash is a frame brighter than the ones
either side of it, so the excursion above both neighbours is the metric, and by
it nothing off-phone flashes.

**Why the desktop cannot show it.** At render scale 3 with
`CROSSPOINT_SIM_LOG_PRESENTS=1`, every present logs `frame from B` — the BASE
pass — and `CROSSPOINT_SIM_LOG_AA=1` prints nothing at all. The grayscale
compose never runs, so the two-pass paint that present coalescing exists to
merge does not happen here. The flash this project already fixed once was
exactly a base-then-compose pair reaching the screen; if this is a relative, the
desktop is blind to it by construction. Same lesson as the last three flash
hunts — the instrument has to overlap the shipped path.

**What would crack it, cheapest first: which palettes, and on what action.** If
it is the long-trail rows it is the accumulator; if it is the pale-ground rows
it is the `panelIsDarkGround()` gate that disables the trail; if it is the
cascades (P7, P14, P17) it is the tail colour multiply. Those are three
different pieces of code and the report as it stands fits all three.

Moved to FIXED 2026-09-04 under the 2026-09-02 ruling that silence closes a shipped fix; shipped in build-102 (`ccf9c21`, from `git tag --contains`; the entry names no build).

### [S-023] Speak Screen goes permanently deaf at the first reboot of a session — FIXED 2026-08-26
**severity: high · scope: ios read-aloud / accessibility · owner report from the phone 2026-08-26**

Owner, verbatim: *"'no speakable content could be found on the screen' error is
happening again"*, then the correction that dated it: *"it was broken before
today."* He sent his device's `a11y.log`, which is decisive and rules out the
2026-08-09 shape (iOS never asking) outright:

```
[    87.0] 69 word rects -> 14 line elements; first "summer and never got home."
[   112.2] 43 word rects -> 9 line elements; first "Chapter 1 — Port Talon"
[  1401.9] page cleared (reader left)
[  3738.5] CHAIN wants=1 page=0B rects=0 fb=0B geo=1 view=1 inWindow=1 elements=0
[  3746.0] TEXTINPUT scroll next -> page turn
[  3748.5] CHAIN wants=1 page=0B rects=0 fb=0B ... elements=0
```

iOS **is** asking (`scroll next` fired and turned the page), the view is
installed and in the window — the app simply has nothing, on both sources, from
t=3738 to the end of the session, on a book that was healthy at t=112.

**What broke.** One flag with two writers that had drifted apart, across a
boundary that resets one of them and not the other.

`ios/CrossPointReadAloud.mm` seeded the firmware's capture flag in **two**
places. `CrossPointReadAloud_begin()` seeded it from
`CrossPointPrefs_readAloudEnabled()`, which was right until capture became
unconditional on the phone (build 42, the fix for the *previous* incarnation of
this same message) and was never updated with it — a Speak Screen user leaves
the Read Aloud (Experimental) toggle OFF, so begin() seeded **false** on every
boot. `CrossPointReadAloud_perFrame()` then corrected it to true, but only on
the edge `g_lastCaptureWanted != 1`.

On the first boot that edge fires and the chain is healthy. The iOS reboot is a
`longjmp` back into `setup()` in the same process:

| | what happens |
|---|---|
| boot 1 | begin() seeds `false`; perFrame's edge fires and sets it TRUE. Healthy. |
| REBOOT | `simreset::runAll()` → `ReadAloudChannel::resetForReboot()`, which deliberately leaves `wanted_` alone ("the consumer re-seeds it"). Every static in the adapter survives — `g_lastCaptureWanted` at 1. |
| boot 2 | `CrossPointHarness_begin()` → `CrossPointReadAloud_begin()` seeds `false` **again**. perFrame's edge is already satisfied, so nothing ever sets it back. |

`HalGPIO::readAloudCaptureWanted()` is then false for the life of the process,
`EpubReaderActivity::captureReadAloudPage` returns at its first line, and
nothing is ever published — which is also why `fb=0B`: the textless-page
fallback (`g_fallbackUtf8`) is only computed inside the drain's `if (got)`
block, so a channel that never delivers starves the substitute as well. One
root, both halves of his log.

Every file transfer, every font download and every sleep/wake crosses that
boundary, so the phone reaches boot 2 in the course of ordinary use. His gap was
39 minutes.

**Reproduced and fixed, both arms measured on an iPhone Air simulator
(`crosspoint-x3-air`), 2026-08-26**, same script both times — open the book,
turn pages, POWER-hold to sleep, POWER-tap to wake (the longjmp), turn pages
again:

| | before the reboot | `[power] longjmp reboot` | after |
|---|---|---|---|
| pre-fix build | `page=746B rects=151`, `790B/165`, `780B/156` | crossed | `page=0B rects=0 fb=0B` at +0.0 s, +5 s, +10 s, +15 s, across two page turns |
| fixed build | `page=812B rects=158 elements=22` | crossed | `page=812B rects=158 elements=22`, then `746B/151` after a turn |

The `[READALOUD] page capture wanted (always, on iOS)` line is its own
discriminator: it prints **once** in the pre-fix run and **twice** — once per
boot — in the fixed one.

**The fix, and why it is two changes rather than one.** Registering the static
would have fixed the instance; both were taken because the class is what keeps
coming back.

* `CrossPointReadAloud_begin()` seeds `true` unconditionally, joining the
  `g_last*` re-arm list that `g_lastEnabled` and `g_lastRatePercent` were
  already in. It must stay in begin() rather than moving to a reset registrar:
  begin() runs *before the first `loop()`*, and a book resumed at boot renders
  its first page inside that iteration.
* `perFrame` pushes the flag **every frame** instead of behind the edge. The
  setter is one atomic store (`ReadAloudChannel::setWanted`), so the guard was
  buying nothing measurable and cost this; the static now throttles only the
  log.

**Held by `tests/readaloud_reboot_seed_test.py`**, which fails on all three of
its properties against the pre-fix file. Its third assertion is the general one:
every `int g_last* = -1;` edge cache declared in the adapter must be re-armed in
`begin()`. Source-level because the live check needs UIKit, a booted phone and a
reboot mid-run — see `docs/speak-screen-chain.md` for that run.

**Audited for siblings and found clean.** Nine other edge-cached statics cross
the same boundary (`g_appliedDark`/`Outline`/`Fill`, `pollBeamPaint`,
`pollPageFade`, `pollPanelGlow`, `pollLetterpress`, `pollPaperTooth`,
`pollScanlines`). None has this bug, and the reason is precise rather than
lucky: the read-aloud flag is the only one whose *mirrored state is actively
re-written on the far side of the boundary*. `gDisplayRebootReset` does not
touch the surface dials — they are atomics in `HalDisplay` that survive the
longjmp — so a stale poll edge is suppressing a push of a value that is already
applied. `applyTheme()` writes `g_appliedDark` unconditionally on every
`CrossPointHarness_begin()`, so the appearance edge is re-armed by construction.
`fontFamilyStepChannel` has no wanted flag and no consumer-side edge at all.
**A stale edge is only a bug where something else resets what it mirrors** — that
is the shape to look for, not the static by itself.

### [S-020] A gun moved in dark mode throws away the light page's chosen ink — FIXED 2026-08-23
**severity: high · scope: ios palette sourcing · owner P1 from the phone 2026-08-23**

Owner, verbatim: *"p1 bug: ink is not being picked up. recreate, review and fix
sourcing for light and dark to be more accurate on load, switch etc."*

**What broke.** The 2026-08-22 doctrine split gave each appearance its own
editor — light is paper and ink (`ios/CrossPointLightInkPicker.mm`), dark is the
CRT (`ios/CrossPointPaletteMixer.mm`), and the page-color chip branches on the
live appearance — historical citation only, `ios/CrossPointIOSShim.cpp:2555`
no longer shows this: the page-color chip itself was removed from the pad on
2026-08-24 (the day after this entry was fixed), so there is no current line to
re-point this at. They share ONE store: a
preset integer plus four hex fields, two per appearance. The mixer was left
`untouched` by that split — `docs/light-ink-picker.md` says so in as many words —
and went on writing **all four** fields from the blend
(`CrossPointPaletteMixer.mm` `applyGuns`, the `r.light.*` writes). So one gun
move in dark mode replaced whatever ink had been chosen in light.

Second half, same shared-slot cause: pointing the preset at Custom for the light
page cost the DARK page its phosphor. The ink picker already froze the dark
TONES, but `pollPanelGlow` (`CrossPointIOSShim.cpp:1644` [was `:1483`,
re-grepped 2026-08-29]) read the preset
integer raw, and Custom names no phosphor — so a light-mode ink pick turned
White CRT's 283 ms emissive trail into 0 ms reflective, and kept it that way
across relaunches.

**Reproduced first, on an iPhone Air simulator (`663B0B14`), 2026-08-23**, with
`CROSSPOINT_SIM_APPLY_INK` and `CROSSPOINT_SIM_MIX_GUNS` driving the editors'
own apply functions:

| step | `panelInkLight` | page text, measured |
|---|---|---|
| Payne's Gray applied in light | `323D47` | (30, 37, 43) |
| relaunch (load) | `323D47` | (30, 37, 43) |
| dark, then light again (switch) | `323D47` | (30, 37, 43) |
| **one gun moved in dark mode** | **`6E0500`** | **(64, 3, 0)** — a red |

`lightInkIndex` still read 15 throughout, so the picker went on showing Payne's
Gray as the chosen row while the page rendered a color nobody picked. The glow
half came off the app's own log: `[glow] preset 21 -> 283 ms trail ... emissive`
at boot, `[glow] preset 0 -> 0 ms trail ... reflective` six seconds later, after
one ink pick.

**Fix.** The decision moved to `src/PanelSource.h` — pure, host-tested — and
`ios/PanelPrefs.h` only fetches. One editor per polarity, neither writing the
other's fields, and one shared claim protocol
(`CrossPointPrefs_claimCustomFor(editingDark)`) that freezes the other
polarity's currently-rendered pair **and its phosphor**
(`panelDarkSnapshotPreset`, append-only, 0 = none) before the shared preset
integer moves — and does nothing once the slot is already Custom. The glow asks
`crosspoint::glowPresetForPrefs()`.

**Verified after, same device, same sequence**: the light page measured
(30, 36, 43) on load, after a light↔dark switch, and after the same gun move that
used to destroy it; the store kept `panelInkLight=323D47`; and the trail stayed
283 ms emissive through the ink pick and across a relaunch. Native-pixel PNGs of
each step were captured with the run.

**Why nothing caught it.** `tests/chip_tint_source_test.py` guards this exact
area and passed through the whole bug: it asserts a delegation CHAIN and never a
tone, and the chain was intact the entire time. `tests/panel_source_test.cpp`
(bytes, both polarities, load / switch / both editor orders) and
`tests/panel_source_test.py` (each editor writes only its own polarity's keys)
now cover it; both fail against the pre-fix tree — 3 and 20 failures
respectively.

### [S-021] The pad's Accessible pin lived at one of its two resolution points — FIXED 2026-08-23
**severity: medium · scope: ios pad and keyboard chips · found 2026-08-23 while fixing S-020**

Owner order 2026-08-22 pinned the button pad to `kPresetAccessible`. The pin
went into `CrossPointIOSShim.cpp`'s `currentLevels()`, which feeds the pad and
the SDL SHOW chip. `ios/PanelPrefs.h`'s `padPaletteForPrefs` resolves the pad a
SECOND time, for the UIKit HIDE chip in the keyboard bar, and went on handing
the raw stored contrasts to `makePaletteOn` — the registered defaults, which are
the Current preset's ±1. So the hide chip drew a ±1 hairline beside a pad drawn
at Accessible's ∓4: the two halves of one gesture, 4–5× apart in contrast, under
a header comment in that very file promising one definition.

Separate defect from S-020 — different control, different mechanism — found in
the same file because the owner's report pointed at it. Both resolution points
call `padpalette::shippedLevels()` now, pinned by `tests/panel_source_test.cpp`
and by `tests/panel_source_test.py`.

### [S-022] Tapping Presets left the page under the sheet live for the rest of the session — FIXED 2026-08-23
**severity: high · scope: ios input gating · found by adversarial review 2026-08-23, hours after the Presets list shipped**

Both page-color drawers PUSH `ios/CrossPointPresetList.mm` onto their own
navigation controller. UIKit sends `viewDidDisappear:` to the PUSHING controller
when it does, and both controllers cleared their presented flag there
unconditionally — `g_mixerPresented`, `g_pickerPresented`. Nothing set it back:
there was no `viewDidAppear:` anywhere in the three files, and the flag was set
true exactly once, at presentation.

Those sheets are undimmed medium detents, deliberately, so the page above them
stays visible as the preview — which means UIKit passes every touch OUTSIDE the
sheet straight through to the SDL view. Five sites gate on the flags
(`CrossPointIOSShim.cpp`'s two finger paths, `CrossPointZenRecognizers.mm`'s
three recognizers). So the sequence "open a drawer, tap Presets, touch the page"
turned the page on a tap, drove font size on a swipe, and toggled zen on a
three-finger tap, while the owner believed he was in a color picker — and it
stayed that way until the sheet was dismissed.

The comment that stood at the clear said "the nav never pushes a second
controller, so disappearing means DISMISSED." That was true when it was written
and false twenty minutes later, which is the whole lesson: an invariant asserted
in prose does not hold itself.

Both controllers now reassert in `viewDidAppear:` and clear only when
`navigationController.topViewController == self`, so a push holds the gate and a
pop restores it. The sheet cannot be dismissed while the list is up
(`modalInPresentation` pins pull-down and the list carries no Done), so "top of
the stack" is the whole distinction. Each transition logs
(`[mixer] on screen; touch gate UP` / `covered by a push; touch gate HELD`), and
`tests/panel_source_test.py` fails an unconditional clear or a missing
`viewDidAppear:`.

Measured on an iPhone Air simulator (`663B0B14`) with
`CROSSPOINT_SIM_OPEN_MIXER=1 CROSSPOINT_SIM_OPEN_PRESETS=1`: gate UP at
presentation, `covered by a push; touch gate HELD` when the list arrives. The
dismiss and pop branches rest on UIKit's push/pop semantics rather than a probe
— neither can be driven headlessly, since there is no hook that taps Done.

### [S-018] iOS appearance and CrossPoint's Dark Mode disagree, and the setting never sticks — FIXED 2026-08-19
**severity: high · scope: ios display · reported from the phone 2026-08-19**

Owner: "fix when ios dark mode is the opposite of dark mode in crosspoint. it
seems to use some stuck fallback."

**Two authorities for one question.** `applyTheme` set `g_dark` from
`systemIsDark()`, so the pad and the field followed iOS — while the PAGE follows
`SETTINGS.darkMode`, which the firmware applies itself in `setup()`. Toggling
Dark Mode inside CrossPoint therefore inverted the page and left the pad on the
system's appearance: the two halves of one screen in opposite polarities.

**And the in-app control did not stick at all.** Every `applyTheme` wrote the
system value back over `SETTINGS.darkMode`. Reproduced before touching anything:
iOS light, `darkMode=1` stored, app launched — **came up light, and the file read
back 0.**

**Fixed by making the firmware's setting the single source of truth.** The system
now only SEEDS it: on a fresh install, and whenever the phone's appearance
actually changes while running. Everything else reads the setting, so an in-app
toggle moves the page, the pad and the field together and survives a relaunch.

**Two further overwrites were found while fixing it, each hiding behind the last:**

* seeding on every startup — a relaunch is not the phone changing its mind, but
  it was treated as one, so the stored choice was overwritten every launch.
  Seeding now happens only when there is no `settings.json` yet.
* `pollAppearance` starting its "last system appearance" at `-1`, which made its
  FIRST tick look like a change and reseeded immediately — the same overwrite,
  reintroduced one function further down. It initialises from the system now.

**Verified in the simulator, both directions:** iOS light with `darkMode=1`
stored renders the whole screen dark and the file still reads 1
(`ios/mockups/dark-mode-setting-respected-2026-08-19.png`); a live system flip to
light while running takes the app light and the file to 0.


### [S-017] The Back|Select rocker's divider sits hard left, not centred — FIXED 2026-08-19
**severity: medium · scope: ios display · reported from the phone 2026-08-19**

Owner, with a screenshot: "the left and center of it messed up. seems like the
dividing line stopped being centered… Back and Select rocker has a dividing line
on its left instead of centered."

**A phantom third pair, left behind by today's side-rocker removal.** `paintPad`
declares its rocker list as

```
const int pairs[3][2] = {{kPadBack, kPadConfirm}, {kPadLeft, kPadRight}};
```

— dimension **three**, two initialisers. The trailing row zero-initialises to
`{0, 0}`, and `kPadBack` is 0 (`CrossPointIOSShim.cpp:173` [was `:121`,
re-grepped 2026-08-29 — this file is under heavy concurrent edit, expect this
citation to drift again]). So the loop ran a
third time with `a == b ==` the Back cell, painting an entire extra capsule over
the left rocker's Back half and a divider tick at *that half's* own edge. The
result reads exactly as reported: the seam on the left rocker is at the quarter
point rather than the middle.

Before today it was harmless — `Up|Down` was the third pair, and the array was
full. The ruling "lose the side button UI on all devices" removed that pair from
the initialiser and left the dimension at 3, which is what turned a correct
array into a self-overdraw.

**Fixed** by sizing from the initialiser, `const int pairs[][2]`, so removing a
pair can never leave a phantom one again.

**Verified by measurement, not by eye**, on an iPhone simulator in the same green
CRT palette as the report: left rocker edges 46-375 with its divider at 210
against a true centre of 210 (**0 px off**), right rocker 704-1033 with its
divider at 869 against 868. Capture kept at
`ios/mockups/pad-divider-centred-2026-08-19.png`.


### [S-015] `test_text_entry.sh` no longer reaches the field it tests — FIXED 2026-08-17
**severity: medium · scope: tests · found 2026-08-17 · fixed in ac88f12**

**Cause, and it was the same fault twice:** it navigated both lists with UP and
DOWN, which are the SIDE pair and page by a screenful. A one-screen menu has no
next screenful, so those presses moved nothing. Home now uses RIGHT (over-pressed,
since the row count follows the recents list), Settings uses LEFT counted
backwards from row 0 (that list wraps: LEFT x1 Colophon, LEFT x2 Device Owner).
Spacing was a third fault — 180 ms where ~900 ms is needed. Now PASSES.

It fails at case 1 against firmware `main`, and has failed since before the
B-028 work (confirmed by stashing that fix and re-running: identical failure).
The failure is its own navigation, not the channel it covers — which means the
host-keyboard channel currently has NO passing end-to-end guard on the
single-line side, and a real regression there would look exactly like this.

Two stale things, both in `NAV_TO_OWNER_FIELD`, and the second is only visible
once the first is fixed:

1. **Home navigation uses `DOWN`.** Lists navigate on the FRONT pair; the side
   buttons page by a screenful and a one-screen menu has no next screenful, so
   the fifteen `DOWN`s move nothing and the `ENTER` opens row 0 (`Recent
   Books`). See [docs/headless-qa.md](docs/headless-qa.md) — the same point that
   `test_note_editor_repaint.sh` was written against. Swapping `DOWN` for
   `RIGHT` gets it into Settings.
2. **The Settings tail count is stale.** With Home fixed, `6700:UP;7000:UP`
   lands on `FontSelect`, not Device Owner. The test's own comment predicted
   exactly this ("Colophon was added after it… keep asserting the activity
   rather than trusting the count"); something has since been appended or
   reordered again.

**Close by:** recounting the Settings tail against the current build and
switching Home to `RIGHT`. Both arms of case 4 (the daisywheel) and cases 5–6
(the RAWKEY path) use the same nav string, so one fix restores all six.

Only diagnosed here, not fixed — it surfaced while proving B-028 and repairing
it is a separate recount.

**VERIFIED FIXED 2026-08-18.** Re-run against a clean firmware worktree at
`f80b140b6` with a seeded `fs_`: PASSES, along with the other three shell tests.
This entry sat under `## OPEN` while its own title said FIXED, and CLAUDE.md
went on telling every new session the test was broken — for a day after it was
not. The lesson is the one at the top of this file pointed the other way: an
entry also may not STAY open once there is evidence it is fixed.

---

### [S-014] The image validator and the flasher are excluded from the simulator build — FIXED 2026-08-16
**severity: medium · scope: fidelity · found and FIXED 2026-08-16**

**Fixed by splitting the file, which is what the entry proposed.** The firmware
now has `src/network/FirmwareImageValidator.cpp` holding the READ-ONLY half —
`resultName()`, `runningPartitionChipId()`, `feedHashAndChecksum()` and
`validateImageFile()` — with the shared layout constants moved to
`src/network/FirmwareImageFormat.h` so neither file's existing unqualified uses
had to be rewritten. `FirmwareFlasher.cpp` keeps `flashFromSdPath()` alone and
stays excluded from the `simulator` env; the validator is not excluded, so the
real one compiles in. `platformio.ini` did not need editing at all, which also
means no build directory was wiped.

The simulator's `src/simulator_firmware.cpp` dropped its fake
`validateImageFile()` and `resultName()` (they would now be duplicate symbols)
and kept the `flashFromSdPath()` stub. One new shim was needed:
`esp_ota_get_running_partition()` returns null, which is honest AND safe —
`runningPartitionChipId()` caches `0xFFFF` on a failed read and
`validateImageFile()` explicitly skips the chip check on `0xFFFF`. So a host
validates everything about an image except which MCU it targets, which is the
one property a host cannot know.

**Proven both directions, through the real screen** (Home → Settings → SD
firmware update → file browser → pick a `.bin`):

| Image | Result |
|---|---|
| the genuine 4,492,880-byte `20260807T0857Z-crosspoint-f1459353.bin` | validation passes; the **"Update firmware?"** confirmation prompt appears, which is reachable only on `Result::OK` |
| the same file with **one byte flipped** at offset 2,246,440 | `validate: checksum mismatch computed=0x03 stored=0xFC` → `image validation failed: BAD_CHECKSUM` |

That pass is also the end-to-end proof that the mbedtls SHA-256 shim is now
real: the image carries a SHA-256 trailer, and the old XOR fold could not have
matched it under any reading.

Firmware TU count went 129 → 130, so `cmake/CrossPointSources.cmake` was
regenerated. Desktop, iOS and 22/22 host tests all green after.

**Original entry follows.**

Found while closing S-001's partition half, by driving the SD firmware update
screen to the end. With a partition now available the firmware gets as far as
`firmware_flash::validateImageFile()` and hits this:

```
[FW] Selected: /20260807T0857Z-crosspoint-f1459353.bin
[FLASH] [SIM] Firmware image validation is disabled in the native simulator
[FW] image validation failed: UNSUPPORTED_IN_SIMULATOR
```

The stub is [src/simulator_firmware.cpp:15](src/simulator_firmware.cpp), and it
is there because the firmware's own `platformio.ini` drops the real file from
the `simulator` env:

```ini
build_src_filter =
  -<network/FirmwareFlasher.cpp>    ; "Firmware-update code remains
  -<network/OtaBootSwitch.cpp>      ;  non-destructive in the simulator."
  -<network/OtaUpdater.cpp>
```

**The exclusion is right for two of those three and wrong for the validator.**
`flashFromSdPath()` and `switchTo()` write flash and move the boot pointer —
nothing a host should imitate. But `validateImageFile()` writes nothing at all:
it opens a file, checks the 0xE9 magic, walks the segment table, folds the XOR
checksum and compares a SHA-256 trailer. That is pure computation over a file on
the simulated card, it is the code most worth running before shipping a
firmware image, and it has never executed here once.

**Verified, not assumed:** `validateImageFile` is `src/network/FirmwareFlasher.cpp:107`
and its only side effect is `Storage.openFileForRead` + reads. The mbedtls
SHA-256 it needs is now real (see below); `SPI_FLASH_SEC_SIZE` is already
shimmed at [src/spi_flash_mmap.h](src/spi_flash_mmap.h).

**Close by:** splitting the validator out of `FirmwareFlasher.cpp` so the
simulator can compile it without the flash writer, or narrowing the src_filter
and letting the write side fail through the existing `esp_partition_write()`
`ESP_FAIL`. Either is a FIRMWARE change, and editing `platformio.ini` wipes
every build directory, so it wants its own pass rather than a rider on this one.

**Related and already fixed here:** the mbedtls SHA-256 shim
([src/mbedtls/sha256.h](src/mbedtls/sha256.h)) was a fake — `digest[i % 32] ^=
input[i]`, returning success. Every SHA-256 computed in this simulator was
silently wrong. It now uses CommonCrypto on macOS and OpenSSL on Linux, with
`tests/sha256_test.cpp` pinning it to the published FIPS-180-4 vectors. It had
no live caller (the only one is the excluded file above), so nothing was
observably broken by it — but the validator could never have passed its SHA
check, and that would have been the next wrong diagnosis.

---

### [S-001] The simulator reports the opposite of the device in six places — FIXED 2026-08-16
**severity: medium · scope: fidelity · found 2026-08-07** · heap + battery FIXED 2026-08-08 · **remaining four FIXED 2026-08-16**

Not crashes — false confidence. Each makes a firmware path look exercised when
it never ran, and the simulator is the project's only pre-device gate.

| Reports | Device | What it hides |
|---|---|---|
| ~~1 MB free heap~~ **FIXED 2026-08-08** (`CROSSPOINT_SIM_HEAP`, `CROSSPOINT_SIM_HEAP_FREE`) (`src/Arduino.h:41,51`) | ~380 KB, no PSRAM | every graceful-degradation gate: indexing pause, glyph prewarm, SD font streaming fallback, image/CSS/JPEG bailouts |
| ~~`supportsAsyncRefresh()` false~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_ASYNC_REFRESH=1`) | supported | was: the overlapped page turn had never executed in a simulator run |
| ~~no panic ever~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_PANIC=<reason>`) | 225 lines of panic handling | was: `CrashActivity` compiled in and could not be entered |
| ~~battery 100%, USB always connected~~ **FIXED 2026-08-08** — `CROSSPOINT_SIM_BATTERY=<0-100>`, `CROSSPOINT_SIM_USB=0`; default unchanged. Verified: at 7% unplugged the charging bolt is gone and the battery draws empty | real gauge + GPIO | was: charging bolt always drawn, plug/unplug repaint never fires |
| ~~`esp_ota_get_next_update_partition()` null~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_OTA_PARTITION=1`) | valid | was: SD firmware update showed "Invalid firmware" before reading a byte |
| ~~OTA pinned to NO_UPDATE~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_OTA=available\|error`) | real check | was: the available→download→install flow was unreachable — but see the caller note below |

**All four remaining reversals now answer honestly, opt-in.** The definitions
live in [src/SimulatorDeviceTruth.h](src/SimulatorDeviceTruth.h), pure and
host-tested by `tests/device_truth_test.cpp`, and every default is byte-for-byte
what this simulator always reported — so no existing headless script or
screenshot run changes behaviour. That is the same shape the heap budget took,
and for the same reason: turning device-truth on is a thing a test asks for.

**Proof each one now runs, rather than merely compiles:**

- **Overlapped page turn.** A/B on the same script: `CROSSPOINT_SIM_ASYNC_REFRESH=1`
  logs `Page render (tiled async)` twice, the identical run without it logs it
  zero times. First execution of `EpubReaderActivity.cpp:1593`'s branch in this
  simulator's history. The `!inverted` term mirrors the device rather than being
  invented: `FreeInkDisplay::supportsAsyncRefresh()` is
  `!_inverted && !_inversionDirty && _driver->supportsAsyncDisplay()`, and both
  X3 drivers (Uc8253X3, Ssd1677) answer true — so on hardware the capability
  comes and goes with dark mode, and now it does here too.
- **CrashActivity.** `CROSSPOINT_SIM_PANIC='Guru Meditation Error (LoadProhibited)'`
  produces `[ACT] Entering activity: Crash`, `Previous boot panicked: …` and a
  582-byte `/crash_report.txt` on the card. The control run with no env var
  enters it zero times. The latch is ONE-SHOT by construction — it `unsetenv`s
  on first read, so the desktop `execvp` reboot's child boots clean, exactly as
  the boot after a real panic does. Without that the crash screen would have no
  exit.
- **Next-update partition.** A/B through the real screen (Home → Settings → SD
  firmware update → file browser → pick the .bin). Off: `no next-update
  partition available`. On: the firmware gets past it into the real size check.
  **The first version of this shim invented the slot geometry and was caught by
  that very run** — a guessed 0x1F0000 rejected a genuine 4,492,880-byte image
  as "exceeds partition (2031616 bytes)", which is a NEW wrong answer wearing
  the old one's clothes. The numbers now come off the firmware's own
  `partitions.csv`: `app1, app, ota_1, 0x650000, 0x640000`.
- **OTA check.** Answers `available` / `error` / `none` with a version and an
  install outcome. **But nothing in this fork calls `OtaUpdater`** — grepped
  2026-08-16 across `src/`, `lib/` and `freeink-sdk/`, the only references are
  its own header and .cpp. So this row was unreachable for a second reason it
  never stated: there is no caller. The one firmware-update path a person can
  actually open is `SdFirmwareUpdateActivity`, which is the partition row above.

**Where the SD update path stops now:** at `validateImageFile()`, which is a
different stub and a different bug — filed as **S-014**.

**Closing note, 2026-08-29:** re-confirmed clean — `src/SimulatorDeviceTruth.h`
exists and `tests/device_truth_test.cpp` is wired into `tests/run_all.sh:532`
(was `:479` — the file has grown since this note was written earlier
2026-08-29; re-grepped).
No further action.

---

### [S-011] `test_sleep_wake.sh` fails against current firmware `main` — the scripted POWER hold no longer sleeps — FIXED 2026-08-17
**severity: medium · scope: tests / firmware drift · found 2026-08-08** · FIXED 2026-08-08

**ROOT CAUSE FOUND 2026-08-17, and it was never firmware drift: the test was the
only one here that did not run HEADLESS.** It omitted `SDL_VIDEODRIVER=dummy`,
so it opened a real SDL window and its timing followed the window server, the
GPU and the machine's load — surfacing as "the 1ms wake tap was missed", which
is indistinguishable from a wake regression from the outside.

Measured both ways on the same tree and binary:

| | result |
|---|---|
| windowed | 2 of 3 FAILED |
| headless | 4 of 4 PASSED |

A first guess that the wake tap needed more headroom (6 s → 15 s) was wrong and
was reverted: it still failed windowed at 15 s. The two tests here that were
never flaky, `test_text_entry.sh` and `test_note_editor_repaint.sh`, both set
the variable. Dummy still renders, so the after-wake screenshot is captured
exactly as before.


The test's scenario (`2500:POWER:700` must enter deep sleep, a later 1 ms tap
must relaunch the process) no longer matches the firmware: against the fork's
`main` @ `4ded8fc`, the process neither sleeps nor relaunches — it idles until
killed, and the harness reports "never relaunched as a wake". Reproduced
byte-identically with the simulator at `origin/main` (`ebf2b54`, before any
read-aloud work), so this is firmware drift, not a simulator regression:
power-button semantics have grown options since the test was calibrated
(`SHORT_PWRBTN::PAGE_TURN`, the long-press behavior setting), and a 700 ms
hold no longer crosses the sleep threshold on the boot-into-reader path a
seeded card lands on.

Found running the full shell-test sweep after the read-aloud input changes —
which the bisect exonerates. `test_text_entry.sh` passes against the same
binary, and the sleep wake edge-latch itself is untouched.

**Close by:** recalibrating the test against the current firmware's power
semantics (which hold duration sleeps, from which screens), or pinning it to
a firmware ref it matches. Decide which behavior is intended before touching
either side.


**Fixed, and the cause was not firmware drift.** This entry blamed the power
semantics growing options. Reading the code says otherwise: sleep on a hold
needs `millis() >= allowSleepAt`, and `main.cpp:562` sets that to
**(end of setup) + 2000 ms**. Booting into Home, setup finishes in ~400 ms and
the test's 2500 ms press lands well clear. Booting into the READER, setup also
paginates — tens of seconds on the seed book's mono-file chapter — so
`allowSleepAt` moves past the press and the device never sleeps.

The defect was therefore in the test, not the firmware: it `cd`s into the
firmware checkout and runs against whatever state the working card happens to be
in, so the same binary passed or failed depending on what had been read last.
It now seeds `readerActivityLoadCount = 1` (the documented lever for a Home boot)
and restores the card afterwards.

Proved both directions: set the card to the boot-into-reader state that produced
the original failure and the test passes, and the card is byte-restored after.

Writing the restore also produced a small lesson worth keeping — the first
version trapped `rm -rf "$WORK"` BEFORE the restore, and the backup lives inside
`$WORK`, so cleanup ate the file the restore needed and silently left the seeded
state on the working card. Restore first, clean up second.

**Closing note, 2026-08-29:** re-confirmed clean — `tests/test_sleep_wake.sh:48-67`
seeds `readerActivityLoadCount=1` before the run and restores `state.json` from
the backup before the `$WORK` cleanup. No further action.

### [S-013] The in-process reboot orphans the parked accept worker — FIXED 2026-08-08
**severity: low · scope: iOS lifecycle · found 2026-08-08** · FIXED 2026-08-08


Every file transfer ends in `silentRestart()`. On iOS that is a `longjmp` back
into `setup()`, which skips destructors — so the `WebServer` whose handler
triggered the restart is never destroyed, and its accept worker, parked on the
dispatch condition variable, lives on forever holding a client socket. Each
transfer leaks one thread and one fd.

This is strictly better than what S-003 replaced (a cross-thread `longjmp`,
undefined behavior), and it is invisible on desktop, where the restart is
`execvp` and the whole process is replaced. But a long-lived phone doing many
transfers accumulates orphaned workers.

**Close by:** on the reboot reset path (`simreset::runAll()` /
`forceReleaseAllForReboot()`), also stop the server and join or detach its
worker before the jump — or have the reboot tear the server down explicitly
rather than leaving it to skipped destructors.


**Fixed.** Live `WebServer` instances register themselves, and a
`simreset::Registrar` stops each one immediately before the in-process jump —
beside the mutex release and the static resets that already run there. `stop()`
sets the abandoned flag, shuts the listening socket and joins, so the worker
exits instead of outliving the reboot.

Safe to call from that point precisely because of S-003: the handler that
triggered the restart runs on the main thread now, so the accept worker is only
ever accepting or parked, and `stop()` releases both. Under the pre-S-003
arrangement the worker WAS the handler and this could not have worked.

Verified: 12/12 simulator tests, and 10/10 requests still served after the
change — the registry does not disturb the normal path.

**Closing note, 2026-08-29:** re-confirmed clean — `src/WebServer.cpp:453-461`
holds `gServerReboot` (the `simreset::Registrar` that stops every live server
before the jump). No further action.

### [S-012] A throwing route handler hung the file-transfer server forever
**severity: high · scope: web server / threading · found + FIXED 2026-08-08**

Introduced by S-003's dispatch handoff (same day). `handleClient()` unlocked,
called `dispatchParkedRequest()`, then re-locked and set `dispatchDone = true`
to wake the accept worker parked on its condition variable. The signal was a
trailing statement, and route handlers are arbitrary `std::function<void()>`
with no no-throw contract — and this TU builds WITH exceptions, unlike the
device's `-fno-exceptions`. A handler that threw (`std::bad_alloc` under memory
pressure being the realistic case on a phone) skipped the signal, and the worker
waited forever. Every subsequent request parked behind it: one throw and the
whole server was dead until the app restarted.

Found by the 2026-08-08 P0 audit, verified against the code: exceptions are
enabled in both the simulator and iOS builds, so the outcome is a hang rather
than an abort.

**Fixed** by moving the signal into a scope guard, so it fires on normal return
and on exception unwind alike. `tests/dispatch_signal_test.cpp` pins it, and its
FIRST assertion proves the trailing-statement form still hangs — if that ever
passes, the test has stopped exercising the bug. Verified against the running
server too: 20 consecutive requests all return 200 where a parked worker would
hang after the first.

Noted, not fixed here: `ESP.restart()` from a handler does not return, so the
guard is skipped (longjmp on iOS) or the whole process is replaced (execvp on
desktop). The parked worker is orphaned by the reboot — a per-transfer thread
and socket leak on iOS, but not the permanent hang the throw was. Tracked as
S-013.


**The heap half is fixed; the other five reversals stay open.**

`ESP.getFreeHeap()` returned a flat 1 MB, so the firmware's low-memory branches
— the background page build (`EpubReaderActivity.cpp:268`), the plane buffer
(`:1692`), retaining a mini font (`SdCardFont.cpp:121`), image decode
(`ImageBlock.cpp:152`), the JPEG path and the CSS parser (`CssParser.cpp:693`)
— could not run at all. [src/SimulatorHeap.h](src/SimulatorHeap.h) replaces it
with two opt-in modes:

    CROSSPOINT_SIM_HEAP=380000      a budget that counts down as the firmware allocates
    CROSSPOINT_SIM_HEAP_FREE=40000  a pinned free figure

Measured: default still reports a flat 1048576 (every existing script is
untouched), the pin holds at its value, and the budget starts at 33,863 free of
380,000 and falls to 26,391 over ten seconds.

**Two honest limits, both found by measuring rather than assumed:**

- The accounting is **asymmetric**. Only a sized `operator delete` can know what
  to return, and `tests/heap_budget_test.cpp` caught libc++ freeing a
  `std::vector`'s buffer without going through it — so the budget drifts DOWN
  over a long run regardless of what the firmware frees. That is why the pin
  exists: a test wanting an exact number should state it, not allocate its way
  there. `malloc`/`free` are untracked, so vendored C (miniz, uzlib) is
  invisible.
- Fragmentation is not modelled, so `getMaxAllocHeap()` equals the free figure.
  Anything comparing the two — as `BleHidHost` does — is asking a question this
  cannot answer.

**Not demonstrated:** that a specific firmware branch fires under the pin. The
values the firmware reads definitely change, and the thresholds are now
crossable, but I did not get a book open under a low pin to watch one trigger.
The five remaining reversals in this entry are untouched.

### [S-002] Sleep/restart statics survive the iOS in-process reboot — FIXED 2026-08-08
**severity: medium · scope: iOS lifecycle · found 2026-08-07** · PARTIALLY FIXED 2026-08-07


`rebootAsPowerWake()` promotes the `*_AFTER_WAKE` schedules
(`src/SimulatorLifecycle.cpp:93`), but the consumers read the environment once
per *process* — `syntheticEventsInitialized` (`src/HalGPIO.cpp:280,598-600`) and
`screenshotEventsInitialized` (`src/HalDisplay.cpp:428,460-462`) [all three
re-grepped 2026-08-29; were `:79`, `:186`, `:123`]. Desktop re-execs, so
it works there; iOS longjmps into the same process, so the promotion is dead
code on the only platform that uses that path. `CLAUDE.md` states the promotion
unconditionally.

Two more of the same shape: `textEntryActive` survives a restart, leaving the
keyboard channel latched and the button map suppressed; and the jump skips
destructors, so a `RenderLock` held when `ESP.restart()` is called is never
released and the render task deadlocks on the first post-reboot frame.

**Close by:** resetting the process-scoped statics on the in-process reboot
path, and correcting the `CLAUDE.md` claim.


**Fixed for the statics half.** `src/SimulatorRebootResets.h` holds a registry
that `SimulatorLifecycle` runs immediately before both in-process jumps. HalGPIO
registers a reset for `syntheticEventsInitialized`, the pending
`syntheticEvents`, and `textEntryActive`; HalDisplay for
`screenshotEventsInitialized` and `screenshotEvents`. So the `*_AFTER_WAKE`
promotion now actually reaches its consumers on the phone, and a reboot taken
mid-text-entry no longer leaves the keyboard channel latched with the button map
suppressed.

`CLAUDE.md` no longer states the promotion unconditionally: it now says why the
desktop got it for free (`execvp` is a new process), and that anything caching
env-derived state behind a `static bool ...Initialized` must register a reset.

`tests/reboot_resets_test.cpp` pins the contract the lifecycle depends on —
everything registered runs, in registration order, and `runAll()` does not
consume the registry, because a process can reboot more than once.

**STILL OPEN, and why this entry stays:** the longjmp also skips destructors, so
a `RenderLock` held when `ESP.restart()` is called is never released and the
render task deadlocks on the first post-reboot frame. That is not a stale static
and a reset callback cannot fix it — it needs the lock either dropped before the
jump or made reentrant across it. Untouched here.

**Now fully fixed.** The statics half landed earlier; this closes the other one.

A `RenderLock` held when the longjmp fires never runs `xSemaphoreGive`, so the
mutex stayed locked by a thread that no longer existed and the render task
blocked forever on the first frame back. `std::recursive_mutex` offered no way
out — unlocking one you do not own is undefined, destroying one with a waiter
parked on it is worse — so the shim now implements the recursive mutex itself
over a plain mutex, a condition variable and an owner/count that
`simsemphr::forceReleaseAllForReboot()` can clear and wake. It runs beside
`simreset::runAll()` at both jump sites.

`tests/semphr_reboot_test.cpp` pins it, and writing it corrected the design
twice — both times because the test asserted the deadlock as a PRECONDITION and
the precondition failed:

1. Ownership by `TaskHandle_t` let any thread in. Threads not created through
   `xTaskCreate` share a handle, so an unrelated thread read as the holder
   re-entering.
2. Ownership by `std::thread::id` let the *probe* in. Thread ids are recycled
   once a thread ends — and a holder that ended without releasing is precisely
   this bug, so the replacement thread inherited its identity.

Ownership is now a per-thread token from a counter that only goes up. A give
from a non-holder is a no-op rather than a decrement, so a stale unwind after
the release cannot free somebody else's lock.

**Closing note, 2026-08-29:** re-confirmed clean — `src/SimulatorRebootResets.h`
plus `simsemphr::forceReleaseAllForReboot()` are called at three sites in
`src/SimulatorLifecycle.cpp:115,185,220`; `tests/reboot_resets_test.cpp` and
`tests/semphr_reboot_test.cpp` are wired into `tests/run_all.sh:335,338` (was
`:302,305`, re-grepped 2026-08-29 — the file has grown since this note was
written). No
further action.

### [S-003] Route handlers run on the accept worker, not the firmware task — FIXED 2026-08-08
**severity: high · scope: web server / threading · found 2026-08-07** · FIXED 2026-08-08


`WebServer::handleClient()` is an empty function (`src/WebServer.cpp:677`), so
the firmware's poll does nothing and every route handler runs on
`impl_->worker` instead (`:643`). Two consequences: unsynchronised mutation of
firmware state and the framebuffer against the render task, and — worse —
`ESP.restart()` reached from a handler calls `std::longjmp(gRebootJump, 1)` on
iOS (`src/SimulatorLifecycle.cpp:146`) against a `setjmp` taken on the **main**
thread (`src/simulator_main.cpp:101`). Longjmp across threads is undefined
behavior, and `silentRestart()` is how every file transfer ends.

**Close by:** queueing handler invocations for `handleClient()` to drain on the
calling thread, which is what the device does.


**Fixed.** `handleClient()` is no longer empty. The accept worker now accepts
and parses only, parks the request behind a condition variable, and waits;
`handleClient()` drains it on the caller's thread and signals back, after which
the worker closes the socket. That is where the device runs handlers too.

The thread it lands on is the point: `loop()` runs on the MAIN thread
(`simulator_main.cpp:148`), which is the thread that took the `setjmp`. So a
handler calling `ESP.restart()` — which every file transfer does, via
`silentRestart()` — now longjmps on the right thread instead of committing
undefined behavior from a worker.

Two things the shape had to get right. The dispatch runs with the mutex
UNLOCKED, because a handler that restarts never returns and would otherwise
leave the worker blocked on a mutex nobody will release. And `stop()` sets an
abandoned flag before `join()`, or a worker parked on a dispatch that will never
be drained deadlocks the shutdown.

Verified against the running server: index, the file listing, a download and a
WebDAV PUT all succeed (the PUT's bytes land on the card), and the process exits
0 with nothing left alive. That the requests complete at all is itself the
thread evidence — `handleClient()` is now the only thing that dispatches, so if
it were not running they would hang.

**Closing note, 2026-08-29:** re-confirmed clean — `src/WebServer.cpp:665-799`
still has the accept worker parking on the `dispatchDone` condvar and
`dispatchParkedRequest()`/`handleClient()` running the drain on the main
thread. No further action.

### [S-004] `getFrameBuffer()` can return null and five callers dereference it — FIXED 2026-08-07
**severity: high · scope: display · found 2026-08-07** · FIXED 2026-08-07


`HalDisplay::getFrameBuffer()` returns `nullptr` while the buffer is lent out
(`src/HalDisplay.cpp:784`), and every consumer assumes non-null:
`clearScreen` goes straight into `memset(getFrameBuffer(), …)`
(`:532`), `refreshDisplay` into `snapshotBwBase` (`:612-614`), plus `drawImage`
(`:537`), `drawImageTransparent` (`:560`) and `composeGrayscalePreview`
(`:275`).

`frameBufferLent` is a **plain `bool`** at file scope (`:114`), written by the
borrower and read by the render thread with no synchronisation, so the window is
not even deterministic.

Dormant today: nothing in this repo calls `lendFrameBufferStorage`. It arms the
moment the firmware's decode path does.

**Close by:** deciding the contract — either the callers check, or the loan
blocks/copies instead of handing back null — and making the flag an atomic
either way.


**Fixed.** All five dereferences now check. The behavior on null is to skip,
not to substitute a buffer: whoever holds the loan owns those pixels, and the
lender's own refresh follows, so a skipped clear or blit repaints on the next
draw. `refreshDisplay` returning early matters most — converting a half-owned
buffer would have presented a torn frame rather than crashed, which is the worse
failure because it looks like a rendering bug somewhere else entirely.

`composeGrayscalePreview` keeps the last presented frame instead of compositing
from null.

**Closing note, 2026-08-29:** re-confirmed clean — all five call sites still
null-check `getFrameBuffer()`: `src/HalDisplay.cpp:878, 1910, 1917, 1938, 2020`.
**The one sub-item this note used to record as unfulfilled is now closed too:**
`frameBufferLent` is an `std::atomic<bool>` (`src/HalDisplay.cpp:419`), which is
the atomic the original entry's "Close by" asked for. Correcting the reasoning
along with the fact: this was NOT pure hardening over an already-serialized
flag. `getFrameBuffer()`, `lendFrameBufferStorage()` and
`returnFrameBufferStorage()` (`src/HalDisplay.cpp:4132-4155`) read and write
`frameBufferLent` with no `pixelBufMutex` of their own — verified by reading
all three bodies, none takes the lock — unlike `frameBufferStorage`'s other
readers/writers a few lines below, which do. So the earlier claim that "every
access is serialized through `pixelBufMutex`" was wrong: those three functions
were racing on a plain `bool` with no synchronization at all, and the change
closed a narrow real gap rather than hardening an already-safe path.

### [S-010] `CROSSPOINT_NO_NETWORK` outlived the reason it existed — FIXED 2026-08-07
**severity: medium · scope: iOS features · FIXED 2026-08-07 · `d7e8b27`, firmware `f1459353`**

The flag excluded 16 TUs and gated Wi-Fi, File Transfer, font downloads and
Claude out of the iOS build. That was correct when it was written: the radio was
fake — `WiFi.scanNetworks()` returned a synthetic list and `localIP()` was
hardcoded to `127.0.0.1`, so File Transfer painted a QR code pointing at
loopback. That is B-008, the lying-control defect.

It stopped being correct at `4a98ba8`, which gave the target a real radio:
`CrossPointWiFi.mm` over NetworkExtension, in-process HTTP, Bonjour, and servers
bound to all interfaces on iOS. From then on the flag was suppressing features
that work — the mirror image of the defect it was introduced to fix.

Split into `CROSSPOINT_NO_DEVICE_FLASH`, which gates only OTA and SD Firmware
Update. Those write firmware to an ESP32 partition; no phone has one. The
exclusion list went from 16 TUs to 4.

Two conflations surfaced while mapping the guard sites, both accidental:
Bluetooth keyboard pairing sat inside the network guard (so Pair/Forget BT were
unavailable on iOS for no reason), and Download Fonts sat inside the OTA guard
(so it went out with firmware flashing rather than with networking). Both now
follow the surface they belong to.

**Verified:** `crosspoint_core` AND the `CrossPointX3` app target both link for
`arm64-apple-ios` with the network TUs restored — the app-target link is the
gate that matters, since a static library can hide unresolved symbols and that
is exactly where build 30 died. The two flash activities' absence is proven by
the same link: their rows and switch cases must be compiled out, or
`OtaUpdateActivity` could not resolve. Home renders all seven rows including
File Transfer and Claude; Settings shows Wi-Fi Networks. Device `gh_release` and
the desktop canary both build; 215/215 firmware tests, 6/6 simulator tests.

**Not confirmed on hardware:** that a transfer actually completes from another
machine. Linking is not the same as working.

**Depended on B-004.** Editing `platformio.ini` used to wipe every environment's
build directory, which is why this kind of change was avoided.

**Closing note, 2026-08-29:** re-confirmed clean — `CROSSPOINT_NO_NETWORK`
appears nowhere outside historical doc prose (`ios/README.md:1614`,
`ios/WIFI.md:138,141,320`, all describing that the macro is gone), and
`CROSSPOINT_NO_DEVICE_FLASH` stays scoped to OTA/SD-flash only in
`cmake/CrossPointIOSExclusions.cmake:36,46`. No further action.

### [S-009] The pad contrast dial had its resolution in the wrong place
**severity: medium · scope: iOS settings · FIXED 2026-08-07 · `258bb14`**

Two reports, one cause: "missing all the steps between default and invisible",
and "I can't select black for dark".

Nine of the nineteen rows bought nothing, and the shim's own comment said so:
on the light side the paper is 4 levels off white, so `+1..+9` spanned
`FBFBF9 -> FFFFFD` — 1.00:1 to 1.03:1, several rows pixel-identical. Meanwhile
the two rows an owner most wants to choose between, the default (`-1`, 1.36:1)
and invisible (`0`), were **adjacent integers with nothing in between**. All the
resolution sat where nobody could see it and none where it mattered.

Those rows were spent on the gap instead. Light `+1..+9` now give 1.3 / 1.24 /
1.2 / 1.15 / 1.11 / 1.08 / 1.05 / 1.04 / 1.02; dark `-1..-8` give 1.38 / 1.29 /
1.22 / 1.16 / 1.11 / 1.08 / 1.04 / 1.02.

**Black was already reachable in dark** — level `-9` is field `121212` plus a
`-18` delta, i.e. `000000` — but its row read "Darker than the field — 1.12:1",
which names a ratio and never says black. Undiscoverable, not absent. It is
labeled `1.12:1 — black` now, and kept last because 1.12:1 against the field
really is low contrast; what earns it a row is that it vanishes into a
true-black page on OLED.

Ratios are computed from sRGB relative luminance rather than estimated, because
the delta tables and Root.plist's row labels have to agree — the standard the
existing comment sets. Root.plist is reordered strongest -> invisible, which is
display order only: `Titles` and `Values` are parallel arrays, so the stored
integers are unchanged and an existing selection still means what it meant.

**Verified:** the `+/-1` default rows are untouched, so a pad left alone is
pixel-identical; all six `static_assert`s (which pin the defaults and the 3:1,
black and white rungs) still hold, confirmed by compiling the shim rather than
by reading it; `plutil -lint` passes; every specifier still offers its own
DefaultValue. Both group footers, which described the old dead zone, were
rewritten — they were about to become false documentation.

### [S-008] `vTaskDelete` left the registry pointing at the handle it freed
**severity: high · scope: FreeRTOS shim · FIXED 2026-08-07 · `7370b10`**

`xTaskCreate` dedupes by task name on purpose — the iOS in-process reboot
re-runs `setup()` without tearing the process down, and a second `"render"`
task would orphan the first, leaving two threads writing one framebuffer. But
`vTaskDelete` freed the handle and left the registry entry behind, so the
create/delete/create sequence that reboot performs took the dedupe branch and
returned freed memory. The next `xTaskNotify()` is a use-after-free.

**Verified RED first** by `tests/task_registry_test.cpp`: without the erase only
one of two task bodies ran, because the stale dedupe returned early and never
spawned a thread. The assertion is behavioural rather than `new != old` — an
earlier version asserted pointer inequality and failed against the *fixed* code,
because the allocator reuses the just-freed block.

### [S-007] `String::toInt()` threw where Arduino returns 0
**severity: high · scope: Arduino shim · FIXED 2026-08-07 · `6f15ec6`**

It was `std::stoi`, which throws `invalid_argument` on empty or non-numeric
input and `out_of_range` past `INT_MAX`. Arduino's returns 0 and never throws,
so no firmware call site has a `try` — an uncaught exception took the whole
process down. `server.arg("page").toInt()` on a missing query arg reaches it
directly, since `argByName()` returns `String("")`.

Confirmed all three inputs throw under the old implementation. `strtol` matches
Arduino across six cases including `"12abc"` → 12.

### [S-006] `HalFile` leaked a `DIR*` for every directory it opened
**severity: medium · scope: storage · FIXED 2026-08-07 · `6f15ec6`**

`~HalFile` and `operator=(HalFile&&)` inlined only the fd half of `close()`, so
every `HalFile` holding a directory — `openNextFile()`, and `HalStorage::open()`
on a directory — leaked the handle. The SD font registry walks two roots and
Manage Files recurses, so a long session drifts toward `EMFILE`, which surfaces
as books that stop loading with an innocent file named in the log. Both now
delegate to `close()`, which already released both handles.

### [S-005] Long-press power-off fired while typing
**severity: medium · scope: input · SHIPPED 2026-08-07 · `fb49742` · UNCONFIRMED on device**

The text-entry suppression was implemented in `isPressed()` — with a comment
explaining why — and skipped in `getHeldTime()` and `getPowerButtonHeldTime()`.
POWER's host scancode is `p`, so with a text field open those two still read it
held. `buttonPressTime[]` compounded it: cleared only by `clearButtonState()` at
sleep entry, never on key-up, so a POWER press minutes earlier left a live
timestamp and the first `p` typed into a Wi-Fi password returned a hold of tens
of seconds — past the power-off threshold.

**Not headlessly verifiable, and not verified on device.**
`SDL_GetKeyboardState` is only written by the real-input path, so a synthetic
script cannot reproduce this at all. Compiles clean, desktop canary builds and
boots, six host tests pass — none of which is evidence the phone stops sleeping
mid-password.

**Close by:** on a build ≥ 33, tap POWER, open Settings > Device owner, and type
a word containing `p`. It should not sleep.

### [S-000] The deploy guard could not catch the bug it was written for
**severity: medium · scope: iOS deploy · FIXED 2026-08-07 · `94bd6a4`**

`ios/testflight.sh` regex'd every `GCC_PREPROCESSOR_DEFINITIONS` block in the
generated pbxproj and passed if **any** mentioned `SIMULATOR_DEVICE_X3`, with no
way to tell which target a block belonged to. Its own comment claimed "the
library's Release block is the one that governs", but no code selected that
block — so a define set `PRIVATE` on the app target alone still satisfied it,
which is exactly the split-brain build it exists to stop. That build shipped in
1–27.

Replaced with `xcodebuild -target crosspoint_core -showBuildSettings`, which is
scoped to the target and reports what the compiler is handed. Now also checks
`CROSSPOINT_RENDER_SCALE=2`, the other half of the same incident table.

**Verified** against the build-30 project: the two real defines report present,
while `SIMULATOR_DEVICE_X4_PRO` and `CROSSPOINT_RENDER_SCALE=1` report missing —
so the check reads real data rather than passing vacuously.
