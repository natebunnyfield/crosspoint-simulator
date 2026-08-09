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

THE THREE MEASUREMENTS THAT DRIVE EVERYTHING
--------------------------------------------
  * The mark's page edges run at atan(3/5) = 30.96 degrees. Mind the
    convention: an angle here names the stripe's NORMAL, not the stripe, so a
    stripe parallel to an edge needs the edge's angle plus 90. For this mark
    the two are complementary -- edges at 30.96, PAGE_ANGLE at 59.04 -- which
    is a trap worth naming, because passing 30.96 gives stripes at 59.04 that
    look plausibly diagonal while being exactly PERPENDICULAR to the edge.
    Measured, not assumed: stripe slope is dx/dy = -tan(angle), and the page
    edge's is -5/3.
  * Its strokes are STROKE_WIDTH = 46px wide at 1024, so a stroke's deepest
    interior point is ~23px from an edge. Every rim decision below is really a
    decision about that number.
  * Its ink box is 626x696 at (198,164). Stripe phase anchors on that centre,
    so changing pitch grows the stripes outward from the middle of the mark
    rather than sliding them all sideways.

WHY THE RIM IS THE STROKE WIDTH
-------------------------------
A keyline variant holds a solid rim around every edge and stripes only what is
deeper than the rim. The rim is set to the mark's own stroke width, not to some
smaller value that merely "works", because the rim IS an outline and the mark
already contains outlines: the side bars and the strokes around the counters,
all 46px. A 26px rim -- the first thing tried -- reads as a thinner outline
around the top-right mass than around everything else, and the mark looks like
it was drawn with two pens. Matching 46px makes every outline in the icon one
weight.

That choice pays for itself twice, because the rim is also what separates the
mark's two solid masses. See `deep_components`.

Usage:
    python3 packaging/icon-variants/make_striped_icons.py
    python3 packaging/icon-variants/make_striped_icons.py --only matched-diagonal
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

# The mark's own diagonal: the page edges advance 5px horizontally per 3px
# vertically. Passing this as a stripe angle gives stripes PERPENDICULAR to
# those edges -- see the convention note in the module docstring.
DIAGONAL_ANGLE = math.degrees(math.atan2(3.0, 5.0))

# Stripes parallel to the right page's top edge: ruled lines lying on the page
# rather than cutting across it. The complement of DIAGONAL_ANGLE, because the
# angle names the normal.
PAGE_ANGLE = math.degrees(math.atan2(5.0, 3.0))

# Stroke width of the mark at 1024, measured off the master. Doubles as the rim
# that makes every outline read at one weight -- see the module docstring.
STROKE_WIDTH = 46.0

# The rim the first round used. Kept only so those variants still regenerate
# byte-identically; it is too thin to match the mark's own outlines, and too
# thin to separate the masses.
NARROW_RIM = 26.0

# Stripe geometry at 1024. Pitch is centre-to-centre; duty is the ink fraction.
PITCH = 64.0
DUTY = 0.5


def variant(name, angle, blurb, pitch=1.0, duty=DUTY, rim=None, solid_masses=0):
    """One entry in the variant table.

    `pitch` is a multiplier on the --pitch baseline; `rim` is in master pixels;
    `solid_masses` is how many of the mark's masses stay flat-filled, taken from
    the bottom-left end (see `deep_components`).
    """
    return dict(
        name=name, angle=angle, pitch=pitch, duty=duty, rim=rim,
        solid_masses=solid_masses, blurb=blurb,
    )


def page_variant(line, gap, blurb):
    """A ruled-page variant, named and specified in the terms being compared.

    Pitch and duty are the generator's parameters, but the thing actually being
    varied across this set is the width of an ink line and the width of the
    paper gap between lines -- so those are what the name carries. Both are in
    master pixels at 1024, and --pitch still scales the pair.
    """
    pitch = float(line + gap)
    return variant(
        "page-%d-%d" % (line, gap), PAGE_ANGLE, blurb,
        pitch=pitch / PITCH, duty=line / pitch,
        rim=STROKE_WIDTH, solid_masses=1,
    )


# Angles are measured so the stripes run perpendicular to the axis being swept:
# 0 gives vertical stripes, 90 gives horizontal, and anything between names the
# stripe's normal rather than the stripe.
#
# ROUND THREE is the current direction: round two's construction -- matched
# outlines, bottom-left mass flat -- with the stripes lying ALONG the page
# instead of cutting across it, and line/gap as the thing being varied. The
# earlier rounds are kept below as the record of what each correction was made
# against, and because the variants that break the mark break it informatively.
VARIANTS = [
    # -- Round three: ruled lines lying along the page ---------------------
    # Same construction as round two -- matched rim, bottom-left mass flat --
    # turned to PAGE_ANGLE so the stripes run parallel to the right page's top
    # edge and read as ruled lines of text on it. Nothing before this round was
    # actually parallel to a page; the earlier "diagonal" cuts all sat at the
    # complementary angle. Line and gap are what vary; the pair below runs from
    # even rules through thin-line/wide-gap ruling to a heavy stripe.
    page_variant(21, 21, "The round-two fine ruling, turned onto the page angle."),
    page_variant(12, 12, "Finer even ruling: more lines, each lighter."),
    page_variant(30, 30, "Wider even ruling: fewer, heavier lines."),
    page_variant(10, 26, "Thin lines, wide gaps -- closest to ruled text."),
    page_variant(26, 10, "Thick lines, thin gaps -- paper reads as the line."),
    page_variant(7, 21, "Hairline ruling at a 1:3 line-to-gap ratio."),

    # -- Round two: matched outlines, one mass striped ---------------------
    # Ordered as the review sheet numbers them, most even cut first. Only the
    # angle and pitch differ across the six; everything else is the correction.
    variant(
        "matched-counter", -DIAGONAL_ANGLE,
        "Top-right mass ruled at 59 degrees, square across the page's top edge.",
        pitch=72.0 / 64.0, duty=0.45, rim=STROKE_WIDTH, solid_masses=1,
    ),
    variant(
        "matched-vertical", 0.0,
        "Top-right mass in vertical stripes, running with the side bars.",
        pitch=72.0 / 64.0, duty=0.45, rim=STROKE_WIDTH, solid_masses=1,
    ),
    variant(
        "matched-horizontal", 90.0,
        "Top-right mass in horizontal stripes; bottom-left flat, outlines matched.",
        pitch=72.0 / 64.0, duty=0.45, rim=STROKE_WIDTH, solid_masses=1,
    ),
    variant(
        "matched-horizontal-fine", 90.0,
        "As matched-horizontal at a finer pitch: reads closer to a tint than to lines.",
        pitch=42.0 / 64.0, duty=0.5, rim=STROKE_WIDTH, solid_masses=1,
    ),
    variant(
        "matched-diagonal", DIAGONAL_ANGLE,
        "Top-right mass ruled at 59 degrees the other way, shallow to the page edge.",
        pitch=72.0 / 64.0, duty=0.45, rim=STROKE_WIDTH, solid_masses=1,
    ),
    variant(
        "matched-diagonal-fine", DIAGONAL_ANGLE,
        "As matched-diagonal at a finer pitch; the shallow incidence is unchanged.",
        pitch=42.0 / 64.0, duty=0.5, rim=STROKE_WIDTH, solid_masses=1,
    ),

    # -- Round one: both masses striped, thinner rim -----------------------
    # Ordered from the treatment that protects the mark most to the one that
    # takes it apart most. Duty is the lever: at 0.5 a 46px stroke lands on a
    # 32px gap often enough to break into dashes, which is why the "grooved"
    # pair runs 0.72 -- the mark stays continuous and the stripes read as cuts
    # in the fill rather than as gaps between fragments.
    variant(
        "keyline-horizontal", 90.0,
        "Solid 26px keyline, horizontal stripes inside both masses.",
        pitch=72.0 / 64.0, duty=0.45, rim=NARROW_RIM,
    ),
    variant(
        "keyline-diagonal", DIAGONAL_ANGLE,
        "Solid 26px keyline, 59 degree stripes inside both masses.",
        pitch=72.0 / 64.0, duty=0.45, rim=NARROW_RIM,
    ),
    variant(
        "grooved-horizontal", 90.0,
        "Thin horizontal grooves cut across an otherwise solid mark.",
        pitch=48.0 / 64.0, duty=0.72,
    ),
    variant(
        "grooved-diagonal", -DIAGONAL_ANGLE,
        "Thin grooves at 59 degrees, square across the right page's top edge.",
        pitch=48.0 / 64.0, duty=0.72,
    ),
    variant(
        "horizontal-fine", 90.0,
        "Horizontal at a fine line-screen pitch, evenly weighted.",
        pitch=28.0 / 64.0,
    ),
    variant(
        "horizontal", 90.0,
        "Bold 50/50 horizontal scanlines, the e-ink raster reading.",
    ),
    variant(
        "vertical", 0.0,
        "Bold 50/50 vertical stripes.",
    ),
    variant(
        "diagonal-steep", DIAGONAL_ANGLE,
        "Bold 50/50 at 59 degrees, square across the left page's top edge.",
    ),
    variant(
        "diagonal-counter", -DIAGONAL_ANGLE,
        "Bold 50/50 at 59 degrees the other way, square across the right page.",
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
    the rim", which is all it is used for. Paper pixels are 0.

    Deliberately not an erosion loop: eroding by 46 would be 46 passes over a
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


def deep_components(distance, size, rim, min_area):
    """Label the mark's masses: islands of interior deeper than the rim.

    WHY NOT JUST LABEL THE INK. The mark is one connected shape -- its two solid
    masses meet at the centre crossing -- so components of the ink cannot tell
    them apart. Components of the part deeper than the rim can, but only if the
    rim is wide enough to drown the crossing where they touch. Measured on the
    master:

        rim 26  ->  ONE island (the masses are still bridged at the crossing)
        rim 40  ->  two islands
        rim 46  ->  two islands, 70971px centred (655,425) and 28972px (318,685)

    So the rim that matches the mark's stroke weight is also the rim that first
    separates the masses cleanly. Below ~40 this returns one island, every mass
    is "the bottom-left mass", and a variant asking to keep one flat would
    silently come out as the unmodified icon -- which is why `build` refuses
    rather than emitting it.

    Returns (labels, infos) where labels is 0 for anything not deep, and infos
    is one (label, area, cx, cy) per island bigger than min_area, ordered from
    bottom-left to top-right by centroid.
    """
    labels = [0] * (size * size)
    infos = []
    label = 0

    for start in range(size * size):
        if labels[start] or distance[start] <= rim:
            continue
        label += 1
        labels[start] = label
        stack = [start]
        area = sum_x = sum_y = 0
        while stack:
            i = stack.pop()
            x = i % size
            area += 1
            sum_x += x
            sum_y += i // size
            for j, inside in (
                (i - 1, x > 0),
                (i + 1, x + 1 < size),
                (i - size, i >= size),
                (i + size, i + size < size * size),
            ):
                if inside and not labels[j] and distance[j] > rim:
                    labels[j] = label
                    stack.append(j)
        if area >= min_area:
            infos.append((label, area, sum_x / area, sum_y / area))

    # Bottom-left first. The mark's masses sit on opposite sides of the centre
    # crossing, so their centroids separate cleanly on x-y (-367 against +230 at
    # rim 46) -- far apart enough that the ordering is not a near-tie.
    infos.sort(key=lambda info: info[2] - info[3])
    return labels, infos


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


def render(mask, size, angle_deg, period, duty, centre, rim, distance, labels, solid):
    """Composite: ink = mask coverage * fill coverage, painted black on white."""
    stripes = stripe_field(size, angle_deg, period, duty, centre)
    out = bytearray(size * size * 4)
    for i in range(size * size):
        coverage = mask[i]
        if coverage:
            fill = stripes[i]
            if rim is not None and fill < 255:
                depth = distance[i]
                # `solid` is empty unless a variant holds a mass flat, and
                # `labels` is empty with it -- so it must be tested first.
                if depth <= rim or (solid and labels[i] in solid):
                    # The rim, and any mass held flat, are solid ink.
                    fill = 255
                elif depth < rim + 1.0:
                    # Blend over one pixel so the keyline does not show a hard
                    # step where it meets the stripes.
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
    min_area = size * size // 500
    distance = None
    components = {}
    written = []

    for spec in VARIANTS:
        name = spec["name"]
        if only and name not in only:
            continue

        rim = None if spec["rim"] is None else spec["rim"] * scale
        labels, solid = [], set()

        if rim is not None:
            if distance is None:
                distance = edge_distance(mask, size)
            if spec["solid_masses"]:
                if rim not in components:
                    components[rim] = deep_components(distance, size, rim, min_area)
                labels, infos = components[rim]
                if len(infos) <= spec["solid_masses"]:
                    raise IconError(
                        "%s wants %d of the mark's masses flat, but a %.0fpx rim "
                        "leaves only %d island(s) -- the masses are still bridged "
                        "at the centre crossing, so every mass would be filled and "
                        "the variant would come out as the unmodified icon. Widen "
                        "the rim past ~40px."
                        % (name, spec["solid_masses"], rim, len(infos))
                    )
                solid = {info[0] for info in infos[: spec["solid_masses"]]}

        rgba_out = render(
            mask, size, spec["angle"],
            pitch * spec["pitch"] * scale,
            spec["duty"] if duty_override is None else duty_override,
            centre, rim, distance, labels, solid,
        )

        path = os.path.join(output_dir, "AppIcon-1024-striped-%s.png" % name)
        with open(path, "wb") as handle:
            handle.write(write_png(size, size, rgba_out))
        written.append((name, path, spec["blurb"]))
        print("wrote %s -- %s" % (os.path.relpath(path, REPO_ROOT), spec["blurb"]))

    if not written:
        raise IconError(
            "no variant matched; known names: %s"
            % ", ".join(v["name"] for v in VARIANTS)
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
