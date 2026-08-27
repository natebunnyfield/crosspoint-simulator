#!/usr/bin/env python3
"""Prove tools/validate_seed_fonts.py still fails the things it claims to fail.

A gate that has quietly become a no-op is worse than no gate: it prints OK and
everyone downstream believes it. That is not hypothetical here -- the deploy's
device-profile guard passed the broken build it was written for, because it
regex'd every GCC_PREPROCESSOR_DEFINITIONS block and could not tell which
target one belonged to (ios/testflight.sh). So each check gets a fixture that
is healthy except for one planted fault, and the test asserts BOTH that the
fault is rejected AND that the identical tree without it passes -- otherwise a
validator that rejected everything would score full marks.

Every fixture is synthesised in a temp directory: no firmware checkout, no
seed-font tree, no machine-local state. That is the point. The real tree lives
in build/seedfonts, which is gitignored and different on every machine, so a
test over it would prove nothing about anyone else's -- the trap already
recorded for the yaml gate. This test proves the INSTRUMENT; the deploy gate
(ios/testflight.sh) and the configure gate (ios/CMakeLists.txt) are what point
it at the tree that ships.
"""

import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import validate_seed_fonts as V  # noqa: E402

FAILS = 0


def write_font(path: Path, *, advance_y, ascender, descender, glyphs,
               styles=(0, 1, 2, 3), version=4, flags=1, magic=V.CPFONT_MAGIC):
    """A header-only .cpfont. The validator reads nothing past the style TOC."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = bytearray()
    out += magic
    out += struct.pack("<HHB", version, flags, len(styles))
    out += bytes(19)
    for sid in styles:
        e = bytearray(32)
        e[0] = sid
        struct.pack_into("<II", e, 4, 40, glyphs)       # intervalCount, glyphCount
        e[12] = advance_y
        struct.pack_into("<hh", e, 13, ascender, descender)
        struct.pack_into("<I", e, 24, 32 + 32 * len(styles))  # dataOffset
        out += e
    path.write_bytes(bytes(out))


# One family, six slots, a 2x tier -- the shape every installed family has.
# advanceY runs 23/29/32/39/45/51, which is InknutJunicode's real 1x ramp.
RAMP = {7: (23, 18, -5), 9: (29, 23, -7), 10: (32, 26, -8),
        12: (39, 31, -9), 14: (45, 36, -10), 16: (51, 41, -12)}
GLYPHS = 2693


def build_tree(root: Path, family="Fam"):
    fam = root / family
    for pt, (a, asc, desc) in RAMP.items():
        write_font(fam / f"{family}_{pt}.cpfont",
                   advance_y=a, ascender=asc, descender=desc, glyphs=GLYPHS)
        write_font(fam / "2x" / f"{family}_{pt}.cpfont",
                   advance_y=2 * a, ascender=2 * asc, descender=2 * desc,
                   glyphs=GLYPHS)
    return fam


def run(root: Path, recipe: Path | None = None, max_tier=2):
    problems, _notes, _fams = V.validate(root, recipe, max_tier)
    return problems


def case(name, mutate, *, expect_substrings, recipe_sizes=None):
    """Healthy tree must pass; the same tree with `mutate` applied must fail."""
    global FAILS
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fam = build_tree(root)
        recipe = None
        if recipe_sizes is not None:
            recipe = root / "sd-fonts.yaml"
            recipe.write_text(
                "installed_families:\n  - Fam\nfamilies:\n"
                f"  - name: Fam\n    sizes: [{', '.join(map(str, recipe_sizes))}]\n"
            )
        clean = run(root, recipe)
        if clean:
            print(f"FAIL {name}: the UNMUTATED tree was rejected -- "
                  f"the fixture or the validator is wrong:\n    " +
                  "\n    ".join(clean))
            FAILS += 1
            return
        mutate(fam)
        problems = run(root, recipe)
        if not problems:
            print(f"FAIL {name}: the planted fault was ACCEPTED. This check is a no-op.")
            FAILS += 1
            return
        blob = "\n".join(problems)
        for want in expect_substrings:
            if want not in blob:
                print(f"FAIL {name}: rejected, but the message never says {want!r}:\n"
                      f"    " + blob.replace("\n", "\n    "))
                FAILS += 1
                return
        print(f"ok   {name}")


# --- A: header ------------------------------------------------------------
case("A magic", lambda fam: write_font(
        fam / "2x" / "Fam_14.cpfont", advance_y=90, ascender=72, descender=-20,
        glyphs=GLYPHS, magic=b"NOTAFONT"),
     expect_substrings=["Fam_14.cpfont", "bad magic"])

case("A version", lambda fam: write_font(
        fam / "2x" / "Fam_14.cpfont", advance_y=90, ascender=72, descender=-20,
        glyphs=GLYPHS, version=5),
     expect_substrings=["Fam_14.cpfont", "version 5"])

case("A truncated", lambda fam: (fam / "2x" / "Fam_14.cpfont").write_bytes(
        (fam / "2x" / "Fam_14.cpfont").read_bytes()[:40]),
     expect_substrings=["Fam_14.cpfont", "style TOC needs"])

# --- B: filename ----------------------------------------------------------
case("B foreign family", lambda fam: write_font(
        fam / "2x" / "Other_14.cpfont", advance_y=90, ascender=72,
        descender=-20, glyphs=GLYPHS),
     expect_substrings=["Other_14.cpfont", "names family"])

case("B unparseable name", lambda fam: write_font(
        fam / "2x" / "Fam-fourteen.cpfont", advance_y=90, ascender=72,
        descender=-20, glyphs=GLYPHS),
     expect_substrings=["Fam-fourteen.cpfont", "not <Family>_<points>"])

# --- C: the 1x ramp against the recipe ------------------------------------
def stale_ramp(fam):
    """A slot from a superseded ramp, exactly as the card's Almendra still
    carries 6/8/10/12/14/17 after 2508a1eb4 moved it to 8/10/12/14/16/18."""
    for d in (fam, fam / "2x"):
        (d / "Fam_16.cpfont").rename(d / "Fam_17.cpfont")


case("C stale ramp", stale_ramp,
     recipe_sizes=sorted(RAMP),
     expect_substrings=["1x ramp is", "missing Fam_16.cpfont",
                        "orphan Fam_17.cpfont"])

case("C missing 1x slot", lambda fam: (fam / "Fam_7.cpfont").unlink(),
     recipe_sizes=sorted(RAMP),
     expect_substrings=["missing Fam_7.cpfont"])

# --- D: the tier's slot set ----------------------------------------------
case("D missing companion", lambda fam: (fam / "2x" / "Fam_9.cpfont").unlink(),
     expect_substrings=["no 2x companion for Fam_9.cpfont", "1x replicated"])

case("D orphan companion", lambda fam: write_font(
        fam / "2x" / "Fam_28.cpfont", advance_y=90, ascender=72,
        descender=-20, glyphs=GLYPHS),
     expect_substrings=["Fam_28.cpfont has no 1x slot"])

# --- E: the ramp must ascend ---------------------------------------------
def swap_ramp(fam):
    a, b = fam / "Fam_12.cpfont", fam / "Fam_14.cpfont"
    a_b, b_b = a.read_bytes(), b.read_bytes()
    a.write_bytes(b_b)
    b.write_bytes(a_b)


case("E swapped 1x slots", swap_ramp,
     expect_substrings=["not ascending", "advanceY", "swapped"])

# --- F: THE ONE. B-039, reconstructed synthetically ----------------------
def plant_b039(fam):
    """The 2x cut of the 7 pt slot, under the 14 pt slot's name. 2 x 7 = 14."""
    (fam / "2x" / "Fam_14.cpfont").write_bytes(
        (fam / "2x" / "Fam_7.cpfont").read_bytes())


case("F B-039 half-size companion", plant_b039,
     expect_substrings=["Fam_14.cpfont", "NOT A 2x RENDER OF 14 pt",
                        "advance_y 46 where a 2x cut needs ~90"])


def plant_adjacent(fam):
    """The tightest real mixup: an adjacent slot's cut under this name."""
    (fam / "2x" / "Fam_14.cpfont").write_bytes(
        (fam / "2x" / "Fam_16.cpfont").read_bytes())


case("F adjacent-slot mixup", plant_adjacent,
     expect_substrings=["Fam_14.cpfont",
                        "advance_y 102 where a 2x cut needs ~90"])

case("F ascender only", lambda fam: write_font(
        fam / "2x" / "Fam_14.cpfont", advance_y=90, ascender=36, descender=-20,
        glyphs=GLYPHS),
     expect_substrings=["ascender 36 where a 2x cut needs ~72"])

# The tolerance must ACCEPT the rounding a real build produces. Worst measured
# deviation across all eight shipped families, both tiers, all four styles is
# 1 px in every one of the three fields (2026-08-26).
case("F rounding is not a fault", lambda fam: (
        write_font(fam / "2x" / "Fam_14.cpfont", advance_y=91, ascender=73,
                   descender=-21, glyphs=GLYPHS),
        # ... and then a real fault, so the case still has something to catch.
        write_font(fam / "2x" / "Fam_12.cpfont", advance_y=39, ascender=62,
                   descender=-18, glyphs=GLYPHS)),
     expect_substrings=["Fam_12.cpfont"])

# --- G: style parity ------------------------------------------------------
case("G missing italic", lambda fam: write_font(
        fam / "2x" / "Fam_14.cpfont", advance_y=90, ascender=72, descender=-20,
        glyphs=GLYPHS, styles=(0, 1)),
     expect_substrings=["carries styles [0, 1]", "1x replicated"])

# --- H: charset coverage --------------------------------------------------
case("H stale charset", lambda fam: write_font(
        fam / "2x" / "Fam_14.cpfont", advance_y=90, ascender=72, descender=-20,
        glyphs=1094),
     expect_substrings=["1094 glyphs", "STALE CHARSET"])

case("H more than the base", lambda fam: write_font(
        fam / "2x" / "Fam_14.cpfont", advance_y=90, ascender=72, descender=-20,
        glyphs=GLYPHS + 50),
     expect_substrings=["cannot cover"])

# A deliberate per-tier drop is NOT a fault. InknutJunicode's 2x tier drops
# U+2E3B, whose 289x5 px raster overflows EpdGlyph's uint8 width, so the
# shipped tier legitimately reads 2692 against the 1x set's 2693.
with tempfile.TemporaryDirectory() as _td:
    _root = Path(_td)
    _fam = build_tree(_root)
    write_font(_fam / "2x" / "Fam_14.cpfont", advance_y=90, ascender=72,
               descender=-20, glyphs=GLYPHS - 1)
    _p = run(_root)
    if _p:
        print("FAIL H one deliberate drop was rejected:\n    " + "\n    ".join(_p))
        FAILS += 1
    else:
        print("ok   H one deliberate drop is accepted")

# --- tiers above the ceiling are skipped, not passed and not failed -------
with tempfile.TemporaryDirectory() as _td:
    _root = Path(_td)
    _fam = build_tree(_root)
    # A 3x tier that is wrong in every way. At ceiling 2 it must not be judged.
    write_font(_fam / "3x" / "Fam_14.cpfont", advance_y=45, ascender=18,
               descender=-5, glyphs=17)
    _p, _n, _ = V.validate(_root, None, 2)
    if _p:
        print("FAIL ceiling: a 3x tier was judged at max-tier 2:\n    " +
              "\n    ".join(_p))
        FAILS += 1
    elif not any("3x" in n and "not checked" in n for n in _n):
        print(f"FAIL ceiling: the skipped tier was not reported: {_n}")
        FAILS += 1
    else:
        print("ok   tiers above the ceiling are skipped and said so")
    _p3, _, _ = V.validate(_root, None, 3)
    if not _p3:
        print("FAIL ceiling: raising max-tier to 3 did not judge the 3x tier")
        FAILS += 1
    else:
        print("ok   raising the ceiling judges the tier")

# --- the recipe parser must not silently become a no-op ------------------
with tempfile.TemporaryDirectory() as _td:
    _r = Path(_td) / "sd-fonts.yaml"
    _r.write_text("installed_families:\n  - Fam\n")   # no `- name:` blocks
    try:
        V.parse_recipe(_r)
        print("FAIL recipe: a recipe with no family blocks parsed as empty "
              "instead of raising -- check C would silently pass everything")
        FAILS += 1
    except V.FontError:
        print("ok   a recipe it cannot parse is an error, not an empty result")

# The REAL recipe must parse, and must name every installed family. This is the
# one place the test touches the firmware checkout, and it is optional: CI and
# a developer's box both have one, a fresh clone might not.
_real = Path(__file__).resolve().parent.parent.parent / "crosspoint-reader" \
    / "lib/EpdFont/scripts/sd-fonts.yaml"
if _real.is_file():
    _sizes = V.parse_recipe(_real)
    _installed = []
    _in = False
    for _line in _real.read_text().splitlines():
        if _line.startswith("installed_families:"):
            _in = True
        elif _in:
            if _line.startswith("  - "):
                _installed.append(_line[4:].strip())
            elif _line and not _line.startswith((" ", "#")):
                _in = False
    _absent = [f for f in _installed if f not in _sizes]
    if not _installed:
        print("FAIL recipe: parsed no installed_families out of the real recipe")
        FAILS += 1
    elif _absent:
        print(f"FAIL recipe: the real recipe parsed, but {_absent} got no sizes")
        FAILS += 1
    else:
        print(f"ok   the real recipe parses ({len(_installed)} installed families, "
              f"{len(_sizes)} recipes)")
else:
    print("skip the real recipe (no firmware checkout beside this repo)")

print()
if FAILS:
    print(f"{FAILS} failure(s)")
    sys.exit(1)
print("validate_seed_fonts: all checks fire")
