# The instruments that decided shipped geometry

These were written in a session scratchpad — a per-session temp directory that
is deleted — and cited in `docs/*.md` and in `outlines/glyphs/*.py` as though
they were locations. **Nineteen such paths were cited on 2026-09-21 alone**,
and the shipping roman g's tail is literally the output of one of them.

That breaks `docs/albo-method.md`'s central rule in a way that is easy to miss:
*a surprising number is the instrument until proven otherwise* cannot be
executed against an instrument that no longer exists. The md landed, so it felt
done.

**Rule from here: a scratchpad script whose number reaches a doc, or whose
output reaches the font, is moved here in the same commit.** Not polished —
moved. If it is not worth twenty lines of tidying, its number is not worth
quoting.

| file | what it decided |
|---|---|
| `tailtrace.py` | the traced descender centrelines — **`G_OPEN_TAILS`**, which the shipping roman g's tail is built from (round 328) |
| `sansg.py` | the nine-face single-storey survey: the depth, tip and symmetry bands (round 328) |
| `loopwall.py` | per-angle wall thickness — overturned `cmp_aldine_g`'s two-point loop reading (rounds 338–341) |
| `gtrace.py` | the connector traced by connectivity; found the reverse bend (round 326) |
| `contrast.py` | the chamfer-ridge weight measure used across the ampersand and g work |
| `amp_measure.py` | the ampersand against its body letters and nine reference italics -- thirds, height, width, weight, contrast, fill, vertical mass; reproduces round 349's 30.3 / 57.1 / 12.6 on `ALBO_IT_AMP=a` (round 377) |
| `amp_lean.py` | the ampersand's back lean with the face's slant removed; found the shipped `g` at 18.9 degrees against Poetica-upright's 10.5 (round 377) |
| `amp_colour.py` | the `&`'s colour in running text (ink per unit advance) over the lowercase beside it at 13 and 60 px; round 377's italic read 0.82 against six references' 0.75-1.33 -- the owner's "too thin" (round 381) |
| `amp_reach.py` | the `&`'s top-right terminal: its height (right of the bowl only), its reach past the bowl, and its rise over its own E, against the reference italics and Poetica's alt051; found round 381 at 1.60 xh tall against 0.88-1.46 (round 383) |
| `amp_touch.py` | the `&` against every letter, figure and mark -- `cmp_touch.py` has no `&` in its charset (round 377) |
| `counter-bench.html` | the bench the owner dialled the counter's 393 / 19 / 17 on (round 332) |
| `r388_pair_white.py` | a pair's white as rsb + GPOS kern (HarfBuzz) + lsb; set round 388's six re-ask kerns against the bench-time fonts, and found the italic capitals' bearing-plus-kern double count |

They import each other and `render.py` by bare name, so run them from this
directory or put it on `PYTHONPATH`. They are working instruments, not library
code: read the header of the one you are about to trust.
