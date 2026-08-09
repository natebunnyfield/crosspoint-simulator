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
| Diagonal angle | atan(3/5) = 30.96° | The "parallel" variants run with the mark instead of cutting an unrelated angle across it. |
| Stroke width | ~46px at 1024 | A stroke's deepest interior point is ~23px from an edge, which sets the keyline rim. |
| Ink bounding box | 626 x 696 at (198,164) | Stripe phase is anchored to its centre, so changing pitch grows stripes outward from the middle rather than sliding them sideways. |

The mark is *not* symmetric — the top-left counter is a parallelogram and the
bottom-right one a triangle — so there is no symmetry axis to align stripes to.
Anchoring on the bounding box centre is a registration choice, not a symmetry
one.

## The variants

Ordered as the generator emits them: from the treatment that protects the mark
most to the one that takes it apart most.

| File suffix | Treatment |
|---|---|
| `keyline-horizontal` | Solid keyline, horizontal stripes inside the masses only |
| `keyline-diagonal` | Solid keyline, 31° stripes inside the masses only |
| `grooved-horizontal` | Thin horizontal grooves cut across an otherwise solid mark |
| `grooved-diagonal` | Thin grooves at -31°, cutting across the diagonals |
| `horizontal-fine` | Horizontal at a fine line-screen pitch, evenly weighted |
| `horizontal` | Bold 50/50 horizontal scanlines |
| `vertical` | Bold 50/50 vertical stripes |
| `diagonal-parallel` | Bold stripes parallel to the mark's own diagonals |
| `diagonal-counter` | Bold stripes across the diagonals at -31° |

**Duty cycle decides whether the mark survives, not angle.** At duty 0.5 a
46px stroke lands on a 32px gap often enough to break into dashes — that is
what happens to the vertical bars in `horizontal`, and to the diagonals in
`diagonal-parallel`, where the stripes run along the strokes and erase them
wholesale. The `grooved-*` variants run duty 0.72 for exactly this reason: the
mark stays continuous and the stripes read as cuts in the fill rather than as
gaps between fragments. Angle only decides *which* strokes take the damage.

The keyline variants sidestep the problem instead of tuning around it. A 26px
solid rim is held around every edge, and since no point inside a 46px stroke is
more than ~23px from an edge, the strokes are never deep enough to reach the
striped core — they stay solid, and only the large masses get striped. Raise
`KEYLINE_RIM` past ~26 and more of the mark goes solid; drop it below ~23 and
the thin strokes break into dashes, which is the failure these variants exist
to avoid.

## Tuning

```bash
# One variant, at a coarser pitch and with more paper showing.
python3 packaging/icon-variants/make_striped_icons.py \
    --only grooved-diagonal --pitch 96 --duty 0.6
```

`--pitch` is centre-to-centre at 1024 and scales with the source; `--duty` is
the ink fraction of a stripe and overrides each variant's own. Both are the
levers worth turning first.

## Adopting one

The variants are byte-for-byte the same kind of file as the master — 1024x1024,
8-bit, non-interlaced, opaque black on white — so adopting one is a copy:

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
