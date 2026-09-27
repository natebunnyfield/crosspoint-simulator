"""Italic figure arms: build, render ONE compact PNG, run the gates.

Written 2026-09-26 for the italic 2/7 work (docs/albo-figures-2-7-2026-09-26.md).
It builds from the LIVE tree it sits in, so uncommitted edits to the builders
are in every arm, today's included.

    uv run --no-project --with uharfbuzz --with freetype-py --with numpy --with pillow \\
      python instruments/fig_it_arms.py OUTDIR \\
        --arm "p: Palatino Italic::ALBO_FIG_2=p ALBO_FIG_7=p" \\
        --arm "t: 7 leg straight::ALBO_FIG_7=t" [--no-gates] [--bold]

Each --arm is "LABEL::ENV=VAL ENV=VAL ...". Those env dials are added to the
shipping italic environment (build_env.sh's ALBO_ITA_ENV / ALBO_BIT_ENV).

Writes the following into OUTDIR:
  sheet.png    54 px, unhinted, HarfBuzz-shaped. Today is the top row, then
               one row per arm, each row being the figure line and a line of
               italic words.
  gates.txt    per arm:
                 - cmp_touch counts, Italic and BoldItalic, plus the q2 / R2 /
                   72 / 24 white;
                 - hairs (the full sweep);
                 - dents at 700 against today;
                 - the glitch sweep;
                 - approved.py.
  <label>/     each arm's fonts.

Builds use ALBO_BUILD_PY (default: the asdf python3, which has shapely and
fontTools). The uv python only renders.
"""
import argparse, os, re, shlex, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fig27_sheet as S  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

PY = os.environ.get("ALBO_BUILD_PY", os.path.expanduser("~/.asdf/shims/python3"))
FIGS = "1927 2024 7:27 £72 27 of 72"
WORDS = "in 1927, 72 lazy waves of 2024 quietly drift"
BASE = {  # build_env.sh, copied as gates.sh copies it: a harness must not source what it is testing
    "Regular": "FJORD_STEM=66.9 FJORD_CONTRAST=0.892",
    "Italic": "ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_SLANT=13",
    "BoldItalic": "ALBO_ITALIC=aldine FJORD_STEM=116 FJORD_SLANT=13 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_CUT=0",
}


def build(out, style, extra=""):
    env = dict(os.environ, PYTHON_GIL="0")
    for kv in (BASE[style] + " " + extra).split():
        k, v = kv.split("=", 1); env[k] = v
    r = subprocess.run([PY, "-m", "outlines.build", out, "--style", style], cwd=WS, env=env,
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"BUILD FAILED {out} {style}: {r.stderr[-400:]}")


def run(args):
    r = subprocess.run([PY] + args, cwd=WS, env=dict(os.environ, PYTHON_GIL="0"), capture_output=True, text=True)
    return r.stdout + r.stderr


def touch_summary(ttf):
    out = run(["cmp_touch.py", ttf, "--top", "6000"])
    tot = re.search(r"(\d+) pair\(s\) TOUCHING, (\d+) below", out)
    pairs = dict(re.findall(r"^\s{2}(\S\S)\s+(-?[0-9.]+)", out, re.M))
    keep = " ".join(f"{p} {pairs[p]}" for p in ("q2", "R2", "72", "24", "27", "7a") if p in pairs)
    return (f"{tot.group(1)} touching, {tot.group(2)} under" if tot else "?") + f"   [{keep}]"


def hairs(ttf):
    out = run(["cmp_contour_hairs.py", ttf])
    return " ".join(l.split()[0] for l in out.splitlines() if re.match(r"^\s+\S+\s+segs", l)) or "0"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--arm", action="append", default=[])
    ap.add_argument("--no-gates", action="store_true")
    ap.add_argument("--bold", action="store_true", help="also put the BoldItalic lines on the sheet")
    A = ap.parse_args()
    os.makedirs(A.out, exist_ok=True)
    arms = [("today", "")] + [tuple(a.split("::", 1)) for a in A.arm]
    dirs = {lab: os.path.join(A.out, re.sub(r"[^A-Za-z0-9]+", "_", lab)[:24] or "arm") for lab, _ in arms}
    jobs = [(dirs[lab], st, env) for lab, env in arms for st in ("Italic", "BoldItalic")]
    jobs.append((dirs["today"], "Regular", ""))
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda j: build(*j), jobs))

    ui = ImageFont.truetype(S.UI, 15)
    styles = ["Italic"] + (["BoldItalic"] if A.bold else [])
    rows = []
    for lab, _ in arms:
        for st in styles:
            f = os.path.join(dirs[lab], f"Albo-{st}.ttf")
            rows.append((lab + ("" if st == "Italic" else "  (700)"), S.line(f, text=FIGS), S.line(f, text=WORDS)))
    LW = 250; RH = rows[0][1].height
    W = LW + max(max(a.width, b.width) for _, a, b in rows)
    im = Image.new("L", (W, 30 + 2 * RH * len(rows) - 14 * len(rows)), 255); dr = ImageDraw.Draw(im)
    dr.text((8, 6), "Italic -- 54 px, unhinted, shaped", font=ui, fill=0)
    y = 30
    for lab, a, b in rows:
        dr.text((8, y + RH // 2 - 8), lab, font=ui, fill=60)
        im.paste(a, (LW, y)); im.paste(b.crop((0, 14, b.width, b.height)), (LW, y + RH - 14))
        y += 2 * RH - 14
        dr.line([(0, y - 1), (W, y - 1)], fill=215)
    im.save(os.path.join(A.out, "sheet.png"))
    print(os.path.join(A.out, "sheet.png"), im.size)
    if A.no_gates:
        return
    lines = []
    today = dirs["today"]
    for lab, env in arms:
        d = dirs[lab]
        lines.append(f"== {lab}   [{env}]")
        for st in ("Italic", "BoldItalic"):
            f = os.path.join(d, f"Albo-{st}.ttf")
            lines.append(f"  touch.{st:10s} {touch_summary(f)}")
            lines.append(f"  hairs.{st:10s} {hairs(f)}")
        dn = run(["cmp_counter_dents.py", os.path.join(today, "Albo-BoldItalic.ttf"), os.path.join(d, "Albo-BoldItalic.ttf"),
                  "--out", os.path.join(d, "dents")])
        lines.append("  dents.700      " + " ".join(dn.strip().splitlines()[-1:]))
        gl = run(["cmp_aldine_glitch.py", "--ttf", os.path.join(d, "Albo-Italic.ttf")])
        lines.append("  glitch         " + " ".join(gl.strip().splitlines()[-1:]))
        ap_ = run(["approved.py", "--check", "--regular", os.path.join(today, "Albo-Regular.ttf"),
                   "--italic", os.path.join(d, "Albo-Italic.ttf")])
        lines.append("  approved       " + " ".join(ap_.strip().splitlines()[-1:]))
    open(os.path.join(A.out, "gates.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
