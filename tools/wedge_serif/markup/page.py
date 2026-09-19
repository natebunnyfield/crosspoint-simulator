import json, html
SP='/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad/ledger'
idx=json.load(open(f'{SP}/index.json'))
def section(style, title):
    rows=[]
    for rid,e in idx.items():
        if e['style']!=style: continue
        rd = e['reading'] or '—'
        rows.append(f'''<figure id="{rid}"><div class="head"><span class="id">{rid}</span><span class="g">{html.escape(e["glyph"])}</span><span class="n">{html.escape(e["name"])}</span></div>
<img src="{e["file"]}" alt="{rid} {html.escape(e["glyph"])} {html.escape(e["name"])}" width="{e["size"][0]}" height="{e["size"][1]}">
<figcaption><b>my reading:</b> {html.escape(rd)}</figcaption></figure>''')
    return f'<section><h2>{title} <small>{len(rows)} regions</small></h2><div class="grid">' + "\n".join(rows) + '</div></section>'
page = f'''<title>Albo Bump Markup Index</title>
<style>
  :root{{--ink:#1b1917;--soft:#5d574e;--ground:#f6f4ef;--rule:#ded8cc;--accent:#7b5430;--mark:#b58a00;}}
  @media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--ink:#ece8e0;--soft:#9a9288;--ground:#141312;--rule:#343029;--accent:#d4a26e;--mark:#e0b830;}}}}
  :root[data-theme="dark"]{{--ink:#ece8e0;--soft:#9a9288;--ground:#141312;--rule:#343029;--accent:#d4a26e;--mark:#e0b830;}}
  body{{background:var(--ground);color:var(--ink);padding-block:36px 80px;padding-left:20px;padding-right:20px;font:16px/1.55 "Iowan Old Style",Palatino,Georgia,serif;}}
  .wrap{{max-width:1400px;margin:0 auto;display:flex;flex-direction:column;gap:30px;}}
  h1{{font-size:30px;margin:0;font-weight:600;}} h2{{font-size:22px;margin:0 0 14px;font-weight:600;border-top:2px solid var(--rule);padding-top:12px;}} h2 small{{font:13px ui-monospace,Menlo,monospace;color:var(--soft);margin-left:10px;}}
  p{{margin:0;max-width:72ch;}} .eyebrow{{font:600 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 10px;}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:18px;}}
  figure{{margin:0;display:flex;flex-direction:column;gap:6px;min-width:0;}}
  figure img{{display:block;max-width:100%;height:auto;image-rendering:pixelated;background:#fff;border:1px solid var(--rule);}}
  .head{{display:flex;gap:10px;align-items:baseline;font:13px ui-monospace,Menlo,monospace;color:var(--soft);}}
  .id{{font-weight:700;color:var(--mark);font-size:15px;}} .g{{font:600 20px "Iowan Old Style",Georgia,serif;color:var(--ink);}}
  figcaption{{font:13px/1.45 ui-monospace,Menlo,monospace;color:var(--soft);}}
  code{{font:12px ui-monospace,Menlo,monospace;}}
</style>
<div class="wrap">
  <header><p class="eyebrow">Albo · bump markup · your yellow regions, indexed</p><h1>Albo Bump Markup Index</h1>
  <p>Every yellow region on your four marked half-sheets, read off and numbered — <b>R01–R57 roman, I01–I127 italic</b> — so your write-up can name them. Each crop is the built outline (vertices as red dots; blue lines are baseline, x-height, cap), the yellow box is where I read your mark, the red circles are the sheet's own numbers. Where I already found the geometry I say so under "my reading"; correct me where the mark meant something else, and tell me any region I have missed or mis-placed. Crops are native pixels (3 px per unit, less on the big ones).</p></header>
{section('roman','Roman')}
{section('italic','Italic')}
  <p>The same index, with room for the write-up, is <code>docs/albo-bump-markup-2026-09-18.md</code> in the repo.</p>
</div>
'''
open(f'{SP}/index.html','w').write(page); print('page', len(page))
