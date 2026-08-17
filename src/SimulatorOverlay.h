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

// PHOSPHOR GLOW: how long the previous frame lingers, in milliseconds. 0 is off,
// and off is the default and the entire desktop behaviour.
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

} // namespace SimulatorOverlay
