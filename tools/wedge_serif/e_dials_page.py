import sys, os, json, math, base64
sys.path.insert(0, '/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif')
import round12, round17, round19, round20, latin, alphabet2 as A
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
W = '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/414829eb-ff28-4317-bac9-e346395042d3/scratchpad/wedge'
p = dict(round19.DESIGN)
A.GLYPHS.update(round17.cp_glyphs(round20.SEED, round20.EVERY, round20.AMP, 1.0, None)); round17.patch_arch(1.0)
glyphs_all = round19.all_glyphs()
c0 = round19.ctx_with_cut(p); C = latin.capH(c0); XH = c0["xh"]
capbear = round20.REF["Hbear"] / 2 * C
lt, rt = round19.SIDES['e']; lsb = capbear * A.SIDE_FRACTION[lt] + 17; rsb = capbear * A.SIDE_FRACTION[rt] + 17
def e_path(deg, th, bar, end):
    round17.E_VARIANTS[0] = dict(deg=deg, bar=bar, th=th, end=end, nose='blunt')
    pen_fn = round17.pen_linear(round20.SEED, round20.EVERY, round20.AMP); post = round17.Cut(round20.SEED, 4, 3.0, 2.0, hand=False)
    polys, c = round20.draw('e', p, glyphs_all, pen_fn, post)
    band = [x for poly in polys for (x, y) in poly if -c["over_edge"] <= y <= XH + c["over_edge"]]
    xs = [x for poly in polys for (x, y) in poly]; l, r = (min(band), max(band)) if band else (min(xs), max(xs))
    adv = lsb + (r - l) + rsb; dx = lsb - l; s = 1 / XH
    d = ''.join('M' + ' '.join(f'{(x + dx) * s:.4f} {-y * s:.4f}' for x, y in poly) + 'Z' for poly in polys)
    return d, adv * s
ANG = [float(a) for a in range(0, 9)]; TH = [round(0.62 + (1.20 - 0.62) * i / 9, 2) for i in range(10)]; BAR = [0.54, 0.56, 0.58, 0.60, 0.62]; END = [305, 318, 330]
grid = {}
for a in ANG:
    for t in TH:
        for b in BAR:
            for e in END:
                d, adv = e_path(a, t, b, e); grid[f'{a:.0f}|{t:.2f}|{b:.2f}|{e}'] = [d, round(adv, 4)]
print(len(grid), 'e paths')
# base glyphs from the current build, as x-height-unit paths
f = TTFont(f'{W}/fonts/Fjord-Regular.ttf'); gs = f.getGlyphSet(); cm = f.getBestCmap(); base = {}
for ch in set("The eye of the needle, seen here; even the eleven elves were free. Hamburgefonstiv fjord reader beleaguered"):
    gn = cm.get(ord(ch))
    if gn is None: continue
    sp = SVGPathPen(gs); gs[gn].draw(TransformPen(sp, (1 / XH, 0, 0, -1 / XH, 0, 0))); base[ch] = [sp.getCommands(), gs[gn].width / XH]
page = f'''<title>Fjord e Dials</title>
<style>
:root{{--bg:#f6f3ec;--ink:#1a1814;--mute:#6f6a60;--line:#d9d2c4}}
body{{background:var(--bg);color:var(--ink);margin:0;padding:20px;font:14px/1.45 -apple-system,Helvetica,Arial,sans-serif}}
h1{{font-size:20px;font-weight:600;margin:0 0 6px}} p{{max-width:70ch;color:var(--mute);margin:0 0 12px}}
.ctl{{display:grid;grid-template-columns:auto 1fr auto;gap:8px 14px;align-items:center;background:#fff;border:1px solid var(--line);padding:12px 14px;border-radius:4px;margin-bottom:14px;max-width:560px}}
input[type=range]{{width:100%}} b.v{{font-variant-numeric:tabular-nums;min-width:5em;display:inline-block}}
.pane{{background:#fff;border:1px solid var(--line);padding:8px 12px;margin-bottom:12px;overflow-x:auto}}
svg{{display:block}} .rule{{stroke:#c9c2b6;stroke-width:0.012}} .xr{{stroke:#e2dcd0;stroke-width:0.012}}
</style>
<h1>The e, four dials</h1>
<p>Real geometry: every combination is the e drawn through the font builder (blunt nose throughout), set into words with the current build's other letters. Angle is the bar's rise left to right; thickness is the bar over the pen's own thickness at that angle; bar height is where the bar sits in the x-height (lower = bigger eye); arm length is where the lower arm stops round the bowl. The two you did not name are the ones the e still has.</p>
<div class="ctl">
 <label>angle</label><input type="range" id="a" min="0" max="8" step="1" value="5"><b class="v" id="av"></b>
 <label>thickness</label><input type="range" id="t" min="0" max="9" step="1" value="6"><b class="v" id="tv"></b>
 <label>bar height</label><input type="range" id="b" min="0" max="4" step="1" value="2"><b class="v" id="bv"></b>
 <label>arm length</label><input type="range" id="e" min="0" max="2" step="1" value="1"><b class="v" id="ev"></b>
 <label>reading size</label><input type="range" id="s" min="24" max="96" step="1" value="54"><b class="v" id="sv"></b>
</div>
<div class="pane"><svg id="big" width="900" height="420" viewBox="0 0 900 420"></svg></div>
<div class="pane"><svg id="txt" width="1600" height="420" viewBox="0 0 1600 420"></svg></div>
<script>
const GRID={json.dumps(grid, separators=(',',':'))}, BASE={json.dumps(base, separators=(',',':'))};
const ANG={json.dumps(ANG)}, TH={json.dumps(TH)}, BAR={json.dumps(BAR)}, END={json.dumps(END)};
const LINES=["The eye of the needle, seen here;","even the eleven elves were free.","Hamburgefonstiv fjord reader beleaguered"];
function key(){{return ANG[+a.value].toFixed(0)+'|'+TH[+t.value].toFixed(2)+'|'+BAR[+b.value].toFixed(2)+'|'+END[+e.value]}}
function setLine(svg,text,x0,y0,S,ep){{let x=x0,out='';for(const ch of text){{if(ch===' '){{x+=0.6*S;continue}}const g=(ch==='e')?ep:BASE[ch];if(!g)continue;out+=`<path d="${{g[0]}}" transform="translate(${{x}},${{y0}}) scale(${{S}})"/>`;x+=g[1]*S}}return out}}
function apply(){{const ep=GRID[key()];av.textContent=ANG[+a.value]+'°';tv.textContent=TH[+t.value].toFixed(2)+'× pen';bv.textContent=BAR[+b.value].toFixed(2)+' xh';ev.textContent=END[+e.value]+'°';sv.textContent=s.value+' px';
 const S=220,y0=300;big.innerHTML=`<line class="rule" x1="0" x2="900" y1="${{y0}}" y2="${{y0}}" style="stroke-width:1"/><line class="xr" x1="0" x2="900" y1="${{y0-S}}" y2="${{y0-S}}" style="stroke-width:1"/>`+setLine(big,'e eye ne',20,y0,S,ep);
 const px=+s.value,ss=px*0.415*1000/1000;const sc=px/1000*415;let o='';LINES.forEach((L,i)=>{{o+=setLine(txt,L,20,60+i*px*1.35,px*0.415,ep)}});txt.innerHTML=o;txt.setAttribute('height',Math.round(60+3*px*1.35))}}
for(const id of ['a','t','b','e','s'])document.getElementById(id).addEventListener('input',apply);apply();
</script>'''
open(f'{W}/fonts/fjord-e-dials.html', 'w').write(page); print(len(page) // 1024, 'KB')
