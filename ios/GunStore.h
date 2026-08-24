#pragma once

// THE FOUR-GUN RECIPE, AS IT SITS IN NSUserDefaults.
//
// Extracted 2026-08-23, when a SECOND caller appeared: selecting a named preset
// now seeds the guns to match it (owner: "selecting a preset should set the
// guns' values too"), so the mixer is no longer the only thing that reads and
// writes phosphorGunAssign / phosphorMixBlend. Two hand-written copies of that
// load -- one of them in a UI file's anonymous namespace -- is the shape that
// produced the owner's P1 earlier the same day, where one store had two writers
// and no owner (src/PanelSource.h).
//
// SAME SPLIT AS ios/PanelPrefs.h, and for the same reason: this file only
// FETCHES and STORES; src/GunMixCsv.h owns the encoding and src/PhosphorMix.h
// owns every decision about what the guns should hold. Nothing here chooses
// anything.
//
// Header-only and inline because both includers are Objective-C++ and neither
// build wants another translation unit for eight lines.

#import <Foundation/Foundation.h>

#include <string>

#include "FrozenPage.h"
#include "GunMixCsv.h"
#include "PhosphorMix.h"

namespace gunstore {

// The keys. Named ONCE, here, so a rename cannot half-land.
inline NSString *const kAssign = @"phosphorGunAssign";  // "11,40,24,21"
inline NSString *const kBlend = @"phosphorMixBlend";    // "11:50,40:50,..."
inline NSString *const kMode = @"phosphorMixMode";

// Current assignments + weights.
//
// FROZEN 2026-08-24 by owner ruling ("take out paper and crt settings for now
// ... attached image for crt"): the four guns are src/FrozenPage.h's, and this
// consults NSUserDefaults for NEITHER key. Same discipline as
// CrossPointPrefs.mm's frozen getters -- with the page-color chip gone from the
// pad there is no control that reaches the mixer, so an install holding an
// older recipe would render it forever with no way back.
//
// The parse path below is what a stored recipe used to go through, and it is
// kept as the record of what a load has to get right if the store is ever
// consulted again: assignments must be EXACTLY four valid mixable presets or
// the whole set falls back to the defaults -- half a stored assignment is a
// foreign recipe -- and weights come from the blend CSV POSITIONALLY, pair g to
// gun g, with each pair's preset cross-checked against the assignment. Never
// matched by preset: two guns MAY share a phosphor (owner bug report
// 2026-08-22, "duplicated guns"), and a by-preset lookup collapsed both onto
// whichever shared pair parsed last, destroying one gun's weight on every load.
inline void load(int presets[gunmix::kGunCount], int w[gunmix::kGunCount]) {
  for (int g = 0; g < gunmix::kGunCount; g++) {
    presets[g] = frozenpage::kGunPreset[g];
    w[g] = frozenpage::kGunWeight[g];
  }
}

// Both keys together, always: the weight CSV cross-checks itself against the
// assignment on load, so writing one without the other makes the next load
// throw the pair away and silently fall back to the defaults.
//
// STILL WRITES, and load() no longer reads it back. That is not an oversight:
// its two callers (the mixer's applyGuns, and the preset list's gun seed) are
// unreachable from the pad since 2026-08-24, and leaving them whole -- writing
// a store a frozen load ignores -- is what makes unfreezing this one function
// body rather than an archaeology exercise. Nothing renders from it meanwhile.
inline void save(const int presets[gunmix::kGunCount],
                 const int w[gunmix::kGunCount]) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setObject:@(gunmix::encodeAssign(presets).c_str()) forKey:kAssign];
  [d setObject:@(gunmix::encodeBlend(presets, w).c_str()) forKey:kBlend];
  [d setInteger:phosphormix::Blend forKey:kMode];
}

}  // namespace gunstore
