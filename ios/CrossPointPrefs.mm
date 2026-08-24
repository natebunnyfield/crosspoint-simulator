#include "CrossPointPrefs.h"

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
// The panel's supersampling factor. Missing-key failure mode is MALIGNANT --
// -integerForKey: returns 0, and cp::setRenderScale(0) clamps to 1, i.e. the
// coarsest render the app can produce -- so this key relies on ensureDefaults()
// having seeded 2 from Root.plist, exactly like readAloudRatePercent above.
static NSString *const kRenderScale = @"renderScale";
static NSString *const kPanelPalettePreset = @"panelPalettePreset";
static NSString *const kBeamPaintMs = @"beamPaintMs";
// `zenBottomRatio` RETIRED 2026-08-22 (owner: "let's remove the option for
// every ratio but 1:2") — the five-rung ladder shipped 2026-08-21 and the shim
// now fixes the multiplier at 1:2. A stored value on an existing install is an
// ignored orphan key: nothing reads it, so checkKnown never fires for it.
// Whether the 1-bit pass may reach the screen ahead of the composed one. The
// missing-key answer from -integerForKey: is 0, which is Off, which is also the
// shipped default -- so this one is harmless either way.
static NSString *const kPresentFlash = @"presentFlash";
static NSString *const kPageFadeSeconds = @"pageFadeSeconds";
static NSString *const kPageFadeDepthPercent = @"pageFadeDepthPercent";
// Phosphor grain. The missing-key failure for the strength is the MALIGNANT
// one: -integerForKey: answers 0, and 0 here is the feature switched off while
// the picker still reads "1x — realistic". So it goes through -objectForKey:
// like the fade depth, for the same reason. The coverage's 0 is Even, which is
// both the shipped default and a legitimate value, so it is harmless either
// way.
// Split per appearance 2026-08-19. The single `phosphorGrainPercent` it
// replaces is deliberately NOT migrated: the owner asked for these two defaults
// by name, so carrying a stored single value into both would override the thing
// he just asked for. The old key is left in place rather than deleted -- it
// costs nothing, and reading it later is the only way to answer "what was it
// before" if anyone asks.
static NSString *const kPhosphorGrainPercentLight = @"phosphorGrainPercentLight";
static NSString *const kPhosphorGrainPercentDark = @"phosphorGrainPercentDark";
static NSString *const kPhosphorGrainCoverage = @"phosphorGrainCoverage";
// The mottle's two dials. Depth is stored in HUNDREDTHS (0, 3, 10, 30) because
// a picker persists integers and 0 is a real choice — "no blotching" — that
// -integerForKey: cannot distinguish from an absent key, same trap as the
// grain strength above.
static NSString *const kPhosphorGrainMottleDepth = @"phosphorGrainMottleDepth";
// The 2026-08-22 doctrine dials: letterpress for the light page, scanlines for
// the dark one. Both stored as the meaningful percent, both read through
// -objectForKey: because 0 is a real choice (the effect off) that
// -integerForKey: cannot tell from an absent key -- the same malignant trap as
// the grain strength above.
static NSString *const kLetterpressPercent = @"letterpressPercent";
// PAPER DEFECTS. Bound to a PSSliderSpecifier in Root.plist -- the bundle's
// FIRST slider row, every other one being a multi-value picker -- and to the
// light-mode drawer's Defects slider. ONE key, two views: a Settings.bundle row
// IS a view onto an NSUserDefaults key, so this is not a second source of
// truth. It has to be a slider and not a picker precisely because the drawer
// can store 47, and a PSMultiValueSpecifier renders BLANK for a value that is
// not one of its listed Values.
//
static NSString *const kScanlinesPercent = @"scanlinesPercent";
// The raster's PITCH, as a percent of the source-row pitch. 100 is the shipped
// one-line-per-row; there is no "off" value, so -integerForKey: would be safe
// here -- it is read the same way as its siblings anyway, because a 0 from an
// absent key would silently mean the finest pitch rather than "unset".
static NSString *const kScanlineSizePercent = @"scanlineSizePercent";
// Bloom strength, percent of the standard gain. 0 IS a real choice here -- a
// field with no content awareness at all -- so this one genuinely needs
// -objectForKey:, the same trap as the grain strength above.
static NSString *const kScanlineBloomPercent = @"scanlineBloomPercent";
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
    // in app system settings below zen bottom margin"). The KEYS keep working
    // — stored values, env overrides, and the in-app chip/mixer still read
    // and write them — but the derivation above no longer sees their
    // DefaultValues, so the former values are registered here. Without this
    // an untouched install would silently change look: panelPalettePreset
    // would answer 0 (Custom -> Default page) instead of CRT White, and grain
    // coverage would fall from Vignette + Mottled to Even.
    [[NSUserDefaults standardUserDefaults] registerDefaults:@{
      kPresentFlash : @(0),
      kPhosphorGrainPercentLight : @(60),
      kPhosphorGrainPercentDark : @(160),
      kPhosphorGrainCoverage : @(3),
      kPhosphorGrainMottleDepth : @(90),
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
      // screen awake indefinitely on battery. The pad levels fall back to the
      // shipped tones for the same reason — the alternative is 0, an invisible
      // pad, and an unlabeled control that draws nothing is not recoverable
      // from inside the app.
      NSLog(@"[CrossPoint] Settings.bundle/Root.plist unreadable; defaulting to allow-sleep");
      [[NSUserDefaults standardUserDefaults] registerDefaults:@{
        kAllowSleepOnBattery : @YES,
        kAllowSleepWhileCharging : @YES,
        kPadOutlineContrastLight : @(-1),
        kPadOutlineContrastDark : @(1),
        kPadFillContrastLight : @(-1),
        kPadFillContrastDark : @(1),
        // MUST MATCH Root.plist's DefaultValue for this key. This branch runs
        // only when Root.plist could not be read at all, so a drift between the
        // two is invisible until a packaging fault exposes it.
        kPadContrastPreset : @(4),  // padpalette::kPresetBlackWhite
        // ON by default (owner 2026-08-22: "default to zen mode on app
        // launch"). Registered defaults only fill ABSENCE: an install whose
        // owner stored zenModeEnabled=false keeps that choice.
        kZenModeEnabled : @YES,
        kReadAloudEnabled : @NO,
        kReadAloudRatePercent : @(100),
        // Default preset, and the four hex fields seeded with the tones that
        // preset selects -- so a first visit to Custom shows the page's actual
        // colors to edit from rather than four empty boxes.
        kPanelPalettePreset : @(1),  // panelpalette::kPresetDefault
        kPanelInkLight : @"2D2D2D",
        kPanelPaperLight : @"FBFBF9",
        kPanelInkDark : @"E0E0DE",
        kPanelPaperDark : @"121212",
        // renderScale was registered here until 2026-08-23, when its row went
        // and its getter stopped consulting NSUserDefaults. Registering a
        // default now would state a value nothing reads.
        // Off: the page arrives at once, which is what every build before this
        // did and what an e-ink panel does.
        kBeamPaintMs : @(0),
        // pageFadeSeconds and pageFadeDepthPercent were registered here until
        // 2026-08-23. Their getters no longer consult NSUserDefaults at all,
        // so registering a default would state a value nothing reads.
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

int CrossPointPrefs_phosphorGrainPercent(int dark) {
  ensureDefaults();
  NSString *const key =
      dark ? kPhosphorGrainPercentDark : kPhosphorGrainPercentLight;
  checkKnown(key);
  // Stored as a PERCENTAGE OF REALISTIC, the meaningful value itself rather
  // than a row index -- so the picker can gain steps without re-pointing what
  // an existing install already chose. 100 is realistic and is the default; 0
  // is off; 1000 is the 10x the owner asked for.
  //
  // -objectForKey: rather than -integerForKey: because 0 is a REAL choice and
  // the two cannot otherwise be told apart. The wrong answer on an install
  // whose defaults never registered would be a flat screen for an owner who
  // never turned grain off.
  NSNumber *v = [[NSUserDefaults standardUserDefaults] objectForKey:key];
  // The fallback is per appearance too: a missing key must not drop a dark
  // screen to the light strength, which is most of the way to flat.
  if (![v isKindOfClass:[NSNumber class]]) return dark ? 160 : 60;
  const int pct = v.intValue;
  if (pct < 0) return 0;
  return pct > 1000 ? 1000 : pct;
}

int CrossPointPrefs_phosphorGrainCoverage(void) {
  ensureDefaults();
  checkKnown(kPhosphorGrainCoverage);
  // 0 is Even, which is the shipped default -- so unlike the strength above,
  // -integerForKey:'s answer for a missing key is the right one and no
  // NSNumber dance is needed. Clamped in phosphorgrain::clampCoverage anyway;
  // clamped again here so a garbage store cannot reach the setter at all.
  const NSInteger raw =
      [[NSUserDefaults standardUserDefaults] integerForKey:kPhosphorGrainCoverage];
  if (raw < 0) return 0;
  return raw > 3 ? 0 : (int)raw;
}

int CrossPointPrefs_phosphorGrainMottleDepth(void) {
  ensureDefaults();
  checkKnown(kPhosphorGrainMottleDepth);
  // Hundredths. Read through -objectForKey: because 0 means "no blotching",
  // which is a legitimate choice and not the same as never having chosen.
  NSNumber *v = [[NSUserDefaults standardUserDefaults]
      objectForKey:kPhosphorGrainMottleDepth];
  if (![v isKindOfClass:[NSNumber class]])
    return (int)(phosphorgrain::kMottleDepthDefault * 100.0f);
  const int d = v.intValue;
  if (d < 0) return 0;
  return d > 100 ? 100 : d;
}

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
int CrossPointPrefs_showThroughPercent(void) { return 100; }

// FROZEN 2026-08-23 with the roadmap item that introduced it (D3). Same
// argument: the corner spot's growth is set by a tube's geometry, not by taste,
// and the one published bound (TG18's corner astigmatism ratio < 1.5) leaves no
// interesting range to offer. 100 = a corner spot 1.45x the centre's, an
// astigmatism ratio of 1.23.
//
// TEMPORARY ROW, added 2026-08-23 by owner ruling ("decide it on device
// first"). The effect measures SUB-CODE-VALUE on this app's rasters -- the
// corner loses 41% of its raster depth while the whole frame deviates by 1.0
// code value -- so no screenshot can settle whether it is visible and both of
// us would be guessing from numbers.
//
// It is a Settings ROW and not a defaults key, because the first attempt was a
// defaults key: unusable on a TestFlight build, where the owner has no shell.
// A probe he cannot reach is not a probe. The lesson generalises -- an
// on-device question needs an on-device control.
//
// DELETE THE ROW AND THIS BRANCH once the question is answered. It is a
// comparison, not a setting, and it should not outlive the decision. An absent
// key reads as ON, so an install that never opens Settings keeps the shipped
// value.
int CrossPointPrefs_cornerDefocusPercent(void) {
  ensureDefaults();
  NSNumber *v = [[NSUserDefaults standardUserDefaults]
      objectForKey:@"cornerDefocusEnabled"];
  if ([v isKindOfClass:[NSNumber class]] && !v.boolValue) return 0;
  return 100;
}

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

int CrossPointPrefs_presentFlash(void) {
  ensureDefaults();
  checkKnown(kPresentFlash);
  return [[NSUserDefaults standardUserDefaults] integerForKey:kPresentFlash] ? 1 : 0;
}

int CrossPointPrefs_beamPaintMs(void) {
  ensureDefaults();
  checkKnown(kBeamPaintMs);
  // Stored as the DURATION ITSELF rather than as a row index, so the picker's
  // rows can be added, reordered or retuned without a migration table and
  // without a saved choice ever pointing at a different speed. That is only
  // safe because the value is meaningful on its own -- unlike a palette preset,
  // which is a name for a pair of colors and must persist as an opaque integer.
  const int ms = static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:kBeamPaintMs]);
  if (ms < 0) return 0;
  // A sweep longer than this is not a beam, it is a wipe transition, and it
  // would hold the render loop open for the whole of it. Nothing in the picker
  // reaches here; a hand-edited plist would.
  return ms > 1000 ? 1000 : ms;
}

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
