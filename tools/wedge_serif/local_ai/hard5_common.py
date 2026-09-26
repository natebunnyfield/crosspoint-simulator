"""Shared data for the hard-pairs evaluation (docs/hard-pairs-eval-2026-09-26.md).

Every reading he has given, on ONE zero: the 2026-09-20 bench fonts
(bench/fonts-2026-09-20/), the font every bench and re-ask answer was given
against and the zero the B2 fit lives on.

    bench     bench_values.json "literal" (the 396-row bench, 2026-09-20/21)
    reask     bench/answers/reask-2026-09-25-answers.json (same fonts, 40 rows)
    outlier   extra-judgments.json, kind outlier, converted to the 09-20 zero
    active    extra-judgments.json, kind active (session 1), converted

The re-ask readings are NOT in the shipped B2's training (b2_fit.readings
never read them); they are used here only as a second reading of his truth.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, WS)
import bench_fit  # noqa: E402
import b2_fit  # noqa: E402

STYLES = ("roman", "italic")
REASK_KEY = os.path.join(WS, "bench", "reask-2026-09-25.key.json")
REASK_ANS = os.path.join(WS, "bench", "answers", "reask-2026-09-25-answers.json")
EXTRA = os.path.join(WS, "bench", "answers", "extra-judgments.json")
SCRATCH = os.environ.get(
    "HARD5_DIR",
    "/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/"
    "c03d2901-2d80-4074-84f8-7539dfb0f2e2/scratchpad/hard5")


def all_readings(style):
    """{pair: [(d on the 09-20 zero, source)]}, g dropped as in bench_fit."""
    out = {p: [(float(d), "bench")] for p, d in bench_fit.judgments(style).items()}
    key = {(r["style"], r["id"]): r for r in json.load(open(REASK_KEY))["rows"]}
    for a in json.load(open(REASK_ANS))["answers"]:
        r = key[(a["style"], a["id"])]
        if r["style"] == style and "g" not in r["pair"]:
            out.setdefault(r["pair"], []).append((float(a["delta"]), "reask"))
    for r in json.load(open(EXTRA))["rows"]:
        if r["style"] == style and "g" not in r["pair"]:
            src = r.get("kind", "extra")
            if r.get("verdict") == "skipped-ok":
                src = "active-skip"
            out.setdefault(r["pair"], []).append((float(r["d0920"]), src))
    return out
