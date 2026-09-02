#!/usr/bin/env python3
"""ONE gesture-action dispatcher, and the SDL deliberate tap goes through it.

The one-finger tap is SDL's verb, classified below UIKit in
ios/CrossPointIOSShim.cpp, while every other gesture is a UIKit recognizer
dispatched by performGestureAction in ios/CrossPointZenRecognizers.mm. Until
2026-09-02 the tap branch carried its own smaller switch (ToggleZen,
FontFamilyStep, the button actions) and a comment saying an appended action
would have to be taught there too -- and both actions appended after it,
FontFamilyStepBack (2026-08-29) and OpenActionMenu (2026-09-01), missed it.
Settings.app offered them on the three Tap rows; binding either was a silent
no-op on the gesture a reader uses most (docs/ux-navigation-audit-2026-09-02.md,
finding 1, P1).

Source-level, like chip_tint_source_test.py and panel_source_test.py: the real
check needs a booted simulator and a finger, and this is the shape of drift a
compile cannot see -- a second switch compiles, links and is only wrong when
the next action is appended. So this pins that the shim's tap branch calls the
shared entry point and holds NO switch of its own.

Known limit (adversarial review 2026-09-02): the "no switch of its own" half
is a blocklist of the names the OLD switch used, inside a regex window that
ends at the fingerUp call. A second dispatcher written with new names, or
placed outside that window, passes. It pins the historical shape, not the
invariant; the invariant is the comment at the call site.
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SHIM = REPO / "ios" / "CrossPointIOSShim.cpp"
RECOGNIZERS = REPO / "ios" / "CrossPointZenRecognizers.mm"

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


shim = SHIM.read_text()
rec = RECOGNIZERS.read_text()

# The tap branch: from the zone hit-test to the fingerUp that closes it.
m = re.search(r"gesturebind::oneFingerAction\(\s*gesturebind::OneFinger::Tap,.*?applyActions\(g_core\.fingerUp",
              shim, re.S)
check(m is not None, "shim: could not find the SDL deliberate-tap dispatch branch")
branch = m.group(0) if m else ""

check("CrossPointZenRecognizers_performAction(" in branch,
      "shim tap branch does not call CrossPointZenRecognizers_performAction -- a second dispatcher is back")
check("\"deliberate tap\"" in branch,
      "shim tap branch must name itself \"deliberate tap\" (the log name the zen toggle keys on)")
for own in ("gesturebind::buttonFor(", "queueButtonTap(", "injectFontFamilyStep(",
            "CrossPointZen_toggleFromRecognizer(", "is not handled on the SDL tap path"):
    check(own not in branch, f"shim tap branch dispatches on its own again: {own!r}")

# The entry point exists and forwards to the one dispatcher.
check(re.search(r'extern "C" void CrossPointZenRecognizers_performAction\(int action, const char \*what\)\s*\{\s*'
                r"performGestureAction\(static_cast<gesturebind::Action>\(action\), what\);", rec) is not None,
      "recognizers: CrossPointZenRecognizers_performAction must forward straight to performGestureAction")

# And that dispatcher handles every host action the bindings can name. The
# button actions fold through gesturebind::buttonFor; the rest are named.
for action in ("ToggleZen", "FontFamilyStep", "FontFamilyStepBack", "OpenActionMenu", "Nothing"):
    check(f"gesturebind::Action::{action}" in rec.split("void performGestureAction")[1].split("\n}\n")[0],
          f"performGestureAction no longer names Action::{action}")

if failures:
    for f in failures:
        print("FAIL:", f)
    sys.exit(1)
print("tap_dispatch_source: OK")
