#pragma once

#include <cstdint>

#include "SimulatorDials.h"

struct SDL_Renderer;

// Simulator-only chrome drawn outside the panel.
//
// Deliberately NOT a HalDisplay method: the HAL's public surface must mirror the
// firmware's, and an on-screen button pad has no analog on real hardware. This is
// a free hook the presentation path calls, so the HAL stays the shape the
// firmware expects.
//
// The callback runs with logical presentation DISABLED and receives the real
// output size, so it draws in device pixels and can paint the letterboxed
// margins that the panel's logical coordinate space cannot reach.
namespace SimulatorOverlay {

using DrawFn = void (*)(SDL_Renderer *renderer, int outWidthPx, int outHeightPx);

// Register (or clear, with nullptr) the overlay painter.
void setDrawCallback(DrawFn fn);

// The color the presentation path clears to before the panel is drawn: the
// field the panel sits on. Defaults to white, which matches a blank e-ink page
// so the panel edge is invisible. On desktop the window is exactly panel-sized
// and the field never shows, so nothing there needs to call this; a host that
// letterboxes the panel (the phone presents it at 2x inside a taller screen)
// sets it to whatever its own appearance calls for.
void setClearColor(unsigned char r, unsigned char g, unsigned char b);

// Ask for a repaint. The firmware only presents when it has new panel content,
// which on an e-ink device is rare -- without this a button's pressed state
// would not appear until the next page render.
void requestPresent();

// Reserve the bottom `px` device pixels of the output for overlay chrome: the
// panel is fitted TOP-ALIGNED in the space ABOVE the band instead of centered
// in the whole output, so a button pad can sit directly under the panel's
// bottom edge without ever overlapping panel content (the firmware draws its
// own button-hint bar along that edge). 0 (the default) keeps the plain SDL
// letterbox path, which is what every desktop build uses. Honours the
// pixel-exact policy: with INTEGER_SCALE presentation the manual fit also
// floors to an integer scale.
void setBottomInset(int px);

// Reserve the top `px` device pixels for the host's own furniture -- on a phone
// the status bar and, on an Island/notch device, the cut-out. The manual fit is
// TOP-ALIGNED, so without this the page starts within 16px of y=0 and the first
// lines of text are drawn under the Island. Same units and same effect as
// setBottomInset: with either band set, the panel is fitted into the space
// BETWEEN them. 0 (the default) is what every desktop build uses.
void setTopInset(int px);

// Where the panel's bottom edge landed on the last present, in device pixels
// (0 until the first manual-placement present). The pad anchors to this so it
// hugs the page for thumb reach instead of sinking to the screen bottom.
int panelBottomPx();

// The panel's presented height on the last present, in device pixels (0 until
// the first manual-placement present). Lets the pad scale hardware-derived
// proportions (the chassis panel-to-buttons gap) with the presented panel
// instead of hardcoding screen points.
int panelHeightPx();

// The panel's presented left edge and width, same units and same lifecycle
// as the pair above (0 until the first manual-placement present). Together
// the four give the full presented rect, which is what maps logical panel
// coordinates to the glass: the read-aloud highlight painter and tap
// hit-test scale by panelWidthPx / <logical portrait width> and offset from
// (panelLeftPx, panelBottomPx - panelHeightPx).
int panelLeftPx();
int panelWidthPx();

// The reader's FINAL text-block insets — top after the firmware's paint-time
// cap-ink trim, then right, bottom, left — in FRAMEBUFFER pixels, as published
// by EpubReaderActivity through HalGPIO::publishReaderTextInsets on every
// render. Returns false until the first page render publishes (a caller keeps
// its own fallback then). Device px = value * (presented panel size /
// HalDisplay::active* framebuffer size). Implemented in HalGPIO.cpp beside the
// publisher; declared here because this namespace is already the host-facing
// window onto panel geometry (panel*Px above).
bool readerTextInsetsPx(int &top, int &right, int &bottom, int &left);

// WHICH PAGE OF WHICH BOOK IS ON SCREEN, as published by every reader activity
// through HalGPIO::publishReaderPageIdentity on every displayed page. Returns
// false until a book has rendered once — a boot into a menu has no page, and
// the caller keeps its launch-seeded field then.
//
// The consumer is the LIGHT page's paper: both letterpress fields seed from
// hash3(lo32(bookKey), hi32(bookKey) ^ spineIndex, pageInSpine) with NO launch
// term, which is what makes a revisited page the same sheet across a relaunch.
// Declared here rather than on HalDisplay for the same reason as everything
// else in this namespace: nothing in the firmware could ever consume it, and
// the HAL surface must stay the firmware's shape. Implemented in HalGPIO.cpp
// beside the publisher.
bool readerPageIdentity(uint64_t &bookKey, int &spineIndex, int &pageInSpine);

// THE SHEET the screen on glass is printed on, as a seed, whether that screen
// is a book page or a system screen — the resolved form of the two publishers
// above and the only thing the light fields read. Returns false only before
// the first activity has entered, which on a healthy firmware is a handful of
// milliseconds at boot; the caller keeps its launch-seeded field until then.
//
// Separate from readerPageIdentity() rather than replacing it, because the two
// answer different questions: that one is still the truth about which page of
// which book was last displayed, and a screen entered on top of a book does not
// make it false. Implemented in HalGPIO.cpp beside both publishers.
bool sheetIdentitySeed(uint32_t &seed);
// True when the sheet identity above came from a reader page rather than from a
// system screen. Show-through is gated on it -- owner 2026-08-24, "do not have
// verso bleed outside of reading mode" -- and nothing else reads it, because
// every other sheet field is a property of the stock and a menu is printed on
// the same paper as a page.
bool sheetIsReaderPage();
// True while the firmware has a text field open. The letterpress pass holds its
// cached field while this is set -- see ensureLetterpressTexture.
bool textEntryOpen();
// The firmware has entered its sleep screen. The page-polarity latch stops
// sampling here -- see the note at sleepScreenEnteredValue in HalGPIO.cpp.
bool sleepScreenEntered();

// Panel polarity driven by the host appearance: dark renders the panel
// white-on-black through HalDisplay's inversion flag. A free hook rather than
// a HAL method for the same reason as the rest of this namespace -- following
// a host theme has no analog on real hardware, and the HAL surface must stay
// the firmware's shape.
//
// Takes effect on the very next present, not the next firmware refresh:
// inversion is applied while converting the 1bpp framebuffer to pixels, so
// HalDisplay re-runs that conversion from its cached last frame when the flag
// changes (see reconvertLastFrame in HalDisplay.cpp).
//
// CROSSPOINT_SIM_DARK overrides the argument: "1" forces dark, "0" forces
// normal, unset follows the caller. Both the platform-theme path (the iOS
// harness) and the env path land here, so exercising either verifies the
// other's mechanics.
void setPanelDark(bool dark);

// The panel's two tones for ONE polarity: what a fully-black source pixel is
// drawn as (ink) and what a fully-white one is drawn as (paper), each three
// bytes RGB. Every level in between is interpolated from the pair, which is why
// there is no separate control for the intermediate 2-bit grays -- move the two
// ends and the grays move with them, in proportion.
//
// A free hook rather than a HAL method, for the same reason as the rest of this
// namespace: a real e-ink panel has one set of tones, decided by its physics,
// and nothing in the firmware could ever call this.
//
// Both polarities default to the tones this app has always drawn
// (panelpalette::kDefaultLight / kDefaultDark in src/PanelPalette.h), so a host
// that never calls this -- every desktop build -- is pixel-identical.
//
// Takes effect on the very next present, not the next firmware refresh: the
// tones are applied while converting the 1bpp framebuffer to pixels, so
// HalDisplay re-runs that conversion from its cached last frame, exactly as it
// does for a polarity change. Writing the polarity that is NOT on screen only
// stores, so a host may publish both on every settings change.
//
// Setting the ON-SCREEN polarity also moves the field (setClearColor) to the
// new paper, so the page keeps its edgeless seam against whatever the host
// paints around it.
//
// CROSSPOINT_SIM_PANEL_INK_LIGHT / _PAPER_LIGHT / _INK_DARK / _PAPER_DARK
// override the argument, "RRGGBB" / "#RRGGBB" / "0xRRGGBB"; unset or
// unparseable follows the caller. Same contract as CROSSPOINT_SIM_DARK above,
// and the reason is the same: it is the only way a desktop or headless run can
// reach a non-default palette, since the owner-facing control is in the iOS
// Settings app.
void setPanelPalette(bool dark, const unsigned char ink[3],
                     const unsigned char paper[3]);

// Whether the page EMITS its light rather than reflecting it.
//
// It changes one thing: how a partly-covered (antialiased) pixel is mixed. A
// phosphor emitting half its light is a linear-light mix; pigment on paper is
// not, and the integer lerp that ships for e-ink is the contract for it. On a
// dark CRT page the difference is most of the edge ramp -- reported from the
// phone as "the antialiasing on the sans serif fonts looks bad in crt", which
// it did, because every edge pixel was landing a third too dark.
//
// Default false, so every e-ink palette renders exactly the pixels it always
// did. CROSSPOINT_SIM_PANEL_EMISSIVE=1/0 overrides the argument, same contract
// as CROSSPOINT_SIM_DARK.
void setPanelEmissive(bool emissive);

// PAGE FADE: how long the page you are READING takes to decay after the last
// input, in milliseconds. 0 is off, the default, and the entire desktop
// behaviour.
//
// Distinct from the glow, and the distinction is the feature: the glow fades
// the PREVIOUS page out as the next arrives, over a fraction of a second. This
// fades the page in front of you, over seconds or minutes, the way a phosphor
// screen goes on dimming after the beam has moved on.
//
// It decays toward the PAPER (a phosphor dying, which is what was asked for)
// and STOPS at a legible floor -- a page that fades to nothing is a page you
// cannot finish reading. notePageInteraction() re-energises it; any input
// should call that.
//
// CROSSPOINT_SIM_PAGE_FADE_MS overrides the argument.
void setPageFade(float fadeMs);

// PAGE FADE DEPTH: how far that decay goes, as a percentage of the palette's
// legible floor that is KEPT. 100 is the default and is the floor described
// above -- a build that never calls this is pixel-identical to one that cannot.
// 0 is FULLY TRANSPARENT: the page fades all the way to paper.
//
// The steps between are proportions of the same per-palette figure, so a
// low-contrast page still fades less far than a high-contrast one at the same
// setting. Below 100 the WCAG floor is deliberately given up -- owner ruling
// 2026-08-18, with the measured contrast at each depth written out at
// pagefade::floorFor(). Clamped to 0..100.
//
// CROSSPOINT_SIM_PAGE_FADE_DEPTH overrides the argument.
void setPageFadeDepth(int depthPercent);

// Something happened: restart the fade from full. Cheap and safe to call on
// every input event -- it returns immediately when the fade is off.
void notePageInteraction();

// BEAM PAINT: how long the new frame takes to sweep in from the top of the
// page, in milliseconds. 0 is off, which is the default and the entire desktop
// behaviour.
//
// A CRT does not swap pictures, it DRAWS them: the beam runs top to bottom at
// the field rate, and until it arrives a given line still shows the previous
// frame. That is a different claim from the glow -- the glow says what becomes
// of a pixel after it is lit, the beam says the picture arrives progressively
// rather than all at once -- so they compose rather than overlap.
//
// The HAL is told a DURATION, not a preset, for the same reason the glow is:
// which rate is wanted is a host question.
//
// CROSSPOINT_SIM_BEAM_MS overrides the argument, for a desktop or headless run
// with no Settings app to reach the control.
void setBeamPaint(float sweepMs);

// PHOSPHOR GLOW: how long the previous frame lingers, in milliseconds. 0 is off,
// and off is the default and the entire desktop behavior.
//
// A CRT does not switch pictures, it decays into them: the beam repaints and
// what was there fades at a rate that is a property of the phosphor. With this
// set, presentIfNeeded keeps the previous panel image and fades it out over
// `trailMs` on TOP of the new one, so every transition the panel makes -- page
// turn, menu move, selection -- ghosts instead of cutting.
//
// The HAL is deliberately told a DURATION and not a preset. Which phosphor is
// selected, whether the owner turned the effect on, and how the published decay
// figures are scaled are all host questions; this layer only knows how long to
// hold a ghost. Same division as setPanelPalette, which is handed tones rather
// than a preset number.
//
// The published figures are 2-33 ms (see panelpalette::PresetInfo), which is one
// to two frames and invisible -- so a host is expected to scale them. It is the
// RATIO between phosphors that is real; the multiplier is a taste decision and
// belongs where taste lives, not here.
//
// CROSSPOINT_SIM_PANEL_GLOW_MS overrides the argument, for a desktop or headless
// run that has no Settings app to reach the control.
void setPanelGlow(float trailMs);

// The color the trail decays TOWARD, for a two-layer phosphor. Null means the
// trail keeps the tone it was drawn in, which is every ordinary phosphor.
//
// P7 is the reason this exists. It is a cascade -- a blue-white ZnS:Ag flash
// over a (Zn,Cd)S:Cu layer that keeps emitting for over a minute -- so what
// lingers is not a dimmer copy of what was written, it is a DIFFERENT COLOUR.
// Fading toward zero would lose exactly the property the phosphor is known for.
//
// Applied as a color multiply on the ghost that ramps in as it decays: at full
// brightness the trail is what was drawn, and by the end it is this hue.
// CROSSPOINT_SIM_PANEL_GLOW_TAIL overrides the tint argument, "RRGGBB".
//
// `onsetMs` is WHEN the handover completes: the moment every component faster
// than the survivors has died (phosphormix::Result::tailOnsetMs). For the
// reported P46+P33 mix that is ~17 ms into a 2828 ms fade -- the recolor must
// CASCADE at the fast phosphor's death, not drift across the whole trail. 0
// (the default, and every single-preset caller) keeps the old whole-trail
// ramp, so presets that never learned about onsets are timing-unchanged.
void setPanelGlowTail(const unsigned char tint[3], float onsetMs = 0.0f);

// PHOSPHOR GRAIN: the spatial texture of the screen itself. `strengthPercent`
// is a percentage of what a real settled-powder screen has, so 100 is realistic
// and the default, 0 is off (bit-exact off), and 1000 is the 10x the owner
// asked for. `coverage` is a phosphorgrain::Coverage integer saying how that
// grain is spread -- evenly, heavier at the rim with a dimmed corner, in
// low-frequency blotches, or both.
//
// This is the answer to "the colors and persistence look good, but it is
// flat": the palette gets the phosphor's color right and the accumulator gets
// its decay right, and a real tube's screen is still a layer of crystals with
// uneven coverage rather than a uniform fill.
//
// It only ever DARKENS -- coverage variation is a deficit against an ideal
// screen, and a multiplier cannot lift a pixel the page left dark, which is the
// bug class the page-turn flash and the grey-background report both came from.
// Owner ruling 2026-08-18 rules out the other two candidates: no bloom or
// halation (it spreads light across glyph edges and costs legibility) and no
// scanlines (a raster artifact, not a phosphor one).
//
// The model lives in src/PhosphorGrain.h and is host-tested; this layer only
// carries the two numbers. CROSSPOINT_SIM_GRAIN and
// CROSSPOINT_SIM_GRAIN_COVERAGE override the arguments, for a desktop or
// headless run with no Settings app to reach the control.
// `mottleCells` is how many blotches span the long edge and
// `mottleDepthHundredths` how hard they swing the grain, as an integer
// percentage (0, 3, 10, 30) because that is how Settings.app persists it.
// Depth 0 is exact: a Mottled coverage then renders byte-for-byte as Even.
// CROSSPOINT_SIM_GRAIN_MOTTLE_CELLS / _DEPTH override those two.
// PAGE-TURN FLASH: whether the 1-bit pass is allowed to reach the screen on its
// own, ahead of the antialiased compose that follows it 13-271 ms later.
//
// FALSE is the default and the shipped behaviour: a present is held briefly and
// released early by the compose, so only the composed frame lands. TRUE restores
// what the device itself does -- the page arrives twice, and you see the panel's
// own refresh rather than only its result.
//
// CROSSPOINT_SIM_PRESENT_FLASH overrides the argument.
void setPresentFlash(bool wanted);

void setPhosphorGrain(int strengthPercent, int coverage, int mottleCells,
                      int mottleDepthHundredths);

// LETTERPRESS: the LIGHT page's surface treatment (owner doctrine 2026-08-22:
// light mode is paper-and-ink emulation, dark mode is CRT emulation). Percent
// of standard: 0 off (bit-exact), 50 subtle (the iOS light default), 100
// standard, 200 heavy. Ink-squeeze rim, deboss shadow, plate pressure and
// paper tooth, all darken-only, drawn over the PANEL only -- it is a property
// of the page, not the glass. Model: src/Letterpress.h (host-tested); design:
// docs/letterpress-and-scanlines.md. While it is active in light mode the
// grain pass is skipped (the doctrine replaces it); dial it to 0 to A/B the
// old grain. CROSSPOINT_SIM_LETTERPRESS overrides the argument.
void setLetterpress(int strengthPercent);

// PAPER TOOTH: how rough the SHEET the letterpress is printed on is, as a
// percent of the reference stock's (owner order 2026-08-22, with the paper
// tint slider: "be sure to be adding the existing noise treatment to it").
// 100 is the shipped Bright White, so an unseeded build renders the tooth it
// always did; a chamois at full tint asks for 180. The number comes from
// lightink::toothScaleFor(paperIndex, paperStrengthPercent), so dialing a
// stock's tone up brings its texture up with it. It scales the sheet pass's
// amplitude only -- the ink-carried components are a property of the press,
// not the paper. Model: src/Letterpress.h. CROSSPOINT_SIM_PAPER_TOOTH
// overrides the argument.
void setPaperTooth(int percentOfReference);

// THE REST OF THE PAPER INSTRUMENT (owner order 2026-08-22: "make tooth,
// formation, pressure and all other paper variables sliders in the 'color
// button' drawer"). Every one of these was a constant inside the model until
// this order; each is now a live dial, grouped Ink / Paper / Press in the
// light-mode page-color drawer, and each defaults to the value that reproduces
// exactly what this repo already drew.
//
// ONE SOURCE OF TRUTH PER QUANTITY. The Settings.bundle `Letterpress` row stays
// as the MASTER scale (setLetterpress above); the three Press dials here are
// the per-component PARTS, composing multiplicatively with it. Neither is a
// second authority over the other.

// PAPER FORMATION: the sheet's cloudiness -- how hard the low-frequency fibre
// distribution swings the tooth's amplitude, as a percent (0 = a perfectly even
// sheet, which no real stock is; 55 is what this repo shipped; 100 is the
// model's maximum). Mean-preserving by construction, so it costs nothing
// against the paper's contrast budget. CROSSPOINT_SIM_PAPER_FORMATION
// overrides.
void setPaperFormation(int depthPercent);

// PAPER DEFECTS: how marked the sheet is, 0..100 (0 off and bit-exact, 30 the
// iOS default, 100 a thoroughly used book). It is an INCIDENCE dial -- turning
// it up gives an older book, not a dirtier ink. Foxing, red rag flecks, blue
// marks, brown stains, fly specks and wax spots, masked by the page's own ink
// so a mark never sits on a glyph, and bounded by whatever the tooth left of
// the palette's paper budget. Model: src/PaperDefects.h (host-tested); design
// and citations: docs/paper-defects.md. CROSSPOINT_SIM_PAPER_DEFECTS overrides.
void setPaperDefects(int dialPercent);

// SHEET-TO-SHEET DRIFT: how far this leaf's paper tone may sit from the
// stock's, 0..100 (0 off and bit-exact, which is the shipped value on both
// platforms). A book is printed from several reams and ages unevenly, so no
// two leaves measure the same tone; every page here measures identically
// without this. The offset is derived from the SAME page identity the tooth,
// the wires and the defects use, so a leaf is the same leaf across a
// relaunch, and it moves the PAPER only -- a different ream does not change
// the pigment. Bounded to +/-2 code values at the top of the dial, because
// this tone is the whole page's ground; the 7:1 clamps take that bound as the
// darkest sheet the dial can produce and move the density floor to suit.
// Applied at ONE read (livePanelPalette in HalDisplay.cpp), so no consumer of
// the page's tone can be forgotten. Model: src/LightInkPalette.h
// (host-tested); design: docs/surface-roadmap.md section 1c.
// CROSSPOINT_SIM_PAPER_DRIFT overrides the argument.
void setPaperDrift(int dialPercent);

// CHAIN AND LAID LINES: the wire structure of a hand mould, for a stock that
// carries it (lightink::Paper::laid -- Laid Antique today). Percent of
// standard; the iOS picker pushes the paper-strength percent for a laid stock
// and 0 for every wove one, so the wires ride the paper slider the way tooth
// and formation do. 0 off and bit-exact -- the desktop default, so the canary
// is unchanged. Generated at OUTPUT size inside the sheet pass (at ~1.9 px
// the laid pitch is ST-008 territory in the framebuffer), darken-only, seeded
// by the page's identity so a page is the same sheet forever. Model:
// src/LaidStructure.h (host-tested); measured geometry:
// docs/paper-colorimetry-sources.md section 3c. CROSSPOINT_SIM_LAIDLINES
// overrides the argument.
void setLaidLines(int strengthPercent);

// THE PRESS'S THREE PARTS, each a percent of the standard press (100 is the
// shipped composition, 0 removes that component, 200 is the ceiling -- which is
// not taste but the no-new-worst-case bound: 200% on the heaviest OFFERED
// master rung lands exactly on letterpress::kStrengthMax, a state the shipped
// Letterpress ladder could already reach).
//
//   ring     the ink-squeeze rim around every stroke, the letterpress signature
//   deboss   the shadowed top-left walls of the type's bite into the sheet
//   pressure the low-frequency unevenness of impression across the forme
//
// All three are carried by ink or its edges, so none can breach the PAPER's
// contrast floor. CROSSPOINT_SIM_PRESS_RING / _DEBOSS / _PRESSURE override.
void setPressRing(int percentOfStandard);
void setPressDeboss(int percentOfStandard);
void setPressPressure(int percentOfStandard);

// SCANLINES: the DARK page's screen texture, replacing the mottled grain
// (supersedes the 2026-08-18 "no scanlines" ruling -- owner order 2026-08-22).
// Percent of standard: 0 off (bit-exact), 50 subtle (the iOS dark default),
// 100 standard, 150 deep. One scan line per source row, Gaussian beam profile
// box-integrated at output size (the ST-008 lesson), content-aware bloom, and
// the mottle folded into the ladder as depth modulation ON the line
// structure. Darken-only, over the whole app surface like the grain was.
// Model: src/Scanlines.h (host-tested). While it is active in dark mode the
// grain pass is skipped; dial it to 0 to A/B the old grain.
// CROSSPOINT_SIM_SCANLINES overrides the argument.
void setScanlines(int intensityPercent);

// SCANLINE SIZE: the line PITCH, as a percent of the SOURCE-ROW pitch (owner
// order 2026-08-22, from build 126). 100 = one line per page row, which is
// what build 126 shipped, so the default changes nothing. Settings.app offers
// 100 / 150 / 200 / 300 -- MULTIPLES of the lattice the panel already resamples
// on, never absolute pixels, because a free ratio against a per-device
// presentation scale is the rejected fixed-tube design. Measured on the ST-008
// subject (a bilinear-minified Bayer fill): the field adds +0.05 / +0.11 /
// +0.17 / +0.05 levels of low-frequency banding at the four rungs, against the
// 1.55 levels that fill already carries and the 8.14 that was the bug.
// Model: scanlines::pitchFor. CROSSPOINT_SIM_SCANLINE_PITCH overrides.
void setScanlineSize(int percentOfRowPitch);

// SCANLINE BLOOM: how far beam current widens the lit band, as a percent of
// the standard gain (owner order 2026-08-22, "add another ios app settings for
// selecting bloom values with scanlines"). 0 off (bit-exact: the field stops
// being content-aware at all), 50 subtle, 100 standard -- what build 126
// shipped and the default -- 200 strong, 400 extreme. It is a fraction of the
// PITCH, so it stays proportionate at every scanline size. It cannot lift a
// pixel: bloom darkens the gap LESS near bright content, never adds light.
// Model: scanlines::bloomGainFor. CROSSPOINT_SIM_SCANLINE_BLOOM overrides.
void setScanlineBloom(int percentOfStandard);

// SHOW-THROUGH: the previous leaf, mirrored and heavily blurred, faintly
// visible through this one (roadmap 1a). LIGHT mode only -- it is the paper
// half of the doctrine -- and it rides on the letterpress sheet pass, so it
// draws only where that pass does. 0 off (bit-exact), 100 the reference
// sheet's own show-through; the CHOSEN STOCK then scales it, which is the
// whole feature (India 3.0x, Kozo 3.7x, a calfskin vellum 0.25x), so the
// percent handed here is already the dial times
// lightink::showThroughScaleFor. Darken-only, and its share of the paper's
// 7:1 budget is taken before the marks are generated.
// Model: src/ShowThrough.h (host-tested). CROSSPOINT_SIM_SHOW_THROUGH
// overrides.
void setShowThrough(int percentOfStandard);

// CORNER DEFOCUS: the beam spot grows and turns elliptical off-axis, so the
// raster softens toward the corners (roadmap D3). DARK mode only, and it
// modulates the SCANLINE field rather than drawing one of its own -- with
// scanlines off it does nothing at all. 0 off (bit-exact), 100 the shipped
// tube. It softens without changing the page's mean brightness (the period
// mean divides out; see scanlines::rowTransmission), so it cannot lift a
// corner and it costs the contrast budget nothing.
// Model: src/CornerDefocus.h (host-tested). CROSSPOINT_SIM_CORNER_DEFOCUS
// overrides.
void setCornerDefocus(int percentOfStandard);

// THE POWER-OFF COLLAPSING DOT (roadmap D8): at sleep, the picture squeezes to
// a bright line, the line closes to a dot, and the dot fades out. DARK mode
// only, off by default, and the one surface dial that is an iOS Settings row
// rather than a frozen value -- turning it on means the glass stays dark for
// the whole sleep instead of holding the sleep screen, and that is a trade
// only the owner may make.
// Model: src/PowerOffCollapse.h (host-tested).
// CROSSPOINT_SIM_POWEROFF_COLLAPSE overrides.
void setPowerOffCollapse(bool enabled);

// Advance the collapse by one frame and present it. Called from the deep-sleep
// loop (HalGPIO::startDeepSleep), which is where it can run WITHOUT delaying
// sleep: the firmware has already handed over, the wake checks run before this
// on every iteration, and a wake mid-collapse simply abandons it.
//
// Returns true while there are more frames to draw. False means "nothing to do"
// -- disabled, not a dark page, already finished, or no frame to collapse -- and
// the caller must stop asking. Main thread only, like every other SDL call in
// this library.
bool stepPowerOffCollapse();

// THE TUBE WARMING UP -- the other half of the same switch (owner ruling
// 2026-08-23: "show crt powering on animation if power off animation is
// enabled"). There is deliberately NO setter and no second Settings row: the
// warm-up arms itself when the collapse actually switches the tube off, and
// reads the same `Sleep > Power-Off Collapse` value through the same atomic.
// It composites inside HalDisplay::presentIfNeeded, so it never delays the
// wake -- the firmware boots and renders underneath it.
// Model: src/PowerOnWarmUp.h (host-tested).
// CROSSPOINT_SIM_POWERON_WARMUP=1 arms it on a plain desktop launch, which is
// the only way to photograph it without a whole sleep/wake cycle; 0 suppresses.
//
// Abandon a warm-up in progress and show the page at once. Called from
// HalGPIO's event pump on a fresh press DOWN -- and only on a DOWN, because the
// release of the tap that woke the device can still be in the queue. A no-op
// when nothing is warming up. Safe from the firmware task.
void cancelPowerOnWarmUp();

// --- THE DIAL TABLE'S APPLIERS ---------------------------------------------
//
// src/SimulatorDials.h is the single definition of what each surface dial is
// called, which env var and settings key reach it, what it clamps to, what an
// unseeded desktop draws and what the iOS app ships. These two functions are
// the only thing that turns a row into a setter call, and they are what let the
// desktop boot seed, the settings-file watcher and CROSSPOINT_SIM_AS_SHIPPED
// all be generated from that one list instead of hand-kept in three.
//
// They live here rather than in the table because the table must stay free of
// this header: a pure data table can be host-tested, a table of pointers into
// HalDisplay.cpp cannot be linked by a test.

// Push ONE dial -- or, for the grain's four-argument group, the whole group.
// `group` must be a group leader (simdials::isGroupLeader); a member row is a
// no-op, because its value reaches the setter through its leader's call.
void applyDialGroup(simdials::Id group, const simdials::Values &v);

// Push every dial, once each, in table order.
void applyDials(const simdials::Values &v);

} // namespace SimulatorOverlay
