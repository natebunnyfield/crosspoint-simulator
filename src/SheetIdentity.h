#pragma once

// WHICH SHEET THE SCREEN IN FRONT OF YOU IS PRINTED ON.
//
// The light page's whole surface stack -- tooth, formation, laid wires, marks,
// show-through and the sheet-to-sheet tone drift -- is generated from one
// number, and that number is the PAGE'S IDENTITY rather than the launch's: a
// book is not re-printed when you close it, so a page you turn back to has to
// be the same leaf, across a relaunch included.
//
// Until 2026-08-24 only the three reader activities published an identity, so
// every screen that is not a book page -- Home, Settings, the font picker,
// Manage Files, Recents, chapter select -- fell back to the LAUNCH seed. That
// fallback was invisible in every way that matters and wrong in three:
//
//   1. Settings was a different sheet on every launch. Nothing about a menu
//      changes between runs, so nothing about its paper should.
//   2. Show-through was DEAD on those screens, and this is the one a reader of
//      the code would never guess. The verso map promotes when the seed
//      CHANGES (see updateVersoMaps in HalDisplay.cpp); a seed that never
//      changes never promotes, so the leaf behind a menu stayed the all-zero
//      map it was allocated with. Measured on the Settings screen: the
//      show-through dial moved 0.000 code values at any strength, against
//      0.223 mean / 4 max on a reader page.
//   3. Walking Home -> Settings -> Home showed one continuous sheet where a
//      book shows a new leaf per page. The owner's ruling of 2026-08-24 is
//      that the system screens get the treatment A BOOK PAGE GETS, and a book
//      page's treatment is per-page.
//
// So a screen publishes an identity too, off its activity NAME -- one call in
// Activity::onEnter(), which is the single place every screen in the firmware
// passes through. Reader activities are skipped there and keep publishing
// their real page identity from their render, so a book page is unaffected and
// there is never a frame where the two publishers disagree about the leaf.
//
// WHY A PURE HEADER. Same argument as PanelPalette.h, PhosphorGrain.h,
// FieldSelection.h and the rest of the field family: every failure mode here
// is a wrong PICTURE that compiles, renders and logs nothing. A screen seed
// that collided with a page seed would silently print Settings on page 240 of
// the open book, and a seed that came back 0 would read as "nothing published"
// and quietly restore the launch-seeded behaviour this replaces.

#include <cstdint>

#include "PhosphorGrain.h"  // hash3 -- the mixer every seed in this repo uses

namespace sheetid {

// 0 is the latch's "nothing has been published yet" sentinel, so no seed this
// header produces may be 0. Both functions below fold to this instead; the
// value is arbitrary and only has to be a seed like any other.
inline constexpr uint32_t kNeverZero = 0x53484554u;  // 'SHET'

// The screen lane. Mixed into a screen's key so a name hash can never land on
// the same sheet as some book's page, however the two hashes happen to fall.
inline constexpr uint32_t kScreenLane = 0x53435231u;  // 'SCR1'

// A BOOK PAGE. Exactly the mixing the light fields used before this header
// existed -- moved here rather than rewritten, because changing it would
// re-print every page of every book with a different sheet.
inline uint32_t forPage(uint64_t bookKey, int spineIndex, int pageInSpine) {
  const uint32_t s = phosphorgrain::hash3(
      static_cast<uint32_t>(bookKey & 0xFFFFFFFFu),
      static_cast<uint32_t>(bookKey >> 32) ^ static_cast<uint32_t>(spineIndex),
      static_cast<uint32_t>(pageInSpine));
  return s ? s : kNeverZero;
}

// A SYSTEM SCREEN, from the FNV-1a of its activity name (screenKey below).
// Deterministic, so Settings is the same sheet on every launch and on every
// machine, and distinct per screen, so Home and Settings are two leaves and
// the one you came from shows through the one you are on.
inline uint32_t forScreen(uint32_t screenKey) {
  const uint32_t s = phosphorgrain::hash3(screenKey, kScreenLane, 0u);
  return s ? s : kNeverZero;
}

// FNV-1a over an activity name. Here as well as at the firmware call site
// because the firmware cannot include this header on device -- the simulator
// is not linked there -- so the two definitions have to be provably the same
// function, and tests/sheet_identity_test.cpp is what proves it by reading the
// firmware's copy as text.
inline constexpr uint32_t screenKey(const char *name) {
  uint32_t h = 2166136261u;
  if (!name) return h;
  for (const char *p = name; *p; ++p) {
    h ^= static_cast<uint32_t>(static_cast<unsigned char>(*p));
    h *= 16777619u;
  }
  return h;
}

}  // namespace sheetid
