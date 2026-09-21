#!/usr/bin/env python3
"""The two touch/mouse hints point opposite ways, and one of them is a trap.

TOUCH -> MOUSE must stay OFF: with it on, SDL synthesizes a mouse event from
every real finger, and HalGPIO consumes mouse events (its
SDL_EVENT_MOUSE_BUTTON_DOWN branch feeds beginTouch, the X4 Pro digitizer).

MOUSE -> TOUCH must stay ON. It is SDL's own iOS default, and it is the only
way an INDIRECT POINTER can ever reach padWatch, which handles no mouse event:
SDL_uikitview.m diverts a UITouchTypeIndirectPointer touch to
indirectPointerPressed -> SDL_SendMouseButton and `continue`s, emitting no
SDL_EVENT_FINGER_* for it, and SDL_mouse.c's mouse->touch synthesis is what
turns it back into one.

It is INERT on this bundle today and the test is kept anyway. UIKit only
reports that touch type to an app declaring
UIApplicationSupportsIndirectInputEvents, which ios/Info.plist.in does not;
without it, pointer input arrives as ordinary direct touches and there is no
mouse event to convert (SDL says so itself in SDL_InitGCMouse). So this pins
correctness for the day that key is added -- and, more immediately, it pins the
"0" that sat in MOUSE_TOUCH from the harness's first day out of the tree. That
"0" was the TOUCH_MOUSE comment beside it applied to the opposite direction,
and it is exactly the confusion this test exists to catch: the two hint names
differ by one word, both values compile, both link, and both look identical on
glass to a finger. See BUGS.md S-041, which is OPEN -- the Mirroring report
that produced this file is NOT explained by it.

Source-level, like chip_tint_source_test.py and tap_dispatch_source_test.py:
the real check needs a Mac, an iPhone and Mirroring.
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
