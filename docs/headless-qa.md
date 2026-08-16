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

### 5. Captures are BMP, whatever you name them

`SDL_SaveBMP` writes the file (`src/HalDisplay.cpp:266`), so `shot.png` is a
BMP. Anything that sniffs by content will refuse it. Convert first:

```bash
sips -s format png shot.png --out shot_real.png
```

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
