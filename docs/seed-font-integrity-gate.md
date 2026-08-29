# The seed-font integrity gate

*Written 2026-08-26 against this working tree and firmware `b955029bc`. Every
number below is measured out of a shipped `.cpfont` header; nothing is derived.*

## What it refuses, and why nothing else could

**The class: a `.cpfont` in the shipping tree whose actual rendered size does
not match the size its filename claims.**

On 2026-08-26 `InknutJunicode` shipped to TestFlight with its L slot drawing at
half size — every letter separated by a gap, obvious to the owner in one glance.
`build/seedfonts/InknutJunicode/2x/InknutJunicode_14.cpfont` held a **14 ppem**
render where a 28 ppem one belonged: the 2x cut of the **7 pt** slot, left under
the wrong name by a hi-res build that aborted before it could rename its
outputs. `2 × 7 = 14`, and 14 pt is itself a slot in that ramp, so the orphan
landed on exactly the path `SdCardFontManager::hiResCompanionPath` looks for and
**loaded with no error anywhere**. The advance grid comes from the 1x file and
the ink from the companion, so the spacing was right and the ink filled half of
it. Full account, with the per-character fill measurements:
`crosspoint-reader/docs/inknut-l-slot-2026-08-26.md` (B-039).

**Every gate we had passed that build.** The host suites passed, the ESP32 build
passed, `ios/testflight.sh`'s own five checks passed, the app launched and
rendered. A human looking at a page was the only thing that caught it — and this
is the second time a wrong-but-loadable data file has shipped past a full green
board, after build 126's three unreachable iA Writer families
(`docs/ios-app-size.md` A1).

The reason no code gate can see it is that **nothing about the failure is in the
code**. The renderer is right, the loader is right, the format is right; one
file's bytes belong to a different point size. So the gate has to look at the
data, and it can, cheaply: every number it needs is in the file's own 32-byte
global header and 32-byte-per-style TOC
(`crosspoint-reader/docs/cpfont-format.md` §2.2–2.3). No rasterizer, no
rendering, **0.11 s for the whole eight-family tree**.

## Where it lives, and why there

`tools/validate_seed_fonts.py` — in **this** repo, not the firmware's.

The firmware repo owns the *producer* and already got the producer-side fix on
the same day: `rename_to_slot_names()` returns a reason instead of `None`, and a
failed `build_family` deletes exactly what it created. What was missing is a
gate on the *artifact that ships*, and the artifact is `build/seedfonts`, which
this repo's CMake bundles and this repo's script deploys. A validator in the
firmware repo would be a consumer check parked in the producer.

It runs in **two** places, and both are deliberate:

| Where | Why |
|---|---|
| `ios/CMakeLists.txt`, configure time, immediately before the CPZ1 compression pass | The un-skippable copy. It is the only place that knows which tree is actually being bundled, and **every** iOS build configures — the deploy, CI, a local device build. It also fails in a tenth of a second rather than after the ~40 s spent packing files that must not ship. |
| `ios/testflight.sh`, as a named `Verify seed fonts` section before Configure | The deploy pipes cmake's stdout to `/dev/null`, so the configure copy's verdict would be **invisible** on the one path that matters. A gate whose result nobody sees is the thing this repo keeps re-learning (`say "Source set freshness"` carries the same note). It also fails at the top of the deploy instead of a minute in. |

It is deliberately **not** in `tests/run_all.sh` pointed at the real tree:
`build/seedfonts` is gitignored and machine-local, so a green run on one
developer's box proves nothing about anyone else's — the same trap already
recorded for the yaml gate. What *is* in `run_all.sh` is
`tests/validate_seed_fonts_test.py`, which synthesises header-only fixtures in a
temp directory and asserts, per check, that a planted fault is rejected **and**
that the same tree without it passes. That second half matters: a validator that
rejected everything would otherwise score full marks. 22 cases, no firmware
checkout needed.

There is **no override flag**. A wrong-size `.cpfont` renders successfully and
looks broken.

## The eight checks

| | Check | What it is for |
|---|---|---|
| A | header — magic, version 4, styleCount 1–4, TOC parses, styleIds unique | A truncated, half-written or entirely wrong file under a `.cpfont` name. The reader rejects these loudly anyway, so this is the floor, not the point. |
| B | filename is `<Family>_<int>.cpfont` with the prefix equal to the directory | A file from another family copied into the wrong tree. `SdCardFontRegistry` takes the family from the **directory**, so it would load as this family's slot. |
| C | the 1x slot set equals `sd-fonts.yaml`'s `sizes:` for that family | Makes the tree answerable to the **recipe** rather than merely self-consistent. Catches a stale ramp, an orphan filename, and a slot that never built. |
| D | every shipped hi-res tier carries exactly the 1x slot set | A missing companion degrades **silently** to 1x-replicated; an orphan companion is B-039. Independent of C, so it still bites with no recipe. |
| E | `advanceY` strictly ascends with point size, per style, per tier | A non-monotonic ramp is two files swapped. |
| **F** | `\|advanceY_T − T·advanceY_1x\| ≤ 1 + T`, and the same for `ascender` and `descender` | **The one that catches B-039.** The broken file read 45 where 90 was required, against a tolerance of 3. |
| G | the tier carries the same styleIds as its 1x base | A companion missing italic renders italic 1x-replicated while its siblings do not. |
| H | `0.99 ≤ tier glyphCount / 1x glyphCount ≤ 1.0`, per style | A tier built from an older, narrower charset. Right scale, stale charset — F cannot see it. The bundle carried three 2x files with 1094 glyphs against the 1x set's 2693, so ~1600 codepoints rendered 1x-replicated at those slots. The 1.0 ceiling is not slack: a tier covering **more** than its base was built from a different recipe. |

**Not checked, deliberately:** the interval table's internal layout, the glyph
table, the bitmap section. `SdCardFont` validates all three at load and fails
loudly (`cpfont-format.md` §2.5), so a second copy here would be a second
definition to drift. This gate exists for the failures that load **cleanly**.

## Where check F's tolerance comes from

`advanceY`, `ascender` and `descender` are whole-pixel integers, so a tier's
value is `round(T · exact)` against a base of `round(exact)`. The ideal bound is
`0.5 + T·0.5` — 1.5 at 2x — and hinting at a different ppem adds a little.

**Measured across all eight shipped families, both tiers, all four styles
(2026-08-26): the worst real deviation is 1**, in each of the three fields.

| Field | Worst | Where |
|---|---|---|
| `advanceY` | 1 | `Almendra/2x/Almendra_10.cpfont` — 57 against 2 × 29 |
| `ascender` | 1 | `Almendra/2x/Almendra_12.cpfont` — 51 against 2 × 26 |
| `descender` | 1 | `Almendra/2x/Almendra_10.cpfont` — −15 against 2 × −8 |

Expressed as the ratio the earlier audit used, that is **1.957 – 2.045** at 2x
and **2.970 – 3.029** at 3x.

The tolerance is `1 + T` — **3 px at 2x, 4 px at 3x**. Below it, three times the
worst real rounding. Above it, the *tightest fault it must still separate* is a
one-slot mixup in the closest ramp any installed family has (TeX Gyre Heros,
11 pt `advanceY` 35 against 12 pt's 39), which is 7 — a little under twice the
tolerance. B-039 itself is 45.

## Fault injection, 2026-08-26

Against the real tree at `build/seedfonts`, 124 files, restored and verified
byte-for-byte afterwards (`shasum -a 256` over all 124, identical).

| Fault | Planted how | Verdict |
|---|---|---|
| **B-039 verbatim** | `cp InknutJunicode/2x/InknutJunicode_7.cpfont InknutJunicode/2x/InknutJunicode_14.cpfont` | REJECTED, exit 1. F: *"THIS FILE IS NOT A 2x RENDER OF 14 pt. styles 0,1,2,3 advance_y 45 where a 2x cut needs ~90 (1x reads 45; ratio 1.000, not 2.000)"* — plus ascender, descender, and E on the same file. |
| Missing slot | delete `InknutJunicode/2x/InknutJunicode_9.cpfont` | REJECTED. D, naming the file and saying the slot would render 1x-replicated and silent. |
| Orphan name | `cp .../_16.cpfont .../InknutJunicode_28.cpfont` (one of the four the aborted build really left) | REJECTED. D + E. |
| Stale 1x ramp | rename `Almendra_18` → `Almendra_17` | REJECTED. C, naming both the missing and the orphan file, plus D on both tiers. |
| Clean tree | — | PASS, exit 0, 8 families, 1x + 2x, 0.11 s. |

The same run against the simulator's **card**
(`crosspoint-reader/fs_/fonts/`) independently rediscovered the one real defect
that was already known and owed, and only that one:

```
FAIL  .../fs_/fonts/Almendra: 1x ramp is [6, 8, 10, 12, 14, 17], the recipe
      says [8, 10, 12, 14, 16, 18] -- missing Almendra_16.cpfont,
      Almendra_18.cpfont; orphan Almendra_6.cpfont, Almendra_17.cpfont.
```

Seven of the eight families on the card were clean.

## Tiers above the ceiling are skipped, not passed

`--max-tier` is the bundling ceiling (`CROSSPOINT_IOS_RENDER_SCALE`, 2 today).
A tier above it is reported as *skipped*, never as passed — at ceiling 2 that is
every `3x/` tree, and those are known to carry the pre-`reading` charset (1094
glyphs against 2693). They are excluded from the bundle rather than deleted,
since rebuilding one is a ~40 minute rasterisation run, so checking them would
fail H for a tier nothing ships. Raising the ceiling starts judging them, which
is exactly right: re-enabling 3x is one number in `ios/CMakeLists.txt`, and this
gate would then refuse to ship the stale trees.

## Running it by hand

```bash
python3 tools/validate_seed_fonts.py build/seedfonts \
  --recipe ~/src/crosspoint-reader/lib/EpdFont/scripts/sd-fonts.yaml \
  --max-tier 2
```

Works on any tree of this shape — the card at `crosspoint-reader/fs_/fonts/` is
the other one. It reads CPZ1 containers transparently (inflating block 0 only),
so a bundled or installed tree can be audited without unpacking it.

## A second gate: what the app BUNDLES, not just what a file claims (2026-08-28)

The gate above validates the CONTENT of a `.cpfont` — that its header renders at
the size its filename claims. It says nothing about **which files reach the
app**, and that turned out to be a separate, shipped defect.

### What happened

Inknut's ramp was re-fitted from `7 9 11 12 14 16` to `8 10 12 14 16 18` and the
seed tree was rebuilt correctly: `build/seedfonts/InknutJunicode/` held exactly
six files at 1x and six at 2x, and `validate_seed_fonts.py` passed.

Build 159 shipped **nine**: `7 8 9 10 11 12 14 16 18`, at both tiers. Verified
in the archive itself —

```
$ find build/CrossPointX3.xcarchive/Products/Applications/CrossPointX3.app/SeedFonts/InknutJunicode -name '*.cpfont' | wc -l
      18      # 9 at 1x + 9 at 2x
```

The owner deleted the three orphans from the app's fonts folder and reported
they came back: *"7 9 11 are being regenerated after i delete them"*. They were.
`seedOneFontDirectory()` copies the bundle onto the card at every launch, so a
file in the bundle cannot be deleted by hand — the app is doing its job, and the
bundle was wrong.

### Cause

`file(GLOB)` in `ios/CMakeLists.txt`. A glob is evaluated when CMake
**configures**, and its result is baked into the generated Xcode project. The
seed tree changing on disk does not re-run it. So the project went on listing the
file set from whenever configure last happened to run, and a rebuilt ramp shipped
alongside the ramp it replaced.

This is worse than it sounds because both ramps are *valid* files. Every
content-level check passes: the headers are right, the companions are present,
the charsets are current. The integrity gate had nothing to object to. The defect
is only visible as a SET — nine installed sizes against six slot names, so size
stepping walks files the slot table cannot name.

### Fix, in two parts

1. **`CONFIGURE_DEPENDS` on all three seed-font globs.** The build system
   re-checks the glob and re-configures when the set changes. Costs a directory
   stat per build.
2. **A set comparison in `ios/testflight.sh`**, after Archive and before upload:
   the archived app's `.cpfont` set must equal the seed tree's, minus `3x`
   (built but deliberately not bundled — render scale is frozen at 2). It is a
   set comparison and not a count, because a count matches when one file is
   swapped for another. On mismatch it prints both directions of the diff and
   names the fix (`rm -rf` the build dir).

Part 2 exists because part 1 is invisible when it fails. `CONFIGURE_DEPENDS`
working is indistinguishable from `CONFIGURE_DEPENDS` not working until someone
lists a bundle by hand, which is the shape of every defect this repo has had to
put a gate in front of.

**The gate was mutation-tested against the build 159 archive**, which it refuses,
naming all six orphans. A gate that has never rejected a real bad input is a
guess.

### Blast radius, checked rather than assumed

The shipped bundle was diffed against the whole seed tree, all families:

```
shipped=102  tree=123 (123 includes 21 3x files that are not bundled)
in SHIPPED but not in tree:  the 6 Inknut orphans, and nothing else
in TREE but not shipped:     nothing
```

So Inknut was the only family affected, because it was the only family whose
ramp moved. Every other family's set was already correct and stays correct.

### What this does NOT fix

An install that already has the nine files. It self-heals on the next launch:
`seedOneFontDirectory()`'s prune pass deletes any file in a bundled family's
directory that the bundle does not carry, so build 160 removes 7/9/11 from the
card without the owner touching anything. That prune only runs when
`cloneFontDirectory()` declines — which it does whenever the destination is a
real directory, i.e. on every upgrade.
