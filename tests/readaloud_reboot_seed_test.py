#!/usr/bin/env python3
"""THE CAPTURE FLAG MUST SURVIVE THE IN-PROCESS REBOOT. (S-023)

The iOS reboot is a longjmp back into setup() in the SAME process, so every
static in ios/CrossPointReadAloud.mm outlives it while the state those statics
MIRROR does not. The 2026-08-26 failure was exactly that shape and it is worth
spelling out, because nothing in the app, the log or any other test could see
it:

  * `CrossPointReadAloud_begin()` seeded the firmware's capture flag from the
    Read Aloud (Experimental) toggle -- correct before capture became
    unconditional on the phone, never updated with it. A Speak Screen user
    leaves that toggle OFF, so begin() seeded FALSE on every boot.
  * `CrossPointReadAloud_perFrame()` then set it TRUE, but only on the edge
    `g_lastCaptureWanted != 1`.
  * On boot 1 the edge fires and the chain is healthy. Across the reboot the
    channel's `wanted_` is re-seeded false by begin() while `g_lastCaptureWanted`
    survives at 1 -- so the edge never fires again, EpubReaderActivity's capture
    returns at its first line forever, and every CHAIN line reads
    `page=0B rects=0 fb=0B` over a page that is on the glass.

Two properties are pinned here, and the second is the one that generalizes:

  1. begin() seeds the flag UNCONDITIONALLY TRUE, and perFrame pushes it
     unconditionally rather than behind the edge cache -- an edge guard around
     a single atomic store bought nothing and cost this.
  2. EVERY `g_last*` edge cache declared in the file is re-armed in begin().
     That list is the reboot contract for this translation unit; a new edge
     added without a matching re-arm is the same bug with a different name, and
     it would ship silently.

Source-level for the reason chip_tint_source_test.py and panel_source_test.py
are: the real check needs UIKit, a booted iPhone, and a reboot in the middle of
the run. A test that cannot run in this suite is a test nobody runs.

Usage: readaloud_reboot_seed_test.py [path-to-CrossPointReadAloud.mm]
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
ADAPTER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (
    REPO / "ios" / "CrossPointReadAloud.mm")

raw = ADAPTER.read_text()

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def strip_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def body_of(text, signature):
    """The brace-matched body of a function, comments removed."""
    start = text.find(signature)
    if start < 0:
        return None
    open_brace = text.find("{", start)
    if open_brace < 0:
        return None
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace:i + 1]
    return None


code = strip_comments(raw)

begin = body_of(code, "void CrossPointReadAloud_begin(void)")
per_frame = body_of(code, "void CrossPointReadAloud_perFrame(void)")
check(begin is not None, "CrossPointReadAloud_begin(void) not found")
check(per_frame is not None, "CrossPointReadAloud_perFrame(void) not found")

# --- 1. The seed, before the first loop() -----------------------------------
#
# begin() runs on EVERY boot including the longjmp, and it runs before the
# first loop() iteration -- which is where a resumed book renders its first
# page. A seed derived from any preference is what put a `false` on the wrong
# side of the boundary; the value is not a preference, it is a constant on this
# platform, and perFrame's own comment has said so since build 42.
if begin is not None:
    seeds = re.findall(r"setReadAloudCaptureWanted\(([^;]*)\);", begin)
    check(
        seeds,
        "CrossPointReadAloud_begin no longer seeds the capture flag; a book "
        "resumed at boot renders its first page inside the first loop() "
        "iteration, before perFrame has ever run",
    )
    check(
        all(s.strip() == "true" for s in seeds),
        "CrossPointReadAloud_begin seeds the capture flag from something other "
        f"than a literal true ({seeds!r}). Capture is unconditional on iOS; a "
        "pref-derived seed here re-cleared the flag on every reboot while "
        "perFrame's edge cache survived to suppress the correction (S-023)",
    )

# --- 2. perFrame pushes, it does not merely intend to -----------------------
if per_frame is not None:
    push = re.search(r"gpio\.setReadAloudCaptureWanted\(true\);", per_frame)
    check(
        push is not None,
        "CrossPointReadAloud_perFrame no longer asserts the capture flag; "
        "nothing else re-asserts it after begin()",
    )
    guard = re.search(r"if\s*\(\s*g_lastCaptureWanted\s*!=\s*1\s*\)\s*\{",
                      per_frame)
    if push is not None and guard is not None:
        # The push must sit OUTSIDE the edge block. Anything inside it can be
        # suppressed by a cache that outlived the boundary.
        block_start = guard.end() - 1
        depth = 0
        block_end = len(per_frame)
        for i in range(block_start, len(per_frame)):
            if per_frame[i] == "{":
                depth += 1
            elif per_frame[i] == "}":
                depth -= 1
                if depth == 0:
                    block_end = i
                    break
        check(
            not (block_start < push.start() < block_end),
            "the capture-flag push sits inside the g_lastCaptureWanted edge "
            "block. That cache survives the in-process reboot while the flag "
            "it mirrors is re-seeded, so the push it guards is the one call "
            "that never happens (S-023). Push unconditionally and let the "
            "static throttle the log only",
        )

# --- 3. Every edge cache is re-armed at the boundary ------------------------
#
# The generalizing half. `g_lastEnabled` and `g_lastRatePercent` were already
# re-armed in begin(); `g_lastCaptureWanted` was not, and nothing said so.
edges = sorted(set(re.findall(r"^\s*int\s+(g_last\w+)\s*=\s*-1\s*;", code,
                              flags=re.M)))
check(
    edges,
    "no `int g_last* = -1;` edge caches found -- either they were renamed or "
    "this test has gone blind; it must not silently pass on nothing",
)
if begin is not None:
    for name in edges:
        check(
            re.search(rf"\b{name}\s*=\s*-1\s*;", begin) is not None,
            f"{name} is an edge cache that is NOT re-armed in "
            "CrossPointReadAloud_begin. The iOS reboot is a longjmp, so it "
            "survives with a stale answer while the state it mirrors is rebuilt "
            "-- the edge then never fires again for the life of the process",
        )

if failures:
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    sys.exit(1)
print(f"readaloud reboot seed: capture flag re-seeded true, "
      f"{len(edges)} edge caches re-armed ({', '.join(edges)})")
