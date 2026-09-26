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
    KLI_DIR=... python3 kli_arms.py --flags 0x2 --script size_sweep.py -- --font ... --img DIR --out res.json

`--script` picks another ../etrace tool that renders through the index's
render.py (size_sweep.py: the same reader over 8-13 px).
"""
import os, sys, runpy

argv = sys.argv[1:]
flags = 0
if argv[:1] == ["--flags"]:
    flags = int(argv[1], 0)
    argv = argv[2:]
script = "kli_e.py"
if argv[:1] == ["--script"]:
    script = argv[1]
    argv = argv[2:]
if argv[:1] == ["--"]:
    argv = argv[1:]

import freetype  # noqa: E402
freetype.FT_LOAD_TARGET_NORMAL = flags
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "etrace"))
sys.argv = [script] + argv
runpy.run_path(os.path.join(here, "..", "etrace", script), run_name="__main__")
