// The page-color modal: the four-gun (RGBW) mixer.
//
// Owner ruling 2026-08-21: "the mixer ui sucks and doesn't actually mix
// colors. let's keep it simple and just make a ui for only p22. ignore
// everything else for now." This file previously held a four-tab table
// (Presets / Blend / Parts / Cascade, premix recipes, persistence-banded
// shelves); all of it is gone. What remains is the gun mixer, extended the
// same day to FOUR ASSIGNABLE GUNS on the industry-standard four-emitter
// channel scheme (RGBW — owner delegated the naming pick):
//
//   [R slider]  default P22R, the red gun
//   [G slider]  default P22G, the green gun
//   [B slider]  default P22B, the blue gun
//   [W slider]  default P45, the white gun — weight 0 by default, so a fresh
//               open renders the same page the three-gun build did
//
// Each gun's name row is a menu button: any mixable phosphor can be assigned
// to any gun, grouped by the core's persistence bands and sorted by its shelf
// key, so the mixer's shelves and the proof page order identically.
//
// The blend is computed by the shipped core (phosphormix::mixBlend, linear
// light) and applied LIVE into the Custom slot as the sliders move -- the page
// behind the half-height sheet is the preview. Preset selection stays in
// Settings.app; this modal is only the mixer.
//
// Storage: phosphorGunAssign is the new CSV of four assigned preset ints;
// phosphorMixBlend stays the mix of record, the same "preset:weight" CSV as
// before (weight-0 guns included) -- so a mix built here reads back on the
// desktop through settings.json exactly as before, and old stored mixes from
// the removed UI still compute (the core kept every mode; only the UI
// narrowed).
//
// Owner's device crash (build 110, iOS 26.6) note carried forward: NO
// self.title anywhere in this controller -- and none on the navigationItem
// either. objc_retain(0x1) inside UIKit's setTitle: was the crash site,
// sidestepped in build 111; this rewrite keeps the sidestep.

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <vector>

#include "PanelPalette.h"
#include "PhosphorMix.h"
#include "SimulatorOverlay.h"
#include "CrossPointPrefs.h"

// C++ LINKAGE, deliberately: defined in the firmware with no extern "C" --
// declaring it C made the mixer reference an unmangled symbol that does not
// exist, one of build 110's two link deaths.
void crosspointRequestRender();
extern "C" void CrossPointMixer_glowChanged(void);

// --- persistence (same keys as the removed UI and the desktop) --------------
static NSString *const kMixMode = @"phosphorMixMode";
static NSString *const kMixBlend = @"phosphorMixBlend";   // "11:w,40:w,24:w,21:w"
static NSString *const kMixActive = @"phosphorMixActive";
static NSString *const kGunAssign = @"phosphorGunAssign"; // "11,40,24,21"
static NSString *const kInkLight = @"panelInkLight";
static NSString *const kPaperLight = @"panelPaperLight";
static NSString *const kInkDark = @"panelInkDark";
static NSString *const kPaperDark = @"panelPaperDark";

namespace {

constexpr int kGunCount = 4;

// The channel labels: the industry-standard four-emitter scheme.
constexpr const char *kGunLabel[kGunCount] = {"R", "G", "B", "W"};

// Default assignments. Preset integers pinned by name in PanelPalette.h.
constexpr int kDefaultGunPreset[kGunCount] = {
    panelpalette::kPresetRedCrt,    // P22R
    panelpalette::kPresetP22GCrt,   // P22G
    panelpalette::kPresetBlueTvCrt, // P22B
    panelpalette::kPresetWhiteCrt}; // P45

// Default weights. W ships at 0 so a fresh open matches the three-gun build.
constexpr int kDefaultGunWeight[kGunCount] = {50, 50, 50, 0};

// Slider range. 0 = that gun off (component omitted); the core clamps weights
// below 1, so omission is the only honest zero.
constexpr int kWeightMax = 100;

NSString *hexOf(const unsigned char c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
}

// Current gun assignments + weights from the store. Assignments come from
// phosphorGunAssign and must be EXACTLY four valid mixable presets or the
// whole set falls back to the defaults -- half a stored assignment is a
// foreign recipe. Weights come from phosphorMixBlend matched by preset; a
// preset in the blend CSV not among the assignments is ignored, and a gun
// with no stored weight keeps its default.
void loadGuns(int presets[kGunCount], int w[kGunCount]) {
  for (int g = 0; g < kGunCount; g++) {
    presets[g] = kDefaultGunPreset[g];
    w[g] = kDefaultGunWeight[g];
  }
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  NSString *assign = [d stringForKey:kGunAssign];
  if (assign.length) {
    NSArray<NSString *> *parts = [assign componentsSeparatedByString:@","];
    int parsed[kGunCount];
    bool ok = parts.count == kGunCount;
    for (int g = 0; ok && g < kGunCount; g++) {
      parsed[g] = parts[g].intValue;
      ok = phosphormix::isMixablePreset(parsed[g]);
    }
    if (ok)
      for (int g = 0; g < kGunCount; g++) presets[g] = parsed[g];
  }
  NSString *csv = [d stringForKey:kMixBlend];
  if (!csv.length) return;
  for (NSString *pair in [csv componentsSeparatedByString:@","]) {
    NSArray<NSString *> *kv = [pair componentsSeparatedByString:@":"];
    if (kv.count != 2) continue;
    const int preset = kv[0].intValue;
    for (int g = 0; g < kGunCount; g++)
      if (preset == presets[g])
        w[g] = MAX(0, MIN(kWeightMax, kv[1].intValue));
  }
}

phosphormix::Result computeGuns(const int presets[kGunCount],
                                const int w[kGunCount]) {
  phosphormix::Component comps[kGunCount];
  int n = 0;
  for (int g = 0; g < kGunCount; g++) {
    if (w[g] <= 0) continue;             // gun off = component absent
    comps[n].preset = presets[g];
    comps[n].weight = w[g];
    n++;
  }
  return phosphormix::mixBlend(comps, n);  // n==0 -> the default page
}

// renderPage = ask the firmware for a full page re-render (re-layout + dither
// for the new pair). That render costs hundreds of ms and queues per call, so
// it must NOT ride on every slider tick -- a drag emits dozens of them and the
// page falls seconds behind the thumb (owner report 2026-08-21: "there is a
// large lag"). The LIVE half is cheap: the four hex fields plus
// requestPresent(), which recolors the CACHED framebuffer at present time,
// same mechanism as a dark-mode flip. The re-dither happens ONCE, when the
// finger lifts.
void applyGuns(const int presets[kGunCount], const int w[kGunCount],
               bool renderPage) {
  NSMutableArray *assign = [NSMutableArray array];
  NSMutableArray *parts = [NSMutableArray array];
  for (int g = 0; g < kGunCount; g++) {
    [assign addObject:[NSString stringWithFormat:@"%d", presets[g]]];
    [parts addObject:[NSString stringWithFormat:@"%d:%d", presets[g], w[g]]];
  }
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setObject:[assign componentsJoinedByString:@","] forKey:kGunAssign];
  [d setObject:[parts componentsJoinedByString:@","] forKey:kMixBlend];
  [d setInteger:phosphormix::Blend forKey:kMixMode];

  const phosphormix::Result r = computeGuns(presets, w);
  [d setObject:hexOf(r.light.ink) forKey:kInkLight];
  [d setObject:hexOf(r.light.paper) forKey:kPaperLight];
  [d setObject:hexOf(r.dark.ink) forKey:kInkDark];
  [d setObject:hexOf(r.dark.paper) forKey:kPaperDark];
  [d setBool:YES forKey:kMixActive];
  CrossPointPrefs_setPanelPalettePreset(panelpalette::kPresetCustom);
  CrossPointMixer_glowChanged();
  SimulatorOverlay::requestPresent();
  if (renderPage) crosspointRequestRender();
}

const panelpalette::PresetInfo *infoForPreset(int preset) {
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++)
    if (panelpalette::kPresetInfo[i].preset == preset)
      return &panelpalette::kPresetInfo[i];
  return nullptr;
}

// --- the shelf, resolved ONCE per process ----------------------------------
// Band membership, in-band order and row titles never change at runtime, but
// the old code recomputed all of them (34 resolve() calls per menu) on every
// reassignment, which is half of why the selector felt slow (owner 2026-08-21:
// "make the phosphor selector snappier"). The other half is fixed at the call
// sites: the menus are deferred, and the re-dither no longer rides the menu
// dismiss animation.
const std::vector<std::vector<int>> &shelfBands() {
  static const std::vector<std::vector<int>> bands = [] {
    std::vector<std::vector<int>> out(phosphormix::kTrailBandCount);
    struct Row { int preset; float key; };
    for (int band = 0; band < phosphormix::kTrailBandCount; band++) {
      std::vector<Row> rows;
      for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
        const auto &info = panelpalette::kPresetInfo[i];
        if (!phosphormix::isMixablePreset(info.preset)) continue;
        if (phosphormix::trailBand(
                panelpalette::trailMsForPreset(info.preset)) != band)
          continue;
        rows.push_back({info.preset, phosphormix::shelfSortKey(info.preset)});
      }
      std::sort(rows.begin(), rows.end(),
                [](const Row &a, const Row &b) { return a.key < b.key; });
      for (const Row &row : rows) out[band].push_back(row.preset);
    }
    return out;
  }();
  return bands;
}

NSString *shelfTitleFor(int preset) {
  static NSMutableDictionary<NSNumber *, NSString *> *titles;
  static dispatch_once_t once;
  dispatch_once(&once, ^{
    titles = [NSMutableDictionary dictionary];
    for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
      const auto &info = panelpalette::kPresetInfo[i];
      if (!phosphormix::isMixablePreset(info.preset)) continue;
      titles[@(info.preset)] = [NSString
          stringWithFormat:@"%s %s", info.phosphor ? info.phosphor : "?",
                           info.name ? info.name : "?"];
    }
  });
  return titles[@(preset)] ?: @"?";
}

}  // namespace

// The glow branch for the Custom slot (called from pollPanelGlow). Unchanged
// contract from the previous UI: any stored mix mode computes through the core.
extern "C" bool CrossPointMixer_glowForCustom(float *trailMs,
                                              unsigned char tail[3],
                                              bool *hasTail) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  if (![d boolForKey:kMixActive]) return false;
  int presets[kGunCount];
  int w[kGunCount];
  loadGuns(presets, w);
  const phosphormix::Result r = computeGuns(presets, w);
  *trailMs = r.trailMs;
  *hasTail = r.hasTail;
  for (int c = 0; c < 3; c++) tail[c] = r.tail[c];
  return true;
}

// --- the controller ---------------------------------------------------------

@interface CPXGunMixerController : UIViewController
@end

@implementation CPXGunMixerController {
  UIButton *_name[kGunCount];
  UISlider *_slider[kGunCount];
  UILabel *_value[kGunCount];
  UIView *_swatchDark;
  UIView *_swatchLight;
  UILabel *_readout;
  int _presets[kGunCount];
  int _w[kGunCount];
  // The coalesced deferred settle: the one pending firmware re-render, or nil.
  dispatch_block_t _pendingSettle;
}

- (void)viewDidLoad {
  [super viewDidLoad];
  SDL_Log("[mixer] p22 viewDidLoad");
  self.view.backgroundColor = UIColor.systemBackgroundColor;
  self.navigationItem.rightBarButtonItem = [[UIBarButtonItem alloc]
      initWithBarButtonSystemItem:UIBarButtonSystemItemDone
                           target:self
                           action:@selector(dismissSelf)];

  loadGuns(_presets, _w);

  UIFont *mono = [UIFont monospacedSystemFontOfSize:13 weight:UIFontWeightSemibold];
  UIFont *monoS = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightRegular];

  for (int g = 0; g < kGunCount; g++) {
    _name[g] = [UIButton buttonWithType:UIButtonTypeSystem];
    _name[g].titleLabel.font = mono;
    _name[g].contentHorizontalAlignment =
        UIControlContentHorizontalAlignmentLeading;
    _name[g].showsMenuAsPrimaryAction = YES;
    _name[g].tag = g;
    [self.view addSubview:_name[g]];

    _value[g] = [UILabel new];
    _value[g].font = monoS;
    _value[g].textColor = UIColor.secondaryLabelColor;
    _value[g].textAlignment = NSTextAlignmentRight;
    [self.view addSubview:_value[g]];

    _slider[g] = [UISlider new];
    _slider[g].minimumValue = 0;
    _slider[g].maximumValue = kWeightMax;
    _slider[g].value = _w[g];
    _slider[g].tag = g;
    [_slider[g] addTarget:self
                   action:@selector(gunMoved:)
         forControlEvents:UIControlEventValueChanged];
    [_slider[g] addTarget:self
                   action:@selector(gunDropped:)
         forControlEvents:UIControlEventTouchUpInside |
                          UIControlEventTouchUpOutside |
                          UIControlEventTouchCancel];
    [self.view addSubview:_slider[g]];
    [self applyAssignment:g];

    // The menu is DEFERRED and built once: the provider runs when the finger
    // opens it, never on a reassignment. Uncached, so the checkmark always
    // reflects the current assignment without any rebuild bookkeeping.
    __weak CPXGunMixerController *weakSelf = self;
    const int gun = g;
    _name[g].menu = [UIMenu
        menuWithTitle:@""
             children:@[ [UIDeferredMenuElement elementWithUncachedProvider:^(
                            void (^completion)(NSArray<UIMenuElement *> *)) {
               CPXGunMixerController *strongSelf = weakSelf;
               completion(strongSelf ? [strongSelf menuSectionsForGun:gun]
                                     : @[]);
             }] ]];
  }

  // The computed pair, both polarities, with exact hex. The page behind the
  // sheet is the real preview; these are the numbers.
  _swatchDark = [UIView new];
  _swatchDark.layer.cornerRadius = 8;
  _swatchDark.layer.borderWidth = 1;
  _swatchDark.layer.borderColor = UIColor.separatorColor.CGColor;
  [self.view addSubview:_swatchDark];

  _swatchLight = [UIView new];
  _swatchLight.layer.cornerRadius = 8;
  _swatchLight.layer.borderWidth = 1;
  _swatchLight.layer.borderColor = UIColor.separatorColor.CGColor;
  [self.view addSubview:_swatchLight];

  _readout = [UILabel new];
  _readout.font = monoS;
  _readout.textColor = UIColor.secondaryLabelColor;
  _readout.numberOfLines = 2;
  [self.view addSubview:_readout];

  [self refresh];
  SDL_Log("[mixer] p22 controller ready");
}

// Frame math, run whenever geometry settles: the nav bar's height rides in
// the safe area, so rows start 12 pt below it.
- (void)viewDidLayoutSubviews {
  [super viewDidLayoutSubviews];
  const CGFloat margin = 20;
  const CGFloat W = self.view.bounds.size.width;
  CGFloat y = self.view.safeAreaInsets.top + 12;
  for (int g = 0; g < kGunCount; g++) {
    _name[g].frame = CGRectMake(margin, y, W - 2 * margin - 60, 20);
    _value[g].frame = CGRectMake(W - margin - 56, y, 56, 20);
    _slider[g].frame = CGRectMake(margin, y + 20, W - 2 * margin, 32);
    y += 60;
  }
  y += 6;
  _swatchDark.frame = CGRectMake(margin, y, (W - 2 * margin - 12) / 2, 44);
  _swatchLight.frame = CGRectMake(margin + (W - 2 * margin + 12) / 2, y,
                                  (W - 2 * margin - 12) / 2, 44);
  y += 52;
  _readout.frame = CGRectMake(margin, y, W - 2 * margin, 36);
}

// Re-tints the gun's slider and retitles its menu button. Called at build
// time and on every reassignment. The menu itself never needs rebuilding: it
// is a deferred element whose provider reads _presets when opened.
- (void)applyAssignment:(int)g {
  const panelpalette::Palette gun =
      panelpalette::resolve(_presets[g], true, -1, -1);
  _slider[g].minimumTrackTintColor = [UIColor colorWithRed:gun.ink[0] / 255.0
                                                     green:gun.ink[1] / 255.0
                                                      blue:gun.ink[2] / 255.0
                                                     alpha:1];
  const panelpalette::PresetInfo *info = infoForPreset(_presets[g]);
  NSString *title =
      [NSString stringWithFormat:@"%s — %s %s", kGunLabel[g],
                                 info && info->phosphor ? info->phosphor : "?",
                                 info ? info->name : "?"];
  [_name[g] setTitle:title forState:UIControlStateNormal];
}

// Every mixable phosphor, grouped into the core's persistence bands (section
// titles from trailBandName), ordered within each band by shelfSortKey — the
// same grouping and order as the proof page, by construction. Membership,
// order and titles come from the once-per-process shelf caches; only the
// checkmark and the actions are built here, when the menu opens.
- (NSArray<UIMenuElement *> *)menuSectionsForGun:(int)g {
  __weak CPXGunMixerController *weakSelf = self;
  NSMutableArray<UIMenuElement *> *sections = [NSMutableArray array];
  const std::vector<std::vector<int>> &bands = shelfBands();
  for (int band = 0; band < phosphormix::kTrailBandCount; band++) {
    if (bands[band].empty()) continue;
    NSMutableArray<UIAction *> *actions = [NSMutableArray array];
    for (const int preset : bands[band]) {
      UIAction *a = [UIAction actionWithTitle:shelfTitleFor(preset)
                                        image:nil
                                   identifier:nil
                                      handler:^(UIAction *action) {
                                        [weakSelf assignGun:g preset:preset];
                                      }];
      a.state = preset == _presets[g] ? UIMenuElementStateOn
                                      : UIMenuElementStateOff;
      [actions addObject:a];
    }
    [sections addObject:[UIMenu menuWithTitle:@(phosphormix::trailBandName(band))
                                        image:nil
                                   identifier:nil
                                      options:UIMenuOptionsDisplayInline
                                     children:actions]];
  }
  return sections;
}

- (void)assignGun:(int)g preset:(int)preset {
  _presets[g] = preset;
  [self applyAssignment:g];
  // The CHEAP half lands now, so the page tint changes in the same frame the
  // menu starts dismissing; the firmware re-dither (hundreds of ms) is
  // deferred past the dismiss animation instead of stuttering it.
  applyGuns(_presets, _w, /*renderPage=*/false);
  [self refresh];
  [self scheduleSettle];
}

// The deferred, COALESCED settle: one firmware re-render, 0.35 s after the
// newest change. A newer change (another reassignment, or a slider touch-up,
// which renders on its own) cancels the pending one, so re-dithers never
// stack up behind a fast series of picks.
- (void)scheduleSettle {
  [self cancelPendingSettle];
  _pendingSettle = dispatch_block_create((dispatch_block_flags_t)0, ^{
    crosspointRequestRender();
  });
  dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.35 * NSEC_PER_SEC)),
                 dispatch_get_main_queue(), _pendingSettle);
}

- (void)cancelPendingSettle {
  if (!_pendingSettle) return;
  dispatch_block_cancel(_pendingSettle);
  _pendingSettle = nil;
}

- (void)dismissSelf {
  [self dismissViewControllerAnimated:YES completion:nil];
}

- (void)gunMoved:(UISlider *)s {
  // A drag is a newer change: a settle pending from a reassignment must not
  // fire mid-drag and put a re-render on the drag path.
  [self cancelPendingSettle];
  _w[s.tag] = (int)lroundf(s.value);
  applyGuns(_presets, _w, /*renderPage=*/false);
  [self refresh];
}

// The finger lifted: the mix is settled, so pay for the one firmware
// re-render that re-dithers the page's grays for the final pair. This render
// supersedes any deferred settle still pending.
- (void)gunDropped:(UISlider *)s {
  [self cancelPendingSettle];
  applyGuns(_presets, _w, /*renderPage=*/true);
}

- (void)refresh {
  const phosphormix::Result r = computeGuns(_presets, _w);
  _swatchDark.backgroundColor = [UIColor colorWithRed:r.dark.paper[0] / 255.0
                                                green:r.dark.paper[1] / 255.0
                                                 blue:r.dark.paper[2] / 255.0
                                                alpha:1];
  _swatchLight.backgroundColor = [UIColor colorWithRed:r.light.paper[0] / 255.0
                                                 green:r.light.paper[1] / 255.0
                                                  blue:r.light.paper[2] / 255.0
                                                 alpha:1];
  _readout.text = [NSString
      stringWithFormat:@"dark %@ on %@ · light %@ on %@\nfade %.0f ms",
                       hexOf(r.dark.ink), hexOf(r.dark.paper),
                       hexOf(r.light.ink), hexOf(r.light.paper),
                       (double)r.trailMs];
  for (int g = 0; g < kGunCount; g++)
    _value[g].text = _w[g] > 0 ? [NSString stringWithFormat:@"%d", _w[g]] : @"off";
}
@end

// --- entry point ------------------------------------------------------------

extern "C" void CrossPointMixer_present(void) {
  dispatch_async(dispatch_get_main_queue(), ^{
    int count = 0;
    SDL_Window **wins = SDL_GetWindows(&count);
    SDL_Window *win = (wins && count > 0) ? wins[0] : nullptr;
    SDL_free(wins);
    if (!win) return;
    UIWindow *uiWindow = (__bridge UIWindow *)SDL_GetPointerProperty(
        SDL_GetWindowProperties(win), SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER,
        nullptr);
    UIViewController *root = uiWindow.rootViewController;
    if (!root || root.presentedViewController) return;
    CPXGunMixerController *mixer = [CPXGunMixerController new];
    // Standard Done lives in a nav bar, so the sheet is a nav controller.
    // No title string is ever set on it -- see the build 110 crash note above.
    UINavigationController *nav =
        [[UINavigationController alloc] initWithRootViewController:mixer];
    nav.modalPresentationStyle = UIModalPresentationPageSheet;
    if (nav.sheetPresentationController) {
      // Medium: about 340 pt of controls, and the PAGE stays visible above the
      // sheet -- the page is the preview.
      nav.sheetPresentationController.detents =
          @[ UISheetPresentationControllerDetent.mediumDetent ];
      // Undimmed at medium: without this, UIKit dims the presenting view AND
      // pulls it back (down and slightly scaled), so the panel slid every time
      // the tray opened or closed (owner 2026-08-21: "prevent the panel from
      // sliding up and down"). The page above the sheet stays full-bright and
      // in place -- it IS the preview.
      nav.sheetPresentationController.largestUndimmedDetentIdentifier =
          UISheetPresentationControllerDetentIdentifierMedium;
    }
    [root presentViewController:nav animated:YES completion:nil];
  });
}

// Headless test hook: drive the EXACT function the sliders call, so a scripted
// run exercises the same write path a finger does. Assignments are always the
// defaults here (no env for assignments). Same family as
// CROSSPOINT_SIM_OPEN_MIXER / _TAP_CHIP in the shim.
extern "C" void CrossPointMixer_applyGunsForTest(int r, int g, int b, int w) {
  int weights[kGunCount] = {
      MAX(0, MIN(kWeightMax, r)), MAX(0, MIN(kWeightMax, g)),
      MAX(0, MIN(kWeightMax, b)), MAX(0, MIN(kWeightMax, w))};
  applyGuns(kDefaultGunPreset, weights, /*renderPage=*/true);
  SDL_Log("[mixer] test hook applied guns %d/%d/%d/%d", weights[0], weights[1],
          weights[2], weights[3]);
}
