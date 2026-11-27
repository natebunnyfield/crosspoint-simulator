#!/usr/bin/env python3
"""THE PICCO'S LIGHT GOES OFF ON THE WAY INTO SLEEP, and the iOS page must see it.

Review row R-15, 2026-11-27 (docs/frontlit-page-2026-11-27.md). The firmware
draws the sleep screen and then switches the light off, inside the loop() that
ends in the sleep loop. On iOS the page learns of a light change only from
three per-frame polls, and perFrame does not run while the firmware sleeps, so
the sleep screen sat on the lit paper for the whole sleep. The fix is that the
host's sleep tick runs the same three reads.

A SOURCE GATE, like font_resize_wiring: ios/CrossPointIOSShim.cpp compiles only
for iOS, so no host test can run the sleep tick. Delete the three calls and
every other test here still passes, and the page is wrong only on a Picco phone,
only asleep, only with the light away from 60/50. The behavior was measured on
the iOS Simulator (the doc's section for this row); this pins the wiring.
"""

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
# An argument names another copy of the shim, which is how this gate was shown
# to fail: against the file as it stood before the fix.
SHIM = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "ios" / "CrossPointIOSShim.cpp"

failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


def code_of(text):
    """`text` with its // comments removed: the checks are about code."""
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines()) + "\n"


def body_of(text, signature, where):
    """The source between `signature` and the first line-start `}`.

    A missing signature is a FAILURE, not a traceback: it means the function
    this test is about was renamed or deleted, which is when the gate must
    speak up.
    """
    start = text.find(signature)
    if start < 0:
        failures.append(f"{where} has no `{signature.strip()}` to check")
        return ""
    end = text.find("\n}\n", start)
    return text[start:end] if end > 0 else text[start:]


shim = code_of(SHIM.read_text())
tick = body_of(shim, "void sleepTick() {", SHIM.name)
sync = body_of(shim, "bool syncPanelPalette() {", SHIM.name)
poll = body_of(shim, "void pollPanelPalette() {", SHIM.name)
frame = body_of(shim, "void CrossPointHarness_perFrame() {", SHIM.name)

# 1. The sleep tick reads the light: the pair, the tube's decay, the bloom.
for call, what in (
    ("syncPanelPalette()", "the page's ink and paper"),
    ("pollPanelGlow()", "the tube's decay"),
    ("pollScanlines()", "the scanline bloom"),
):
    check(
        call in tick,
        f"sleepTick no longer calls {call}, so {what} keeps the lit value for "
        "the whole sleep though the firmware has switched the light off (R-15)",
    )

# 2. ...and does not ask the firmware to render. The request is a flag only the
#    firmware's loop() reads, and that loop next runs in the waking boot.
for call in ("pollPanelPalette()", "crosspointRequestRender()"):
    check(
        call not in tick,
        f"sleepTick calls {call}: the request is a flag only the firmware's "
        "loop() reads, and no loop() runs until the waking boot",
    )
check(
    "crosspointRequestRender()" not in sync,
    "syncPanelPalette requests a firmware render; that belongs to "
    "pollPanelPalette, which the sleep tick must not call",
)

# 3. Not while the power-off collapse holds the glass: it is dark until the
#    wake and presentIfNeeded returns before it would service the reconvert.
guard = tick.find("collapseOwnsGlass()")
check(
    guard >= 0
    and all(
        guard < tick.find(c)
        for c in ("syncPanelPalette()", "pollPanelGlow()", "pollScanlines()")
    ),
    "sleepTick's light reads are no longer behind the collapseOwnsGlass() check",
)

# 4. The awake path still has all three, and its palette poll still re-renders.
check(
    "syncPanelPalette()" in poll and "crosspointRequestRender()" in poll,
    "pollPanelPalette no longer syncs the pair and then asks the firmware to "
    "re-render (owner 2026-08-18: refresh the page on a page color change)",
)
for call in ("pollPanelPalette()", "pollPanelGlow()", "pollScanlines()"):
    check(call in frame, f"CrossPointHarness_perFrame no longer calls {call}")

if failures:
    print("frontlit_page_sleep: FAIL")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("frontlit_page_sleep: sleep tick reads the light; no firmware render asked while asleep")
