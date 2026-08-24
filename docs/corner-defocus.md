# Corner defocus

2026-08-23. Roadmap item **D3**, "the cheapest real item on this list"
([surface-roadmap.md](surface-roadmap.md) §3). Model:
[src/CornerDefocus.h](../src/CornerDefocus.h). Test:
[tests/corner_defocus_test.cpp](../tests/corner_defocus_test.cpp). It modulates
the scanline field (`HalDisplay::ensureScanlinesTexture`) rather than drawing
one of its own.

**Dark mode only**, and only where scanlines are: with
`scanlinesPercent` at 0 this does nothing at all.

## What it is

A deflected beam lands further from the gun and at an oblique angle, so the spot
is both LARGER and ELLIPTICAL, its long axis pointing radially outward.
Dynamic-focus circuits drive the focus electrode from a signal proportional to
X² + Y², which is why the correction — and therefore the residual error — is a
**parabola in the radius** and not a linear ramp.

    a(r) = 1 + kRadial     · r²      the long, radial axis
    b(r) = 1 + kTangential · r²      the short, tangential axis

with r normalized to 1 at the screen corner. The scanline field only ever
samples the spot's **vertical** extent (a scan line is the spot dragged
horizontally), and the vertical semi-axis of that ellipse is a closed form:

    σ_y = sqrt( (a² dy² + b² dx²) / r² )

which is `a` at the top and bottom, `b` at the left and right, and exactly 1 at
the centre. The consequence falls out for free and is the physically right one:
**the raster softens most at the top and bottom, where the radial direction is
nearly vertical, and not at all at the left and right, where the spot spreads
sideways and the lines stay crisp.** Measured, as shipped: corners −41%, top
edge midpoint −40%, left edge midpoint −0.0%, centre −0.0%.

## Ellipticity, not isotropic blur

The roadmap's refinement, taken: an isotropic blur reads as "the corner text is
worse", an ellipse reads as character. The test pins the difference — top edge
and side edge sit at the same normalized radius, so an isotropic model would
make them equal, and that is exactly the check that fails it.

## Magnitudes, and the one published bound

TG18 gives no spot size in mm for a monochrome tube. It states the direction
("the corners always yield lower values than the center", §4.5.4.2.1) and one
hard limit: the corner **astigmatism ratio**, long axis over short, must stay
under **1.5** for primary-class reading.

Shipped: `kRadial = 0.45`, `kTangential = 0.18`, giving a corner spot 1.45x the
centre's and a ratio of **1.229** — inside the bound with room. The widely
repeated "0.1–0.2 mm centre vs 0.3–0.5 mm corner" figure is deliberately NOT
used: it is about colour convergence, not mono spot size, and the roadmap
already flagged it as unsourced.

## It softens without lifting, and that is the whole design

The period-mean of the raw scanline sum is the area under one line's profile
divided by the pitch, which is **linear in sigma**. So `rowTransmission` divides
by the defocus scale: the mean stays exactly where it was and only the
modulation is removed.

Without that division a wide spot's integral simply grows and the corners read
as **lit** — the page-flash bug class wearing a physics argument. With it:

- a corner is blurrier, not brighter and not darker;
- the 7:1 budget is untouched (proven by sweep, not deduced);
- there is no setting at which a corner is *sharper* than the centre.

**The divide must apply to the defocus and NOT to the bloom**, and getting that
wrong is the one real bug this work produced. Bloom and defocus both scale the
same sigma, so the obvious economy is to bucket their product and keep one table
axis. It is arithmetically identical inside `rowTransmissionRaw` and wrong at the
normalization — bloom *spares* light and must not be divided out. Collapsed onto
one axis it softened the raster by 27% **at the centre**, where the defocus
scale is exactly 1. Caught by measuring off vs on per screen region; it passes
every other check.

## Settings: FROZEN, and why

No row. The corner spot's growth is set by a tube's geometry under a published
bound, not by taste, and TG18's 1.5 limit leaves no interesting range to offer.
`CrossPointPrefs_cornerDefocusPercent` returns 100.

`CROSSPOINT_SIM_CORNER_DEFOCUS=<percent>` is the desktop override and the
desktop default is 0 (bit-exact off, canary unchanged);
`cornerDefocusPercent` in `settings.json` is the same value for a packaged Mac
app.

## Cost, and the shape it had to take to be affordable

`sigmaScaleAt` is a divide and a square root per pixel, and it depends on the
output size and the dial and on nothing else — not the page, not the palette,
not the content. So it is computed ONCE into a byte map (`defocusMap`, keyed on
size and strength) and read on every page turn thereafter. Computing it 3.4
million times per page turn would have cost more than the raster it modulates.

The table is `(row, level bucket, defocus anchor)` with **3 anchors**
interpolated per pixel. Five were measured first and cost +13.5 ms per page turn
against three at +10.3; the extra accuracy was not visible. The summation window
stays fixed at ±2 lines at every sigma — the historical behaviour, and the same
treatment bloom already gets; widening it with the scale cost **+93 ms** per dark
page turn (the window grows with the product of bloom and defocus, so at Extreme
bloom it reached 27 lines) and moved the corner's mean by under a twentieth of a
code value.

Measured, `CROSSPOINT_SIM_LOG_TIMING=1`, twelve page turns, medians:

| Output size | Scanline field, off | Scanline field, on | Page turn total |
|---|---|---|---|
| 528x792 (0.42 Mpx) | 40.7 ms | **51.0 ms** (+10.3) | 71.3 → 80.8 ms |
| 1056x1584 (1.67 Mpx) | 135.9 ms | **159.4 ms** (+23.5) | 171.4 → 198.0 ms |

Extrapolated to a phone's 3.4 Mpx that is roughly **+42 ms per dark page turn**,
which is above §4c's ~30 ms output-space class. A still page is unchanged
(cached; idle present 7.2 ms in both arms).

## What it looks like, measured — and the finding

**A/B captures of this field MUST pin `CROSSPOINT_SIM_GRAIN_SEED`.** The
raster's phase jitter, thickness jitter and mottle all hang off `grainSeed()`,
which is re-rolled every launch, so two runs of the same dials differ by ~2.2
code values before any dial is touched — larger than the effect. That cost a
wrong reading on 2026-08-23 and the note now sits above `ensureScanlinesTexture`.

Raster peak-to-peak (row means over a 192 px patch), pinned seed, identical page:

| Patch | As shipped, off → on | Deepest raster the model allows, off → on |
|---|---|---|
| Top-left corner | 1.79 → 1.05 (**−41%**) | 7.55 → 6.33 (−16%) |
| Top edge midpoint | 1.79 → 1.07 (−40%) | 7.60 → 6.40 (−16%) |
| Left edge midpoint | 1.79 → 1.79 (**±0%**) | 7.36 → 7.27 (−1.3%) |
| Centre | 1.79 → 1.79 (**±0%**) | 6.65 → 6.62 (−0.5%) |
| Bottom-right corner | 1.79 → 1.00 (−44%) | 6.34 → 5.24 (−17%) |

**And here is the finding.** The whole-frame delta is `mean |d| = 0.039`,
`max |d| = 1.0` **code values** as shipped, and 0.196 / 2.0 at the deepest raster
the model can produce. No honest native-pixel crop can show this: the figure
fails proof-check 3 and it fails it for a real reason, which is that the
scanline raster the shipped tube draws is only **1.8 code values peak-to-peak on
the dark ground**, and 40% of 1.8 is 0.7.

Two things follow, and they should be decided rather than assumed:

1. Sub-code-value is **not** the same claim as imperceptible. What moved is the
   depth of a *periodic* field, which the visual system integrates over many
   cycles; periodic-pattern detection thresholds sit well below a single code
   value. This has not been confirmed on a device and is marked **SHIPPED —
   UNCONFIRMED on device**.
2. It costs ~42 ms of a dark page turn on the phone. If the owner judges it
   invisible, the right move is `cornerDefocusPercent` → 0 and the whole pass
   costs nothing again; the model, the wiring and the test stay banked, and it
   becomes worth its cost the moment the raster is made deeper (a lower bloom or
   a higher scanline intensity).

## Failure modes the test exists for

- a scale below 1 SHARPENS the corner, which no tube does;
- an isotropic scale reads as "the corner text is worse", and only a directional
  test separates the two;
- a field that forgets to divide the widening out of its own normalization lifts
  the corners;
- an "off" that is nearly-off changes every dark page silently.

`multiplierAt` with a sigma scale of exactly 1 is asserted byte-identical to the
call that predates this feature, and the HalDisplay off-path is the original
code untouched rather than a special case of the new one.

## OPEN: is it visible? (owner ruling 2026-08-23)

The measurement is honest and it does not settle the question. On this app's
rasters the corner loses **41%** of its peak-to-peak depth while the centre and
the side midpoints lose **exactly 0%** -- the ellipse doing precisely what it
models -- but whole-frame deviation is **1.0 code value**. No native-pixel crop
can show that, so the figure fails the repo's third proof check and none was
faked.

Sub-code-value is not the same claim as imperceptible: what moved is the DEPTH
OF A PERIODIC FIELD, and the eye integrates a repeating structure differently
than it does an isolated pixel. So the numbers argue both ways and the owner
ruled to decide it on the phone instead.

**The probe is a Settings row**, `Screen Test > Corner Defocus`, default on.

It was a `defaults` key first, and that was a mistake worth recording: on a
TestFlight build the owner has no shell, so the probe could not be reached by
the one person whose eyes the question needed. **An on-device question needs an
on-device control.** The row costs a line in a Settings screen that spent the
same day being emptied, and it is labelled temporary in its own footer.

**It is a probe, not a setting.** Delete the branch once the question is
answered. Its cost is real -- roughly **+42 ms per dark page turn on a phone**,
above the ~30 ms class the timing work calls cheap -- so "leave it on because
nobody minds" is not a free answer.
