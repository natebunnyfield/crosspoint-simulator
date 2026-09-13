"""Round 58: three bowl profiles as full TTFs and one comparison page.
    python3 -m outlines.cmp.bowl_options <out_dir>"""
import sys, os, html
from .. import primitives as PR, build
from .proof import b64, eink, block
import round19

PARA = "By Dover Road the Bishop barred the Palace door; Ruby rode past Bedford. " + round19.PARAGRAPHS[1][:230]
def main(out):
    paths = {}
    for key in ('A', 'D', 'B', 'C'):
        PR.set_bowl(key); path, W, rep = build.build(out, name='Fjord', style='bowl' + key); paths[key] = path
    PR.set_bowl(None)
    nib = os.path.join(out, 'Fjord-Regular-phase2.ttf')
    figs = []
    def img(im, cap): figs.append(f'<figure><img src="{b64(im)}" width="{im.size[0]}" height="{im.size[1]}"><figcaption>{html.escape(cap)}</figcaption></figure>')
    blocks = [(k, PR.BOWL_OPTIONS[k]['name'], paths[k]) for k in ('A', 'D', 'B', 'C')] + [('nib', 'round 56, the 26-degree nib (reference)', nib)]
    for key, name, path in blocks:
        o = PR.BOWL_OPTIONS.get(key)
        desc = f"hair {o['hair']:.2f} stem, max {o['max']:.2f} stem, exponent {o['pow']}, joins taper to {o['taper']} of the hair, round end k {o['k']}" + (", free terminals widen 15% over the last 12% into the cut" if o.get('widen') else '') + (f", stress maximum at +{o['stress']:.0f} degrees" if o.get('stress') else '') + (", arches never thinner than the stem" if o.get('arch_floor') else '') if o else 'the pen at each tangent (26-degree stress), the shipping bowls before round 57'
        figs.append(f'<h2>{key}: {html.escape(name)}</h2><p>{html.escape(desc)}</p>')
        img(block(path, "DB PR Oo ce bd pq g", 554, line=1.15, rules=True), f'{key}: DBPR Oo ce bdpq g at 230 px x-height')
        img(eink(path, PARA), f'{key}: 13 pt on the 2x reader, four-level pipeline')
    doc = f"""<title>Fjord bowl options</title>
<style>:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 10px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 6px}}h2{{font-size:14px;letter-spacing:.04em;text-transform:uppercase;color:var(--soft);margin:22px 0 4px;border-top:1px solid var(--rule);padding-top:10px}}
figure{{margin:0 0 10px}}figure img{{width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block;background:#fff}}figcaption{{font-size:11px;color:var(--soft);margin-top:2px}}p{{max-width:64ch;color:var(--soft);font-size:13px;margin:0 0 8px}}</style>
<main><h1>Fjord bowl options</h1><p>Four bowl profiles, one hand each across D B P R, O Q C G and o c e b d p q g -- the Albertus direction (low contrast, near-vertical stress, substantial joins, no hairlines); D is fitted to Albertus Medium's measured strokes -- and round 56's nib bowls for reference. The B's waist is one shared bar in every variant. PNG at native pixels; 750 px blocks shown at 375 CSS px. Every ruled proportion, width, wedge, kick, the e's bar and the G3 g are unchanged.</p>{''.join(figs)}</main>"""
    open(os.path.join(out, 'fjord-bowl-options.html'), 'w').write(doc); print('page', len(doc) // 1024, 'KB', paths)

if __name__ == '__main__':
    main(sys.argv[1])
