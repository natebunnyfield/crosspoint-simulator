#!/usr/bin/env python3
"""Print the firmware -I flags, read from cmake/CrossPointSources.cmake.

The host-compiled tests in tests/ need the same include set the CMake build
uses. Duplicating that list into each test command guarantees the two drift;
this reads the one authoritative copy instead.

Usage (from the repo root):
    c++ ... -Isrc $(python3 tools/fw_include_flags.py) tests/foo.cpp

CROSSPOINT_FIRMWARE_DIR overrides the firmware checkout (default
~/src/crosspoint-reader).
"""

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES = REPO / "cmake" / "CrossPointSources.cmake"


def main() -> int:
    firmware = Path(
        os.environ.get("CROSSPOINT_FIRMWARE_DIR", Path.home() / "src" / "crosspoint-reader")
    ).expanduser()
    if not firmware.is_dir():
        print(f"error: firmware dir not found: {firmware}", file=sys.stderr)
        return 1

    text = SOURCES.read_text()
    match = re.search(r"set\(CROSSPOINT_FW_INCLUDE_DIRS(.*?)\n\)", text, re.S)
    if not match:
        print("error: CROSSPOINT_FW_INCLUDE_DIRS not found", file=sys.stderr)
        return 1

    # Comment lines start with # in CMake; the list itself is plain paths.
    dirs = [
        line.strip()
        for line in match.group(1).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    print(" ".join(f"-I{firmware / d}" for d in dirs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
