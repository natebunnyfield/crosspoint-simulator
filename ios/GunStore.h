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

#include "GunMixCsv.h"
#include "PhosphorMix.h"

namespace gunstore {

// The keys. Named ONCE, here, so a rename cannot half-land.
inline NSString *const kAssign = @"phosphorGunAssign";  // "11,40,24,21"
inline NSString *const kBlend = @"phosphorMixBlend";    // "11:50,40:50,..."
inline NSString *const kMode = @"phosphorMixMode";

// Current assignments + weights. Assignments must be EXACTLY four valid
// mixable presets or the whole set falls back to the defaults -- half a stored
// assignment is a foreign recipe. Weights come from the blend CSV
// POSITIONALLY: pair g belongs to gun g, with each pair's preset cross-checked
// against the assignment. Never matched by preset -- two guns MAY share a
// phosphor (owner bug report 2026-08-22: "duplicated guns"), and a by-preset
// lookup collapsed both onto whichever shared pair parsed last, destroying one
// gun's weight on every load.
inline void load(int presets[gunmix::kGunCount], int w[gunmix::kGunCount]) {
  for (int g = 0; g < gunmix::kGunCount; g++) {
    presets[g] = phosphormix::kDefaultGunPreset[g];
    w[g] = phosphormix::kDefaultGunWeight[g];
  }
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  NSString *assign = [d stringForKey:kAssign];
  if (assign.length) gunmix::parseAssign(assign.UTF8String, presets);
  NSString *csv = [d stringForKey:kBlend];
  if (csv.length) gunmix::parseWeights(csv.UTF8String, presets, w);
}

// Both keys together, always: the weight CSV cross-checks itself against the
// assignment on load, so writing one without the other makes the next load
// throw the pair away and silently fall back to the defaults.
inline void save(const int presets[gunmix::kGunCount],
                 const int w[gunmix::kGunCount]) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setObject:@(gunmix::encodeAssign(presets).c_str()) forKey:kAssign];
  [d setObject:@(gunmix::encodeBlend(presets, w).c_str()) forKey:kBlend];
  [d setInteger:phosphormix::Blend forKey:kMode];
}

}  // namespace gunstore
