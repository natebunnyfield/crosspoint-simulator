#include "CrossPointPrefs.h"

#include "GestureBindings.h"
#include "GunStore.h"
#include "PanelPalette.h"
#include "PanelPrefs.h"
#include "PanelSource.h"
#include "PhosphorGrain.h"

#import <UIKit/UIKit.h>

#include <cstdlib>

// Keys must match ios/Settings.bundle/Root.plist. A typo is silent:
// -boolForKey: on a missing key returns NO, which here would read as "never
// allow sleep" and hold the screen on forever. checkKnown() below turns that
// into a log line instead of a mystery.
static NSString *const kAllowSleepOnBattery = @"allowSleepOnBattery";
static NSString *const kAllowSleepWhileCharging = @"allowSleepWhileCharging";

// Same trap, worse failure: -integerForKey: on a missing key returns 0, which on
// this scale means "tone equals the field", i.e. an invisible outline AND an
// invisible press — a pad that shows nothing at all.
static NSString *const kPadOutlineContrastLight = @"padOutlineContrastLight";
static NSString *const kPadOutlineContrastDark = @"padOutlineContrastDark";
static NSString *const kPadFillContrastLight = @"padFillContrastLight";
static NSString *const kPadFillContrastDark = @"padFillContrastDark";
// The preset row above those four. 0 is Custom here, so the 0 a missing key
// returns means "read the four pickers" — which is the one answer that is never
// wrong whatever they hold, unlike the trap above. The registered default is
// still 1 (Current), from Root.plist.
static NSString *const kPadContrastPreset = @"padContrastPreset";

// Zen mode. Missing-key failure mode is benign — NO means the pad stays, which
// is the shipped default; the three-finger gesture and CROSSPOINT_SIM_ZEN can
// still toggle the live state regardless.
static NSString *const kZenModeEnabled = @"zenModeEnabled";
// Host bookkeeping, not a Settings.app row: the system appearance this app last
// acted on. Deliberately NOT registered as a default -- "never recorded" has to
// be distinguishable from "recorded as light", and a registration domain value
// would make -integerForKey: answer 0 for both.
static NSString *const kLastSeenSystemDark = @"lastSeenSystemDark";

// Read-aloud TTS. Here the missing-key failure mode is benign — NO means the
// feature stays off, which is also the shipped default.
static NSString *const kReadAloudEnabled = @"readAloudEnabled";
// ...and here it is malignant again: -integerForKey: on a missing key returns
// 0, which as a percentage of normal speaking rate is silence. The clamp in
// readAloudRatePercent() is what makes that survivable.
static NSString *const kReadAloudRatePercent = @"readAloudRatePercent";
static NSString *const kDiagnosticsEnabled = @"diagnosticsEnabled";

// The panel's own two tones. The missing-key failure mode for the preset is the
// benign one again: -integerForKey: returns 0, which here is Custom, i.e. "read
// the four hex fields" -- and those, missing, parse as invalid and fall back to
// the shipped tones. Every road from an empty store leads to the shipped look,
// which is the only acceptable answer for a control that decides whether text
// is legible at all.
static NSString *const kPanelPalettePreset = @"panelPalettePreset";
// ORPHANED KEYS -- stored on existing installs, named by nothing here.
// `renderScale`, `beamPaintMs`, `pageFadeSeconds`, `pageFadeDepthPercent`,
// `presentFlash`, `letterpressPercent`, `scanlinesPercent`,
// `scanlineSizePercent`, `scanlineBloomPercent`, `paperDefectsPercent`,
// `phosphorGrainPercentLight`, `phosphorGrainPercentDark`,
// `phosphorGrainCoverage`, `phosphorGrainMottleDepth`, the pre-2026-08-19
// single `phosphorGrainPercent` and `zenBottomRatio` all had constants here
// until their getters were frozen or deleted. A constant for a key no getter
// reads is not documentation, it is a claim that something reads it; the frozen
// getters below carry the reasons now. The VALUES are left in the store rather
// than cleared from it -- that costs nothing, and reading one later is the only
// way to answer "what was it before" if anyone asks. checkKnown() never fires
// for any of them, because nothing looks them up.

// THE POWER-OFF COLLAPSING DOT. A Settings.app row, and the only surface dial
// that is one -- see its getter for the argument.
static NSString *const kPowerOffCollapse = @"powerOffCollapse";
static NSString *const kPanelInkLight = @"panelInkLight";
static NSString *const kPanelPaperLight = @"panelPaperLight";
static NSString *const kPanelInkDark = @"panelInkDark";
static NSString *const kPanelPaperDark = @"panelPaperDark";

// NOT a Settings.bundle row, and deliberately so: nothing chooses this: it is
// written by whichever editor claims the Custom slot, so the OTHER polarity's
// phosphor survives the move. See CrossPointPrefs_claimCustomFor below and
// src/PanelSource.h. checkKnown() is therefore not called on it.
static NSString *const kPanelDarkSnapshotPreset = @"panelDarkSnapshotPreset";

// The mixer's own "a blend is in force" flag. Its writer is
// ios/CrossPointPaletteMixer.mm (kMixActive there); it is read here because the
// panel resolver has to know whether the mixer owns the dark page's decay.
// Two files naming one key is the existing shape in this store (panelInkLight
// is named in three), and the pairing is pinned by tests/panel_source_test.cpp.
static NSString *const kPhosphorMixActive = @"phosphorMixActive";

// THE DEFAULTS LIVE IN Root.plist AND NOWHERE ELSE.
//
// A Settings.bundle needs its defaults stated twice by construction, and the
// two halves do different jobs, so neither can simply be deleted:
//
//   DefaultValue in Root.plist   what Settings.app DISPLAYS for a key the owner
//                                has never touched. It does not write anything.
//   registerDefaults             what -boolForKey: RETURNS for that same
//                                untouched key. Settings.app cannot see it.
//
// Omit the first and the switch reads OFF while the app behaves as ON. Omit the
// second and every untouched key answers NO — here, "never allow sleep". So the
// duplication is unavoidable; what is avoidable is the DRIFT. This reads the
// shipped Root.plist and builds the registration domain out of its own
// DefaultValues, so there is one place to edit and adding a switch needs no
// code change at all.
static NSDictionary *defaultsFromSettingsBundle(void) {
  NSString *path = [[NSBundle mainBundle] pathForResource:@"Root"
                                                   ofType:@"plist"
                                              inDirectory:@"Settings.bundle"];
  NSDictionary *root = path ? [NSDictionary dictionaryWithContentsOfFile:path] : nil;
  NSArray *specifiers = root[@"PreferenceSpecifiers"];
  if (![specifiers isKindOfClass:NSArray.class]) return nil;

  NSMutableDictionary *defaults = [NSMutableDictionary dictionary];
  for (NSDictionary *spec in specifiers) {
    if (![spec isKindOfClass:NSDictionary.class]) continue;
    id key = spec[@"Key"];              // group specifiers have neither
    id value = spec[@"DefaultValue"];
    if ([key isKindOfClass:NSString.class] && value != nil) defaults[key] = value;
  }
  return defaults.count ? defaults : nil;
}

// A PRESET DEFAULTING TO Current WOULD SILENTLY OVERRIDE AN EXISTING DIAL.
//
// The preset row is new; the four fine pickers are not. On an upgrade the
// preset key has never been written, so it answers with its registered default
// (Current) and the four pickers stop being read — which for anyone who had
// dialled them in is their setting disappearing with no message and no way to
// tell why. Removing a capability quietly is the failure mode this whole file
// is written against, so the upgrade is migrated instead of assumed:
//
//   preset never written  AND  any of the four written to a NON-DEFAULT value
//     -> write preset = Custom, once.
//
// Explicitly written but equal to the shipped default is left alone: it selects
// the same tones either way, so Current is the more useful label for it. The
// write is what makes this a one-time migration — afterwards the key exists and
// this cannot fire again, including if the owner later chooses Current on
// purpose.
//
// -persistentDomainForName:, NOT -objectForKey:. This is the whole correctness
// of the thing and it is a trap that was live in this function for one build:
// -objectForKey: searches the ARGUMENT and REGISTRATION domains as well as the
// persistent one, so once registerDefaults has run — which is exactly when this
// is called from — it answers with the registered Current for a key nobody has
// ever written, the guard returns early every time, and the migration silently
// never fires. The persistent domain is only what has actually been written to
// disk, which is the question being asked.
static void migratePadPresetForExistingCustomisation(void) {
  NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
  NSString *suite = [[NSBundle mainBundle] bundleIdentifier];
  NSDictionary *written = suite ? [ud persistentDomainForName:suite] : nil;
  if (written[kPadContrastPreset] != nil) return;

  NSDictionary<NSString *, NSNumber *> *shipped = @{
    kPadOutlineContrastLight : @(-1),
    kPadFillContrastLight : @(-1),
    kPadOutlineContrastDark : @(1),
    kPadFillContrastDark : @(1),
  };
  for (NSString *key in shipped) {
    id stored = written[key];
    if ([stored isKindOfClass:NSNumber.class] &&
        [(NSNumber *)stored integerValue] != shipped[key].integerValue) {
      [ud setInteger:0 forKey:kPadContrastPreset];  // Custom
      NSLog(@"[CrossPoint] pad contrast: existing custom levels found (%@), "
            @"preset migrated to Custom",
            key);
      return;
    }
  }
}

// Six uppercase hex digits, the form every panel* field in this store holds and
// the only form panelpalette::parseHexRgb has to accept back.
static NSString *hexStringOf(const uint8_t c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
}

static void ensureDefaults(void) {
  static dispatch_once_t once;
  dispatch_once(&once, ^{
    NSDictionary *fromBundle = defaultsFromSettingsBundle();
    // ROWS REMOVED FROM Settings.app 2026-08-22 (owner: "remove all settings
    // in app system settings below zen bottom margin"). The KEYS that still
    // have readers keep working — stored values, env overrides, and the in-app
    // chip/mixer read and write them — but the derivation above no longer sees
    // their DefaultValues, so the former values are registered here. Without
    // this an untouched install would silently change look: panelPalettePreset
    // would answer 0 (Custom -> Default page) instead of CRT White.
    //
    // presentFlash and the four phosphorGrain* keys were registered here until
    // 2026-08-23, when their getters stopped consulting NSUserDefaults.
    // Registering a default now would state a value nothing reads -- the same
    // reason renderScale and the two pageFade keys already say so below.
    //
    // THIS BLOCK IS UNCONDITIONAL AND RUNS FIRST, which is what lets the
    // Root.plist-unreadable branch below carry only the keys that branch alone
    // owns. It used to restate ten of these, one of them (panelPalettePreset)
    // with a DIFFERENT value -- see there.
    [[NSUserDefaults standardUserDefaults] registerDefaults:@{
      kPanelPalettePreset : @(21),  // panelpalette::kPresetWhiteCrt
      kPanelInkLight : @"2D2D2D",
      kPanelPaperLight : @"FBFBF9",
      kPanelInkDark : @"E0E0DE",
      kPanelPaperDark : @"121212",
      kPadContrastPreset : @(4),  // padpalette::kPresetBlackWhite
      kPadOutlineContrastLight : @(-1),
      kPadFillContrastLight : @(-1),
      kPadOutlineContrastDark : @(1),
      kPadFillContrastDark : @(1),
    }];
    if (fromBundle) {
      [[NSUserDefaults standardUserDefaults] registerDefaults:fromBundle];
    } else {
      // Root.plist missing or unreadable — a packaging fault, not a
      // configuration. Fall back to letting the phone sleep, which is the
      // do-no-harm answer: the alternative failure mode holds a stranger's
      // screen awake indefinitely on battery. The pad's levels and the page's
      // colors need no fallback here at all — the unconditional block above
      // already registered them, and it registered exactly the shipped tones,
      // which is what makes a plist this branch cannot read a chrome failure
      // rather than a visual one.
      NSLog(@"[CrossPoint] Settings.bundle/Root.plist unreadable; defaulting to allow-sleep");
      // ONLY THE KEYS THIS BRANCH ALONE OWNS. Everything the unconditional
      // block above already registered is deliberately absent: -registerDefaults:
      // MERGES into the registration domain, and a key named twice takes the
      // value of the LAST call (measured, not assumed), so restating a key here
      // could only either repeat it or contradict it.
      //
      // It did contradict it. panelPalettePreset was registered @(21) (CRT
      // White) above and @(1) (Default) here, so a packaging fault silently
      // changed the page's colors on top of losing the sleep rows -- the one
      // symptom nobody would connect to an unreadable plist. 21 is the correct
      // value and the block above is its one statement: it is what the app
      // ships and what an untouched install renders, and a plist that will not
      // load is a reason to keep rendering that, not to repaint the page.
      // The four panelInk/panelPaper hex fields left with it; they were exact
      // duplicates, and a named preset ignores them anyway.
      [[NSUserDefaults standardUserDefaults] registerDefaults:@{
        kAllowSleepOnBattery : @YES,
        kAllowSleepWhileCharging : @YES,
        // ON by default (owner 2026-08-22: "default to zen mode on app
        // launch"). Registered defaults only fill ABSENCE: an install whose
        // owner stored zenModeEnabled=false keeps that choice.
        kZenModeEnabled : @YES,
        kReadAloudEnabled : @NO,
        kReadAloudRatePercent : @(100),
      }];
    }

    migratePadPresetForExistingCustomisation();

    // Off by default; without it batteryState is always UIDeviceBatteryStateUnknown.
    [UIDevice currentDevice].batteryMonitoringEnabled = YES;
  });
}

// Catches the one drift the derivation above cannot: a key renamed in the plist
// but not here, or vice versa. Logged once per key rather than asserted — a
// wrong sleep setting is not worth killing a reader mid-page over.
static void checkKnown(NSString *key) {
#if !defined(NDEBUG) || defined(ENABLE_SERIAL_LOG)
  static NSMutableSet *warned;
  static dispatch_once_t once;
  dispatch_once(&once, ^{ warned = [NSMutableSet set]; });
  if ([[NSUserDefaults standardUserDefaults] objectForKey:key] == nil && ![warned containsObject:key]) {
    [warned addObject:key];
    NSLog(@"[CrossPoint] pref key '%@' is not in Settings.bundle/Root.plist", key);
  }
#else
  (void)key;
#endif
}

int CrossPointPrefs_wantsScreenAwake(void) {
  ensureDefaults();

  const UIDeviceBatteryState state = [UIDevice currentDevice].batteryState;
  // Full counts as charging: the phone is on a cable, which is the thing the
  // owner is actually distinguishing. Unknown counts as battery — the
  // conservative side, since holding a phone awake on battery is the outcome
  // with a real cost.
  const BOOL charging =
      (state == UIDeviceBatteryStateCharging || state == UIDeviceBatteryStateFull);

  NSString *key = charging ? kAllowSleepWhileCharging : kAllowSleepOnBattery;
  checkKnown(key);

  // Read live rather than cached. NSUserDefaults is an in-memory store, so this
  // is a dictionary lookup, and reading it here means a change made in
  // Settings.app while the app was backgrounded takes effect on the first frame
  // after returning — no notification observer, nothing to forget to unregister.
  const BOOL allowSleep = [[NSUserDefaults standardUserDefaults] boolForKey:key];
  return allowSleep ? 0 : 1;
}

// Read live, same as above and for the same reason: NSUserDefaults is an
// in-memory store, so this is a dictionary lookup, and a level changed in
// Settings.app while the app was backgrounded lands on the first frame after it
// returns. No observer, nothing to unregister.
static int padContrast(NSString *key) {
  ensureDefaults();
  checkKnown(key);
  NSInteger level = [[NSUserDefaults standardUserDefaults] integerForKey:key];
  // Clamp rather than trust: the value comes from a plist a user can edit
  // through a jailbroken Settings or a restored backup, and the caller indexes
  // a 19-entry table with it.
  if (level < -9) level = -9;
  if (level > 9) level = 9;
  return static_cast<int>(level);
}

int CrossPointPrefs_padOutlineContrast(int dark) {
  return padContrast(dark ? kPadOutlineContrastDark : kPadOutlineContrastLight);
}

int CrossPointPrefs_zenModeEnabled(void) {
  ensureDefaults();
  checkKnown(kZenModeEnabled);
  // Read live, same as everything here: a toggle flipped in Settings.app
  // while the app was backgrounded lands on the first frame after returning.
  return [[NSUserDefaults standardUserDefaults] boolForKey:kZenModeEnabled] ? 1
                                                                            : 0;
}

int CrossPointPrefs_lastSeenSystemDark(void) {
  // objectForKey, not integerForKey: absence is the answer that matters here
  // and integerForKey collapses it into 0 (light). Not checkKnown'd and not
  // in the defaults registration for the same reason.
  NSNumber *v = [[NSUserDefaults standardUserDefaults] objectForKey:kLastSeenSystemDark];
  if (![v isKindOfClass:[NSNumber class]]) return -1;
  return [v intValue] != 0 ? 1 : 0;
}

void CrossPointPrefs_setLastSeenSystemDark(int dark) {
  [[NSUserDefaults standardUserDefaults] setObject:@(dark ? 1 : 0)
                                            forKey:kLastSeenSystemDark];
}

int CrossPointPrefs_readAloudEnabled(void) {
  ensureDefaults();
  checkKnown(kReadAloudEnabled);
  // Read live, same as everything here: a toggle flipped in Settings.app
  // while the app was backgrounded lands on the first frame after returning.
  return [[NSUserDefaults standardUserDefaults] boolForKey:kReadAloudEnabled]
             ? 1
             : 0;
}

int CrossPointPrefs_readAloudRatePercent(void) {
  ensureDefaults();
  checkKnown(kReadAloudRatePercent);
  NSInteger percent = [[NSUserDefaults standardUserDefaults]
      integerForKey:kReadAloudRatePercent];
  // Clamp WIDER than the steps Root.plist offers (50..200), because this is
  // guarding against a value the picker never produced -- a restored backup,
  // a hand-edited plist, or the 0 a missing key returns. 25 is slow enough to
  // transcribe from and 300 is past the point AVSpeech saturates, so nothing
  // outside is worth honouring.
  if (percent < 25) percent = 25;
  if (percent > 300) percent = 300;
  return static_cast<int>(percent);
}

int CrossPointPrefs_diagnosticsEnabled(void) {
  // The headless door. A sandboxed app's NSUserDefaults live in its data
  // container, so a simulator run cannot flip the Settings.app row without
  // tapping through Settings by hand -- and the accessibility log is the one
  // instrument this area has. `CROSSPOINT_SIM_DIAGNOSTICS=1` turns it on for a
  // scripted run; it is read once, and it can only ENABLE (the owner's Off
  // stays Off unless a run asks for the instrument).
  static const bool forced = [] {
    const char *v = std::getenv("CROSSPOINT_SIM_DIAGNOSTICS");
    return v != nullptr && v[0] == '1';
  }();
  if (forced) return 1;
  ensureDefaults();
  checkKnown(kDiagnosticsEnabled);
  // Default OFF (owner ruling 2026-08-09: "disable diagnostics for now"). The
  // toggle stays in Settings.app so a TestFlight investigation can turn the
  // instrument back on without shipping a build -- which is the whole reason
  // the instrument exists.
  return [[NSUserDefaults standardUserDefaults] boolForKey:kDiagnosticsEnabled] ? 1 : 0;
}

int CrossPointPrefs_padFillContrast(int dark) {
  return padContrast(dark ? kPadFillContrastDark : kPadFillContrastLight);
}

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
// 0 = Off: the page holds its brightness.
int CrossPointPrefs_pageFadeSeconds(void) { return 0; }

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
//
// ALL FOUR OF THE GRAIN'S DIALS, frozen at the values their rows registered:
// 60 light / 160 dark strength, Vignette+Mottled coverage, 0.90 blotch depth,
// and the model's own blotch SIZE (never a stored setting -- the shim pushes
// phosphorgrain::kMottleCellsDefault).
//
// PER APPEARANCE, and that is not cosmetic: the same grain reads very
// differently on a black page and a white one, so one number cannot serve both.
// `dark` is 0 for light, 1 for dark.
//
// NOTE WHAT THIS ACTUALLY RENDERS TODAY, WHICH IS NOTHING. HalDisplay skips the
// grain pass entirely while letterpress (light) or scanlines (dark) is live,
// and the app freezes BOTH of those on -- so on the phone this field is never
// composited. It is frozen honestly anyway, so that turning a doctrine dial off
// falls back to exactly the grain the app last shipped rather than to whatever
// a pre-2026-08-22 install happens to hold.
int CrossPointPrefs_phosphorGrainPercent(int dark) { return dark ? 160 : 60; }

int CrossPointPrefs_phosphorGrainCoverage(void) {
  return phosphorgrain::VignetteMottled;
}

// Hundredths, so 90 is a depth of 0.90.
int CrossPointPrefs_phosphorGrainMottleDepth(void) { return 90; }

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
// 100 = Standard, a visible impression. Still the master the light
// drawer's press sub-dials scale against.
int CrossPointPrefs_letterpressPercent(void) { return 100; }

// FROZEN 2026-08-23 by owner ruling: this was a Settings.bundle row, then for
// part of one day the light drawer's Defects slider, and is now neither ("set
// Paper, tooth, formation, defects and press to these parameter values, then
// remove sliders and option to set this in app"). The value below is the one
// the owner had chosen when he ruled, and it is returned WITHOUT consulting
// NSUserDefaults -- an install that stored a different value before the
// control was removed must not keep rendering it, and with the control gone
// there would be no way to change it back. The setter and the
// paperDefectsPercent key went with it: nothing writes that key any more, and
// a key naming a value nothing consults is worse than no key.
// 0 = a fresh sheet, unmarked.
int CrossPointPrefs_paperDefectsPercent(void) { return 0; }

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
// 50 = Subtle, the raster at a glance.
int CrossPointPrefs_scanlinesPercent(void) { return 50; }

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
// 100 = Fine, one line per page row.
int CrossPointPrefs_scanlineSizePercent(void) { return 100; }

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
// 400 = Extreme, text burns through the raster.
int CrossPointPrefs_scanlineBloomPercent(void) { return 400; }

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
// 0 = fully transparent. Moot while the fade is Off, and kept honest
// anyway so the two cannot disagree if the fade is ever revived.
int CrossPointPrefs_pageFadeDepthPercent(void) { return 0; }

// FROZEN 2026-08-23 with the roadmap item that introduced it (1a). There is
// one obviously right value: show-through is physics, and the quantity that
// genuinely varies -- how thin the sheet is -- is already a choice the owner
// makes, in the paper picker, so a second dial beside it would be two
// authorities over one number. 100 = the reference sheet's own show-through;
// CrossPointInkPicker multiplies the CHOSEN STOCK's factor into it before it
// reaches the SDL side, which is why a bible paper shows through three times as
// much as a bright white and a calfskin barely at all.
//
// HALVED TO 50 on 2026-08-24, owner: "half the verso bleed visibility." 100 was
// the reference sheet's own show-through, and with India's 3.0x that landed on
// showthrough::kStrengthMax exactly -- the model's ceiling, sized for the
// thinnest stock it offers. So the shipped page was carrying the most
// show-through the model can express, on the thinnest paper in the list. 50
// puts it at 150, half the visibility and half the sheet's darkening budget
// share, with the stock still doing the varying.
int CrossPointPrefs_showThroughPercent(void) { return 50; }

// FROZEN 2026-08-23 with the roadmap item that introduced it (D3). Same
// argument: the corner spot's growth is set by a tube's geometry, not by taste,
// and the one published bound (TG18's corner astigmatism ratio < 1.5) leaves no
// interesting range to offer. 100 = a corner spot 1.45x the centre's, an
// astigmatism ratio of 1.23.
//
// OFF, 2026-08-23, and the reason is worth more than the feature.
//
// The model is right: the beam spot grows and turns elliptical off-axis, so the
// corner loses 41% of its raster depth while the centre and the side midpoints
// lose exactly nothing. TG18 bounds the astigmatism ratio and the shipped 1.23
// sits inside it. None of that is in question.
//
// What is in question is whether a reader can SEE it, and the answer is no.
// Whole-frame deviation is one code value; the effect modulates the scanline
// field, and the corners of a reading page hold no text -- so the region where
// the effect is strongest is uniform ground, where a 1/255 change in the depth
// of a faint periodic texture is nothing at all. A Settings row was shipped to
// let the owner judge it on glass; he looked and reported "nothing is being
// rendered in any corners", which is the correct observation, not a missed one.
//
// The test designed to answer this could not be passed. That is a fault in the
// test, and by extension in shipping an effect whose visibility was never
// established before it was built.
//
// Kept, not deleted: src/CornerDefocus.h, its host test and its doc all stand,
// so re-enabling is this one number if a denser panel ever makes it visible.
// Returning 0 also gives back ~42 ms per dark page turn, which was above the
// cheap class.
int CrossPointPrefs_cornerDefocusPercent(void) { return 0; }

// A ROW, NOT A FROZEN VALUE, and the only one of the three 2026-08-23 items
// that is. Every other surface dial has an answer that is simply right; this
// one has a TRADE. Turning it on means the tube switches off at sleep and the
// glass stays dark for the whole sleep, instead of holding the sleep screen --
// which is a real feature with a book cover or a clock on it. Nobody may make
// that trade on the owner's behalf, which is also why it defaults OFF.
int CrossPointPrefs_powerOffCollapse(void) {
  ensureDefaults();
  checkKnown(kPowerOffCollapse);
  return [[NSUserDefaults standardUserDefaults] boolForKey:kPowerOffCollapse] ? 1
                                                                              : 0;
}

// FROZEN 2026-08-23 by owner ruling: these were Settings.bundle rows and are
// not any more. The value below is the one the owner had chosen when he ruled
// ("make these settings the default and remove them from ios app settings as
// options"), and it is returned WITHOUT consulting NSUserDefaults -- an install
// that stored a different value before the row was removed must not keep
// rendering it, and with the row gone there would be no way to change it back.
//
// 0 = off: the 1-bit pass is held and only the composed frame lands, which is
// what every build before the flash became a dial did. The owner did ask for
// this one as a row on 2026-08-19 ("make that page-turn flash an option in ios
// settings"); the 2026-08-22 sweep of everything below the zen margin took it
// with the rest of the group, and it has had no writer since. Reinstating it is
// a Root.plist row plus unfreezing this -- an owner decision, not a cleanup.
// The desktop keeps CROSSPOINT_SIM_PRESENT_FLASH either way.
int CrossPointPrefs_presentFlash(void) { return 0; }


int CrossPointPrefs_panelPalettePreset(void) {
  ensureDefaults();
  checkKnown(kPanelPalettePreset);
  // NOT clamped and NOT validated here, for the same reason the pad preset is
  // not: an unknown integer is handed straight to panelpalette::resolve, which
  // answers anything it does not recognize with Default. Deciding that twice,
  // in two files, is how the two answers drift.
  return static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:kPanelPalettePreset]);
}


void CrossPointPrefs_setPanelPalettePreset(int preset) {
  ensureDefaults();
  // Not validated here for the same reason the getter does not validate: an
  // unknown integer resolves to Default in panelpalette::resolve, and deciding
  // that in a second place is how two answers drift.
  [[NSUserDefaults standardUserDefaults] setInteger:preset
                                             forKey:kPanelPalettePreset];
}

int CrossPointPrefs_phosphorMixActive(void) {
  ensureDefaults();
  return [[NSUserDefaults standardUserDefaults] boolForKey:kPhosphorMixActive]
             ? 1
             : 0;
}

int CrossPointPrefs_darkSnapshotPreset(void) {
  ensureDefaults();
  // An absent key answers 0 = kPresetCustom = "no phosphor", which is the
  // historical answer for every install that predates this key. Not validated,
  // for the third time in this file: panelsource::glowPreset and
  // panelpalette::trailMsForPreset resolve an unknown integer themselves.
  return static_cast<int>([[NSUserDefaults standardUserDefaults]
      integerForKey:kPanelDarkSnapshotPreset]);
}

void CrossPointPrefs_claimCustomFor(int editingDark) {
  ensureDefaults();
  const panelsource::Claim claim = panelsource::claimCustom(
      CrossPointPrefs_panelPalettePreset(), editingDark != 0);
  if (!claim.freezeOther) return;  // already Custom: both polarities are chosen

  // RESOLVED BEFORE THE PRESET MOVES, which is the whole point: once the preset
  // is Custom the named preset's pair is unreachable and the frozen polarity
  // would fall back to whatever stale hex the fields happen to hold.
  const panelpalette::Palette other = crosspoint::panelForPrefs(claim.freezeDark);
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setObject:hexStringOf(other.ink)
        forKey:claim.freezeDark ? kPanelInkDark : kPanelInkLight];
  [d setObject:hexStringOf(other.paper)
        forKey:claim.freezeDark ? kPanelPaperDark : kPanelPaperLight];
  if (claim.freezeDark)
    [d setInteger:claim.rememberPhosphor forKey:kPanelDarkSnapshotPreset];
  CrossPointPrefs_setPanelPalettePreset(panelpalette::kPresetCustom);
  NSLog(@"[CrossPoint] palette: %@ editor claimed Custom; froze %@ at "
        @"%@ on %@%@",
        editingDark ? @"dark (mixer)" : @"light (ink picker)",
        claim.freezeDark ? @"dark" : @"light", hexStringOf(other.ink),
        hexStringOf(other.paper),
        claim.freezeDark
            ? [NSString stringWithFormat:@", phosphor preset %d",
                                         claim.rememberPhosphor]
            : @"");
}

void CrossPointPrefs_selectPanelPreset(int preset) {
  ensureDefaults();
  const panelsource::Release release = panelsource::releaseCustom(preset);
  if (!release.apply) {
    NSLog(@"[CrossPoint] palette: preset %d is not a selectable row; ignored",
          preset);
    return;
  }
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  // THE TWO CUSTOM-ONLY KEYS GO FIRST, and they are written rather than left.
  // Both are read only while the slot is Custom, so a stale one is silent until
  // the next claim and then decides against the owner: glowPreset asks the mix
  // flag BEFORE the frozen phosphor, so a blend from a page that is no longer
  // on screen would own the decay of a preset chosen after it. src/PanelSource.h.
  [d setBool:release.mixActive ? YES : NO forKey:kPhosphorMixActive];
  [d setInteger:release.darkSnapshotPreset forKey:kPanelDarkSnapshotPreset];
  CrossPointPrefs_setPanelPalettePreset(release.preset);
  // The four hex fields are deliberately untouched -- a named preset ignores
  // them, and the next claim re-freezes whichever polarity it does not own from
  // the preset's own pair.
  NSLog(@"[CrossPoint] palette: preset %d selected for BOTH appearances "
        @"(mix cleared, no frozen phosphor)",
        release.preset);

  // ...AND THE GUNS ARE SEEDED TO MATCH IT. Owner 2026-08-23: "selecting a
  // preset should set the guns' values too." Without this the mixer opened
  // showing a recipe from some earlier session, and the first slider move
  // jumped the page to it instead of nudging it.
  //
  // THE MIX IS NOT TURNED ON. phosphorMixActive was just cleared above and
  // stays cleared: the preset still owns the page (panelsource::panelFor
  // resolves the name and ignores the hex), and moving a gun claims the Custom
  // slot exactly as it did before. The guns are being seeded to MATCH, not
  // activated -- turning them on here would put a blend on screen under a
  // preset's name, which is S-020.
  //
  // The decision is phosphormix::seedForPreset and nothing about it is decided
  // here; a preset a four-gun blend cannot be (the three cascade premixes, and
  // every paper row the LIGHT picker offers) refuses, and refusing means the
  // stored recipe is left exactly as it was.
  int guns[gunmix::kGunCount], weights[gunmix::kGunCount];
  gunstore::load(guns, weights);
  const phosphormix::GunSeed seed =
      phosphormix::seedForPreset(release.preset, guns);
  if (!seed.apply) {
    NSLog(@"[CrossPoint] palette: guns left alone -- %s",
          phosphormix::seedReasonText(seed.reason));
    return;
  }
  gunstore::save(seed.preset, seed.weight);
  NSLog(@"[CrossPoint] palette: guns seeded (%s) %d:%d,%d:%d,%d:%d,%d:%d",
        phosphormix::seedReasonText(seed.reason), seed.preset[0],
        seed.weight[0], seed.preset[1], seed.weight[1], seed.preset[2],
        seed.weight[2], seed.preset[3], seed.weight[3]);
}

int CrossPointPrefs_renderScale(void) {
  ensureDefaults();
  // No checkKnown: renderScale is deliberately not a Settings.bundle row any
  // more, so an absent value is the normal state rather than a missing row.
  // CEILING not clamped here. cp::setRenderScale() clamps to [1, the ceiling
  // this binary was compiled at], and that ceiling is a compile-time fact this
  // file has no business restating -- a second clamp here would be the drift
  // that ships a 3 the framebuffer cannot hold, or refuses a 3 it can.
  //
  // A RETIRED ROW MAPS TO ITS NEAREST SURVIVOR, because the choice persists as
  // an integer and an install that has already stored one keeps answering with
  // it long after the row is gone. Same shape as panelpalette::resolve, where a
  // retired preset behaves exactly like an unknown one rather than falling
  // through to whatever the enum now numbers.
  //
  // 3 is retired as of 2026-08-23 (owner: "drop 3x support for now"), so a
  // store written by build 129 or earlier -- where 3 was both an offered row
  // and the DEFAULT, i.e. most installs -- answers 3 here. 1 was retired
  // earlier, on 2026-08-21 ("keep 2x and 3x").
  //
  // With both of those gone the row itself went (owner 2026-08-23): a
  // one-value control is worse than no control. So this is no longer a
  // PREFERENCE -- it is the single scale the app renders at, and every stored
  // value maps to it. Reading NSUserDefaults at all would only let an old
  // store re-point something the owner can no longer see or change.
  //
  // Deliberately not left to cp::setRenderScale()'s ceiling clamp, which is
  // about what the BINARY can hold and would silently start meaning something
  // else the moment that ceiling moved.
  return 2;
}

int CrossPointPrefs_panelCustomColor(int dark, int ink) {
  ensureDefaults();
  NSString *key = dark ? (ink ? kPanelInkDark : kPanelPaperDark)
                       : (ink ? kPanelInkLight : kPanelPaperLight);
  checkKnown(key);
  // -stringForKey: also answers for a value stored as a number, which is what a
  // hand-edited plist or a restored backup can hold; anything it cannot render
  // as a string comes back nil and parses as invalid. Read live, same as
  // everything here.
  NSString *value = [[NSUserDefaults standardUserDefaults] stringForKey:key];
  return panelpalette::parseHexRgb(value ? value.UTF8String : nullptr);
}

int CrossPointPrefs_padContrastPreset(void) {
  ensureDefaults();
  checkKnown(kPadContrastPreset);
  // NOT clamped and NOT validated here. An unknown integer — a restored backup
  // from a future build, a hand-edited plist — is handed straight to
  // padpalette::resolveLevels, which resolves anything it does not recognize as
  // Current. Deciding that twice, in two files, is how the two answers drift.
  return static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:kPadContrastPreset]);
}

// WHAT ONE GESTURE IS BOUND TO. A FETCH, NOT A DECISION -- every fallback lives
// in ios/GestureBindings.h, which is pure and host-tested, so there is exactly
// one place a binding can be decided and it is not this file (owner ruling
// 2026-08-28, T-025).
//
// checkKnown() is NOT called. It logs a key that is missing from the
// registration domain, and these keys are in Root.plist like any other row, so
// a real absence here means an unreadable Settings.bundle -- which already logs
// once, loudly, in ensureDefaults(). Twenty-eight more lines saying the same thing
// per gesture would bury it.
//
// Read live, same as everything else here: a binding changed in Settings.app
// while the app was backgrounded lands on the first gesture after it returns.
// No observer, nothing to unregister.
int CrossPointPrefs_gestureBinding(int gesture) {
  ensureDefaults();
  if (gesture < 0 || gesture >= gesturebind::kGestureCount)
    return static_cast<int>(gesturebind::Action::Unset);
  NSString *key = [NSString
      stringWithUTF8String:gesturebind::key(
                               static_cast<gesturebind::Gesture>(gesture))];
  return static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:key]);
}

// HAS THE OWNER ACTUALLY WRITTEN THIS BINDING? See the header for why
// -integerForKey: cannot answer it.
//
// -persistentDomainForName:, NOT -objectForKey:, for exactly the reason spelled
// out above migratePadPresetForExistingCustomisation: -objectForKey: searches
// the registration domain as well, so once ensureDefaults() has run -- which is
// always, by the time anything asks -- it answers for every key in Root.plist
// whether or not a human ever touched it. The persistent domain is only what has
// been written to disk, which is the question.
int CrossPointPrefs_gestureBindingIsExplicit(int gesture) {
  ensureDefaults();
  if (gesture < 0 || gesture >= gesturebind::kGestureCount) return 0;
  NSUserDefaults *ud = [NSUserDefaults standardUserDefaults];
  NSString *suite = [[NSBundle mainBundle] bundleIdentifier];
  NSDictionary *written = suite ? [ud persistentDomainForName:suite] : nil;
  NSString *key = [NSString
      stringWithUTF8String:gesturebind::key(
                               static_cast<gesturebind::Gesture>(gesture))];
  return written[key] != nil ? 1 : 0;
}
