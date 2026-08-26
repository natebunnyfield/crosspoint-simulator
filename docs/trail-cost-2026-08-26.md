# What a phosphor trail costs, and what it was spending it on

2026-08-26. Measured against `2e0d5d9` (the page-fade fix from the day before),
X3, dark page, `CROSSPOINT_SIM_AS_SHIPPED=1`, `CROSSPOINT_SIM_GRAIN_SEED=7`,
render scale 2, card reseeded per run. Every figure below is measured on this
machine unless it says otherwise; nothing here is inferred from source.

The owner's ruling that framed the work, verbatim:

> *"keep refresh as high possible, 120hz is best. never shorten the window so
> that it drops frames. tell me how things could be enhanced while preserving or
> lowering resource usage."*

So the target is the **cost per present**, never the count, and no frame a
viewer could tell apart from its neighbour may be skipped.

---

## 1. The reported symptom

A dark page turn drives its own present loop for the length of the phosphor
trail. Reported: ~84 presents over 2.63 s, present #2 building the scanline
field and #3-#84 all cache hits costing 4-12 ms each in `flip`; ~38% of a core
on the desktop at scale 1 and ~35% in the iOS Simulator on Metal at scale 3.

**Nine times the pixels on a GPU for the same cost.** That is the shape of a
CPU-side cost that does not care about resolution or backend, and it was the
right thing to chase.

## 2. The leading hypothesis was WRONG, and this is the half worth keeping

**The scanline bloom's `SDL_RenderReadPixels` does not run on trail frames at
all.** It never did. `ensureScanlinesTexture` keys its cache on `pixelBufSeq`
(`src/SurfaceTube.cpp`), and a trail is by definition a run of presents during
which the framebuffer does not change, so the readback fires **once per page
turn** and is served from cache for every present after it.

Measured directly with `CROSSPOINT_SIM_LOG_TIMING=1`, one dark page turn:

```
[timing] #1 total 40.47 ms | scanlines BUILD 36.72 | readback yes 4.27 | flip 0.58
[timing] #2 total 48.02 ms | scanlines BUILD 37.74 | readback yes 5.11 | flip 0.58
[timing] #3 total  5.05 ms | scanlines cache 0.00 | readback -   0.00 | flip 4.27
[timing] #4 total  4.82 ms | scanlines cache 0.00 | readback -   0.00 | flip 4.05
   ... 78 more, every one of them `readback - 0.00` ...
```

`CLAUDE.md`'s "the readback is 2-6% of a page turn" was right, and the worry
that it was being paid 83 times over was not. Do not re-open this: the readback
is a per-PAGE cost and moving it to a shader would buy about 5 ms per page turn,
against the 830 ms this work actually recovered.

## 3. What it really was: a full framebuffer upload per present

`presentIfNeeded` called `SDL_UpdateTexture(texture, ...)` unconditionally on
every present. The 1bpp→ARGB conversion that fills `pixelBuf` correctly runs
once per page — but its RESULT was pushed to the GPU on every frame of the
trail, unchanged: 1.7 MB at 1x, 6.7 MB at 2x, **15 MB at the phone's 3x**, on
the main thread, ~80 to 160 times per page turn.

That is the resolution-independent-looking cost the symptom pointed at, and it
is resolution-independent for a boring reason: on the desktop's SOFTWARE
renderer it is a memcpy competing with a rasteriser that dominates it, and on
Metal it is a CPU→GPU staging transfer competing with almost nothing. Two
different bottlenecks that happened to land near each other.

Measured on Metal at 2x, the upload alone: **0.96 ms per present.** At the
phone's 3x that is ~2.2 ms, times ~160 presents, ~350 ms of pure upload per
dark page turn.

### The audit behind that, in full

Every per-present touch of pixel data in `presentIfNeeded`, and its verdict:

| Touch | Size | Verdict |
|---|---|---|
| `SDL_UpdateTexture(texture, …)` | whole framebuffer | **was per-present, now per-page.** Fixed. |
| `ghostPixels.assign(pixelBuf, …)` | whole framebuffer | already inside `if (contentChanged)`. Checked, not assumed — I misread the brace nesting first and had to reread it. |
| the ghost→intensity conversion loop | whole framebuffer | already inside `if (contentChanged)`. |
| `simpower::keepSleepSourceFrame` | whole framebuffer | already keyed on the seq (`SurfacePower.cpp:577`). |
| `SDL_RenderReadPixels` (scanline bloom) | whole output | already keyed on the seq. Section 2. |
| `getenv` ×6 | — | four of them per present, in the log guards. Latched. |

**After the fix a trail present touches no pixel data on the CPU at all.** It is
a render-target fade, a fill, two textured draws, a cached field composite and a
flip — all GPU work. That is the owner's *"use gpu, obviously"* satisfied by
removing the one CPU touch that was left, not by moving a computation.

## 4. The other half: 64% of the trail could not change a pixel

The accumulator is composited **MAXIMUM** over the page. It therefore stops
mattering the moment its brightest pixel, after the colour mod that paints it,
falls to or below the darkest tone the page can show — from there `max(dst,src)`
is `dst` everywhere and the frame is byte-identical to the one before it.

`accumLive` ran to `trailMs * 2.4f`, and its comment says where 2.4 came from:
"a deposit is spent once it has decayed below one 8-bit step", i.e. 10^-2.4 of
full scale. **That is the decay to invisibility against BLACK, and the trail is
never composited against black.** On the shipped dark pair (E0E0DE on 121212)
the paper is 8% of the ink, so the honest figure is ~1.04 trails.

Measured, trail 1095 ms, deposit at t=0:

| age | frames |
|---|---|
| 0 → 846 ms | 29 presents, 15 distinct pictures |
| 846 → 2628 ms | 15 presents, **1 picture** |

1782 ms of the 2628 ms trail — **64% of its wall time** — redrawing one frame.

### Why the rule is a tracked bound and not a constant

The obvious fix is to replace 2.4 with 1.04. It is not safe, and the reason is
the failure mode this repo keeps rediscovering: *the desktop canary is the
platform on which the bug cannot be reproduced.*

The fade is `dst *= (255-drop)/255` evaluated in the renderer's own arithmetic.
SDL's software blitter TRUNCATES, so the real value falls faster than a float
model — which is why the desktop measures the trail dead at 0.77 trails, ahead
of the 1.04 the model predicts. A GPU rasteriser ROUNDS TO NEAREST, and that
error compounds: `e <- e*k + 0.5` settles at `0.5*255/drop`, about 16 of 255 at
the shipped cadence. A constant tuned on the desktop ships a visible ghost to
the phone.

So `src/TrailLifetime.h` carries a scalar UPPER BOUND on the accumulator's
brightest channel, stepped with the same `drop` the texture just took and with
the half-code term included, and `accumLive` ends when that bound crosses the
per-palette invisibility threshold. `trailMs * 2.4f` stays as a backstop, so the
rule can only ever shorten the loop — a pure-black paper makes the threshold
zero and without the backstop that is a render loop with no end.
`tests/trail_lifetime_test.cpp` runs both arithmetics against the bound for 400
steps at every drop from 1 to 64.

## 5. A latent bug found on the way, and why it matters for 120 Hz

`accumLastFadeMs = now` sat ABOVE the `if (drop > 0)` guard, so a present whose
elapsed time rounded `drop` to zero **discarded that time permanently**. Nothing
decayed and the millisecond could never be recovered.

It cannot fire at 60 Hz on the shipped 1095 ms trail (dt 16 ms gives drop 8),
which is why it has never been seen — and it is exactly what raising the refresh
rate walks toward: at 120 Hz drop is 4-5, and each further doubling halves it.
The clock now advances only when the fade applied, so dt accumulates until the
fade is representable. That is also MORE accurate: one larger multiply rounds
once where several small ones round several times.

## 6. Results

Controlled A/B, three runs each, software renderer, X3 at 2x, dark, as-shipped
dials, card reseeded to the same page and polarity before every run:

| | trail presents | ms per present | CPU per dark page turn |
|---|---|---|---|
| `2e0d5d9` | 114.3 | 15.64 | **1788 ms** |
| with this work | 85.7 | 11.15 | **955 ms** |
| | −25% | −29% | **−47%** |

At one page turn every 3 s that is 60% of a core down to 32%.

### Proof that nothing visible was removed

The settled-frame gate (`tools/capture_arm.sh`) passes both polarities
unchanged: dark `53aaf43c38cc834f501525b5973d2566`, light
`3f4773ed9d77fac0da90d6d2fb4aba72`.

That gate photographs a page with no trail running, so it cannot speak for the
trail. **The trail's interior is NOT reproducible run to run** — measured: two
runs of the UNMODIFIED binary, screenshotting the same wall-clock instants, give
different mid-trail frames, because the rendered decay depends on how many
truncating fade steps the present cadence happened to fit in. An
instant-by-instant md5 gate over a trail is therefore invalid, and reading one
as a regression would be a false positive. Two observations per arm.

What is valid, and what was run: dense captures across the window the new rule
removes, in both builds, on an identically seeded card.

```
                       BASELINE (draws the trail to 5808 ms)   WITH THIS WORK
3950 ms   e3bc81d1 …                                           059ee961 …
4000 ms   6989c7d3 …                                           e3bc81d1 …
4060 ms   b546d7fd …                                           6989c7d3 …
4130 ms   b546d7fd …   <- the new rule stops here              b546d7fd …
4200 … 5850 ms  b546d7fd (14 captures, all identical)          b546d7fd
7000 ms   b546d7fd     (long after the backstop)               b546d7fd
```

The baseline reaches its final picture at 4060 ms and redraws it for the
remaining **1748 ms** of its trail. Both arms pass through the same sequence of
distinct frames and settle on the same one. The ~50 ms phase offset in which
instant each distinct frame lands on is the pre-existing cadence sensitivity
above, not the change — the same-binary control shows a larger offset.

## 7. 120 Hz

**It was not reachable, and that was a finding on its own.** `ios/Info.plist.in`
carried no `CADisableMinimumFrameDuration`, and iOS clamps every app to 60 Hz
without it whatever the panel can do. The owner's *"keep refresh as high
possible"* was therefore not being honoured on any device, at any cost.

Sequenced deliberately behind section 3: doubling the rate doubles the presents,
so lifting the cap first would have doubled the battery draw and called it an
improvement.

Three things now ship together:

1. **Both plist spellings.** Apple's ProMotion note documents
   `CADisableMinimumFrameDuration`; SDL3's own `SDL_uikitviewcontroller.m`
   tells you in a comment to use `CADisableMinimumFrameDurationOnPhone`. Exactly
   one is live, an unrecognised Info.plist key is inert, and guessing wrong is a
   silent 60 Hz cap that looks like a working feature. Both are set; both were
   verified present in the built `.app` with `PlistBuddy`.
2. **A boot log that states the truth.** `[BUILD] display: N Hz maximum, high
   frame rate DECLARED/not declared -> app may present at up to N Hz`, read from
   `UIScreen.maximumFramesPerSecond` and from the bundle's OWN Info.plist, beside
   the existing `[BUILD]` identity line. A ProMotion panel with no key and a key
   on a 60 Hz panel are indistinguishable from outside; this line is what tells
   them apart, and it is why the Air's capability is not asserted anywhere in
   this document. **Nobody has read that line on an iPhone Air yet.**
3. Nothing else. SDL's high-rate `CADisplayLink` only drives its own animation
   callback, which this app does not use — its loop is `presentIfNeeded()` +
   `SDL_Delay(1)`, paced by drawable availability.

**UNCONFIRMED on device.** What to observe on an Air: the `[BUILD] display:`
line in the log, and whether a dark page turn's trail is visibly smoother.

### The caveat, and it is real

At 120 Hz `drop` roughly halves (5 rather than 9 on the shipped trail), which
raises the rounding bound's floor (`0.5*255/drop`) from ~14 to ~25 — above the
20.5 invisibility threshold. **Section 4's saving degrades toward the backstop
at 120 Hz.** The arithmetic, at 60 Hz cadence on a phone: baseline 157 presents
per turn; with this work ~66; at 120 Hz with the bound degraded, ~317. Times a
per-present cost that is now much lower, that is still well under where it
started — but it is the reason item 1 below is ranked first.

---

## 8. Ranked list of further enhancements

**Item 3 has shipped**, and on the way it turned up something this document
should have said and could not: SDL's software renderer -- the canary and all
three Mac apps -- has no `SDL_BLENDOPERATION_MAXIMUM` and takes the ADD fallback
for both the deposit and the composite, while the phone takes MAXIMUM. Every
trail-brightness figure in this file is therefore the fallback path. See
`docs/whole-glass-crt.md` section 6.


Costs are measured where a number is given and marked as estimates otherwise.

**1. Probe the renderer's blend rounding once at startup, instead of assuming
the worst.** The `+0.5` per step in `fadePeakBound` exists only because we do
not know whether the backend truncates or rounds. Render a known value into a
1x1 target, apply one fade, read back one pixel: one 1x1 readback per process,
never per frame. On a truncating backend the bound becomes the exact float
recurrence and the trail ends at ~1.04 trails at ANY frame rate — which is
precisely what section 7's caveat needs. Estimated: restores the full section 4
saving at 120 Hz, ~40% of trail presents there. Provably invisible, so a commit
rather than a proposal. **Do this before or with any device confirmation of
120 Hz.**

**2. Move the accumulator's fade off the render-target pass.** Measured, it is
now the largest single item in a trail present: 3.19 ms of 10.98 at 2x on the
software renderer, and `SDL_SetRenderTarget` flushes the command queue twice per
present to do it. Fold the decay into the draw's `SDL_SetTextureColorMod`
instead and materialise it into the texture only when a new deposit lands — the
maths is identical (one multiply instead of many) and the intermediate
render-target passes disappear entirely. **PROPOSAL, not a commit**: the colour
mod is 8-bit, so the rounding path differs from the current one and the rendered
trail will move by a code value or two. It changes how the fade looks in the
smallest possible way, and the owner tuned that effect by eye.

**3. Size the accumulator to the OUTPUT, not to the panel.** ~~PROPOSAL~~ **DONE
2026-08-26, and it went further than this item did** -- the owner ruled that
persistence must cover the paper as well as the panel, so the accumulator is not
merely output-SIZED, it is fed by the composed glass and composited over
everything. Full record and measurements: `docs/whole-glass-crt.md`. Measured on
the canary at 2x rather than the 3x this item estimated: four times fewer pixels,
12.46 -> 8.30 ms per trail present, 544 -> 434 ms of CPU per dark page turn. The
caveat this item raised was real and was characterised rather than waved at: the
trail's decay envelope is unchanged within the run-to-run spread of a single
binary, and the settled frame is byte-identical.

**4. Give the software renderer a straight blit.** *(Partly collected by item 3:
the ACCUMULATOR'S draw is now an axis-aligned 1:1 blit and the flip fell from
8.5 ms to 1.7 ms on a trail present. The PANEL's own draw is still rotated, so
the rest of this item stands.)* The panel and the accumulator
are both drawn through `SDL_RenderTextureRotated`, which on the software backend
is the slow transform path; the `flip` is 7.9 ms of an 11.2 ms present at 2x and
this is where it goes. Pre-rotating the framebuffer during the 1bpp→ARGB
conversion (per PAGE, not per present) would make both draws axis-aligned.
Desktop only — Metal does not care — so it buys the canary and the Mac apps,
not the phone. Estimated large, unmeasured, and it touches the rotation
arithmetic that `CLAUDE.md` warns lives in two places.

**5. Work out why late-trail presents get slower.** Reproducible in the
BASELINE build and therefore not caused by any of this: about 900 ms after a
page turn the present cadence collapses from 16 ms to ~90 ms and the per-present
cost triples. Something else on the machine starts competing at a fixed offset
after a page render — a firmware background build is the obvious suspect and is
untested. Worth knowing before any further timing work, because it silently
weights every mean measured over a whole trail.

**6. Retire `2.4f`'s sibling assumptions.** Not measured, listed so it is not
re-derived: the same "decayed below one 8-bit step against black" reasoning
appears wherever a decaying layer decides it is finished. The page fade already
got its own treatment (`2e0d5d9`); the beam sweep has not been looked at.
