#!/usr/bin/env python3
"""Refuse a seed-font tree whose files do not render the size their names claim.

WHY THIS EXISTS
---------------
On 2026-08-26 InknutJunicode shipped to TestFlight with its L slot drawing at
half size -- every letter separated by a gap, obvious to the owner in one
glance. `build/seedfonts/InknutJunicode/2x/InknutJunicode_14.cpfont` held a
**14 ppem** render where a 28 ppem one belonged: the 2x cut of the 7 pt slot,
left under the wrong name by a build that aborted before it could rename its
outputs. `2 x 7 = 14`, and 14 pt is itself a slot in that ramp, so the orphan
landed on exactly the path `SdCardFontManager::hiResCompanionPath` looks for
and **loaded with no error anywhere**. The advance grid comes from the 1x file
and the ink from the companion, so the spacing was right and the ink filled
half of it. Full account: crosspoint-reader/docs/inknut-l-slot-2026-08-26.md.

Every gate we had passed that build. The host suites passed, the ESP32 build
passed, the deploy's own checks passed, the app launched and rendered. A human
looking at a page was the only thing that caught it.

The class this refuses is therefore: **a .cpfont in the shipping tree whose
actual rendered size does not match the size its filename claims** -- plus the
adjacent ways a tier can be wrong without any reader complaining. It needs no
rasterizer and no rendering: every number it judges is in the file's own 32-byte
header and style TOC (docs/cpfont-format.md sections 2.2-2.3), so the whole
eight-family tree is read in well under a second.

WHAT IT CHECKS, AND WHAT EACH ONE IS FOR
----------------------------------------
A. header    -- magic, version, style count, TOC parses, styleIds unique.
                For a truncated, half-written or entirely wrong file sitting
                under a .cpfont name. The reader would reject these loudly, so
                this is the cheap floor, not the point.
B. filename  -- `<Family>_<int>.cpfont`, prefix equal to the directory name.
                For a file from another family copied into the wrong tree.
C. ramp      -- the 1x slot set equals sd-fonts.yaml's `sizes:` for that family.
                This is what makes the tree answerable to the RECIPE rather
                than merely self-consistent: it catches a stale ramp, an orphan
                filename, and a slot that never built. It found one on its
                first run -- the simulator card's Almendra was still on the
                superseded 6/8/10/12/14/17 ramp, and has been reprovisioned.
D. tier set  -- every shipped hi-res tier carries exactly the 1x slot set.
                Catches a missing companion (which degrades SILENTLY to
                1x-replicated) and an orphan companion (which is what B-039
                was). Independent of C, so it still bites with no recipe.
E. ascending -- advanceY strictly increases with point size, per style, per
                tier. A ramp that is not monotonic is two files swapped.
F. scale     -- |advanceY_T - T * advanceY_1x| <= 1 + T, and the same for
                ascender and descender. THE check that catches B-039: the
                broken file read advanceY 45 where 90 was required, against a
                tolerance of 3. Measured across all eight healthy families,
                both tiers, all four styles, the worst real deviation is 1 --
                advanceY is an integer rounding of a real, so the ideal bound
                is 0.5 + T*0.5 and hinting at a different ppem adds a little.
                The tightest FAULT this must still separate is a one-slot
                mixup in the closest ramp (TeXGyreHeros 11 vs 12 pt), which is
                7. So: 3x headroom over noise, and the smallest fault is 2x
                the tolerance.
G. styles    -- the tier carries the same styleIds as its 1x base. A companion
                missing italic renders italic 1x-replicated, silently.
H. coverage  -- 0.99 <= tier glyphCount / 1x glyphCount <= 1.0, per style.
                For a tier built from an older, narrower charset: the bundle
                carried three 2x files with 1094 glyphs against the 1x set's
                2693, so ~1600 codepoints rendered 1x-replicated at those
                slots. Right scale, stale charset -- F cannot see it.
                The ceiling of 1.0 is not slack: a tier with MORE glyphs than
                its base was built from a different recipe.

WHAT IT DOES NOT CHECK, deliberately: the interval table's internal layout, the
glyph table, the bitmap section. SdCardFont validates all three at load and
fails loudly (docs/cpfont-format.md section 2.5), so a second copy here would
be a second definition to drift. This gate exists for the failures that load
CLEANLY and look fine.

Tiers above --max-tier are NOT checked, and are reported as skipped rather than
passed. At the shipping ceiling of 2 that is every `3x/` directory, and those
are known to carry the pre-`reading` charset -- excluded from the bundle rather
than deleted, since rebuilding one is a ~40 minute rasterisation run
(ios/CMakeLists.txt). Checking them would fail on H for a tier nothing ships.

Also usable as an auditor of any tree of this shape -- the simulator's card at
crosspoint-reader/fs_/fonts/ is the other one.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zlib
from pathlib import Path

CPFONT_MAGIC = b"CPFONT\0\0"
CPFONT_VERSION = 4
CPZ1_MAGIC = b"CPZ1"
CPZ1_HEADER_BYTES = 24

# Enough for the 32-byte global header plus four 32-byte TOC entries, with room
# to spare. Nothing past offset 160 is read.
HEADER_SLICE = 4096

# Fraction of the 1x glyph count a hi-res tier must still carry (check H).
# Deliberate per-tier codepoint drops exist -- InknutJunicode's 2x tier drops
# U+2E3B, whose 289x5 px raster overflows EpdGlyph's uint8 width -- so this is
# not 1.0. Measured on the shipped tree the only real deficit is that single
# glyph (2692 of 2693). 0.99 leaves room for ~26 such drops and still rejects
# the 0.41 a stale charset produces.
MIN_COVERAGE = 0.99

FILENAME_RE = re.compile(r"^(?P<family>.+)_(?P<pt>\d+)$")
TIER_DIR_RE = re.compile(r"^(?P<tier>\d+)x$")


class FontError(Exception):
    pass


# --------------------------------------------------------------------------
# Reading the header
# --------------------------------------------------------------------------

def _read_head(path: Path) -> bytes:
    """The first HEADER_SLICE logical bytes, through a CPZ1 container if present.

    The tree is validated BEFORE compression on the deploy path, so the
    container branch is not what normally runs. It is here so the same tool can
    audit a bundled or installed tree, where every file is a container -- and
    because a validator that silently mis-parses a container would report a
    wrong advanceY rather than an error, which is the exact failure mode this
    file exists to prevent.
    """
    with path.open("rb") as f:
        buf = f.read(HEADER_SLICE)
        if buf[:4] != CPZ1_MAGIC:
            return buf
        if len(buf) < CPZ1_HEADER_BYTES:
            raise FontError("CPZ1 container is shorter than its own header")
        block, original, count, _reserved = struct.unpack("<IQII", buf[4:24])
        if count == 0 or block == 0:
            raise FontError("CPZ1 container declares no blocks")
        index_bytes = 4 * count
        f.seek(0)
        prefix = f.read(CPZ1_HEADER_BYTES + index_bytes)
        if len(prefix) < CPZ1_HEADER_BYTES + index_bytes:
            raise FontError("CPZ1 block index is truncated")
        first_end = struct.unpack_from("<I", prefix, CPZ1_HEADER_BYTES)[0]
        payload = f.read(first_end)
        try:
            # Raw deflate, no zlib wrapper -- tools/compress_seed_fonts.py.
            return zlib.decompressobj(-15).decompress(payload)[:HEADER_SLICE]
        except zlib.error as exc:
            raise FontError(f"CPZ1 block 0 will not inflate: {exc}") from exc


class Style:
    __slots__ = ("style_id", "glyph_count", "advance_y", "ascender", "descender")

    def __init__(self, style_id, glyph_count, advance_y, ascender, descender):
        self.style_id = style_id
        self.glyph_count = glyph_count
        self.advance_y = advance_y
        self.ascender = ascender
        self.descender = descender


class Font:
    __slots__ = ("path", "point_size", "styles")

    def __init__(self, path, point_size, styles):
        self.path = path
        self.point_size = point_size
        self.styles = styles  # {styleId: Style}


def read_font(path: Path, point_size: int) -> Font:
    """Check A: parse the global header and the style TOC, or raise."""
    buf = _read_head(path)
    if len(buf) < 32:
        raise FontError(f"file is {len(buf)} bytes; a header is 32")
    if buf[:8] != CPFONT_MAGIC:
        raise FontError(f"bad magic {buf[:8]!r}, expected {CPFONT_MAGIC!r}")
    version, flags, style_count = struct.unpack_from("<HHB", buf, 8)
    if version != CPFONT_VERSION:
        raise FontError(f"version {version}, the reader accepts only {CPFONT_VERSION}")
    if not (flags & 1):
        raise FontError("flags bit 0 (is2Bit) is clear; every shipped file sets it")
    if not 1 <= style_count <= 4:
        raise FontError(f"styleCount {style_count} outside 1..4")
    need = 32 + 32 * style_count
    if len(buf) < need:
        raise FontError(f"file is {len(buf)} bytes; the style TOC needs {need}")
    styles = {}
    for i in range(style_count):
        e = 32 + 32 * i
        style_id = buf[e]
        if style_id > 3:
            raise FontError(f"TOC entry {i} has styleId {style_id}, outside 0..3")
        if style_id in styles:
            raise FontError(f"styleId {style_id} appears twice in the TOC")
        glyph_count = struct.unpack_from("<I", buf, e + 8)[0]
        advance_y = buf[e + 12]
        ascender, descender = struct.unpack_from("<hh", buf, e + 13)
        if advance_y == 0:
            raise FontError(f"style {style_id} has advanceY 0")
        styles[style_id] = Style(style_id, glyph_count, advance_y, ascender, descender)
    return Font(path, point_size, styles)


# --------------------------------------------------------------------------
# The recipe
# --------------------------------------------------------------------------

def parse_recipe(path: Path) -> dict[str, list[int]]:
    """`sizes:` per family out of sd-fonts.yaml, without a YAML dependency.

    Hand-parsed for the same reason ios/CMakeLists.txt hand-parses
    installed_families: this runs on the deploy path and on CI, and PyYAML is
    not guaranteed on either. It is deliberately strict -- a family whose block
    is found but whose `sizes:` is not is an ERROR, not a silent skip, or a
    format change would turn check C into a no-op that still prints OK.
    """
    sizes: dict[str, list[int]] = {}
    current: str | None = None
    seen_families = False
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0] if not raw.lstrip().startswith("#") else ""
        m = re.match(r"^\s*-\s*name:\s*(\S+)\s*$", line)
        if m:
            current = m.group(1)
            seen_families = True
            continue
        if current is None:
            continue
        m = re.match(r"^\s*sizes:\s*\[([^\]]*)\]\s*$", line)
        if m:
            sizes[current] = [int(x) for x in m.group(1).replace(",", " ").split()]
            current = None
    if not seen_families:
        raise FontError(
            f"parsed no `- name:` blocks out of {path}. The recipe's format "
            "changed; fix this parser rather than deleting the check."
        )
    return sizes


# --------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------

def scale_tolerance(tier: int) -> int:
    """Check F's tolerance, in whole pixels. See the module docstring."""
    return 1 + tier


def collect_tier(directory: Path, family: str, problems: list[str], label: str):
    """Checks A and B over one directory. Returns {pointSize: Font}."""
    out: dict[int, Font] = {}
    for path in sorted(directory.glob("*.cpfont")):
        m = FILENAME_RE.match(path.stem)
        if not m:
            problems.append(
                f"{path}: filename is not <Family>_<points>.cpfont, so nothing "
                f"on the device can address it as a slot of {family}."
            )
            continue
        if m.group("family") != family:
            problems.append(
                f"{path}: names family {m.group('family')!r} but sits in the "
                f"{family!r} tree. SdCardFontRegistry takes the family from the "
                f"DIRECTORY, so this would load as a {family} slot."
            )
            continue
        pt = int(m.group("pt"))
        try:
            out[pt] = read_font(path, pt)
        except FontError as exc:
            problems.append(f"{path}: {exc} [{label}]")
    return out


def check_family(fam_dir: Path, recipe_sizes, max_tier: int, problems, notes):
    family = fam_dir.name
    base = collect_tier(fam_dir, family, problems, "1x")
    if not base:
        problems.append(f"{fam_dir}: no readable 1x .cpfont files at all.")
        return

    # C -- the 1x ramp against the recipe.
    if recipe_sizes is not None:
        want, have = sorted(recipe_sizes), sorted(base)
        if want != have:
            missing = [s for s in want if s not in base]
            extra = [s for s in have if s not in recipe_sizes]
            bits = []
            if missing:
                bits.append("missing " + ", ".join(f"{family}_{s}.cpfont" for s in missing))
            if extra:
                bits.append("orphan " + ", ".join(f"{family}_{s}.cpfont" for s in extra))
            problems.append(
                f"{fam_dir}: 1x ramp is {have}, the recipe says {want} -- "
                + "; ".join(bits)
                + ". A slot the recipe names and the tree lacks is a size the "
                  "reader cannot offer; a file the recipe does not name is "
                  "either a stale cut from an older ramp or a misnamed output."
            )
    else:
        notes.append(f"{family}: not named in the recipe, so its 1x ramp is unchecked.")

    check_ascending(family, "1x", base, problems)

    for tier_dir in sorted(d for d in fam_dir.iterdir() if d.is_dir()):
        m = TIER_DIR_RE.match(tier_dir.name)
        if not m:
            notes.append(f"{tier_dir}: not a <N>x tier directory; ignored.")
            continue
        tier = int(m.group("tier"))
        if tier > max_tier:
            notes.append(
                f"{family}/{tier}x: above the bundling ceiling of {max_tier}x, "
                f"not shipped, not checked."
            )
            continue
        check_tier(family, tier, tier_dir, base, problems)


def check_ascending(family: str, label: str, fonts: dict[int, Font], problems):
    """Check E. One message per offending file, however many styles agree."""
    order = sorted(fonts)
    hits: dict[int, dict[tuple, list[int]]] = {}
    for style_id in sorted({s for f in fonts.values() for s in f.styles}):
        prev_pt = None
        for pt in order:
            st = fonts[pt].styles.get(style_id)
            if st is None:
                continue
            if prev_pt is not None:
                prev = fonts[prev_pt].styles[style_id]
                if st.advance_y <= prev.advance_y:
                    hits.setdefault(pt, {}).setdefault(
                        (prev_pt, prev.advance_y, st.advance_y), []
                    ).append(style_id)
            prev_pt = pt
    for pt, groups in sorted(hits.items()):
        lines = []
        for (prev_pt, prev_a, a), ids in groups.items():
            which = ("style " if len(ids) == 1 else "styles ") + \
                ",".join(str(i) for i in ids)
            lines.append(f"{which} advanceY {prev_a} at {prev_pt} pt "
                         f"then {a} at {pt} pt")
        problems.append(
            f"{fonts[pt].path}: the {label} ramp is not ascending -- "
            + "; ".join(lines)
            + ". Two slots are swapped, or one was rasterised at the wrong size."
        )


def check_tier(family: str, tier: int, tier_dir: Path, base, problems):
    fonts = collect_tier(tier_dir, family, problems, f"{tier}x")

    # D -- the tier must carry exactly the 1x slot set.
    missing = sorted(set(base) - set(fonts))
    orphan = sorted(set(fonts) - set(base))
    if missing:
        problems.append(
            f"{tier_dir}: no {tier}x companion for "
            + ", ".join(f"{family}_{s}.cpfont" for s in missing)
            + f". SdCardFontManager looks for that exact path and finds nothing, "
              f"so those slots render 1x replicated into {tier}x{tier} blocks -- "
              f"coarse, and silent."
        )
    if orphan:
        problems.append(
            f"{tier_dir}: "
            + ", ".join(f"{family}_{s}.cpfont" for s in orphan)
            + " has no 1x slot. An orphan under a name no lookup reaches is dead"
              " weight; an orphan under a name that DOES collide with a real slot"
              " is B-039, and loads with no error."
        )

    check_ascending(family, f"{tier}x", fonts, problems)

    tol = scale_tolerance(tier)
    for pt in sorted(set(fonts) & set(base)):
        hi, lo = fonts[pt], base[pt]
        # G -- style parity.
        if set(hi.styles) != set(lo.styles):
            problems.append(
                f"{hi.path}: carries styles {sorted(hi.styles)} against the 1x "
                f"file's {sorted(lo.styles)}. A style with no companion renders "
                f"1x replicated while its siblings do not."
            )
        # F -- the size the file actually renders at. Aggregated to ONE message
        # per file: a wrong cut fails every field of every style at once, and
        # sixteen restatements of one fault bury the other files in the run.
        # Styles that fail identically are named together: in a wrong-cut file
        # all four do, and four restatements of one number teach nothing.
        grouped: dict[tuple, list[int]] = {}
        for style_id in sorted(set(hi.styles) & set(lo.styles)):
            h, l = hi.styles[style_id], lo.styles[style_id]
            for field in ("advance_y", "ascender", "descender"):
                got, base_v = getattr(h, field), getattr(l, field)
                if abs(got - tier * base_v) > tol:
                    grouped.setdefault((field, got, base_v), []).append(style_id)
        scale_hits = []
        for (field, got, base_v), ids in grouped.items():
            ratio = (got / base_v) if base_v else float("nan")
            which = ("style " if len(ids) == 1 else "styles ") + \
                ",".join(str(i) for i in ids)
            scale_hits.append(
                f"{which} {field} {got} where a {tier}x cut needs ~{tier * base_v} "
                f"(1x reads {base_v}; ratio {ratio:.3f}, not {tier}.000)"
            )
        if scale_hits:
            problems.append(
                f"{hi.path}: THIS FILE IS NOT A {tier}x RENDER OF {pt} pt. "
                + "; ".join(scale_hits)
                + f". Tolerance is {tol} px; the worst rounding a real build "
                  f"produces is 1. It is a cut of some other size sitting under "
                  f"this name -- it will load with no error anywhere and draw at "
                  f"the wrong size, which is exactly B-039."
            )
        for style_id in sorted(set(hi.styles) & set(lo.styles)):
            h, l = hi.styles[style_id], lo.styles[style_id]
            # H -- charset coverage.
            if l.glyph_count:
                frac = h.glyph_count / l.glyph_count
                if frac > 1.0:
                    problems.append(
                        f"{hi.path}: style {style_id} carries {h.glyph_count} glyphs "
                        f"against the 1x base's {l.glyph_count}. A tier cannot cover "
                        f"MORE than its base; this was built from a different recipe."
                    )
                elif frac < MIN_COVERAGE:
                    problems.append(
                        f"{hi.path}: style {style_id} carries {h.glyph_count} glyphs "
                        f"against the 1x base's {l.glyph_count} ({frac:.3f}, floor "
                        f"{MIN_COVERAGE}). Right scale, STALE CHARSET -- the missing "
                        f"{l.glyph_count - h.glyph_count} codepoints render 1x "
                        f"replicated at this slot while their neighbours do not."
                    )


# --------------------------------------------------------------------------

def validate(tree: Path, recipe: Path | None, max_tier: int):
    problems: list[str] = []
    notes: list[str] = []
    sizes = parse_recipe(recipe) if recipe else None

    families = sorted(d for d in tree.iterdir() if d.is_dir())
    if not families:
        problems.append(f"{tree}: no family directories.")
    for fam_dir in families:
        check_family(
            fam_dir,
            None if sizes is None else sizes.get(fam_dir.name),
            max_tier,
            problems,
            notes,
        )
    return problems, notes, families


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("tree", type=Path, help="a <Family>/*.cpfont tree")
    ap.add_argument("--recipe", type=Path, default=None,
                    help="firmware lib/EpdFont/scripts/sd-fonts.yaml, for check C")
    ap.add_argument("--max-tier", type=int, default=2,
                    help="highest hi-res tier this build bundles (default 2)")
    ap.add_argument("--quiet", action="store_true",
                    help="print only the one-line verdict when everything passes")
    args = ap.parse_args(argv)

    if not args.tree.is_dir():
        print(f"ERROR: {args.tree} is not a directory", file=sys.stderr)
        return 2
    if args.recipe is not None and not args.recipe.is_file():
        print(f"ERROR: no recipe at {args.recipe}", file=sys.stderr)
        return 2

    try:
        problems, notes, families = validate(args.tree, args.recipe, args.max_tier)
    except FontError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        for n in notes:
            print(f"  note: {n}")

    if problems:
        print("", file=sys.stderr)
        print("SEED FONT TREE REJECTED", file=sys.stderr)
        print(f"  {args.tree}", file=sys.stderr)
        print("", file=sys.stderr)
        for p in problems:
            print(f"  FAIL  {p}", file=sys.stderr)
            print("", file=sys.stderr)
        print(
            f"{len(problems)} problem(s). A .cpfont whose rendered size does not "
            f"match its filename LOADS WITHOUT ERROR and draws at the wrong size "
            f"(B-039, InknutJunicode's L slot, 2026-08-26). Rebuild the family "
            f"rather than shipping this.",
            file=sys.stderr,
        )
        return 1

    print(
        f"seed fonts OK: {len(families)} families, 1x + tiers up to {args.max_tier}x, "
        f"header-verified against "
        + (f"{args.recipe}" if args.recipe else "the tree's own 1x ramp")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
