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

Incidence scales with the dial (0–100, default 30); the DEPTHS do not. Turning
the dial up gives an older book, not a dirtier ink.

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

`Paper Defects`, 0–100, default 30.

- iOS: a slider in the light-mode page-color drawer's **Paper** group, and a
  `PSSliderSpecifier` row in `Settings.bundle/Root.plist` bound to the SAME
  `paperDefectsPercent` key — a Settings.bundle row is a view onto a
  `NSUserDefaults` key, so this is one source of truth with two views, not two
  sources. It has to be a slider row and not the `PSMultiValueSpecifier` every
  other row uses: a multi-value row renders BLANK for a drawer value of 47.
- Desktop: `CROSSPOINT_SIM_PAPER_DEFECTS`, and `paperDefectsPercent` in
  `settings.json`.
- `CROSSPOINT_SIM_AS_SHIPPED=1` seeds 30, with the rest of the iOS defaults.

Every proof and render run needs `CROSSPOINT_SIM_DARK=0` alongside it:
`CROSSPOINT_SIM_AS_SHIPPED=1` forces DARK, and letterpress only draws on a light
page. Getting that wrong yields captures with no letterpress at all, which look
exactly like a failed feature.
