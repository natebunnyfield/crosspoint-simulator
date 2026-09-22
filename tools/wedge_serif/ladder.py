#!/usr/bin/env python3
"""Prove a dial is LIVE before spending a ladder on it.

2026-09-21 spent six ladders on dials that did nothing, and every one looked
the same from outside -- a flat response across the rungs:

  * the env var had the wrong prefix (`_gof` prepends ALBO_G_OPEN_, the dial
    was typed ALBO_G_QS_STEM_W) -- five arms, identical numbers;
  * the variable was live but reached DEAD CODE (`G_LRING` is ignored while
    `G_LOOP_PEN` is set, because the ring takes the pen model instead of the
    width table) -- two different tables, byte-identical output;
  * the value went into a table the shipping path does not consult
    (`BENCH_DELTAS` is gated on ALBO_KERN_BENCH, empty by default);
  * the arm was not selected (`ALBO_ALD_G_NECK_W` reads 21->40, 32->78 on its
    own arm and nothing at all while another arm draws the letter);
  * the clip removed nothing, because the ring was already inside the edge it
    was clipped to.

`docs/albo-method.md` states only the INERT direction -- "a dial's zero must
reproduce the previous round exactly". Nothing asserted the LIVE direction.
This does, and it is cheap: a Regular build is about 1.2 s.

    python3 ladder.py --env ALBO_ALD_G_LOOP_PHI --rungs 40,70,100 \
        --style Italic --glyph g

Exit 0 and print DIAL LIVE with the per-rung outline hashes when the glyph
actually moves; exit 1 and print FLAT when it does not. `--measure` runs a
command per rung (the built font's path substituted for {}) and parses the
last number on its stdout, which also catches the instrument-side twin: a
measure that cannot SEE the dial reports the same value while the outline
moves, and that is reported separately rather than as a dead dial.
"""
import argparse, hashlib, os, re, shlex, subprocess, sys, tempfile


# THE STYLE'S OWN ENVIRONMENT, or the ladder builds a DIFFERENT FONT and every
# dial in it reads FLAT. `--style Italic` with no environment is not the aldine
# italic: `ALBO_ITALIC` is unset, so aldine.py's letters are not drawn at all
# and an aldine dial cannot move anything. On 2026-09-21 that reported
# ALBO_ALD_Y_GAP as dead when it moves the gap 6.1 -> 17.1 units -- a FALSE
# FLAT, which is worse than no tool, because this file's whole output is
# "stop laddering that". Same two lines gates.sh and build_env.sh use.
STYLE_ENV = {
    "Regular": {"FJORD_STEM": "66.9", "FJORD_CONTRAST": "0.892"},
    "Italic": {"ALBO_ITALIC": "aldine", "FJORD_STEM": "66.9",
               "FJORD_CONTRAST": "0.80", "FJORD_WIDTH": "95", "FJORD_SLANT": "13"},
}


def build(style, env, outdir):
    e = dict(os.environ)
    e.update(STYLE_ENV.get(style, {}))       # first, so an explicit --env still wins
    e.update(env); e.setdefault("PYTHON_GIL", "0")
    r = subprocess.run([sys.executable, "-m", "outlines.build", outdir, "--style", style],
                       env=e, capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.abspath(__file__)) or ".")
    if r.returncode:
        sys.stderr.write(r.stderr[-800:] + "\n")
        raise SystemExit(f"build failed at {env}")
    return os.path.join(outdir, f"Albo-{'Regular' if style=='Regular' else style}.ttf")


def glyph_hash(path, ch):
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import RecordingPen
    f = TTFont(path); gs = f.getGlyphSet()
    n = f.getBestCmap()[ord(ch)] if len(ch) == 1 else ch
    p = RecordingPen(); gs[n].draw(p)
    return hashlib.md5(repr(p.value).encode()).hexdigest()[:12], f["hmtx"][n][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True, help="the environment variable to ladder")
    ap.add_argument("--rungs", required=True, help="values, separated by --sep")
    ap.add_argument("--sep", default=",", help="rung separator; use e.g. '|' when a "
                    "rung is itself a comma-separated table")
    ap.add_argument("--style", default="Regular")
    ap.add_argument("--glyph", default="g", help="the character the dial is meant to move")
    ap.add_argument("--also", default="", help="extra VAR=VAL pairs, comma separated")
    ap.add_argument("--measure", default="", help="command per rung; {} is the font path")
    args = ap.parse_args()

    extra = dict(kv.split("=", 1) for kv in args.also.split(",") if "=" in kv)
    rungs = [r.strip() for r in args.rungs.split(args.sep)]
    rows = []
    with tempfile.TemporaryDirectory() as td:
        for i, v in enumerate(rungs):
            out = os.path.join(td, f"r{i}"); os.makedirs(out, exist_ok=True)
            env = dict(extra); env[args.env] = v
            ttf = build(args.style, env, out)
            h, adv = glyph_hash(ttf, args.glyph)
            m = ""
            if args.measure:
                cmd = args.measure.replace("{}", shlex.quote(ttf))
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                nums = re.findall(r"-?\d+\.?\d*", r.stdout)
                m = nums[-1] if nums else "?"
            rows.append((v, h, adv, m))

    w = max(len(args.env), 12)
    print(f"{args.env:>{w}}  {'outline':>12}  {'adv':>5}" + ("  measure" if args.measure else ""))
    for v, h, adv, m in rows:
        print(f"{v:>{w}}  {h:>12}  {adv:>5}" + (f"  {m:>7}" if args.measure else ""))

    moved = len({r[1] for r in rows}) > 1
    seen = len({r[3] for r in rows}) > 1 if args.measure else None
    print()
    if not moved:
        print(f"FLAT — the glyph is identical at every rung. {args.env} did not arrive, "
              f"or it reaches code this build does not run. Do NOT ladder it further.")
        return 1
    print(f"DIAL LIVE — the glyph moves across the rungs ({len({r[1] for r in rows})} distinct).")
    if args.measure and not seen:
        print("BUT THE MEASURE IS BLIND: it returns the same value while the outline "
              "moves. The dial is live and the instrument cannot see it — fix the "
              "instrument before reading this ladder.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
