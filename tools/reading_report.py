#!/usr/bin/env python3
"""Read the reading ledger and say what it actually supports.

The device writes an append-only JSONL stream and computes NOTHING (see
src/ReadingLog.h). Every outcome lives here, offline, on purpose: an outcome
definition baked into the logger is one that cannot be revised when it turns
out to be the wrong one, and the first few will be.

    tools/reading_report.py reading.jsonl [reading.jsonl.1 ...]
    tools/reading_report.py --books ~/Documents/books reading.jsonl
    tools/reading_report.py --idle-cap 60 --washout 0 reading.jsonl

WHAT IT COMPUTES, and why each choice is the way it is. The full argument is in
docs/reading-experiments.md; this is the operational summary.

A RUN is a maximal stretch of consecutive page lines in the SAME book whose
gaps are all at or under --idle-cap seconds. Runs, not sessions: a book left
open on a table is not reading, and the only evidence the device has that
reading stopped is that pages stopped turning. The cap is a parameter and the
report prints its answer at three of them, because a conclusion that survives
only at one cap is a conclusion about the cap.

A run's ACTIVE TIME is the sum of the dwells of the pages that are COUNTED,
where a page's dwell is the gap to the next page. The last page's dwell is
unknown -- nothing says when he stopped looking at it -- so that page's text is
not counted and neither is any time for it. Rate = characters over active
minutes, and the two sides of that ratio come from the same pages: a page the
washout or the no-count filter drops takes its wall-clock with it. Anything
else deflates a run in proportion to how much of it was dropped, and the
washout drops pages exactly where the Phase 2 randomizer changes the arm.

CHARACTERS, not words, are the denominator. A word split across two lines is
two tokens, and which line breaker runs is one of the things being compared, so
a word count carries a bias pointing the same way as a treatment. See
src/activities/reader/PageTextMetrics.h in the firmware.

The WASHOUT drops the first --washout pages of each chapter. Under the Phase 2
randomizer the arm changes at chapter boundaries, so the adaptation transient
sits exactly where the treatment changes and is perfectly confounded with it.

THE COMPARISON IS A PERMUTATION TEST, blocked within book. No scipy, no normal
approximation, no distributional assumption -- with a few hundred runs the exact
test is cheap and the assumptions are the part most likely to be wrong. The
null is "the arm labels within each book are exchangeable", which is exactly
what the randomization makes true.

Nothing here writes anything, opens a socket, or reaches the network.
"""

import argparse
import json
import math
import os
import random
import sys
from collections import defaultdict

# The one hash shared with the device: readerBookKey() in the firmware's
# lib/hal/HalGPIO.h, FNV-1a over the book's path. Spelled out rather than
# imported because the device is C++ and this is the audit.
FNV64_OFFSET = 1469598103934665603
FNV64_PRIME = 1099511628211
MASK64 = (1 << 64) - 1


def book_key(path):
    h = FNV64_OFFSET
    for b in path.encode("utf-8"):
        h ^= b
        h = (h * FNV64_PRIME) & MASK64
    return h


def load(paths):
    """Parse every line of every file. Order is by timestamp, not by file.

    Rotation renames the live file to .1, so the newest generation is the one
    WITHOUT a suffix and a naive concatenation puts the stream out of order.
    Sorting by (ts, ms) fixes that without the caller having to know.

    Unparseable lines are counted and skipped rather than fatal: a phone killed
    mid-write leaves a partial last line, and losing the whole ledger to it
    would be absurd.
    """
    records, bad = [], 0
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except ValueError:
                        bad += 1
        except OSError:
            print("cannot read %s" % path, file=sys.stderr)
    records.sort(key=lambda r: (r.get("ts", 0), r.get("ms", 0)))
    return records, bad


def configs_and_pages(records):
    """Split the stream into the cfg table and the page list.

    A page names its cfg by id. A cfg id is a hash of the settings, so the same
    settings produce the same id in every launch and across generations -- which
    is what lets a comparison span months of file rotations.
    """
    cfgs, pages = {}, []
    for r in records:
        t = r.get("t")
        if t == "cfg":
            cfgs[r.get("id")] = r
        elif t == "page":
            pages.append(r)
    return cfgs, pages


def split_runs(pages, idle_cap):
    """Maximal same-book stretches with no gap over idle_cap seconds."""
    runs, cur = [], []
    for p in pages:
        if cur:
            prev = cur[-1]
            gap = p.get("ts", 0) - prev.get("ts", 0)
            same_book = p.get("bk") == prev.get("bk")
            if not same_book or gap < 0 or gap > idle_cap:
                runs.append(cur)
                cur = []
        cur.append(p)
    if cur:
        runs.append(cur)
    return runs


def run_stats(run, washout):
    """One run's contribution, or None if it cannot support a rate.

    Returns (cfg, book, minutes, chars, words, pages). The LAST page is excluded
    from the text totals: its dwell is unknown. A run of one page therefore
    contributes nothing, which is correct -- a single page is a timestamp, not a
    duration.

    A run that spans more than one configuration is DROPPED, not split. The
    settings changed mid-run, which means the reader stopped to change them, and
    a rate measured across that is a rate for neither configuration. It is rare
    and dropping it is cheaper than reasoning about it.

    THE NUMERATOR AND THE DENOMINATOR ARE ACCUMULATED BY THE SAME LOOP, and
    that is the whole shape of this function. A page's dwell is the gap to the
    NEXT page, so a page contributes (chars, dwell) or it contributes NEITHER --
    never its time without its text.

    This was wrong until 2026-08-25 and it was wrong in the worst possible
    direction. `minutes` was one span, last timestamp minus first, computed
    BEFORE the loop that skips pages; so every page the washout or the
    no-count filter dropped left its wall-clock behind in the denominator and
    deflated the run's rate in proportion to how much of the run was dropped.
    Under the Phase 2 randomizer the arm changes AT chapter boundaries, which is
    exactly where the washout bites, so the deflation lined up perfectly with
    the treatment: on synthetic data with one true rate and no effect at all,
    --washout 3 manufactured +477 chars/min at p=0.0002 where --washout 0
    correctly found +0 at p=1.0000. A tool that invents a significant result out
    of a parameter is worse than no tool.
    """
    if len(run) < 2:
        return None
    cfgs = {p.get("cfg") for p in run}
    if len(cfgs) != 1:
        return None
    minutes = 0.0
    chars = words = pages = 0
    for i in range(len(run) - 1):
        p = run[i]
        # The dwell is the gap to the next page. split_runs() has already
        # guaranteed it is non-negative and at or under the idle cap; a zero
        # gap (two page lines in the same second) carries text with no time to
        # read it in, so it is dropped whole rather than divided by.
        seconds = run[i + 1].get("ts", 0) - p.get("ts", 0)
        if seconds <= 0:
            continue
        if washout > 0 and p.get("pg", 0) < washout:
            continue
        c = p.get("c", 0)
        if not c:
            # 0/0/0 is the TXT/XTC reader saying it could not count. Excluded
            # from the rate rather than read as an empty page -- see the
            # channel's note in the firmware's lib/hal/HalGPIO.h. Its TIME goes
            # with it: a page with a denominator and no numerator is not a slow
            # page, it is an unmeasured one.
            continue
        chars += c
        words += p.get("w", 0)
        pages += 1
        minutes += seconds / 60.0
    if pages == 0 or minutes <= 0:
        return None
    return {
        "cfg": run[0].get("cfg"),
        "book": run[0].get("bk"),
        "minutes": minutes,
        # Wall-clock span of the whole run, INCLUDING the pages that were not
        # counted. Not the rate's denominator and must never become it -- that
        # is the bug above. It is here because the "volume" outcome in
        # docs/reading-experiments.md ("total active minutes per configuration")
        # is a question about time spent rather than about text read, and that
        # one does want the span. Nothing computes it yet; recorded so the next
        # outcome does not reach for `minutes` and get a different number than
        # it thinks.
        "span_minutes": (run[-1].get("ts", 0) - run[0].get("ts", 0)) / 60.0,
        "chars": chars,
        "words": words,
        "pages": pages,
        "start": run[0].get("ts", 0),
    }


def describe_config(cfg):
    """A short human label. Only the fields that usually differ."""
    if not cfg:
        return "(unknown)"
    fam = cfg.get("fam") or "built-in"
    bits = ["%s %spt" % (fam, cfg.get("pt"))]
    ls = {0: "tight", 1: "normal", 2: "wide"}.get(cfg.get("ls"), "ls%s" % cfg.get("ls"))
    bits.append(ls)
    if cfg.get("grid"):
        bits.append("grid")
    if not cfg.get("lig", 1):
        bits.append("no-lig")
    bits.append("lb%s" % cfg.get("lb"))
    bits.append("jt%s" % cfg.get("jt"))
    if cfg.get("dark"):
        bits.append("dark")
    if cfg.get("arm"):
        bits.append("[%s/%s]" % (cfg.get("exp"), cfg.get("arm")))
    return " ".join(str(b) for b in bits)


def group_by_book(runs):
    out = defaultdict(list)
    for r in runs:
        out[r["book"]].append(r)
    return out


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def permutation_test(groups, iters=20000, seed=12345):
    """Two-group difference of means, permuting WITHIN book.

    `groups` is {label: [(book, value, weight), ...]}. Exactly two labels.
    Weight is minutes, so a twenty-minute run counts for more than a two-minute
    one -- an unweighted mean of run rates lets a short noisy run outvote a long
    steady one.

    Permuting within book is what makes this a blocked test: the book is the
    largest confound, and shuffling labels across books would test a null that
    includes "the books differ", which is not in question.
    """
    labels = sorted(groups)
    if len(labels) != 2:
        return None
    by_book = defaultdict(list)
    for label in labels:
        for book, value, weight in groups[label]:
            by_book[book].append((label, value, weight))
    # Books with only one arm present carry no information about the contrast
    # and are dropped, exactly as a paired test drops unpaired observations.
    usable = {b: rows for b, rows in by_book.items() if len({r[0] for r in rows}) == 2}
    if not usable:
        return None

    def weighted_diff(assign):
        sums = {labels[0]: [0.0, 0.0], labels[1]: [0.0, 0.0]}
        for rows in assign.values():
            for label, value, weight in rows:
                sums[label][0] += value * weight
                sums[label][1] += weight
        a = sums[labels[0]][0] / sums[labels[0]][1] if sums[labels[0]][1] else 0.0
        b = sums[labels[1]][0] / sums[labels[1]][1] if sums[labels[1]][1] else 0.0
        return a - b

    observed = weighted_diff(usable)
    rng = random.Random(seed)
    hits = 0
    for _ in range(iters):
        shuffled = {}
        for book, rows in usable.items():
            perm = [r[0] for r in rows]
            rng.shuffle(perm)
            shuffled[book] = [(perm[i], rows[i][1], rows[i][2]) for i in range(len(rows))]
        if abs(weighted_diff(shuffled)) >= abs(observed) - 1e-12:
            hits += 1
    return {
        "labels": labels,
        "observed": observed,
        "p": (hits + 1) / (iters + 1),  # add-one: a p of exactly 0 is a lie
        "books": len(usable),
        "runs": sum(len(r) for r in usable.values()),
    }


def resolve_books(books_dir):
    """Map book keys back to filenames by rehashing the paths on the card.

    The ledger records a hash, never a title -- so a log copied off the phone
    does not carry a reading list with it. This puts the names back locally, for
    whoever has the card.

    The path hashed is the one the FIRMWARE saw, which is rooted at the card:
    "/books/Name.epub". A directory handed in here is treated as that root.
    """
    out = {}
    if not books_dir:
        return out
    for root, _dirs, files in os.walk(books_dir):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, books_dir)
            out["%016x" % book_key("/books/" + rel)] = rel
    return out


def report(records, idle_cap, washout, books_dir=None, iters=20000, out=sys.stdout):
    cfgs, pages = configs_and_pages(records)
    names = resolve_books(books_dir)

    runs = [s for s in (run_stats(r, washout) for r in split_runs(pages, idle_cap)) if s]

    print("reading ledger: %d cfg, %d pages, %d usable runs" % (len(cfgs), len(pages), len(runs)), file=out)
    print("idle cap %ds, washout %d pages" % (idle_cap, washout), file=out)
    if not runs:
        print("\nnothing to report yet. A usable run needs at least two pages in one book,", file=out)
        print("under one configuration, with no gap over the idle cap.", file=out)
        return {"runs": [], "by_config": {}, "comparison": None}

    by_cfg = defaultdict(list)
    for r in runs:
        by_cfg[r["cfg"]].append(r)

    # "counted min" and not "minutes": this column is the rate's denominator, so
    # it holds only the dwells of the pages that were counted. It is NOT how long
    # he had the book open under that configuration.
    print("\n%-46s %6s %11s %9s %9s" % ("configuration", "runs", "counted min", "chars/min", "pages/min"), file=out)
    rows = []
    for cfg_id, rs in by_cfg.items():
        minutes = sum(r["minutes"] for r in rs)
        chars = sum(r["chars"] for r in rs)
        pgs = sum(r["pages"] for r in rs)
        rows.append((minutes, cfg_id, rs, chars, pgs))
    for minutes, cfg_id, rs, chars, pgs in sorted(rows, reverse=True):
        label = describe_config(cfgs.get(cfg_id))
        print(
            "%-46s %6d %11.1f %9.0f %9.2f"
            % (label[:46], len(rs), minutes, chars / minutes if minutes else 0, pgs / minutes if minutes else 0),
            file=out,
        )

    # Per-run rate spread: the number that decides whether ANY of this is worth
    # doing. The power estimate in the doc is written against an assumed
    # coefficient of variation; this is the measured one, and it replaces the
    # assumption the moment there is data.
    rates = [r["chars"] / r["minutes"] for r in runs]
    m, sd = mean(rates), stdev(rates)
    print("\nrun-level rate: mean %.0f chars/min, sd %.0f, cv %.1f%% over %d runs"
          % (m, sd, 100 * sd / m if m else 0, len(runs)), file=out)

    # WITHIN-BOOK spread, which is the one the sample size actually depends on.
    #
    # The pooled figure above includes between-book variance, and the design
    # BLOCKS that out -- quoting it would overstate the runs needed, by a lot,
    # because the book is the largest confound there is. This is the pooled
    # within-book sd: residuals about each book's own mean, with one degree of
    # freedom spent per book.
    within_sq, dof = 0.0, 0
    for book, rs in group_by_book(runs).items():
        if len(rs) < 2:
            continue  # a book with one run contributes no residual
        vals = [r["chars"] / r["minutes"] for r in rs]
        bm = mean(vals)
        within_sq += sum((v - bm) ** 2 for v in vals)
        dof += len(vals) - 1
    within_sd = math.sqrt(within_sq / dof) if dof else 0.0
    if within_sd:
        print("within-book: sd %.0f, cv %.1f%% (%d residual df) -- this is the one the sample size depends on"
              % (within_sd, 100 * within_sd / m if m else 0, dof), file=out)

    cv_used = (within_sd / m) if (within_sd and m) else ((sd / m) if (sd and m) else 0.0)
    if cv_used:
        which = "within-book" if within_sd else "pooled (no book has two runs yet)"
        print("  sample sizes below use the %s cv:" % which, file=out)
        for effect in (0.03, 0.05, 0.10):
            # Two-sample, equal n per group, alpha .05 two-sided, power .80:
            #   n = 2 (z_a/2 + z_b)^2 sigma^2 / delta^2.
            # Unpaired, so it is CONSERVATIVE for a design that pairs within
            # book -- the pairing buys back some of it, by however much the
            # within-book runs are correlated.
            n = 2 * (1.96 + 0.84) ** 2 * cv_used**2 / effect**2
            print("  to detect a %2.0f%% difference: ~%d runs per arm" % (100 * effect, math.ceil(n)), file=out)

    # The comparison, when the log carries arms.
    groups = defaultdict(list)
    for r in runs:
        cfg = cfgs.get(r["cfg"]) or {}
        arm = cfg.get("arm")
        if arm:
            groups[arm].append((r["book"], r["chars"] / r["minutes"], r["minutes"]))
    comparison = permutation_test(groups, iters=iters) if len(groups) == 2 else None
    if comparison:
        print(
            "\n%s vs %s, blocked within book: %+.0f chars/min, p=%.4f (%d books, %d runs)"
            % (
                comparison["labels"][0],
                comparison["labels"][1],
                comparison["observed"],
                comparison["p"],
                comparison["books"],
                comparison["runs"],
            ),
            file=out,
        )
    elif groups:
        print("\n%d arm(s) present; a comparison needs exactly two." % len(groups), file=out)
    else:
        print("\nNo arms in this log -- Phase 1 instrumentation only. Nothing was randomized,", file=out)
        print("so the table above is observational: it says what he chose, not what worked.", file=out)

    if names:
        seen = {r["book"] for r in runs}
        print("\nbooks:", file=out)
        for key in sorted(seen):
            print("  %s  %s" % (key, names.get(key, "(not on this card)")), file=out)

    return {"runs": runs, "by_config": dict(by_cfg), "comparison": comparison}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="+", help="reading.jsonl and any rotated generations")
    ap.add_argument("--idle-cap", type=int, default=120, help="seconds; a longer gap ends a run (default 120)")
    ap.add_argument("--washout", type=int, default=0, help="pages to drop at the start of each chapter (default 0)")
    ap.add_argument("--books", default=None, help="card's books directory, to name the book keys")
    ap.add_argument("--iters", type=int, default=20000, help="permutation iterations")
    args = ap.parse_args(argv)

    records, bad = load(args.logs)
    if bad:
        print("skipped %d unparseable line(s)" % bad, file=sys.stderr)
    report(records, args.idle_cap, args.washout, args.books, args.iters)

    # Sensitivity: a conclusion that survives only at one idle cap is a
    # conclusion about the cap. Printed always, because the temptation to quote
    # the flattering one is exactly what this is here to spoil.
    if args.idle_cap == 120:
        for cap in (60, 300):
            print("\n--- same data, idle cap %ds ---" % cap)
            report(records, cap, args.washout, None, args.iters)
    return 0


if __name__ == "__main__":
    sys.exit(main())
