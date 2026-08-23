#pragma once

// iOS-native preferences, read from the Settings app (Settings.bundle).
//
// SEPARATE FROM THE FIRMWARE'S SETTINGS ON PURPOSE. Everything else the owner
// can configure lives in settings.json and is edited on the emulated e-ink
// panel, because it is the reader's own state and travels with the SD card.
// These are not: they are properties of THIS PHONE running the app, they mean
// nothing on device hardware, and the natural place to look for them is
// Settings > CrossPoint X3.
//
// The firmware's own "Keep Screen Awake" row still exists and is untouched;
// which of the two wins on iOS is an open decision, see the note in
// simulator_main.cpp's applyKeepScreenAwake().

#ifdef __cplusplus
extern "C" {
#endif

// Should the host display be held awake right now?
//
// 1 = keep awake, 0 = let iOS dim and lock normally. Answers for the CURRENT
// power state: the owner sets sleep behavior separately for battery and for
// charging, because reading propped on a charger and reading in bed are
// different situations and the same answer does not serve both.
//
// Safe to call every frame and from a non-Objective-C translation unit. Main
// thread only — it touches UIDevice.
int CrossPointPrefs_wantsScreenAwake(void);

// How far the button pad's outline / pressed wash sits from the field behind it.
//
// One signed scale, -9..9, clamped. 0 means the tone EQUALS the field, so the
// control draws nothing; negative is darker than the field, positive is
// lighter, and +/-9 is the end of the gamut. The two tones are set separately
// because the stroke covers a line and the wash covers a whole cell, and the
// answer is stored per appearance because light and dark have opposite
// headroom. `dark` is 1 for the dark appearance, 0 for light.
//
// The level indexes the delta tables in ios/PadPalette.h; the mapping from
// level to a measured contrast ratio lives there and in Root.plist's row
// labels, not here.
//
// THESE TWO ARE ONLY CONSULTED WHEN THE PRESET BELOW IS Custom. They are read
// and clamped regardless, so the caller can resolve the pair itself
// (padpalette::resolveLevels) and so that switching back to Custom restores
// whatever the owner last dialled in.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_padOutlineContrast(int dark);
int CrossPointPrefs_padFillContrast(int dark);

// Which named pad-contrast preset is selected: one of padpalette::Preset
// (0 Custom, 1 Current, 2 Accessible, 3 Transparent). Anything else is returned
// unchanged and resolved as Current by padpalette::resolveLevels, which is the
// safe direction — an unknown value must not produce an invisible pad.
//
// Current is the default and is the shipped look, so an untouched install is
// pixel-identical to the build before presets existed.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_padContrastPreset(void);

// Is zen mode on? 1 = just the page: the button pad disappears and the screen
// becomes three big tap targets. Same state the three-finger gesture and the
// CROSSPOINT_SIM_ZEN env var toggle; the setting is authoritative only when its
// stored value CHANGES (compare-applied in the shim's pollZenMode), so the
// gesture keeps working between edits. Missing-key failure mode is benign — NO
// is the shipped default.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_zenModeEnabled(void);

// Is read-aloud TTS enabled? 1 = read the open book aloud (see
// CrossPointReadAloud.h), 0 = off, the default. A phone property like the
// rest of this file: the device hardware has no speaker, so the setting
// means nothing in settings.json.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_readAloudEnabled(void);

// How fast read-aloud speaks, as a PERCENTAGE OF NORMAL: 100 is the system's
// default speaking rate, 50 is half, 200 is double. Clamped to 25..300.
//
// A percentage rather than AVSpeechUtterance's own 0..1 scale, and the
// conversion lives in the adapter, because that scale is not a rate at all --
// its midpoint 0.5 is normal speech and the number means nothing to anyone
// reading a settings row. The stored value has to survive a restored backup
// and a hand-edited plist, which is why the clamp is here and not only in the
// picker's list of steps.
//
// NOTE the system's own Spoken Content > Speaking Rate slider does NOT reach
// AVSpeechUtterance -- it applies to VoiceOver and Speak Screen. Without this
// key there is no speaking-rate control for this feature at all.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_readAloudRatePercent(void);

// Diagnostics file logging (diagnostics/a11y.log + tree dumps + probes).
// Default OFF; Settings.app toggle re-arms it without a rebuild.
int CrossPointPrefs_diagnosticsEnabled(void);

// Which named panel palette is selected: one of panelpalette::Preset
// (0 Custom, 1 Default, 2 High Contrast, 3 Sepia, 4 Cool Gray). Anything else
// is returned unchanged and resolved as Default by panelpalette::resolve --
// the safe direction, since an unknown value must not produce an unreadable
// page.
//
// Default is the default and is the shipped look, so an untouched install
// renders pixel-identically to the build before this existed.
//
// Safe to call every frame. Main thread only.
// BEAM PAINT: how long the new page takes to sweep in from the top, in ms.
// 0 (the default) is off -- the page arrives at once, as an e-ink panel's does.
//
// The stored value IS the duration, not a row index, so the picker's rows can
// be retuned or reordered without a migration and without a saved choice
// silently changing speed. Clamped to 0..1000 on read.
//
// Safe to call every frame. Main thread only.
// PAGE FADE: how long the page takes to dim after the last input, in SECONDS.
// 0 (the default) is off. Clamped to 0..600 on read.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_pageFadeSeconds(void);

// PAGE FADE DEPTH: how FAR that fade goes, as the percentage of the palette's
// legible floor that is kept. 100 (the default) stops where the page is still
// at WCAG AA body text -- what shipped before this setting. 0 is fully
// transparent: the page fades away entirely. Clamped to 0..100 on read.
//
// Owner-elected below 100; the contrast given up at each step is written out at
// pagefade::floorFor() in src/PageFade.h.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_pageFadeDepthPercent(void);

// PHOSPHOR GRAIN. Strength as a percentage of what a real settled-powder screen
// has: 0 is off, 100 is realistic and the default, 1000 is 10x. Coverage is a
// phosphorgrain::Coverage integer (0 Even, 1 Vignette, 2 Mottled, 3 both).
// PER APPEARANCE, like the pad's contrast pair beside it (owner 2026-08-19).
// The same grain reads very differently on a black page and a white one: what
// is a whisper on paper is invisible on a dark screen, so one number cannot
// serve both. `dark` is 0 for light, 1 for dark. Defaults: 60 light, 160 dark.
int CrossPointPrefs_phosphorGrainPercent(int dark);
int CrossPointPrefs_phosphorGrainCoverage(void);
// Blotch size (cells across the long edge) and blotch depth in HUNDREDTHS.
int CrossPointPrefs_phosphorGrainMottleDepth(void);

int CrossPointPrefs_beamPaintMs(void);

// Whether the 1-bit pass may land on its own, ahead of the composed frame.
int CrossPointPrefs_presentFlash(void);

// THE 2026-08-22 DOCTRINE DIALS. Light mode is paper and ink: LETTERPRESS,
// percent of standard (0 off, 50 subtle -- the default -- 100 standard, 200
// heavy). Dark mode is a CRT: SCANLINES replace the mottled grain, percent of
// standard (0 off, 50 subtle -- the default -- 100 standard, 150 deep; the
// blotch depth is folded into the dial by scanlines::mottleDepthFor). While
// either is active in its mode the grain pass is skipped by HalDisplay.
int CrossPointPrefs_letterpressPercent(void);
int CrossPointPrefs_scanlinesPercent(void);

// PAPER DEFECTS: how marked the light page's sheet is, 0..100 (0 a fresh sheet
// and bit-exact off, 30 the default, 100 a thoroughly used book). An INCIDENCE
// dial. FROZEN at 0 on 2026-08-23 with no control anywhere that reaches it --
// the Settings.bundle row and then the light drawer's slider both went. The
// setter went with them. Model: src/PaperDefects.h; design:
// docs/paper-defects.md.
int CrossPointPrefs_paperDefectsPercent(void);

// SCANLINE SIZE: the line pitch, as a percent of the SOURCE-ROW pitch (owner
// order 2026-08-22, from build 126). 100 = one line per page row, the pitch
// build 126 shipped and the default here; 150 / 200 / 300 are one line per
// 1.5 / 2 / 3 rows. Multiples of the page's own lattice rather than absolute
// pixels, so no rung can lay a second lattice over the panel -- see
// scanlines::pitchFor.
int CrossPointPrefs_scanlineSizePercent(void);

// SCANLINE BLOOM: how far beam current widens the lit band, as a percent of
// the standard gain (owner order 2026-08-22). 0 off (bit-exact -- the field
// stops being content-aware), 50 subtle, 100 standard (build 126's value, and
// the default), 200 strong, 400 extreme. A fraction of the PITCH, so it stays
// proportionate at every scanline size.
int CrossPointPrefs_scanlineBloomPercent(void);

// SHOW-THROUGH from the other side of the leaf, percent of the reference
// sheet's (roadmap 1a). FROZEN 2026-08-23: the quantity that varies is the
// STOCK's thinness, which the paper picker already owns, and the picker
// multiplies its factor into this before pushing. Light pages only.
int CrossPointPrefs_showThroughPercent(void);

// CORNER DEFOCUS, percent of the standard tube (roadmap D3). FROZEN
// 2026-08-23: it is set by a tube's geometry under TG18's astigmatism bound,
// not by taste. Dark pages only, and it modulates the scanline raster rather
// than drawing a field of its own.
int CrossPointPrefs_cornerDefocusPercent(void);

// THE POWER-OFF COLLAPSING DOT (roadmap D8). 1 = at sleep the picture squeezes
// to a bright line, the line closes to a dot, and the dot fades -- after which
// the glass stays DARK for the rest of the sleep instead of holding the sleep
// screen. That trade is why this is a Settings row rather than a frozen value,
// and why it ships off. Dark pages only.
int CrossPointPrefs_powerOffCollapse(void);

// CrossPointPrefs_zenBottomRatio was RETIRED 2026-08-22: the zen band
// proportion is a constant 1:2 (Van de Graaf) in the shim now, so the setting
// row died with it (a one-option row is decoration). Stored values are ignored
// orphan keys.

int CrossPointPrefs_panelPalettePreset(void);

// Write it. Settings.app owns this key too, and both write the same
// NSUserDefaults store, so the in-app picker is not a second source of truth --
// it is a second editor of the one store. pollPanelPalette() in the shim
// notices the change on the next frame and repaints; nothing else is needed.
void CrossPointPrefs_setPanelPalettePreset(int preset);

// The owner's custom panel tone for one appearance and one role, as packed
// 0xRRGGBB, or -1 (panelpalette::kInvalidColor) when the field is empty or does
// not hold six hex digits. `dark` is 1 for the dark appearance; `ink` is 1 for
// the ink and 0 for the paper.
//
// A HEX STRING RATHER THAN A COLOR WELL because a Settings.bundle has no color
// specifier -- PSTextFieldSpecifier is the only one that can carry an arbitrary
// color. Parsing (and the -1 for junk) lives in src/PanelPalette.h so it is
// host-testable; this function only fetches the string.
//
// ONLY CONSULTED WHEN THE PRESET ABOVE IS Custom, on the same terms as the pad's
// four fine pickers: read and returned regardless, so switching back to Custom
// restores whatever the owner last typed.
//
// Safe to call every frame. Main thread only.
int CrossPointPrefs_panelCustomColor(int dark, int ink);

// The supersampling factor the panel is rendered at: 1, 2 or 3 framebuffer
// pixels per logical pixel on each axis. Clamped by cp::setRenderScale() to
// [1, CROSSPOINT_RENDER_SCALE], the ceiling this binary was compiled at, so a
// stale or hand-edited value can never ask for a framebuffer bigger than the
// one that was allocated.
//
// READ ONCE, AT LAUNCH -- unlike everything else in this file. The factor sizes
// the SDL texture and selects which hi-res glyph tier is registered, both of
// which are committed before the first frame, so a change takes effect on the
// next launch. That is stated in the Settings footer rather than left to be
// discovered. See RenderScale.h and docs/ios-render-scale.md.
//
// Defaults to 3, which is what the app has always rendered at
// (CROSSPOINT_IOS_RENDER_SCALE in ios/CMakeLists.txt), so an untouched install
// is pixel-identical to the build before this setting existed.
//
// Main thread only.
int CrossPointPrefs_renderScale(void);

#ifdef __cplusplus
}
#endif
