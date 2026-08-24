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

# 6. THE CHIPS MATCH THE PAD. Owner instruction 2026-08-17, "match show/hide
#    keyboard button outline with rest of app", reversing the light-gray rule
#    they carried before. The failure mode is silent -- a chip with its own
#    tone still LOOKS deliberate -- so it is pinned in three places.
prefs = PREFS.read_text()
check(
    "padPaletteForPrefs" in prefs,
    "ios/PanelPrefs.h has no padPaletteForPrefs; the chips cannot be following "
    "the pad",
)
chip_def = prefs[prefs.index("chipPaletteForPrefs(bool dark)"):]
chip_def = chip_def[: chip_def.index("}")]
check(
    "padPaletteForPrefs" in chip_def,
    "chipPaletteForPrefs no longer delegates to padPaletteForPrefs -- the chips "
    "have become a special case again, against the 2026-08-17 instruction",
)
check(
    "makePaletteOn" not in chip_def,
    "chipPaletteForPrefs builds its own palette instead of taking the pad's",
)

# 7. The SDL chip must paint with the palette it is HANDED, not one it resolves
#    for itself -- that is how it acquired a separate tone the first time.
paint = shim[shim.index("void paintKeyboardChip("):]
paint = paint[: paint.index("\n}\n")]
check(
    "chipPaletteForPrefs" not in paint,
    "paintKeyboardChip resolves its own chip palette again instead of using the "
    "pad palette passed to it",
)

# 8. THE KEYBOARD CHIP STILL EXISTS -- draws, hit-tests, and toggles.
#
#    Widening, 2026-08-24. This file was about the two chips' TONES; it gains
#    one about the keyboard chip's EXISTENCE, because that day the OTHER chip
#    was removed from the pad (owner: "remove the color button from single
#    finger (not zen) mode ui") and the two sat forty lines apart in the same
#    three functions -- the layout, the paint and the finger-up branch. Taking
#    the wrong one is a small edit that compiles, links and passes everything
#    here, and its cost is a reader stuck in a text field with 40% of the
#    screen gone: an off-pad tap does nothing by deliberate ruling, and the
#    iPhone keyboard carries no dismiss key of its own, so this chip is the
#    only way back. A comment saying "do not confuse these" is what stood in
#    the way before, and a comment is not a control.
for needle, what in (
    ("g_kbChip", "the chip's own rect"),
    ("void paintKeyboardChip(", "its paint"),
    ("bool hitKeyboardChip(", "its hit test"),
    ("paintKeyboardChip(r, p, radius, hairline);", "the paint being CALLED"),
    ("hitKeyboardChip(candX, candY)", "the hit test being CALLED on finger-up"),
    ("const bool want = !gpio.isHostKeyboardVisible();", "the TOGGLE's flip"),
    ("gpio.setHostKeyboardVisible(want);", "the TOGGLE's push"),
):
    check(
        needle in shim,
        f"{SHIM.name} has lost {what} ({needle!r}). The keyboard chip is the "
        "only way to dismiss the iPhone software keyboard -- an off-pad tap "
        "does nothing by ruling, and iPhone's keyboard has no dismiss key -- "
        "so removing it traps a reader in a text field.",
    )
check(
    "if (!gpio.isTextEntryActive()) return;" in shim,
    f"{SHIM.name}'s paintKeyboardChip no longer gates on an open field. That "
    "gate is what distinguishes it from the removed page-color button, which "
    "drew unconditionally (owner ruling 2026-08-10: the chip appears only "
    "while the feature is in play).",
)

# 9. ...and the PAGE-COLOR button does not. Removed 2026-08-24; the drawers it
#    opened are deliberately intact and unreachable, so a chip that comes back
#    must be a conscious act rather than a merge. Same shape as
#    panel_palette_test.py asserting `presentFlash` absent from Root.plist.
#    Checked on the shim with its COMMENTS STRIPPED, because the prose that
#    records why the button went -- and that it must not be confused with the
#    chip beside it -- names it several times, and a guard satisfied by deleting
#    that explanation is worse than no guard.
shim_code = "\n".join(
    line for line in shim.splitlines() if not line.lstrip().startswith("//")
)
check(
    "g_paletteChip" not in shim_code and "PaletteChip" not in shim_code,
    f"{SHIM.name} declares or uses g_paletteChip in CODE. The page-color "
    "button was removed by owner ruling 2026-08-24 ('remove the color button "
    "from single finger (not zen) mode ui'); bringing it back is a ruling, not "
    "a cleanup. The drawers it opened are still whole -- unfreeze "
    "src/FrozenPage.h and re-add the entry point together, or the button opens "
    "editors whose sliders move nothing.",
)

if failures:
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    sys.exit(1)
print("chip tint source: one definition, and only the keyboard chip is left")
