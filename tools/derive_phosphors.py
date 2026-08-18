#!/usr/bin/env python3
"""Derive page palettes for JEDEC phosphors from their published emission.

WHY THIS IS A SCRIPT. The first twelve CRT rows were derived by hand, one at a
time, and that was fine at twelve. The owner then asked for "all possible
phosphors" (2026-08-17), which is the whole JEDEC P-number registry -- around
thirty more. Hand-deriving thirty rows guarantees they drift from each other:
one lifted a little further toward white, one rounded differently, one taking a
slightly different white point. This applies ONE method to every row, so the
family is internally consistent and the next phosphor is one table entry.

THE METHOD, unchanged from the hand-derived rows (docs/crt-phosphor-presets.md):

  1. published peak wavelength -> CIE 1931 xy on the spectral locus
  2. xy at Y=1 -> XYZ -> linear sRGB (sRGB primaries, D65)
  3. negative components clipped, then desaturated toward white only as far as
     the gamut requires
  4. scaled to the brightest in-gamut version of that chromaticity
  5. lifted toward the page's white until the pair clears the contrast floor

The CIE 1931 colour matching functions are the multi-lobe Gaussian fits from
Wyman, Sloan & Shirley, "Simple Analytic Approximations to the CIE XYZ Color
Matching Functions", JCGT 2013. Max error ~1% of peak, which is far inside the
uncertainty of "the published peak wavelength of a phosphor powder".

WHAT THIS CANNOT DO, and does not pretend to:

  * A phosphor is a BAND, not a spectral line. Rendering its peak as a
    monochromatic colour makes every row more saturated than the real tube.
    That is why step 5 exists at all, and why rows with a published CIE point
    (P1, P11, P22R, P31, P47, P22B, P56) use it INSTEAD of this derivation --
    a measured chromaticity always beats a reconstructed one.
  * Two-peak phosphors (whites, cascades) are mixed in linear light at the
    ratio given, which is a guess about relative intensity. Named as such.
  * P10 is a SCOTOPHOR: it does not emit, it darkens. It is derived by a
    different path and marked.
"""

import math

# --- CIE 1931 colour matching, Wyman/Sloan/Shirley single-lobe fits ---------


def _g(x, mu, s1, s2):
    s = s1 if x < mu else s2
    return math.exp(-0.5 * ((x - mu) / s) ** 2)


def cie_xyz(nm):
    x = (1.056 * _g(nm, 599.8, 37.9, 31.0) + 0.362 * _g(nm, 442.0, 16.0, 26.7)
         - 0.065 * _g(nm, 501.1, 20.4, 26.2))
    y = 0.821 * _g(nm, 568.8, 46.9, 40.5) + 0.286 * _g(nm, 530.9, 16.3, 31.1)
    z = 1.217 * _g(nm, 437.0, 11.8, 36.0) + 0.681 * _g(nm, 459.0, 26.0, 13.8)
    return x, y, z


# --- colour space ----------------------------------------------------------

_M = [[3.2406, -1.5372, -0.4986],
      [-0.9689, 1.8758, 0.0415],
      [0.0557, -0.2040, 1.0570]]


def xyz_to_linear(xyz):
    return [sum(m[i] * xyz[i] for i in range(3)) for m in _M]


def encode(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def decode(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (decode(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


def to_bytes(lin):
    return tuple(int(round(encode(c) * 255)) for c in lin)


D65 = (0.3127, 0.3290)

# HOW FAR A REAL PHOSPHOR SITS INSIDE THE SPECTRAL LOCUS.
#
# This is the correction that matters, and the first two attempts got it wrong
# in opposite directions. A phosphor does not emit a spectral LINE; it emits a
# band tens of nm wide, and a band's chromaticity lies well inside the locus,
# toward white. Treating the peak wavelength as the colour makes every row far
# more saturated than any real tube -- and then whatever fixes the gamut
# afterwards decides the hue:
#
#   * adding equal-energy white until in gamut made every green a pale mint
#     (P20 "Terminal Green" came out A5FF81, a washed lime -- reported by the
#     owner as a mismatch between the row's name and its page);
#   * clamping negatives to zero kept them vivid but COLLAPSED them -- 520, 525,
#     530, 543, 544 and 545 nm all landed on the same 59FF59.
#
# So the broadening happens FIRST, in chromaticity space, before any gamut
# mapping: move the locus point 18% toward D65. That is a model, and it is
# validated rather than asserted -- fitted against the four phosphors here that
# have BOTH a published peak and a measured CIE point (P1, P11, P22R, P47), mean
# error 0.042 in xy. P11, P22R and P47 land within ~0.03; P1 is the worst at
# 0.06 because willemite's band is unusually broad.
#
# A measured chromaticity still beats this every time, and the rows that have
# one use it.
BAND_TOWARD_WHITE = 0.18


def chroma_from_nm(nm):
    """Brightest in-gamut sRGB for a phosphor whose peak is `nm`, linear rgb."""
    X, Y, Z = cie_xyz(nm)
    s = X + Y + Z
    if s <= 0:
        return [0.0, 0.0, 0.0]
    x, y = X / s, Y / s
    x += BAND_TOWARD_WHITE * (D65[0] - x)
    y += BAND_TOWARD_WHITE * (D65[1] - y)
    return chroma_from_xy(x, y)


def mix(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(3)]


# --- page pairs ------------------------------------------------------------

FLOOR = 10.0  # what the shipped CRT rows sit at; the repo's hard floor is 7:1


def lift(ink_lin, paper_lin, floor=FLOOR):
    """Move the ink toward the paper until the pair clears `floor`.

    Reversed from what it sounds like: we START at full purity and walk toward
    the paper only if we are ABOVE the floor with room to spare, or toward the
    paper's opposite if we are below it. In practice the ink is the saturated
    phosphor and the paper is near-white or near-black, so the only move that
    ever helps is making the ink darker (light page) or lighter (dark page).
    """
    paper_is_dark = luminance(to_bytes(paper_lin)) < 0.2
    target = [1.0, 1.0, 1.0] if paper_is_dark else [0.0, 0.0, 0.0]
    lo, hi = 0.0, 1.0
    best = None
    for _ in range(40):
        t = (lo + hi) / 2
        cand = mix(ink_lin, target, t)
        if contrast(to_bytes(cand), to_bytes(paper_lin)) >= floor:
            best = cand
            hi = t
        else:
            lo = t
    return best if best is not None else mix(ink_lin, target, 1.0)


def pairs_for(chroma):
    """Light and dark page pairs for one phosphor chromaticity."""
    # Light page: a faintly tinted paper, ink is the phosphor darkened.
    paper_l = mix([1.0, 1.0, 1.0], chroma, 0.06)
    ink_l = lift(chroma, paper_l)
    # Dark page: a near-black ground carrying the same tint, ink is the
    # phosphor at (near) full emission -- which is what a tube actually is.
    paper_d = [c * 0.028 for c in chroma]
    ink_d = lift(chroma, paper_d)
    return (to_bytes(ink_l), to_bytes(paper_l),
            to_bytes(ink_d), to_bytes(paper_d))


def hexs(t):
    return "%02X%02X%02X" % t


def chroma_from_xy(x, y):
    """Brightest in-gamut sRGB for a MEASURED chromaticity. Always preferred
    over chroma_from_nm when the phosphor has a published CIE point."""
    if y <= 0:
        return [0.0, 0.0, 0.0]
    xyz = (x / y, 1.0, (1.0 - x - y) / y)
    lin = xyz_to_linear(xyz)
    lo = min(lin)
    if lo < 0:
        lin = [c - lo for c in lin]
    hi = max(lin)
    return [c / hi for c in lin] if hi > 0 else [0.0, 0.0, 0.0]
