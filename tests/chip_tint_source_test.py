#!/usr/bin/env python3
"""The two keyboard chips must take their colors from ONE source.

The SHOW chip is painted by SDL every frame from the pad palette, which is built
on the owner's chosen paper (`makePaletteOn(..., panel.paper)` in
CrossPointIOSShim.cpp). The HIDE chip is a UIKit button in the keyboard's
accessory bar (CrossPointKeyboardBar.mm) and is painted once, by hand.

For a long time the hide chip carried the shipped tones written out as hex
literals. That was invisible while the palette was fixed, and became a visible
bug the moment it became settable: choose Green CRT and the show chip went
phosphor while the hide chip stayed gray -- two halves of the same gesture in
two different colors (owner, 2026-08-15: "match hide keyboard color to show
keyboard color").

The fix routed both through `crosspoint::panelForPrefs` in ios/PanelPrefs.h.
This test is what stops the literals coming back, because nothing else can see
them: a hardcoded color compiles, links, passes every other test here, and is
only wrong on screen -- and only under a non-default palette.

Deliberately source-level. The real check would render the chip, but that needs
UIKit and a booted simulator, and a test that cannot run in this suite is a test
nobody runs.
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
BAR = REPO / "ios" / "CrossPointKeyboardBar.mm"
SHIM = REPO / "ios" / "CrossPointIOSShim.cpp"
PREFS = REPO / "ios" / "PanelPrefs.h"

failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


bar = BAR.read_text()
shim = SHIM.read_text()

# 1. The hide chip must not carry color literals of its own. Matches the shape
#    the old code used -- a UIColor built from hex components -- rather than any
#    stray 0x, so the glyph rasterizer's own constants do not trip it.
literal = re.compile(r"colorWithRed:\s*0x[0-9A-Fa-f]{2}")
hits = literal.findall(bar)
check(
    not hits,
    f"{BAR.name} builds {len(hits)} UIColor(s) from hex literals; the chip must "
    "read the live palette through crosspoint::panelForPrefs instead",
)

# 2. ...and it must actually reach the shared resolver.
check(
    "panelForPrefs" in bar,
    f"{BAR.name} never calls crosspoint::panelForPrefs -- its colors cannot be "
    "following the owner's palette",
)
check(
    'PanelPrefs.h"' in bar,
    f"{BAR.name} does not include PanelPrefs.h",
)

# 3. The SDL side must resolve through the same function, or the two can still
#    disagree while both look correct in isolation.
check(
    "panelForPrefs" in shim,
    f"{SHIM.name} does not resolve through crosspoint::panelForPrefs; the show "
    "and hide chips would have separate definitions again",
)

# 4. A palette change raises no trait change and a CGColor never re-resolves, so
#    an already-built bar has to be pushed the new tones explicitly.
check(
    "CrossPointKeyboardBar_refreshTint" in shim,
    f"{SHIM.name} never refreshes the keyboard bar's tint, so the hide chip "
    "would keep the palette it was built with until the keyboard is rebuilt",
)

# 5. One definition, not two copies that drift.
check(PREFS.exists(), "ios/PanelPrefs.h is missing")

if failures:
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    sys.exit(1)
print("chip tint source: one definition, both chips")
