# The composition test, and what it found — 2026-08-29

`docs/surface-roadmap.md` section 8 asked for a test that pins every surface
dial to its maximum simultaneously, for every shipped palette, and asserts the
7:1 floor still holds through the real budget-sharing chain rather than
through each pass's own isolated proof. `tests/composition_test.cpp` is that
test, wired into `tests/run_all.sh` as `composition`.

**It found a real gap, on the first run, with no code changed to produce it.**
Per the owner's standing rule ("if the test fails, stop, do not weaken the
assertion, report it"), the assertion was left as written — the test is wired
in and reports FAIL until this is decided.

## The finding

`lightink::paperWorstDrift` — the sheet-to-sheet drift model
(`src/LightInkPalette.h` ~633) — darkens the paper by a fixed ±2 code values
per channel at `driftPct=100` (`kPaperDriftCodeValuesAt100 = 2`,
`kPaperDriftMax = 100`), completely independent of how much headroom the live
palette has. Unlike every other surface pass in this repo (letterpress's
tooth, the laid wires, show-through, the defect marks), **drift carries no
`paperBudget`-aware clamp of its own.**

That is safe for the picker's own ink/paper/density model, because
`lightink::floorDensityPct` / `clampDensityPct` are drift-aware: they choose
the ink density (or clamp the paper-strength dial) so that the DARKEST
drifted leaf still clears 7:1 — proven exhaustively by
`tests/light_ink_test.cpp`'s "frozen sheet" sweep, and it is what
`frozenpage::lightSelection()` (`src/FrozenPage.h` ~116-131) actually leans on
for the one page the shipped app renders (Sanguine ink on India paper, density
and paper-strength both run through those same clamps with `drift =
kPaperDriftMax`).

It is **not** safe for a **named preset** selected directly — Latte, Sepia,
etc. — because a preset's ink and paper are fixed bytes from
`panelpalette::resolve()`, never routed through the density/strength clamps
that make drift safe for the picker path. Latte is `testpalettes::kLightLatte`
(`tests/TestPalettes.h` ~89), the tightest page this repo ships at **7.06:1**
undrifted (`ink 4C4F69`, `paper EFF1F5`). At drift 100 the darkest leaf is
`EDEFF3` (every channel −2), and the composition test measures the resulting
ratio at **6.937:1** — under the 7:1 floor, with the -0.05 tolerance every
other floor test in this repo uses (`6.937 < 6.95`). This happens with
**every other surface dial contributing exactly zero** — `letterpress::
paperBudget(inkLum, driftedPaperLum)` correctly returns `0.0` once the pair is
already below the floor, so the tooth, the wires, show-through and the
defects all correctly spend nothing further. The breach is drift alone.

Verified by hand outside the test harness too (`/tmp/latte_probe.cpp`,
discarded): `panelpalette::resolve(kPresetLatte, false, -1, -1)` resolves to
`ink 4C4F69 / paper EFF1F5`; `lightink::paperWorstDrift(paper, 100, leaf)`
gives `EDEFF3`.

## Is this reachable in the shipped app?

**Not on iOS as it ships today.** The light page is frozen to Sanguine-on-India
(`docs/surface-roadmap.md`'s 2026-08-24 ruling); the 52 named presets are
"still intact... unreachable" per that same doc, and the frozen page's own
selection already goes through the drift-aware density clamp described above.

**It is reachable on the desktop**, where preset selection
(`settings.json`'s `panelPalettePreset`, or `CROSSPOINT_SIM_*` presets) and
`paperDriftPercent` / `CROSSPOINT_SIM_PAPER_DRIFT` are two independent knobs
with no cross-check between them. Setting drift to 100 with Latte selected —
both legitimate, separately-documented desktop QA levers — renders a page
under the floor with nothing to catch it.

## What was NOT done

No production code was touched to fix this — the task that produced this test
was scoped to writing the test, not to fixing what it finds, and "touch only
what the ask named" applies. Candidate fixes, not evaluated for cost here:

1. Give `paperWorstDrift` (or its caller) the same `paperBudget`-style clamp
   every other pass has, scaling the drift bound down when the live pair is
   already tight.
2. Gate drift off (or cap its bound) for a NAMED PRESET specifically, since
   the picker path already has its own protection and only the direct-preset
   path is exposed.
3. Leave it: it is not reachable on iOS today, and the desktop combination
   requires deliberately setting two QA-only dials against each other.

This is the owner's call, not mine to make silently — flagged here per "no
invented rationale" and "architectural choices go to the owner before
building."

## Where this left `tests/run_all.sh`, before the fix below

`composition` was wired in and reported **1 failure** (the Latte case above)
out of its light-mode sweep; the dark-mode sweep (scanlines, the only
dark-mode doctrine field, with grain and letterpress left pinned) was clean
across all five dark palettes and three pitches. Every other passing test in
that suite was unaffected — a new failure surfaced by new coverage, not a
regression in anything that session touched. Superseded by the next section —
see there for the current tally.

## The ruling, and what landed — 2026-08-29 (same day, later)

**Owner's ruling, verbatim intent, choosing from the three candidates above:
"Clamp drift like every other pass."** Option 1. Not option 2 (a named-preset
special case) and not option 3 (leave it) — the invariant is restored
everywhere, not patched around one reachable path.

**What was found on reading the three reference passes first, before writing
anything:** `letterpress::paperBudget(inkLum, paperLum)` and
`phosphorgrain::darkeningBudget(inkLum, paperLum)` (`src/Letterpress.h:194`,
`src/PhosphorGrain.h:207`) both express their budget as a MULTIPLIER on
luminance, because both passes darken a texel by scaling its intensity
uniformly — physically honest for them. Sheet drift does not do that: it is a
fixed per-channel BYTE offset applied in sRGB space
(`lightink::applyPaperDrift`), so a code value's effect on luminance depends on
which channel and where that channel starts, not on one multiplier. Borrowing
`paperBudget`'s `m` and translating it into a code-value count would be an
approximation — and this file's OWN doctrine already rejects exactly that kind
of approximation for its other two clamps: `floorDensityPct` and
`maxPaperStrengthPct` are explicitly "found by SCAN rather than by inverting
the formula... which makes the guarantee exact instead of approximate"
(`src/LightInkPalette.h`, the comment above those two functions). So the fix
applies the SAME doctrine — "clamp this pass's own effect to what the live
pair can afford" — through the SAME mechanism this file already uses
elsewhere (a scan for the exact boundary), rather than importing a different
pass's approximate multiplicative shape. This is not a second budget
mechanism; it is the one doctrine, expressed in the units drift already ships
in.

**What landed**, all in `src/LightInkPalette.h` unless noted:

- `driftBoundForPair(ink, paper, rawBound)` — new. Scans the candidate bound
  `b` from 0 up to `rawBound` (0..2 at the dial's own maximum) and returns the
  last `b` for which `contrastRatio(ink, paper-drifted-by-b-every-channel) >=`
  the 7:1 floor. Monotone non-increasing in `b` for the same reason
  `paperWorstDrift`'s own header comment already gives for the all-negative
  corner being the minimum, so the first failure IS the ceiling — the same
  "scan up, stop at first failure" shape `maxPaperStrengthPct` uses.
- `paperWorstDriftForPair(ink, paper, driftPct, out)` — new. `paperWorstDrift`'s
  twin for a pair that never passed through the density/strength clamps: calls
  `driftBoundForPair` and applies that (possibly smaller) bound instead of the
  raw one.
- `paperDriftedForPair(ink, paper, seed, driftPct, out)` — new. `paperDrifted`'s
  twin for the actual per-leaf RENDER: same budget-clamped bound, same random
  draw (`paperDriftOffsetsWithBound`, factored out of the existing
  `paperDriftOffsets` so the draw itself is byte-identical either way — only
  the bound it is drawn within can shrink).
- `paperWorstDrift`, `paperDriftOffsets`, `maxDriftCodeValues`, and every
  picker-path consumer (`contrastAtDensity`, `floorDensityPct`,
  `clampDensityPct`, `maxPaperStrengthPct`, `clampPaperStrengthPct`) are
  UNCHANGED, deliberately. Those four functions already re-derive density and
  paper strength against `paperWorstDrift`'s raw, unclamped worst case, which
  is what makes the picker's own pages — the shipped frozen page included —
  safe with no further change (see "Is this reachable" above). Adding a second
  clamp inside `paperWorstDrift` itself would have corrupted the "darkest leaf
  is the all-negative one" property `tests/light_ink_test.cpp`'s box sweep
  (lines ~979-1009) depends on `paperWorstDrift` reporting the RAW reachable
  minimum, not a budget-clamped one — that sweep asserts every one of the 125
  reachable corners is no darker than what `paperWorstDrift` reports, which
  would be trivially false against a bound that had already been clamped
  smaller than the dial's own maximum.
- `src/HalDisplay.cpp`'s `livePanelPalette` (~2483-2489) now calls
  `lightink::paperDriftedForPair(pal.ink, pal.paper, pageSheetSeed(), driftPct,
  out.paper)` instead of `lightink::paperDrifted(pal.paper, ...)` — the actual
  render path a NAMED PRESET's raw bytes reach, which is exactly the
  reachable gap this file's "Is this reachable" section named.
- `tests/composition_test.cpp`'s Latte case now calls
  `lightink::paperWorstDriftForPair(inkBytes, paperBytes, kPaperDriftMax,
  leaf)` instead of `lightink::paperWorstDrift(paperBytes, kPaperDriftMax,
  leaf)` — testing the exact bound production now renders for a directly
  selected preset, not the raw dial maximum. The 7:1 assertion itself is
  UNCHANGED; only the input that feeds it was corrected to match the fixed
  code path.

**The shipped page proof, computed rather than assumed** (the hard
constraint). Both tables computed with `wcag::kContrastFloorAAA = 7.0`
exactly (`src/ContrastFloor.h:28`) and this repo's standing sRGB relative-
luminance arithmetic, reproduced outside the harness in Python and cross-
checked against the doc's own earlier-measured figures (matches to 3 decimal
places).

Sanguine `5C332B` on India `F9F3E9`, per candidate bound `b`:

| `b` | drifted paper | contrast |
|---|---|---|
| 0 | `F9F3E9` | 9.689:1 |
| 1 | `F8F2E8` | 9.604:1 |
| 2 | `F7F1E7` | 9.519:1 |

Every candidate clears 7:1, so `driftBoundForPair` returns the last one
scanned: **2 — the SAME raw bound `maxDriftCodeValues(100)` already
returned.** Before the fix: bound 2, leaf `F7F1E7`, 9.519:1. After the fix:
bound 2 (unchanged), leaf `F7F1E7` (unchanged), 9.519:1 (unchanged).
Byte-identical, because the pair has headroom to spare — the frozen page
never gets near its own clamp.

Latte, for contrast — the case that motivated the fix, worked through the
same table so the difference is visible rather than asserted:

| `b` | drifted paper | contrast |
|---|---|---|
| 0 | `EFF1F5` | 7.062:1 |
| 1 | `EEF0F4` | **6.999:1 — fails** |
| 2 | `EDEFF3` | 6.937:1 |

`b=1` already falls a hair under 7.0, so `driftBoundForPair` stops there and
returns the LAST PASSING value: **0.** For Latte specifically, the fix does
not shrink the drift bound — it disables drift entirely (every leaf renders
the nominal, undrifted paper). That is a real behavior change for anyone who
has Latte selected on the desktop with drift turned up, and it is the correct
one: a 7.06:1 page has essentially no room to darken further and stay legible,
which is exactly what "clamp drift like every other pass" means for a pair
this tight.

**`tests/run_all.sh`: 69 passed, 0 skipped, 0 failed** (measured 2026-08-29,
after the fix above; `composition` and `light_ink` both PASS). That count will
drift as tests are added, so trust a fresh run over this line if it looks
stale.

`tests/light_ink_test.cpp`'s "frozen sheet" sweep was re-run specifically per
the owner's ask, standalone (`c++ -std=c++17 -O1 -Isrc -Iios -o light_ink
tests/light_ink_test.cpp`), and **DID NOT move**: `git diff
src/LightInkPalette.h` shows the change is purely additive (three new
functions plus a mechanical extraction of `paperDriftOffsets`'s body into
`paperDriftOffsetsWithBound`, called with the SAME `maxDriftCodeValues
(driftPct)` bound it always used) — `paperWorstDrift`, `contrastAtDensity`,
`floorDensityPct`, `clampPaperStrengthPct`, `washOnGround` and
`paperAtStrength`, every function the frozen-sheet sweep actually calls, are
byte-for-byte unedited, so its result cannot have moved because of this fix.
Measured worst figures this run: **model 7.001:1 (Verdigris on Kozo),
textured 6.999:1 (Standard on India)**. The textured figure reads 0.001 lower
than the "7.000:1" `docs/light-ink-picker.md`'s own §8 recorded on
2026-08-23 for the same 64×64 grid — but that same paragraph already flags
the 64×64 measurement as an approximation of a value that "converges to
7.0000 ± 0.0002 at 512×512", so a ~0.001 read at the smaller grid is within
what that doc already expected, not a new discrepancy. Re-running the
UNMODIFIED code path (confirmed by the `git diff` above: nothing this sweep
calls was edited) reproduces 6.999:1 deterministically — it did not move
because of this fix, and it was not re-measured at 512×512 to chase a
difference this small.
