# iOS app size — where it lives and what to do about it

*Measured 2026-08-22 against `build/CrossPointX3.xcarchive` (build 126, marketing 0.1.0) and `build/export/CrossPoint X3.ipa`, the artifacts `ios/testflight.sh` last produced. Every number below is either a command output quoted here or an arithmetic combination of them; anything derived from a ratio rather than measured directly is labelled **estimated**.*

> **Superseded in part, 2026-08-23.** Sections 1-7 are the build-126 audit as
> taken and are left as taken. Two of their items have since shipped: the 3x
> tier is gone and the seed fonts are block-compressed, which together took the
> install from 329 MB to 45.8 MB. Read the dated section at the foot of this
> file before acting on any number above it.

## 1. The headline

| | bytes | note |
|---|---:|---|
| **IPA (what uploads, and what downloads)** | **88,895,697** | `ls -l "build/export/CrossPoint X3.ipa"` |
| Payload uncompressed (what installs) | 359,073,904 | `unzip -lv` footer: `359073904 / 88858747 / 75% / 152 files` |
| `.xcarchive` on disk | 343 MB | `du -sh` — the archive is the payload plus signing; `dSYMs/` is **0 bytes** |

The IPA is **not** fat. `lipo -info` reports `Non-fat file: CrossPointX3 is architecture: arm64`, `ENABLE_BITCODE = NO` (`ios/CMakeLists.txt:350`), there are no on-demand resources, and `assetutil --info Assets.car` shows a single 1024×1024 monochrome icon rendition per idiom (phone, pad) at scale 1. **App Store thinning therefore removes essentially nothing** — there are no per-device variants to strip. Treat the ~85 MiB IPA as the download, and 359 MB as the installed footprint. (The App Store re-compresses with LZFSE rather than deflate; the delta is small and unmeasured here — **estimated** within a few percent either way.)

Under Apple's 200 MB over-cellular limit, comfortably. The 359 MB *installed* number is the one an owner with a 128 GB phone notices.

### The whole bundle, compressed and uncompressed

From `unzip -lv "build/export/CrossPoint X3.ipa"`, aggregated by top-level entry:

| Entry | uncompressed | compressed | % of IPA |
|---|---:|---:|---:|
| `SeedFonts/` (108 `.cpfont`) | 338,233,138 | **76,996,008** | **86.62 %** |
| `CrossPointX3` (Mach-O) | 20,562,800 | **11,656,917** | **13.11 %** |
| `SeedBooks/` (1 epub) | 165,677 | 165,014 | 0.19 % |
| `Assets.car` | 45,272 | 13,149 | 0.015 % |
| `embedded.mobileprovision` | 14,536 | 8,548 | — |
| `_CodeSignature/` | 33,251 | 8,158 | — |
| `Settings.bundle/` | 9,688 | 2,518 | — |
| `AppIcon*.png` (2, loose) | 6,888 | 6,699 | — |
| `Info.plist`, `PkgInfo` | 2,654 | 1,736 | — |

**Two things are the app: the seeded card fonts and the compiled-in glyph tables.** Everything else in the bundle together is 242,772 compressed bytes — 0.27 %. There is nothing to win in assets, the settings bundle, or the seed book, and this document will not pretend otherwise.

## 2. The Mach-O binary: 82 % of it is font bitmaps

`size -m` on the shipped binary:

```
Segment __TEXT: 20168704
	Section __text: 2646308
	Section __const: 17172468        <-- 83.5% of __TEXT
	Section __cstring: 144202
	Section __gcc_except_tab: 60512
	... (all others together: 145,369)
Segment __DATA_CONST: 131072
Segment __DATA: 17006592   (__bss 16947776 zerofill, costs no file bytes)
Segment __LINKEDIT: 229376
```

`otool -L` lists only system dylibs. **There are no embedded frameworks or dylibs** — SDL3 is `SDL_STATIC ON` (`CMakeLists.txt:140`) and links in. `__LINKEDIT` at 229 KB and `nm | wc -l` = 698 (nearly all `U`) confirm the product is stripped, and `GCC_GENERATE_DEBUGGING_SYMBOLS = NO` in the Release config means no dSYM is produced at all (`build/CrossPointX3.xcarchive/dSYMs` is empty — worth knowing separately: **TestFlight crashes from this build cannot be symbolicated**).

### Which objects

`ar -tv` on `build/ios-dev/Release-iphoneos/libcrosspoint_core.a` (158 members, 22,819,840 bytes):

```
17006880  main.o          <-- next largest is 373,816
```

Summing non-zerofill `size -m` sections per extracted object and attributing by source path:

| Subsystem | bytes | |
|---|---:|---|
| `main.o` | **16,883,206** | 86.9 % of the library |
| firmware `src/` (activities, settings, network) | 1,406,699 | |
| `lib/Epub` | 435,701 | |
| harness + HAL (simulator repo) | 222,728 | |
| freeink-sdk UI | 163,831 | |
| `lib/EpdFont` (loader, not tables) | 89,485 | |
| `lib/GfxRenderer` | 71,563 | |
| expat (`xmltok`+`xmlparse`+`xmlrole`) | 116,405 | |
| all other vendored libs combined | ~163,000 | uzlib 7,691; miniz 1,404; InflateReader 712 |
| **core total** | **19,436,610** | |
| **libSDL3.a total** | **1,633,136** | 215 members |

19,436,610 + 1,633,136 = 21,069,746 against a binary whose non-zerofill segments total ~20.35 MB. **Almost every object in both archives lands in the binary.** See §5 — the link runs without `-dead_strip`.

### Inside `main.o`: the builtin glyph tables

Address-delta symbol sizing over `nm -n --defined-only main.o`:

```
FONT TOTAL: 16,836,051   NON-FONT: 50,565
```

**16,836,051 bytes — 81.9 % of the 20,562,800-byte shipped binary — is builtin font data**, all of it `__TEXT,__const` (`main.o` `__const` = 16,835,013). The rest of `main.o` is 4,332 bytes of `__GLOBAL__sub_I_main.cpp` plus `setup()`/`loop()`.

By kind: `Bitmaps` 14,021,133 · `Glyphs` 1,813,344 · `KernMatrix` 305,834 · italic variants 363,976 · everything else (`Intervals`, kern class maps, `Groups`, ligatures) 331,764.

**By family:**

| family | bytes | % of binary |
|---|---:|---:|
| `notosans` | 4,843,450 | 23.6 % |
| `librefranklin_reader` | 4,281,641 | 20.8 % |
| `librefranklin` (chrome) | 3,508,810 | 17.1 % |
| `nittitypewriter` | 1,898,384 | 9.2 % |
| `iawriterquattro` | 1,560,274 | 7.6 % |
| `pragmatapro` | 743,492 | 3.6 % |

**By scale tier:** 1x 2,308,074 · 2x 5,188,767 · 3x 9,339,210.

**By family × scale:**

| | 1x | 2x | 3x |
|---|---:|---:|---:|
| notosans | 518,127 | 1,419,356 | 2,905,967 |
| librefranklin_reader | 736,917 | 1,395,418 | 2,149,306 |
| librefranklin | 352,024 | 1,025,381 | 2,131,405 |
| nittitypewriter | 290,796 | 599,496 | 1,008,092 |
| iawriterquattro | 271,350 | 506,396 | 782,528 |
| pragmatapro | 138,860 | 242,720 | 361,912 |

By style: bold 6,211,058 · regular 5,809,869 · bolditalic 2,117,493 · italic 2,033,713 (the chrome faces are regular+bold only; the reader and editor faces carry all four).

**Compressibility, measured not guessed.** Deflating `__TEXT,__const` out of the binary at level 9, raw window:

```
__TEXT,__const: raw=17,172,468  deflate=10,086,218  ratio=0.587
whole binary:   raw=20,562,720  deflate=11,598,925  ratio=0.564
```

So **every uncompressed byte of glyph table removed from the binary is worth ≈0.587 compressed bytes of download.** All "est. compressed" figures below for binary-side cuts use that factor and are labelled estimated.

### Which families are compiled in, and why

`lib/EpdFont/builtinFonts/` holds 205 headers, 114 MB of source, across ten families. Only six reach this binary, because `all.h` is the gate:

- **1x, unconditional** (`all.h:5-31`, `:134-140`): iA Writer Quattro 12/14 ×4 styles; Libre Franklin 8/10/12 ×2 (chrome); Libre Franklin **Reader** 12/14/16/18 ×4; Noto Sans 8/10/12 ×2.
- **2x block** `#if CROSSPOINT_RENDER_SCALE >= 2` (`all.h:57-94`).
- **3x block** `#if CROSSPOINT_RENDER_SCALE >= 3` (`all.h:95-132`).
- Nitti Typewriter and PragmataPro come in through `main.cpp` behind `__has_include` (commercial, gitignored).

`ios/CMakeLists.txt` set `CROSSPOINT_IOS_RENDER_SCALE 3` when this was taken (2 since 2026-08-23), pushed to the library at `:242-244` as `CROSSPOINT_RENDER_SCALE=3` plus `CROSSPOINT_RENDER_SCALE_RUNTIME=1`, so **all three tiers compile in**. That is correct, not a bug: `RenderScale.h` makes the macro a *ceiling* and latches the active factor at launch from the owner's setting, and `all.h:60-77` spells out why registering the wrong tier's companions is worse than registering none.

**Note that the 1x tier cannot be dropped even though 1x is unselectable.** `ios/Settings.bundle/Root.plist` Page Sharpness now offers `Values: [3, 2]` only — the "Panel (1x)" row described in its own `FooterText` is no longer in `Titles`/`Values` (a stale footer worth fixing separately). But the hi-res companions carry bitmaps *only*; metrics come from the 1x tables (`convert-builtin-fonts.sh:441-444`), so the 1x set is structural.

## 3. The seeded card fonts: 86.6 % of the download, 94 % of the install

`build/seedfonts` → `Resources/SeedFonts/` via `ios/CMakeLists.txt:101-166`, and `ios/CrossPointFsPrep.cpp:282-334` **symlinks** each family into the emulated card's `fonts/` root rather than copying (`:305`, "Prefer a symlink"), so the install cost is the bundle once, not twice. Good.

Nine families × 4 point sizes × 3 scale tiers = 108 files, 338,233,138 bytes.

| family | uncompressed | compressed | 1x c. | 2x c. | 3x c. |
|---|---:|---:|---:|---:|---:|
| Edgar | 59,719,574 | 13,916,367 | 2,007,012 | 4,546,831 | 7,362,524 |
| TeXGyreSchola | 56,155,369 | 12,437,558 | 1,787,773 | 4,057,523 | 6,592,262 |
| Coelacanth | 53,165,265 | 12,249,463 | 1,601,566 | 4,014,222 | 6,633,675 |
| LibreFranklin | 42,598,843 | 10,329,213 | 1,503,356 | 3,349,961 | 5,475,896 |
| InknutJunicode | 27,166,827 | 6,299,124 | 890,004 | 2,057,884 | 3,351,236 |
| LibrisADF | 25,491,448 | 5,601,178 | 794,436 | 1,828,419 | 2,978,323 |
| **iAWriterDuo** | 24,821,573 | **5,406,629** | 743,093 | 1,752,658 | 2,910,878 |
| **iAWriterQuattro** | 24,535,728 | **5,399,572** | 745,272 | 1,750,512 | 2,903,788 |
| **iAWriterMono** | 24,578,511 | **5,356,904** | 736,141 | 1,737,253 | 2,883,510 |
| **tier totals** | | | **10,808,653** | **25,095,263** | **41,092,092** |
| | 28,759,836 | | 97,882,289 | 211,591,013 | |

**Added since this audit.** TeX Gyre Heros joined `installed_families` on
2026-08-23 (owner ruling, firmware `docs/sd-card-fonts.md`) and is now in the
CI seed list, so a build from that day on carries one more family than the
table above. Measured on `ios/seedfonts/TeXGyreHeros/` with the same zlib
accounting:

| family | uncompressed | compressed | 1x c. | 2x c. | 3x c. |
|---|---:|---:|---:|---:|---:|
| TeXGyreHeros | 48,778,166 | 12,214,509 | 1,777,375 | 3,989,761 | 6,447,373 |

That is +12.2 MB compressed, and it is *reachable* data — unlike the three iA
Writer families below, it is in `installed_families` and both reading surfaces
offer it. The rest of the audit's numbers are the build-126 measurement and are
left as taken.

### Duplication between compiled-in and card faces

Libre Franklin is in both — and it is **not** redundant. The compiled-in `librefranklin_reader` ramp is 12/14/16/18 (`convert-builtin-fonts.sh:74`); the card cut is 10/12/14/16. More importantly `CrossPointSettings.h:405` defaults `sdFontFamilyName` to `""`, so **a fresh install reads with the compiled-in face**, and `ios/CMakeLists.txt:246-267` records in detail what happened the last time someone removed builtin reader cuts on a safety argument: `getReaderFontId()` returned `LIBREFRANKLIN_READER_18_FONT_ID`, `drawText`'s `fontMap` lookup missed, and the page rendered **completely blank** while the firmware logged successful renders. Do not touch the compiled-in reader ramp.

### The real duplication: three card families nothing can reach

`sd-fonts.yaml:145-152` names the installed reading families — six when this audit was taken, **seven since 2026-08-23**: Edgar, Coelacanth, TeXGyreSchola, LibreFranklin, LibrisADF, InknutJunicode and TeXGyreHeros. The build this audit measured shipped **nine**. The extra three are iA Writer Duo, Mono and Quattro, and the code says plainly that none of them is reachable from the card:

- Both reading surfaces filter through one predicate. `FontSelectionActivity.cpp:135` and `EpubReaderActivity.cpp:835` each call `readingfonts::offeredForReading()`, which returns false for writing-only families (`ReadingFontList.cpp:34-39`).
- `iAWriterDuo` and `iAWriterMono` are in `FORMER_WRITING_FAMILIES` (`EditorFonts.cpp:107-112`, removed 2026-08-15) so `isWritingOnlyFamily()` returns true (`:155-164`). Not offered for reading, and no longer rows in the editor's `FAMILIES` either. **Nothing in the app can select them.**
- `iAWriterQuattro` is a live editor row with `alsoReading=false` (`EditorFonts.h:97-101`, the flag removed 2026-08-21) → also filtered out of reading. As an *editor* face it never consults the card: `EditorFonts.h:42-50` documents that a non-zero `builtinFontId` means "the card is then never consulted for it", `SIZES` is `{12, 14}` (`:36`), and both `IAWRITERQUATTRO_12/14_FONT_ID` are compiled in — confirmed by `iawriterquattro_12_*` and `_14_*` symbols in `main.o`. `resolve()` (`EditorFonts.cpp:166-176`) returns the builtin before `sdLookup` is ever called.

Those three families are **73,935,812 uncompressed / 16,163,105 compressed bytes of unreachable data** — 18.2 % of the download, 20.6 % of the install. They are in the bundle because the CI step takes a hand-typed family list (`.github/workflows/testflight-ios.yml:154-157`, `--only "${{ inputs.seed_fonts }}"`) with nothing checking it against `installed_families`.

Two surfaces *do* list the registry unfiltered and would visibly change: `src/SettingsList.h:38-50` (`buildFontFamilySetting`, all registry names) and the web font manager (`CrossPointWebServer.cpp:1751-1760`, `handleFontList`). If either is reachable, the owner will see three rows disappear.

### `.cpfont` bitmaps are stored uncompressed

`fontconvert_sdcard.py:4` — *"Outputs binary .cpfont files containing glyph metadata and **uncompressed** 2-bit bitmaps."* Confirmed by measurement: `LibreFranklin/3x/LibreFranklin_16.cpfont` is 9,613,668 bytes, byte entropy **2.448 bits/byte**, 54.4 % zero bytes, and deflates to 1,665,162 (ratio 0.173). Whole tree, level 9:

```
seed tree: files=108 raw=338,233,138 deflate9=74,401,301 ratio=0.2200
```

The IPA's own zip already gets 76,996,008 for the same data, so **pre-compressing buys only ~2.6 MB of download** — but it would take the *installed* tree from 338 MB to ~74 MB. The runtime machinery already exists: `EpdFontData.h:141-147` defines `EpdFontGroup` ("a DEFLATE-compressed block of glyph bitmaps") and `:185-186` says `groups`/`groupCount` are `NULL`/`0` *for uncompressed fonts* — the built-in tables use this path through `FontDecompressor`/`InflateReader`; `SdCardFont` simply does not emit or read it.

## 4. SDL3 — already trimmed, with one option that does nothing

`CMakeLists.txt:139-159` turns off shared, tests, examples, install, audio, camera, haptic, HIDAPI, joystick, sensor, `SDL_RENDER_VULKAN` and `SDL_GPU_VULKAN`. libSDL3.a contributes **1,633,136 bytes** — 8 % of the binary, ~921 KB compressed (**estimated**, ×0.564).

Grouped:

| group | bytes |
|---|---:|
| surface / blit / image decode (`SDL_blit_*`, `SDL_stb`, `SDL_yuv`, RLE) | 493,609 |
| **GPU subsystem** (`SDL_gpu.o`, `SDL_gpu_metal.o`, `SDL_gpu_vulkan.o`, `SDL_shaders_gpu.o`) | **322,115** |
| core / stdlib / misc | 268,132 |
| video / UIKit / events | 199,774 |
| render backends (metal, gles2, shaders) | 188,340 |
| joystick + gamepad (with `SDL_JOYSTICK=OFF`) | 99,847 |
| audio (with `SDL_AUDIO=OFF`) | 61,319 |

**`set(SDL_GPU_VULKAN OFF CACHE BOOL "" FORCE)` at `CMakeLists.txt:159` is a no-op.** In SDL 3.4.12 `SDL_GPU_VULKAN` is not a user option — it is an internal variable set from `SDL_VIDEO_VULKAN` (`_deps/sdl3-src/CMakeLists.txt:3526-3532`, `set(SDL_GPU_VULKAN 1)`), and `SDL_VULKAN:BOOL=ON` in the cache. Proof it links: `nm -m SDL_gpu.o` shows `(undefined) external _VulkanDriver` and `SDL_gpu_vulkan.o` defines it — so the archive member is pulled unconditionally. That is **144,592 bytes of Vulkan GPU driver in an iOS binary**.

## 5. Compiler and linker flags: what is actually set

Read from `build/ios-dev/CMakeCache.txt` and the generated `crosspoint_simulator.xcodeproj/project.pbxproj` CrossPointX3 Release config:

| Setting | Value | Comment |
|---|---|---|
| `GCC_OPTIMIZATION_LEVEL` | `3` | `CMAKE_CXX_FLAGS_RELEASE:STRING=-O3 -DNDEBUG` (CMakeCache.txt:38,53) |
| `DEAD_CODE_STRIPPING` | **not set → NO** | see below |
| `OTHER_LDFLAGS` | `-lpthread -Wl,-search_paths_first -Wl,-headerpad_max_install_names` | **no `-dead_strip`** |
| `LLVM_LTO` | not set → NO | |
| `GCC_GENERATE_DEBUGGING_SYMBOLS` | `NO` | no dSYM; no crash symbolication |
| `ENABLE_BITCODE` | `NO` | dead technology, correctly off |
| `COPY_PHASE_STRIP` | `NO` | product is nonetheless stripped (`__LINKEDIT` 229 KB) |
| `ARCHS` / `ONLY_ACTIVE_ARCH` | `arm64` / `NO` | single-slice |

The default matters, so it was checked rather than assumed. In `Xcode.app/Contents/SharedFrameworks/XCBuild.framework/.../Ld.xcspec`:

```
Name = "DEAD_CODE_STRIPPING";
Type = Boolean;
DefaultValue = NO;
CommandLineArgs = { YES = ("-Xlinker", "-dead_strip"); NO = (); };
```

**The archive links without `-dead_strip`.** That is consistent with §2's observation that the summed object contributions (21.07 MB) essentially equal the binary's non-zerofill segments (20.35 MB).

`-ffunction-sections`/`--gc-sections` are the ELF spelling and do not apply; ld64 dead-strips at atom granularity with no compiler flag needed. `-Os` would not touch the glyph tables (pure `__const` data) — its whole surface is the 2,646,308-byte `__text`.

## 6. The plan, ranked by bytes saved per unit of risk

Baseline: **IPA 88,895,697** / **install 359,073,904**.

---

### A1 — Remove iA Writer Duo, Mono and Quattro from the seeded font set
**Rank 1. Best single item in the app.**

- **What.** Three of the nine `SeedFonts/` families are not in `sd-fonts.yaml:145-151`'s installed set, and no reachable code path can load them (§3, evidence chain: `ReadingFontList.cpp:34-39` → `EditorFonts.cpp:155-164` + `:107-112`; editor path short-circuits at `EditorFonts.cpp:170` via `EditorFonts.h:42-50`).
- **Measured.** −16,163,105 compressed (**−18.2 % of the IPA**), −73,935,812 installed.
- **Mechanism.** Drop them from the CI `seed_fonts` input (`.github/workflows/testflight-ios.yml:154-157`) and from the local `build/seedfonts` tree; `ios/seedfonts/` already holds exactly the correct six. Then make it un-repeatable: have `build-sd-fonts.py` or `ios/CMakeLists.txt` fail when a bundled family is absent from `installed_families`, the same shape of gate as the define-parity check at `ios/CMakeLists.txt:291-340`.
- **What breaks / what the owner notices.** Nothing in Text Settings, the in-book cycle, or the Editor Font picker — the reading list stays at six rows and iA Writer Quattro still resolves from the built-in tables at 12 and 14 pt. Two unfiltered surfaces would lose three entries: the enum built by `SettingsList.h:38-50`, and the web font manager page (`CrossPointWebServer.cpp:1751-1760`). If either is owner-facing, that is the visible change and it is arguably a fix.
- **Verify.** `unzip -l` the new IPA — no `SeedFonts/iAWriter*`. On device: Text Settings lists six families; open the Editor Font picker, choose iA Writer Quattro at 12 and 14, type, confirm the face is Quattro and not the mono fallback (`EditorFonts.cpp:178-180`).

### A2 — Fix the SDL Vulkan/GPU options
**Rank 2. Small, but a real defect.**

- **What.** `CMakeLists.txt:159` sets a variable SDL does not read (§4). `SDL_gpu_vulkan.o` links in.
- **Measured.** `SDL_gpu_vulkan.o` = 144,592 uncompressed; the whole GPU subsystem = 322,115. **Estimated** compressed: ~82 KB and ~182 KB respectively.
- **Mechanism.** Replace with `set(SDL_VULKAN OFF CACHE BOOL "" FORCE)` (kills `SDL_VIDEO_VULKAN`, hence `SDL_GPU_VULKAN`). If the renderer never uses the GPU backend, `set(SDL_GPU OFF ...)` additionally drops `SDL_gpu.o`, `SDL_gpu_metal.o` and `SDL_shaders_gpu.o` — but confirm first which driver `HalDisplay` gets, since `SDL_RENDER_GPU` is `dep_option`-ed on `SDL_GPU`.
- **What breaks.** Nothing, if the Metal or GLES2 render backend is what is in use. If `SDL_GPU=OFF` were set while the GPU render driver was live, `SDL_CreateRenderer` falls back — visible as a renderer change, not a crash.
- **Verify.** `nm libSDL3.a | grep VulkanDriver` returns nothing; `ar -tv` no longer lists `SDL_gpu_vulkan.o`; app launches and draws a page.

### A3 — Turn on `DEAD_CODE_STRIPPING`
**Rank 3. One line, effect unmeasured.**

- **What.** The link runs without `-dead_strip` (§5, `Ld.xcspec` `DefaultValue = NO`).
- **Measured.** The *cut* is unmeasured — it needs a test link. Upper bound is the non-font part of the binary: 3,726,749 uncompressed, of which `__text` is 2,646,308. **Estimated** realistic yield 150–500 KB compressed; the honest answer is "measure it".
- **Mechanism.** `set_target_properties(CrossPointX3 PROPERTIES XCODE_ATTRIBUTE_DEAD_CODE_STRIPPING "YES")` in `ios/CMakeLists.txt`, next to the other `XCODE_ATTRIBUTE_*` at `:342-364`.
- **What breaks.** Nothing user-visible. The glyph tables are all referenced by `setupDisplayAndFonts()` and are not at risk. The one hazard is any symbol reached only through Objective-C runtime lookup or `dlsym`; the harness has none — `otool -L` shows no dynamic plugin loading, and `__objc_classlist` is 240 bytes (10 classes).
- **Verify.** Diff `size -m` before/after; the delta must land in `__text`/`__cstring` and **`__TEXT,__const` must not move**. Then run the full app: library, reader at each font, editor, Wi-Fi, read-aloud.

### A4 — Drop the Noto Sans hi-res companions
**Rank 4. Best bytes-per-risk item inside the binary.**

- **What.** Noto Sans is the *coverage* face behind the chrome, not a chrome face (`convert-builtin-fonts.sh:411-417`): 2,965 codepoints against Libre Franklin's 918, reached when a title or filename carries Greek, Cyrillic or the rest of Latin Extended. It is the single largest builtin family at 4,843,450 bytes, and 4,325,323 of that is its 2x + 3x companions.
- **Measured.** −4,325,323 uncompressed; **estimated** −2,538,965 compressed (×0.587). If A5 lands first, only the 3x half remains: −2,905,967 raw / **est.** −1,705,803 compressed.
- **Mechanism.** The hi-res loop over `UI_FAMILIES` at `convert-builtin-fonts.sh:441-465` emits companions for both `librefranklin` and `notosans`; restrict it to `librefranklin`, and delete the `notosans_*_2x/3x` includes from `all.h:78-93` / `:116-131`.
- **What breaks / what the owner notices.** The fallback is **per-glyph**, not per-string: `GfxRenderer.cpp:747` and `:787` are `if (hiRes && hiRes->getGlyph(cp, style))`. So Latin chrome is untouched (Libre Franklin keeps its companions) and only the *individual characters Libre Franklin cannot draw* render 1x-replicated — blocky at Page Sharpness 3. That is Greek/Cyrillic/Latin-Ext letters inside book titles and filenames. For a mostly-Latin library this is invisible; for a Cyrillic library it is a noticeable coarsening of title text only, never of the page.
- **Verify.** A screenshot of the library screen with a Cyrillic-titled and a Greek-titled book before and after, at Sharpness 3, plus a Latin-only screen that must be byte-identical.

### A5 — Drop the 2x tier and retire the "Exact (2x)" Page Sharpness row
**Rank 5. The biggest lever left, and the first one with a real user cost.**

- **What.** Page Sharpness ships two rows, `Values: [3, 2]`. Supporting the 2x row costs a whole seed tier plus a whole builtin tier. `docs/ios-render-scale.md` already prices it at "about +53 MB of app bundle" for six families; measured today at nine, it is more.
- **Measured**, assuming A1 has landed (so only the six keepers count): seed 2x = 25,095,263 − 1,752,658 − 1,737,253 − 1,750,512 = **−19,854,840 compressed** (−78,220,624 installed). Builtin 2x tables = −5,188,767 raw, **est.** −3,045,806 compressed. **Total ≈ −22.9 MB compressed, ≈ −83.4 MB installed.**
- **Mechanism.** `CROSSPOINT_HIRES_SCALES=3` when regenerating builtin headers (`convert-builtin-fonts.sh:57`); delete the `>= 2` include block at `all.h:57-94`; change `ios/CMakeLists.txt:143`'s `foreach(_tier RANGE 2 ${...})` to seed only the ceiling tier; remove the `2` row from `ios/Settings.bundle/Root.plist`. `RenderScale.h`'s `setRenderScale()` already clamps, so a stored `2` degrades safely rather than mis-blitting — but it will silently render 1x-replicated unless the stored value is migrated to 3. **Migrate it.**
- **What breaks / what the owner notices.** The "Exact (2x) — one page pixel per screen pixel" option disappears. Per `Root.plist`'s own footer that setting exists so nothing is resampled; anyone using it is choosing un-smoothed letterforms over detail, and would be moved to Fine (3x), which is the default and has always been. This is a deliberate feature removal and needs a ruling, not an engineering decision.
- **Verify.** Settings shows one Sharpness row; a device with `renderScale=2` in its plist launches and logs no `No hi-res companion` lines (`SdCardFontManager.cpp:128`) — that log line is exactly the silent-fallback detector.

### A5′ — *(evaluated and not recommended)* Drop the 3x tier instead
Saves more: seed 3x for six keepers = **−32,393,916 compressed** (−126.4 MB installed), builtin 3x = −9,339,210 raw / **est.** −5,482,116 compressed; ≈ **−37.9 MB compressed** total. But it deletes the default row, the one the app "has always used" and the one with the most detailed letterforms, on the @3x screens the target was raised to match (`ios/CMakeLists.txt:217-225`). Listed because it was measured; do not do it.

### A6 — Compress `.cpfont` glyph groups
**Rank 6 for download, Rank 1 for installed size, and the most work.**

- **What.** Card font bitmaps are stored uncompressed (`fontconvert_sdcard.py:4`), measured at 2.448 bits/byte entropy and 54 % zero bytes (§3).
- **Measured.** Installed: 338,233,138 → **74,401,301** (deflate-9, whole tree) — **−264 MB on the owner's phone.** Download: only **−2,594,707**, because the IPA's zip already achieves 76,996,008 on the same bytes. Combined with A1 + A5 the installed tree would be roughly 74.4 × (1 − 0.219 − 0.289) ≈ **36 MB** (**estimated**, scaling by the removed fractions).
- **Mechanism.** Bump `CPFONT_VERSION`; have `fontconvert_sdcard.py` emit `EpdFontGroup` records the way the builtin converter already does; have `SdCardFont` populate `EpdFontData::groups`/`groupCount` (`EpdFontData.h:185-186`) so the existing `FontDecompressor`/`InflateReader` path takes over. The runtime side already exists and is proven on the builtin tables.
- **What breaks / what the owner notices.** Risk is **page-turn latency**, not correctness: `SdCardFont` currently reads glyph bitmaps straight from the file, and this inserts an inflate per group. `FontDecompressor` is built for exactly this (`prewarmCache`, hot-group slot, the `Stats` struct with `decompressTimeMs`), but it was tuned for an ESP32-C3 with flash-resident data, not for file-backed groups. Also: an existing card provisioned by an older build carries v-old files, so the loader must read both versions or the seeder must overwrite — `CrossPointFsPrep.cpp:179-224` already copies-and-prunes on destination mismatch, which covers it.
- **Verify.** `FontDecompressor::logStats()` across a chapter at each family; compare page-turn wall time against the current build on the same book (`ios/README.md:1189` records a 743 ms family-cycle baseline). Byte-identical page captures at Sharpness 3 for every installed family.

### Not worth doing — measured, and there is nothing there

- **Asset catalog.** 45,272 uncompressed / 13,149 compressed. One 1024×1024 monochrome PNG source (19,114 bytes on disk), two renditions (phone, pad), plus two loose 3.9 KB/3.0 KB legacy icon PNGs. Total possible saving under 20 KB.
- **`Settings.bundle`.** 9,688 / 2,518.
- **`SeedBooks`.** 165,677 / 165,014 — an epub is already a zip. Removing the sample book saves 0.19 % and costs the first-run library its only content.
- **`-Os` instead of `-O3`.** Applies to 2,646,308 bytes of `__text`; a typical `-O3`→`-Os` yield of 5–15 % is **est.** 130–400 KB uncompressed, ~75–225 KB compressed, at a cost in render-loop throughput on a path (`drawPixel`'s block loop, `MASK_PERIOD` modulo) that `docs/ios-render-scale.md` already flags as no longer folding to constants on host builds. Bad trade. Consider `-Os` on the non-rendering TUs only if ever needed.
- **LTO.** Same 2.6 MB surface; long link times on 158 + 215 objects; do `DEAD_CODE_STRIPPING` first and re-measure before considering it.
- **Bitcode.** Already `NO` and removed from the toolchain.
- **expat / uzlib / miniz.** 116,405 + 7,691 + 1,404 = 125,500 bytes total, ~71 KB compressed. `XML_GE=0` and `XML_CONTEXT_BYTES=1024` are already set in the Release defines. Nothing here.
- **Dropping compiled-in reading faces to the card.** `librefranklin_reader` is 4,281,641 bytes and looks tempting. It is the face a fresh install reads with (`CrossPointSettings.h:405` defaults `sdFontFamilyName` to `""`), and `ios/CMakeLists.txt:246-267` is a first-hand account of the blank page this caused the last time. Its hi-res companions alone (1,395,418 + 2,149,306 = 3,544,724 raw, **est.** −2,080,743 compressed) could go, at the cost of a blocky reading page on first run before any card family is chosen — which is the worst possible moment for it. Not recommended.
- **The editor's built-in faces.** iA Writer Quattro 1,560,274 + PragmataPro 743,492 + Nitti Typewriter 1,898,384 = 4,202,150 bytes. `EditorFonts.h:42-50` is explicit that these must stay compiled in; leave them. (Their 2x/3x companions go with A5 like everything else's.)

## 7. Target

| Step | IPA (bytes) | Installed (bytes) |
|---|---:|---:|
| **Today** | **88,895,697** | **359,073,904** |
| + A1 iA trio removed | 72,732,592 | 285,138,092 |
| + A2 SDL Vulkan/GPU (est.) | ~72,550,000 | ~284,816,000 |
| + A3 dead-strip (est., low end) | ~72,400,000 | ~284,600,000 |
| + A4 Noto companions (est.) | **~69,861,000** | ~280,275,000 |
| + A5 2x tier retired (est.) | **~46,960,000** | **~196,900,000** |
| + A6 compressed `.cpfont` (est.) | ~44,400,000 | **~40,000,000** |

**Realistic target without removing a feature: ~70 MB IPA (−21 %), ~280 MB installed (−22 %).** Every step there is invisible to the owner except three rows vanishing from two font-management surfaces that were listing unreachable families anyway.

**With the "Exact (2x)" Page Sharpness row retired: ~47 MB IPA (−47 %), ~197 MB installed (−45 %).** That one needs a ruling.

**With compressed card fonts on top: ~44 MB download and ~40 MB installed** — a 9× cut in the app's footprint on the phone, at the price of an inflate on the glyph path that has to be benchmarked before it can be believed.

## 8. Method, so this can be re-run

```bash
A="build/CrossPointX3.xcarchive/Products/Applications/CrossPointX3.app"
unzip -lv "build/export/CrossPoint X3.ipa"        # compressed + uncompressed, per file
size -m "$A/CrossPointX3"                          # per-section
otool -L "$A/CrossPointX3"                         # embedded dylibs (there are none)
lipo -info "$A/CrossPointX3"                       # slices (arm64 only)
xcrun assetutil --info "$A/Assets.car"             # icon renditions
ar -tv build/ios-dev/Release-iphoneos/libcrosspoint_core.a   # per-object
ar -x  build/ios-dev/Release-iphoneos/libcrosspoint_core.a main.o
nm -n --defined-only main.o                        # then size = next symbol's address - this one
```

No link map exists and none was generated (that needs a link, and this pass was read-only). Symbol-delta sizing on `main.o` is exact for the glyph tables because they are `static` arrays in a single TU with internal linkage (`__ZL…`) and nothing between them. Object-level attribution to the final binary is approximate — it is an upper bound that happens to be tight here *because* the link does not dead-strip; once A3 lands, re-measure with `-Wl,-map`.

---

**Files that would change**, for whoever picks this up: `.github/workflows/testflight-ios.yml:154-157` (A1) · `CMakeLists.txt:158-159` (A2) · `ios/CMakeLists.txt:342-364` (A3), `:97,:142-157` (A5) · `crosspoint-reader/lib/EpdFont/scripts/convert-builtin-fonts.sh:57,:441-465` and `lib/EpdFont/builtinFonts/all.h:57-131` (A4, A5) · `ios/Settings.bundle/Root.plist` (A5, and the stale 1x footer regardless) · `crosspoint-reader/lib/EpdFont/scripts/fontconvert_sdcard.py` + `lib/EpdFont/SdCardFont.cpp` + `lib/EpdFont/scripts/cpfont_version.py` (A6).

## The bundle is built from `build/seedfonts`, not `ios/seedfonts`

Recorded 2026-08-23 after it nearly shipped a family invisibly. The two trees
are NOT the same thing and both are real:

- **`ios/seedfonts/`** WAS the reference set — full, unsubsetted, and what
  `sd-fonts.yaml` means when its comment says nothing in the firmware repo can
  reach the iOS seed directory. **DELETED 2026-08-26.** It had stopped being a
  reference: it was pre-XS/XXS for every family and two point sizes behind on
  Almendra, so a build made against it looked plausible and was a fortnight out
  of date — a picker offering six slots whose lower two resolve to nothing.
  `ios/README.md`'s local-build recipe pointed at it, which is how it would have
  caught someone. Nothing unique was lost: both trees come from
  `build-sd-fonts.py`, so regenerating a reference set is one command. A stale
  reference is worse than no reference, and 428 MB worse than that on a machine
  whose disk hit 100% twice that day.
- **`build/seedfonts/`** is what actually reaches the app. `ios/CMakeLists.txt`
  copies it into `Resources/SeedFonts/`, and its files are ~10% smaller because
  they carry the subsetted charsets from the A-series cuts above.

Adding a family to the S tier therefore means building it into
`build/seedfonts` as well, at **every tier the app can render** — 1x and 2x
today, since the ceiling in `ios/CMakeLists.txt` dropped to 2 on 2026-08-23; it
was 1x/2x/3x while `renderScale` defaulted to 3, and would be again if the
ceiling went back up. TeX Gyre Heros was installed to
`ios/seedfonts` and to the card, passed every check, and would have shipped in
build 129 with the firmware believing in seven families and the bundle carrying
six. Nothing failed; the family simply would not have been there.

```bash
for sc in 1 2 3; do
  python3 <firmware>/lib/EpdFont/scripts/build-sd-fonts.py \
    --only <Family> --scale $sc --output-dir <simulator>/build/seedfonts
done
```

**That loop is correct again as of 2026-08-26, and was NOT before.** It used to
need per-family codepoint drops passed by hand — a family with a glyph that
overflows `EpdGlyph`'s uint8 width at a hi-res ppem would abort, and
`build-sd-fonts.py` renamed its output to slot names only on SUCCESS, so
fontconvert's raw ppem names survived in the tree. `InknutJunicode` shipped an L
slot that was the 7 pt slot's 2x cut, because `2 x 7 = 14` collided with a real
slot name and loaded with no error (B-039 in the firmware repo).

**And the tree this loop writes is now gated.** `tools/validate_seed_fonts.py`
runs at iOS configure time and again as a named section in `ios/testflight.sh`,
and refuses a `.cpfont` whose own header says it renders at a different size
from the one its filename claims — the exact B-039 shape — along with a missing
companion, an orphan name, a stale charset and a ramp that disagrees with
`sd-fonts.yaml`. There is no override.
[docs/seed-font-integrity-gate.md](seed-font-integrity-gate.md).

The drop tables now live in `sd-fonts.yaml` as `tier_drops:` / `hires_drops:`
and the builder applies them, so the recipe carries its own knowledge and this
loop cannot forget it. A failed build also deletes exactly what it created.
**Do not reintroduce a caller-side drop list** — that is where the knowledge was
when it failed: `scripts/install-sim-fonts.py` had held the right drop for that
family since 2026-08-20, but it writes the CARD, and nothing routed this loop
through it.

Hi-res tiers can fail on a single glyph: at 3x the 16 pt slot rasterises as
48 pt, and a glyph over 255 px in either dimension cannot be expressed by
`EpdGlyph`'s uint8 fields, so the SIZE raises a ValueError rather than
degrading. Heros needs `--drop-codepoints 0x2E3B` at 3x for exactly that
reason (its three-em dash measures 276 px); the recipe in `sd-fonts.yaml`
carries the command.

**Worth making mechanical.** The configure-time gate already fails when a
bundled family is missing from `installed_families`; the inverse check — an
`installed_families` entry with no bundled files — is the one that would have
caught this, and does not exist yet.

---

# 2026-08-23 — 3x dropped, seed fonts compressed

*Owner ruling, verbatim: "drop 3x support for now. compress fonts in ios app".
Two changes, measured together and separately. Method is §8's, with one
deliberate substitution: both arms were zipped here with `zip -r -9 -X` over a
`Payload/` directory rather than compared through two differently-produced
IPAs, so the compressor is identical on both sides. That makes the two columns
comparable to each other; it makes them ~2.8 % smaller than Apple's own
packaging, which is why the build-129 download reads 81,324,453 below and
83,643,205 in its shipped IPA (the `Symbols/` dSYM directory, another
2,605,164, sits beside `Payload/` and does not install).*

## The headline

| | installed (bytes) | download (bytes) |
|---|---:|---:|
| **build 129** — scale 3, raw `.cpfont` | **329,310,056** | **81,324,453** |
| **after** — scale 2, CPZ1 containers | **45,776,580** | **41,048,304** |
| | **−283,533,476 (−86.1 %)** | **−40,276,149 (−49.5 %)** |

Per top-level entry:

| Entry | before raw | before comp | after raw | after comp |
|---|---:|---:|---:|---:|
| `SeedFonts/` 1x (36) | 26,979,496 | 10,253,007 | 10,710,671 | 10,708,862 |
| `SeedFonts/` 2x (35) | 90,675,364 | 23,180,248 | 24,126,710 | 24,123,095 |
| `SeedFonts/` 3x (35) | 195,420,632 | 37,295,579 | — | — |
| `CrossPointX3` (Mach-O) | 15,946,912 | 10,385,403 | 10,713,656 | 6,028,259 |
| `SeedBooks/` | 165,677 | 164,969 | 165,677 | 164,969 |
| everything else | 121,975 | 45,247 | 59,866 | 23,119 |

The "everything else" row is the one place the two arms are not the same
experiment: build 129's `.app` came out of a signed archive and carries
`_CodeSignature/` and `embedded.mobileprovision`, which the unsigned
measurement build does not. That accounts for the whole 62,109-byte difference
in that row and for nothing else.

## Attribution, exactly

The two changes are separable, and the columns above add up to the byte:

**Dropping 3x** (`CROSSPOINT_IOS_RENDER_SCALE` 3 → 2, `ios/CMakeLists.txt`):

| | installed | download |
|---|---:|---:|
| the 3x seed tier, no longer bundled | −195,420,632 | −37,295,579 |
| the 3x builtin glyph tables, no longer compiled | −5,233,256 | −4,357,144 |
| | **−200,653,888** | **−41,652,723** |

The builtin half is free of any edit to the font tooling: `all.h:95-132` and
`main.cpp`'s registration block are already `#if CROSSPOINT_RENDER_SCALE >= 3`,
so lowering the ceiling removes them. This is **A5′** from §6, which that
section measured and recommended against — the ruling supersedes it, and the
seed figure it estimated at 32,393,916 for six families measures 37,295,579 for
the seven that actually shipped.

**Compressing the survivors** (CPZ1, `docs/seed-font-compression.md`):

| | installed | download |
|---|---:|---:|
| 1x + 2x seed fonts | 117,654,860 → 34,837,381 = **−82,817,479** | 33,433,255 → 34,831,957 = **+1,398,702** |

The download **grows** by 1.4 MB, and that is the deal: a container does not
compress again inside the zip, so the zip's 3.5:1 on raw `.cpfont` is traded for
keeping the same ratio on disk. 83 MB off the phone for 1.4 MB of download.

This is **A6** from §6, arrived at from the other end. A6 proposed the format
change (bump `CPFONT_VERSION`, teach `SdCardFont` to read `EpdFontGroup`s) and
priced the installed tree at ~74.4 MB for nine families. What shipped instead is
a container at the HAL's file layer, which the device never compiles and no
published font pack has to be re-emitted for — and it compresses *more*, because
it takes the 9.6 MB of glyph/interval/kern metadata with it instead of only the
bitmap section. The three rejected alternatives are priced in
`docs/seed-font-compression.md`; the one worth repeating here is that inflating
at first launch would have made the install **bigger**, because the bundle copy
cannot be deleted and `CrossPointFsPrep` symlinks rather than copies.

## What did not change

- The families are still the seven in `installed_families`, and both gates in
  `ios/CMakeLists.txt` still hold in both directions.
- `SeedBooks/`, `Assets.car` and `Settings.bundle` are byte-identical.
- The 3x seed trees are still on disk in `build/seedfonts/<Family>/3x/` and
  `build-sd-fonts.py --scale 3` still works. The tier is excluded at bundle
  time, not deleted — re-enabling it is one number, not a 40-minute
  rasterisation run. Checklist: `docs/ios-render-scale.md`.

## Still open from §6

A2 (the SDL Vulkan/GPU options) and A3 (`DEAD_CODE_STRIPPING`) are untouched by
this pass and still worth their ~250 KB. A4 landed before build 129 — the Noto
Sans hi-res companions are gone from `all.h`, which is why the build-129 Mach-O
measures 15,946,912 against this document's original 20,562,800.
