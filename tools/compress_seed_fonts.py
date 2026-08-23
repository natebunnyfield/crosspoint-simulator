#!/usr/bin/env python3
"""Rewrite a seed-font tree into CPZ1 block-compressed containers.

The container is `src/SimCompressedFile.h`; read that header for why it exists
and why it sits at the HAL's file layer instead of inside the .cpfont format.
This script is the only writer.

What it does NOT do is rasterise anything. It reads finished `.cpfont` files
and re-packages their bytes, so a run costs seconds where rebuilding the same
families from outlines costs tens of minutes. The output keeps the input's
directory shape AND its filenames -- `Edgar/2x/Edgar_28.cpfont` in, the same
path out -- because SdCardFontRegistry finds families by scanning for that
extension and SdCardFontManager finds a hi-res companion at the exact path
`<family>/<tier>x/<same basename>`. A container with a different name would be
invisible to both.

Idempotent and incremental: a file already carrying the magic is copied through
untouched, and an output newer than its input is left alone, so the CMake
configure step that calls this can run on every configure without paying for it
twice.

    python3 tools/compress_seed_fonts.py --input build/seedfonts \\
                                         --output build/seedfonts-cpz
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b"CPZ1"
HEADER_BYTES = 24

# 32 KiB. Measured on the shipped 1x+2x tree (7 families, 56 files,
# 117,654,860 bytes): 8 KiB blocks give 41.9 MB, 16 KiB 40.7 MB, 32 KiB 39.8 MB,
# and a single whole-file stream -- which the reader cannot use, because
# .cpfont is seeked per glyph -- 33.4 MB. Past 32 KiB the curve is flat and the
# reader's per-access inflate cost keeps rising, so this is the knee. It is a
# HEADER FIELD rather than a constant on both sides: the reader sizes its buffer
# from the file, so changing this number does not strand containers already
# written.
DEFAULT_BLOCK = 32768


def compress_one(src: Path, dst: Path, block: int, level: int) -> tuple[int, int]:
    """Write `src` to `dst` as a CPZ1 container. Returns (raw, packed) sizes."""
    data = src.read_bytes()
    if data[:4] == MAGIC:
        # Already a container (a re-run over its own output). Copying rather
        # than double-wrapping keeps this idempotent.
        dst.write_bytes(data)
        return len(data), len(data)

    blocks = []
    for at in range(0, len(data), block):
        # Raw deflate, no zlib header: the block index already carries every
        # length, and InflateStream's one-shot mode expects the bare stream.
        c = zlib.compressobj(level, zlib.DEFLATED, -15)
        blocks.append(c.compress(data[at : at + block]) + c.flush())

    index = bytearray()
    end = 0
    for b in blocks:
        end += len(b)
        index += struct.pack("<I", end)

    header = struct.pack("<4sIQII", MAGIC, block, len(data), len(blocks), 0)
    assert len(header) == HEADER_BYTES, len(header)

    tmp = dst.with_suffix(dst.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(header)
        f.write(index)
        for b in blocks:
            f.write(b)
        packed = f.tell()
    # Rename into place: a configure step killed mid-write must not leave a
    # truncated container where the bundler will pick it up.
    os.replace(tmp, dst)
    return len(data), packed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--block", type=int, default=DEFAULT_BLOCK)
    ap.add_argument("--level", type=int, default=9)
    ap.add_argument("--max-tier", type=int, default=0,
                    help="Skip <Family>/<N>x/ directories above this tier. 0 "
                         "(default) takes the whole tree. The app bundles only "
                         "the tiers it can render, so compressing the rest is "
                         "configure time spent on bytes nothing will read.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.input.is_dir():
        print(f"error: {args.input} is not a directory", file=sys.stderr)
        return 1
    if args.block < 1024 or args.block > (1 << 20):
        # The reader rejects anything outside this range, so refuse to write it.
        print(f"error: --block {args.block} is outside [1024, 1048576]",
              file=sys.stderr)
        return 1

    def above_max_tier(rel: Path) -> bool:
        # <Family>/<N>x/<file>.cpfont -- the tier is the middle component, and
        # it is the ONLY subdirectory shape build-sd-fonts.py emits.
        if args.max_tier <= 0 or len(rel.parts) != 3:
            return False
        name = rel.parts[1]
        if not name.endswith("x") or not name[:-1].isdigit():
            return False
        return int(name[:-1]) > args.max_tier

    raw_total = packed_total = 0
    written = skipped = 0
    for src in sorted(args.input.rglob("*.cpfont")):
        rel = src.relative_to(args.input)
        if above_max_tier(rel):
            continue
        dst = args.output / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            skipped += 1
            raw_total += src.stat().st_size
            packed_total += dst.stat().st_size
            continue
        raw, packed = compress_one(src, dst, args.block, args.level)
        raw_total += raw
        packed_total += packed
        written += 1
        if not args.quiet:
            print(f"  {rel}: {raw:,} -> {packed:,} ({packed / raw:.3f})")

    if raw_total == 0:
        print(f"error: no .cpfont files under {args.input}", file=sys.stderr)
        return 1

    # Anything that is not a .cpfont is carried across verbatim, so a tree with
    # a manifest or a licence file beside the fonts survives the trip.
    for src in sorted(args.input.rglob("*")):
        if src.is_dir() or src.suffix == ".cpfont":
            continue
        dst = args.output / src.relative_to(args.input)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)

    print(f"cpz: {written} written, {skipped} up to date; "
          f"{raw_total:,} -> {packed_total:,} bytes "
          f"({packed_total / raw_total:.3f}), block {args.block}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
