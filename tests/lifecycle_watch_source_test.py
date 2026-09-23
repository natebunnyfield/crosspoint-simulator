#!/usr/bin/env python3
"""The app lifecycle events must be read from a WATCH, never from the queue.

SDL does not queue them. SDL_SendAppEvent special-cases TERMINATING,
LOW_MEMORY and the four BACKGROUND/FOREGROUND events and hands them to
SDL_CallEventWatchers only -- "We won't actually queue this event, it needs to
be handled in this call stack by an event watcher" (SDL_events.c). Anything
that reads one out of SDL_PollEvent is dead code on a real device.

This is not hypothetical and it is not cheap. S-037's wake fix shipped on
2026-09-06 with BOTH halves reading SDL_EVENT_DID_ENTER_FOREGROUND out of the
poll loop, and neither ran on a phone for eighteen days -- the one device the
feature exists for. The app could return from the background and re-sleep on
its first loop(), which is indistinguishable from an app that has stopped
receiving input, and it is a live candidate for S-041.

Nothing caught it. The compiler cannot: the branch is reachable code on a type
that exists. The shell test could not: tests/test_foreground_wake.sh drives the
script's FOREGROUND verb, which goes through pushForeground() ->
SDL_PushEvent, and THAT does queue -- so the scripted route exercised a path
the real lifecycle transition never takes. This is CLAUDE.md's "a scripted pass
is not evidence about input routing" with a second instance.

So the gate is mechanical and source-level, like tap_dispatch_source_test.py:
the poll loop must not test for one of these types, and the watch must exist.
A watch sees BOTH routes, because SDL_PushEvent calls the watchers before it
queues -- so moving to a watch costs the scripted path nothing.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GPIO = ROOT / "src" / "HalGPIO.cpp"

# The six SDL_SendAppEvent special-cases. TERMINATING and LOW_MEMORY are here
# for completeness: nothing reads them today, and a future branch on either
# would be dead in exactly the same way.
NEVER_QUEUED = [
    "SDL_EVENT_TERMINATING",
    "SDL_EVENT_LOW_MEMORY",
    "SDL_EVENT_WILL_ENTER_BACKGROUND",
    "SDL_EVENT_DID_ENTER_BACKGROUND",
    "SDL_EVENT_WILL_ENTER_FOREGROUND",
    "SDL_EVENT_DID_ENTER_FOREGROUND",
]

# Lines that legitimately name these types: the watch's own switch, the
# script verb that synthesizes one, and prose.
def is_comment(line: str) -> bool:
    return line.lstrip().startswith(("//", "*", "/*"))


def main() -> int:
    src = GPIO.read_text(encoding="utf-8")
    lines = src.splitlines()
    failures = []

    # 1. The watch must exist and must be installed.
    if "lifecycleWatch" not in src:
        failures.append(
            "src/HalGPIO.cpp has no lifecycleWatch. The app lifecycle events "
            "are watcher-only; without a watch nothing sees them on a device.")
    if "SDL_AddEventWatch(lifecycleWatch" not in src:
        failures.append(
            "lifecycleWatch is never passed to SDL_AddEventWatch, so it never "
            "runs.")

    # 2. No `e.type == <never-queued>` test anywhere -- that shape is only ever
    #    a read of the polled event struct. The watch switches on `e->type`.
    for n, line in enumerate(lines, 1):
        if is_comment(line):
            continue
        for ev in NEVER_QUEUED:
            if re.search(r"e\.type\s*==\s*" + ev, line):
                failures.append(
                    "%s:%d reads %s off the polled event (`e.type ==`). SDL "
                    "never queues it -- this branch cannot run on a device. "
                    "Latch it in lifecycleWatch instead." % (GPIO.name, n, ev))

    if failures:
        for f in failures:
            sys.stderr.write("FAIL: %s\n" % f)
        return 1
    print("lifecycle events: read from a watch, not from the queue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
