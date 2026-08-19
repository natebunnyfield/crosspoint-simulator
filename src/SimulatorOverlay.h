#pragma once

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
// CROSSPOINT_SIM_PANEL_GLOW_TAIL overrides the argument, "RRGGBB".
void setPanelGlowTail(const unsigned char tint[3]);

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

} // namespace SimulatorOverlay
