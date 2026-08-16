# CrossPoint X3 on iPhone — iOS harness

A native iOS target for the CrossPoint simulator, scoped to the X3 profile
(`SIMULATOR_DEVICE_X3`), portrait, CMake + SDL3.

## The model

**The iPhone impersonates X3 peripherals; it is not a new CrossPoint board.**

| Layer | Sees | Change |
|---|---|---|
| Harness (`ios/`) | touches on an on-screen button pad | new |
| Device (`HalGPIO`) | the X3's seven GPIO buttons, as SDL scancodes | none |
| Firmware | nothing iOS-specific | none |

The harness translates the first into the second by calling
`gpio.injectButtonDown/Up()` directly. Pushing synthetic `SDL_EVENT_KEY_*` was the
original design and was abandoned: `SDL_PushEvent` does not update
`SDL_GetKeyboardState`, so level reads (`isPressed`, `powerHoldDuration`) stayed
false and long-press power-off never fired. See the injection section below.
There is no `#if TARGET_OS_IPHONE` in `HalGPIO` or the firmware.

`hasTouch()` stays **false** for X3 — verified in both capability tables:

- simulator `src/BoardConfig.h:74` — `inline bool hasTouch() { return isX4Pro(); }`
- firmware SDK `freeink-sdk/.../BoardConfig.h:987` — table-driven, and the
  `XTEINK_X3` profile passes `NO_TOUCH`

Flipping it would make the firmware take X4-Pro-only paths, i.e. test a device
that does not exist. Hit-testing happens in the harness, above SDL; no coordinate
ever reaches the firmware.

## Status

The real firmware runs. `CROSSPOINT_BUILD_FIRMWARE=ON` compiles the whole source
set — 135 firmware TUs plus 20 simulator TUs — for `arm64-apple-ios`, links it
into the app, and `main()` comes from `src/simulator_main.cpp` exactly as on
desktop.

Verified on an iPhone Air simulator (`iOS 26.5`, native 1260×2736 px):

- **The library and the reader both render**, with dithered covers and the
  firmware's own 4-level grayscale.
- **All seven buttons drive the firmware.** `UP` `DOWN` `LEFT` `RIGHT` `CONFIRM`
  `BACK` `POWER` each log a clean down/up pair; CONFIRM opens a book, a
  horizontal press turns the page, BACK returns to the library.
- **1-bit fidelity is exact.** 0 of 418,176 origin-aligned 2×2 blocks are
  non-uniform, so integer scale with nearest-neighbor sampling is holding. With
  the diagnostic pattern enabled the panel contains exactly two colours.
- **Geometry.** Panel 1056×1584 px at 2×, centered, on a white field that matches
  a blank page so no panel edge is visible.

Not yet run on a physical device — no iPhone Air is paired to this Mac. It HAS
been built and run on the iOS Simulator (2026-08-15, iPhone 13 mini): the app
launches, the panel presents, and the Page Colours setting was confirmed to
reach pixels end to end — writing `panelPalettePreset` to 6 and relaunching
changed the dominant colours from `#E0E0DE on #121212` to `#33FF33 on #001A00`,
matching `PanelPalette.h` exactly. That run also logged
`scale 0.6717 (FRACTIONAL) ... filter linear`, i.e. the minified-panel bilinear
path is live on iOS.

## Build and run

```bash
cmake -B build/ios-app -G Xcode \
  -DCMAKE_SYSTEM_NAME=iOS \
  -DCMAKE_OSX_SYSROOT=iphonesimulator \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCROSSPOINT_FIRMWARE_DIR=$HOME/src/crosspoint-reader \
  -DCROSSPOINT_BUILD_FIRMWARE=ON
cmake --build build/ios-app --config Debug --target CrossPointX3
```

For a device, drop `CMAKE_OSX_SYSROOT` and add `-DCROSSPOINT_IOS_TEAM_ID=<id>`.

The first configure clones and builds SDL3 (`release-3.4.12`), which takes a few
minutes. Reuse an existing checkout with
`-DFETCHCONTENT_SOURCE_DIR_SDL3=<path>`.

Install, seed books, and launch:

```bash
xcrun simctl install <udid> build/ios-app/ios/Debug-iphonesimulator/CrossPointX3.app
cp -R $HOME/src/crosspoint-reader/fs_/books "$(xcrun simctl get_app_container <udid> com.natebunnyfield.crosspoint.x3 data)/Documents/"
xcrun simctl launch <udid> com.natebunnyfield.crosspoint.x3
```

**The app's Documents directory is the emulated SD card.** The harness
`chdir()`s there (the iOS default CWD is the read-only bundle), points
`CROSSPOINT_SIM_SD` at it, and creates `books/` on first launch. Because the
Info.plist enables file sharing and in-place document opening, the card is
browsable in the Files app as **On My iPhone → CrossPoint X3**, and dropping an
EPUB into its `books` folder — from Files, iCloud Drive, or AirDrop — is how
books get onto the phone. Firmware state lives in `.crosspoint`, dot-prefixed,
which both `HalStorage` iteration and Files keep hidden. Installs that predate
this layout (which kept the card at `Documents/fs_`) are migrated on launch:
`fs_/books` and `fs_/.crosspoint` are renamed up a level, so libraries and
reading positions survive the update.

**Fonts sideload the same way, through a visible `fonts` folder.** The firmware
scans two SD roots and merges them — `/.fonts` (hidden, preferred) and `/fonts`
(visible; `SdCardFontRegistry.h:33-34`) — but Files refuses to create or show
dot-prefixed names, so on the phone only the visible root is reachable. The
harness creates `fonts/` eagerly next to `books/`; drop a font family folder of
`.cpfont` files into it (see the firmware's `docs/sd-card-fonts.md`) and the
firmware picks it up at the next boot. Families the firmware itself downloaded
into `.fonts` earlier are moved up into `fonts/` on launch (per-family rename,
never overwriting), which also steers the firmware's future downloads to the
visible root — `defaultWriteRoot()` only prefers the hidden root while it
exists. This lives in `CrossPointFsPrep.cpp`, split from the shim so the whole
filesystem-prep path can be compiled and exercised on a desktop host.

The shipped panel shows only what the firmware draws, which means a presentation
bug has nothing to show itself against. Add
`-DCROSSPOINT_HARNESS_TEST_PATTERN=ON` for a diagnostic pattern — 1 px gratings,
a Bayer 4×4 ramp, and per-corner glyphs that identify rotation. It is a build
flag, not on-screen UI.

## Deploying without touching the Mac

**A `build-N` tag does not identify the firmware inside the build.** The tag is
created in this repo and points at whatever `main` was, but the app compiles the
firmware source set live out of `CROSSPOINT_FIRMWARE_DIR` — so two TestFlight
builds can carry materially different readers under the same simulator commit.
Builds 22 and 23 (2026-08-03) both tag `1fba621`; everything that changed between
them was firmware-side, and nothing records that. If a tester reports a
difference, the build number is the only handle you have, and it will not tell
you which reader they ran. Worth stamping the firmware `git describe` into the
build if that ever matters — see also `CROSSPOINT_RC_HASH` on the firmware side,
which has the same "clean and dirty builds are indistinguishable" property.

Signing needs the login keychain, which only a GUI Terminal session has — an
SSH shell fails at codesign with `errSecInternalComponent`. The bridge, same as
crds-ios: let AppleScript hand the command to Terminal.app, which runs it under
the logged-in user with the keychain unlocked. **The usual trigger is a Claude
session on the Mac** (crds-ios `DEPLOY_BUGS.md` D.12: "agents CAN deploy this
way") — paste [DISPATCH.md](DISPATCH.md) into one and it ships a build
end-to-end. A phone SSH client works identically:

From any phone SSH client (Terminus, Blink):

```bash
ssh <your-mac> 'osascript ~/src/crosspoint-simulator/ios/deploy.applescript'
```

That opens a Terminal tab on the Mac running
[deploy-from-repo.sh](deploy-from-repo.sh), which pulls the current branch
(`--ff-only`) and runs [testflight.sh](testflight.sh) — so a phone-fired deploy
ships what was just merged, and the result lands back on the phone as the
script's ntfy notification. KEY=VALUE arguments pass through `env` into the
Terminal subshell:

```bash
ssh <your-mac> 'osascript ~/src/crosspoint-simulator/ios/deploy.applescript "CROSSPOINT_MARKETING_VERSION=0.1.1"'
```

One-tap version, as an iOS Shortcut (crds-ios `SHORTCUTS_RECIPES.md` pattern):

| step | action | parameters |
|---|---|---|
| 1 | Run Script Over SSH | `osascript ~/src/crosspoint-simulator/ios/deploy.applescript` |
| 2 | Show Notification | "Deploy started — watch ntfy" |

Pin it to the home screen as **"X3 Deploy"**. One-time Mac setup: allow the
SSH-launched `osascript` to control Terminal (Privacy & Security → Automation —
the prompt appears on the Mac's screen the first time, so approve it while
you're at the machine), and the Mac must be logged in and unlocked when you
fire — a locked screen keeps the keychain shut.

## Controls

An on-screen pad with one control per physical X3 button — no more, no fewer.
PURE PASSTHROUGH: every control is down-on-touch and up-on-lift and nothing
else, so it carries a real hold — page-turn autorepeat and hold-to-sleep both
work exactly as on hardware. Dragging off a control cancels it. The
finger→button decisions live in `ios/PadCore.{h,cpp}`, a pure, SDL-free,
clock-free unit (`tests/pad_core_test.cpp`); the API cannot express time, so
time-based gesture invention (an earlier POWER tap-stretch held the injected
button 600 ms past the finger and read as a stuck control) cannot return
without changing that header.

Two rows on a five-column square grid (owner-approved layout 2026-08-02):

```
[Back|Select]      [Left|Right]     <- front rockers, full squares, hugging
                                       the panel's bottom edge
[Power]              [Up|Down]      <- half-height row, anchored at the screen
                                       bottom, clear of the home indicator
```

UP/DOWN are the X3's SIDE buttons (fixed page-turn pair), fused into one
rocker at the right of the bottom row; POWER sits at the left. BACK/SELECT and
LEFT/RIGHT are the FRONT buttons. Every fused pair paints as one capsule —
rounded outer corners only, a center tick marking the seam, no pinched notch
between two rounded squares. There is no grabber/drag handle any more; the pad
is fixed.

**The controls are hollow** (owner-approved 2026-08-03, after three rounds of
palette mockups). A control is a one-device-pixel stroke around nothing: the
face equals the field, so at rest the pad is seven outlines on the same tone as
the paper, and a press lays a wash inside the outline while the stroke stays
put. Both tones step *toward mid-gray* from the field — darker than the paper in
light, lighter than 121212 in dark — which is the direction with room in both
appearances; the old arrangement stepped away from the field and ran into the
4-level ceiling above white and the 18-level floor above black. The stroke is
specified in device pixels rather than points because the old `S * 0.5f` was
1.5 px at 3x and could not land on the pixel grid. Numbers, the WCAG 1.4.11
position, why the scale is signed and field-relative rather than an absolute
0–100% lightness, and the rejected alternatives are in the comment at the top of
`ios/PadPalette.h`.

**Both tones are owner-settable**, in Settings > CrossPoint X3. One preset row
sets all four at once; four pickers underneath are the manual state.

| Setting | Key | Default |
|---|---|---|
| Preset | `padContrastPreset` | Current (1) |
| Outline contrast, light | `padOutlineContrastLight` | −1 |
| Outline contrast, dark | `padOutlineContrastDark` | +1 |
| Pressed fill contrast, light | `padFillContrastLight` | −1 |
| Pressed fill contrast, dark | `padFillContrastDark` | +1 |

The four are per-appearance because light and dark have opposite headroom, and
per-role because a wash covers a whole cell where a stroke covers a line.

**The presets** are `Current` (1), `Accessible` (2), `Transparent` (3) and
`Custom` (0):

| Preset | light outline / fill | dark outline / fill | What it is |
|---|---|---|---|
| Current | −1 / −1 | +1 / +1 | The shipped look: D9D9D7 stroke and EDEDEB wash on paper (1.364:1, 1.131:1), 333333 and 202020 on ink (1.483:1, 1.150:1). The default, so an untouched install is pixel-identical to the build before presets existed. |
| Accessible | −4 / −5 | +4 / +5 | The WCAG 1.4.11 3:1 rung, measured: 929290 at 3.01:1 for both roles in light, 616161 at 3.02:1 for both in dark. |
| Transparent | 0 / 0 | 0 / 0 | Tone equals field. The controls still work; nothing is drawn. |
| Custom | the four pickers | the four pickers | Whatever was last dialled in. |

A preset **overrides** the four pickers rather than writing them, so a detour
through Accessible loses nothing and Settings.app is never displaying values the
app wrote behind its back. Upgrades are migrated once: a preset key that has
never been written, alongside any of the four holding a non-default value, is
written as Custom (`migratePadPresetForExistingCustomisation` in
`CrossPointPrefs.mm`), because defaulting an existing dial to Current would be a
setting vanishing with no message.

One signed scale for all four pickers. **0 puts the tone on the field** — 1:1,
the control draws nothing — and **±9 are the absolute gamut ends in BOTH
appearances: −9 is #000000 and +9 is #FFFFFF whether the field is paper or ink.**
The rungs between are WCAG-meaningful ratios and every row in Settings.app is
labeled with its real measured ratio against that appearance's field.

The sign stops meaning "darker/lighter" past ±1, and that is deliberate: **the
fine end lives in the field's roomy direction.** In light, +1..+8 are all darker
than the paper and run 1.300:1 down to 1.026:1; in dark, −1..−8 are all lighter
than 121212 and do the same. That direction used to run to the field's opposite
gamut end instead, which on the light side was a **dead zone**: +1..+9 spanned
FBFBF9 → FFFFFD, 1.000:1 to 1.030:1, several rows pixel-identical, while the two
rows an owner most wants to choose between — the default and invisible — were
adjacent integers. That was fixed in `258bb14`, and this file described the
broken state for some time after; `tonesDistinct` in `PadPalette.h` is now a
`static_assert` that stops it returning, with a runtime check in
`tests/pad_palette_test.cpp` alongside.

Each appearance still reaches its opposite gamut end, on exactly **one** row,
listed last after invisible: dark has always had −9 = black (1.121:1 on 121212),
and light now has +9 = white (1.036:1 on FBFBF9). Neither is high contrast —
that is how close each field already sits to that end — but each is the one tone
that vanishes into a true-black or a blown-out white page, and neither was
reachable from a row that named a ratio and never said the color. Light +9 was
1.017:1 (F9F9F7) before this; the finest light rungs are now +8, at 1.035:1
(stroke) and 1.026:1 (wash).

The tones are precomputed delta tables in `ios/PadPalette.h` (indexed by
level + 9, `static_assert`ed against the shipped ±1 tones, the four 3:1 rungs,
all eight gamut ends, the three presets, and pairwise tone distinctness) — no
sRGB luminance is computed at runtime. That header is pure — no SDL, no UIKit,
no clock, the same discipline as `PadCore.h` — so `tests/pad_palette_test.cpp`
recomputes every ratio on a host and cross-checks it against the label
`Root.plist` actually ships. Every failure mode in here is silent (a rung equal
to the field paints nothing, a mislabelled row lies to the one person the labels
are for), which is why it is a test and not a habit.

`pollPadContrast()` resolves the preset and the four levels every frame from
`NSUserDefaults` and repaints only on an edge **in the resolved levels**, the
same shape as `pollAppearance()`: Settings.app is a separate process, so a
change made there arrives with no event to hang it on, and an e-ink presentation
model cannot afford a present per frame. Edge-triggering on the resolved pair is
what makes the preset free — editing a fine picker under a non-Custom preset
changes nothing and correctly repaints nothing.

| Control | Button index |
|---|---|
| Back | `HalGPIO::BTN_BACK` |
| Select | `HalGPIO::BTN_CONFIRM` |
| Up / Down / Left / Right | `BTN_UP` `BTN_DOWN` `BTN_LEFT` `BTN_RIGHT` |
| Power | `HalGPIO::BTN_POWER` |

The controls are deliberately **unlabelled** — no glyph, no text. An earlier
revision of this table listed one per control; `paintPad` draws none.

Each control names a `HalGPIO::BTN_*` index directly and drives it through
`gpio.injectButtonDown/Up()`. Scancodes are not involved: they were the transport
while the pad injected by pushing SDL key events, and that indirection is what
broke level reads (see below). There is no HOME — `hasHomeKey()` is X4-Pro-only.
There is no control for the simulator's own SLEEP (`S`) either: that is a harness
command, not a button the hardware has.


**iPad (family 2) — IMPLEMENTED 2026-08-04** (owner-approved spec 2026-08-03,
computed mockups: the "device_mockups" artifact). `TARGETED_DEVICE_FAMILY` is
"1,2" and `layoutPad()` branches on `CrossPointAppearance_isPad()` into
`layoutPadTablet()`:

- The panel takes the full safe height, centered — no reserved bottom band.
  Centering is by construction: the tablet branch replicates HalDisplay's
  manual fit over the full safe height, then sets top+bottom insets that
  sandwich the panel exactly, so HalDisplay's own fit lands on the same scale
  and its top-margin term collapses to the band edge.
- Front rockers move to the side margins, vertically centered to the screen:
  Back|Select in the left margin, Left|Right in the right (thumb height when
  gripping the tablet's sides).
- The bottom row keeps its screen-bottom anchor in the same margin columns:
  Power bottom-left, Up|Down rocker bottom-right.
- Cell = min(60pt, margin fit): 60pt everywhere except iPad mini portrait
  (54pt — its 108pt margin holds a two-cell rocker exactly, flush to both
  edges). The phone's kPipLift / kTopReserve / chassis gap do not apply — the
  pad is beside the page, not under it.
- Portrait stays the only orientation, now made legal on iPad by
  `UIRequiresFullScreen` in Info.plist (a portrait-only iPad app without it
  fails App Store validation over Split View). The spec's iPad-mini-landscape
  0.875x row stays theoretical until landscape is ever enabled.

Verified 2026-08-04 on iPad Pro 13-inch (M5) and iPad mini (A17 Pro)
simulators (iOS 26.5): panel centered at 2x panel px (1x pt on the 2x glass),
hi-res LibreFranklin 2x companion loaded, rockers/Power/Up|Down placed as
above on both frames, and a scripted `injectButton` press navigated Home —
touch hit-testing itself is PadCore + the rects, covered by
`tests/pad_core_test.cpp`. Not yet exercised with a real finger.

### The page's ink and paper

**The two tones the page is drawn in are owner-settable**, in Settings >
CrossPoint X3 > Page Colours (added 2026-08-15). One preset row selects both
appearances; four hex fields underneath are the manual state.

| Setting | Key | Default |
|---|---|---|
| Palette | `panelPalettePreset` | Default (1) |
| Ink, light | `panelInkLight` | `2D2D2D` |
| Paper, light | `panelPaperLight` | `FBFBF9` |
| Ink, dark | `panelInkDark` | `E0E0DE` |
| Paper, dark | `panelPaperDark` | `121212` |

| Preset | light ink / paper | dark ink / paper | Measured |
|---|---|---|---|
| Default (1) | 2D2D2D / FBFBF9 | E0E0DE / 121212 | 13.29:1 / 14.17:1 — the shipped tones, so an untouched install is pixel-identical |
| High Contrast (2) | 000000 / FFFFFF | FFFFFF / 000000 | 21.00:1 both |
| Sepia (3) | 3B3228 / F2E7D0 | E8D9BC / 1C1710 | 10.23:1 / 12.79:1 |
| Cool Gray (4) | 1F2429 / E8ECEF | DCE3E8 / 10141A | 13.17:1 / 14.24:1 |
| Custom (0) | the four hex fields | the four hex fields | unbounded — see below |

**The intermediate grays are interpolated, never listed.** The framebuffer is
1bpp plus two AA planes, so the panel has no colors of its own — it has a level
0..255, and the palette says what 0 and 255 look like. `colorForLevel` lerps
between them, which is why the 2-bit gray targets need no table of their own and
why a custom pair still produces a graded page. It is also why **inversion needs
no 255-level flip**: the dark palette's ink→paper direction already runs
light-on-dark. Hardcoding an intermediate would break both properties.

**A hex string, not a color well, and that is a platform limit.** A
`Settings.bundle` has six specifier types and none is a color picker;
`PSTextFieldSpecifier` is the only one that can carry an arbitrary color. So
Custom is four text fields accepting `RRGGBB` / `#RRGGBB` / `0xRRGGBB`, either
case. **Each field falls back independently** — a valid ink beside a mistyped
paper still gives the owner their ink on the default paper, so one typo costs
one colour rather than the page. An empty field is a fallback too, which is what
makes clearing one a way back rather than a way to a blank screen.

**Named presets are floored at 7:1; Custom is not.** `panel_palette_test`
enforces the floor on every preset in both appearances, because a curated list
has no business offering an unreadable page. Typing a color is an explicit act
and gets no such guard.

**The pad's field follows the paper.** The field behind the panel is the paper
tone, which is what makes the page float edgeless; the pad's own rungs are
relative deltas from that field, so `makePaletteOn(dark, o, f, panel.paper)`
carries the whole ladder onto whatever the owner picked. The consequence worth
knowing: the contrast figures printed on the Button Pad rows are measured
against the *default* paper and are approximate against a custom one. Said so on
the row.

`pollPanelPalette()` resolves the preset and the four fields every frame from
`NSUserDefaults` and repaints only on an edge **in the resolved pair** — the
same shape, and the same reasons, as `pollPadContrast()` above. It runs *before*
the pad poll, since the pad is built on the paper. The tones are applied while
converting the framebuffer to pixels, so `SimulatorOverlay::setPanelPalette`
reuses inversion's `pendingReconvert`: the change lands on the next present, not
the next firmware refresh.

The definitions, presets, parsing and guards live in
[src/PanelPalette.h](../src/PanelPalette.h), pure and host-tested
(`tests/panel_palette_test.cpp`, which also reads the shipped `Root.plist` and
fails when a preset row's printed ratio disagrees with the tones it selects).
Every failure mode here is a wrong *colour*, which no compiler and no other test
in this repo can see.

**Desktop and headless runs reach it through the environment**, there being no
Settings.app on a Mac: `CROSSPOINT_SIM_PANEL_INK_LIGHT`, `_PAPER_LIGHT`,
`_INK_DARK`, `_PAPER_DARK`, same syntax as the fields, applied inside
`setPanelPalette` on every call so both paths exercise identical mechanics —
the same contract `CROSSPOINT_SIM_DARK` has.

```bash
CROSSPOINT_SIM_PANEL_INK_LIGHT=3B3228 CROSSPOINT_SIM_PANEL_PAPER_LIGHT=F2E7D0 \
  pio run -e simulator_x3 -t run_simulator
```

### Dithered grays, moire, and the panel scale

Raised 2026-08-06: the gray dithered selection area shows irregular moire on an
iPad Pro. **The panel scale is not the cause** — checked, not assumed.

`CROSSPOINT_SIM_PIXEL_EXACT=1` is set, but on `crosspoint_core` in the ROOT
[CMakeLists.txt](../CMakeLists.txt), not in [ios/CMakeLists.txt](CMakeLists.txt)
where you would look for it — so `INTEGER_SCALE` + `SCALEMODE_NEAREST` are both
live on iOS. Transcribing both stages exactly (`layoutPadTablet` publishing the
insets, then `HalDisplay`'s manual placement recomputing from them) gives, on
every iPad:

| frame | output | scale | dst | 1 texel : |
|---|---|---|---|---|
| iPad Pro 13″ | 2064x2752 | **1.0000** | 240,852 1584x1056 | 1 device px |
| iPad Air 13″ | 2048x2732 | **1.0000** | 232,842 1584x1056 | 1 device px |
| iPad Pro 11″ | 1668x2420 | **1.0000** | 42,686 1584x1056 | 1 device px |
| iPad Air 11″ | 1640x2360 | **1.0000** | 28,656 1584x1056 | 1 device px |
| iPad mini | 1488x2266 | **1.0000** | -48,609 1584x1056 | 1 device px |

Integral scale, whole-number dst, one texel per device pixel, on all five. The
90-degree rotation is about the dst center and lands on whole numbers too.
`UIRequiresFullScreen` rules out a fractional Split View window.

**The dither is at LOGICAL resolution, not framebuffer resolution.** Worth
recording because the opposite is the natural assumption and it is wrong: the
firmware's `GfxRenderer` divides the device coordinate by `CROSSPOINT_RENDER_SCALE`
when building the dither mask (`fillRectImpl`, the comment at
"That keeps the dither at LOGICAL resolution"), and the per-pixel path gets the
same result for free because `drawPixel` expands one logical pixel into an SxS
device block. So at `RENDER_SCALE=2` a dither cell is 2x2 device pixels, not 1x1
— the fill "looks pixel-for-pixel like scale 1, just replicated". A selection
row is `Color::LightGray`, which is `x % 2 == 0 && y % 2 == 0`: one 2x2 device-pixel
dot on a 4x4 device-pixel grid.

That leaves the resample somewhere **below the app**. The prime suspect is
iPadOS **Display Zoom**, which renders the whole screen at a smaller logical
size and upscales it to the panel by a non-integer factor — on a 13-inch Pro,
1024x1366@2x = 2048x2732 stretched to 2064x2752, a 1.0078x resample with a beat
period around 128 px. Against a 4 px dot grid that is exactly broad irregular
banding, it is invisible in a screenshot (captured pre-composite), and no
arithmetic in this repo can see or undo it.

`HalDisplay.cpp`'s manual placement now logs the presented geometry once and on
every change, flagging `(FRACTIONAL)` and `(OFF-GRID)`, so this is answerable
from the console instead of by inference:

```
[panel] out 2064x2752 px, scale 1.0000, dst 240.00,852.00 1584x1056
```

**Check `out` against the device's true native pixel size.** A 13-inch Pro
reporting 2048x2732 rather than 2064x2752 is Display Zoom, and the fix is in
Settings, not in the code.

### Open: rockers to the screen edge, page to the top

Raised 2026-08-06. Two complaints against the layout above — the rockers are
too far inboard for a thumb to find without looking, and the page sits too low.
**Nothing is approved yet**; the options are live in
[mockups/ipad-pad-placement.html](mockups/ipad-pad-placement.html), which
computes every frame from `layoutPadTablet()`'s own arithmetic rather than
sketching it, and draws the shipped layout underneath as a dashed ghost.

Four measurements bound whatever gets chosen.

**The inset complaint is a 13-inch complaint.** `leftX` centres the pair in the
margin, so how far inboard the rockers sit is `(margin - 2 * cell) / 2` — which
scales with the frame and is nearly nothing on the small ones:

| frame | margin | cell | rocker inset | page top | vertical slack |
|---|---|---|---|---|---|
| iPad Pro 13″ | 252 pt | 60 | **66 pt** | 294 pt | 540 pt |
| iPad Air 13″ | 248 pt | 60 | **64 pt** | 289 pt | 530 pt |
| iPad Pro 11″ | 153 pt | 60 | 16.5 pt | 211 pt | 374 pt |
| iPad Air 11″ / iPad | 146 pt | 60 | 13 pt | 196 pt | 344 pt |
| iPad mini | 108 pt | 54 | **0 pt** | 172.5 pt | 297 pt |

The mini is already flush — its 108 pt margin holds a two-cell rocker exactly —
so "move the rockers to the edge" is a no-op there and worth 64-66 pt on the
13-inch frames. Any rule has to be written so the mini does not go negative.

**Moving the page up is free.** The tablet branch sets top and bottom insets that
sandwich the panel exactly, so `availH` equals the panel height and
`HalDisplay`'s own fit lands on the same scale; its
`topMargin = topBand + min(16, slack/2)` then collapses to the band edge
(`HalDisplay.cpp:688`). The page therefore lands at exactly whatever `topInset`
the branch publishes, at an unchanged scale. Centring is one term —
`(availPx - panelHpx) / 2.0f` — and replacing it with a chosen offset is the
whole change.

**The page cannot get bigger to absorb the slack.** An integer 2x panel wants
1056 pt of width and the widest iPad is 1032, so every frame presents at 1x,
528 × 792 pt. The 297-540 pt of vertical slack is genuinely spare space; the
only question is where it goes, not whether it can be spent on a larger page.

**The cell is capped by the margin,** `min(60, margin / 2)`, so a fatter target
is available on the 13-inch frames (up to 126 pt) and nowhere else. Option F in
the mockup tries 88 pt.

The option sets, all with the rockers flush unless stated: **A** edge only, page
untouched — **B** edge + page as high as the safe area allows — **C** B with the
rockers at 62% rather than 50%, which is where a two-hand side grip actually
sits on a tablet held for balance — **D** page high and the whole pad low and
tucked together — **E** a fifth of the spare margin instead of flush, on the
argument that a control touching the bezel invites edge-swipe conflicts — **F**
C with 88 pt cells — **G** the owner's 2026-08-06 dial-in, below. The mockup also
carries a thumb-reach overlay (40 mm easy / 55 mm stretch rings from a pivot on
the side edge, per frame's own ppi) and an optional hit-slop band that runs the
target to the screen edge while the stroke stays inboard — the same trade
already banked as the phone's fallback for its half-height row.

**Every placement is a RATIO, never a point value** (owner ruling 2026-08-06).
The first dial-in — page top 186 pt, rocker inset 26 pt — was tuned on an iPad
Pro 13″ and means nothing on the other four frames, so the mockup now takes
percentages and resolves them per frame. The denominators are picked so the
ratio cannot express an illegal layout at either end of its range, which is what
makes them the right ones:

| setting | unit | meaning |
|---|---|---|
| page top | **ratio** of the spare height, `availH - panelH` | 0 = as high as the safe area allows, **50% = today's centered page**, 100 = as low |
| rocker inset | **points** | a minimum distance in from the bezel, honored on every frame |
| rocker center | **ratio** of screen height | **50% = today's centered rockers** |
| cell | **points** | `kOptimalSquare`, a thumb-sized physical optimum |

That the shipped page is exactly 50% of the spare height is the check that that
denominator is the right one.

**The rocker inset is POINTS, not a ratio** (owner ruling 2026-08-06, revising
the first pass). Two reasons. How far a thumb travels in from the bezel is a
physical distance, the same kind of quantity as the cell — and as a ratio of the
spare margin it resolved to **0 pt on the mini**, whose margin holds a pair
exactly, so the setting had no effect at all on the one frame that was already
flush. As a point minimum it applies everywhere, and **the cell yields to make
room**: `cell = min(requested, (margin - inset) / 2)`. The inset is capped so the
cell can never be squeezed under the 44 pt HIG floor, and the readout says when
that cap bites.

Both point values are resolved per frame, never stored clamped — storing the
clamp meant one visit to the mini pinned every frame to 54 pt.

The owner's draft, **G — page at 30% of the spare height, rockers 26 pt in**,
resolves to:

| frame | page top | rocker inset | cell |
|---|---|---|---|
| iPad Pro 13″ | 186 pt | 26 pt | 60 pt |
| iPad Air 13″ | 183 pt | 26 pt | 60 pt |
| iPad Pro 11″ | 136 pt | 26 pt | 60 pt |
| iPad Air 11″ / iPad | 127 pt | 26 pt | 60 pt |
| iPad mini | 113 pt | **20 pt** | **44 pt** |

**26 pt is not achievable on the mini.** Its 108 pt margin caps the inset at
`108 - 2 x 44 = 20 pt`, and even that puts the cell exactly on the HIG floor.
If a constant inset across all five frames matters more than the cell size, 8 pt
is the comfortable figure — it costs the mini nothing but 4 pt of cell (54 -> 50)
and every other frame keeps 60.

**The bottom row must clear the display's corner arcs** (owner ruling
2026-08-06). Moving the rockers outward pushes POWER and UP|DOWN into the two
bottom corners, and an iPad's corners are rounded — so past a certain inset the
display itself clips the control. A clipped control is dead, not merely ugly:
the pixels under the arc are not on the screen, so neither is the touch.

The geometry is a quarter-arc of radius `r` centered at `(r, H-r)`. A control
whose bottom edge sits `d` points up from the screen bottom pokes `r - d` into
the arc's band, and needs `r - sqrt(r² - (r-d)²)` of inset to clear. With the
bottom row anchored at the 20 pt home-indicator inset:

| radius | bottom row at 20 pt up | minimum inset |
|---|---|---|
| 18 pt | above the arc band | none needed |
| 21.5 pt | 1.5 pt into it | 0.05 pt |
| 30 pt | 10 pt into it | **1.7 pt** |

So the constraint is small but real, and it binds exactly on the frames the
whole change is for — the M4-generation Pro bodies, whose corners are rounder
than the 18 pt the 2018-2022 ones used. Flush-to-the-edge on a Pro 13″ clips
POWER and DOWN by 1.6 pt.

**The exact radius is `UIScreen._displayCornerRadius`, which is private**, so
the mockup carries per-frame defaults (30 / 18 / 30 / 18 / 21.5) as a slider
rather than a constant, draws the frame at that radius in point space, paints a
clipped control red, and reports the overshoot. Check a layout against a radius
*larger* than you believe, never smaller. Two corrections are offered and
neither is free — inset the bottom row until it clears, which costs its column
alignment with the rockers above, or raise it, which costs its screen-bottom
anchor. All seven option sets default to insetting.

**One question is still open in G:** the page ratio can be taken against the
spare height or against screen height. Both reproduce 186 pt on a Pro 13″ — they
are the same number there — and they diverge below it, reaching the mini at
113 pt and 153 pt respectively. Spare height holds the *proportion* of emptiness
above and below constant across frames; screen height holds the absolute
position and lets the page drift back toward centered on small frames. The mockup
carries both as a toggle, switching without moving the page.

**Regenerating the source list: clean first.** `pio run -e simulator -t
compiledb` emits compile actions only for TUs that are not restored from the
firmware's build cache (`build_cache_policy.py`), so an incremental run
produces a silently PARTIAL DB — this cost a full build cycle on 2026-08-04
(the missing FileManagerActivity/FsOps TUs surfaced only at link). Always
`rm -rf .pio/build/simulator` in the firmware repo before `-t compiledb`.

Below is the shipped iPhone layout.

**Placement mirrors the chassis where it's measurable.** The SDK describes the
buttons only electrically (six on a resistor ladder across two ADC pins, POWER
on its own digital pin — `BoardConfig` `InputPins`,
`InputStyle::XteinkAdcLadder`), but the panel-to-top-row gap now matches the
physical X3: the front buttons' top edge sits 11.6 mm below the panel window,
14.8% of the 78.2 mm panel height, and the pad keeps that proportion of the
presented panel height (`kPanelGapRatio`, fed by
`SimulatorOverlay::panelHeightPx()`). Full measurement table + methodology:
the firmware repo's `docs/hardware-dimensions.md`.

Sizing: strict square grid, cell constrained to the 60 pt optimum — the column
count absorbs device width (nearest-to-60 integer fit, minimum five columns),
so wider devices gain empty middle columns instead of fatter buttons: 55.8 pt
cell / 6 columns on SE and 13 mini, 58.8/6 on 16, 57.1/7 on 16 Pro Max.
Controls count from the grid's ends (Back|Select cols 0-1, Left|Right and
Up|Down in the last two, Power col 0). The top row is full-height cells; the
bottom row is half-height (~28-32 pt) — a deliberate, owner-approved exception
to the 44 pt HIG minimum, with invisible hit-slop as the agreed fallback if
page-turns feel cramped on device. Layout is computed in points and converted
once, so targets keep their real physical size at any device scale. The panel
is top-aligned in the space above a fixed reserved bottom band
(`SimulatorOverlay::setBottomInset`), presents at an integer scale, and
publishes its bottom edge; the top row hugs that edge (falling back to sitting
just above the bottom row before the first present), while the bottom row
anchors to the screen edge using the system safe-area inset (fallback 34 pt,
floor 16 pt on home-button devices).

**Open: the pad collides with system Picture-in-Picture.** A floating video
window parks in a bottom corner, which is where both halves of the bottom row
live: bottom-right takes the UP|DOWN page-turn rocker whole, bottom-left takes
POWER. Two facts bound every fix. **The app cannot see the window** — no public
API reports another app's PiP, so the pad cannot dodge at runtime and the answer
has to be a static layout or a reader preference. **Touches over it never
arrive**, the window being a system window above the app, so the invisible
hit-slop earmarked above is no help; an overlapped control is dead, not hidden.
Measured on an iPhone Air against the shipped build, the front rockers clear the
window's top edge by **6.7 pt** — they survive by luck, not by design.

The room to fix it is one number: the panel presents at an integer scale, so the
reserved band can grow only until the panel would drop 2x → 1x. On the Air that
is **86.7 pt of headroom** (band 223.3 pt of a 310 pt ceiling), against the
**166 pt** a full window band wants. So a vertical answer buys its clearance from
the chassis-matched gap, from the two-row split, or not at all — on a 13 mini or
an SE there is no room for one. Six options, drawn to scale from this file's own
layout math with the window movable to any corner and resizable:
[mockups/pip-window-alignment.html](mockups/pip-window-alignment.html). Nothing
is approved yet.

**Settled part: `kPipLift` = 12 pt (owner ruling 2026-08-04).** The narrower
complaint was not the buried bottom row — it was the TOP row (LEFT|RIGHT)
clearing the window's top edge by only 6.7 pt, close enough to read as a
collision. That needs no restructuring: **both rows move up 12 pt as a block**,
taken out of the panel gap and nothing else. The reserved band is unchanged, so
the page neither moves nor changes scale — the pad just sits higher in the space
it already had. Clearance goes 6.7 → 18.7 pt, and the width the window can be
pinched to before it reaches the top row goes 50% → 55% of the screen.

**Judge the gap in millimetres, not points.** It is a chassis measurement (11.6
mm below the panel window on a 78.2 mm panel, 14.8%) and the Air presents 6.75 pt
per real millimetre, so a shift of X points leaves `(78.3 - X) / 6.75` mm of the
hardware's gap. Below about 4 mm the pad stops reading as a control surface under
the page and starts reading as a border around it.

| move up | clearance | page gap | on the X3 |
|---|---|---|---|
| 0 pt (was) | 6.7 pt | 78.3 pt | 11.6 mm |
| **12 pt (now)** | **18.7 pt** | **66.3 pt** | **9.8 mm** |
| 25.3 pt | 32 pt | 53.0 pt | 7.9 mm |
| 41.3 pt | 48 pt | 37.0 pt | 5.5 mm |
| 78.3 pt | 85 pt | 0 | 0 mm |

**Settled too: `kTopReserve` = 80 pt (owner ruling 2026-08-04).** The top band is
now `max(safe area, 80 pt)` rather than the safe area alone — a floor, not a
replacement, so a deeper safe area still wins. The safe area is the minimum the
system asks for, not a margin: on an iPhone Air it reads 74, which starts the
text 5 pt below the Island rather than clear of it. The page moves 79.3 → 85.3,
and because the pad hangs off the page's bottom edge it moves with it, so the
clearance `kPipLift` bought falls **18.7 → 12.7 pt** and the pinch the top row
survives falls 55.0% → 52.5%. Page still 2×, headroom 86.7 → 80.7 pt.

**Explored and not taken: reserving a top band so a small window misses the
page.** `setTopInset` would grow from the safe area's 74 pt to 159.2 pt (safe
area + the window's own 11 pt inset + a small window's 74.2 pt height), which
puts the page at 160-688 rather than 79-607. Two things follow. The top row
hangs off the page's bottom edge, so it descends with it and lands in the
bottom-corner windows unless the lift goes from 12 pt to ~41 pt — taking the
panel gap to 5.5 mm. And the budget closes to **1.5 pt**: top band plus the band
below may total 384 pt before the page halves to 1x, and this arrangement wants
382.5. A device whose safe area reads a few points differently loses the page.
The bottom row cannot be saved at any lift — with the page ending at 688 there
are 104.8 pt above a small bottom window and the two rows stand 111 pt tall, so
one of them is always behind it. Live, with both bands on sliders:
[mockups/pip-envelope.html](mockups/pip-envelope.html).

Two more mockups, both computed from this file's own layout math rather than sketched:
[mockups/pip-gap-shift.html](mockups/pip-gap-shift.html) puts the shift and the
window width on live sliders, and
[mockups/pip-corner-matrix.html](mockups/pip-corner-matrix.html) checks the
settled 12 pt against all four corners at both pinch extremes. The one case 12 pt
does not cover is the largest pinch size (~62.8% of width, 148 pt tall), which
reaches 18.4 pt into the top row from either bottom corner; clearing that too
would want 30 pt of lift, i.e. 4.5 mm of chassis gap, which is the trade this
stops short of. Top corners never touch the pad at any size — they cover page
text, which no pad layout can prevent.

## Read aloud

Off by default; **Settings > Apps > CrossPoint X3 > Read Aloud (Experimental)**.
With it on and a book open, the phone reads the page in the owner's Spoken
Content voice, turns the page itself, highlights each word as it is spoken, and
starts from any word tapped.

| What the owner does | What happens |
|---|---|
| Turns the toggle on | Takes effect at the next page render — capture publishes when a page is drawn, so the current page is not retroactively spoken |
| Opens a book | The page is spoken from the top, in the voice from Settings > Accessibility > Spoken Content > Voices |
| Waits | At the end of the page the app presses the page-forward button itself and reads on. Progress persists, because the press is a REAL button press the firmware handles |
| Turns the page manually | Speech stops and re-starts on the new page |
| Taps a word | Reading jumps to that word. No page turn, no double audio |
| **Taps the word being read** | **Reading STOPS.** The only stop a finger can reach; tapping that word again starts it back up |
| Taps a margin, or drags | Nothing. Only a tap that lands on a word counts |
| **Two-finger double tap (magic tap)** | **Pause / resume**, and from a full stop it starts again at the word it stopped on. VoiceOver's gesture, so it exists only while VoiceOver or AssistiveTouch is on — everyone else stops with a tap |
| **Moves Speaking Rate** | Applies immediately: the current word is re-spoken at the new rate rather than waiting for the page to end. 50%–200% of normal, default 100% |
| **Locks the phone** | Keeps reading, and keeps turning pages |
| Presses BACK to Home | Speech stops and the highlight clears |
| Turns the toggle off | Stops on the first frame after returning to the app |
| Reaches the end of the book | One `[READALOUD] page timeout` and a clean stop |
| Uses the button pad | Unchanged — read-aloud adds no gestures and takes no pad slot |

The highlight is overlay chrome, so it does **not** appear in
`CROSSPOINT_SIM_SCREENSHOTS` captures (those are taken pre-composite). A device
screenshot does show it. It **survives a pause** — while paused it is the
answer to "where was I" — and clears on a stop.

**The system's own Speaking Rate slider does not reach this feature.** Settings
> Accessibility > Spoken Content > Speaking Rate applies to VoiceOver and Speak
Screen, not to an `AVSpeechUtterance`, so without the app's own row there is no
rate control at all. It is stored as a percentage of normal and mapped onto
AVSpeech's 0..1 scale in [CrossPointReadAloud.mm](CrossPointReadAloud.mm) —
that scale's DEFAULT is its MIDPOINT (0.5), so 200% lands exactly on
`AVSpeechUtteranceMaximumSpeechRate`. Named `PSMultiValueSpecifier` steps
rather than `PSSliderSpecifier`, because a Settings slider row carries neither
a title nor a numeric readout: the owner would be dragging an unlabelled
control with no way to see what they picked.

Ring/silent on silent still plays, and reading survives the screen locking: the
session is `AVAudioSessionCategoryPlayback` + `ModeSpokenAudio`, and
`UIBackgroundModes: audio` is declared in [Info.plist.in](Info.plist.in). The
two are one mechanism — either alone grants nothing, and the background grant
is also what keeps the FIRMWARE running, which is what turns the pages. The
session is handed back (`NotifyOthersOnDeactivation`) ~1.5 s after the reader
stops, so an interrupted podcast can resume and a ~1 kHz loop is not holding
background execution it is not using; a PAUSE deliberately does not release it.
**Neither the silent switch nor screen-off playback can be reproduced in the
Simulator, and no physical phone is paired to this Mac — SHIPPED, UNCONFIRMED
on device.**

Logs are greppable: every line starts `[READALOUD] `. The ones worth knowing:
`utterance start ... rate=N% (r) voice=V`, `speaking serial=N` (the engine
really is talking, as opposed to holding a silent utterance — otherwise
indistinguishable), `stopped`, `paused`, `resumed`, `page turn queued`, `page
timeout`, `audio session released`.

**Driving the new controls headlessly.** Speech is inaudible to a test and the
magic tap is a gesture no script can perform, so
`CROSSPOINT_SIM_READALOUD_SCRIPT` fires them on the `SDL_GetTicks` millisecond
clock `CROSSPOINT_SIM_INPUT_SCRIPT` already uses, through the same entry points
UIKit and a finger use:

```bash
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='2500:BACK;5000:RIGHT;6500:RIGHT' \
SIMCTL_CHILD_CROSSPOINT_SIM_READALOUD_SCRIPT='12000:TAPWORD;15000:MAGICTAP;18000:DELEGATETAP' \
  xcrun simctl launch --console-pty <udid> com.natebunnyfield.crosspoint.x3
```

`TAPWORD` taps the center of the word being spoken **in screen pixels**, so the
panel geometry and the hit-test are exercised too — which makes it precisely
the tap-to-stop case. `MAGICTAP` calls what the gesture calls; `DELEGATETAP`
sends `accessibilityPerformMagicTap` to the application delegate, the message
UIKit itself sends once the gesture goes unhandled up the responder chain, so
the only part left unproven is Apple's own routing. Note the book opens on its
COVER, which has no text: page forward at least once, or the channel publishes
a page with nothing to say and every control correctly reports "nothing to
toggle".

The magic-tap handler is installed on the app delegate's class with
`class_addMethod`, and **the guard is that call's return value, not
`respondsToSelector`** — UIKit declares `accessibilityPerformMagicTap` in a
category on `NSObject`, so every class in the process answers YES and the
obvious guard declines to install, every time. That was the first measured
failure of this code.

### Accessibility — VoiceOver, Speak Screen, Braille, Switch Control

**SOLVED (build 54, 2026-08-09), and the mechanism matters: iOS 26's Speak
Screen consumes exactly one thing — a full `UITextInput` adoption on the
accessibility element.** Seven instrumented builds measured out everything
else: synthetic `UIAccessibilityElement` containers, the explicit container
protocol, `UIAccessibilityReadingContent`, elements vended from the window,
hidden real `UITextView`s, and a sentinel matrix whose fully VISIBLE `UILabel`
went unread. VoiceOver read every one of those; Speak Screen read none. The
recipe that works is WWDC26 session 219 ("Enhance the accessibility of your
reading app"): `ScannedPage: UIView, UITextInput`, implemented in its
entirety.

Two surfaces, two consumers, one data source (the read-aloud channel's page
text + per-word rects):

- **`CPAccessibilityOverlay`** — per-LINE `UIAccessibilityElements` for
  VoiceOver, Braille and Switch Control. Per-line because Speak-anything
  concatenates elements; per-word would pause after every word. The container
  implements `accessibilityElementCount`/`AtIndex`/`indexOf` EXPLICITLY *and*
  sets the stored property — overriding only the getter is the trap that cost
  three builds (UIKit derives the container methods from the stored property,
  not a getter override; the container reports zero children and every
  assistive technology says "no speakable content").
- **`CPPageTextInputView`** (`CrossPointPageTextInput.mm`) — the Speak Screen
  consumer. A view that IS the accessibility element and adopts `UITextInput`
  fully: UTF-8 channel offsets mapped to UTF-16 once per page, geometry
  answered from the word rects, the stock `UITextInputStringTokenizer` riding
  the position math. Read-only: never first responder, never the keyboard.
  Carries `UIAccessibilityTraitCausesPageTurn`; `accessibilityScroll(.next)`
  queues the same BTN_RIGHT tap the read-aloud adapter uses, and the next
  publish posts `PageScrolled` (not `ScreenChanged`) so continuous reading
  crosses the page turn. The system draws its own reading highlight from
  `selectionRects` — owner ruling: leave it; no workarounds.

**Scope (owner ruling 2026-08-09): only EPUB text is speakable.** The one
channel publisher is `EpubReaderActivity`; Home, menus, and .txt/.xtc books
deliberately publish nothing, and "no speakable content" there is correct
behavior, not a bug. The pad is SDL-drawn and invisible to accessibility by
construction.

**Diagnostics are OFF by default** (same ruling). Everything —
`diagnostics/a11y.log` on the card, tree dumps, QUERY/READING/TEXTINPUT
probes — funnels through `CrossPointDiag_log`, which is gated on the
**Settings.app → CrossPoint X3 → Diagnostics Log** toggle. Flip it on and the
full instrument returns without a rebuild: the log lands on the card,
browsable in the Files app (On My iPhone → CrossPoint X3 → diagnostics),
long-press to share. The desktop equivalents stay available always:
`CROSSPOINT_SIM_READALOUD_DUMP=1` prints per-line labels against a real book,
`tests/readaloud_lines_test.cpp` pins the grouping, and `tools/axprobe/`
queries the app through Apple's real out-of-process AX channel (the
instrument that separated "the container answers" from "nobody asks", which
was the whole investigation).

**Speak Screen cannot be tested in the simulator** — its Spoken Content pane
offers only Speak Selection, so `UIAccessibilityIsSpeakScreenEnabled()` reads
0 there. VoiceOver is available in the simulator and reads the line elements;
`CROSSPOINT_SIM_FORCE_SPEAKSCREEN=1` builds the Speak Screen surfaces anyway
so the AX probe can verify them off-device. The full investigation — six
failed exposure mechanisms, the research fleet, the Kindle control experiment
that overturned it, and why each probe exists — is in the git history of
`CrossPointAccessibility.mm` and `CrossPointPageTextInput.mm`; the memory of
it is deliberately kept there rather than here.

## Keyboards — Bluetooth and on-screen

**Both work, in every text field the firmware has**, and they are the same
mechanism: a keyboard is a keyboard as far as SDL is concerned. Verified on an
iPhone 13 mini simulator (iOS 26.5) against Settings > Device owner.

The X3 has seven buttons and no keyboard, so firmware text entry pecks
characters out of an on-screen grid (or the daisywheel). That grid is untouched
and still works — typing is an *additional* input, not a replacement, and both
edit the same field and the same cursor.

| Key | While a text field is open | Otherwise |
|---|---|---|
| Printable characters | inserted at the cursor | — (see suppression below) |
| Backspace | erases before the cursor | — |
| Return, single-line field | `BTN_CONFIRM` — Select on the on-screen keyboard, which types the highlighted character | `BTN_CONFIRM` |
| Cmd/Ctrl+Return, single-line field | commits the entry, same as the grid's OK key | `BTN_CONFIRM` |
| Return, multi-line editor | inserts a NEWLINE (note editor, Claude) | `BTN_CONFIRM` |
| Cmd/Ctrl+Return, multi-line editor | `BTN_CONFIRM` — the panel's pick, kept reachable from a desktop keyboard | `BTN_CONFIRM` |
| Escape | `BTN_BACK`, which cancels the entry | `BTN_BACK` |
| Arrows | move the on-screen grid selection | `BTN_UP/DOWN/LEFT/RIGHT` |

**Return is the one key whose answer depends on the field**, and both ways of
getting it wrong have shipped. Giving it to the text in a single-line field
made Select on the daisywheel commit and leave instead of typing a character;
leaving it on the button in a multi-line editor made Return press Select
instead of breaking the line (ST-006). The rule, the reasoning and the truth
table live in [../src/TextEntryKeyRouting.h](../src/TextEntryKeyRouting.h) and
are unit-tested in `tests/text_entry_enter_test.cpp`; the activity says which
kind of field it opened via `setTextEntryActive(true, TextEntryLines::Multi)`.
On hardware there is no conflict to resolve — Confirm is a GPIO button and a
paired keyboard's Enter arrives as `'\n'` through the HID path — which is why
this is a simulator-side decision at all.

**Every text field, including the two editors.** Wi-Fi passwords, Device owner,
the daisywheel, **Create Note and Claude**. The two editors were the last
holdouts: they took characters only from their own on-screen grid, so on the
phone they raised no keyboard at all, and a paired keyboard's letters fell
through to the button map — typing "sleep" in a note put the device to sleep.
They now announce text entry like every other field.

**The suppression is the load-bearing part.** `HalGPIO` maps real key events to
buttons by scancode, and that map spends letters: `P` is POWER, `S` is the sleep
shortcut, `H` is the Home key, Return is CONFIRM. Typing "password" into a Wi-Fi
field would otherwise press POWER twice, sleep the device on the `s` and fire
Home on the `h`. While a text field is open, `HalGPIO::update()` maps only
Escape, the four arrows and (per the table above) Return, routing everything
else to the typed-text queue;
`isPressed()` applies the same rule, so a held letter cannot read as a held
button either. Measured, not assumed: typing ` psh` into the owner field on the
phone inserts three characters and does nothing else.

The firmware is what opens and closes the channel —
`KeyboardEntryActivity`/`DaisyEntryActivity` call
`mappedInput.setTextEntryActive()` on enter and exit — so the host keyboard is
live exactly while a field is on screen and never while the reader is.

**The on-screen keyboard comes up by itself**, because `SDL_StartTextInput()`
is what iOS uses to raise it. It is called on the main thread from
`simulator_main.cpp` (`gpio.pumpHostTextInput()`), edge-triggered on the
firmware's flag — the flag is set on the firmware task, and raising a keyboard
is UIKit work that cannot ride along there. It covers the bottom of the screen,
including the button pad and the lower rows of the firmware's own grid; the
panel does not move or rescale under it (verified: panel geometry is identical
with and without the keyboard up), so the text field stays visible, which is
the part that matters.

**A paired Bluetooth keyboard suppresses the on-screen one automatically** —
that is iOS behavior, not something this app decides — and types straight
through. Nothing here distinguishes the two.

**One difference to know about in the Simulator.** The on-screen keyboard's
Delete key does nothing there. SDL synthesises `SDL_SCANCODE_BACKSPACE` for a
soft-keyboard deletion only when `!SDL_HasKeyboard()`
(`SDL_uikitviewcontroller.m`, `textFieldTextDidChange`), on the assumption that
a real keyboard would have sent the key itself — and an iOS Simulator reports a
keyboard attached whether or not one is, so the synthesis is skipped. The
harness logs both flags when text input starts:

```
[TEXT] host text input started (screen keyboard support 1, keyboard attached 1)
```

`keyboard attached 1` is the tell. On a phone with no keyboard paired it reads
0 and soft Delete works. In the Simulator, use the Mac's own Delete key
instead — that is a real key event and it does erase (verified). Typing on the
soft keyboard is unaffected and works in both cases (verified by tapping its
keys).

### What was verified, and how

On the iPhone 13 mini simulator, in Settings > Device owner, all with the real
key path — not the injection hook:

- Hardware keyboard: characters (` Rowan`), Backspace (erased one of two typed
  `Q`s), Return (committed; the entry closed and the name persisted), and
  Return again from Settings acting as CONFIRM (reopened the field), which is
  the proof the button mapping is intact once the field is closed.
- Suppression: ` psh` inserted three characters — no sleep, no Home, no power.
- On-screen keyboard: raised itself when the field opened, and its letter keys
  typed into the field.

Headlessly, `tests/test_text_entry.sh` drives the same field on the desktop
binary through `CROSSPOINT_SIM_INPUT_SCRIPT`'s `TYPE` action and asserts the
persisted `settings.json`, and the firmware's `TypedTextEntryTest.cpp` covers
the drain semantics (run ordering, backspace position, commit/cancel, the
multi-byte length check). Neither can cover the suppression, because both
inject below SDL — that is why the phone runs above are written down.

### Putting the keyboard away

iPad's system keyboard has a dismiss key in its bottom-right corner. **iPhone's
does not** — so once the firmware opened a field, the keyboard covered ~40% of
the screen (336 pt of 812 on a 13 mini), taking the lower page and the whole
button pad with it, and the only way out was to leave the screen.

Three controls, one state (`hostkbd::State`, host-tested in
`tests/host_keyboard_test.cpp`):

| Control | Does |
|---|---|
| Bar above the keyboard | Lowers it. Rides on the keyboard, so it leaves with it. |
| Keyboard chip, one cell wide, centred in the bottom row | Toggles it. Drawn whenever a field is open; the chevron points where the keyboard is about to go. |
| Tap anywhere else | **Nothing.** Only the chip toggles the keyboard. |

Off-chip taps used to raise it too, on the theory that a bigger target is
kinder. It is not: the margins around the panel and the band around the pad are
most of the screen, so putting the phone down or shifting a grip threw the
keyboard back over the page (owner, 2026-08-11: "it needs to only pop up when
show keyboard is tapped"). A control that fires when you touch nothing in
particular is not a control.

On the phone the chip sits under the keyboard while it is up, so in practice the
bar lowers and the chip raises. On the tablet the bottom row lifts clear (see
below) and the chip is a true toggle, which is why it draws both chevrons.

The bar is a `UIToolbar` set as `inputAccessoryView` on SDL's hidden
`SDLUITextField`. SDL exposes neither the field nor any accessory API
(`grep -rn inputAccessoryView` across SDL 3.4.12: nothing), so it is found by
public traversal — `SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER` → `rootViewController`
→ subviews → the one `UITextField`. No private headers, no ivar reads, no
swizzling. `[harness] keyboard bar attached` on the console says it worked, and
a failure to find the field logs loudly on the same channel, because a silent
miss looks exactly like the bug this fixes.

Verified on the iPhone 13 mini simulator with the hardware keyboard
disconnected (`ConnectHardwareKeyboard = 0` for that device — leave it connected
and iOS suppresses the software keyboard, so none of this is visible), driving
Settings > Device owner:

- Field opens → keyboard up, bar attached at depth 1, chip absent.
- Tap the bar → `[TEXT] host keyboard hidden by request`, keyboard down, page
  and firmware grid fully visible, chip drawn in the pad band's middle columns.
- Tap the page → `host keyboard shown by request` → `host text input started`,
  keyboard back, chip gone.
- Typed `Ada` after the raise; it reached the firmware's field.

Not verifiable here, and so **UNCONFIRMED**: iPad's own dismiss key driving the
chip (the `SDL_EVENT_SCREEN_KEYBOARD_HIDDEN` path), and behavior with a paired
Bluetooth keyboard — no iPad and no paired keyboard on this Mac.

### The keyboard overlaps the page; it does not shrink it

Owner ruling 2026-08-10, and it replaces the panel half of the 2026-08-09
clearance band.

That band reserved the keyboard's height out of the panel's space. On a phone
that leaves too little room for the panel's own integer scale, so the page
dropped to roughly 60% — trading about 40% of the text for a sight of its lower
edge. It always did; `CrossPointIOS_setKeyboardHeight` simply never asked for a
present, so the relayout waited for whatever page the firmware rendered next and
mostly went unseen. Fixing that made it immediate, and immediately obviously
wrong.

Now the keyboard covers the page's lower edge the way it covers content in every
other iOS app, and the bar above it puts it away in one tap.

The **bottom row still lifts on the tablet** and no longer on the phone. Same
asymmetry `kThumbRowFromBottom` rests on: the tablet's pad lives in the margins
*beside* the page, so lifting it costs the page nothing, while the phone's pad
is a band *below* the page — lifting that would paint controls over the text,
and with the panel no longer shrinking there is nowhere for a lifted band to go.
While the keyboard is up on a phone it covers the page's lower edge and the pad
alike.

## How the harness attaches

Two seams, both in simulator code — the firmware and `HalGPIO` are untouched.

**Input: an event watch, not a poll loop.** `HalGPIO::update()` owns the SDL
event pump for the whole simulator and must keep owning it; two pollers would
split events between them. `SDL_AddEventWatch` observes events as they are queued
without consuming them, so the harness sees finger events that `HalGPIO` ignores
and neither steals from the other.

**Output: `SimulatorOverlay`.** The pad is painted by a free hook the
presentation path calls (`src/SimulatorOverlay.h`), deliberately not a
`HalDisplay` method — the HAL's public surface must mirror the firmware's, and an
on-screen pad has no analog on real hardware. The callback runs with logical
presentation disabled and receives the real output size, so it can paint the
letterboxed margins that the panel's logical coordinate space cannot reach. It
also exposes `requestPresent()`, because an e-ink firmware presents rarely and a
pressed state would otherwise not appear until the next page render.

`simulator_main.cpp` holds the only iOS-specific lines in the simulator: the
`chdir()`, the harness install, and a normal `return 0` in place of `_exit(0)`
(iOS reports a self-terminating process as a crash).

## Closed: level reads do not see injected keys

**Resolved.** Option 1 below was taken. The pad no longer pushes SDL key events;
it calls `gpio.injectButtonDown/Up(HalGPIO::BTN_*)`.

The bug, measured not assumed:

```
SDL_PushEvent rc=1
AFTER PUSH+PUMP: GetKeyboardState[P]=0
event dequeued from queue=1
AFTER POLL:      GetKeyboardState[P]=0
```

`SDL_PushEvent` delivers an event to the queue but does not update SDL's internal
keyboard state array — that array is only written on the real-input path.
Consequences for `HalGPIO`, when the pad injected by pushing key events:

- **Edge reads worked.** `update()` sets `pressedThisFrame` /
  `releasedThisFrame` straight from the dequeued event, so `wasPressed()` /
  `wasReleased()` behaved.
- **Level reads did not.** `isPressed()`, `getHeldTime()` and
  `getPowerButtonHeldTime()` consult
  `SDL_GetKeyboardState(NULL) || syntheticButtonDown[]`. Pushed events set
  neither, so every held-button gesture silently never fired. Two the user hit:
  - **Hold POWER to sleep.** `main.cpp:573-574` needs
    `gpio.isPressed(BTN_POWER) && gpio.getPowerButtonHeldTime() > 400`; the
    second call returned 0 at its early exit, so the device could only ever
    sleep on the inactivity timeout.
  - **Hold a side button to cycle font family.**
    `EpubReaderActivity.cpp:648-665` needs
    `ReaderUtils::detectHeldSideDirection()` (which is `isPressed()`) and
    `getHeldTime() >= 700`; both were dead, so the branch was unreachable. The
    font-SIZE tap in the same block survived, because it reads a release edge.

The fix, in `HalGPIO`; the firmware does not change and no `#ifdef` is needed:

1. **A live injection API** — platform-neutral
   `HalGPIO::injectButtonDown/Up(uint8_t)`, writing the press edge, the held
   level and the `SDL_GetTicks()` press timestamp together.
   `processSyntheticEvents()` (the `CROSSPOINT_SIM_INPUT_SCRIPT` batch) and the
   `S` sleep shortcut were refactored onto it, so there is one code path and the
   script env var is now a second caller of the same API rather than a parallel
   implementation.
2. *(not taken)* **Make the keyboard path level-consistent** — have `update()`
   also set `syntheticButtonDown[]` on KEYDOWN/KEYUP. Keeps the translation point
   at SDL, but needs focus-loss handling so a real held key cannot stick.

Verified on the desktop binary, which runs the identical `injectButtonDown/Up`
code the pad now calls, driven through `CROSSPOINT_SIM_INPUT_SCRIPT`:

- `4000:P:2000` → `[4430] [MAIN] Entering deep sleep`, i.e. 430 ms after the
  injected press, matching `getPowerButtonDuration()` = 400 ms. A later
  `9000:P:300` woke it: the relaunched process logged
  `Verifying power button press duration`, which is reached only when
  `getWakeupReason() == PowerButton`.
- `6000:DOWN:1400` in the reader → `[6743] Loaded /.fonts/Edgar/Edgar_12.cpfont`
  and `sdFontFamilyName` `Coelacanth` → `Edgar`, i.e. the family cycled 743 ms
  into the hold (`SKIP_HOLD_MS` = 700).
- `6000:DOWN:150` (a tap) stepped `fontSize` 0 → 1 and left the family alone, so
  the edge path is not regressed and hold/tap still disambiguate.

### Closed: the wake path no longer execs on iOS

This section previously described `rebootAsPowerWake()`'s `execvp()` as an open
problem on iOS. It was closed by `10a8c5a` ("fix(ios): wake from deep sleep
without exec"): `SimulatorLifecycle.h` defines `CROSSPOINT_SIM_REBOOT_IN_PROCESS`
for `__APPLE__ && TARGET_OS_IPHONE`, and `SimulatorLifecycle.cpp` takes a
`std::longjmp` back to the armed jump buffer before the `execvp()` line can be
reached. The exec is still compiled into the iOS binary but is unreachable there.

Leaving the stale text in place cost a later investigation real time — it is the
first suspect anyone reads. The actual iOS wake bug was downstream of the jump:
the firmware's inactivity clock was a `loop()`-local static, so it survived the
longjmp holding its pre-sleep value and the first post-wake `loop()` immediately
auto-slept again. Fixed in the firmware by hoisting it to file scope and
resetting it in `setup()`, next to the same reset for `deepSleepInProgress`.

## Resolved along the way

- **Both `run_simulator.py` build-time patches are dead.** Its docstring
  describes two patches CMake would need to replicate; the implementing code no
  longer exists in the 63-line script. `BookMetadataCache` `size_t` → `uint32_t`
  is already a real source edit upstream
  (`lib/Epub/Epub/BookMetadataCache.h:23`), so there is no cache-corruption risk
  on arm64. The `GfxRenderer::setOrientation` notify is superseded by polling:
  `setOrientation` is a bare setter (`GfxRenderer.h:150`) and
  `presentIfNeeded` re-reads `getOrientation()` every present
  (`HalDisplay.cpp:395-396`). The stale docstring is worth deleting.
- **SDL2 → SDL3 is done, on both toolchains.** Four files touched SDL
  (`HalDisplay.cpp/.h`, `HalGPIO.cpp`, `simulator_main.cpp`). The desktop
  PlatformIO env moved to SDL3 at the same time (`!pkg-config --cflags --libs
  sdl3`), so there is one source set and no per-platform SDL shim. The only
  non-mechanical change was `SDL_GetKeyboardState` returning `const bool*`
  instead of `const Uint8*`.
- **Presentation policy is keyed on intent, not platform.**
  `CROSSPOINT_SIM_PIXEL_EXACT` selects `INTEGER_SCALE` + `SCALEMODE_NEAREST`;
  without it the desktop keeps letterbox + linear filtering, which is right at
  1:1 because Bayer dither averaging to gray is what e-ink actually looks like.
  A desktop build can ask for exact pixels too.

## Still deferred

- **Tilt.** `HalTiltSensor::begin()` sets `_available = true` for
  `SIMULATOR_DEVICE_X3` while every predicate hard-returns false and there is no
  injection hook. **Leave it that way** — the real X3 does carry the sensor
  (`ImuType::Qmi8658` in the X3 board profile), and forcing it false would hide a
  capability the hardware exposes. Known, accepted dead zone.
- **Physical device.** Signing identities exist; no iPhone Air is paired.
- **WiFi.** Landed. [WIFI.md](WIFI.md) is the plan and the running state. The
  radio backend ([CrossPointWiFi.mm](CrossPointWiFi.mm)), the bind-address
  switch, Bonjour (`ESP.cpp`) and the in-process HTTP client
  ([CrossPointHttp.mm](CrossPointHttp.mm)) are all in, and the firmware's gate
  split happened on 2026-08-07: `CROSSPOINT_NO_NETWORK` is gone, replaced by the
  narrower `CROSSPOINT_NO_DEVICE_FLASH`, which gates only OTA and SD Firmware
  Update — the two things that write an ESP32 partition a phone does not have.
  Wi-Fi Networks, File Transfer, font downloads and Claude are all in the iOS
  build and reachable from the UI.

  A phone still cannot impersonate the X3's radio — no scan API, no soft AP —
  but peer transfer needs neither: it happens over whatever WiFi the phone is
  already on. The Apple-only paths have no automated coverage; there is no Mac
  in the loop for them, so [../tests/wifi_host_test.cpp](../tests/wifi_host_test.cpp)
  exercises the logic against a scripted backend and the rest is device
  observation. **Compiling and linking is now verified** — `crosspoint_core` and
  the `CrossPointX3` app target both build for `arm64-apple-ios` with every
  network TU included — but "the transfer actually works from another machine"
  is still unconfirmed on hardware.

## Rejected reading-UX proposals — do not re-propose

Owner rulings, 2026-08-04, from a round of "what would help distraction-free
reading". All four were rejected. They are written down because each one is the
sort of idea that reads as obviously good in the abstract and gets re-invented
by the next session.

| Proposal | Ruling |
| --- | --- |
| Hide or auto-hide the home indicator; defer the bottom screen edge to make swiping out take two swipes | **No.** "The bottom bar has been fine." Covers the *whole* bottom edge, gesture as well as pixels — this was re-proposed once in the same conversation as a swipe change rather than a visual one and rejected again. |
| Dim below the iOS brightness floor | **No.** Dark mode already covers it. |
| Fade or auto-hide the button pad after idle | **No.** "The buttons are already low contrast and animating them is very distracting and hostile." |
| A "you've been reading a while" mark or session timer | **No.** "The opposite of what we are trying to solve." |

The principles underneath, which are the reusable part:

- **Nothing on the page moves.** Animation is not a way to reduce distraction;
  it *is* the distraction. This rules out fades, auto-hide, reveal-on-touch and
  anything else that changes the screen while the owner is reading it.
- **The goal is staying in the book, not moderating it.** Anything that
  interrupts to inform — elapsed time, progress nudges, streaks — solves
  stopping, and stopping is not the problem.
- **Do not invent the problem.** Accidental exits, glare and screen clutter were
  all proposed without the owner ever reporting them. An idea whose motivation
  came from the assistant rather than from use is the failure mode here.

A fifth, a **Focus Filter** (App Intents, so opening the app silences other
notifications), was also rejected. It was offered as the survivor on the grounds
that it addressed interruptions arriving rather than attention wandering. That
did not save it either.

**So the topic is closed.** Nothing in this area is open, and the correct number
of unprompted "this would help you focus" proposals is zero. The reading surface
is the panel and the pad, and it is finished unless the owner says otherwise —
which is the same ruling the firmware's own SOUL doc reached about feature
sprawl, arrived at from the other direction.

## Source-set translation

`cmake/CrossPointSources.cmake` is **generated**, never hand-edited — 135
firmware TUs, 20 simulator TUs, 24 include dirs, 14 defines, derived from the
PlatformIO env that already works:

```bash
cd $HOME/src/crosspoint-reader
pio run -e simulator -t compiledb
python3 <simulator>/tools/gen_cmake_sources.py --firmware-dir . --compile-db compile_commands.json
```

The root `CMakeLists.txt` validates every listed path at configure time and fails
loudly with the regeneration command if any has moved. On a fork the firmware
moves under you continuously, so a hand-maintained list would rot silently.

Notable: the `simulator` env compiles **zero third-party TUs**. ArduinoJson is
header-only, and QRCode/WebSockets are shimmed by the simulator itself, so SDL is
the only real external dependency.

## Keeping the desktop build green

The desktop build is the canary: green desktop + red iOS means the harness is
wrong; both red means the HAL drifted. Build desktop first whenever iOS fails.

```bash
cd $HOME/src/crosspoint-reader && pio run -e simulator
```

For that to carry signal it must compile *this* working copy, so the firmware's
`[env:simulator]` `lib_deps` uses
`simulator=symlink:///Users/natebunnyfield/src/crosspoint-simulator` rather than
the upstream git URL. Verified live by appending `#error` to `HalGPIO.cpp` and
confirming the build failed with it.

### Preset list (ruling 2026-08-15)

Eleven rows now, appended in this order and **append-only** — the value persists
as an integer, so inserting one re-points every saved choice:

| # | Preset | Light | Dark |
|---|---|---|---|
| 1 | Default | 13.29:1 | 14.17:1 |
| 2 | High Contrast | 21.00:1 | 21.00:1 |
| 3 | Sepia | 10.23:1 | 12.79:1 |
| 4 | Cool Gray | 13.17:1 | 14.24:1 |
| 5 | Solarized | **4.13:1** | **4.75:1** |
| 6 | Green CRT | 10.31:1 | 13.50:1 |
| 7 | Amber CRT | 10.13:1 | 10.25:1 |
| 8 | Nord | 10.84:1 | 9.25:1 |
| 9 | Gruvbox Light | 10.22:1 | 10.75:1 |
| 10 | Catppuccin Latte | 7.06:1 | 11.34:1 |
| 0 | Custom | — | — |

**Solarized is the one preset exempt from the 7:1 floor**, and the exemption is
by NAME rather than by relaxing the floor. Its low contrast is the palette's
thesis; raising it produces something that is not Solarized. `isLowContrastByDesign()`
carries the exemption and `tests/panel_palette_test.cpp` asserts that exactly
one preset may claim it, so a second cannot arrive inside a palette commit.

**Solarized ships as ONE row, not two.** Every preset's dark half must be
light-on-dark — the polarity assertion rejects anything else, and a
"Solarized Light" row that stayed light in dark mode would hand back a blinding
page at night. So the row pairs the two authentic variants: Solarized Light by
day, Solarized Dark by night.

The CRT rows are honest about which half is real: the DARK half is phosphor on
a black tube, the authentic article. A lit CRT has no light mode, so the light
half keeps the hue instead — deep phosphor ink on paper tinted the same way.

**Rendering a palette headlessly needs the SETTING, not just the env var.**
`CROSSPOINT_SIM_DARK=1` is applied inside `setPanelDark`, but `main.cpp:781`
runs `display.setInverted(SETTINGS.darkMode != 0)` afterwards and wins, so a
desktop capture comes out light no matter what the env says. Set `darkMode` in
`fs_/.crosspoint/settings.json` to capture a dark half:

```bash
CROSSPOINT_SIM_PANEL_INK_DARK=33FF33 CROSSPOINT_SIM_PANEL_PAPER_DARK=001A00 \
CROSSPOINT_SIM_SCREENSHOTS="4000:/tmp/shot.png" SDL_VIDEODRIVER=dummy \
  .pio/build/simulator/program        # with darkMode=1 in settings.json
```

Captures are written by `SDL_SaveBMP` — the file is a BMP whatever you name it.

### Running it on the iOS Simulator

Worth knowing before the first build: **seed fonts are opt-in**.
`CROSSPOINT_IOS_SEED_FONTS_DIR` defaults to empty, and the build recipe above
does not pass it, so a plain build produces an app with NO `.cpfont` resources
at all — 19 MB instead of 202 MB. That is deliberate (the 183 MB `ios/seedfonts/`
is gitignored, so a clone without it must still build), but it means a bundle
with no fonts is not evidence of a bundling bug. Pass the directory to get them:

```bash
cmake -B build/ios-app -DCROSSPOINT_IOS_SEED_FONTS_DIR=$PWD/ios/seedfonts
cmake --build build/ios-app --config Debug --target CrossPointX3
```

Verified 2026-08-15: that bundles 24 `.cpfont` files at each of 1x, 2x and 3x
across all six installed families — both hi-res tiers, which is what the render
scale setting needs to change tier without a rebuild.

Install and drive it:

```bash
D=$(xcrun simctl list devices available | grep -o '[0-9A-F-]\{36\}' | head -1)
xcrun simctl boot $D
xcrun simctl install $D build/ios-app/ios/Debug-iphonesimulator/CrossPointX3.app
xcrun simctl spawn $D defaults write com.natebunnyfield.crosspoint.x3 panelPalettePreset -int 6
xcrun simctl launch $D com.natebunnyfield.crosspoint.x3
xcrun simctl io $D screenshot /tmp/shot.png
xcrun simctl spawn $D log show --last 60s --predicate 'processImagePath CONTAINS "CrossPoint"' | grep panel
```

`defaults write` on the booted simulator is the only way to exercise a
Settings.app row without tapping through Settings by hand, and it is what proved
the palette path end to end.
