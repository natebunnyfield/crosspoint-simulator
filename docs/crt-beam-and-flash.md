# The page-turn flash, the beam, and how a phosphor's speed is chosen

Date: 2026-08-17. Simulator `main` at the P22B/P7 commit (`d24b332`), reported
against TestFlight build 85, fixed for build 86.

Three things landed together because they are all the same question — *what
does the panel do between one page and the next* — and two of them are bug
fixes to work that shipped in 85.

---

## 1. The full-screen flash (fixed)

**Report:** "fix full screen flash asap."

### What it actually was

A page with antialiased text is painted **twice**:

1. the firmware displays the **1-bit** page (`displayBuffer` → `renderBwPixels`);
2. `TextAntiAliasing::overlay` renders the two grayscale planes over it and
   calls `displayGrayBuffer`, which composes the real page.

Measured gap on the desktop, reader page turn: **13–22 ms**. Both passes reached
the screen, so every page turn showed a hard black-and-white rendering of the
page for a frame or two before the real one replaced it.

On the device that first pass is not a choice — an e-ink panel has to drive
every pixel hard before it can hold an intermediate level, and you watch it
happen. Reproducing it here reproduced the device's **process** rather than its
**result**, on a screen with none of the physics that made it necessary.

### The fix

`presentHoldUntil` in `src/HalDisplay.cpp`. A paint arms a **30 ms hold**; a
compose **releases** it. If the compose lands inside the window — the normal
case, every time — only the composed frame is presented and the 1-bit one never
reaches the screen. If no compose follows (every menu, every 1-bit screen) the
deadline expires and the frame presents anyway, at most 30 ms late.

**Nothing is ever dropped**: the hold returns *before* `pendingPresent` is
consumed, so the frame stays owed. Two callers flush it explicitly —
`deepSleep()` (the loop stops there, so a held frame would be the frame nobody
sees, and it is the sleep screen) and a due screenshot (headless QA asks for a
capture at a wall-clock instant and must not silently get a frame from 30 ms
later).

`CROSSPOINT_SIM_PRESENT_FLASH=1` restores the old behaviour.

### The wrong first attempt, recorded because it cost a cycle

The hold was first armed in `displayGrayscaleBase`, on the reasoning that the
grayscale path is the one that double-paints. **The reader never calls it.**
Instrumenting (`CROSSPOINT_SIM_LOG_PRESENTS=1`) showed `[base]` firing zero
times while `[compose]` fired on every page turn: the BW pass arrives through
plain `displayBuffer`, and the only signal that a compose is coming arrives
*after* it. There is nothing to key on, so the hold has to be unconditional.

### Evidence

`CROSSPOINT_SIM_LOG_PRESENTS=1`, three page turns, desktop:

| | presents | per page turn |
|---|---|---|
| `PRESENT_FLASH=1` (old) | 9 | two, 11–25 ms apart |
| coalesced (new) | 4 | one |

A present count alone cannot tell "the flash is gone" from "the composed page is
gone", so the log also tags which producer wrote the presented pixels:

```
=== PRESENT_FLASH=1 ===        === coalesced ===
[present] #8 at 11090 ms, from B   [present] #3 at 7132 ms, from G
[present] #9 at 11104 ms, from G   [present] #4 at 11106 ms, from G
```

`B` is the 1-bit pass, `G` the composed one. Coalesced, every page turn presents
exactly once and it is always `G`. The boot screen still presents from `B` —
it has no compose — which is the proof that a frame without a second pass is not
lost.

**A screenshot cannot photograph this**, because a due screenshot deliberately
overrides the hold. Hence the counter.

---

## 2. Beam paint (new setting)

**Ask:** "make beam paint a selectable setting of useful preset values."

A CRT does not swap pictures, it **draws** them: the beam runs top to bottom at
the field rate, and until it arrives a given line still shows the previous
frame. Separate claim from the glow — the glow says what becomes of a pixel
*after* it is lit, the beam says the picture arrives progressively.

`SimulatorOverlay::setBeamPaint(sweepMs)`; 0 is off and is the default and the
entire desktop behaviour. `CROSSPOINT_SIM_BEAM_MS` overrides it.

### Rows

| Stored | Row |
|---|---|
| 0 | Off — the page arrives at once |
| 17 | 17 ms — 60 Hz, a real field sweep |
| 33 | 33 ms — 30 Hz, just visible |
| 67 | 67 ms — slow enough to watch |
| 150 | 150 ms — deliberate |
| 300 | 300 ms — a wipe, not a tube |

**The stored value IS the duration, not a row index.** Unlike a palette preset —
which is an opaque name for a pair of colors and must therefore persist as an
integer that is never re-pointed — a duration is meaningful on its own, so rows
can be added, reordered or retuned with no migration table and no saved choice
silently changing speed. Clamped to 0..1000 on read.

### How it draws

The old picture is drawn opaque across the glass, then the new frame is drawn
clipped to the swept band. The clip is expressed against the **visible rect**,
not against the texture: in portrait the texture is rotated, so a band of
texture rows is a band of screen *columns*, and clipping in texture space would
sweep sideways. The clip is in the current render coordinate space — output
pixels on the manual path, logical units under SDL's letterbox — which is the
space the panel rect was computed in either way.

The previous picture is captured for the beam as well as for the glow, so the
beam works with the glow off.

**IT SWEEPS THE WHOLE FACE, since 2026-08-26** (owner: *"apply persistence and
other crt effects equally to paper and panel"*). It used to sweep the PANEL: the
old picture below the line was the previous panel framebuffer and the band was
the panel rect, so the button pad was painted afterwards, unclipped, and arrived
all at once. A tube has one gun and one raster. The old picture is now the
previous composed GLASS drawn 1:1 in device pixels, the band spans the output,
the overlay re-states the same band so the pad is swept too, and the letterpress
moved inside the clip (the old picture already carries its own). The accumulator
stays clipped to the band, deliberately — below the line the previous frame is
standing there with whatever trail it had, and lighting it again brightened the
un-swept region by 18% on a renderer without MAXIMUM.

That change also fixed something nobody had noticed: **the old picture used to
be the wrong picture.** The raw framebuffer reached the window by a different
resample from the one the live panel takes, so for the length of every sweep the
un-swept half was a blurrier, ~9% darker copy of the frame standing there a
moment earlier (band means 48.7/50.3 before the turn, 44.4/46.3 during the
sweep). It is now bit-identical. Measurements: `docs/whole-glass-crt.md`.

### Evidence

`CROSSPOINT_SIM_BEAM_MS=600`, capture mid-sweep, classifying every row that
differs between the two pages as showing the old page or the new one:

```
800 rows, 257 informative
topmost row still showing OLD page: 140
lowest row already showing NEW page: 139
map: NNNNNNNNOOOOOOOOOOOOOOOOOO
```

One clean crossing, no interleaving.

---

## 3. Two build-85 defects, both found by the owner on the phone

### The cascade was dead (P7)

**Report:** "cascade does not seem to work."

`PresetInfo::decayMs` for P7 is 1000 — this repo's reading of ">1 minute" — and
`pollPanelGlow` multiplied every row by a flat `kGlowScale = 20`. The phone
therefore asked for a **20-second trail**. At 900 ms such a ghost is still at 90%
of full and the cascade's color shift (which ramps with `1 - alpha`) has barely
begun, so the one phosphor whose entire identity is its afterglow was the one
that appeared to do nothing.

The desktop A/B that "proved" the cascade in the previous commit missed it
because `CROSSPOINT_SIM_PANEL_GLOW_MS` supplies the duration directly and never
runs that arithmetic. **The proof and the shipped path did not overlap.**

Fixed by moving the arithmetic to `panelpalette::trailMsForPreset()` — pure,
host-tested — and compressing the span as a square root anchored on P1:

| P | decay (interp.) | old, flat ×20 | now |
|---|---|---|---|
| P47 | 0.05 ms | 1 ms | 20 ms |
| P31 | 1 ms | 20 ms | 89 ms |
| P11 | 2 ms | 40 ms | 126 ms |
| P22R / P45 / P56 / P22B | 10 ms | 200 ms | 283 ms |
| P3 | 13 ms | 260 ms | 322 ms |
| P1 | 20 ms | 400 ms | **400 ms** (anchor) |
| P4 | 33 ms | 660 ms | 514 ms |
| P39 | 150 ms | 3000 ms | 1095 ms |
| P7 | 1000 ms | **20000 ms** | 2828 ms |

The published span is 1:20000. No single multiplier serves it — pick one that
makes the fastest visible and the slowest is unusable; pick one that keeps the
slowest usable and the fastest is a single frame. What survives compression is
the **order**, exactly, and the rough sense of proportion. What does not survive
is the literal ratio, and that is deliberate: 20 seconds is not a truer
rendering of P7 than 2.8 is, only an unusable one.

Also fixed: the cascade tint is now applied **only on the additive (dark-ground)
path**. A color multiply on a ghost whose paper is black touches nothing but the
lit ink, which is the intent; on the pale-paper cross-dissolve the same multiply
hits the paper too and washes the entire decaying frame green — a stain, not a
longer-lived layer.

### The antialiasing looked bad in CRT

**Report:** "the antialiasing on the sans serif fonts looks bad in crt."

An AA edge pixel is a pixel the glyph only partly covers, encoded as a level. On
a phosphor, half coverage means half the **light** — and light adds linearly,
while sRGB code values do not. `colorForLevel` blends in code space by contract
("no gamma"), so every edge pixel on a dark page was landing far too dark:

| palette (dark) | level | code-space | linear-light |
|---|---|---|---|
| Cascade | 128 | `626593` | `8F91BD` |
| Green | 192 | `0D530D` | `168A16` |
| Amber | 192 | `533800` | `8A5E00` |

Worst on a sans serif, whose long straight verticals are almost entirely edge
pixels at these sizes and which has no bracketing to hide the fringe.

`colorForLevelEmissive()` decodes both ends to linear light, mixes there, and
re-encodes. Endpoints are untouched by construction. `SimulatorOverlay::
setPanelEmissive(bool)` selects it; the iOS shim sets it from whether the preset
names a phosphor, `CROSSPOINT_SIM_PANEL_EMISSIVE` overrides it.

**It is not the default path.** `colorForLevel` stays the byte-for-byte contract
for every e-ink palette — a real e-ink panel's grays are pigment, not emission,
and its shipped look must not move. HalDisplay caches the 256-entry ramp per
palette, so the transfer function runs 768 times per palette change rather than
1.2M times per frame.

---

## 3b. The fringe was not the ramp: dark-mode AA was being discarded entirely

Follow-up to the AA fix above, found by actually looking ("check fringe
especially in dark mode"). The linear-light ramp was real but **could not have
fixed what was reported**, because there were no intermediate levels for it to
act on.

`GrayscalePreview::previewLevel` returned white for any base-white pixel,
discarding its plane flags, on the reasoning that the firmware only flags
base-black pixels. From the firmware's own table (`GlyphAa::planes`):

| | baseInk | consequence |
|---|---|---|
| light mode | `L0\|L1\|L2` | every coverage level painted as ink, flags arrive on BLACK, decode worked |
| dark mode | `L0` (Standard) | partial coverage NOT painted, flags arrive on WHITE, decode discarded them |

So with `darkMode: 1` every glyph edge was thrown away: 28,550 computed AA
pixels for one book page, all rendered as paper. The text was not badly
antialiased, it was **not antialiased at all** -- skeletal stems with hard
edges, worst on a sans serif because its long straight verticals are almost
entirely edge pixels at reading sizes.

Fixed by letting a flag win over the base in both polarities. Light mode is
provably unchanged: there a flagged pixel is already black, so both orderings
agree on every input the firmware emits, and `tests/grayscale_preview_test.cpp`
pins that with the firmware's own masks. Failing-first verified: 8 failures
against the old decode, all "edge is the page".

Measured on the same page, Green CRT dark:

| arm | levels | AA px | light gray | dark gray |
|---|---|---|---|---|
| build 86 | 2 | 0 | — | — |
| decode fixed | 4 | 3,637 | `32,169,32` | `11,76,11` |
| + linear light | 4 | 3,637 | `39,208,39` | `20,130,20` |

**The two fixes compound and neither is sufficient alone.** Note also that
`CROSSPOINT_SIM_DARK` does NOT reach this: the firmware picks its AA masks from
its own `darkMode` setting, so the env var changes the presentation polarity
while the masks stay put. A headless check of the light-mode path has to flip
the firmware setting, which is why the unit test carries that half.

## 4. The CRT rows are sorted (owner ask: "sort phosphors in a logical way")

Hue first, **fastest to slowest inside each hue**, cascade last as the only
two-layer row:

    Green Fast · Green · Green Long · Amber · Red · Red Projector ·
    Blue Fast · Blue · Blue TV · White · Gray · Cascade

Persistence is what distinguishes rows that share a hue — there are three blues
and three greens — so speed is the only ordering inside a hue that carries
information. Display order in `Root.plist` and the order of `kPresetInfo` were
changed together (the cycle button follows the settings order, and a test pins
them to each other). **No stored integer moved**, which is the whole reason the
picker can be reordered at all.

---

## What is still unconfirmed

Everything above is verified headlessly on the desktop. What a host cannot
check, and what build 86 is for:

- that the flash is actually gone *to the eye* on the phone;
- that the cascade now reads as blue-white → green rather than as a smear;
- that the AA fringe is gone on sans-serif body text;
- which beam row is the one worth keeping (17 ms may be too subtle to see at
  all on a 60 Hz panel, which is itself the interesting answer).


---

## 5. The flash that survived the flash fix (2026-08-18)

Owner, after §1 shipped: **"a flash on every redraw (page turn, row change on
home, etc)"**. §1 was real and is still right — it suppressed the 1-bit pass of a
two-pass paint. This was a different flash, in the composition rather than the
framebuffer, and it took three attempts because of where it was measured.

### Why every earlier measurement said "clean"

`CROSSPOINT_SIM_LOG_PRESENTS`'s luminance samples **`pixelBuf`** — the panel
framebuffer. That is upstream of the field clear, the page fade's alpha, the
glow accumulator, the beam and the overlay. **The flash lived entirely in the
blind spot.** Every present count and every luma figure taken through that
instrument was correct and irrelevant.

`CROSSPOINT_SIM_LOG_SCREEN=1` reads back the composed frame with
`SDL_RenderReadPixels` immediately before `SDL_RenderPresent`, over the
published panel rect. `CROSSPOINT_SIM_SCREEN_DUMP=<dir>` writes those frames as
BMP. That is the instrument this needed.

### What it was

Per pixel, over the page rect, on a reader page turn:

| | mean page luma |
|---|---|
| old page settled | 38.60 |
| **frame at the redraw** | **71.82** |
| new page settled | 37.89 |

99.77% of the page brighter than **both** pages; `mean |frame − (old+new)| =
0.11`; max luma 255 against 224 in either page. The frame was the arithmetic
**sum** of the two pages, to a rounding step — a drawn double exposure at ~1.9x,
decaying over about a second, on every content change. Home row changes measured
the same shape, which is why the report said "every redraw".

### The physics were wrong, not the arithmetic

`SDL_BLENDMODE_ADD` says two emitters stack. **A pixel lit in both frames is one
phosphor being re-excited**, and it cannot exceed full emission.
`SDL_BLENDOPERATION_MAXIMUM` is the saturating model: a pixel the new page
lights is exactly as bright as the new page draws it; a pixel only the OLD page
lit still shows and still decays, which is the entire point of a trail.

| | ADD | MAXIMUM |
|---|---|---|
| px brighter than both pages | 99.77% | **0.00%** |
| `mean │frame − max(old,new)│` | — | **0.00** |
| max luma | 255 (clipped) | 224 |
| peak lift over the old page | +58% to +86% | **−3.2%** |

Falls back to ADD at alpha 96 if a renderer cannot compose the custom mode.

### What remains, and it is not a bug

A one-frame double exposure in **coverage**: both pages' text legible at their
own brightness, decaying over the trail. That IS a phosphor trail. Whether it
still reads as objectionable is device-feel — **SHIPPED, UNCONFIRMED on device.**
What to watch for is the previous page's text briefly readable through the new
one, NOT a brightness spike; the spike is gone and measured gone.

### Also fixed here

The accumulator claimed to be live on a **pale** ground, where it draws nothing:
~30 presents per redraw, each a full clear, a 15 MB texture upload and a
render-target pass, for an identical picture. Measured 67 presents in a run,
now **4**.

### Harness traps that cost runs

- `simctl ui <dev> appearance dark` does **not** reach the app. `CROSSPOINT_SIM_DARK=1`
  does, because `setPanelDark` applies the override on every call. The flash is
  dark-ground + phosphor-preset only, so without that lever it cannot be
  reproduced at all.
- The data container GUID **changes on reinstall**. Re-resolve with
  `get_app_container` before editing `state.json`, or the seeded
  `readerActivityLoadCount` goes to a dead directory and the app resumes
  wherever it was.
- `pgrep -f "simctl launch"` matches the waiting shell itself, so wait-loops
  never exit.
- `simctl io recordVideo` captured 1.6 s and then went black in every run here.


## The flash became a setting, 2026-08-19

Owner: *"make that page-turn flash an option in ios settings, if possible"* —
and *"default to off"*, which is what already shipped.

`Page Turn Flash` sat under Beam Paint: **Off** (the page arrives composed) or
**On** (the 1-bit pass lands first, like the panel itself). Off was the default.

**Both rows are gone.** `presentFlash` left on 2026-08-22 with the palette rows,
and `beamPaintMs` with it when the sweep was hard set at 55 ms; the rest of the
Page Colors group followed on 2026-08-23. The behaviour is unchanged -- Off, and
composed -- but it is no longer selectable, and the desktop env
`CROSSPOINT_SIM_PRESENT_FLASH` is now the only way to see the flash at all.

One thing had to change to make it possible at all. `presentFlashWanted()` was a
`static const bool` initialised from `CROSSPOINT_SIM_PRESENT_FLASH` on first
call — the first present latched it for the life of the process, which is
exactly the shape a setting cannot have. It is an atomic now, written through
`SimulatorOverlay::setPresentFlash`, with the env still overriding so a headless
run can force either behaviour.

Verified end to end on the desktop by counting presents over the same script:
**3 presents with it off, 5 with it on** — the two extra being the un-coalesced
1-bit passes, which is the flash itself.

## 6. The flash fired every time and still "didn't work" (2026-08-20)

Owner, on build-108: *"fix presentFlash (it didn't work on my first try)."*

He was right, and the earlier "verified end to end, 3 presents off / 5 on" in
section 1 was also right. Both, at once: the setting produced its extra
presents, and the flash was still invisible.

### What was actually wrong

Presents run **continuously at ~15 ms** — idle repaints for the beam and the
grain, not just on new content. Against that, the numbers that mattered are:

| | 1-bit pass presented | how long it stays |
|---|---|---|
| flash off | never — the 30 ms coalescing hold swallows it | — |
| flash on, before this fix | yes | **~15 ms, one frame** |
| flash on, after | yes | **73 ms, measured** |

The compose lands only 13–22 ms behind the 1-bit pass, so "don't hold the 1-bit
frame" bought a single frame at 60 Hz and less at 120. `presentFlash` had no
deadline of its own — it only *declined* the hold — so there was nothing to make
the flash last.

### The fix

`kPresentFlashMs = 70`, and `presentFlashUntil` armed by the 1-bit pass. The
composed frame then waits out that deadline instead of replacing the flash on
the next repaint.

**Arm the hold at the TOP of `composeGrayscalePreview()`, before any pixel is
written.** The compose overwrites `pixelBuf` in place, so a present landing
mid-compose already shows composed pixels: holding at the tail freezes the NEW
page for 70 ms and lets the flash through in one frame — exactly backwards, and
measured that way at 12175/12190 ms before the placement was fixed.

### Evidence

```
CROSSPOINT_SIM_LOG_PRESENTS=1 CROSSPOINT_SIM_PRESENT_FLASH=$fl \
CROSSPOINT_SIM_INPUT_SCRIPT='4000:ENTER;12000:QTAP:RIGHT;18000:QUIT' \
SDL_VIDEODRIVER=dummy .pio/build/simulator/program
```
```
FLASH=1  1-bit frame presented at 12171 ms, on screen 73 ms
FLASH=0  no 1-bit frame ever presented at the page turn
```

### Two instruments that lied, both worth knowing

* **`lastPixelWriter` is sticky.** Every idle repaint carries the tag of the
  last writer, so "time from the last B-tagged present to the first G-tagged
  one" measures COMPOSE LATENCY, not how long a frame is on screen. It reads
  14–25 ms whatever the hold does, which is why an early version of this fix
  looked like it changed nothing. Use the **mean luma** column: the 1-bit frame
  (47.7) is distinct from both the old page (43.4) and the composed one (50.3).
* **A sampled counter hides a small effect.** The `[hold] suppressed %d` line
  printed every 25th suppression, so a hold that suppressed 4 frames printed
  `suppressed 1` — indistinguishable from a hold that never engaged, which is
  what it was misread as. Removed rather than fixed; the present timeline shows
  the gap directly.

Still **UNCONFIRMED on the phone** — 73 ms is a headless measurement of when
pixels are handed to SDL, and whether it reads as a page-turn blink is a
device-feel question.

## The beam does NOT sweep for a polarity reconvert — 2026-08-31

S-031, reported by the owner as zen flashing off and back on a dark/light
switch. A reconvert rewrites every pixel from the cached planes and bumps
`pixelBufSeq` exactly like a new page, so the sweep trigger armed and revealed
the NEW palette over the OLD one top-down across the sweep — frames with the
top of the page in one palette and the rest in the other, the sheet's geometry
never moving. `reconvertSeq` in `src/HalDisplay.cpp` marks a bump produced by a
reconvert, and the trigger withholds the sweep for exactly that seq: the frame
still uploads and presents, there is simply no new picture to sweep IN.

Verified by reproduction through the RESUME trigger (S-033's path holds the
split until the next present, which is what makes it capturable): present on a
pre-fix binary, absent at HEAD, twice. A page turn still sweeps.
