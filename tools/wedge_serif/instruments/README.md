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
| `counter-bench.html` | the bench the owner dialled the counter's 393 / 19 / 17 on (round 332) |

They import each other and `render.py` by bare name, so run them from this
directory or put it on `PYTHONPATH`. They are working instruments, not library
code: read the header of the one you are about to trust.
