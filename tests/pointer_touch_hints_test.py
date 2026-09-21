#!/usr/bin/env python3
"""The two touch/mouse hints, and why one of them carries iPhone Mirroring.

iPhone Mirroring delivers a click to the phone as UITouchTypeIndirectPointer.
SDL3's UIKit backend intercepts that touch type in touchesBegan/Ended
(SDL_uikitview.m), hands it to indirectPointerPressed/Released -- which emits
SDL_SendMouseButton -- and `continue`s, so NO SDL_EVENT_FINGER_DOWN is ever
emitted for it. ios/CrossPointIOSShim.cpp's padWatch handles only
SDL_EVENT_FINGER_*, so the pad, the tap candidate, the zen verb classifier,
the keyboard chip and the read-aloud tap all go dead under Mirroring unless
SDL's own mouse->touch synthesis is left on. The UIKit gesture recognizers
take indirect pointer natively, so the failure looks like an app that answers
gestures and ignores every button -- not like an app with dead input.

The harness shipped SDL_HINT_MOUSE_TOUCH_EVENTS = "0" from its first day,
disabling exactly that bridge. It was the neighbouring TOUCH_MOUSE comment
applied to the opposite direction.

Source-level, like chip_tint_source_test.py and tap_dispatch_source_test.py:
the real check needs a Mac, an iPhone and Mirroring, and the failure mode is
silent -- both values compile, both link, and both look identical on glass to
a finger. The directions are also one character apart in the hint name, which
is how they were confused once already.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHIM = ROOT / "ios" / "CrossPointIOSShim.cpp"


def hint_value(src: str, hint: str) -> str:
    m = re.search(r'SDL_SetHint\(\s*' + re.escape(hint) + r'\s*,\s*"([^"]*)"\s*\)', src)
    if not m:
        return None
    return m.group(1)


def main() -> int:
    src = SHIM.read_text(encoding="utf-8")
    failures = []

    # MOUSE -> TOUCH: must be on. Absent is also acceptable in principle (SDL's
    # iOS default is true), but require it explicitly: a default that changes
    # upstream would take Mirroring with it, silently.
    m2t = hint_value(src, "SDL_HINT_MOUSE_TOUCH_EVENTS")
    if m2t is None:
        failures.append(
            "SDL_HINT_MOUSE_TOUCH_EVENTS is not set at all. Set it to \"1\" "
            "explicitly -- SDL's iOS default is true today, but iPhone "
            "Mirroring depends on it and nothing else here would say so.")
    elif m2t not in ("1", "true"):
        failures.append(
            'SDL_HINT_MOUSE_TOUCH_EVENTS is "%s". With mouse->touch off, '
            "iPhone Mirroring's indirect-pointer clicks never become finger "
            "events and padWatch sees nothing." % m2t)

    # TOUCH -> MOUSE: must stay off, or a real finger is also delivered to
    # HalGPIO's mouse branch (beginTouch, the X4 Pro digitizer).
    t2m = hint_value(src, "SDL_HINT_TOUCH_MOUSE_EVENTS")
    if t2m is None:
        failures.append(
            "SDL_HINT_TOUCH_MOUSE_EVENTS is not set. It must be \"0\": SDL's "
            "iOS default would synthesize a mouse event from every real "
            "finger, and HalGPIO consumes mouse events.")
    elif t2m not in ("0", "false"):
        failures.append(
            'SDL_HINT_TOUCH_MOUSE_EVENTS is "%s", so a real finger is '
            "delivered twice -- once as a finger to padWatch, once as a mouse "
            "event to HalGPIO." % t2m)

    if failures:
        for f in failures:
            sys.stderr.write("FAIL: %s\n" % f)
        return 1
    print("pointer/touch hints: mouse->touch on, touch->mouse off")
    return 0


if __name__ == "__main__":
    sys.exit(main())
