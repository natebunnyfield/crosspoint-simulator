# Zen page margins — how margin is accounted for, and what the top whitespace is made of

Research, 2026-08-22. Owner ask: "how is page margin accounted for should it be
5,10 or something else? are we taking out all empty space at the top of a
rendered page? let's optimize all aspects of this using md documented research."

Measured against firmware `f0b04e6cb` (clean tree) with the desktop X3
simulator (`pio run -e simulator_x3`, 528x792 window at render scale 1 —
device-exact, so every pixel number below is a firmware logical pixel unless
marked "device px"). Simulator repo: the zen work in
`ios/CrossPointIOSShim.cpp` was uncommitted when this research started and was
committed by another agent mid-research as `4f68e3b`; the
`kInkTopInsetPx`/`kInkBottomInsetPx` constants cited are unchanged between the
two states. Book: the owner's live
`wingspan-the-whole-bird.epub` (spine 3, Libre Franklin built-in family,
justified). Headless method: `CROSSPOINT_SIM_INPUT_SCRIPT` +
`CROSSPOINT_SIM_SCREENSHOTS`, 4 pages per cell, `progress.bin` pinned to the
same paragraph anchor before every run so all cells show the same content.
Phone conversion factor: 3x render presented at 0.7197 → 1 logical px = 2.159
device px (iPhone Air, X3 presentation).

## 1. Where the margins come from (verified, file:line)

| Layer | Value | Source |
|---|---|---|
| Panel viewable margin | top 9, right 3, bottom 3, left 3 | `lib/GfxRenderer/GfxRenderer.h:160-163`, oriented by `GfxRenderer.cpp:3104` |
| Owner margin | `SETTINGS.screenMargin` added to ALL FOUR sides | `src/activities/reader/EpubReaderActivity.cpp:980-984` |
| Ramp | 0..45 step 5, default 5 | `src/CrossPointSettings.h:350-357` (`SCREEN_MARGIN_MIN/MAX/STEP/DEFAULT`), picker built in `src/SettingsList.h:144-189` |
| Owner's live value | 10 (both the phone card and the desktop card) | `fs_/.crosspoint/settings.json` |

So at margin *m* the text area is `(528 − 2(3+m)) × (792 − (9+m) − (3+m))`.
Stored value is pixels, never a picker index (`SettingsList.h:126-134`).

**Changing screenMargin forces repagination.** The viewport is part of
`ReaderRenderSpec`, and "Section-cache validation keys on every field: a
section file built with a different spec is discarded and rebuilt"
(`lib/Epub/Epub/ReaderRenderSpec.h:4-6`; viewport fields filled at
`EpubReaderActivity.cpp:986-987,992`). Confirmed live: every margin run in the
matrix logged a full `[SCT] Page N processed` rebuild; the font-mirror runs
(which did not change the spec) logged `Reusing cached HTML` and no rebuild.

**Negative result — the `fontSize` JSON key is a mirror, not a dial.** Editing
`fontSize` 18→12 produced four byte-identical geometry runs; the firmware
rewrote the key back to 18. `fontSizeSlot` is the persisted truth and
`fontSize` is a derived compatibility mirror (`src/CrossPointSettings.cpp:63-74`,
`src/SdCardFontSystem.cpp:14-31`). Font-size cells below were re-run via
`fontSizeSlot` (0..3 → 12/14/16/18 pt on `BUILTIN_READER_POINT_SIZES`,
`src/ReaderFontSizes.h:24`).

## 2. Measurements

### 2a. Margin matrix at the owner's font (18 pt, slot 3)

Body pages (pages that start mid-paragraph — p3/p4 of each run). Line pitch is
45 px at 18 pt in every cell (2.5 px/pt; 30/35/40/45 px for 12/14/16/18 pt).

| margin | text width | ink L..R (measured) | ink top (measured) | design top (9+m) | extra "ascent air" | min ink-to-bottom residual | line-slot capacity floor((780−2m)/45) | chars/line (counted) |
|---|---|---|---|---|---|---|---|---|
| 0 | 522 | 4..523 | 18 | 9 | 9 | 5 | 17 | **30.5** (24–32) |
| 5 | 512 | 9..518 | 23 | 14 | 9 | 20* | 17 | **26.7** (22–30) |
| 10 | 502 | 14..514 | 28 | 19 | 9 | 15 | 16 | **26.8** (25–29) |
| 15 | 492 | 19..509 | 33 | 24 | 9 | 25* | 16 | ~26 |
| 20 | 482 | 24..505 | 38 | 29 | 9 | 29* | 16 | **26.2** (25–29) |

\* page did not fill to the last slot in the captured sample; the true floor is
design bottom + ~2 px descender slack (m0 measured 5 vs design 3; m10 measured
15 vs design 13).

Chars per line were counted by reading the rendered lines (3–6 full justified
lines per cell) — the automated column-cluster count returned word clusters,
not characters, at this size (letters merge under antialiasing; negative
result, method abandoned). Justification quantizes breaks, which is why m5 and
m10 count nearly the same while m0 clearly gains.

### 2b. Font-size sensitivity at margin 10

| slot / pt | line pitch | body-page ink top | ascent air above design 19 | chars/line |
|---|---|---|---|---|
| 0 / 12 | 30 | 25 | 6 | **~43** (counted 42–44) |
| 1 / 14 | 35 | 26 | 7 | ~35 (est., width/14.4) |
| 2 / 16 | 40 | 27 | 8 | ~30 (est.) |
| 3 / 18 | 45 | 28 | 9 | **26.8** (counted) |

The ascent air scales linearly, ≈ pt/2 px: it is the line box's slack above the
tallest glyphs, so it is a font-metric constant per size, stable to the pixel
across every page and margin measured.

### 2c. The comfort band (Bringhurst 45–75 cpl, 66 ideal)

At the owner's 18 pt, the X3's 528 px width delivers **26–30 cpl at every
margin offered** — barely 40% of ideal and under 60% of the 45-cpl floor.
Margin 0→20 moves cpl by ~4 chars; font 18→12 pt moves it by ~16. **Margin is
not the typographic lever on this panel; font size is.** Only 12 pt at margin
0–5 (~44–45 cpl) touches the band floor.

## 3. Every contributor to top whitespace (owner: "are we taking out all empty space at the top?")

For a page at margin 10, 18 pt, in firmware logical px (× 2.159 for phone
device px):

| # | Contributor | px | Removable? |
|---|---|---|---|
| 1 | `VIEWABLE_MARGIN_TOP` | 9 | Firmware constant (`GfxRenderer.h:160`); panel-edge allowance, not settable |
| 2 | `screenMargin` | 10 | Settable 0–45 (costs repagination per §1) |
| 3 | Ascent air (line-box slack above cap height) | 9 at 18 pt (6/7/8 at 12/14/16 pt) | Not without per-line cap-height metrics; it IS part of the first line's box |
| 4 | Heading `marginTop` honored at page top | **46 px at 12 pt, 68 px at 18 pt (~1.8 em)** on pages that open with a heading | Yes in principle — see below |
| 5 | (zen only) paper band above the panel | 12 pt × scale non-zen; ratio-derived in zen | Already the shim's own dial |

So body pages are already tight: 28 px total at m10/f18, of which only the
10 px owner margin is discretionary. **The real "empty space at the top" is
item 4.** `ChapterHtmlSlimParser::makePages()` adds `blockStyle.marginTop`
unconditionally (`lib/Epub/Epub/parsers/ChapterHtmlSlimParser.cpp:2340-2347`),
including when the block opens a fresh page; a new page's y starts at 0 only
via the overflow path in `addLineToPage`
(`ChapterHtmlSlimParser.cpp:2294-2306`), which mid-paragraph breaks take —
that is why body pages have no such gap. There is **no page-top margin-collapse
mechanism anywhere**: `BlockStyle::withoutTopInset()` exists
(`lib/Epub/Epub/blocks/BlockStyle.h:55-58`) but its only consumer is the image
path (`ChapterHtmlSlimParser.cpp:1263`) — verified by grep, negative result.
Classic typesetting drops space-before at the top of a page; this engine does
not.

Also measured, for honesty: the anchor page (p1) in every cell ended its ink
far above the page bottom (380 px unused at 18 pt, 566 px at 12 pt) with the
next section's heading starting the following page. No `page-break-before`
handling exists in the parser (grep negative), headings CAN sit at page bottom
(12 pt run shows one), and the residual does not scale with line height, so the
cause was not identified. Logged as an open observation; it does not affect the
margin numbers above.

## 4. The zen nested margin (phone)

Zen paints paper around the panel, and the page bitmap carries the firmware
margin inside it — two margins nested. At m10/f18 in device px: the panel's
interior contributes **60 px above the first ink** (28 logical × 2.159 = 60.4)
and **~33 px below the last line** (15–16 logical), plus **28 px each side**
(13 logical), duplicating the paper band the shim already draws outside the
panel. Cost of the duplication relative to a phone-tuned margin 0:
**~22 device px top + ~22 bottom + ~22 per side**, one text line per page
(16 → 17 slots), and ~4 cpl.

This is exactly why `kInkTopInsetPx = 60` / `kInkBottomInsetPx = 35`
(`ios/CrossPointIOSShim.cpp:761-762`, uncommitted) are what they are: this
measurement reproduces both to within measurement noise **at the shipped
config only** (margin 10, 18 pt, body page).

### Drift of the constants across the matrix (device px)

| config | true top inset | error of 60 | true bottom inset | error of 35 |
|---|---|---|---|---|
| m0 / 18 pt | 38.9 | +21 | 10.8 | +24 |
| m10 / 18 pt (shipped) | 60.4 | 0 | 32.4–34.5 | ~0 |
| m20 / 18 pt | 82.0 | −22 | 54.0 | −19 |
| m10 / 12 pt | 54.0 | +6 | 32.4 | ~0 |
| m10, heading-start page | 155–188 | −95 to −128 | — | — |

Within one config the body-page inset is stable to the pixel — constants are
exact, not approximate, as long as the config doesn't move. Heading-start
pages blow through every option below except (iii).

### Options for the placement constants, ranked honesty vs complexity

1. **(i) Keep the constants, state the tolerance** — zero complexity; exact at
   the shipped m10/f18; ±22 device px if the margin dial moves, ±6 across font
   sizes; wrong by ~100+ on heading pages (as is every static answer). Right
   answer while the phone card stays at margin 10.
2. **(ii) Derive: `(9 + screenMargin + pt/2) × 2.159` top, `(3 + screenMargin + 2) × 2.159` bottom** —
   honest to both dials. Needs `screenMargin` and `fontSizeSlot`; the card IS
   the app's Documents directory (`ios/CrossPointFsPrep.cpp:368-380`), so
   `<Documents>/.crosspoint/settings.json` is one small file read at zen
   relayout time — cheap, no new plumbing. The `pt/2` ascent-air term is
   empirical but linear and measured to the pixel (§2b).
3. **(iii) Measure from the framebuffer** — the only option that is right on
   heading pages, but the answer then changes per page, so the sheet would
   visibly re-seat on page turns. Most honest, worst behavior. Not
   recommended unless smoothed, which buys back the dishonesty.

## 5. Should screenMargin be 5, 10, or something else?

The two platforms genuinely want different values — and **they can already
have them with no code change**, because settings are per card and the phone's
card (Documents, `CrossPointFsPrep.cpp:368-380`) is a different card from the
device's SD. The "one global setting" tension is real per card but dissolves
across platforms.

- **Phone (zen)**: the paper band already supplies the outer margin, so the
  firmware margin is double-paid. **Recommend 0–5** (5 if the panel's own edge
  should never touch ink; 0 is defensible since the paper band is outside the
  panel anyway). Gain over 10: one line per page (17 vs 16 at 18 pt), +1–4
  cpl, ~22 device px back on each side. One-time cost: repagination of cached
  books on the next open (§1).
- **Device (e-ink)**: the bezel is the outer margin, but ink hard against the
  glass edge reads badly and `VIEWABLE_MARGIN_*` only guarantees 3 px. The
  17-line capacity threshold sits between m5 and m10 at 18 pt
  (floor(770/45)=17, floor(760/45)=16): **margin 5 keeps the extra line; 10
  pays a full line per page for 5 px of air**. Recommend trying 5 on the
  device card; 10 is a taste call, not a typography win.

## 6. Ranked recommendations (smallest change first — nothing implemented)

1. **Set the phone card's `screenMargin` to 5 (or 0); leave the device card at
   the owner's 10.** No code anywhere; per-card settings already support it;
   one-time repagination. Resolves most of the nested-margin cost (§4).
2. **If (1) is adopted, move the zen ink insets to derivation (option ii,
   §4)** so the placement follows the phone card's margin instead of assuming
   10: `(9+m+pt/2)·s` / `(5+m)·s`. Until then, keep the constants and record
   their tolerance (option i) — they are exact for the shipped config.
3. **On the device, drop 10 → 5** to recover the 17th line at 18 pt (§5).
4. **Firmware, only if the heading gap ever earns a work order:** suppress
   `blockStyle.marginTop` when a block opens a page
   (`ChapterHtmlSlimParser.cpp:2342` is the exact line) — recovers 46–68 px
   (~1.8 em) on every heading-start page, the single largest removable top
   whitespace. It changes pagination for every book without changing any
   `ReaderRenderSpec` field, so it REQUIRES a section-file version bump (the
   established mechanism — see the v33 note at `lib/Epub/Epub/Section.cpp:26`)
   and repaginates every cached book once. Do not do this casually.
5. **Not a margin fix, recorded for honesty:** at 18 pt this panel is at
   26–30 cpl against a 45–75 comfort band; no margin choice changes that. The
   cpl lever is font size (12 pt ≈ 43–45 cpl).

## Appendix: what was verified where

- All pixel numbers: 8 headless matrix runs (margins 0/5/10/15/20 at slot 3;
  slots 0/1/2 at margin 10), 4 screenshots each, same paragraph anchor, ink
  threshold at the measured bimodal gap (background <40, ink ≥60 luminance
  under the desktop's live CRT White palette). Character counts read off the
  rendered bitmaps.
- Desktop card state was edited during the runs and restored byte-identical
  afterwards (`settings.json`, `state.json` MD5-matched to the pre-run copies;
  `progress.bin` restored to its pre-run values spine=3/page=0/para=1/word=0;
  wingspan section cache restored at the owner's spec).
- Negative results are inline: `fontSize` mirror (§1), no page-top margin
  collapse and unused `withoutTopInset` (§3), no `page-break-before` handling
  (§3), cluster-count cpl method rejected (§2a), p1 early-break residual
  unexplained (§3).
