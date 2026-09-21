# The Albo process, reviewed — 2026-09-21

Owner: *"subagent to reflect and identify areas to improve on this entire
process. including bench pages and md files"*. A read-only agent reviewed
rounds ~291–341, the four standing docs, the three bench pages and the seven
gates. **Every headline claim below was re-verified in the main session before
this file was written**; where I did not re-verify, it says so.

## The finding that pays for the rest: a gate regression shipped

**VERIFIED here by building the parent commit**, not taken from the report:

| commit | italic 400 `--letters` rows |
|---|---|
| `bdd55a1` (round 296) | `b p` |
| **`36821a9` (round 297)** | **`b p y`** |
| HEAD | `b p y` |

Round 297 introduced a HAIR in the italic **`y`** at (195, 6), arms 18.60 /
2.24. Its own commit body says *"BoldItalic hairs 2 → 1, **every other font
unchanged**; counter dents and the collision sweep identical on every font."*
That is false for the Italic 400. `8ce01d5` then shipped *"Regular 400, Bold
700, Italic 400, BoldItalic 700 at round 297"* to TestFlight as **build 205** —
during the round where the owner had said *"Chase them to zero first"*.

Cost to have caught it: one 1.2 s build, one 0.4 s gate run, one diff.

## Ranked, with the fix

1. **A ladder is built and rendered before anything proves the dial is live —
   six times today.** The env prefix (`ALBO_G_OPEN_` vs `ALBO_G_`); `G_LRING`
   reaching dead code because the ring takes the pen; `LOOP_THIN_F` moving the
   wrong way; a ring→stem clip that removed nothing; `ALBO_ALD_G_NECK_W`
   reported dead when it was only unselected; an enclosed-area measure that is
   undefined on an open curve. **One failure in six coats**, and the symptom is
   always a flat response across the rungs.
   *Fix:* `tools/wedge_serif/ladder.py` — takes `(env, rungs, measure)` and
   REFUSES to render when rung 1 equals rung N. Catches five outright and the
   sixth by printing the direction.
2. **No gate runner, no baseline.** All seven gates exit non-zero on the
   shipping font; the `VI`/`ff`/`fT` set is genuinely pre-existing and accepted
   *in prose*, not in `cmp_touch.py`'s own exemption table. So "clean" has
   drifted to mean "my glyph raises no row" in some commits and "the same rows
   as before" in others, and a reader cannot tell which. Of today's 29 albo
   commits **only `cmp_contour_hairs` was run** — `cmp_touch` zero times, in a
   day that changed the roman g's advance by 23 units.
   *Fix:* `gates.sh` + a tracked `gates-baseline.json`; exit non-zero only on a
   DELTA; `--accept` makes accepting a finding a reviewable commit. The
   precedent and its rationale are already written — `tests/run_all.sh` is "the
   CATALOG, not just the runner". The Albo toolchain has zero presence there.
3. **A new session asking "what is the g now?" gets the wrong answer twice**
   from this repo's own index — `albo-g-anatomy.md` is titled "The binocular g"
   and the roman is not binocular since round 335; `wedge-serif-exploration.md`'s
   STATE says `ALBO_G_STYLE` defaults to `bent` and the code says `open`. The
   two docs that hold the truth are not in `CLAUDE.md`'s table at all.
   *Fix:* a GENERATED `docs/albo-STATE.md` read from the builders' own
   `os.environ.get(..., default)` values. A generated state file cannot go
   stale about the thing it generates.
4. **The record is append-only; corrections do not reach the claim.** Docs
   gained 1,823 lines today and lost 3. In one file a bolded conclusion at line
   60 is retracted at line 112 — and left bolded, under its original heading.
   `grep -c "SUPERSEDED"` over the four main docs: 0, 0, 0, 0.
   *Fix:* edit the earlier claim in place; keep the wrong number visible, never
   leave it asserted.
5. **The instruments that decided shipped geometry live in a temp directory.**
   Nineteen `scratchpad/...` paths are cited as if they were locations. The
   shipping roman g's tail is literally the output of `tailtrace.py`, which is
   not in the repo. `albo-method.md`'s central rule — *"a surprising number is
   the instrument until proven otherwise"* — cannot be executed against an
   instrument that no longer exists.
6. **A ruling made on an explicit ladder does not transfer to the ship build**
   (round 336: shipped `j`, every ruling made on `futura`).
   *Fix:* `approved.json` mapping glyph → outline hash + the owner's quote, and
   `cmp_outlines.py` — which does not exist, though 8 commit bodies today cite
   "0 of 493 glyph outlines differ" from a re-typed snippet.
7. **Every measure that misled was a low-dimensional proxy for a shape** —
   two sample points for a ring's contrast, a row's ink for a flat connector,
   the deepest row's ink called a "tip". Every measure that held consumes the
   whole object: the per-angle sweep, every vertex, all 5,193 pairs, all
   2,007,794 pairs. *Rule to add:* a measure that reduces a curve to fewer than
   ~20 samples must be laddered to prove it responds. Today's bad numbers were
   all **unsurprising** ones — 50/54 looks like a reasonable pair of stroke
   widths, which is why it survived.
8. **A measured optimum with no floor.** Round 338 drove the italic loop's thin
   to 12 units under a known 28-unit hairline; the owner found it by eye one
   round later. The floor is a number applied from memory, not a gate.
9. **The bench pages divide on two axes, and neither is stated on the page.**
   The 396-row spacing bench used the Artifact **db** and 329 judgments came
   back as auditable data; the counter and editor benches use copy-paste, which
   ceilings at a handful of values. And a LADDER page shows PNGs from the real
   built font, where a MODELLING bench draws its own approximation — the
   editor let the owner dial `DIVE` to 1.10 against a control that saturates
   past 0.7 in the build. *Fix:* say which kind the page is, on the page; and
   round-trip the bench's extremes through a real build before publishing.
   The `fill-rule` finding (a counter is a hole only inside ONE path) lives in
   a comment in a file that will be deleted, and in no repo doc.

## What is working and must not change

The reasoning is the strong half; nearly every finding above is plumbing
around it. Verified over today's 29 albo commits: **27 carry the owner's
verbatim words**, **17 record an explicit negative result**, **8 cite an
outline diff**, and two open by retracting a claim made to him an hour earlier.
Round 331 — rebuilding the letter instead of adjusting its parts — made three
separately-dialled quantities fall out of the construction. Round 328 — trace
before you dial — found what no ladder would have. The subagent guard worked:
`782b0e5` verified the open-g agent's ten arms rather than trusting them, and
caught one column that does not reproduce.

## All five are built (same day)

Owner ruled "all five". Each was validated against a failure it was written for:

| | validated by |
|---|---|
| `ladder.py` | LIVE on `ALBO_ALD_G_LOOP_PHI`; **FLAT on `G_LRING`** (dead code) and **FLAT on `ALBO_G_QS_STEM_W`** (today's wrong-prefix bug) |
| `gates.sh` + `gates-baseline.txt` | passes against HEAD; edit the baseline's italic row to round 296's `b p` and it prints exactly the `+b p y` diff that would have stopped build 205 |
| `gen_state.py` → `docs/albo-STATE.md` | reads `ALBO_G_STYLE = open`, `ALBO_G_OPEN = futura`, `ALBO_ALD_G_STYLE = cursive` — the three the prose docs had wrong |
| `approved.py` + `approved.json` | the roman and italic g are recorded with the owner's own words; pointed at round 335's build it reports **`Regular:g CHANGED`**, which is round 336 caught retroactively |
| `instruments/` | `tailtrace.py`, `sansg.py`, `loopwall.py`, `gtrace.py`, `contrast.py`, `counter-bench.html` moved in with a README saying why |

`gates.sh` runs the approved-glyph check too, so a build that is gate-identical
but draws a letter nobody ruled on still fails.
