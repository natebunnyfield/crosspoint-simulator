#!/usr/bin/env python3
"""Derive the macOS .icns from the iOS app icon artwork.

WHY THIS EXISTS
---------------
`package_macos_app.py --icon` has always accepted an .icns, and nothing has ever
passed one: there is no .icns in this repo, so every packaged Mac app has
shipped with the generic blank-document icon. App Store review rejects a
submission without an app icon, so this was a latent blocker in the same class
as the ITMS-90683 purpose strings that file already guards.

WHY GENERATE RATHER THAN CHECK ONE IN
-------------------------------------
There is exactly one piece of icon artwork in this repo --
ios/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png -- and two platforms
that need it. Checking in a second, hand-made .icns would create a copy that
silently drifts from the iOS icon the first time either is updated. Generating
keeps one source of truth.

WHY IT IS NOT A STRAIGHT COPY
-----------------------------
iOS and macOS disagree about who owns the icon's shape. iOS artwork is a full
square and the OS masks it to the superellipse at display time. macOS does NOT
mask: an app ships its own rounded rectangle with transparent corners, inset
inside the canvas so the Dock's drop shadow has room. Handing the iOS square
straight to macOS produces a hard-edged full-bleed square that reads as broken
next to every other app in the Dock.

So this rounds and insets to Apple's macOS icon grid: on a 1024 canvas the icon
body is 824x824 centred, with a corner radius of 185. Those proportions come
from Apple's macOS app icon template.

WHY PURE PYTHON
---------------
The obvious implementation is `sips` + `iconutil`, which is what a Mac would
use. Both are macOS-only, and this repo's CI and much of its development happen
on Linux, where an icon that cannot be built is an icon that silently is not
there -- exactly the failure being fixed. zlib is in the standard library and
PNG is a simple format, so this has no dependencies and runs anywhere.

Usage:
    python3 packaging/macos/make_icns.py --output dist/CrossPointX3.icns
    python3 packaging/macos/make_icns.py --source path/to/1024.png --output out.icns
"""

import argparse
import os
import struct
import sys
import zlib

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SOURCE = os.path.join(
    REPO_ROOT, "ios", "Assets.xcassets", "AppIcon.appiconset", "AppIcon-1024.png"
)

# Apple's macOS icon grid, expressed against a 1024 canvas. The body is inset so
# the Dock shadow has somewhere to fall; the radius is what makes it read as a
# macOS icon rather than a sticker.
CANVAS = 1024
BODY = 824
RADIUS = 185

# icns chunk type -> pixel size. These are the PNG-carrying types iconutil emits
# for a full .iconset, which is what gives a crisp icon at every place macOS
# draws one (Dock, Finder list, Get Info, App Store).
ICNS_TYPES = [
    (b"icp4", 16),
    (b"ic11", 32),   # 16x16@2x
    (b"icp5", 32),
    (b"ic12", 64),   # 32x32@2x
    (b"ic07", 128),
    (b"ic13", 256),  # 128x128@2x
    (b"ic08", 256),
    (b"ic14", 512),  # 256x256@2x
    (b"ic09", 512),
    (b"ic10", 1024), # 512x512@2x
]


class IconError(Exception):
    pass


# --------------------------------------------------------------------------
# PNG decode. Only what the source artwork actually is: 8-bit, non-interlaced,
# RGB or RGBA. Anything else is rejected loudly rather than guessed at, because
# a silently mis-decoded icon still produces a plausible-looking file.
# --------------------------------------------------------------------------

def read_png(path):
    """Return (width, height, RGBA bytearray)."""
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError as error:
        raise IconError("cannot read %s: %s" % (path, error))

    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise IconError("%s is not a PNG" % path)

    width = height = None
    depth = colortype = interlace = None
    idat = bytearray()

    offset = 8
    while offset < len(data):
        (length,) = struct.unpack(">I", data[offset : offset + 4])
        ctype = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if ctype == b"IHDR":
            width, height, depth, colortype, _comp, _filt, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
        elif ctype == b"IDAT":
            idat += payload
        elif ctype == b"IEND":
            break
        offset += 12 + length

    if width is None:
        raise IconError("%s has no IHDR" % path)
    if depth != 8 or interlace != 0 or colortype not in (2, 6):
        raise IconError(
            "%s must be an 8-bit non-interlaced RGB or RGBA PNG "
            "(got depth=%s colortype=%s interlace=%s)" % (path, depth, colortype, interlace)
        )

    channels = 3 if colortype == 2 else 4
    raw = zlib.decompress(bytes(idat))
    return width, height, _unfilter(raw, width, height, channels)


def _unfilter(raw, width, height, channels):
    """Reverse the per-scanline PNG filters, returning RGBA."""
    stride = width * channels
    expected = (stride + 1) * height
    if len(raw) != expected:
        raise IconError("PNG data is %d bytes, expected %d" % (len(raw), expected))

    out = bytearray(width * height * 4)
    prev = bytearray(stride)
    pos = 0
    for y in range(height):
        filter_type = raw[pos]
        pos += 1
        line = bytearray(raw[pos : pos + stride])
        pos += stride

        if filter_type == 1:  # Sub
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up = prev[i]
                upleft = prev[i - channels] if i >= channels else 0
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                if pa <= pb and pa <= pc:
                    pred = left
                elif pb <= pc:
                    pred = up
                else:
                    pred = upleft
                line[i] = (line[i] + pred) & 0xFF
        elif filter_type != 0:
            raise IconError("unknown PNG filter type %d" % filter_type)

        base = y * width * 4
        if channels == 4:
            out[base : base + stride] = line
        else:
            for x in range(width):
                o, s = base + x * 4, x * 3
                out[o] = line[s]
                out[o + 1] = line[s + 1]
                out[o + 2] = line[s + 2]
                out[o + 3] = 255
        prev = line

    return out


def write_png(width, height, rgba):
    """Encode RGBA bytes as a PNG. Filter 0 throughout: icons are small and the
    extra compression from adaptive filtering is not worth the code."""
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw += rgba[y * stride : (y + 1) * stride]

    def chunk(ctype, payload):
        return (
            struct.pack(">I", len(payload))
            + ctype
            + payload
            + struct.pack(">I", zlib.crc32(ctype + payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------

def resize(src, src_w, src_h, dst_w, dst_h):
    """Box-average downscale, alpha-weighted.

    Averaging must be weighted by alpha or transparent pixels drag their colour
    into the visible edge, which shows up as a dark halo around the rounded
    corners at small sizes -- the exact place icons are judged.
    """
    dst = bytearray(dst_w * dst_h * 4)
    for y in range(dst_h):
        y0, y1 = y * src_h // dst_h, max(y * src_h // dst_h + 1, (y + 1) * src_h // dst_h)
        for x in range(dst_w):
            x0, x1 = x * src_w // dst_w, max(x * src_w // dst_w + 1, (x + 1) * src_w // dst_w)
            r = g = b = a = 0
            n = 0
            for sy in range(y0, y1):
                row = sy * src_w * 4
                for sx in range(x0, x1):
                    o = row + sx * 4
                    alpha = src[o + 3]
                    r += src[o] * alpha
                    g += src[o + 1] * alpha
                    b += src[o + 2] * alpha
                    a += alpha
                    n += 1
            o = (y * dst_w + x) * 4
            if a:
                dst[o] = min(255, r // a)
                dst[o + 1] = min(255, g // a)
                dst[o + 2] = min(255, b // a)
            dst[o + 3] = a // n if n else 0
    return dst


def rounded_mask(size, body, radius, samples=4):
    """Coverage 0..255 for a centred rounded rectangle, supersampled for AA.

    Without antialiasing the corners stair-step, which is glaring at 512 and
    above where the curve is long enough to see.
    """
    inset = (size - body) / 2.0
    left, top = inset, inset
    right, bottom = inset + body, inset + body
    mask = bytearray(size * size)
    step = 1.0 / samples
    offset = step / 2.0

    for y in range(size):
        for x in range(size):
            hits = 0
            for sy in range(samples):
                py = y + offset + sy * step
                for sx in range(samples):
                    px = x + offset + sx * step
                    if px < left or px > right or py < top or py > bottom:
                        continue
                    # Only the four corner boxes need a distance test.
                    cx = left + radius if px < left + radius else (
                        right - radius if px > right - radius else px
                    )
                    cy = top + radius if py < top + radius else (
                        bottom - radius if py > bottom - radius else py
                    )
                    if cx == px and cy == py:
                        hits += 1
                    else:
                        dx, dy = px - cx, py - cy
                        if dx * dx + dy * dy <= radius * radius:
                            hits += 1
            mask[y * size + x] = (hits * 255) // (samples * samples)
    return mask


def compose(source_rgba, src_size):
    """Scale the artwork to the icon body and mask it onto a transparent canvas."""
    body = resize(source_rgba, src_size, src_size, BODY, BODY)
    mask = rounded_mask(BODY, BODY, RADIUS)

    canvas = bytearray(CANVAS * CANVAS * 4)
    inset = (CANVAS - BODY) // 2
    for y in range(BODY):
        for x in range(BODY):
            s = (y * BODY + x) * 4
            coverage = mask[y * BODY + x]
            if not coverage:
                continue
            d = ((y + inset) * CANVAS + (x + inset)) * 4
            canvas[d] = body[s]
            canvas[d + 1] = body[s + 1]
            canvas[d + 2] = body[s + 2]
            canvas[d + 3] = body[s + 3] * coverage // 255
    return canvas


def build_icns(source_path):
    width, height, rgba = read_png(source_path)
    if width != height:
        raise IconError("icon source must be square (got %dx%d)" % (width, height))

    canvas = compose(rgba, width)

    entries = []
    cache = {}
    for ctype, size in ICNS_TYPES:
        if size not in cache:
            scaled = canvas if size == CANVAS else resize(canvas, CANVAS, CANVAS, size, size)
            cache[size] = write_png(size, size, scaled)
        entries.append((ctype, cache[size]))

    body = b"".join(
        ctype + struct.pack(">I", len(png) + 8) + png for ctype, png in entries
    )
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--source",
        default=DEFAULT_SOURCE,
        help="1024x1024 PNG to derive from (default: the iOS app icon)",
    )
    parser.add_argument("--output", required=True, help="path of the .icns to write")
    args = parser.parse_args()

    try:
        data = build_icns(args.source)
    except IconError as error:
        print("error: %s" % error, file=sys.stderr)
        return 1

    directory = os.path.dirname(os.path.abspath(args.output))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(args.output, "wb") as handle:
        handle.write(data)

    print(
        "wrote %s (%d bytes, %d sizes, from %s)"
        % (args.output, len(data), len({s for _, s in ICNS_TYPES}), args.source)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
