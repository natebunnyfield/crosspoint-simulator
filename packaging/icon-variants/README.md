# Striped app icon variants

Candidate app icons that replace the shipping mark's flat fill with a line
screen. Nothing in the build reads this directory — it is design exploration,
parked next to the packaging code because that is where the icon pipeline lives.

Regenerate with:

```bash
python3 packaging/icon-variants/make_striped_icons.py
```

## Why they are generated rather than drawn

There is no vector source for the CrossPoint mark in this repo;
`ios/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png` *is* the master. Any
variant drawn by hand would be a second, slightly-wrong copy of the shape, and
every later variant would inherit that error. So the generator reads the ink
coverage out of the master and uses it as a mask: each variant's silhouette is
the current icon's, exactly, down to its antialiased edges. Only the fill
changes.

## What the master measures

Three numbers off the artwork drive every default in the generator:

| Measured | Value | Why it matters |
|---|---|---|
| Page edge angle | atan(3/5) = 30.96° | `PAGE_ANGLE` is its complement, because the angle parameter names the stripe's *normal* — see below. |
| Stroke width | 46px at 1024 | A stroke's deepest interior point is ~23px from an edge. This sets the rim — see below. |
| Ink bounding box | 626 x 696 at (198,164) | Stripe phase is anchored to its centre, so changing pitch grows stripes outward from the middle rather than sliding them sideways. |

The mark is *not* symmetric — the top-left counter is a parallelogram and the
bottom-right one a triangle — so there is no symmetry axis to align stripes to.
Anchoring on the bounding box centre is a registration choice, not a symmetry
one.

## The angle convention, and a trap in it

**An angle in the variant table names the stripe's normal, not the stripe.**
A stripe parallel to an edge therefore needs the edge's angle plus 90 — and for
this mark the two are complementary, edges at 30.96° and `PAGE_ANGLE` at
59.04°. Passing `DIAGONAL_ANGLE` as a stripe angle produces stripes that look
plausibly diagonal while being *exactly perpendicular* to the page edges, which
is what every "diagonal" variant in rounds one and two turned out to be.

Measured rather than assumed — stripe slope is `dx/dy = -tan(angle)`, and the
page edge's is −5/3:

| Angle passed | Stripe slope | From horizontal | Versus the page edge |
|---|---|---|---|
| 30.96° | −0.600 | 59.04° | perpendicular |
| 59.04° | −1.667 | 30.96° | **parallel** |

That one fact explains round two's ranking. `matched-counter` read cleanest
because its lines met the right page's top edge at exactly 90°;
`matched-diagonal` wedged because it met that same edge at a shallow 28°, so
its line ends drew long tapers.

## Round five: `facing-*`

The current direction. The lower sheet — the bottom-left mass, the right
page's continuation under the fold — has its own edges on the *other*
diagonal, top-left to bottom-right, so round four's single-direction ruling
cut across its grain. Here each sheet is ruled along its own fold:
the upper page keeps its direction, the lower sheet rotates to the mirrored
angle, and the two read as the facing pages of the open book. Its two lines
re-fit at 43.5px gaps (was 44.4 across the grain); the upper page is
untouched.

`mass_angles` carries the per-sheet directions, listed bottom-left mass first
(the order `deep_components` returns them). The flush-stop cap for a filled
counter is measured along the swallowed mass's own angle, so `uniform-solid`
regenerates byte-identically.

| File suffix | Bottom-right counter |
|---|---|
| `facing-paper` | Left as paper |
| `facing-ruled` | Ruled with the lower sheet — the lower band reads as one chevron |
| `facing-single` | A single line of the lower sheet's ruling |
| `facing-upper` | Ruled with the upper page instead |
| `facing-solid` | Filled — measured on the filled geometry |

## Round four: `uniform-*`

One direction throughout, what the rotation was made against. **Nothing in the icon is drawn at a weight the mark does
not already use:** line, gap and rim are all `STROKE_WIDTH`, so a ruled line
running into an outline merges into one continuous stroke instead of reading as
two elements that happen to touch. Both masses are ruled — nothing is held
flat. The only thing that varies is the bottom-right counter.

| File suffix | Bottom-right counter |
|---|---|
| `uniform-paper` | Left as paper |
| `uniform-ruled` | Ruled to match, two lines |
| `uniform-single` | Carrying a single line |
| `uniform-mirror` | Ruled the mirrored way, as if it were the facing page |
| `uniform-solid` | Filled, the only flat area in the mark |

**The gap is solved for, not chosen.** A periodic pattern and a rim are
independent: the phase decides where the first and last bands fall relative to
the rim, and nothing makes that land well. With line = gap = rim = 46 a scan
across the right page ran

    ink 48 | gap 10 | ink 46 | gap 46 | ink 46 | gap 42 | ink 90

— perfect in the middle, and at the ends a 10px sliver next to a 90px slab
where a line had merged into the rim. So `fit_ruling` solves each region
instead: it spans `t_max - t_min` between its two rims and fills it with `n`
lines and `n+1` gaps,

    span = n*line + (n + 1)*gap

taking whichever `n` puts the gap nearest the line width. Every line is then
exactly 46, every gap in a region is identical, and both ends land flush — no
phase is left free to produce a sliver. Gaps differ slightly *between* regions
(56.0 in the deeper right page, 44.4 in the left mass, 43.2 in the counter),
which is the price of none of them being ragged.

There is no out-of-phase variant, and there cannot be: fitting determines each
region's phase, so "offset by half a period" is exactly the sliver this
solves.

**A filled counter is not a counter.** `uniform-solid` measures its geometry on
the mark the fill leaves behind. Filling afterwards laid the ruling out around
a hole the finished icon does not have, and left the rim arcing around an apex
that was no longer there. Its ruling also stops flush on the fill's leading
edge — which is parallel to the ruling — rather than being fitted across the
merged region, since fitting across the pair puts a gap astride that edge and
leaves a wedge of paper sitting on top of the fill.

**A counter is paper, not ink**, which is why it needed new machinery. Every
other treatment in this file operates on the ink mask; a counter is the paper
the mark *encloses*. `paper_counters` floods from the canvas border to mark the
outside, then labels whatever paper is left — two regions, a parallelogram
top-left and a triangle bottom-right, which separate on `cx + cy`.

`grown_counter` then widens that membership by one pixel into the mark's own
edge antialiasing. Without it, filling a counter solid leaves the boundary's
part-grey pixels untouched: a visible hairline tracing the old edge through the
middle of a filled black area.

## Round three: `page-*`

Round two's construction with the lines lying *along*
the right page rather than cutting across it, so they read as text ruled on the
page. Line and gap are what vary, and they are what the filenames carry —
`page-<line>-<gap>`, in master pixels at 1024.

| File suffix | Line | Gap | Reads as |
|---|---|---|---|
| `page-21-21` | 21 | 21 | Even rule — round two's #4 ruling, turned onto the page |
| `page-10-26` | 10 | 26 | Ruled text — closest to text on a white page |
| `page-30-30` | 30 | 30 | Even rule — fewest, heaviest lines; best downscale |
| `page-12-12` | 12 | 12 | Even rule — twice the line count |
| `page-7-21` | 7 | 21 | Ruled text — hairline at 1:3 |
| `page-26-10` | 26 | 10 | Inverted — ink is the field, gaps are the ruling |

`page_variant(line, gap)` derives pitch and duty from that pair, so the set is
specified in the terms actually being compared rather than in the generator's.

## Round two: `matched-*`

Every outline in the icon reads at one weight, and only the top-right mass
carries the line screen. Superseded by round three only in the angle: the
construction is identical.

| File suffix | Cut |
|---|---|
| `matched-counter` | 59°, square across the page's top edge |
| `matched-vertical` | Vertical, running with the side bars |
| `matched-horizontal` | Horizontal |
| `matched-horizontal-fine` | Horizontal at a finer pitch |
| `matched-diagonal` | 59° the other way, shallow to the page edge |
| `matched-diagonal-fine` | The same, at a finer pitch |

**The rim is the stroke width, and that is not a coincidence twice over.** A
keyline variant holds a solid rim around every edge and stripes only what is
deeper than the rim. Round one used 26px, which merely *worked*; it reads as a
thinner outline around the top-right mass than around the side bars and the
counters, so the mark looks drawn with two pens. Setting the rim to the mark's
own 46px stroke makes every outline one weight.

The same number is also what makes "keep the bottom-left mass flat" possible.
The mark is one connected shape — its two masses meet at the centre crossing —
so labelling connected ink cannot tell them apart. Labelling the interior
*deeper than the rim* can, but only once the rim is wide enough to drown that
crossing. Measured on the master:

| Rim | Islands found |
|---|---|
| 26px | **one** — the masses are still bridged at the crossing |
| 40px | two |
| 46px | two: 70,971px centred (655,425) and 28,972px centred (318,685) |

Below ~40px every mass is "the bottom-left mass", and a variant asking to hold
one flat would silently emit the unmodified icon. `build` raises rather than
writing that file.

Angle is the only real choice left in this round, and incidence against the
page's top edge is what ranks them — 90° for `matched-counter`, 28° for
`matched-diagonal`, which is why the latter's line ends taper.

## Round one

Kept as the record of what those corrections were made against. Both masses are
striped and the rim, where there is one, is 26px.

| File suffix | Treatment | At 32px |
|---|---|---|
| `keyline-horizontal` | 26px keyline, horizontal stripes in both masses | Holds |
| `keyline-diagonal` | 26px keyline, 59° stripes in both masses | Holds |
| `grooved-horizontal` | Thin horizontal grooves, duty 0.72 | Holds |
| `grooved-diagonal` | Thin grooves at 59°, duty 0.72 | Holds |
| `horizontal-fine` | Fine line screen, duty 0.5 | Greys out |
| `horizontal` | Bold 50/50 horizontal | Breaks the side bars |
| `vertical` | Bold 50/50 vertical | Breaks the diagonals |
| `diagonal-counter` | Bold 50/50 at 59° | Breaks the mark |
| `diagonal-steep` | Bold 50/50 at 59°, the other way | Breaks the mark |

**Duty cycle decides whether the mark survives, not angle.** At duty 0.5 a
46px stroke lands on a 32px gap often enough to break into dashes — that is
what happens to the side bars in `horizontal`, and to the top-left stroke in
`diagonal-steep`, which its stripes cross at exactly 90° and chop into even
dashes. The `grooved-*` variants run duty 0.72 for exactly this reason: the
mark stays continuous and the stripes read as cuts in the fill rather than as
gaps between fragments. Angle only decides *which* strokes take the damage.

## Tuning

```bash
# One variant, at a coarser pitch and with more paper showing.
python3 packaging/icon-variants/make_striped_icons.py \
    --only page-10-26 --pitch 96 --duty 0.6
```

`--pitch` is centre-to-centre at 1024 and scales with the source; `--duty` is
the ink fraction of a stripe and overrides each variant's own. Both are the
levers worth turning first. Rim and which masses stay flat live in the variant
table (`rim=`, `solid_masses=`).

## Adopting one

The variants are the same kind of file as the master — 1024x1024, 8-bit,
non-interlaced, opaque black on white — so adopting one is a copy:

```bash
cp packaging/icon-variants/AppIcon-1024-striped-<name>.png \
   ios/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png
```

Both platforms follow from there: iOS reads that file directly, and the macOS
`.icns` is derived from it at package time by
[../macos/make_icns.py](../macos/make_icns.py), so the two cannot drift apart.
Verify with:

```bash
python3 packaging/macos/make_icns.py --output /tmp/check.icns
```

Judge candidates at 32px before committing. A line screen that reads well at
1024 can collapse into flat grey in a Finder list, and the icon is judged in
both places.
