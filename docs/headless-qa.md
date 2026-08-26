# Driving the simulator headlessly

`CROSSPOINT_SIM_INPUT_SCRIPT` + `CROSSPOINT_SIM_SCREENSHOTS` can walk the UI and
capture it with no window and no phone. This file records what that actually
takes, because four of the five things below cost a wrong diagnosis first.

Written 2026-08-16, after the scripted path was blamed for a bug it did not
have.

## The five things that bite

### 1. Lists navigate on the FRONT pair, not the side buttons

This is the one that looks like a broken harness. Sending `DOWN` at the Home
screen does nothing at all, and it is correct:

| Logical button | Resolves to | `MappedInputManager.cpp` |
|---|---|---|
| `NavNext` / `NavPrevious` — next/previous ITEM | front **Right** / **Left** | `:89`, `:99` |
| `PageNext` / `PagePrevious` — next/previous SCREENFUL | side **Down** / **Up** | `:102`, `:112` |

The side pair pages. On a menu that fits one screen there is no next screenful,
so `DOWN` is a legitimate no-op. **Script `RIGHT` to move down a list.** The
narrowing was deliberate (owner ruling 2026-08-14, "make side buttons be page up
and page down, when they are identical functionality to front buttons") — see
`docs/ui-conventions.md` in the firmware repo.

### 2. Home starts on a COVER, not on a menu row

The Home screen is a row of recent-book covers with the text menu below, and the
selection begins on the first cover. So the menu rows sit further down than the
list implies:

```
RIGHT x1  -> second cover
RIGHT x2  -> Recent Books      <- first MENU row
RIGHT x3  -> Browse Files
RIGHT x4  -> Manage Files
RIGHT x5  -> File Transfer
RIGHT x6  -> Create Note
```

Counting from the menu rather than from the cover is an off-by-two, and it lands
you in Manage Files while you think you are in Create Note.

The full menu after Create Note, as of 2026-08-21: Claude, Update Firmware
(dropped on builds that cannot flash, i.e. iOS), **Update Library**, Settings.
Update Library landed above Settings on 2026-08-21, so any older script whose
RIGHT-count targeted Settings or "the row above Settings" shifted by one.
Selection clamps at Settings (no wrap), so over-shooting with extra RIGHTs
still lands on Settings; it is the rows above it that moved.

### 3. Presses need roughly 900 ms between them

At 500 ms only about half register — the panel repaint has not finished and the
next synthetic edge is swallowed. Four presses arrived as two, which reads as a
flaky harness rather than as pacing. Space them ~900 ms and they all land.

### 4. Launch is NOT a fixed screen

The firmware resumes the last book, so a run can start in the reader, in Select
Chapter, or on Home depending on what the previous run left in
`fs_/.crosspoint/`. A script written against Home will do something else
entirely on the next run. Either pin the state first, or capture an early
screenshot and confirm where you actually are before trusting the rest.

**The lever is `readerActivityLoadCount` in `fs_/.crosspoint/state.json`, and a
timed-out run is what moves it.** That counter is the firmware's crash-recovery
escape hatch: non-zero means "the reader did not exit cleanly last time, go to
Home instead". Every headless run that ends on `QUIT` or a `timeout` leaves it
at 1, so a series of otherwise identical runs alternates between resuming the
book and landing on Home — which reads as a flaky harness. Writing it back to
**0** before each launch makes the run resume the book deterministically:

```bash
python3 -c "import json;p='fs_/.crosspoint/state.json';d=json.load(open(p));\
d['readerActivityLoadCount']=0;json.dump(d,open(p,'w'))"
```

Confirm it took by grepping the log for `Entering activity: EpubReader`. This
is the concrete mechanism behind the paragraph above; found 2026-08-16 while
capturing palette proofs, after five identical runs produced two different
screens.

**A script CAN hold a button during boot, and that is the other half of the
lever** (measured 2026-08-23; CLAUDE.md said it could not, and that sentence was
wrong). `main.cpp:957` routes to Home when *either* the counter is non-zero
**or** Back is held at the routing check, and a scheduled tap with a hold long
enough to span it does exactly that:

```
CROSSPOINT_SIM_INPUT_SCRIPT='200:QTAP:BACK:2500;5000:QTAP:BACK;…'
```

The check runs around 850–1000 ms after launch, so a 2.5 s hold from 200 ms
covers it with room for a slow first boot. It works because `QTAP` writes
`syntheticButtonDown[]` directly — a *level*, which `isPressed()` reads — where
a pushed SDL key event would produce only an edge. Where the counter needs the
card written before launch (impossible from inside XCUITest, which can set only
environment variables), this needs nothing but the script, so it is the portable
one: `tools/axprobe`'s cover test uses it, and every launch there now starts on
Home. Note the two levers point OPPOSITE ways — the counter above is written to
0 to force the *book*, this forces *Home*.

### 5. Captures are BMP, whatever you name them

`SDL_SaveBMP` writes the file (`src/HalDisplay.cpp:266`), so `shot.png` is a
BMP. Anything that sniffs by content will refuse it. Convert first:

```bash
sips -s format png shot.png --out shot_real.png
```

## Where you actually are — confirm it, do not assume it

Moved here from `CLAUDE.md` on 2026-08-23, along with the correction that made
the move necessary: that file taught a `DOWN`-count walk to Settings, which
§1 above shows is a no-op, and a menu order that §2 above supersedes. What
follows is the part of it that was measured and is not recorded anywhere else.

**Grep `[ACT] Entering activity:` before believing any screenshot.** A capture
of the wrong screen looks a great deal like a capture of a screen that never
changed, and every wasted run below was diagnosed that way in the end.

**A startup screenshot looks like the reader even when it is Home.** Under the
Lyra Six theme the Home screen renders the current book's page, so "the reader
is open" is not something a picture can tell you. The log line can.

**Three levers that do NOT change the boot destination**, each verified after it
was assumed to:

| Tried | What actually happens |
|---|---|
| `rm -rf ./fs_/.crosspoint/` | clears caches only. Verified 2026-08-04: with the directory deleted the sim still went `Boot -> Reader -> EpubReader` within 500 ms |
| clearing `openEpubPath` | checked, then the branch opens the book anyway unless one of the two escape conditions in §4 holds |
| clearing `lastSleepFromReader` | same |

Booting into the last book is deliberate — `main.cpp`'s comment is "The device
IS the current book" — and Home is the escape hatch, reached only by the two
levers in §4 (hold Back across the routing check, or a non-zero
`readerActivityLoadCount`).

**`HOME` is not a state-independent opener.** It reaches Home from Home (a
no-op) and does nothing at all from `EpubReader`. An earlier `CLAUDE.md`
recommended opening every script with `2000:HOME` for exactly that reason and
was wrong; it then said so two bullets later, in the same list. Pin the boot
state with a §4 lever instead of trying to normalize at runtime.

**Inside the reader, Confirm opens Select Chapter** (`[ACT] Entering activity:
EpubReaderChapterSelection`, measured 2026-08-23). It is not a way back to the
reader from somewhere else, and a run was burned on believing it was. From Home,
Confirm opens the selected book, which logs a page render.

**In Settings, Confirm on the first row cycles the category tab**, so repeated
Confirm + screenshot walks every tab.

**Scripts that list ALL files (Manage Files) shift by one after the first run.**
The firmware creates `.crosspoint/` on the test card during boot, and in a
show-everything list it sorts to row 0 of the root. A press-count written
against a fresh card acts on the wrong rows in every later run. Recount against
the current card (`find fs_ -print`) or grep the activity's log before trusting
the script — this burned a debugging cycle on 2026-08-04, where the "wrong file
moved" was the script and not the firmware.

## A working example

Open Create Note and capture the editor:

```bash
cd ~/src/crosspoint-reader           # run from the FIRMWARE repo
pio run -e simulator

SDL_VIDEODRIVER=dummy \
CROSSPOINT_SIM_INPUT_SCRIPT="4000:RIGHT;4900:RIGHT;5800:RIGHT;6700:RIGHT;7600:RIGHT;8500:RIGHT;9600:CONFIRM" \
CROSSPOINT_SIM_SCREENSHOTS="12500:/tmp/editor.png" \
  timeout 30 .pio/build/simulator/program
sips -s format png /tmp/editor.png --out /tmp/editor_real.png
```

Multiple captures in one run, to see what each press did — the fastest way to
stop guessing:

```bash
CROSSPOINT_SIM_SCREENSHOTS="3000:/tmp/a.png;5000:/tmp/b.png;6500:/tmp/c.png"
```

## The gate harness — use it instead of hand-rolling a recipe

`tools/capture_arm.sh <program> <dark 0|1> <out.bmp> [input-script] [shot-ms]`
takes one capture and prints its md5. It exists because three separate traps
each cost a wrong reading or a dead session on 2026-08-25, and it handles all
three:

- **It does not copy the card.** An earlier hand-rolled recipe copied the whole
  522 MB simulated SD card per arm. It filled the disk and blocked a session
  outright — Bash could not run at all, because it could not create its own
  output file. Only `fs_/.crosspoint` is mutable, so only that is restored.
- **It parks the desktop `settings.json`** for the duration, on an EXIT trap so
  a failed run still restores it. That file sits beside the binary and its
  watcher re-asserts the palette about once a second, over
  `CROSSPOINT_SIM_AS_SHIPPED`.
- **It fails loudly when no capture appears**, rather than printing the md5 of a
  stale file from a previous arm.

Set `CROSSPOINT_CARD_BACKUP` to a pristine `.crosspoint` copy first.

**Two arms coming back with the same md5 is the signature of a trap, not a
result.** If dark and light agree, something is overriding you.

It is deliberately not wired into `tests/run_all.sh`: a capture needs a built
firmware and a card, which that runner does not assume.

## Getting a DARK page headlessly — and why `CROSSPOINT_SIM_DARK` is not it

**`CROSSPOINT_SIM_DARK=1` does not give you a dark reader page.** It sets the
simulator's polarity, and `setPanelDark` does call `display.setInverted` — but
the FIRMWARE asserts its own `darkMode` setting during startup and overrides it.
On a card with no saved settings that value is 0, so the page renders light no
matter what the env var says.

This cost two separate dead ends on 2026-08-24: a collapse investigation that
could not reproduce a dark-ground bug, and a Tier-2 refactor baseline whose
"dark" and "light" captures came out byte-identical and therefore proved nothing.

The firmware reads `/.crosspoint/settings.json` (`CrossPointSettings.h:563`),
which on a fresh simulated card **does not exist** — every value is a default.
Write one:

```bash
python3 -c "import json; json.dump({'darkMode':1}, open('fs_/.crosspoint/settings.json','w'))"
```

Missing keys take their defaults (`fromJson` is `doc[key] | default`), so a
one-key file is safe and does not disturb anything else.

**Confirm it took by sampling the page, not by trusting the flag.** With the
as-shipped dials the dark ground is `171B1B` and the light sheet is `F9F3E9`;
sample the modal color of the middle third of a capture. Both arms coming back
identical is the signature of this trap.

```bash
CROSSPOINT_SIM_AS_SHIPPED=1 CROSSPOINT_SIM_GRAIN_SEED=7 CROSSPOINT_SIM_INPUT_SCRIPT='9000:QUIT' CROSSPOINT_SIM_SCREENSHOTS='6000:./dark.bmp'   SDL_VIDEODRIVER=dummy ./program
```

Note this is also the cheapest end-to-end check that the frozen dark page is
what the app actually renders: `171B1B` at the centre is the owner's four-gun
mix resolving correctly through the whole stack, which no host test proves.

## A `settings.json` beside the binary overrides the palette, once a second

**`CROSSPOINT_SIM_AS_SHIPPED=1` does not win the palette.** The desktop settings
watcher re-reads `./settings.json` — beside the simulated card, so
`<firmware>/settings.json` for a command-line run — about once a second and
pushes the palette it names. `applyDials` was taught in 2026-08-23 to respect
as-shipped for the DIALS (an absent key is not a key set to the default), but
the palette and mix paths were not, so a stored pair keeps re-asserting itself
over the seed.

That is not hypothetical and it is not subtle to fall for. On 2026-08-25 the
file left in `~/src/crosspoint-reader` from an earlier session differed from the
frozen dark pair by exactly ONE code value on every channel, so every capture
after the first second of a run was the shipped page + 1: `171B1B` ground read
back as `181C1C`, ink `B5EEFE` as `B6EFFF`. A collapse investigation measured
that step, found it 100% of pixels with zero geometry change, and nearly filed
it as the bug it was looking for. It was the settings file. `CROSSPOINT_SIM_PANEL_INK_DARK`
does not save you either — the watcher's palette path does not go through the
env override.

Run from a clean working directory instead, with the card symlinked in:

```bash
mkdir -p /tmp/simrun && ln -sfn <firmware>/fs_ /tmp/simrun/fs_
echo '{}' > /tmp/simrun/settings.json      # names no key, so nothing is asserted
cd /tmp/simrun && <firmware>/.pio/build/simulator_x3/program
```

Confirm it took by sampling the ground, exactly as the dark-mode check above
says: with the as-shipped dials it must read `171B1B`, not `181C1C`.

## Screenshots are FLUSHED IN A BATCH, so a dense sweep is not a film strip

`captureDueScreenshots()` walks the whole schedule and writes **every** entry
whose time has passed, from the frame currently in the backbuffer. Under the
software renderer a collapse iteration costs ~130 ms, so a sweep at 8 ms
spacing writes sixteen byte-identical files and looks like a frozen picture.
Worse, each capture is a full-output readback, and forty of them starve the
input pump enough that a scripted `QTAP:POWER` can be missed entirely — a run
that then never sleeps at all.

Schedule **six or fewer** captures around the moment you want, and identify
which path served each from the `[present] #N` line that follows it (a capture
with no `[present]` after it came from the collapse). Both facts cost a run on
2026-08-25.

**To catch the collapse's OPENING frame**, schedule a capture for a time between
the last ordinary present and sleep entry. From `deepSleep()` onward
`presentIfNeeded` returns before its own capture check, so a pending shot in
that window is not consumed by a present — it waits, and the collapse's first
iteration serves it at elapsed 0.

## Forcing state the desktop does not have

The desktop has no phone, so several branches are unreachable without help.
Each of these leaves the real state alone when unset or unparseable:

| Variable | Forces |
|---|---|
| `CROSSPOINT_SIM_HOST_KEYBOARD=1` | a host software keyboard is up — the editors then drop their own panel and give the rows to text |
| `CROSSPOINT_SIM_PANEL_{INK,PAPER}_{LIGHT,DARK}` | the panel's two tones |
| `CROSSPOINT_SIM_DARK=1` | panel polarity — **but see below** |

`CROSSPOINT_SIM_DARK` does **not** survive on the desktop: the firmware runs
`display.setInverted(SETTINGS.darkMode != 0)` during `setup()`, after the
override is applied, and wins. Set `darkMode` in
`fs_/.crosspoint/settings.json` instead, and restore it afterwards.

## Worked example: proving the editor's panel actually disappears

The same script, run twice, with and without the host-keyboard override. Ink
counted inside the band the keyboard grid occupies:

| Run | Ink in y 500–750 |
|---|---|
| default | 6858 |
| `CROSSPOINT_SIM_HOST_KEYBOARD=1` | 60 |

The residual 60 is the character count, which moves down with the status band
when the panel goes. That is the whole feature, measured rather than asserted.
