#!/usr/bin/env python3
"""The Kept Legibility Index for one hinting ARM (2026-09-26).

The index renders with its own bench/render.py, which loads every glyph with
`FT_LOAD_RENDER | FT_LOAD_TARGET_NORMAL` -- the same default hinting the
firmware's converter asks for. A font-file arm (ttfautohint) needs nothing
else. A LOAD-FLAG arm (no hinting, light autohint) cannot be expressed as a
font, so this wrapper rebinds `freetype.FT_LOAD_TARGET_NORMAL` (0) to the
arm's extra flags BEFORE the index is imported; render.py reads the attribute
at call time, so every glyph the index draws in this process takes the arm's
flags. One arm per process, because the rebinding applies to every font the
process renders (do not put a reference face in a load-flag arm's run).

Then it hands off to ../etrace/kli_e.py unchanged (the index's own v3.1
protocol and its own confusion reduction).

    KLI_DIR=... python3 kli_arms.py --flags 0x2 -- --font "Albo nohint" F.ttf --out res.json
"""
import os, sys, runpy

argv = sys.argv[1:]
flags = 0
if argv[:1] == ["--flags"]:
    flags = int(argv[1], 0)
    argv = argv[2:]
if argv[:1] == ["--"]:
    argv = argv[1:]

import freetype  # noqa: E402
freetype.FT_LOAD_TARGET_NORMAL = flags
here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["kli_e.py"] + argv
runpy.run_path(os.path.join(here, "..", "etrace", "kli_e.py"), run_name="__main__")
