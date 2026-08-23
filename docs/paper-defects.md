# Paper defects, and the page that is the same sheet forever

Owner order, 2026-08-22: the light page should carry the marks real historical
paper carries — foxing, red rag flecks, **blue marks**, brown stains, fly specks,
wax spots — and *a given page must be the same sheet every time you turn back to
it*, including across a relaunch.

Two changes, and the second is the one with teeth. This file is the research and
the reasoning; the model is `src/PaperDefects.h` (pure, host-tested by
`tests/paper_defects_test.cpp`) and the placement is `src/HalDisplay.cpp`.

**The word is BLUE MARKS.** Blue ink, blue dye, blue rag fibre. It is not the
Mars pigment family, and the string `mars` appears nowhere in the code, the
settings strings or this document.

---

## 1. Why a page has to be one sheet

Before this change both light-mode fields seeded from `grainSeed()`, which is
deliberately re-rolled on every launch (`HalDisplay.cpp`, and a
`simreset::Registrar` re-rolls it across the iOS in-process reboot as well). That
is right for a *screen* — two runs of the app are two tubes — and exactly wrong
for a *sheet*. A book is not re-printed when you close it.

So the light page's seed is now a hash of the page's IDENTITY:

```
seed = hash3(lo32(bookKey), hi32(bookKey) ^ spineIndex, pageInSpine)
```

with `bookKey = fnv1a64(book path)`. When no identity has been published (a cold
boot into a menu, the settings screen, anything that is not a reader) the seed
falls back to `grainSeed() ^ 'PRES'`, which is exactly what shipped.

Three details are load-bearing:

- **`grainSeed()` is not mixed in at all** on the identity path. Mixing it would
  have left the headline claim false while looking like it had been addressed:
  the hash would differ per page *and* per launch.
- **FNV-1a, never `std::hash`.** `Epub`'s cache key uses
  `std::hash<std::string>` (`lib/Epub/Epub.h:46`), which is
  implementation-defined — libc++ and libstdc++ disagree, so a desktop build and
  an iOS build of the same book would print it on different paper. A 12-line
  constexpr FNV-1a in the firmware's `lib/hal/HalGPIO.h` makes determinism a
  property this change owns rather than one it borrows.
- **`(spine, page)` IS the ordinal.** The EPUB reader paginates one `Section` at
  a time and has no book-cumulative page number; `pageCount` is a watermark, not
  a count. The pair is exact where the watermark is not.

Nothing clears the latch. Walk out of a book into a menu and the menu keeps the
last page's sheet rather than snapping back to the launch seed — cheaper (no
field rebuild on every menu entry) and truer: you did not put the book down on
different paper.

**Why this is provable at all.** In light mode with letterpress on, the phosphor
grain pass is skipped, so a light page is fully determined by the page seed and
nothing else random survives. Capture page N, kill the process, relaunch, revisit
N: the frames are byte-identical, with no `CROSSPOINT_SIM_GRAIN_SEED` pinning.

## 2. What the defects are

Six types. Each is a per-channel MOD multiplier folded into the sheet field, so
one texture, one upload, one draw — and they inherit the page seed through the
same cache key.

| Defect | Mechanism | Appearance | Tint at full depth |
|---|---|---|---|
| **Foxing** | Iron-gall/metallic specks in the furnish oxidising, plus fungal (*Aspergillus*, *Chaetomium*) staining around them. Needs damp; hence the edge bias — the block's edges take up humidity first. | Rust-brown, clustered, ragged-edged, edge-biased | `(1.00, 0.93, 0.86)` |
| **Red rag flecks** | Shives: undigested dyed rag from the beater. Pre-1850 European stock is recycled cloth, and a red thread survives the rag engine as a short elongated fleck. | Tiny elongated dyed fibres, oriented | `(1.00, 0.90, 0.90)` |
| **Blue marks** | Two sources with one look: blue rag fibre (indigo/woad-dyed linen) surviving the beater, and blue writing-ink or laundry-blue offset. Papermakers added smalt or Prussian blue to counter the yellow cast, so blue in the sheet is often deliberate and unevenly dispersed. | Small marks and short fibres, cool | `(0.92, 0.94, 1.00)` |
| **Brown stains** | Tannin migration from board or leather, and old water damage: a tide line with a soft interior. | Large, soft, low-contrast | `(0.97, 0.92, 0.85)` |
| **Fly specks** | Insect frass. Genuinely near-black, genuinely tiny, and the reason this layer needs its own floor. | Hard-edged near-black dots | achromatic, deep |
| **Wax spots** | Candle wax and sebum, which make the sheet locally translucent so it reads slightly darker against the ground behind it. | Soft, very shallow, larger | achromatic, shallow |

Four more were appended on 2026-08-22 with the raised ceiling — see §6.

## 2b. The dial's two halves (2026-08-22)

Owner order, after seeing a render: *"raise the defect ceiling so 100% is
actually distracting. be sure to include examples of flecks and marks and other
paper making realism."*

The complaint was measured, and it was right. At dial 100 the strongest mark on
a 792×528 sheet moved a pixel by about **36 of 255** across a soft bloom. The
brief for the two ends is `30` = "happens occasionally and not every page" and
`100` = "distracting and not very legible"; 30 was already right and 100 was
nowhere near.

Those two ends pull opposite ways, so the dial is now **two terms** and only one
of them is new:

```
incidence(d) = d / 100                          the shipped linear law, untouched
surge(d)     = t^2,  t = (d - 50) / 50,  and EXACTLY 0 at or below d = 50
```

Everything the model already did rides `incidence`. Everything added — the deep
tints, the larger radii, the extra counts, the deeper depth range, and all four
new kinds — rides `surge`.

**Why the square, and why it starts at 50.** A straight ramp from 50 is already
half strength at 75; the owner's word for the top is a *quarter* of the dial.
`surge(75) = 0.25`, `surge(90) = 0.64`, `surge(100) = 1`, so three quarters of
the travel happens in the top quarter, which is where he asked for it.

**Why "exactly 0" matters more than "small".** Because `surge` is identically
zero through the lower half, the model emits the *same mark list, byte for byte*,
that shipped — at every dial from 0 to 50, including the default 30. That is not
an intention, it is checked: `tests/paper_defects_test.cpp` carries six FNV-1a
checksums of the composited sheet (tooth + marks, 420×300, seed `0x5EED1234`)
frozen off commit `28029d1` **before a line of the new model was written**, and
asserts them at dials 0/10/20/30/40/50. A checksum re-derived from the new code
would agree with itself no matter what moved; these do not.

The verified delta at dial 30 is therefore **zero on every byte**.

### What actually rose, on all three axes

| Axis | At `surge` 0 | At `surge` 1 |
|---|---|---|
| Tint | `KindInfo::tint` — the shipped column, unmoved | `KindInfo::tintDeep`, lerped per mark |
| Size | `radiusMin..radiusMax` | `radiusMin..radiusMaxDeep`, roughly 2× the top |
| Count | `countAt100 × d/100`, rounded | plus `countSurge × surge`, floor + a per-page Bernoulli on the fraction |
| Depth | `0.55 + 0.45u` | `0.72 + 0.28u` — the floor rises, the top stays 1.0 |

**The tint had to travel rather than be scaled.** Deep foxing is a rust brown.
The shipped tint is `(1.00, 0.93, 0.86)`, whose red deficit is exactly zero, so
*any* scalar multiple of that deficit vector is a neon orange — no amount of
"more depth" can reach brown from there. A second tint per kind, interpolated,
is the only way the hue arrives somewhere real.

**The fractional counts are a per-page Bernoulli, not a rounding.** A kind whose
expectation is 0.4 marks then "happens occasionally and not every page" — the
owner's own phrase, applied at the top of the dial to the rare damage kinds. It
is safe to do this only for the surge term, because the surge term is zero
through the frozen half.

### Measured, at dial 100, 792×528, repo-default palette

| Kind | Peak channel shift, before | after |
|---|---|---|
| foxing | ≈36 | **179** |
| red rag | | **170** |
| blue mark | | **143** |
| brown stain | | **142** |
| fly speck | | **238** |
| wax spot | | **42** (deliberately the shallow end — wax is translucency) |
| shive | | **206** |
| set-off | | **82** (deliberately the shallow end — it is a ghost) |

Whole page against the same page at dial 0: mean channel delta **14.2 / 255**,
**29.6%** of pixels changed by more than 4 levels. At dial 30 the same figures
are 0.062 and 0.44%.

## 3. Safety, which is the part with teeth

### 3a. Its own floor

`letterpress::kMinMultiplier = 0.25f` exists *specifically* to forbid specks —
its comment reads "Never take a texel out entirely; a black speck is a defect,
not impression." A fly speck IS the thing that comment forbids. So the defect
layer gets `paperdefects::kMinMultiplier` (lower, and applied per channel) and
its own function. It never rides `sheetToothMultiplierAt`, and the letterpress
floor is not touched.

### 3b. The budget is SHARED, so defects take headroom rather than a fresh grant

`letterpress::paperBudget()` returns the largest MEAN paper darkening the live
palette can take before 7:1 breaks. The tooth already spends against it. If the
defect layer computed its own `coverage × (1 − m̄) ≤ budget` it would be
individually safe and jointly over.

So defects get what is LEFT:

```
remaining = max(0, paperBudget − clampedToothAmp/2)
```

and `clampedToothAmp` reproduces the tooth's clamp exactly — including the fact
that **the clamp is conditional**. `Letterpress.h` clamps only when
`budget < 0.5`; above that the tooth is not clamped at all. Computing `remaining`
as though the clamp always bit would assert a bound the tooth does not obey in
the ≥0.5 regime. `tests/paper_defects_test.cpp` sweeps **both regimes
explicitly** rather than sampling and hoping.

When a palette sits at the floor, `remaining` is 0 and the defects vanish. That
is correct, and it is the same structural posture the tooth already has.

### 3b-bis. The bound was never what made the marks faint (2026-08-22)

This is the honest re-derivation the raised ceiling rests on, and it overturns
the assumption the first version of this feature was tuned under.

The budget is denominated in **mean luminance darkening over the whole sheet**.
Measured on a 792×528 sheet at dial 100, the SHIPPED table spent:

```
total bound = 0.00038      (brown stain 72%, foxing 16%, fly speck 7%, wax 4%, rest ~1%)
```

against what the palettes actually leave:

| Palette | `paperBudget` | tooth's share | `remainingPaperBudget` |
|---|---|---|---|
| black on white | 0.7000 | 0.0150 | **0.6850** |
| repo default (2D2D2D on FBFBF9) | 0.4980 | 0.0150 | **0.4830** |
| iron gall on rag | 0.4386 | 0.0150 | **0.4236** |
| sepia ink on tan | 0.3169 | 0.0150 | **0.3019** |
| latte | 0.0093 | 0.0186 | **0.0000** |

So on the repo default the layer was spending **1/1270th** of its allowance. The
budget clamp had never once bitten. The marks were faint because their *tints*
were faint — a taste decision — not because the safety argument made them faint.

The structural reason sparse deep marks are cheap: the bound is
`area × profileMean × depth × lumDeficit / (w·h)`. A fly speck is near-black
(`lumDeficit` 0.90) and 2 px across, so twenty-four of them cost 0.00026. What
costs is *area*: the largest-area kinds dominate the bill at dial 100.

**After the raise, at dial 100:** total bound **0.0577**, measured mean
darkening **0.0461** (792×528, seed `0xABCDEF01`).
Still **10× inside** what the repo default leaves and **6× inside** sepia.
The clamp continues not to bite on any palette with real headroom, and the
ceiling is therefore set by TASTE — which is the honest thing to say about it.

### 3b-ter. The ceiling IS palette-dependent, and it always was

The brief asked for a palette-dependent ceiling if the honest bound would not
let 100 be distracting on a tight palette. It already is one, and no new
mechanism was needed: `remainingBudget` is per-palette and `generate()` scales
every mark's depth by `remaining / bound`. So the same dial 100 is

- **loud** on black-on-white and the repo default (0.68 / 0.48 remaining, no
  scaling at all — the marks render at full strength);
- **restrained** on a tight palette, scaled down continuously;
- **absent** on latte, whose budget is 0.0093 and which the tooth alone
  exhausts. The layer vanishes rather than taking the page under 7:1.

The worst case the sweep finds at dial 100 *where marks were actually painted*
is **7.002:1** — on latte, at the (strength, tooth) combination that leaves it a
sliver of headroom. That figure is the clamp binding tightly rather than loosely,
which is exactly what it should do: it spends the last of the allowance and
stops at the floor.

### 3c. The bound is an upper bound, and it is enforced in the model

Each mark carries an analytic upper bound on the mean luminance darkening it
contributes:

```
bound_m = (π · rx · ry · profileMean[kind] · depth · lumDeficit(tint)) / (w · h)
```

`profileMean` is the mean of the mark's radial profile over its own footprint —
exactly 1/3 for the quartic bump `(1−u²)²` every soft mark uses, 0.85 for the
fly speck's hard-edged disc. `generate()` sums those, and if the sum exceeds
`remaining` it scales every mark's depth by `remaining / bound`. The actual
rendered darkening is then ≤ the bound by four independent margins:

1. overlapping multiplicative marks satisfy `(1−a)(1−b) ≥ 1 − a − b`, so the sum
   over-counts;
2. foxing's ragged-edge noise only ever REDUCES the profile;
3. the per-channel floor clamp only ever RAISES the multiplier;
4. ink masking only ever raises it further.

So the safety argument is a proof about the model rather than an assertion in a
comment, and the test measures the rasterized mean as well, to catch a bound that
is right on paper and wrong in code.

### 3d. Ink masks defects

The defect multiplier lerps to 1.0 as inkness → 1: `m' = 1 − (1−m)·(1−inkness)`.
Physically right — ink is printed *on* the paper — and it is what protects
legibility at every dial setting.

### 3e. OFF is bit-exact

Dial 0 generates zero marks, so the field is byte-for-byte the sheet tooth alone.
The desktop canary and every existing capture are unchanged.

## 4. Where it runs, and what that cost

The defects are folded into the SHEET field (`ensureSheetToothTexture`), at
OUTPUT size, drawn 1:1. Not baked into the framebuffer, for the ST-008 reason
that governs every field in this repo: the panel is minified to ~0.7955 on a
phone and a regular field written into the framebuffer beats against that
resample.

The field is rasterized in two passes — the tooth per pixel as before, then each
mark over its own bounding box only. Total extra work is proportional to the
marks' area, not to the sheet's, which is what makes a per-page rebuild
affordable at all.

### Negative results, recorded so they are not re-derived

- **`pixelBufSeq` is NOT the page signal.** It increments twice per displayed
  page (the 1-bit pass, then the AA compose). Keying the sheet field on it would
  regenerate a ~3.4 Mpx field twice per page turn. The sheet keys on the page
  IDENTITY and takes whatever inkness snapshot is current at that moment: one
  rebuild per page. The consequence is that defects mask against the first
  pass's glyph shapes while the compose paints slightly softer edges — a
  sub-pixel difference at glyph boundaries, under a mask that is already a fade.
- **`grainSeed()` had to LEAVE the light-mode seed** rather than be mixed with
  the page hash. See §1.
- **The panel and sheet fields are now REUSED, not destroyed and recreated.** The
  sheet already reused on a key match but destroyed on a miss; the panel field
  had no reuse at all. Both now destroy only when the dimensions change and
  otherwise `SDL_UpdateTexture` into the existing texture. A per-page rebuild is
  what made that matter.
- **The sheet field's old comment said "never per page"** and is now the
  opposite. It was rewritten rather than left lying.

## 5. The dial

`Paper Defects`, 0–100. **On iOS it is no longer a dial at all: it is frozen at
0** (owner ruling 2026-08-23, from a screenshot reading "0% (a fresh sheet)").
The model keeps its full range and its own default of 30 — this is the app's
choice, not a change to what the model considers normal.

It had two views onto one `paperDefectsPercent` key, a drawer slider and a
`PSSliderSpecifier` row (a slider and not the `PSMultiValueSpecifier` every
other row used, because a multi-value row renders BLANK for a drawer value of
47). Both are gone: the Settings row with the whole Paper Defects group, the
drawer slider with the rest of the paper instrument.

- Desktop: `CROSSPOINT_SIM_PAPER_DEFECTS`, and `paperDefectsPercent` in
  `settings.json`. **These stay** — the desktop is where the model is exercised
  and proved, and every render in this document was made through them.
- `CROSSPOINT_SIM_AS_SHIPPED=1` seeds 0, matching the frozen app.

Every proof and render run needs `CROSSPOINT_SIM_DARK=0` alongside it:
`CROSSPOINT_SIM_AS_SHIPPED=1` forces DARK, and letterpress only draws on a light
page. Getting that wrong yields captures with no letterpress at all, which look
exactly like a failed feature.


## 6. Four kinds appended, six candidates rejected (2026-08-22)

Owner: *"be sure to include examples of flecks and marks and other paper making
realism."* The brief named nine candidates. Four are in; five are out, and one
of the four was reshaped on the way. Nothing here was photographed — the tints
and sizes are CHOSEN to match what the sources describe, the same honesty
posture as `Letterpress.h`'s component table.

The bar each candidate had to clear: **(a)** real, **(b)** visible at 792×528 on
a reading page, **(c)** not already covered by an existing kind, **(d)**
expressible as a strictly-darkening per-channel multiplier — this layer composites
`SDL_BLENDMODE_MOD` and *cannot lighten anything*, which decides three of the
rejections on its own.

### In

| Kind | Shape | Mechanism, and the source it comes from |
|---|---|---|
| **shive** | hard ellipse, high aspect | An undigested bundle of fibres — a splinter of wood that survived pulping — dark brown against the sheet. The characteristic defect of mechanical/groundwood and unbleached kraft stock, and the thing "shive counting" is a standard pulp QC measure *for*. Distinct from **red rag**, which is a *dyed textile* fleck from the rag engine of a pre-1850 European mill (Hunter, *Papermaking*): different furnish, different colour, different era. This is the papermaking one the table lacked. |
| **set-off** | rotated rect, soft, striped | The trade's own word for a facing page's still-wet ink transferring to the sheet opposite. Slip-sheeting and anti-set-off spray exist because of it; it is routine in hand-press books (Gaskell, *A New Introduction to Bibliography*). Rendered as a faint block the size of a text block, striped along the short axis so it reads as ghosted *lines of type*. **This is an approximation and is labelled one**: a true ghost would need the facing page's framebuffer, which this layer does not have. |

### Out, with reasons

- **Laid pattern (chain and wire lines).** Real, and the single most recognisable
  feature of pre-1757 European paper — laid lines ~20–28 to the inch, chain lines
  ~25 mm apart (Hunter). **Rejected from this table because it is not a defect**:
  it is a property of the *stock*, uniform over the whole sheet, and its home is
  `Letterpress.h`/`LightInkPalette.h` beside the tooth and the formation, not a
  list of marks with positions. There is also a hard technical objection recorded
  here so it is not re-derived: a regular grid at roughly one line per 2–3 device
  pixels written into a full-sheet field is precisely the ST-008 moiré generator
  (the panel is minified to 0.7955 on a phone), and the measured beat amplitude
  for a regular field at that scale was 8.14 levels. If laid paper is ever wanted
  it needs its own design, at output size, with that beat measured — not a row in
  `kKinds`.
- **Watermark ghosting.** Real: a wire design sewn to the mould thins the sheet
  there. Rejected on two independent grounds. It is a **lightening** in
  transmitted light and this layer can only darken, so implementing it here would
  be physically backwards; and a watermark is one design per *mould*, so it would
  have to repeat identically across every page of a book — a book-level property,
  not a page-level one, and the seed here is `(book, spine, page)`.
- **Pin holes / needle marks.** Rejected as **already covered and out of contract**.
  At 792×528 a hole reads as a small dark dot, which is what **fly speck** already
  paints; and a hole is a *hole* — `kMinMultiplier`'s comment draws exactly that
  line ("a hole in the sheet is a different phenomenon and this is not it"). The
  drying-loft mark that *is* real and *is* distinct is the rope mark the sheet
  hung over, which is a fold line and is now out with the rest of them.
- **Deckle-edge fibre wander.** Real — the feathered thin edge left by the
  mould's frame. Rejected because the "sheet" in this simulator is the whole
  output surface and has no visible silhouette: a deckle would draw a band along
  the *bezel*, not along a page edge. It is also a thinning, i.e. a lightening.
- **A separate "tide line" kind.** Rejected as duplicate: **brown stain** is
  already tannin migration and old water damage, and a second large soft brown
  kind would be two rows painting the same page.

### The rect footprint, which is where this could have gone quietly wrong

Two of the four are rectangles, not ellipses. `markDarkeningBound` therefore takes
its footprint from `footprintFactorFor(shape)` — `π·rx·ry` for the ellipse shapes,
`4·rx·ry` for the rect ones — and `bounds()` uses the rotated-rect extent
`|rx·cosA| + |ry·sinA|` rather than the inscribed ellipse's. Getting the first
wrong understates the bound by 27%; getting the second wrong clips a straight
edge along its diagonal, which reads as a rendering artifact rather than as a bug
in a bounds function. Both profile means are closed form and both are rounded
**up**, because the bound must over-state:

```
band  = mean_u min(1, (1-u^2)/0.55) x mean_v (1-v)/2 = 0.8462 x 0.5 = 0.4231 -> 0.43
ghost = (mean_u (1-u^2)^2)^2                         = (8/15)^2      = 0.2844 -> 0.29
```


## Removed 2026-08-23: crease and clipping burn

Owner ruling: *"lose clipping burn and crease effect. anything with a long
straight line is too distracting."*

Both were appended the day before with the raised ceiling, and both were
straight lines by construction — a crease is a fold's shadow run clean across
the sheet at aspect ~1:100, and a clipping burn's entire signature is the hard
straight edge where the newsprint lay. That is exactly what the ruling names.
A blob in the margin is scenery; a line across the text block is something the
eye tracks instead of reading.

They are **removed, not disabled**. `ShapeBand` and `PlaceMargin` went with
them (nothing else used either), and `kKindCount` fell 10 → 8. A kind's integer
is not persisted, so nothing stored re-points; pages simply re-roll, which is
expected — the per-page seed is stable but the table it indexes changed.

The ruling is now enforced as a **property of the rendered sheet rather than as
the absence of two table rows**: `paper_defects_test` sweeps every dial and 40
seeds and fails if any kind produces a mark whose long axis exceeds 100 px at
an aspect ratio over 8:1. Re-adding a line-shaped defect fails that check
without anyone remembering this paragraph. Set-off is the near miss and passes
deliberately — it is a soft block the size of a facing text page at aspect
~1.6, not a line.

**Still shipping a long straight line, and NOT covered by this ruling:** the
laid-paper wires (`src/LaidStructure.h`), which are the defining structure of
the Laid Antique stock rather than a defect, and only render when that stock is
chosen. Flagged here because it plainly meets the words of the ruling; left in
because removing an opt-in stock's whole reason for existing is not what was
asked. Say the word and it goes.
