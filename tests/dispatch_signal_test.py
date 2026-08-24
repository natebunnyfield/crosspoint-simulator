#!/usr/bin/env python3
"""The web-server dispatch hand-off must signal the parked worker from a SCOPE
GUARD, not from a trailing statement.

P0, 2026-08-08. WebServer's accept worker parses a request, parks it behind a
condition variable, and waits for handleClient() -- on the firmware thread -- to
drain it and set `dispatchDone`. The signal used to be a trailing statement
after the handler call. Route handlers are arbitrary std::function<void()> with
no no-throw contract and this translation unit builds WITH exceptions, so one
std::bad_alloc under memory pressure skipped the flag and left the accept worker
parked forever: the whole file-transfer server hung, with no recovery.

WHY THIS TEST WAS REWRITTEN (2026-08-23). It used to be a C++ file that included
ZERO repo headers and re-implemented both the bug and the fix locally, on its own
Channel struct. Its own comment admitted it: "this pins the pattern, not the
socket code". Measured before replacing it:

  * `grep -c '#include "'` on it returned 0 -- it never read src/WebServer.cpp,
    so deleting the guard from the shipping code left it green.
  * Its assertions were bare assert(), so `-DNDEBUG` compiled them away; an
    inverted assertion still printed "dispatch_signal: PASS" and exited 0.

Source-level on purpose, and for the same reason chip_tint_source_test.py is:
the behavioural test would need a socket, a worker thread and a throwing handler
inside the real server, and what actually regresses here is the SHAPE of the
code -- a guard demoted back to a trailing statement compiles, links, and passes
everything else.

    tests/dispatch_signal_test.py [path/to/WebServer.cpp]

The optional path is how the guard's absence is proved to turn this red: point
it at a mutated copy.
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SERVER = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "src" / "WebServer.cpp"

failures = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        failures.append(msg)


def strip_comments(text):
    """Blank out // and /* */ comments, preserving length and line structure.

    Load-bearing: WebServer.cpp's own comment QUOTES the trailing statement it
    replaced -- `used to skip the "dispatchDone = true" below` -- so a naive
    count of that string in the function finds two and reports the bug that was
    fixed. Whitespace is substituted rather than deleted so every offset this
    test computes still lines up with the real file.
    """
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"' or c == "'":
            q = c
            out.append(c)
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == "\\":
                    if i + 1 < n:
                        out.append(text[i + 1])
                    i += 2
                    continue
                if text[i] == q:
                    i += 1
                    break
                i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def body_after(text, index):
    """Brace-matched body starting at the first '{' at or after `index`."""
    start = text.index("{", index)
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return start, text[start : i + 1]
        i += 1
    raise ValueError("unbalanced braces")


if not SERVER.exists():
    print(f"FAIL cannot read {SERVER}", file=sys.stderr)
    sys.exit(1)

src = strip_comments(SERVER.read_text())
print(f"dispatch_signal: reading {SERVER}")

# 1. The drain function itself.
m = re.search(r"\bvoid\s+WebServer::handleClient\s*\(\s*\)", src)
check(bool(m), "WebServer::handleClient() exists (it is the drain the guard protects)")
if not m:
    sys.exit(1)
_, fn = body_after(src, m.end())

# 2. A local struct with a DESTRUCTOR is what makes the signal fire on the
#    exception-unwind path. Its name is not load-bearing; its being a destructor
#    is the whole fix.
guard = re.search(r"\bstruct\s+(\w+)\s*\{", fn)
check(
    bool(guard),
    "handleClient declares a local scope-guard struct (the exception-safe form)",
)
if not guard:
    sys.exit(1)
name = guard.group(1)
struct_at, struct_body = body_after(fn, guard.start())

dtor = re.search(r"~" + name + r"\s*\(\s*\)", struct_body)
check(bool(dtor), f"...and `{name}` has a destructor, so it fires on unwind too")
if not dtor:
    sys.exit(1)
_, dtor_body = body_after(struct_body, dtor.end())

# 3. The destructor is what sets the flag and wakes the worker.
check(
    "dispatchDone = true" in dtor_body,
    f"~{name}() sets dispatchDone -- the flag the parked worker waits on",
)
check(
    "dispatchCv.notify_all()" in dtor_body,
    f"~{name}() notifies dispatchCv, so a worker already parked is woken",
)
check(
    "dispatchMutex" in dtor_body,
    f"~{name}() takes dispatchMutex before touching the flag",
)

# 4. THE REGRESSION ITSELF: nothing in handleClient may set dispatchDone outside
#    that destructor. A trailing `dispatchDone = true` after the handler call IS
#    the bug -- it reads as belt-and-braces and reintroduces the hang, because a
#    throw skips it.
total = fn.count("dispatchDone = true")
inside = dtor_body.count("dispatchDone = true")
check(
    total == inside,
    f"every dispatchDone assignment in handleClient is inside ~{name}() "
    f"(found {total}, {inside} of them in the destructor) -- a trailing one is "
    "skipped by a throwing handler, which is the original hang",
)

# 5. The guard OBJECT has to be constructed, at the function's own scope, before
#    the handler runs. A struct that is only declared guards nothing.
after_struct = fn[struct_at + len(struct_body):]
inst = re.match(r"\s*(\w+)\s*\{[^;]*\}\s*;", after_struct)
check(
    bool(inst),
    f"`{name}` is instantiated as a local object (a declared-but-unconstructed "
    "guard never runs)",
)

call = fn.find("dispatchParkedRequest()")
check(call != -1, "handleClient still invokes dispatchParkedRequest()")
check(
    call > struct_at,
    "the guard is constructed BEFORE the handler runs -- a guard created after "
    "it cannot cover a throw from it",
)

# 6. The handler must not run under the dispatch lock: that was the other half of
#    the original design note, and holding it across a handler that calls
#    ESP.restart() deadlocks the worker on a mutex the restart never releases.
between = fn[struct_at:call] if call > struct_at else ""
check(
    "lock(impl_->dispatchMutex)" not in between,
    "the handler is invoked with dispatchMutex unlocked",
)

if failures:
    print(f"\n{len(failures)} failure(s)", file=sys.stderr)
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    sys.exit(1)
print("dispatch_signal: the scope-guard hand-off is intact in " + SERVER.name)
