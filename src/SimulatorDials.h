#pragma once

// THE DIAL TABLE -- one row per host-side surface dial, and the only place any
// of their numbers is written down.
//
// WHY IT EXISTS (owner ruling 2026-08-23, "yes -- it is the root cause").
// Adding one surface effect used to touch nine plumbing sites, and three of
// them were parallel lists of the SAME values kept in sync by hand: the desktop
// boot seed in HalDisplay.cpp, the `dial()` block in SimulatorSettingsWatch.cpp,
// and the CROSSPOINT_SIM_AS_SHIPPED block. They drifted twice in one day --
// the beam sat at 67 ms while the app had moved to 55, and three of the grain's
// four arguments were wrong (100/8/30 against the app's 160/5/90). Both were
// found by reading the code, not by any test, because nothing anywhere compared
// the three lists. Now there is one list and they are generated from it.
//
// PURE, and deliberately free of SimulatorOverlay: this header is DATA. It
// names the setters through an enum rather than through function pointers,
// because a table of function pointers is a relocation against HalDisplay.cpp
// and the host test could not then link. The switch that turns an Id into a
// setter call lives in HalDisplay.cpp, next to the atomics it writes.
//
// WHAT A ROW IS NOT: the effect itself. Adding a dial still means a pure model
// header, an atomic, a setter and a use in the render path -- that is the
// feature, and it is irreducible. What a row removes is the three copies of its
// VALUE and the plumbing that carried them.
//
// THE VALUES ARE CHECKED AGAINST iOS, not trusted. tests/dial_table_test.cpp
// reads the shipped ios/ sources and fails when a shippedValue here disagrees
// with the frozen constant the app actually pushes. That test is the whole
// point of the table; see its header comment for what it scrapes and why the
// two records are kept separate rather than collapsed into one.

#include <climits>
#include <cstring>

#include "CornerDefocus.h"
#include "LaidStructure.h"
#include "Letterpress.h"
#include "LightInkPalette.h"
#include "PageFade.h"
#include "PaperDefects.h"
#include "PhosphorGrain.h"
#include "Scanlines.h"
#include "ShowThrough.h"

namespace simdials {

// The order here is the order the seed applies them in, which is the order the
// hand-written seed used: the page's own timing first, then the coating, then
// the light page's sheet, then the dark page's tube. Reordering is safe --
// nothing persists an Id -- but keep it meaningful, because a log reads in it.
enum Id {
  PageFadeSeconds,
  PageFadeDepthPercent,
  BeamPaintMs,
  PresentFlash,
  GrainPercent,
  GrainCoverage,
  GrainMottleCells,
  GrainMottleDepth,
  LetterpressPercent,
  PaperToothPercent,
  PaperFormationPercent,
  PaperDefectsPercent,
  PaperDriftPercent,
  LaidLinesPercent,
  PressRingPercent,
  PressDebossPercent,
  PressPressurePercent,
  ScanlinesPercent,
  ScanlineSizePercent,
  ScanlineBloomPercent,
  ShowThroughPercent,
  CornerDefocusPercent,
  PowerOffCollapseOn,
};

// NOT an enumerator: the appliers switch over Id with no `default:`, so that a
// row added here without a setter call is a compiler warning rather than a
// dial that silently does nothing. A count enumerator would have to be
// handled in that switch, which is exactly the case a reader skips past.
inline constexpr int kDialCount = PowerOffCollapseOn + 1;

// THE THREE NON-UNIFORMITIES, as flags rather than as special cases scattered
// through three call sites. Every one of them is a real difference in what the
// dial DOES, so none of them may be papered over -- a uniform "clamp, store,
// present" shape would be wrong for all three, and silently so.
enum Flags : unsigned {
  kPlain = 0u,
  // setPhosphorGrain takes FOUR arguments, not one, and they arrive together.
  // The four grain rows therefore share a group: the watcher's absent-key rule
  // is all-or-nothing across them (a file naming any one of the four is
  // deciding all four), and the seed pushes them in a single call.
  kMultiArg = 1u << 0,
  // setPaperDrift also raises pendingReconvert, because it moves the PAGE'S OWN
  // TONES and the cached frame has to be converted again -- a present alone
  // would re-push pixels that were graded for the previous paper.
  kReconverts = 1u << 1,
  // setPowerOffCollapse asks for no present at all: nothing about a live page
  // changes, and the flag is only read once the firmware is already asleep.
  kNoPresent = 1u << 2,
};

// No ceiling in the setter. Used by the two time dials, which clamp at zero and
// then believe whatever they are given.
constexpr int kNoMax = INT_MAX;

struct Dial {
  Id id;
  // For logs and for test failure messages. Human words, not the key.
  const char *name;
  // The setter's own env override. Every dial has one: a desktop or headless
  // run has no Settings app, so without it the dial cannot be exercised at all
  // off-phone -- which has been a real bug twice (the glow and the fade both
  // shipped with a setter no desktop build ever called).
  const char *envVar;
  // settings.json on the desktop AND NSUserDefaults on iOS -- deliberately the
  // same string, so a settings file and a phone cannot disagree about what a
  // key means.
  const char *settingsKey;
  // The clamp the setter applies. Recorded so the test can prove both values
  // below survive it: a shipped value outside its own clamp is a dial whose
  // stated setting is not the one that renders.
  int minValue;
  int maxValue;
  // What an unseeded DESKTOP build renders. Every one of these is the value
  // this repo drew before the dial existed, which is why a plain
  // `pio run -e simulator_x3` is still byte-identical to every capture ever
  // taken from it.
  int desktopDefault;
  // What the iOS app pushes -- its frozen constant, or its registered default
  // for the two that are still rows. This is what CROSSPOINT_SIM_AS_SHIPPED
  // seeds.
  int shippedValue;
  unsigned flags;
  // The row whose setter call carries this one. Equal to `id` for every dial
  // applied on its own; the four grain rows all name GrainPercent.
  Id group;
};

// clang-format off
inline constexpr Dial kDials[kDialCount] = {
  // --- the page's own timing -------------------------------------------------
  // SECONDS in the settings key, MILLISECONDS at the setter. The key is the
  // owner's unit (a fade is chosen in minutes) and the setter's is the render
  // path's; the seed multiplies. The app froze this at Off on 2026-08-23.
  {PageFadeSeconds, "page fade", "CROSSPOINT_SIM_PAGE_FADE_MS",
   "pageFadeSeconds", 0, kNoMax, 0, 0, kPlain, PageFadeSeconds},
  // How much of the legible floor survives the fade. Moot while the fade is
  // Off, and frozen honestly anyway so the two cannot disagree if it revives.
  {PageFadeDepthPercent, "page fade depth", "CROSSPOINT_SIM_PAGE_FADE_DEPTH",
   "pageFadeDepthPercent", 0, pagefade::kDepthFull, pagefade::kDepthFull, 0,
   kPlain, PageFadeDepthPercent},
  // 55 ms, hard-set in the shim rather than offered as a row (owner
  // 2026-08-22, "hard set beam paint to 55ms, remove ios setting"). THE FIRST
  // OF THE TWO DRIFTS THIS TABLE EXISTS FOR: the as-shipped block said 67 for
  // one day after the app moved, so every desktop reproduction of a beam
  // report ran a 21% longer sweep than the phone.
  {BeamPaintMs, "beam paint", "CROSSPOINT_SIM_BEAM_MS", "beamPaintMs",
   0, kNoMax, 0, 55, kPlain, BeamPaintMs},
  {PresentFlash, "page-turn flash", "CROSSPOINT_SIM_PRESENT_FLASH",
   "presentFlash", 0, 1, 0, 0, kPlain, PresentFlash},

  // --- the screen's coating --------------------------------------------------
  // THE SECOND DRIFT, and the larger one: three of these four disagreed with
  // the app. The strength is the DARK figure (160) because as-shipped forces a
  // dark page and the app stores a strength per appearance; the desktop carries
  // one atomic, so the polarity as-shipped selects is the one that applies.
  {GrainPercent, "screen grain", "CROSSPOINT_SIM_GRAIN",
   "phosphorGrainPercent", 0, phosphorgrain::kStrengthMax,
   phosphorgrain::kStrengthRealistic, 160, kMultiArg, GrainPercent},
  {GrainCoverage, "grain coverage", "CROSSPOINT_SIM_GRAIN_COVERAGE",
   "phosphorGrainCoverage", 0, phosphorgrain::kCoverageCount - 1,
   phosphorgrain::Even, phosphorgrain::VignetteMottled, kMultiArg, GrainPercent},
  {GrainMottleCells, "grain blotch size", "CROSSPOINT_SIM_GRAIN_MOTTLE_CELLS",
   "phosphorGrainMottleCells", phosphorgrain::kMottleCellsMin,
   phosphorgrain::kMottleCellsMax, phosphorgrain::kMottleCellsDefault,
   phosphorgrain::kMottleCellsDefault, kMultiArg, GrainPercent},
  {GrainMottleDepth, "grain blotch depth", "CROSSPOINT_SIM_GRAIN_MOTTLE_DEPTH",
   "phosphorGrainMottleDepth", 0, 100,
   static_cast<int>(phosphorgrain::kMottleDepthDefault * 100.0f + 0.5f),
   static_cast<int>(phosphorgrain::kMottleDepthDefault * 100.0f + 0.5f),
   kMultiArg, GrainPercent},

  // --- the light page's sheet (2026-08-22 doctrine) --------------------------
  {LetterpressPercent, "letterpress", "CROSSPOINT_SIM_LETTERPRESS",
   "letterpressPercent", letterpress::kStrengthOff, letterpress::kStrengthMax,
   letterpress::kStrengthOff, 100, kPlain, LetterpressPercent},
  // The four stock-derived rows below carry the PRODUCT of the app's frozen
  // dial and the chosen paper's own factor. The shipped figures here are that
  // product for the app's default stock (Bright White), whose tooth, formation
  // and show-through factors are all exactly 1.00 and which carries no wires.
  // The test proves those factors rather than trusting this sentence.
  {PaperToothPercent, "paper tooth", "CROSSPOINT_SIM_PAPER_TOOTH",
   "paperToothPercent", 0, 400, 100, 300, kPlain, PaperToothPercent},
  {PaperFormationPercent, "paper formation", "CROSSPOINT_SIM_PAPER_FORMATION",
   "paperFormationPercent", 0,
   static_cast<int>(letterpress::kFormationDepthMax * 100.0f + 0.5f),
   static_cast<int>(letterpress::kFormationDepthDefault * 100.0f + 0.5f), 80,
   kPlain, PaperFormationPercent},
  {PaperDefectsPercent, "paper defects", "CROSSPOINT_SIM_PAPER_DEFECTS",
   "paperDefectsPercent", paperdefects::kDialOff, paperdefects::kDialMax,
   paperdefects::kDialOff, 0, kPlain, PaperDefectsPercent},
  // FROZEN AT THE TOP of its range in the app, deliberately not at the model's
  // default -- kPaperDriftDefault still means "the model ships this off".
  {PaperDriftPercent, "sheet drift", "CROSSPOINT_SIM_PAPER_DRIFT",
   "paperDriftPercent", 0, lightink::kPaperDriftMax,
   lightink::kPaperDriftDefault, lightink::kPaperDriftMax, kReconverts,
   PaperDriftPercent},
  {LaidLinesPercent, "laid wires", "CROSSPOINT_SIM_LAIDLINES",
   "laidLinesPercent", laidstructure::kStrengthOff, laidstructure::kStrengthMax,
   laidstructure::kStrengthOff, 0, kPlain, LaidLinesPercent},
  {PressRingPercent, "press ring", "CROSSPOINT_SIM_PRESS_RING",
   "pressRingPercent", 0,
   static_cast<int>(letterpress::kPartScaleMax * 100.0f + 0.5f), 100, 100,
   kPlain, PressRingPercent},
  {PressDebossPercent, "press deboss", "CROSSPOINT_SIM_PRESS_DEBOSS",
   "pressDebossPercent", 0,
   static_cast<int>(letterpress::kPartScaleMax * 100.0f + 0.5f), 100, 100,
   kPlain, PressDebossPercent},
  {PressPressurePercent, "press pressure", "CROSSPOINT_SIM_PRESS_PRESSURE",
   "pressPressurePercent", 0,
   static_cast<int>(letterpress::kPartScaleMax * 100.0f + 0.5f), 100, 100,
   kPlain, PressPressurePercent},

  // --- the dark page's tube (2026-08-22 doctrine, 2026-08-23 roadmap) --------
  {ScanlinesPercent, "scanlines", "CROSSPOINT_SIM_SCANLINES",
   "scanlinesPercent", scanlines::kIntensityOff, scanlines::kIntensityMax,
   scanlines::kIntensityOff, 50, kPlain, ScanlinesPercent},
  {ScanlineSizePercent, "scanline pitch", "CROSSPOINT_SIM_SCANLINE_PITCH",
   "scanlineSizePercent", scanlines::kSizeMin, scanlines::kSizeMax,
   scanlines::kSizeFine, scanlines::kSizeFine, kPlain, ScanlineSizePercent},
  {ScanlineBloomPercent, "scanline bloom", "CROSSPOINT_SIM_SCANLINE_BLOOM",
   "scanlineBloomPercent", 0, scanlines::kBloomMax, scanlines::kBloomStandard,
   scanlines::kBloomExtreme, kPlain, ScanlineBloomPercent},
  {ShowThroughPercent, "show-through", "CROSSPOINT_SIM_SHOW_THROUGH",
   "showThroughPercent", showthrough::kStrengthOff, showthrough::kStrengthMax,
   showthrough::kStrengthOff, showthrough::kStrengthStandard, kPlain,
   ShowThroughPercent},
  {CornerDefocusPercent, "corner defocus", "CROSSPOINT_SIM_CORNER_DEFOCUS",
   "cornerDefocusPercent", cornerdefocus::kStrengthOff,
   cornerdefocus::kStrengthMax, cornerdefocus::kStrengthOff,
   cornerdefocus::kStrengthStandard, kPlain, CornerDefocusPercent},
  // The one of the three 2026-08-23 items that is still a Settings ROW rather
  // than a frozen value, because it is the one with a trade: it leaves the
  // glass dark for the whole sleep instead of holding the sleep screen. Ships
  // OFF, so the shipped value and the desktop default agree.
  {PowerOffCollapseOn, "power-off collapse", "CROSSPOINT_SIM_POWEROFF_COLLAPSE",
   "powerOffCollapse", 0, 1, 0, 0, kNoPresent, PowerOffCollapseOn},
};
// clang-format on

// A full set of dial values, indexed by Id. Small enough to pass by value and
// simple enough to have no invariant of its own -- it is the argument list the
// seed, the watcher and the as-shipped block all build in their own way.
struct Values {
  int v[kDialCount];
  int &operator[](Id id) { return v[id]; }
  int operator[](Id id) const { return v[id]; }
};

inline Values desktopDefaults() {
  Values out{};
  for (int i = 0; i < kDialCount; i++) out.v[i] = kDials[i].desktopDefault;
  return out;
}

inline Values shippedValues() {
  Values out{};
  for (int i = 0; i < kDialCount; i++) out.v[i] = kDials[i].shippedValue;
  return out;
}

// -1 when the key names no dial. Linear over 23 rows, called at most once per
// settings-file change, which is at most once a second.
inline int indexOfSettingsKey(const char *key) {
  if (!key) return -1;
  for (int i = 0; i < kDialCount; i++)
    if (std::strcmp(kDials[i].settingsKey, key) == 0) return i;
  return -1;
}

// True when `id` is the row whose setter call carries its whole group -- the
// one row per group the applier should act on.
inline bool isGroupLeader(Id id) { return kDials[id].group == id; }

}  // namespace simdials
