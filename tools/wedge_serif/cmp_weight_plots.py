"""XY graphs of weight against width, contrast and the cap ratio, for every
reference family's regular and bold and for Albo's whole nine-rung ladder.
Measures are cmp_bold_stem's, imported, so no second instrument exists."""
import os, sys, json
sys.path.insert(0, '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad/wt226/tools/wedge_serif')
import cmp_bold_stem as B
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SP = '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad'
OUT = SP + '/g/'
os.makedirs(OUT, exist_ok=True)

ALBO = [(100, 'Thin'), (200, 'ExtraLight'), (300, 'Light'), (400, 'Regular'), (500, 'Medium'),
        (600, 'SemiBold'), (700, 'Bold'), (800, 'ExtraBold'), (900, 'Black')]

CACHE = OUT + 'measures.json'


def collect():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    d = {'roman': [], 'italic': [], 'albo': []}
    for fam, reg, bold in B.ROMAN:
        try:
            d['roman'].append((fam, B.measure(*reg), B.measure(*bold)))
        except Exception as e:
            print('skip', fam, e)
    for fam, reg, bold in B.ITALIC:
        try:
            d['italic'].append((fam, B.measure(*reg), B.measure(*bold)))
        except Exception as e:
            print('skip it', fam, e)
    for w, name in ALBO:
        p = f'{SP}/L/w{w}/Albo-{name}.ttf'
        try:
            d['albo'].append((w, name, B.measure(p, 0)))
        except Exception as e:
            print('skip albo', w, e)
    import glob
    d['alboit'] = []
    for w, name in ALBO:
        g = glob.glob(f'{SP}/LI/w{w}/*.ttf')
        if not g: continue
        try:
            d['alboit'].append((w, name, B.measure(g[0], 0)))
        except Exception as e:
            print('skip alboit', w, e)
    json.dump(d, open(CACHE, 'w'))
    return d


D = collect()


def xy(m, xk, yk):
    x = m['stem_xh'] if xk == 'w' else m[xk]
    if yk == 'width':  y = m['n_adv']
    elif yk == 'contrast': y = m['stem'] / m['hair']
    elif yk == 'cap':  y = m['cap_ratio']
    elif yk == 'thin': y = m['hair'] / m['xh']
    return x, y


PANELS = [
    ('width',    'width: n advance / x-height',
     'A bold buys stroke, not width. Every reference pair runs almost flat;\nAlbo climbs.'),
    ('contrast', 'contrast: thick : thin',
     'Most references gain contrast into the bold. Albo is flat by construction\nand starts far lower.'),
    ('thin',     'the hairline / x-height',
     'Albo thickens its hairline in step with its stem, so it never opens up.'),
    ('cap',      'cap stem / cap height',
     'The capitals track the lowercase closely in every family, Albo included.'),
]

INK, GRID, ALBOC, REFC, BOLDC = '#1b1917', '#ded8cc', '#7b5430', '#8c9aa5', '#3f5666'

for key, ylab, note in PANELS:
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.6), dpi=100)
    for ax, group, title, akey, alab in ((axes[0], 'roman', 'Upright', 'albo', 'Albo roman 100\u2013900'), (axes[1], 'italic', 'Italic', 'alboit', 'Albo italic 100\u2013900')):
        for fam, r, b in D[group]:
            x1, y1 = xy(r, 'w', key); x2, y2 = xy(b, 'w', key)
            ax.plot([x1, x2], [y1, y2], '-', color=GRID, lw=1.4, zorder=1)
            ax.scatter([x1], [y1], s=26, color=REFC, zorder=2)
            ax.scatter([x2], [y2], s=26, color=BOLDC, marker='s', zorder=2)
            ax.annotate(fam.replace('*', ''), (x2, y2), fontsize=6.5, color='#7a7a7a',
                        xytext=(4, -3), textcoords='offset points')
        ax.plot([xy(m, 'w', key)[0] for _, _, m in D[akey]],
                [xy(m, 'w', key)[1] for _, _, m in D[akey]],
                '-o', color=ALBOC, lw=2.2, ms=5, zorder=3, label=alab)
        for w, name, m in D[akey]:
            if w in (100, 400, 500, 700, 900):
                x, y = xy(m, 'w', key)
                ax.annotate(str(w), (x, y), fontsize=7.5, color=ALBOC, fontweight='bold',
                            xytext=(3, 5), textcoords='offset points')
        ax.set_title(title, fontsize=11, color=INK)
        ax.set_xlabel('weight: stem / x-height', fontsize=9)
        ax.set_ylabel(ylab, fontsize=9)
        ax.grid(True, color=GRID, lw=0.6, alpha=0.8)
        ax.tick_params(labelsize=8)
        for s in ax.spines.values(): s.set_color(GRID)
    for a in axes: a.legend(fontsize=8, loc='best', frameon=False)
    fig.suptitle(note, fontsize=9.5, color='#5d574e', y=0.995, ha='center')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    p = OUT + f'xy-{key}.png'
    fig.savefig(p, facecolor='white'); plt.close(fig)
    print(p)

# one combined plane: thick against thin, the contrast plane
fig, ax = plt.subplots(figsize=(8.6, 6.4), dpi=100)
for group, mk in (('roman', 'o'), ('italic', '^')):
    for fam, r, b in D[group]:
        ax.plot([r['stem'] / r['xh'], b['stem'] / b['xh']],
                [r['hair'] / r['xh'], b['hair'] / b['xh']], '-', color=GRID, lw=1.2, zorder=1)
        ax.scatter([r['stem'] / r['xh']], [r['hair'] / r['xh']], s=24, color=REFC, marker=mk, zorder=2)
        ax.scatter([b['stem'] / b['xh']], [b['hair'] / b['xh']], s=24, color=BOLDC, marker=mk, zorder=2)
ax.plot([m['stem'] / m['xh'] for _, _, m in D['albo']],
        [m['hair'] / m['xh'] for _, _, m in D['albo']],
        '-o', color=ALBOC, lw=2.4, ms=6, zorder=3, label='Albo roman 100–900')
ax.plot([m['stem'] / m['xh'] for _, _, m in D['alboit']],
        [m['hair'] / m['xh'] for _, _, m in D['alboit']],
        '--s', color='#a8743f', lw=2.0, ms=5, zorder=3, label='Albo italic 100–900')
for w, name, m in D['albo']:
    ax.annotate(str(w), (m['stem'] / m['xh'], m['hair'] / m['xh']), fontsize=7.5,
                color=ALBOC, fontweight='bold', xytext=(4, 4), textcoords='offset points')
for ratio, lab in ((1.5, '1.5:1'), (2.0, '2:1'), (3.0, '3:1'), (5.0, '5:1')):
    xs = [0.10, 0.42]
    ax.plot(xs, [x / ratio for x in xs], ':', color='#b9b2a4', lw=1)
    ax.annotate(lab, (xs[1], xs[1] / ratio), fontsize=7, color='#9a9288',
                xytext=(2, -1), textcoords='offset points')
ax.set_xlabel('thick: stem / x-height', fontsize=10)
ax.set_ylabel('thin: hairline / x-height', fontsize=10)
ax.set_title('The contrast plane — dotted lines are constant thick:thin', fontsize=11)
ax.grid(True, color=GRID, lw=0.6, alpha=0.8); ax.legend(fontsize=9, frameon=False)
for s in ax.spines.values(): s.set_color(GRID)
fig.tight_layout(); fig.savefig(OUT + 'xy-plane.png', facecolor='white'); plt.close(fig)
print(OUT + 'xy-plane.png')
