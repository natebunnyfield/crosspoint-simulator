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

The old frame is drawn opaque across the panel, then the new frame is drawn
clipped to the swept band. The clip is expressed against the **visible page
rect**, not against the texture: in portrait the texture is rotated, so a band
of texture rows is a band of screen *columns*, and clipping in texture space
would sweep sideways. The same rect serves both presentation paths because the
clip is in the current render coordinate space — output pixels on the manual
path, logical units under SDL's letterbox — which is the space the panel rect
was computed in either way.

The previous frame is captured for the beam as well as for the glow, so the
beam works with the glow off.

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
