#pragma once

// THE LIGHT PAGE'S SURFACE: the letterpress plate, and the sheet it is
// pressed into.
//
// Extracted from src/HalDisplay.cpp on 2026-08-25 -- Tier 2 unit 2 of
// docs/refactor-plan-2026-08-24.md, following SurfacePower.cpp (unit 1) and
// built the same way, for the same reason: HalDisplay.cpp is the file every
// visual change must load, and on 2026-08-24 three separate tasks serialised
// behind it.
//
// The MODELS were already pure headers (src/Letterpress.h, src/LaidStructure.h,
// src/ShowThrough.h, src/PaperDefects.h, src/LightInkPalette.h). What moved
// here is the COMPOSITING they imply: two MOD fields, their cache keys, the
// inkness plane the second masks against, and the two blurred maps that make
// the previous leaf show through this one.
//
// --- WHAT THE PLAN EXPECTED, AND WHAT WAS ACTUALLY THERE --------------------
//
// Unit 1's write-up warned that this unit would need "a real parameter object"
// because its passes "sit INSIDE presentIfNeeded, mid-function, reading locals
// it computes". Measured rather than assumed, that turned out to be wrong for
// the sheet: `ensureLetterpressTexture()` takes no arguments at all, and
// `ensureSheetToothTexture(w, h, outPxPerSourcePx)` already took exactly the
// two locals it needs, hoisted there in 2026-08-22 when the laid wires and the
// scanlines both had to derive lattices from one scale. So no parameter object
// was invented: what crosses this boundary is file-scope STATE, exactly as in
// unit 1, and the accessor list below is the honest measure of it.
//
// THE ACCESSORS RETURN REFERENCES, AND THAT IS THE POINT. SurfaceSheet.cpp
// binds file-scope references to them under the ORIGINAL NAMES, so every moved
// body is byte-identical to the one that left HalDisplay.cpp. A compositing
// refactor that changes a pixel has a bug in it, and a body that was retyped
// rather than moved is where such a bug hides.
//
// Binding a reference does not read the referent, and every one of these is a
// namespace-scope static in HalDisplay.cpp, so static-initialisation order
// cannot bite: the address exists before any dynamic initialisation runs.

#include <SDL3/SDL.h>

#include <atomic>
#include <cstdint>
#include <mutex>
#include <vector>

#include <GfxRenderer.h>

#include "PanelPalette.h"
#include "SurfaceTiming.h"

namespace simsheet {

// --- WHAT THE SHEET READS OUT OF HalDisplay.cpp -----------------------------

SDL_Renderer *&rendererRef();

// The PRESENTED page's rect and orientation, in output pixels. Written by
// presentIfNeeded's layout pass and read by the power path too, which is why
// they stayed in HalDisplay.cpp rather than travelling with outputToPanel --
// they describe the presentation, not the paper.
int &panelXRef();
int &panelYRef();
int &panelWRef();
int &panelHRef();
int &panelOrientationRef();

// The framebuffer as ARGB, its seq, and the lock over both. The letterpress
// pass reads the frame and the seq TOGETHER under this lock, so its cache key
// can never describe pixels from a different frame than the ones it read.
uint32_t *pixelBufData();
uint64_t &pixelBufSeqRef();
std::mutex &pixelBufLockRef();

// This present's timing stations. The struct now lives in SurfaceTiming.h so
// that more than one translation unit can write it; the single instance and
// the [timing] line are still HalDisplay.cpp's.
simtiming::PresentTiming &timingFrameRef();
bool timingLogWanted();

// The page's own seed, and the palette with this leaf's DRIFT already folded
// in. Both stay in HalDisplay.cpp because they are not the sheet's alone: the
// drift is applied at the one palette read every consumer of the page's colour
// goes through, the dark passes included, so moving it here would make the
// grain and the scanlines depend on the light unit.
uint32_t pageSheetSeed();
panelpalette::Palette livePanelPalette(bool dark);
float srgbLumOf(const unsigned char c[3]);

// THE FIVE DIALS THIS PASS READS. They are SimulatorOverlay-scoped statics in
// HalDisplay.cpp with internal linkage, so the sheet cannot name them directly
// and cannot be given a second definition of them either. Same treatment
// SurfacePower.cpp gives the three it needs: an accessor out, a reference
// bound back under the original name.
std::atomic<int> &letterpressStrengthRef();
std::atomic<int> &paperToothPctRef();
std::atomic<int> &paperFormationPctRef();
std::atomic<int> &paperDefectsPctRef();
std::atomic<int> &laidLinesStrengthRef();
std::atomic<int> &showThroughStrengthRef();
// ...and the press's three PART percents, which are cache keys for the plate.
std::atomic<int> &pressRingPctRef();
std::atomic<int> &pressDebossPctRef();
std::atomic<int> &pressPressurePctRef();

// --- WHAT HalDisplay.cpp CALLS INTO THE SHEET -------------------------------

// The letterpress plate: a MOD field at FRAMEBUFFER size, drawn through the
// panel's own rotation and dst rect. Returns false when the dial is off or the
// field could not be built, in which case nothing should be drawn.
bool ensureLetterpressField();
SDL_Texture *letterpressField();
void destroyLetterpressField();

// The sheet: a MOD field at OUTPUT size, drawn 1:1 over the whole app surface.
// `outPxPerSourcePx` is the presentation scale with the render scale divided
// out -- the same number the scanlines' base pitch comes from.
bool ensureSheetField(int w, int h, float outPxPerSourcePx);
SDL_Texture *sheetField();
void destroySheetField();

}  // namespace simsheet
