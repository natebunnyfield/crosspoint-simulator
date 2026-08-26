#pragma once

// THE DARK PAGE'S SURFACE: the glass of a tube, and the coating settled on it.
//
// Extracted from src/HalDisplay.cpp on 2026-08-25 -- Tier 2 unit 3 of
// docs/refactor-plan-2026-08-24.md, after SurfacePower.cpp (unit 1) and
// SurfaceSheet.cpp (unit 2), and built exactly the way unit 2 was, for the same
// reason: HalDisplay.cpp is the file every visual change must load, and on
// 2026-08-24 three separate tasks serialised behind it.
//
// The MODELS were already pure headers (src/PhosphorGrain.h, src/Scanlines.h,
// src/CornerDefocus.h). What moved here is the COMPOSITING they imply: two MOD
// fields at OUTPUT size, their cache keys, the beam-current readback the raster
// is built from, and the defocus map that modulates it.
//
// UNIT 2's PREDICTION FOR THIS UNIT WAS RIGHT, and it was checked rather than
// inherited: `ensureGrainTexture(w, h)` and `ensureScanlinesTexture(w, h,
// pitchPx)` were already parameterised with exactly the presentIfNeeded locals
// they need, so no parameter object was invented here either and every body
// below is a verbatim slice of the one that left HalDisplay.cpp.
//
// THE ACCESSORS RETURN REFERENCES, AND THAT IS THE POINT. SurfaceTube.cpp binds
// file-scope references to them under the ORIGINAL NAMES, so no moved body
// needed an edit. A compositing refactor that changes a pixel has a bug in it,
// and a body that was retyped rather than moved is where such a bug hides.
//
// Binding a reference does not read the referent, and every one of these is a
// namespace-scope static in HalDisplay.cpp, so static-initialisation order
// cannot bite: the address exists before any dynamic initialisation runs.

#include <SDL3/SDL.h>

#include <atomic>
#include <cstdint>

#include "PanelPalette.h"
#include "SurfaceTiming.h"

namespace simtube {

// --- WHAT THE TUBE READS OUT OF HalDisplay.cpp ------------------------------

SDL_Renderer *&rendererRef();

// The framebuffer's content seq. The raster is cached against it, so the field
// is rebuilt on a page turn and never on a still frame -- a raster that crawled
// per frame would be beam-current noise, a different phenomenon.
uint64_t &pixelBufSeqRef();

// This present's timing stations. The struct lives in SurfaceTiming.h so more
// than one translation unit can write it; the single instance and the [timing]
// line are still HalDisplay.cpp's.
simtiming::PresentTiming &timingFrameRef();
bool timingLogWanted();

// THE SCREEN'S SEED, and the palette this page is actually drawn in. Both stay
// in HalDisplay.cpp and neither is the tube's alone: pageSheetSeed() (the LIGHT
// page's per-leaf identity) is built on grainSeed(), and the drift is folded in
// at livePanelPalette(), the one palette read every consumer of the page's
// colour goes through. Moving either here would point the dependency the wrong
// way -- unit 2 left them behind for the mirror-image reason.
uint32_t grainSeed();
panelpalette::Palette livePanelPalette(bool dark);
float srgbLumOf(const unsigned char c[3]);

// THE FOUR GRAIN DIALS. They are SimulatorOverlay-scoped statics in
// HalDisplay.cpp with internal linkage, so the tube cannot name them directly
// and cannot be given a second definition of them either. Same treatment
// SurfacePower.cpp and SurfaceSheet.cpp give the ones they need: an accessor
// out, a reference bound back under the original name.
std::atomic<int> &grainStrengthRef();
std::atomic<int> &grainCoverageRef();
std::atomic<int> &grainMottleCellsRef();
std::atomic<int> &grainMottleDepthPctRef();

// ...and the three the RASTER reads. cornerDefocusStrength is one of them even
// though the dial is frozen off on iOS: what it selects is which of two
// transmission tables the raster is built from, and the OFF branch is the
// original code untouched, so the field it modulates has to be here with it.
std::atomic<int> &scanlinesIntensityRef();
std::atomic<int> &scanlineBloomRef();
std::atomic<int> &cornerDefocusStrengthRef();

// --- WHAT HalDisplay.cpp CALLS INTO THE TUBE --------------------------------

// The phosphor coating: a MOD field at OUTPUT size, drawn 1:1 over the whole
// app surface. Returns false when the dial is off or the field could not be
// built, in which case nothing should be drawn.
bool ensureGrainField(int w, int h);
SDL_Texture *grainField();
void destroyGrainField();

// The raster: a MOD field at OUTPUT size, drawn 1:1 over the whole app
// surface. `pitchPx` is the presentation scale with the render scale divided
// out and the owner's size dial applied -- computed by presentIfNeeded, which
// derives the sheet's lattice from the same number.
bool ensureScanlinesField(int w, int h, float pitchPx);
SDL_Texture *scanField();
void destroyScanField();

// The pointers themselves, for the power path. simpower::scanFieldRef() and
// grainFieldRef() forward to these rather than owning the textures: the
// collapse and the warm-up read the live glass field to decide what the dying
// tube is showing, and unit 1 should not have to be edited by unit 3 to learn
// where that field moved to.
SDL_Texture *&grainFieldRef();
SDL_Texture *&scanFieldRef();

}  // namespace simtube
