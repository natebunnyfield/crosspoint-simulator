#include "CrossPointPrefs.h"

#include "PanelPalette.h"
#include "PhosphorGrain.h"

#import <UIKit/UIKit.h>

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
// having seeded 3 from Root.plist, exactly like readAloudRatePercent above.
static NSString *const kRenderScale = @"renderScale";
static NSString *const kPanelPalettePreset = @"panelPalettePreset";
static NSString *const kBeamPaintMs = @"beamPaintMs";
static NSString *const kZenBottomRatio = @"zenBottomRatio";
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
static NSString *const kPanelInkLight = @"panelInkLight";
static NSString *const kPanelPaperLight = @"panelPaperLight";
static NSString *const kPanelInkDark = @"panelInkDark";
static NSString *const kPanelPaperDark = @"panelPaperDark";

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
        kZenModeEnabled : @NO,
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
        // The scale the app has always rendered at. 0 here would clamp to 1 --
        // a quarter of the glyph resolution -- so this fallback is doing real
        // work, not restating the plist for tidiness.
        kRenderScale : @(3),
        // Off: the page arrives at once, which is what every build before this
        // did and what an e-ink panel does.
        kBeamPaintMs : @(0),
        kZenBottomRatio : @(0),
        // Off: the page holds its brightness for as long as you read it, which
        // is what every build before this did.
        kPageFadeSeconds : @(0),
        // 100: the fade stops at the palette's legible floor, which is what
        // every build before this setting did. Missing-key failure mode is
        // MALIGNANT -- -integerForKey: returns 0 for an absent key, and 0 here
        // means FULLY TRANSPARENT, i.e. an owner who never opened this setting
        // would find the page fading away to nothing. This fallback is the
        // thing standing between an unseeded install and that.
        kPageFadeDepthPercent : @(100),
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

int CrossPointPrefs_pageFadeSeconds(void) {
  ensureDefaults();
  checkKnown(kPageFadeSeconds);
  // Stored as SECONDS, and as the duration itself rather than a row index --
  // same reasoning as beamPaintMs: a duration is meaningful on its own, so the
  // picker can be retuned without a migration and without a saved choice
  // quietly changing speed.
  const int s = static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:kPageFadeSeconds]);
  if (s < 0) return 0;
  // Ten minutes is already far past "fades while you read"; beyond it the
  // setting is indistinguishable from off and would hold the render loop open
  // for the whole of it.
  return s > 600 ? 600 : s;
}

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

int CrossPointPrefs_pageFadeDepthPercent(void) {
  ensureDefaults();
  checkKnown(kPageFadeDepthPercent);
  // Stored as the PROPORTION OF THE LEGIBLE FLOOR THAT IS KEPT, 0..100 -- the
  // meaningful value itself rather than a row index, same reasoning as
  // pageFadeSeconds above. 100 is today's behaviour; 0 is fully transparent.
  //
  // Read through -objectForKey: rather than -integerForKey: because 0 is a REAL
  // choice here and -integerForKey: cannot tell it from an absent key. That
  // distinction is load-bearing exactly once -- on an install whose defaults
  // somehow did not register -- and the wrong answer there is a page that fades
  // away for an owner who never asked it to.
  NSNumber *v = [[NSUserDefaults standardUserDefaults]
      objectForKey:kPageFadeDepthPercent];
  if (![v isKindOfClass:[NSNumber class]]) return 75;
  const int pct = v.intValue;
  if (pct < 0) return 0;
  return pct > 100 ? 100 : pct;
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

int CrossPointPrefs_zenBottomRatio(void) {
  ensureDefaults();
  checkKnown(kZenBottomRatio);
  // NOT clamped here, same reasoning as the palette preset: the shim resolves
  // an unknown integer to the default ratio, and deciding that twice is how
  // two answers drift.
  return static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:kZenBottomRatio]);
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

int CrossPointPrefs_renderScale(void) {
  ensureDefaults();
  checkKnown(kRenderScale);
  // CEILING not clamped here. cp::setRenderScale() clamps to [1, the ceiling
  // this binary was compiled at], and that ceiling is a compile-time fact this
  // file has no business restating -- a second clamp here would be the drift
  // that ships a 3 the framebuffer cannot hold, or refuses a 3 it can.
  //
  // FLOOR of 2 on iOS (owner ruling 2026-08-21: "keep 2x and 3x"). Panel (1x)
  // left the Sharpness picker, so a stored 1 from before the trim maps to
  // Exact (2x) -- the nearest survivor -- rather than silently keeping an
  // option the row no longer offers. Desktop QA can still force 1x through
  // CROSSPOINT_SIM_RENDER_SCALE, which bypasses this getter entirely.
  const int raw = static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:kRenderScale]);
  return raw == 1 ? 2 : raw;
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
