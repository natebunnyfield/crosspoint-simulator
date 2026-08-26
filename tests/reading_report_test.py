#!/usr/bin/env python3
"""tools/reading_report.py -- the outcome computation.

Every failure here is a WRONG CONCLUSION from a correct log. That is worse than
a wrong log, because the log can be re-analysed and a conclusion, once believed,
is acted on. The device deliberately computes nothing (src/ReadingLog.h), so
this file is where the whole definition of "got the most reading done" lives and
where it has to be pinned.

Seven things, each of which was a real decision rather than an implementation
detail:

  1. RUN SEGMENTATION. A book left open on a table is not reading. If the idle
     cap did not split, one interrupted afternoon would be logged as a
     four-hour session at a crawl, and it would be attributed to whatever
     configuration happened to be in force.
  2. THE LAST PAGE IS NOT COUNTED. Nothing says when he stopped looking at it.
     Counting it inflates every rate, and it inflates SHORT runs most -- so it
     would favour whichever arm produced more interruptions.
  3. A RUN SPANNING TWO CONFIGURATIONS IS DROPPED. He stopped to change a
     setting; the rate across that belongs to neither.
  4. PAGES WITH NO COUNT ARE EXCLUDED, NOT ZERO. TXT and XTC publish 0/0/0
     because there is no laid-out page to walk. Reading those as empty pages
     would drive every rate that touched them toward zero.
  5. THE COMPARISON IS BLOCKED WITHIN BOOK. The book is the largest confound by
     a wide margin -- larger than any typography effect. A test that permuted
     labels across books would be testing whether the books differ, which they
     do, which is not the question.
  6. WEIGHTED BY MINUTES. An unweighted mean of run rates lets a two-minute
     noisy run outvote a forty-minute steady one.
  7. A DROPPED PAGE TAKES ITS TIME WITH IT. Decisions 2, 4 and the washout all
     remove PAGES; every one of them must remove that page's dwell from the
     denominator too. Until 2026-08-25 the duration was one span computed
     before the filters ran, so a filtered page left its wall-clock behind and
     deflated the run. The washout drops pages at chapter boundaries and the
     Phase 2 randomizer changes the arm at chapter boundaries, so the deflation
     was confounded with the treatment by construction -- on a log with one
     true rate and no effect, --washout 3 reported +477 chars/min at p=0.0002.
     This is the failure mode this whole file is named after: a wrong
     conclusion from a correct log.

The synthetic logs below are built so the right answer is known by construction.
"""

import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))

import reading_report as rr  # noqa: E402


def cfg(cfg_id, **kw):
    d = {
        "t": "cfg",
        "ts": 0,
        "ms": 0,
        "id": cfg_id,
        "fam": "Caledonia",
        "pt": 15,
        "slot": 1,
        "ls": 1,
        "grid": 0,
        "jt": 40,
        "lig": 1,
        "ligoff": "",
        "lb": 0,
        "marg": 5,
        "dev": "X3",
        "scale": 2,
        "pw": 792,
        "ph": 528,
        "dark": 0,
        "ink": "5C332B",
        "paper": "F9F3E9",
        "exp": "",
        "arm": "",
        "armseed": 0,
    }
    d.update(kw)
    return d


def page(ts, cfg_id, bk="aaaaaaaaaaaaaaaa", sp=0, pg=0, chars=500, words=100):
    return {"t": "page", "ts": ts, "ms": ts * 1000, "cfg": cfg_id, "bk": bk, "fmt": "epub",
            "sp": sp, "pg": pg, "w": words, "c": chars, "ln": 20}


def run_report(records, idle_cap=120, washout=0, iters=2000):
    out = io.StringIO()
    result = rr.report(records, idle_cap, washout, None, iters, out)
    return result, out.getvalue()


class BookKey(unittest.TestCase):
    def test_matches_the_firmware_hash(self):
        # readerBookKey() is FNV-1a over the path. Pinned against a value
        # computed independently from the constants, so a typo in either the
        # basis or the prime is caught -- the audit is worthless if the audit's
        # hash is not the device's hash.
        h = 1469598103934665603
        for b in b"/books/Moby.epub":
            h ^= b
            h = (h * 1099511628211) & ((1 << 64) - 1)
        self.assertEqual(rr.book_key("/books/Moby.epub"), h)

    def test_resolves_names_from_a_directory(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "Moby.epub"), "w").close()
            names = rr.resolve_books(d)
            self.assertEqual(names["%016x" % rr.book_key("/books/Moby.epub")], "Moby.epub")


class Loading(unittest.TestCase):
    def test_orders_by_timestamp_across_rotated_files(self):
        # Rotation renames the LIVE file to .1, so the newest generation has no
        # suffix. Concatenating in argument order interleaves months wrongly and
        # every gap computed across the seam is garbage.
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            new = os.path.join(d, "reading.jsonl")
            old = os.path.join(d, "reading.jsonl.1")
            with open(new, "w") as f:
                f.write(json.dumps(page(9000, 1)) + "\n")
            with open(old, "w") as f:
                f.write(json.dumps(page(100, 1)) + "\n")
            records, bad = rr.load([new, old])
            self.assertEqual(bad, 0)
            self.assertEqual([r["ts"] for r in records], [100, 9000])

    def test_a_truncated_last_line_does_not_lose_the_file(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "reading.jsonl")
            with open(p, "w") as f:
                f.write(json.dumps(page(1, 1)) + "\n")
                f.write('{"t":"page","ts":2,')  # killed mid-write
            records, bad = rr.load([p])
            self.assertEqual(len(records), 1)
            self.assertEqual(bad, 1)


class Segmentation(unittest.TestCase):
    def test_a_long_gap_splits_a_run(self):
        pages = [page(0, 1), page(30, 1), page(60, 1), page(6000, 1), page(6030, 1)]
        runs = rr.split_runs(pages, 120)
        self.assertEqual([len(r) for r in runs], [3, 2])

    def test_a_different_book_splits_a_run_even_with_no_gap(self):
        pages = [page(0, 1, bk="a" * 16), page(10, 1, bk="b" * 16)]
        self.assertEqual([len(r) for r in rr.split_runs(pages, 120)], [1, 1])

    def test_a_backwards_clock_splits_rather_than_producing_a_negative_gap(self):
        # A phone's wall clock moves. A dwell computed across an NTP step is a
        # negative number, and a negative minute would flip the sign of a rate.
        pages = [page(1000, 1), page(10, 1)]
        self.assertEqual([len(r) for r in rr.split_runs(pages, 120)], [1, 1])


class RunStats(unittest.TestCase):
    def test_excludes_the_last_page_from_the_text_total(self):
        # Three pages, 30 s apart: 60 s of active time and only the first TWO
        # pages' text is known to have been read in it.
        run = [page(0, 1, chars=500), page(30, 1, chars=500), page(60, 1, chars=500)]
        s = rr.run_stats(run, 0)
        self.assertAlmostEqual(s["minutes"], 1.0)
        self.assertEqual(s["chars"], 1000)
        self.assertEqual(s["pages"], 2)
        self.assertAlmostEqual(s["chars"] / s["minutes"], 1000.0)

    def test_a_single_page_is_a_timestamp_not_a_duration(self):
        self.assertIsNone(rr.run_stats([page(0, 1)], 0))

    def test_a_run_spanning_two_configs_is_dropped(self):
        run = [page(0, 1), page(30, 2), page(60, 2)]
        self.assertIsNone(rr.run_stats(run, 0))

    def test_pages_with_no_count_are_excluded_not_zero(self):
        # A TXT page publishes 0/0/0. Two real pages and one uncountable one:
        # the uncountable page must not drag the rate down.
        run = [page(0, 1, chars=500), page(30, 1, chars=0, words=0), page(60, 1, chars=500), page(90, 1)]
        s = rr.run_stats(run, 0)
        # Four pages: the last is excluded because its dwell is unknown, and the
        # uncountable one is excluded because it has no denominator. Two remain.
        self.assertEqual(s["chars"], 1000)
        self.assertEqual(s["pages"], 2)
        # And the uncountable page's TIME goes with its text. This assertion was
        # 1.5 minutes until 2026-08-25, on the reasoning that "he read it" -- but
        # a page with a denominator and no numerator is not a slow page, it is an
        # UNMEASURED one, and keeping its thirty seconds pushed a true 1000
        # chars/min run down to 667. Two known pages read in sixty seconds is
        # 1000 chars/min whatever happened in the gap between them.
        self.assertAlmostEqual(s["minutes"], 1.0)
        self.assertAlmostEqual(s["chars"] / s["minutes"], 1000.0)

    def test_a_run_of_only_uncountable_pages_contributes_nothing(self):
        run = [page(0, 1, chars=0, words=0), page(30, 1, chars=0, words=0)]
        self.assertIsNone(rr.run_stats(run, 0))

    def test_washout_takes_a_dropped_page_s_time_with_its_text(self):
        # FOUR pages 30 s apart at one true rate of 1000 chars/min. Whatever the
        # washout does to the numerator it must do to the denominator, or the
        # rate stops being the rate.
        run = [page(0, 1, pg=0, chars=500), page(30, 1, pg=1, chars=500),
               page(60, 1, pg=2, chars=500), page(90, 1, pg=3, chars=500)]
        s0 = rr.run_stats(run, 0)
        self.assertEqual(s0["chars"], 1500)
        self.assertAlmostEqual(s0["minutes"], 1.5)
        self.assertAlmostEqual(s0["chars"] / s0["minutes"], 1000.0)

        s2 = rr.run_stats(run, 2)
        self.assertEqual(s2["chars"], 500)   # only pg=2; pg=3 is the last page
        self.assertAlmostEqual(s2["minutes"], 0.5)
        self.assertAlmostEqual(s2["chars"] / s2["minutes"], 1000.0,
                               msg="the washout must not change the measured rate of a run read at one rate")

        # THIS ASSERTION FAILS AGAINST THE CODE AS IT STOOD BEFORE 2026-08-25,
        # and the test it replaces PINNED that code. The old one asserted
        # minutes == 1.5 at washout 2 -- the full span -- with a comment saying
        # the washout "must not change the DURATION" because "rescaling it would
        # inflate the rate of whichever arm sits behind more chapter
        # boundaries."
        #
        # The first half of that reasoning is right and the conclusion inverts
        # it. A global RESCALE of the duration -- keeping the span and inflating
        # it back up by pages_kept/pages_total -- is indeed wrong, and that is
        # what the comment was arguing against. But the code it was defending
        # did not rescale either: it kept the whole span against a fraction of
        # the text, which is the SAME bias in the other direction and larger.
        # A run whose chapter boundary eats 3 of its 5 pages was reported at 40%
        # of its true rate; one whose chapters are 12 pages long lost 25%. The
        # Phase 2 randomizer changes the arm AT chapter boundaries, so that
        # deflation is perfectly confounded with the treatment: on synthetic
        # data with one true rate and no effect whatsoever, --washout 3 produced
        # +477 chars/min at p=0.0002 (--washout 0 correctly gave +0, p=1.0000).
        # The tool manufactured its own significant result out of a parameter.
        #
        # Neither keeping the span nor rescaling it is the answer. The answer is
        # that a page contributes its text and its dwell together or contributes
        # neither, which is what run_stats does now and what
        # test_chapter_length_alone_does_not_manufacture_an_arm_effect proves at
        # the level of the report.
        self.assertLess(s2["minutes"], 1.5)


class Comparison(unittest.TestCase):
    def _arm_log(self, a_rate, b_rate, books=6, runs_per=6, chars=500):
        """Two arms whose true rates are set by construction.

        Each book contributes runs of both arms, so the blocked test has pairs
        everywhere. Page spacing is chosen to hit the requested chars/min.
        """
        records = [cfg(1, exp="e", arm="A", armseed=7), cfg(2, exp="e", arm="B", armseed=7)]
        ts = 0
        for b in range(books):
            bk = ("%016x" % (b + 1))
            for i in range(runs_per):
                for cfg_id, rate in ((1, a_rate), (2, b_rate)):
                    step = int(round(60.0 * chars / rate))
                    for k in range(6):
                        records.append(page(ts + k * step, cfg_id, bk=bk, sp=i, pg=k, chars=chars))
                    ts += 6 * step + 100000  # a gap far past any idle cap
        return records

    def test_a_large_real_difference_is_detected(self):
        records = self._arm_log(1000.0, 1300.0)
        result, text = run_report(records, iters=2000)
        self.assertIsNotNone(result["comparison"])
        self.assertLess(result["comparison"]["p"], 0.05)
        self.assertLess(result["comparison"]["observed"], 0)  # A slower than B
        self.assertIn("blocked within book", text)

    def test_no_difference_is_not_detected(self):
        records = self._arm_log(1000.0, 1000.0)
        result, _ = run_report(records, iters=2000)
        self.assertGreater(result["comparison"]["p"], 0.05)

    def test_a_book_effect_alone_does_not_manufacture_a_result(self):
        # THE TEST THIS FILE EXISTS FOR. Books differ enormously in reading
        # rate; arms do not differ at all. An unblocked comparison would find
        # whatever imbalance the book assignment happened to produce.
        records = [cfg(1, exp="e", arm="A", armseed=7), cfg(2, exp="e", arm="B", armseed=7)]
        ts = 0
        for b, rate in enumerate((400.0, 700.0, 1000.0, 1600.0, 2500.0, 3000.0)):
            bk = "%016x" % (b + 1)
            for i in range(6):
                for cfg_id in (1, 2):
                    step = int(round(60.0 * 500 / rate))
                    for k in range(6):
                        records.append(page(ts + k * step, cfg_id, bk=bk, sp=i, pg=k, chars=500))
                    ts += 6 * step + 100000
        result, _ = run_report(records, iters=2000)
        self.assertGreater(result["comparison"]["p"], 0.05,
                           "a pure book effect must not read as an arm effect")

    def test_chapter_length_alone_does_not_manufacture_an_arm_effect(self):
        # THE SECOND TEST THIS FILE EXISTS FOR, and the same shape as the book
        # effect above: one true rate, zero real difference, and the arms made
        # to differ in a nuisance variable that the washout is sensitive to.
        #
        # Here the nuisance is CHAPTER LENGTH -- A's chapters are 5 pages, B's
        # are 12 -- and the washout drops the first pages of each chapter. A
        # loses 3 of 5, B loses 3 of 12. Under the pre-2026-08-25 run_stats the
        # dropped pages left their wall-clock in the denominator, so A was
        # reported at ~40% of its true rate and B at ~75%, and the test below
        # found p=0.0002 on data containing no effect at all. Because the Phase
        # 2 randomizer switches arms AT chapter boundaries, that is not a
        # far-fetched confound: it is the design.
        #
        # Run at BOTH washouts. Passing only at 0 would mean the parameter still
        # decides the answer, which is the failure being pinned.
        records = [cfg(1, exp="e", arm="A", armseed=7), cfg(2, exp="e", arm="B", armseed=7)]
        ts = 0
        for b in range(6):
            bk = "%016x" % (b + 1)
            for i in range(6):
                for cfg_id, chapter_pages in ((1, 5), (2, 12)):
                    # 500 chars every 30 s is 1000 chars/min, in both arms.
                    for k in range(chapter_pages):
                        records.append(page(ts + k * 30, cfg_id, bk=bk, sp=i, pg=k, chars=500))
                    ts += chapter_pages * 30 + 100000
        for washout in (0, 3):
            result, _ = run_report(records, washout=washout, iters=2000)
            rates = [r["chars"] / r["minutes"] for r in result["runs"]]
            for rate in rates:
                self.assertAlmostEqual(rate, 1000.0, places=6,
                                       msg="washout %d moved a run's measured rate off its true one" % washout)
            self.assertAlmostEqual(result["comparison"]["observed"], 0.0, places=6,
                                   msg="washout %d invented an arm difference" % washout)
            self.assertGreater(result["comparison"]["p"], 0.05,
                               "chapter length alone must not read as an arm effect (washout %d)" % washout)

    def test_books_with_only_one_arm_are_dropped(self):
        # An unpaired book carries no information about the contrast, and
        # including it reintroduces exactly the between-book variance the
        # blocking removes.
        records = [cfg(1, exp="e", arm="A", armseed=7), cfg(2, exp="e", arm="B", armseed=7)]
        ts = 0
        for cfg_id, bk in ((1, "1" * 16), (2, "2" * 16)):
            for k in range(6):
                records.append(page(ts + k * 30, cfg_id, bk=bk, sp=0, pg=k))
            ts += 100000
        result, _ = run_report(records, iters=500)
        self.assertIsNone(result["comparison"], "with no book carrying both arms there is nothing to compare")

    def test_p_is_never_exactly_zero(self):
        # A permutation p of 0 is a lie: it means "no permutation was as
        # extreme", not "impossible". The add-one correction keeps it honest.
        records = self._arm_log(500.0, 5000.0)
        result, _ = run_report(records, iters=500)
        self.assertGreater(result["comparison"]["p"], 0.0)


class Reporting(unittest.TestCase):
    def test_a_phase_one_log_says_it_is_observational(self):
        records = [cfg(1)] + [page(i * 30, 1, pg=i) for i in range(6)]
        _, text = run_report(records)
        self.assertIn("observational", text)
        self.assertIn("what he chose, not what worked", text)

    def test_an_empty_log_does_not_crash(self):
        result, text = run_report([])
        self.assertEqual(result["runs"], [])
        self.assertIn("nothing to report", text)

    def test_prints_the_measured_spread_and_the_sample_size_it_implies(self):
        # The point of Phase 1: the power estimate in the doc is written against
        # an ASSUMED coefficient of variation, and this line replaces it with a
        # measured one the moment there is data.
        # Two runs at different rates, so there is a spread to measure. With a
        # single run the sd is 0 and the sample-size lines are correctly
        # withheld -- printing "0 runs per arm" off one observation would be the
        # most misleading line in the report.
        records = [cfg(1)]
        records += [page(i * 30, 1, sp=0, pg=i) for i in range(6)]
        records += [page(100000 + i * 60, 1, sp=1, pg=i) for i in range(6)]
        _, text = run_report(records)
        self.assertIn("run-level rate", text)
        self.assertIn("runs per arm", text)

        single = [cfg(1)] + [page(i * 30, 1, pg=i) for i in range(6)]
        _, one = run_report(single)
        self.assertIn("run-level rate", one)
        self.assertNotIn("runs per arm", one)


if __name__ == "__main__":
    unittest.main(verbosity=1)
