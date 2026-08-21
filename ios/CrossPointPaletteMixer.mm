// The page-color modal: the P22 gun mixer.
//
// Owner ruling 2026-08-21: "the mixer ui sucks and doesn't actually mix
// colors. let's keep it simple and just make a ui for only p22. ignore
// everything else for now." This file previously held a four-tab table
// (Presets / Blend / Parts / Cascade, premix recipes, persistence-banded
// shelves); all of it is gone. What remains is the one mixer a color tube
// actually had: THREE GUNS.
//
//   [R slider]  P22R, the red gun
//   [G slider]  P22G, the green gun
//   [B slider]  P22B, the blue gun
//
// The blend is computed by the shipped core (phosphormix::mixBlend, linear
// light) and applied LIVE into the Custom slot as the sliders move -- the page
// behind the half-height sheet is the preview. Preset selection stays in
// Settings.app; this modal is only the mixer.
//
// The persistence story is flat by construction: all three P22 guns share the
// same 283 ms class, so the mixture dims in place with no color-shifting tail
// -- which the core reports on its own (equal-speed blends carry no tail).
//
// Storage is unchanged: the same phosphorMixBlend "preset:weight" CSV, mode
// Blend, mixActive -- so a mix built here reads back on the desktop through
// settings.json exactly as before, and old stored mixes from the removed UI
// still compute (the core kept every mode; only the UI narrowed).
//
// Owner's device crash (build 110, iOS 26.6) note carried forward: NO
// self.title anywhere in this controller. objc_retain(0x1) inside UIKit's
// setTitle: was the crash site, sidestepped in build 111; this rewrite keeps
// the sidestep.

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

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
static NSString *const kMixBlend = @"phosphorMixBlend";   // "11:w,40:w,24:w"
static NSString *const kMixActive = @"phosphorMixActive";
static NSString *const kInkLight = @"panelInkLight";
static NSString *const kPaperLight = @"panelPaperLight";
static NSString *const kInkDark = @"panelInkDark";
static NSString *const kPaperDark = @"panelPaperDark";

namespace {

// The guns. Preset integers pinned by name in PanelPalette.h.
constexpr int kGunPreset[3] = {panelpalette::kPresetRedCrt,     // P22R
                               panelpalette::kPresetP22GCrt,    // P22G
                               panelpalette::kPresetBlueTvCrt}; // P22B
// Slider range. 0 = that gun off (component omitted); the core clamps weights
// below 1, so omission is the only honest zero.
constexpr int kWeightMax = 100;

NSString *hexOf(const unsigned char c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
}

// Current gun weights from the store; absent or foreign CSV -> equal thirds.
void loadGuns(int w[3]) {
  w[0] = w[1] = w[2] = kWeightMax / 2;
  NSString *csv = [[NSUserDefaults standardUserDefaults] stringForKey:kMixBlend];
  if (!csv.length) return;
  int seen = 0;
  int parsed[3] = {0, 0, 0};
  for (NSString *pair in [csv componentsSeparatedByString:@","]) {
    NSArray<NSString *> *kv = [pair componentsSeparatedByString:@":"];
    if (kv.count != 2) continue;
    const int preset = kv[0].intValue;
    for (int g = 0; g < 3; g++)
      if (preset == kGunPreset[g]) {
        parsed[g] = MAX(0, MIN(kWeightMax, kv[1].intValue));
        seen++;
      }
  }
  // Only adopt the stored mix when it IS a gun mix; a Parts/Cascade-era store
  // or a blend of other phosphors keeps the neutral default instead of
  // half-adopting a foreign recipe.
  if (seen > 0)
    for (int g = 0; g < 3; g++) w[g] = parsed[g];
}

phosphormix::Result computeGuns(const int w[3]) {
  phosphormix::Component comps[3];
  int n = 0;
  for (int g = 0; g < 3; g++) {
    if (w[g] <= 0) continue;             // gun off = component absent
    comps[n].preset = kGunPreset[g];
    comps[n].weight = w[g];
    n++;
  }
  return phosphormix::mixBlend(comps, n);  // n==0 -> the default page
}

void applyGuns(const int w[3]) {
  NSMutableArray *parts = [NSMutableArray array];
  for (int g = 0; g < 3; g++)
    [parts addObject:[NSString stringWithFormat:@"%d:%d", kGunPreset[g], w[g]]];
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setObject:[parts componentsJoinedByString:@","] forKey:kMixBlend];
  [d setInteger:phosphormix::Blend forKey:kMixMode];

  const phosphormix::Result r = computeGuns(w);
  [d setObject:hexOf(r.light.ink) forKey:kInkLight];
  [d setObject:hexOf(r.light.paper) forKey:kPaperLight];
  [d setObject:hexOf(r.dark.ink) forKey:kInkDark];
  [d setObject:hexOf(r.dark.paper) forKey:kPaperDark];
  [d setBool:YES forKey:kMixActive];
  CrossPointPrefs_setPanelPalettePreset(panelpalette::kPresetCustom);
  CrossPointMixer_glowChanged();
  SimulatorOverlay::requestPresent();
  crosspointRequestRender();
}

}  // namespace

// The glow branch for the Custom slot (called from pollPanelGlow). Unchanged
// contract from the previous UI: any stored mix mode computes through the core.
extern "C" bool CrossPointMixer_glowForCustom(float *trailMs,
                                              unsigned char tail[3],
                                              bool *hasTail) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  if (![d boolForKey:kMixActive]) return false;
  int w[3];
  loadGuns(w);
  const phosphormix::Result r = computeGuns(w);
  *trailMs = r.trailMs;
  *hasTail = r.hasTail;
  for (int c = 0; c < 3; c++) tail[c] = r.tail[c];
  return true;
}

// --- the controller ---------------------------------------------------------

@interface CPXGunMixerController : UIViewController
@end

@implementation CPXGunMixerController {
  UISlider *_slider[3];
  UILabel *_value[3];
  UIView *_swatchDark;
  UIView *_swatchLight;
  UILabel *_readout;
  int _w[3];
}

- (void)viewDidLoad {
  [super viewDidLoad];
  SDL_Log("[mixer] p22 viewDidLoad");
  self.view.backgroundColor = UIColor.systemBackgroundColor;

  loadGuns(_w);

  static const char *kGunName[3] = {"P22R — red gun", "P22G — green gun",
                                    "P22B — blue gun"};
  UIFont *mono = [UIFont monospacedSystemFontOfSize:13 weight:UIFontWeightSemibold];
  UIFont *monoS = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightRegular];

  CGFloat y = 28;
  const CGFloat margin = 20;
  const CGFloat W = self.view.bounds.size.width;

  for (int g = 0; g < 3; g++) {
    const panelpalette::Palette gun =
        panelpalette::resolve(kGunPreset[g], true, -1, -1);
    UIColor *tint = [UIColor colorWithRed:gun.ink[0] / 255.0
                                    green:gun.ink[1] / 255.0
                                     blue:gun.ink[2] / 255.0
                                    alpha:1];
    UILabel *name = [UILabel new];
    name.text = @(kGunName[g]);
    name.font = mono;
    name.frame = CGRectMake(margin, y, W - 2 * margin - 60, 18);
    [self.view addSubview:name];

    _value[g] = [UILabel new];
    _value[g].font = monoS;
    _value[g].textColor = UIColor.secondaryLabelColor;
    _value[g].textAlignment = NSTextAlignmentRight;
    _value[g].frame = CGRectMake(W - margin - 56, y, 56, 18);
    [self.view addSubview:_value[g]];

    _slider[g] = [UISlider new];
    _slider[g].minimumValue = 0;
    _slider[g].maximumValue = kWeightMax;
    _slider[g].value = _w[g];
    _slider[g].minimumTrackTintColor = tint;
    _slider[g].tag = g;
    [_slider[g] addTarget:self
                   action:@selector(gunMoved:)
         forControlEvents:UIControlEventValueChanged];
    _slider[g].frame = CGRectMake(margin, y + 20, W - 2 * margin, 32);
    [self.view addSubview:_slider[g]];
    y += 62;
  }

  // The computed pair, both polarities, with exact hex. The page behind the
  // sheet is the real preview; these are the numbers.
  y += 6;
  _swatchDark = [UIView new];
  _swatchDark.layer.cornerRadius = 8;
  _swatchDark.layer.borderWidth = 1;
  _swatchDark.layer.borderColor = UIColor.separatorColor.CGColor;
  _swatchDark.frame = CGRectMake(margin, y, (W - 2 * margin - 12) / 2, 44);
  [self.view addSubview:_swatchDark];

  _swatchLight = [UIView new];
  _swatchLight.layer.cornerRadius = 8;
  _swatchLight.layer.borderWidth = 1;
  _swatchLight.layer.borderColor = UIColor.separatorColor.CGColor;
  _swatchLight.frame = CGRectMake(margin + (W - 2 * margin + 12) / 2, y,
                                  (W - 2 * margin - 12) / 2, 44);
  [self.view addSubview:_swatchLight];
  y += 52;

  _readout = [UILabel new];
  _readout.font = monoS;
  _readout.textColor = UIColor.secondaryLabelColor;
  _readout.numberOfLines = 2;
  _readout.frame = CGRectMake(margin, y, W - 2 * margin, 36);
  [self.view addSubview:_readout];

  UIButton *done = [UIButton buttonWithType:UIButtonTypeSystem];
  [done setTitle:@"Done" forState:UIControlStateNormal];
  done.titleLabel.font = mono;
  [done addTarget:self
                action:@selector(dismissSelf)
      forControlEvents:UIControlEventTouchUpInside];
  done.frame = CGRectMake(W - margin - 60, 0, 60, 28);
  [self.view addSubview:done];

  [self refresh];
  SDL_Log("[mixer] p22 controller ready");
}

- (void)dismissSelf {
  [self dismissViewControllerAnimated:YES completion:nil];
}

- (void)gunMoved:(UISlider *)s {
  _w[s.tag] = (int)lroundf(s.value);
  applyGuns(_w);
  [self refresh];
}

- (void)refresh {
  const phosphormix::Result r = computeGuns(_w);
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
  for (int g = 0; g < 3; g++)
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
    mixer.modalPresentationStyle = UIModalPresentationPageSheet;
    if (mixer.sheetPresentationController) {
      // Medium: about 320 pt of controls, and the PAGE stays visible above the
      // sheet -- the page is the preview.
      mixer.sheetPresentationController.detents =
          @[ UISheetPresentationControllerDetent.mediumDetent ];
    }
    [root presentViewController:mixer animated:YES completion:nil];
  });
}

// Headless test hook: drive the EXACT function the sliders call, so a scripted
// run exercises the same write path a finger does. Same family as
// CROSSPOINT_SIM_OPEN_MIXER / _TAP_CHIP in the shim.
extern "C" void CrossPointMixer_applyGunsForTest(int r, int g, int b) {
  int w[3] = {MAX(0, MIN(kWeightMax, r)), MAX(0, MIN(kWeightMax, g)),
              MAX(0, MIN(kWeightMax, b))};
  applyGuns(w);
  SDL_Log("[mixer] test hook applied guns %d/%d/%d", w[0], w[1], w[2]);
}
