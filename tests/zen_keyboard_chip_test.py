#!/usr/bin/env python3
"""THE KEYBOARD CHIP SURVIVES ZEN, while a field is open.

Audit finding 5 (docs/ux-navigation-audit-2026-09-02.md): zen hides the whole
pad, and the keyboard chip went with it. Every firmware text field opens with
the host keyboard SUPPRESSED (src/HostKeyboardState.h), and the chip is the
ONLY way to raise it on an iPhone -- so a Wi-Fi password or a rename opened in
zen could only be pecked out of the daisywheel, in the mode where Confirm is a
two-finger tap. Owner ruling 2026-09-02: paint and hit-test only the chip in
zen, gated on the field being open, and leave zen on.

Two lines of ios/CrossPointIOSShim.cpp carry the fix and neither can be host-
compiled (SDL, UIKit, a booted simulator): paintPad's zen branch must call
paintKeyboardChip before it returns, and padWatch's zen deliberate-tap
resolution must ask hitKeyboardChip BEFORE it resolves a gesture action --
after would be too late, since the gesture branch performs the action and the
chip tap would page the book. Both regress silently: the build compiles, zen
draws its black band, and the chip is simply not there again. So this pins
them at the source level, the same way panel_source_test.py pins the editors.

hostkbd::chipLive in src/HostKeyboardState.h is the decision the two sites
implement; tests/host_keyboard_test.cpp static_asserts it.
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SHIM = REPO / "ios" / "CrossPointIOSShim.cpp"

failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


src = strip_comments(SHIM.read_text())

# 1. The zen branch of paintPad paints the chip before returning. Locate the
#    branch by its black fill (`g_zen` guard immediately followed by the fillet
#    call that ends it) rather than by line number.
zen_paint = re.search(
    r"if \(g_zen\) \{(?P<body>.*?)paintBottomFillets\(r, outW, g_zenPaper,\s*true\);"
    r"(?P<tail>.*?)return;",
    src,
    flags=re.S,
)
check(zen_paint is not None, "paintPad's zen branch (black fill + bottom fillets + return) not found")
if zen_paint:
    check(
        "paintKeyboardChip(" in zen_paint.group("tail"),
        "paintPad's zen branch returns without painting the keyboard chip; a field "
        "opened in zen has no way to raise the keyboard (finding 5, ruled 2026-09-02)",
    )

# 2. The zen deliberate-tap path hit-tests the chip BEFORE resolving a gesture.
tap = src.find("zenBefore && verb == zenverbs::Verb::Down")
check(tap >= 0, "zen deliberate-tap branch not found in padWatch")
if tap >= 0:
    # The first Verb::Down branch must be the chip one, and it must toggle the
    # keyboard through the same call the non-zen chip uses.
    window = src[tap : tap + 900]
    check(
        "hitKeyboardChip(g_zenLastX, g_zenLastY)" in window.split("else if")[0],
        "the first zen Verb::Down branch is not the chip hit-test; a chip tap in "
        "zen would resolve as a page-turn gesture",
    )
    check(
        "setHostKeyboardVisible(" in window,
        "zen chip branch does not toggle the host keyboard",
    )
    check(
        'SDL_Log("[kbchip]' in window,
        "zen chip branch does not print the [kbchip] line the headless grep reads",
    )
    check(
        "SimulatorOverlay::requestPresent()" in window,
        "zen chip branch toggles without asking for a present -- the chip's "
        "state would not redraw until the next page render",
    )

# 3. hitKeyboardChip itself stays gated on the field, so the branch is dead
#    outside one and every other deliberate tap in zen still resolves a gesture.
hit = re.search(r"bool hitKeyboardChip\(float x, float y\) \{(.*?)\}", src, flags=re.S)
check(hit is not None, "hitKeyboardChip not found")
if hit:
    check(
        "isTextEntryActive()" in hit.group(1),
        "hitKeyboardChip is no longer gated on the field being open; in zen "
        "every tap on the bottom band would eat a gesture",
    )

if failures:
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    sys.exit(1)
print("zen keyboard chip: painted and hit-tested in zen while a field is open")
