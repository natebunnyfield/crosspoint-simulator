"""Build the contrast x weight grid, measure each, subset it and emit one JSON
of base64 fonts + measured numbers for the interactive page."""
import os, sys, json, base64, subprocess, io
WT = '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad/wt226/tools/wedge_serif'
SP = '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad'
OUT = SP + '/iv/'
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, WT)

WEIGHTS = [(200, 'ExtraLight', 43.8), (400, 'Regular', 66.9), (700, 'Bold', 116), (900, 'Black', 148)]
# (label, BOWL hair fraction, the o's hairline floor)
CONTRAST = [('0', 0.60, 0.55), ('1', 0.53, 0.55), ('2', 0.46, 0.50), ('3', 0.40, 0.46), ('4', 0.34, 0.40)]

TEXT = ("Hamburgefonstiv — obscene goose, folly 1928 "
        "The printer set the page twice, once for the proof and once for the run, "
        "and in between he changed his mind about the spacing of the capitals. "
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789 .,;:!?’“”-—&")


def build(d, stem, style, hair, floor):
    os.makedirs(d, exist_ok=True)
    env = dict(os.environ, FJORD_STEM=str(stem), FJORD_SLANT='0', FJORD_WIDTH='95',
               FJORD_CONTRAST='0.80', FJORD_CUT='0', PYTHON_GIL='0',
               ALBO_BOWL_HAIR=str(hair), ALBO_O_FLOOR=str(floor))
    r = subprocess.run([sys.executable, '-m', 'outlines.build', d, '--style', style],
                       cwd=WT, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print('FAIL', d, r.stderr[-300:]); return None
    for f in os.listdir(d):
        if f.endswith('.ttf'): return os.path.join(d, f)
    return None


import cmp_bold_stem as B
from fontTools import subset as FTS

cells = {}
for w, style, stem in WEIGHTS:
    for cl, hair, floor in CONTRAST:
        key = f'w{w}c{cl}'
        p = build(f'{OUT}build/{key}', stem, style, hair, floor)
        if not p:
            continue
        try:
            m = B.measure(p, 0)
            ratio = round(m['stem'] / m['hair'], 2)
            hair_u = round(m['hair'] / m['xh'] * 429, 1)
            stem_u = round(m['stem'] / m['xh'] * 429, 1)
        except Exception as e:
            print('measure fail', key, e); ratio = hair_u = stem_u = None
        sub = f'{OUT}build/{key}.sub.ttf'
        opts = FTS.Options(); opts.layout_features = ['kern', 'liga']; opts.notdef_outline = True
        opts.drop_tables = ['DSIG']
        font = FTS.load_font(p, opts)
        sr = FTS.Subsetter(options=opts)
        sr.populate(text=TEXT)
        sr.subset(font)
        FTS.save_font(font, sub, opts); font.close()
        b = base64.b64encode(open(sub, 'rb').read()).decode()
        cells[key] = dict(w=w, c=cl, hair=hair, floor=floor, ratio=ratio,
                          hair_u=hair_u, stem_u=stem_u, kb=round(len(b) / 1024), font=b)
        print(key, 'ratio', ratio, 'hair', hair_u, 'stem', stem_u, 'kb', round(len(b) / 1024))

json.dump(cells, open(OUT + 'cells.json', 'w'))
print('total KB', round(sum(len(c['font']) for c in cells.values()) / 1024))
