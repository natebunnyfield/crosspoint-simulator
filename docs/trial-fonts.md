# Fonts on trial

**REOPENED 2026-09-11 for ONE family: AtkinsonHyperlegibleNext.** Owner ruling
the same day the two-family trial below opened: *"drop lexica and atkinson
soft, add atkinson hyperlegible next at 365 weight"*. It is the one name in
`CROSSPOINT_IOS_TRIAL_FAMILIES` in `ios/CMakeLists.txt`, it is bundled for the
owner to judge on the phone, and it is not in `installed_families:`. Firmware
recipe: `lib/EpdFont/scripts/sd-fonts.yaml`, the `AtkinsonHyperlegibleNext`
entry, REWRITTEN IN PLACE -- a static 400/700 recipe on an untuned 4-slot ramp
already stood under that name, never built for a surface, and one name gets
one recipe.

| Family | What it is | License | Weight | Ramp and span |
|---|---|---|---|---|
| **AtkinsonHyperlegibleNext** | Braille Institute's own 2025 successor to Atkinson Hyperlegible -- `googlefonts/atkinson-hyperlegible-next`, the two VARIABLE TTFs in `fonts/variable/` (wght 200-800, one per posture), instanced by `build-sd-fonts.py` with fontTools. The repo has no tags and no releases, so the URLs pin commit `7925f50f` (2025-02-21, the tip of `main` that day). | SIL OFL 1.1, "Copyright 2020-2024 The Atkinson Hyperlegible Next Project Authors", no Reserved Font Name | **365 for regular and italic** (the owner's number, between the Light 300 and Regular 400 named instances). **He named no bold weight; 700 is taken** for bold and bolditalic, the Bold named instance and what every other four-style recipe uses. | `[7, 9, 11, 13, 15, 17]`, `{ascent: 1137, descent: -339}` -- Soft's, since Soft is these outlines rounded, and RE-PROBED at this weight rather than copied |

**Probed, not copied** -- hinted `x` bitmap rows at 150 DPI under the native
hinter, the grotesque bench's own probe, on the four instanced TTFs:
x-height **8/10/12/14/16/18 EXACT in all four styles** (under
`FT_LOAD_FORCE_AUTOHINT` the two 365 cuts drop slot 0 to 7 px, so the recipe
does not force it). Leading with the span 1137/-339, `advy_probe`: **22/28/34/
40/46/52** in all four styles against the tier's 23/28/34/40/46/51, drift 2 --
the same reading Soft and Lexica gave, the source metrics being the same
(x-height 496, cap 668 per 1000 em). Ascent clears the accented capitals at 862
(wght 365) / 880 (700); descent clears the plain ink at -191 / -201. Coverage:
362 codepoints, Latin-1 94/96, Latin Extended-A 93/128, 4 Greek, no Cyrillic,
no `liga` and no fi/fl outlines. No `FontDisplayNames.h` row, per the 2026-08
precedent: it sorts last in the picker under its directory name.

When it is ruled on, the list returns to empty: **promoted** means adding the
name to `installed_families:` in the firmware's `sd-fonts.yaml` and removing
it here (and a `FontDisplayNames.h` row); **declined** means deleting
`build/seedfonts/AtkinsonHyperlegibleNext` and removing the name here. The
recipe stays either way.

---

**CLOSED 2026-09-11, same day it opened -- AtkinsonHyperlegibleSoft and
LexicaUltralegible were both DECLINED.** Owner ruling: *"drop lexica and
atkinson soft, add atkinson hyperlegible next at 365 weight"*. Both names are
out of `CROSSPOINT_IOS_TRIAL_FAMILIES`, `build/seedfonts/AtkinsonHyperlegibleSoft`
and `build/seedfonts/LexicaUltralegible` are deleted, and both recipes stay in
the firmware's `sd-fonts.yaml` with their comment blocks saying declined. That
is Lexica's second ruling against a surface (the 2026-08-04 cut was the
first); Soft's first. Replaced by AtkinsonHyperlegibleNext above. The original
trial note follows.

**Was: REOPENED 2026-09-11 for TWO families: AtkinsonHyperlegibleSoft and
LexicaUltralegible.** Both are named in `CROSSPOINT_IOS_TRIAL_FAMILIES` in
`ios/CMakeLists.txt`, both are bundled for the owner to judge on the phone,
and neither is in `installed_families:`. Firmware recipe commit `89306dfd2`
(`lib/EpdFont/scripts/sd-fonts.yaml`), and the simulator's pin advanced to it.

| Family | What it is | License | 1x + 2x, 12 files | in the bundle (CPZ1) |
|---|---|---|---|---|
| **AtkinsonHyperlegibleSoft** | Namesake's rounded cut of Braille Institute's Atkinson Hyperlegible Next -- `namesakefyi/atkinson-hyperlegible-soft` tag `v1.0.0`, four RIBBI cuts of the fourteen it ships. **Not a Braille Institute release**; the Institute ships Atkinson Hyperlegible, Next and Mono and no "Soft". | SIL OFL 1.1, copyright Namesake Collaborative, no Reserved Font Name | 24,028,212 bytes raw | **7,842,044** |
| **LexicaUltralegible** | Jacob Perez's Atkinson extension, `jacobxperez/lexica-ultralegible` `v1.0.0`. S tier for one day (2026-08-03 to 08-04), buildable-only since; its cut note in the firmware's `docs/sd-card-fonts.md` asked for a fresh ruling before it goes back on any surface, and the owner's ask for this trial is that ruling -- for a TRIAL, not a promotion. | SIL OFL 1.1 | 23,689,987 bytes raw | **7,812,703** |

Together **15,654,747 bytes** in the bundle, measured with
`tools/compress_seed_fonts.py` over the two trees.

**Same ramp and span for both, on purpose.** They are one skeleton (x-height
496, cap 668, n 408 per 1000 em in both), so `sizes: [7, 9, 11, 13, 15, 17]`
and `metrics: {ascent: 1137, descent: -339}` in both recipes: the trial
compares the faces, and the fit must not be a variable in it. Measured, not
copied -- hinted `x` bitmap rows at 150 DPI with the grotesque bench's own
probe: Soft lands x-height 8/10/12/14/16/18 EXACT in all four styles; Lexica's
bold pair is exact and its regular and italic read 7/10/12/14/16/18, slot 0
one px small and unreachable under either hinter (7 pt reads 7, 8 pt reads 9).
Leading read back off the built headers: advanceY 22/28/34/40/46/52 against
the tier's 23/28/34/40/46/51, drift 2, and no span in a 1250..1558 sweep scores
lower. Soft has no `FontDisplayNames.h` row, per the 2026-08 precedent, so it
sorts last under its directory name; Lexica keeps the row it has.

When each is ruled on, the list returns to empty: **promoted** means adding
the name to `installed_families:` in the firmware's `sd-fonts.yaml` and
removing it here (and, for Soft, a `FontDisplayNames.h` row); **declined**
means deleting `build/seedfonts/<Family>` and removing the name here. The
recipes stay either way.

**Found on the way and NOT fixed here, because it is outside this ask:** the
seed tree on this Mac carries no `Doves` and no `VandenKeere`, both of which
are in `installed_families:`. The installed-but-not-bundled gate in
`ios/CMakeLists.txt` FATALs on exactly that, so a configure from this tree
refuses before it reaches either trial family. Both families' sources are in
the firmware's `local_fonts/`, so the fix is two builds at 1x and 2x, not a
ruling.

The DTLRomulus trial below is closed and unaffected.

---

**REOPENED AND CLOSED 2026-09-06, same day — DTLRomulus was PROMOTED.**
Owner ruling: *"add"*. It is in `installed_families:` in the firmware's
`sd-fonts.yaml`, its name is out of `CROSSPOINT_IOS_TRIAL_FAMILIES`, and it now
belongs on every surface. **The trial it was named for never happened**: the
build carrying it could not be archived (codesign `errSecInternalComponent` —
there is no Apple Distribution certificate on the Mac), so the ruling came from
rendered specimens rather than from the phone. It is also the first COMMERCIAL
family in `installed_families:`, so unlike the other eight it cannot be rebuilt
from a clean clone. The original trial note follows.

**Was: REOPENED 2026-09-06 for one family: DTLRomulus.** DTL Romulus — van
Krimpen's 1931 Enschede roman, digitised by Frank E. Blokland for the Dutch
Type Library — is bundled for the owner to judge on the phone and is named in
`CROSSPOINT_IOS_TRIAL_FAMILIES` in `ios/CMakeLists.txt`. It is commercial, it
is not in `installed_families:`, and it costs 10.5 MB compressed in the bundle
(37.8 MB raw, 12 files at 1x + 2x). Its sibling DTL Fleischmann was built the
same day and cut the same day, before it ever reached a build.

When it is ruled on, the list returns to empty: **promoted** means adding it to
`installed_families:` in the firmware's `sd-fonts.yaml` and removing the name
here; **declined** means deleting `build/seedfonts/DTLRomulus` and removing the
name here. The build and every measurement behind it are in the firmware repo's
`docs/dtl-trial-fonts-2026-09-06.md`.

The 2026-08 trial below is closed and unaffected.

---

Written 2026-08-23. **CLOSED 2026-08-24** — every face below has been ruled on,
`CROSSPOINT_IOS_TRIAL_FAMILIES` is empty, and nothing in the build carries an
exemption any more. This file is now the record of what happened rather than a
description of a live state; the sections below are left as they were written,
with the outcome at the top.

## The ruling (2026-08-24)

> keep almendra but add in accurate dates and authors
>
> lose arvo and the other candidate fonts

| Family | Outcome | What that meant |
|---|---|---|
| **Almendra** | **PROMOTED** | added to `installed_families:` in the firmware's `sd-fonts.yaml` — the eighth S-tier family — and its name removed from the trial list. Kept in the seed tree, and copied into `ios/seedfonts/` as well so both trees still satisfy the installed-but-not-bundled half of the gate. |
| Arvo | declined | out of the trial list, `.cpfont` tree deleted from `build/seedfonts/`, recipe and `FontDisplayNames.h` label kept |
| Merriweather | declined | same. Second ruling against it — it was already C tier from 2026-08-12 |
| IBMPlexSans | declined | same. The most expensive of the five, 4,421,311 installed bytes, because its recipe asks for Greek and Cyrillic |
| FiraSansBook | declined | same, except it never had a picker label to keep |

The declined four also came off the simulator's card (`fs_/fonts/` in the
firmware repo), which is what `install-sim-fonts.py`'s `prune_cut_families`
does on a full run — done by hand here, since a full run would have rebuilt
every tier of all eight families to change nothing.

**Measured after, on a FRESH configure** (the cache trap below is real; the
build directory is new, not reconfigured):

```
-- Seed fonts: cpz: 64 written, 0 up to date; 121,821,093 -> 36,032,290 bytes (0.296), block 32768
-- Seed fonts: 8 families, matching installed_families exactly
```

No `ON TRIAL` clause — that is the settled-tree status line, and the gate is
exactly what it was before the trial existed. The seed payload in the bundle
goes from 47,274,326 bytes (twelve families) to 36,032,290 (eight), i.e.
**−11,242,036 bytes, −23.8 %**, which is the sum of the four declined families'
own figures in the Weight table below.

**Two things the removal proved on the way**, both worth knowing:

- A card that had one of the cut families SELECTED recovers by itself. The
  simulator's persisted `sdFontFamilyName` was `FiraSansBook`, and the first
  boot after the prune logged
  `[SDFS] SD font family not found on card: FiraSansBook (clearing)` and fell
  back. Nothing had to be reset by hand.
- Promotion carries a cost the trial did not have to pay, and it is FLAGGED
  rather than fixed: Almendra is the only one of the eight still on
  `intervals: latin-ext`, so it has no arrows and no U+2212 MINUS, and it is
  now the only INSTALLED family failing the firmware's
  `test/sd_font_arrows`. Raising it to the tier's `reading` baseline costs
  4.3x its size. The measurements and the reasoning are in the firmware repo's
  `docs/sd-card-fonts.md`, under "Almendra is S tier".

---


## What was asked

Three messages the same day, each adding to the last:

> without committing it to s tier, quickly and minimally add arvo and
> merriweather and Almendra to a testflight build for my to check out

> add ibm plex sans text too.

> add fira sans book too.

Five faces, on a build, to look at. Explicitly **not** a promotion: "without
committing it to s tier" is the whole frame, and everything below follows from
taking that literally.

## The obstacle, and why the obvious two fixes are both wrong

`ios/CMakeLists.txt` gates the bundled seed tree against `installed_families`
in the firmware's `lib/EpdFont/scripts/sd-fonts.yaml`, in **both** directions:

- bundled but not installed → megabytes nothing can select (build 126 shipped
  16.2 MB of iA Writer that way);
- installed but not bundled → the firmware believes in a font the app does not
  carry (TeX Gyre Heros reached the upload step like that on 2026-08-23).

So bundling a trial face fails the configure, by design. The two reflexive
fixes are both worse than the problem:

- **Adding the five to `installed_families`** is exactly the commitment he
  withheld. That list is the S tier, and it means *every* surface — both device
  SD cards and the simulator card, not just the phone.
- **Disabling the gate** throws away a check that caught a real near-miss the
  same day it was written.

## What was done instead

A third list — `CROSSPOINT_IOS_TRIAL_FAMILIES`, in `ios/CMakeLists.txt` beside
the gate it modifies. A family named there is bundled-but-not-installed **on
purpose**. Four behaviors, all mechanical at configure time, all verified
against this tree on 2026-08-23:

| Case | Result | Verified |
|---|---|---|
| Bundled, in `installed_families` | passes | 7 S-tier families |
| Bundled, in the trial list | passes, and the status line says so | 5 trial families |
| Bundled, in **neither** | `FATAL_ERROR`, naming both lists | configured with an empty trial list — fails |
| In **both** lists | `FATAL_ERROR` — they mean opposite things | added `TeXGyreSchola` to the trial list — fails |
| In the trial list, nothing bundled | `WARNING` — a trial nobody can evaluate | added `Nonesuch` — warns |

The healthy line to look for in a configure log:

```
-- Seed fonts: 12 families — 7 matching installed_families exactly, plus 5 ON
   TRIAL (Almendra, Arvo, FiraSansBook, IBMPlexSans, Merriweather), which are
   bundled and selectable but committed to nothing
```

The contradiction check is the one that is easy to leave out and should not be.
Without it, a promotion that forgot to empty the trial list would leave a
permanent exemption sitting over a shipped family, and the next unclaimed
bundle under that name would sail straight through the gate.

**Why a trial family is selectable at all**, which is what makes a
bundle-only change sufficient: `readingfonts::offeredForReading()`
(firmware `src/ReadingFontList.cpp:33`) says yes to every family on the card
that is not a writing-only editor face and not retired — including, in its own
words, "families this project has never heard of". None of the five is in the
editor table (`src/notes/EditorFonts.h`: iAWriterQuattro, PragmataPro,
NittiTypewriter) and none is retired (`kRetired` holds only Rosarivo). So
`installed_families` governs what a card is *given*, never what the reader does
with one.

## Undoing it

Per face, when he rules:

- **Promoted** — add the name to `installed_families` in `sd-fonts.yaml`, and
  remove it from `CROSSPOINT_IOS_TRIAL_FAMILIES`. The contradiction check fails
  the build if the second half is forgotten. A promoted face should also get a
  `metrics:` span (see the measurements below) and a row in
  `src/FontDisplayNames.h`.
- **Declined** — remove the name from `CROSSPOINT_IOS_TRIAL_FAMILIES` and delete
  its directory from the seed tree. The recipe can stay in `sd-fonts.yaml`; that
  is what every other C-tier recipe does, and it costs nothing.

When the list is empty the status line goes back to "matching
installed_families exactly" and the gate is exactly what it was. That happened
on 2026-08-24 — see the ruling at the top of this file; the status line was
confirmed on a fresh configure.

**Emptying the list needs a fresh configure.** `CROSSPOINT_IOS_TRIAL_FAMILIES`
is a CMake CACHE variable, so a build directory configured while a name was in
it keeps that name after the line is deleted — the same trap that killed build
130 with a stale cached render scale. Reconfigure, or pass
`-DCROSSPOINT_IOS_TRIAL_FAMILIES=` explicitly. The ON TRIAL status line is how
you check what a given build directory actually believes.

## The five faces

All five are OFL and redistributable. Only Arvo and Fira Sans Book needed new
recipes — Merriweather, Almendra and IBM Plex Sans already had buildable ones.

| Family | Source | Styles |
|---|---|---|
| Arvo | `google/fonts` `ofl/arvo` (Anton Koovit) | four real |
| Merriweather | `SorkinType/Merriweather` | four real |
| Almendra | Google Fonts static TTFs (Ana Sanfelippo) | four real |
| IBMPlexSans | `IBM/plex` `packages/plex-sans` | four real |
| FiraSansBook | `mozilla/Fira` `otf/` | four real, mixed cuts — see below |

**"IBM Plex Sans Text" is not a thing.** `IBM/plex` ships plex-sans,
plex-serif, plex-mono, the script families and plex-sans-condensed; there is no
text-optimized cut. This is **IBM Plex Sans**, which is the reading face as
against IBM Plex Mono (already in the project as a writing-only editor face).

**Fira is the BOOK weight, and its bold is SEMIBOLD.** Fira ships Book and
Regular as separate cuts and Book is the lighter of the two — `usWeightClass`
350 against 400, `l` stem 175/1000 em against 183. Google Fonts' static set
omits Book entirely, which is why this one sources from Mozilla's tree. Fira's
name table groups Regular+Bold as its RIBBI four and files Book and SemiBold as
extra members, so the family designates no bold for Book; the pairing was
measured rather than defaulted. Fira's own Regular→Bold contrast is
183→242 = 1.32x. Against Book, SemiBold gives 175→228 = **1.30x** and Bold gives
175→242 = 1.38x. SemiBold reproduces the contrast Fira drew.

## Measured slots

Read back from the built `.cpfont` binaries, not computed from the metrics span
— `sd-fonts.yaml` records that the computed column has been wrong before
(LibrisADF predicted 34/40/46/51 and builds 34/39/45/51).

The installed tier, for comparison:

| Family | pt sizes | x-height px | advanceY px |
|---|---|---|---|
| Edgar | 12/14/16/18 | 12/14/16/18 | 34/39/45/51 |
| Coelacanth | 13/15/18/20 | 12/14/16/18 | 36/41/49/55 |
| TeXGyreSchola | 12/14/16/18 | 12/14/16/18 | 34/39/45/51 |
| LibreFranklin | 10/12/14/16 | 12/14/16/18 | 33/39/46/52 |
| LibrisADF | 12/14/16/18 | 12/14/16/18 | 34/40/46/51 |
| InknutJunicode | 10/12/14/16 | 13/15/17/19 | 32/39/45/51 |
| TeXGyreHeros | 11/12/14/16 | 12/14/16/18 | 35/39/45/51 |

The trial:

| Family | pt sizes | x-height px | advanceY px | against the tier |
|---|---|---|---|---|
| Merriweather | 10/12/13/15 | 12/14/16/18 | 34/41/44/51 | on the rhythm; leading ±1-2 px |
| **Almendra** (promoted) | 10/12/14/17 | 12/14/16/18 | 32/39/45/55 | on the rhythm; slot 3 +4 px loose — **re-measured unchanged at promotion, and no span fixes it**: `metrics:` and `line_height_scale` are both family-wide multipliers, so pulling 55 to 51 takes the two EXACT slots to 36 and 42 |
| IBMPlexSans | 12/14/16/18 | 13/15/17/20 | 33/38/43/49 | +1..+2 px large, 1-2 px tight |
| Arvo | 12/14/16/18 | 13/15/17/19 | 31/36/41/46 | +1 px large, **3-5 px tight** |
| FiraSansBook | 12/14/16/18 | 14/15/18/20 | 30/35/40/45 | +1..+2 px large, **4-6 px tight**, uneven step |

Target rhythm: x-height 12/14/16/18, advanceY 34/39/45/51.

Merriweather and Almendra land on the rhythm because their recipes already
carry tuned `metrics:` spans from earlier bench work. The other three are
deliberately **untuned** — no span was fitted, because fitting one is the work a
promotion pays for and this is a trial. Two of the three are worth knowing about
before judging them:

- **Arvo** is one pixel large *and* 3-5 px tight at every slot at once, so the
  page is both bigger and more closely set than anything installed. Much of what
  reads as a slab serif's density on that page is the leading, not the face.
- **FiraSansBook** is the furthest off, and its x-height *step* is uneven
  (14→15→18→20), so the four sizes do not read as evenly spaced the way the
  tier's do. A span would have to move both the size and the leading.

## Weight

Measured on this tree, CPZ containers at 1x + 2x (3x is not built — the render
scale ceiling is 2 since 2026-08-23):

| Family | installed | in the download |
|---|---|---|
| IBMPlexSans | 4,421,311 | 4,421,658 |
| Merriweather | 3,312,893 | 3,314,169 |
| FiraSansBook | 2,117,352 | 2,119,136 |
| Arvo | 1,390,480 | 1,391,878 |
| Almendra | 1,194,909 | 1,196,375 |
| **trial total** | **12,436,945** | **12,443,216** |
| S-tier 7, for scale | 34,837,381 | 34,833,836 |

Download ≈ installed because a CPZ container is already deflated and does not
compress again inside the zip — the trade `docs/seed-font-compression.md`
records, seen from the other side.

Against a ~42 MB baseline app that is **+11.9 MB, about +28%** — not the
+60-70% a per-family rule of thumb suggests. The three cheapest faces are Latin
only; IBM Plex Sans is the most expensive because its recipe asks for Greek and
Cyrillic as well.

## What was verified, 2026-08-23

- Desktop canary `pio run -e simulator_x3`: SUCCESS. (It compiles no
  translation unit these changes touch — a YAML recipe and an iOS-only
  `CMakeLists.txt` — so this proves only that nothing regressed.)
- iOS CMake configure with the trial tree: passes, with the ON TRIAL status
  line. All four gate behaviors exercised, including the three failure modes.
- `SD font system ready (N families discovered)` went **8 → 13** on the
  simulator card, exactly +5.
- The reading picker (Settings → Text Settings) lists all five. Note they sort
  **last**: `readingfonts::sortsBefore` orders by lineage year newest-first, and
  four of the five have no row in `src/FontDisplayNames.h` so they report year 0.
  That is convenient for a trial — the five cluster at the bottom of the list,
  visibly apart from the tier — and is the reason no display-name rows were
  added. `IBMPlexSans` and `FiraSansBook` therefore appear unspaced in the
  picker; cosmetic, and it goes away with a `FontDisplayNames.h` row if either
  is promoted. **Almendra is the exception and it is worth knowing why**: it
  DID have a row, and still sorted last, because that row dated it
  `1350 London` — an invented model year the firmware's `docs/font-dates.md`
  had flagged as uncited since 2026-08-12. The stage was struck on 2026-08-24
  when the face was promoted; it now reports 2011 and sorts **first**.
- Each face loads and renders a real book page: `[SDFS] Loaded SD card font
  family: <name>` with the matching `_14.cpfont`, five for five.

## Closing a trial leaves a stale COMPRESSED copy behind (2026-09-11)

Deleting a declined family from `build/seedfonts` is not enough: the iOS
configure compresses the tree into `build/ios-dev/seedfonts-cpz/<Family>/`
and the bundled-but-unclaimed gate lists what is THERE. After Soft and Lexica
were deleted from the seed tree the configure still refused with both names,
until their `seedfonts-cpz` directories were removed by hand. Do that as part
of closing a trial, or `rm -rf build/ios-dev`. (The trial list itself is a
CACHE variable and has the same staleness; `cmake -U CROSSPOINT_IOS_TRIAL_FAMILIES
build/ios-dev` re-reads the default, never edit the cache file.)
