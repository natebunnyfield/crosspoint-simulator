#!/usr/bin/env python3
"""Generate striped variants of the CrossPoint app icon.

WHAT THIS IS
------------
Design exploration, not a build step. The shipping icon is a plain filled mark;
these are candidates that replace that flat fill with a line screen. Nothing in
the build depends on this script -- adopting a variant means copying its PNG
over ios/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png, after which the
macOS .icns follows automatically (packaging/macos/make_icns.py derives it).

WHY DERIVE FROM THE ARTWORK INSTEAD OF REDRAWING
------------------------------------------------
There is no vector source for the mark in this repo -- the 1024 PNG *is* the
master. Redrawing the outline by hand to fill it with stripes would produce a
second, slightly-wrong copy of the shape, and every variant would inherit that
error. So the mark's ink coverage is read straight out of the master PNG and
used as a mask: the silhouette of every variant is the current icon's, exactly,
including its antialiased edges. Only the fill changes.

HOW THE STRIPES ARE DRAWN
-------------------------
Analytically, not by drawing rectangles and hoping. Each pixel projects onto the
stripe axis as an interval, and the exact fraction of that interval falling
inside an "on" band is computed by integrating the square wave (`_band_average`).
That yields correct antialiasing at any angle and any pitch, including pitches
finer than a pixel once the icon is scaled down -- where drawn rectangles would
alias into moire. Coverage is then multiplied by the mask's coverage, so stripe
edges and shape edges antialias against each other rather than fighting.

Two facts about the mark drove the defaults:

  * Its diagonals run at atan(3/5) = 30.96 degrees. DIAGONAL_ANGLE matches that,
    so the "parallel" variants run with the artwork instead of cutting a second,
    unrelated angle across it.
  * Its strokes are ~46px wide at 1024, so a stroke's deepest interior point is
    ~23px from an edge. The keyline variants use a 26px solid rim, which is what
    keeps those strokes SOLID (they are never deep enough to reach the striped
    core) while the large masses -- which are much deeper -- do get striped.
    Raise KEYLINE_RIM past ~26 and more of the mark goes solid; drop it below
    ~23 and the thin strokes break into dashes, which is the whole failure mode
    the keyline variants exist to avoid.

Usage:
    python3 packaging/icon-variants/make_striped_icons.py
    python3 packaging/icon-variants/make_striped_icons.py --only keyline-diagonal
    python3 packaging/icon-variants/make_striped_icons.py --pitch 48 --duty 0.4
"""

import argparse
import math
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "packaging", "macos"))

# The PNG codec lives with the .icns builder. Importing it keeps one decoder in
# the repo rather than a second copy that drifts.
from make_icns import IconError, read_png, write_png  # noqa: E402

DEFAULT_SOURCE = os.path.join(
    REPO_ROOT, "ios", "Assets.xcassets", "AppIcon.appiconset", "AppIcon-1024.png"
)
DEFAULT_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# The mark's own diagonal, measured off the master: the edges advance 5px
# horizontally per 3px vertically.
DIAGONAL_ANGLE = math.degrees(math.atan2(3.0, 5.0))

# Solid border, in master pixels, held around every edge of the mark in the
# keyline variants. See the module docstring for why 26 and not less.
KEYLINE_RIM = 26.0

# Stripe geometry at 1024. Pitch is centre-to-centre; duty is the ink fraction.
PITCH = 64.0
DUTY = 0.5

# name -> (angle in degrees, pitch scale, duty, keyline rim or None, blurb)
#
# Angles are measured so that the stripes run perpendicular to the axis being
# swept: 0 gives vertical stripes swept along x, 90 gives horizontal stripes.
#
# Ordered from the treatment that protects the mark most to the one that takes
# it apart most, because that is the axis the choice actually turns on. Duty is
# the lever: at 0.5 a 46px stroke lands on a 32px gap often enough to break into
# dashes, which is why the mid-set "grooved" variants run duty 0.72 -- the mark
# stays continuous and the stripes read as cuts in the fill rather than as gaps
# between fragments.
VARIANTS = [
    (
        "keyline-horizontal",
        90.0, 72.0 / 64.0, 0.45, KEYLINE_RIM,
        "Solid keyline, horizontal stripes inside the masses only.",
    ),
    (
        "keyline-diagonal",
        DIAGONAL_ANGLE, 72.0 / 64.0, 0.45, KEYLINE_RIM,
        "Solid keyline, 31 degree stripes inside the masses only.",
    ),
    (
        "grooved-horizontal",
        90.0, 48.0 / 64.0, 0.72, None,
        "Thin horizontal grooves cut across an otherwise solid mark.",
    ),
    (
        "grooved-diagonal",
        -DIAGONAL_ANGLE, 48.0 / 64.0, 0.72, None,
        "Thin grooves at -31 degrees, cutting across the diagonals.",
    ),
    (
        "horizontal-fine",
        90.0, 28.0 / 64.0, DUTY, None,
        "Horizontal at a fine line-screen pitch, evenly weighted.",
    ),
    (
        "horizontal",
        90.0, 1.0, DUTY, None,
        "Bold 50/50 horizontal scanlines, the e-ink raster reading.",
    ),
    (
        "vertical",
        0.0, 1.0, DUTY, None,
        "Bold 50/50 vertical stripes.",
    ),
    (
        "diagonal-parallel",
        DIAGONAL_ANGLE, 1.0, DUTY, None,
        "Bold stripes parallel to the mark's own 31 degree diagonals.",
    ),
    (
        "diagonal-counter",
        -DIAGONAL_ANGLE, 1.0, DUTY, None,
        "Bold stripes across the diagonals at -31 degrees.",
    ),
]


# --------------------------------------------------------------------------
# Mask
# --------------------------------------------------------------------------

def ink_mask(rgba, size):
    """Ink coverage 0..255 per pixel, from a black-on-white opaque master.

    The master has no alpha channel worth the name (every pixel is opaque), so
    coverage is carried by luminance: white is paper, black is full ink, and the
    greys in between are the artwork's own antialiasing, which is preserved.
    """
    mask = bytearray(size * size)
    for i in range(size * size):
        o = i * 4
        lum = (rgba[o] * 299 + rgba[o + 1] * 587 + rgba[o + 2] * 114) // 1000
        mask[i] = (255 - lum) * rgba[o + 3] // 255
    return mask


def mask_bounds(mask, size, threshold=128):
    """Bounding box of the ink, as (x0, y0, x1, y1) inclusive."""
    x0, y0, x1, y1 = size, size, -1, -1
    for y in range(size):
        row = y * size
        for x in range(size):
            if mask[row + x] >= threshold:
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
    if x1 < 0:
        raise IconError("source artwork has no ink")
    return x0, y0, x1, y1


def edge_distance(mask, size, threshold=128):
    """Distance from each ink pixel to the nearest paper pixel, in pixels.

    A 3-4 chamfer transform: two passes, no dependencies, and within a few
    percent of Euclidean -- accurate enough to decide "is this point deeper than
    the 26px rim", which is all it is used for. Paper pixels are 0.

    Deliberately not an erosion loop: eroding by 26 would be 26 passes over a
    megapixel, and this is two.
    """
    INF = 1 << 28
    dist = [0 if mask[i] < threshold else INF for i in range(size * size)]

    for y in range(size):
        row = y * size
        up = row - size
        for x in range(size):
            i = row + x
            d = dist[i]
            if d == 0:
                continue
            if x > 0:
                d = min(d, dist[i - 1] + 3)
            if y > 0:
                d = min(d, dist[up + x] + 3)
                if x > 0:
                    d = min(d, dist[up + x - 1] + 4)
                if x + 1 < size:
                    d = min(d, dist[up + x + 1] + 4)
            dist[i] = d

    for y in range(size - 1, -1, -1):
        row = y * size
        down = row + size
        for x in range(size - 1, -1, -1):
            i = row + x
            d = dist[i]
            if d == 0:
                continue
            if x + 1 < size:
                d = min(d, dist[i + 1] + 3)
            if y + 1 < size:
                d = min(d, dist[down + x] + 3)
                if x > 0:
                    d = min(d, dist[down + x - 1] + 4)
                if x + 1 < size:
                    d = min(d, dist[down + x + 1] + 4)
            dist[i] = d

    return [d / 3.0 for d in dist]


# --------------------------------------------------------------------------
# Stripes
# --------------------------------------------------------------------------

def _band_average(t0, t1, period, on):
    """Mean of the square wave over [t0, t1]: 1 inside an 'on' band, else 0.

    Exact rather than sampled. `F` is the wave's antiderivative -- how much 'on'
    length lies in [0, t) -- so the mean over any interval is one subtraction,
    and a pixel narrower than the stripe, wider than the stripe, or straddling
    several stripes all come out right with no special cases.
    """
    def F(t):
        whole, rest = divmod(t, period)
        return whole * on + (rest if rest < on else on)

    span = t1 - t0
    if span <= 0.0:
        return 1.0 if (t0 % period) < on else 0.0
    return (F(t1) - F(t0)) / span


def stripe_field(size, angle_deg, period, duty, centre):
    """Stripe coverage 0..255 per pixel for the whole canvas.

    Phase is anchored so an ink stripe is centred on `centre`. The mark is not
    symmetric (its two counters are different shapes -- a parallelogram and a
    triangle), so there is no symmetry to preserve here; centring simply keeps
    the pattern registered to the artwork rather than to the canvas corner, so
    changing the pitch grows the stripes outward from the middle instead of
    sliding them all sideways.
    """
    theta = math.radians(angle_deg)
    ct, st = math.cos(theta), math.sin(theta)
    on = period * duty

    # A one-pixel box projects onto the stripe axis as an interval this wide;
    # integrating over it is what antialiases the stripe edges.
    half = (abs(ct) + abs(st)) / 2.0
    cx, cy = centre

    field = bytearray(size * size)
    for y in range(size):
        # Hoisted: within a row only the x term changes, by ct each step.
        t = (0.5 - cx) * ct + (y + 0.5 - cy) * st + on / 2.0
        row = y * size
        for x in range(size):
            field[row + x] = int(
                _band_average(t - half, t + half, period, on) * 255.0 + 0.5
            )
            t += ct
    return field


def render(mask, size, angle_deg, period, duty, centre, rim, distance):
    """Composite: ink = mask coverage * fill coverage, painted black on white."""
    stripes = stripe_field(size, angle_deg, period, duty, centre)
    out = bytearray(size * size * 4)
    for i in range(size * size):
        coverage = mask[i]
        if coverage:
            fill = stripes[i]
            if rim is not None and fill < 255:
                # Inside the rim the fill is solid; the two blend over one pixel
                # so the keyline does not show a hard step against the stripes.
                depth = distance[i]
                if depth <= rim:
                    fill = 255
                elif depth < rim + 1.0:
                    edge = rim + 1.0 - depth
                    fill = int(fill + (255 - fill) * edge + 0.5)
            coverage = coverage * fill // 255
        value = 255 - coverage
        o = i * 4
        out[o] = out[o + 1] = out[o + 2] = value
        out[o + 3] = 255
    return out


# --------------------------------------------------------------------------

def build(source, output_dir, pitch, duty_override, only):
    size, height, rgba = read_png(source)
    if size != height:
        raise IconError("icon source must be square (got %dx%d)" % (size, height))

    mask = ink_mask(rgba, size)
    x0, y0, x1, y1 = mask_bounds(mask, size)
    centre = ((x0 + x1 + 1) / 2.0, (y0 + y1 + 1) / 2.0)

    scale = size / 1024.0
    distance = None
    written = []

    for name, angle, pitch_scale, duty, rim, blurb in VARIANTS:
        if only and name not in only:
            continue
        if rim is not None and distance is None:
            distance = edge_distance(mask, size)

        rgba_out = render(
            mask,
            size,
            angle,
            pitch * pitch_scale * scale,
            duty if duty_override is None else duty_override,
            centre,
            None if rim is None else rim * scale,
            distance,
        )

        path = os.path.join(output_dir, "AppIcon-1024-striped-%s.png" % name)
        with open(path, "wb") as handle:
            handle.write(write_png(size, size, rgba_out))
        written.append((name, path, blurb))
        print("wrote %s -- %s" % (os.path.relpath(path, REPO_ROOT), blurb))

    if not written:
        raise IconError(
            "no variant matched; known names: %s" % ", ".join(v[0] for v in VARIANTS)
        )
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="master 1024 PNG")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--pitch", type=float, default=PITCH,
        help="stripe pitch at 1024, centre to centre (default %d)" % PITCH,
    )
    parser.add_argument(
        "--duty", type=float, default=None,
        help="ink fraction of a stripe, overriding each variant's own",
    )
    parser.add_argument(
        "--only", action="append",
        help="build just this variant (repeatable)",
    )
    args = parser.parse_args()

    try:
        os.makedirs(args.output_dir, exist_ok=True)
        build(args.source, args.output_dir, args.pitch, args.duty, args.only)
    except IconError as error:
        print("error: %s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
