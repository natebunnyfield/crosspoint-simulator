import json, os
SP = '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad'
cells = json.load(open(SP + '/iv/cells.json'))

faces = "\n".join(
    "@font-face{font-family:'A%s';src:url(data:font/ttf;base64,%s) format('truetype');font-display:block}"
    % (k, v['font']) for k, v in cells.items())
meta = {k: {kk: v[kk] for kk in ('w', 'c', 'hair', 'floor', 'ratio', 'hair_u', 'stem_u')} for k, v in cells.items()}

HTML = """<title>Albo Dial</title>
<style>
:root{--ink:#1b1917;--soft:#5d574e;--ground:#f6f4ef;--panel:#fdfcf9;--rule:#ded8cc;--accent:#7b5430;--warn:#95561b;--ok:#3d6a46;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ink:#ece8e0;--soft:#9a9288;--ground:#141312;--panel:#1c1a17;--rule:#343029;--accent:#d4a26e;--warn:#d69a5e;--ok:#80b289;}}
:root[data-theme="dark"]{--ink:#ece8e0;--soft:#9a9288;--ground:#141312;--panel:#1c1a17;--rule:#343029;--accent:#d4a26e;--warn:#d69a5e;--ok:#80b289;}
__FACES__
body{background:var(--ground);color:var(--ink);padding-block:24px 60px;padding-left:16px;padding-right:16px;
     font:15px/1.55 "Iowan Old Style",Palatino,Georgia,serif;}
.wrap{max-width:1000px;margin:0 auto;display:flex;flex-direction:column;gap:22px;}
h1{font-size:25px;margin:0;font-weight:600;}
h2{font-size:15px;margin:0;font-weight:600;color:var(--accent);
   font-family:ui-monospace,Menlo,monospace;letter-spacing:.06em;text-transform:uppercase;}
p{margin:0;max-width:66ch;} .soft{color:var(--soft);font-size:14px;}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:16px;
       display:flex;flex-direction:column;gap:16px;}
.ctl{display:flex;flex-direction:column;gap:6px;}
.ctl .lab{display:flex;justify-content:space-between;align-items:baseline;gap:10px;
          font:12px/1.4 ui-monospace,Menlo,monospace;letter-spacing:.05em;text-transform:uppercase;color:var(--soft);}
.ctl .val{color:var(--ink);font-weight:700;text-transform:none;letter-spacing:0;font-size:13px;}
input[type=range]{width:100%;accent-color:var(--accent);margin:0;}
.ticks{display:flex;justify-content:space-between;font:11px ui-monospace,Menlo,monospace;color:var(--soft);}
.row{display:flex;gap:8px;flex-wrap:wrap;}
button{font:12px ui-monospace,Menlo,monospace;padding:6px 11px;border:1px solid var(--rule);
       background:transparent;color:var(--ink);border-radius:5px;cursor:pointer;}
button[aria-pressed="true"]{background:var(--accent);color:var(--panel);border-color:var(--accent);}
.spec{background:#fff;color:#111;border:1px solid var(--rule);border-radius:8px;padding:18px 16px;overflow-x:auto;}
.spec div{margin:0 0 10px;}
.spec div:last-child{margin:0;}
.readout{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:12px;}
.cell{border:1px solid var(--rule);border-radius:6px;padding:9px 11px;background:var(--panel);}
.cell b{display:block;font:11px ui-monospace,Menlo,monospace;letter-spacing:.06em;
        text-transform:uppercase;color:var(--soft);font-weight:600;margin-bottom:3px;}
.cell span{font:17px ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums;}
.band{height:9px;border-radius:5px;background:linear-gradient(90deg,var(--rule) 0,var(--rule) 100%);position:relative;margin-top:6px;}
.band i{position:absolute;top:-3px;width:3px;height:15px;background:var(--accent);border-radius:2px;}
.band u{position:absolute;top:0;height:9px;background:var(--ok);opacity:.32;border-radius:5px;}
.note{border-left:3px solid var(--accent);padding-left:13px;color:var(--soft);font-size:14px;}
</style>
<div class="wrap">
  <header>
    <h1>Albo Dial</h1>
    <p class="soft">Twenty real builds &mdash; four weights &times; five contrast steps &mdash; not interpolations. Every one was built, measured and gated; the sliders swap between them. Your four-weight ruling is the weight axis.</p>
  </header>

  <div class="panel">
    <div class="ctl">
      <div class="lab"><span>Contrast</span><span class="val" id="cv"></span></div>
      <input type="range" id="c" min="0" max="4" step="1" value="0">
      <div class="ticks"><span>flat</span><span></span><span></span><span></span><span>open</span></div>
    </div>
    <div class="ctl">
      <div class="lab"><span>Weight</span><span class="val" id="wv"></span></div>
      <input type="range" id="w" min="0" max="3" step="1" value="1">
      <div class="ticks"><span>200</span><span>400</span><span>700</span><span>900</span></div>
    </div>
    <div class="ctl">
      <div class="lab"><span>Size</span><span class="val" id="sv"></span></div>
      <div class="row" id="sizes"></div>
    </div>
  </div>

  <div class="spec" id="spec"></div>

  <div class="readout">
    <div class="cell"><b>thick : thin</b><span id="r_ratio"></span></div>
    <div class="cell"><b>stem, units</b><span id="r_stem"></span></div>
    <div class="cell"><b>hairline, units</b><span id="r_hair"></span></div>
    <div class="cell"><b>dials</b><span id="r_dial" style="font-size:13px"></span></div>
  </div>

  <div class="panel">
    <h2>Against the references</h2>
    <p class="soft" id="ctx"></p>
    <div class="band" id="band"><u id="bandok"></u><i id="mark"></i></div>
    <div class="ticks"><span>1.0</span><span>2.0</span><span>3.0</span></div>
    <p class="soft">Green is where the twelve reference regulars live, 1.49 to 3.00, median 2.34.</p>
  </div>

  <p class="note">The specimen renders with your browser&rsquo;s antialiasing, not the reader&rsquo;s four grey levels, so judge SHAPE here and take the final legibility call from the 13&nbsp;px proofs. Opening the contrast is a trade against round 92&rsquo;s ruling, which floored the o&rsquo;s hairline because it was dropping to grey at 13&nbsp;pt.</p>
</div>
<script>
const M = __META__;
const W = [200,400,700,900], C = ['0','1','2','3','4'];
const SIZES = [13,17,24,40,72];
let size = 40;
const $ = id => document.getElementById(id);
const TXT = [
  "Hamburgefonstiv \\u2014 obscene goose, folly 1928",
  "The printer set the page twice, once for the proof and once for the run, and in between he changed his mind about the spacing of the capitals.",
  "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789"
];
$('sizes').innerHTML = SIZES.map(s=>`<button data-s="${s}" aria-pressed="${s===size}">${s} px</button>`).join('');
$('sizes').addEventListener('click', e => {
  const b = e.target.closest('button'); if(!b) return;
  size = +b.dataset.s;
  [...$('sizes').children].forEach(x=>x.setAttribute('aria-pressed', +x.dataset.s===size));
  draw();
});
function draw(){
  const w = W[+$('w').value], c = C[+$('c').value], k = 'w'+w+'c'+c, m = M[k];
  if(!m) return;
  $('spec').style.fontFamily = "'A"+k+"'";
  $('spec').innerHTML = TXT.map(t=>`<div style="font-size:${size}px;line-height:${size<20?1.5:1.25}">${t}</div>`).join('');
  $('cv').textContent = m.ratio.toFixed(2)+' : 1';
  $('wv').textContent = w + (w===400?'  (the regular)':'');
  $('sv').textContent = size + ' px';
  $('r_ratio').textContent = m.ratio.toFixed(2);
  $('r_stem').textContent = m.stem_u;
  $('r_hair').textContent = m.hair_u;
  $('r_dial').textContent = 'bowl hair '+m.hair+' / o floor '+m.floor;
  const pct = v => Math.max(0,Math.min(100,(v-1.0)/2.0*100));
  $('mark').style.left = pct(m.ratio)+'%';
  $('bandok').style.left = pct(1.49)+'%';
  $('bandok').style.width = (pct(3.00)-pct(1.49))+'%';
  $('ctx').textContent = m.ratio < 1.49
    ? 'Flatter than every reference regular measured. This is where Albo ships today.'
    : (m.ratio < 2.34 ? 'Inside the reference range, below their median of 2.34.'
                      : 'At or past the reference median.');
}
$('c').addEventListener('input', draw);
$('w').addEventListener('input', draw);
draw();
</script>
"""
html = HTML.replace('__FACES__', faces).replace('__META__', json.dumps(meta))
open(SP + '/iv/index.html', 'w').write(html)
print('written', round(len(html) / 1024), 'KB')
