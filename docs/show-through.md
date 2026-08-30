# Show-through from the other side of the leaf

2026-08-23. Roadmap item **1a**, the first of the three approved off
[surface-roadmap.md](surface-roadmap.md) §6. Model:
[src/ShowThrough.h](../src/ShowThrough.h). Test:
[tests/show_through_test.cpp](../tests/show_through_test.cpp). Composited into
the sheet field in `ensureSheetToothTexture`, which moved from
`HalDisplay.cpp` to [src/SurfaceSheet.cpp](../src/SurfaceSheet.cpp) on
2026-08-25.

**Light mode only** — it is the paper half of the 2026-08-22 doctrine, and it
rides the letterpress sheet pass, so it draws exactly where that pass draws and
nowhere else.

## What it is

Paper is not opaque. On any stock under about 90 gsm the ink on the *verso* is
faintly visible from the recto: not readable, but a soft mottling that follows
the text block's shape — strongest in the line band, absent in the margins. On
bible/India paper it is the defining characteristic, which is the whole reason
that stock is famous.

It is the one paper phenomenon in this model that carries **information** rather
than texture. Every other pass on the sheet — tooth, formation, wires, marks —
is stationary noise. This one is a picture of another page, and it is the thing
that most reliably makes a mock page read as paper rather than as a texture over
a screen, because no screen does it.

## Settings: FROZEN, and why

There is no Settings.app row and there is no in-app slider. The dial is frozen
(`CrossPointPrefs_showThroughPercent`), and the quantity that genuinely
varies — **how thin the sheet is** — is already a choice the owner makes, in the
paper picker. A second control beside it would be two authorities over one
number, and the 2026-08-23 settings purge is the standing ruling on decoration.

**The frozen value is 50, HALVED from 100 on 2026-08-24** — owner: *"half the
verso bleed visibility."* The original 100 was the reference sheet's own
show-through, and with India's 3.0x stock factor that landed on
`showthrough::kStrengthMax` (300) *exactly*: the shipped page was carrying the
most show-through the model can express, on the thinnest paper in the list. 50
puts India at 150 — half the visibility and half the sheet's darkening-budget
share — with the STOCK still doing all the varying. Every "at 100" figure below
is therefore the model's own ladder, not what the app ships; the shipped page is
half of it. The reasoning is kept in full at `ios/CrossPointPrefs.mm:505`.

So the number that reaches the SDL side is the frozen dial times the STOCK's own
factor, composed at the pusher exactly as tooth and formation are
(`ios/CrossPointLightInkPicker.mm`, `showThroughPercentFor`).

`CROSSPOINT_SIM_SHOW_THROUGH=<percent>` is the desktop override, and the desktop
default is **0** — off, bit-exact, so the canary and every headless capture stay
byte-identical to what this repo drew before the feature existed.
`showThroughPercent` in `settings.json` is the same value for a packaged Mac app.

## The per-stock ladder, and why it is a ratio of transmissions

`lightink::showThroughScaleFor(paperIdx, strengthPct)` is the third member of
the `toothScaleFor` / `formationScaleFor` family, and the only one derived from
a measurable absolute rather than from a chosen ordering.

Each stock carries an `opacity` field: ISO 2471 opacity, the fraction of
incident light the sheet does NOT pass. What shows through is what gets
*through*, so the factor is the ratio of **transmissions**,
`(1 - opacity) / (1 - opacity_reference)` — not of opacities. Bright White's
0.94 is the reference.

| Stock | Opacity | Factor | Note |
|---|---|---|---|
| Kozo | 0.78 | **3.67x** | unbleached washi, thin and open |
| India | 0.82 | **3.00x** | bible paper; this is its identity |
| Newsprint | 0.92 | 1.33x | thin, but groundwood scatters hard |
| Cream | 0.93 | 1.17x | bulky trade stock |
| Bright White | 0.94 | 1.00x | the reference sheet (shipped default) |
| Bone | 0.94 | 1.00x | |
| Sepia Toned | 0.94 | 1.00x | |
| Chamois | 0.95 | 0.83x | heavier aged sheet |
| Press Gray | 0.95 | 0.83x | |
| Azzurrata | 0.96 | 0.67x | blue rag drawing stock |
| Brightened White | 0.96 | 0.67x | premium coated, mineral-filled |
| Laid Antique | 0.97 | 0.50x | heavy handmade |
| Vellum | 0.985 | **0.25x** | calfskin: nearly opaque |

The opacities are plausible grade values rather than measurements of these exact
sheets — the reference figures are the ones the trade publishes (book text
stocks 0.92–0.96, bible papers 0.78–0.88, coated and filled sheets higher). The
test pins the ORDERING and the two extremes, which is what the feature depends
on; it does not pretend the third decimal is measured. The ladder rides the
paper-strength dial linearly, exactly as tooth and formation do, and is exactly
1.0 for every stock at strength 0.

## The honesty problem, stated plainly

**What shows through page N is page N+1. This ships page N−1.**

A book read forwards means the ghost is the page you just left, not the page
behind the leaf. Three options were considered:

1. **Ship the previous page and say so.** Chosen. A show-through is never
   legible; nobody can tell which page it is. The *statistics* are right — same
   font, same measure, same line grid, same paragraph rag, same chapter-opening
   white — and that is all the eye is reading.
2. Ask the firmware to render N+1 into a scratch buffer. Correct, and expensive:
   a second pagination and a second render per page turn on a device whose whole
   design is "render rarely".
3. Synthesize plausible line bars. Fake, and it looks fake the first time the
   real page has a chapter opening.

The choice is recorded in the code as well as here, above `versoMap` in
`HalDisplay.cpp`.

## The source is the inkness plane, NOT the previous frame

The roadmap proposed `ghostPixels` — a whole previous framebuffer HalDisplay
kept. **Verified 2026-08-23: it existed (`src/HalDisplay.cpp`, the
`wantPrevFrame` block in `presentIfNeeded`) and it was the wrong source**, on
three counts:

*(2026-08-26: `ghostPixels` has since been deleted. The previous picture is now
captured from the composed GLASS at output resolution — `whole-glass-crt.md` —
which makes all three objections below stronger, not weaker: it is one step
further from the page's own ink than the framebuffer was.)*

- it is maintained only while the phosphor trail or the beam is on, and both are
  dark-mode ideas that are off on a paper page;
- it is ARGB that would have to be re-projected onto the palette's ink/paper
  axis to be useful at all;
- it is a copy of the previous **frame**, and an antialiased page produces two
  frames (the 1-bit pass and the compose), so the "previous frame" is routinely
  the same page.

The letterpress pass already computes exactly the quantity wanted — a 0..255
inkness plane, per page, in light mode — so show-through takes that instead, for
free. Promotion happens on the **page seed**, not on `pixelBufSeq`: the seq
increments twice per displayed page, and promoting on it would put the same page
behind itself half the time.

## How it is built and drawn

1. **Downsample.** The inkness plane is box-averaged into `kCellPx` (8
   framebuffer px) cells. The box average is the only prefilter, and it is
   load-bearing: point-sampling a 1-bit dithered page at a stride of 8 would
   carry the dither's lattice into a field that must have no lattice at all —
   ST-008 arriving through the back door. The test pins it.
2. **Blur.** Two passes of a separable binomial `[1 4 6 4 1]`, edge-clamped
   (wrapping would carry the last line of text onto the head margin). Combined
   with the cell's own box that is ~11 framebuffer pixels of spread: letters
   gone, line bands intact. The test measures both — horizontal swing inside a
   line band drops below the vertical swing down a column.
3. **Promote.** On a page-seed change, the recto map becomes the verso map and a
   generation counter increments. That counter is a sheet-field cache key: every
   other thing about a page can be unchanged while the leaf behind it is a
   different page.
4. **Mirror and place.** The verso is the BACK of the sheet, so it is mirrored
   left-to-right. **The mirror is applied in PRESENTED output pixels, not in the
   framebuffer** — the framebuffer is landscape and the page is rotated into it,
   so a mirror about the framebuffer's x axis is a mirror about the page's
   *vertical* axis, i.e. upside-down show-through. `showthrough::mirrorOutputX`
   is that, and the test pins it as an involution that swaps the page's edges.
5. **Resample.** The mirrored point is inverted through the presentation
   (`outputToPanel`) on a coarse `kOutCellPx` = 4 output lattice and bilinearly
   interpolated per pixel. The field is a heavy blur, so a 4 px grid loses
   nothing; inverting a rotation and four clamps 3.4 million times per page turn
   is the cost this avoids.
6. **Fold.** Into the same MOD field the tooth writes, inside the tooth's own
   loop — one traversal, not two.

## The budget, now split four ways

Show-through darkens paper, so it is the fourth consumer of the 7:1 headroom.
What the tooth leaves (`letterpress::remainingPaperBudget`) is shared in this
order:

    wires        take 1/2 of it
    show-through takes 1/2 of what remains
    marks        take the rest

Every share is a MEAN bound and each pass clamps its own depth to fit, so the
composite cannot breach the floor by construction. **With show-through at 0 its
bound is exactly 0 and the marks receive precisely the number they received
before the feature existed**, which is what keeps a wove sheet byte-identical.

`showthrough::meanDarkeningBound` is the declared share; the test proves the
real mean over a dense synthetic page never exceeds it.

## Measurements, 2026-08-23

Desktop, X3 profile at 2x render scale, output 1056x1584, twelve consecutive
`QTAP:RIGHT` page turns of a real EPUB, medians, cold first build excluded,
`CROSSPOINT_SIM_LOG_TIMING=1`.

| Output size | Sheet field, off | Sheet field, 100% | Sheet field, 300% | Verso map (in the panel pass) |
|---|---|---|---|---|
| 528x792 (0.42 Mpx) | 31.9 ms | 31.9 ms | 34.3 ms | +0.6 ms |
| 1056x1584 (1.67 Mpx) | 120.6 ms | 131.3 ms | — | +0.6 ms |

Both the field and its cost are OUTPUT-space and scale with output pixels, which
puts show-through squarely in §4c's **~30 ms class** rather than the ~490 ms
panel-space class: extrapolated to a phone's 3.4 Mpx it is roughly **+22 ms per
page turn**. A still page costs nothing — the field is cached and the idle
present is unchanged at 3.9 ms.

The verso map costs +0.6 ms and is framebuffer-sized, so it does not grow with
the presentation.

### Effect delta (proof figures)

Off vs on, identical card state, identical page, PNG at native pixels:

| Arm | Whole frame mean\|d\| | max\|d\| | %px > 4 | signed |
|---|---|---|---|---|
| Bright White (stock 1.00x) | 0.373 | 6.0 | 1.25% | **−0.373** |
| India / Kozo class (3.0x) | 1.139 | 17.0 | 10.64% | **−1.139** |

In the 256x256 crop under judgment (content coverage 17.1%): Bright White
mean 1.98 / max 6.0 / 9.3% of pixels past 4 levels; India mean 6.02 / max 17.0 /
55.8% past 4 levels.

**The signed mean is negative in every arm and at every pixel**, which is the
darken-only invariant measured rather than asserted.

## Failure modes the test exists for

Every one is silent:

- a pass that LIFTS is the page-flash bug class;
- an "off" that is nearly-off is a change to every install that never asked;
- a mirror in the wrong coordinate space is a page that shows through
  upside-down, which reads as noise rather than as a leaf;
- a point-sampled downsample puts the dither's lattice into a low-frequency
  field;
- a fourth budget consumer that does not declare its share puts a reading page
  under 7:1.

The 7:1 sweep runs the six tightest ink x paper pairs this repo ships against
every offered strength and every stock, measuring the mean multiplier over a
real page's blurred verso density rather than assuming one.
