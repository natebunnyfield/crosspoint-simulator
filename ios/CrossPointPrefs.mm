#include "CrossPointPrefs.h"

#include "PanelPalette.h"

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

int CrossPointPrefs_renderScale(void) {
  ensureDefaults();
  checkKnown(kRenderScale);
  // NOT clamped here. cp::setRenderScale() clamps to [1, the ceiling this
  // binary was compiled at], and that ceiling is a compile-time fact this file
  // has no business restating -- a second clamp here would be the drift that
  // ships a 3 the framebuffer cannot hold, or refuses a 3 it can.
  return static_cast<int>(
      [[NSUserDefaults standardUserDefaults] integerForKey:kRenderScale]);
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
