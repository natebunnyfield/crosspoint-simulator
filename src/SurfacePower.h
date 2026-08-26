#pragma once

// THE POWER PATH: the tube switching off, and the tube coming back.
//
// Extracted from src/HalDisplay.cpp on 2026-08-25 -- Tier 2 of
// docs/refactor-plan-2026-08-24.md, whose organizing principle is contention
// rather than tidiness. HalDisplay.cpp is the file every visual change must
// load, and on 2026-08-24 three separate tasks serialised behind it.
//
// The MODELS were already pure headers (src/PowerOffCollapse.h,
// src/PowerOnWarmUp.h). What moved here is the COMPOSITING they imply: the
// collapse's own frames, the warm-up's pass inside a present, the kept sleep
// source and the arming that crosses a reboot.
//
// --- WHY THIS HEADER HAS TWO HALVES ----------------------------------------
//
// Those draws read a dozen pieces of HalDisplay.cpp's file-static state -- the
// renderer, the panel texture, the presented page's rect, the two glass fields,
// the polarity latch. None of it is the power path's own, and none of it can be
// passed in: stepPowerOffCollapse() is called from HalGPIO's deep-sleep loop,
// not from HalDisplay, so there is no call site to hand it a context. The
// boundary therefore runs both ways -- the accessors below out of
// HalDisplay.cpp, the four entry points at the foot back into it.
//
// THE ACCESSORS RETURN REFERENCES, AND THAT IS THE POINT. SurfacePower.cpp
// binds file-scope references to them under the ORIGINAL NAMES, so every moved
// function body is byte-identical to the one that left HalDisplay.cpp. A
// compositing refactor that changes a pixel has a bug in it, and a body that
// was retyped rather than moved is where such a bug hides. Read the diff of
// this extraction as a move, and it is checkable as one.
//
// Binding a reference does not read the referent, and every one of these is a
// namespace-scope static in HalDisplay.cpp, so static-initialisation order
// cannot bite: the address exists before any dynamic initialisation runs.

#include <SDL3/SDL.h>

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <mutex>

#include <GfxRenderer.h>

#include "PanelPalette.h"
#include "SimulatorOverlay.h"

namespace simpower {

// --- WHAT THE POWER PATH READS OUT OF HalDisplay.cpp ------------------------
//
// One accessor per name the moved code already used. The list is deliberately
// flat rather than a context struct: it IS the measure of how entangled this
// unit was, and the next unit's list should be read against it.

SDL_Renderer *&rendererRef();
SDL_Texture *&panelTextureRef();
// The two GLASS fields. At most one ever exists -- each present destroys the
// one it did not select -- which is why the collapse needs no dial read to
// pick between them.
SDL_Texture *&scanFieldRef();
SDL_Texture *&grainFieldRef();
// The PRESENTED page's rect and orientation, in output pixels. Written by
// presentIfNeeded's layout pass; the power path only reads them.
int &panelXRef();
int &panelYRef();
int &panelWRef();
int &panelHRef();
int &panelOrientationRef();
// Guards pixelBuf. keepSleepSourceFrame() is called with it ALREADY HELD;
// restoreSleepSourceFrame() takes it itself.
std::mutex &pixelBufLockRef();
// The polarity of the frame the sleep source kept -- not "is the page dark
// now", which at sleep time answers about the sleep screen. See its comment in
// HalDisplay.cpp.
std::atomic<bool> &lastReadingDarkGroundRef();
std::atomic<bool> &pendingPresentRef();
std::atomic<uint32_t> &overlayClearColorRef();
SimulatorOverlay::DrawFn &overlayDrawRef();
std::atomic<bool> &powerOffCollapseRef();
const SDL_RendererLogicalPresentation &logicalPresentationRef();

bool powerLogWanted();
bool hasDueScreenshot();
void captureDueScreenshots();
panelpalette::Palette livePanelPalette(bool dark);
bool isPortraitOrientation(GfxRenderer::Orientation orientation);
void getLogicalPresentationSize(GfxRenderer::Orientation orientation, int *width,
                                int *height);

// --- WHAT HalDisplay.cpp CALLS INTO THE POWER PATH --------------------------

// Consume CROSSPOINT_SIM_TUBE_OFF and decide whether this boot owes a warm-up.
// Called from HalDisplay::begin() ABOVE its idempotent early return, because
// iOS wakes by re-entering setup() with the window already built and everything
// past that return is skipped on exactly the boot this feature exists for.
void armPowerOnWarmUp();

// One warm-up pass inside a present. A no-op unless the tube was switched off.
// Composited AFTER the grain and the scanlines -- see the call site.
void compositeWarmUp(GfxRenderer::Orientation orientation, bool scanlinesActive);

// Keep (or drop) the page the collapse will squeeze. Called from inside
// presentIfNeeded's locked block, which is why the buffer and the seq are
// passed rather than reached for.
void keepSleepSourceFrame(const uint32_t *pixelBuf, size_t live,
                          uint64_t pixelBufSeq, bool sleepSettled);

}  // namespace simpower
