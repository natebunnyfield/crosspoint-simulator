#pragma once

// ONE PRESENT'S TIMING STATIONS.
//
// Split out of src/HalDisplay.cpp on 2026-08-25 with Tier 2 unit 2 of
// docs/refactor-plan-2026-08-24.md, and for one mechanical reason: the surface
// passes are moving into their own translation units and each of them writes
// its own station, so the type has to be visible from more than one file. The
// instrument itself is unchanged -- what it measures, when it is latched and
// why is documented at timingLogWanted() in HalDisplay.cpp, which is still
// where the env read, the one `timingFrame` and the [timing] line live.

#include <cstdint>

namespace simtiming {

// One pass's verdict for this present. A cache HIT is as interesting as a
// build: "the sheet rebuilt twice this page" and "the sheet was served" are
// the two answers the field-keying work exists to distinguish, and a bare
// duration cannot tell them apart.
struct PassTiming {
  bool built = false;   // the field was regenerated this present
  bool served = false;  // a cached field was drawn
  double ms = 0.0;      // wall time of the regeneration, 0 when served
};
struct PresentTiming {
  PassTiming letterpress, sheet, grain, scanlines;
  // THE TWO PER-PRESENT COSTS THE LINE USED TO HIDE, and they are the two that
  // dominate a phosphor trail -- where every field above is cache-served and
  // the readback never runs. `upload` is the panel framebuffer's trip to the
  // GPU (skipped now when the picture has not moved, so `built` is the
  // interesting bit); `accum` is the glow accumulator's own render-target pass,
  // which SDL_SetRenderTarget flushes, so its cost lands here rather than in
  // the flip. Adding them was the 2026-08-26 trail-cost work: 4 of the 5 ms of
  // non-draw time in a trail present had no station and was being attributed to
  // "the rest of the present".
  PassTiming upload, accum;
  bool readback = false;  // SDL_RenderReadPixels of the whole output
  double readbackMs = 0.0;
  uint64_t startNs = 0;
  double flipMs = 0.0;  // SDL_RenderPresent itself
};

}  // namespace simtiming
