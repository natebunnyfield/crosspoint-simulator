#pragma once

// WHICH SURFACE FIELD COMPOSITES, AND THE SHARES OF THE BUDGET THEY SPEND.
//
// Two things live here, and they are here for one reason: every surface pass in
// this simulator computed its darkening budget on the assumption that IT IS THE
// ONLY PASS. Scanlines take a share of the grain's budget; the wires and the
// show-through take halves of what the tooth left the paper; letterpress owns
// the light page's ink. Each of those bounds is honest on its own and none of
// them composes -- two fields drawn over one page multiply, and the product can
// sit under the 7:1 contrast floor that every one of those tests proves
// individually.
//
// So the mutual exclusion is not a tidiness rule. It is the thing that makes
// the individual budgets true, and until 2026-08-23 it was five lines in the
// middle of a 4,800-line present function with no test of any kind -- while the
// budgets it protects have seven test files between them.
//
// WHY A PURE HEADER. Same argument as PanelPalette.h, PhosphorGrain.h and the
// rest of the field family: every failure mode here is a wrong PICTURE that
// compiles, renders, logs nothing and looks plausible. A grain field that
// layers under a scanline field does not crash; it produces a page a few
// percent too dark, which is exactly the kind of change nobody catches by
// looking and no other test in this repo can see.

#include "Letterpress.h"
#include "PhosphorGrain.h"
#include "Scanlines.h"

namespace fieldselect {

// The dials as HalDisplay holds them: three atomics and the live polarity.
// Percent/strength scales, each with its own off sentinel, exactly as the
// three model headers define them -- taken from those headers rather than
// re-spelled as 0, so a model that ever moves its sentinel moves this too.
struct Dials {
  bool dark = false;
  int scanlinesIntensity = scanlines::kIntensityOff;
  int letterpressStrength = letterpress::kStrengthOff;
  int grainStrength = phosphorgrain::kStrengthOff;
};

struct Active {
  bool scanlines = false;
  bool letterpress = false;
  bool grain = false;
};

// THE 2026-08-22 DOCTRINE, as a function.
//
//   dark page  -> SCANLINES (the CRT half)
//   light page -> LETTERPRESS (the paper half)
//   neither    -> GRAIN, the pre-doctrine field, unchanged
//
// The doctrine field REPLACES the grain, it does not layer over it. That is
// what keeps the desktop canary byte-identical: the desktop seeds both doctrine
// dials off, so `grain` here is exactly the old unconditional grain condition.
//
// The polarity gate is per field and not shared: a letterpress strength left
// set from a light page must not draw on a dark one, and vice versa. Both are
// gated here rather than at their draw sites so there is ONE answer to "is
// letterpress live" -- it used to be computed twice, sixty lines apart, off the
// same two atomics, and two reads of a mutable value are two chances to
// disagree.
constexpr Active select(const Dials &d) {
  Active a;
  a.scanlines = d.dark && d.scanlinesIntensity > scanlines::kIntensityOff;
  a.letterpress = !d.dark && d.letterpressStrength > letterpress::kStrengthOff;
  // The exclusion. Note it is NOT "not dark-and-scanlines": a letterpress
  // strength with the scanlines also somehow live must still suppress the
  // grain, because the breach is two fields multiplying, whatever the two are.
  a.grain = d.grainStrength != phosphorgrain::kStrengthOff && !a.scanlines &&
            !a.letterpress;
  return a;
}

// At most one field is ever live. This is the property the budgets depend on,
// stated as a predicate so a test can sweep it rather than read it.
constexpr bool atMostOneField(const Active &a) {
  return (a.scanlines ? 1 : 0) + (a.letterpress ? 1 : 0) + (a.grain ? 1 : 0) <=
         1;
}

// --------------------------------------------------------------- the shares --
//
// These were bare literals at the four sites that spend them and at four more
// in tests/, so the app and the tests could disagree with no symptom: change
// the app's share and every test goes on proving the old one, green.

// THE RASTER'S SHARE of the grain's darkening budget. The scanline field spends
// it, and corner defocus modulates that same field rather than drawing its own,
// so both derive from this one number. Below 1.0 because the raster is a
// STRUCTURED field where the grain is a noise one: the same mean darkening
// reads as more contrast loss when it is organized into lines.
constexpr float kRasterBudgetShare = 0.8f;

// THE SHEET'S BUDGET, SPLIT. What the tooth leaves the paper is shared in
// order: the wires take this fraction of it, then show-through takes the same
// fraction of what remains, and the marks take the rest. One constant, applied
// twice, because the split is "halve what is left" and not two independent
// choices -- writing 0.5 twice invites moving one of them.
constexpr float kSheetShareStep = 0.5f;

}  // namespace fieldselect
