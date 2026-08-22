// The page-color modal for LIGHT appearance: historical inks at variable
// density on proven paper stocks.
//
// Doctrine (owner order 2026-08-22): light mode is paper-and-ink emulation
// with letterpress; dark mode is the CRT and keeps the gun mixer
// (CrossPointPaletteMixer.mm). The page-color chip branches on the live
// appearance -- light opens this, dark opens the mixer. Research, the ink and
// paper tables, and every derived number: docs/light-ink-picker.md; the model
// itself is pure and host-tested in src/LightInkPalette.h.
//
// The UI is three controls, top to bottom:
//   * the INK LIST -- one row per historical ink: a swatch at the CURRENT
//     density, the name, and its era note;
//   * a DENSITY slider whose track is a LIVE gradient along the selected
//     ink's own dilution curve on the CURRENT paper (the mixer's
//     thick-gradient pattern, 16 pt). Its floor is wherever 7:1 would break
//     on that paper -- the slider physically cannot select an illegible wash
//     (the PhosphorGrain budget pattern, enforced in the core's clamp);
//   * SIX PAPER swatches in a row.
//
// Selection applies LIVE through the existing custom light fields
// (panelInkLight/panelPaperLight + preset Custom), so the whole downstream --
// letterpress, pad-on-paper, keyboard chips -- follows through
// crosspoint::panelForPrefs() with no new plumbing. Persistence is three
// append-only integer keys, with the applied result mirrored into the light
// hex fields -- the mixer's storage discipline. The custom DARK fields stay
// the mixer's; see applySelection for the one-time dark snapshot that keeps
// the dark page rendering the same tones when the shared preset integer first
// moves to Custom.
//
// Presentation discipline copied from the mixer, deliberately and completely:
// nav wrapper for the system Done, pageSheet pinned at the medium detent,
// modalInPresentation (pull-down is dead), undimmed so the page above the
// sheet stays the live preview, and NO setTitle: anywhere on the controller
// or its navigationItem -- objc_retain(0x1) inside UIKit's setTitle: was the
// build 110 device crash.

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <atomic>
#include <cstring>

#include "CrossPointPrefs.h"
#include "LightInkPalette.h"
#include "PanelPalette.h"
#include "PanelPrefs.h"
#include "SimulatorOverlay.h"

// C++ LINKAGE, deliberately -- defined in the firmware with no extern "C";
// declaring it C is the build 110 link death (see the mixer).
void crosspointRequestRender();

// --- persistence ------------------------------------------------------------
// The three picker keys are APPEND-ONLY integers (LightInkPalette.h's rule);
// the four hex keys are the same store the mixer and Settings.app write.
static NSString *const kInkIndexKey = @"lightInkIndex";
static NSString *const kInkDensityKey = @"lightInkDensityPercent";
static NSString *const kPaperIndexKey = @"lightPaperIndex";
static NSString *const kInkLight = @"panelInkLight";
static NSString *const kPaperLight = @"panelPaperLight";
static NSString *const kInkDark = @"panelInkDark";
static NSString *const kPaperDark = @"panelPaperDark";

namespace {

constexpr int kGradientSamples = 16;  // same argument as the mixer's tracks

NSString *hexOf(const uint8_t c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
}

UIColor *colorOf(const uint8_t c[3]) {
  return [UIColor colorWithRed:c[0] / 255.0
                         green:c[1] / 255.0
                          blue:c[2] / 255.0
                         alpha:1];
}

// Stored selection, clamped through the core so a restored backup from a
// future build lands on the shipped rows rather than out of bounds. Density's
// missing-key trap is the malignant -integerForKey: one: absent answers 0,
// and 0 here would clamp to the floor -- a wash nobody chose. Absent means
// "never touched", which is full strength.
void loadSelection(int *ink, int *paper, int *density) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  *ink = lightink::clampInkIndex((int)[d integerForKey:kInkIndexKey]);
  *paper = lightink::clampPaperIndex((int)[d integerForKey:kPaperIndexKey]);
  id storedDensity = [d objectForKey:kInkDensityKey];
  const int raw = storedDensity ? (int)[d integerForKey:kInkDensityKey]
                                : lightink::kDensityMax;
  *density = lightink::clampDensityPct(*ink, *paper, raw);
}

// Apply the selection: persist the three integers, mirror the computed pair
// into the light hex fields, and point the preset at Custom. renderPage on
// the same terms as the mixer's applyGuns -- the hex fields plus
// requestPresent() are the cheap live half (recolor the cached framebuffer);
// the firmware re-dither rides only on settled changes, never on a drag tick.
void applySelection(int ink, int paper, int density, bool renderPage) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setInteger:ink forKey:kInkIndexKey];
  [d setInteger:paper forKey:kPaperIndexKey];
  [d setInteger:density forKey:kInkDensityKey];

  // THE DARK SNAPSHOT, once, before the preset first moves to Custom. The
  // preset integer is shared by both appearances, so flipping it to Custom
  // for the light page would otherwise yank a named dark preset (the shipped
  // White CRT) off the dark page and hand dark whatever the custom dark
  // fields held. Resolving the CURRENT dark pair first and writing it into
  // those fields keeps the dark page rendering the same tones. When the
  // preset is already Custom the dark fields are the mixer's and are not
  // touched -- dark mode's stored state stays the mixer's.
  if (CrossPointPrefs_panelPalettePreset() != panelpalette::kPresetCustom) {
    const panelpalette::Palette darkNow = crosspoint::panelForPrefs(true);
    [d setObject:hexOf(darkNow.ink) forKey:kInkDark];
    [d setObject:hexOf(darkNow.paper) forKey:kPaperDark];
    SDL_Log("[inkpicker] dark snapshot %s on %s (preset was %d)",
            hexOf(darkNow.ink).UTF8String, hexOf(darkNow.paper).UTF8String,
            CrossPointPrefs_panelPalettePreset());
  }

  uint8_t wash[3];
  lightink::inkAtDensity(ink, paper, density, wash);
  [d setObject:hexOf(wash) forKey:kInkLight];
  [d setObject:hexOf(lightink::kPapers[lightink::clampPaperIndex(paper)].tone)
        forKey:kPaperLight];
  CrossPointPrefs_setPanelPalettePreset(panelpalette::kPresetCustom);
  SimulatorOverlay::requestPresent();
  if (renderPage) crosspointRequestRender();
}

}  // namespace

// The sheet's live presentation state, for the input layers underneath --
// same contract as CrossPointMixer_isPresented, and checked alongside it at
// every gate (the shim's finger paths and the zen recognizers).
static std::atomic<bool> g_pickerPresented{false};

extern "C" bool CrossPointInkPicker_isPresented(void) {
  return g_pickerPresented.load();
}

@interface CPXLightInkPickerController : UIViewController
@end

@implementation CPXLightInkPickerController {
  UIButton *_inkRow[lightink::kInkCount];
  UIView *_inkSwatch[lightink::kInkCount];
  UILabel *_inkName[lightink::kInkCount];
  UILabel *_inkEra[lightink::kInkCount];
  UILabel *_densityLabel;
  UILabel *_densityValue;
  UISlider *_slider;
  UIImageView *_track;  // the live gradient track, the mixer's pattern
  UIButton *_paperRow[lightink::kPaperCount];
  UILabel *_readout;
  int _ink;
  int _paper;
  int _density;
  CGFloat _trackWidth;
  dispatch_block_t _pendingSettle;  // the coalesced deferred firmware render
}

- (void)viewDidLoad {
  [super viewDidLoad];
  SDL_Log("[inkpicker] viewDidLoad");
  self.view.backgroundColor = UIColor.systemBackgroundColor;
  self.navigationItem.rightBarButtonItem = [[UIBarButtonItem alloc]
      initWithBarButtonSystemItem:UIBarButtonSystemItemDone
                           target:self
                           action:@selector(dismissSelf)];

  loadSelection(&_ink, &_paper, &_density);

  UIFont *name = [UIFont monospacedSystemFontOfSize:13 weight:UIFontWeightSemibold];
  UIFont *small = [UIFont monospacedSystemFontOfSize:10 weight:UIFontWeightRegular];

  for (int i = 0; i < lightink::kInkCount; i++) {
    // A custom button with label/swatch SUBVIEWS rather than a titled system
    // button: contentEdgeInsets and friends are deprecated under
    // UIButtonConfiguration, and a configuration is more machinery than three
    // frames.
    _inkRow[i] = [UIButton buttonWithType:UIButtonTypeCustom];
    _inkRow[i].tag = i;
    _inkRow[i].layer.cornerRadius = 6;
    [_inkRow[i] addTarget:self
                   action:@selector(inkTapped:)
         forControlEvents:UIControlEventTouchUpInside];
    [self.view addSubview:_inkRow[i]];

    _inkSwatch[i] = [UIView new];
    _inkSwatch[i].userInteractionEnabled = NO;
    _inkSwatch[i].layer.cornerRadius = 4;
    _inkSwatch[i].layer.borderWidth = 1;
    _inkSwatch[i].layer.borderColor = UIColor.separatorColor.CGColor;
    [_inkRow[i] addSubview:_inkSwatch[i]];

    _inkName[i] = [UILabel new];
    _inkName[i].font = name;
    _inkName[i].textColor = UIColor.labelColor;
    _inkName[i].userInteractionEnabled = NO;
    _inkName[i].text = @(lightink::kInks[i].name);
    [_inkRow[i] addSubview:_inkName[i]];

    _inkEra[i] = [UILabel new];
    _inkEra[i].font = small;
    _inkEra[i].textColor = UIColor.secondaryLabelColor;
    _inkEra[i].textAlignment = NSTextAlignmentRight;
    _inkEra[i].text = @(lightink::kInks[i].era);
    _inkEra[i].adjustsFontSizeToFitWidth = YES;
    _inkEra[i].minimumScaleFactor = 0.7;
    [self.view addSubview:_inkEra[i]];
  }

  _densityLabel = [UILabel new];
  _densityLabel.font = name;
  _densityLabel.text = @"Density";
  _densityLabel.textColor = UIColor.labelColor;
  [self.view addSubview:_densityLabel];

  _densityValue = [UILabel new];
  _densityValue.font = small;
  _densityValue.textColor = UIColor.secondaryLabelColor;
  _densityValue.textAlignment = NSTextAlignmentRight;
  [self.view addSubview:_densityValue];

  _track = [UIImageView new];
  _track.userInteractionEnabled = NO;
  _track.clipsToBounds = YES;
  [self.view addSubview:_track];

  _slider = [UISlider new];
  _slider.minimumValue = lightink::floorDensityPct(_ink, _paper);
  _slider.maximumValue = lightink::kDensityMax;
  _slider.value = _density;
  // Transparent system track, both halves: the gradient underlay IS the track
  // (a track IMAGE compresses as the thumb moves -- see the mixer).
  static UIImage *clearTrack;
  static dispatch_once_t clearOnce;
  dispatch_once(&clearOnce, ^{
    UIGraphicsImageRenderer *r =
        [[UIGraphicsImageRenderer alloc] initWithSize:CGSizeMake(1, 1)];
    clearTrack = [r imageWithActions:^(UIGraphicsImageRendererContext *c){}];
  });
  [_slider setMinimumTrackImage:clearTrack forState:UIControlStateNormal];
  [_slider setMaximumTrackImage:clearTrack forState:UIControlStateNormal];
  [_slider addTarget:self
                action:@selector(densityMoved:)
      forControlEvents:UIControlEventValueChanged];
  [_slider addTarget:self
                action:@selector(densityDropped:)
      forControlEvents:UIControlEventTouchUpInside |
                       UIControlEventTouchUpOutside | UIControlEventTouchCancel];
  [self.view addSubview:_slider];

  for (int p = 0; p < lightink::kPaperCount; p++) {
    _paperRow[p] = [UIButton buttonWithType:UIButtonTypeCustom];
    _paperRow[p].tag = p;
    _paperRow[p].backgroundColor = colorOf(lightink::kPapers[p].tone);
    _paperRow[p].layer.cornerRadius = 6;
    _paperRow[p].titleLabel.font =
        [UIFont monospacedSystemFontOfSize:8 weight:UIFontWeightMedium];
    [_paperRow[p] setTitle:@(lightink::kPapers[p].name)
                  forState:UIControlStateNormal];
    // A fixed dark title reads on all six stocks -- every paper clears 7:1
    // against every full-strength ink, let alone this near-black.
    [_paperRow[p] setTitleColor:[UIColor colorWithWhite:0.15 alpha:1]
                       forState:UIControlStateNormal];
    _paperRow[p].titleLabel.adjustsFontSizeToFitWidth = YES;
    _paperRow[p].titleLabel.minimumScaleFactor = 0.6;
    [_paperRow[p] addTarget:self
                     action:@selector(paperTapped:)
           forControlEvents:UIControlEventTouchUpInside];
    [self.view addSubview:_paperRow[p]];
  }

  _readout = [UILabel new];
  _readout.font = small;
  _readout.textColor = UIColor.secondaryLabelColor;
  _readout.numberOfLines = 1;
  _readout.adjustsFontSizeToFitWidth = YES;
  _readout.minimumScaleFactor = 0.7;
  [self.view addSubview:_readout];

  [self refresh];
  SDL_Log("[inkpicker] controller ready (ink %d, paper %d, density %d)", _ink,
          _paper, _density);
}

- (void)viewDidLayoutSubviews {
  [super viewDidLayoutSubviews];
  const CGFloat margin = 20;
  const CGFloat W = self.view.bounds.size.width;
  CGFloat y = self.view.safeAreaInsets.top + 8;
  const CGFloat rowH = 27;
  for (int i = 0; i < lightink::kInkCount; i++) {
    _inkRow[i].frame = CGRectMake(margin - 8, y, W - 2 * margin + 16, rowH);
    _inkSwatch[i].frame = CGRectMake(8, (rowH - 16) / 2, 26, 16);
    _inkName[i].frame = CGRectMake(42, 0, W / 2 - 42, rowH);
    _inkEra[i].frame = CGRectMake(W / 2, y + (rowH - 14) / 2, W / 2 - margin, 14);
    y += rowH;
  }
  y += 8;
  _densityLabel.frame = CGRectMake(margin, y, 120, 18);
  _densityValue.frame = CGRectMake(W - margin - 120, y, 120, 18);
  _slider.frame = CGRectMake(margin, y + 18, W - 2 * margin, 32);
  // The thick gradient bar, centered on the slider's own track centerline --
  // the mixer's 16 pt pattern verbatim.
  constexpr CGFloat kTrackBarPt = 16.0f;
  const CGRect tr = [_slider trackRectForBounds:_slider.bounds];
  CGRect bar = [_slider convertRect:tr toView:self.view];
  bar.origin.y += (bar.size.height - kTrackBarPt) / 2;
  bar.size.height = kTrackBarPt;
  _track.frame = bar;
  _track.layer.cornerRadius = kTrackBarPt / 2;
  y += 54;
  const CGFloat gap = 6;
  const CGFloat cell =
      (W - 2 * margin - gap * (lightink::kPaperCount - 1)) / lightink::kPaperCount;
  for (int p = 0; p < lightink::kPaperCount; p++) {
    _paperRow[p].frame = CGRectMake(margin + p * (cell + gap), y, cell, 40);
  }
  y += 48;
  _readout.frame = CGRectMake(margin, y, W - 2 * margin, 16);
  if (_track.bounds.size.width != _trackWidth) {
    _trackWidth = _track.bounds.size.width;
    [self rebuildTrackGradient];
  }
}

// The live gradient: the selected ink's own dilution curve on the CURRENT
// paper, sampled from the slider's floor to full strength -- so the track
// shows exactly the washes the thumb can reach, and nothing it cannot.
- (void)rebuildTrackGradient {
  const CGSize size = _track.bounds.size;
  if (size.width < 1 || size.height < 1) return;
  const int floorPct = (int)_slider.minimumValue;
  CGFloat comps[kGradientSamples * 4];
  CGFloat locs[kGradientSamples];
  for (int s = 0; s < kGradientSamples; s++) {
    const float t = (float)s / (kGradientSamples - 1);
    const int pct =
        floorPct + (int)lroundf(t * (lightink::kDensityMax - floorPct));
    uint8_t wash[3];
    lightink::inkAtDensity(_ink, _paper, pct, wash);
    comps[s * 4 + 0] = wash[0] / 255.0;
    comps[s * 4 + 1] = wash[1] / 255.0;
    comps[s * 4 + 2] = wash[2] / 255.0;
    comps[s * 4 + 3] = 1.0;
    locs[s] = t;
  }
  CGColorSpaceRef space = CGColorSpaceCreateWithName(kCGColorSpaceSRGB);
  CGGradientRef grad =
      CGGradientCreateWithColorComponents(space, comps, locs, kGradientSamples);
  CGColorSpaceRelease(space);
  UIGraphicsImageRenderer *ren =
      [[UIGraphicsImageRenderer alloc] initWithSize:size];
  _track.image = [ren imageWithActions:^(UIGraphicsImageRendererContext *ctx) {
    CGContextDrawLinearGradient(ctx.CGContext, grad,
                                CGPointMake(0, size.height / 2),
                                CGPointMake(size.width, size.height / 2), 0);
  }];
  CGGradientRelease(grad);
}

// Re-clamp the density for the current ink+paper (the floor moves with both),
// refresh every swatch, the slider's floor, the gradient and the readout.
- (void)refresh {
  const int floorPct = lightink::floorDensityPct(_ink, _paper);
  _density = lightink::clampDensityPct(_ink, _paper, _density);
  _slider.minimumValue = floorPct;
  if ((int)lroundf(_slider.value) != _density) _slider.value = _density;

  for (int i = 0; i < lightink::kInkCount; i++) {
    uint8_t wash[3];
    lightink::inkAtDensity(i, _paper,
                           lightink::clampDensityPct(i, _paper, _density),
                           wash);
    _inkSwatch[i].backgroundColor = colorOf(wash);
    _inkRow[i].backgroundColor =
        i == _ink ? UIColor.tertiarySystemFillColor : UIColor.clearColor;
  }
  for (int p = 0; p < lightink::kPaperCount; p++) {
    _paperRow[p].layer.borderWidth = p == _paper ? 2 : 1;
    _paperRow[p].layer.borderColor = p == _paper
                                         ? UIColor.labelColor.CGColor
                                         : UIColor.separatorColor.CGColor;
  }
  uint8_t wash[3];
  lightink::inkAtDensity(_ink, _paper, _density, wash);
  _densityValue.text =
      [NSString stringWithFormat:@"%d%% (floor %d%%)", _density, floorPct];
  _readout.text = [NSString
      stringWithFormat:@"%s %d%% on %s — %.1f:1 · %@ on %@",
                       lightink::kInks[_ink].name, _density,
                       lightink::kPapers[_paper].name,
                       lightink::contrastAtDensity(_ink, _paper, _density),
                       hexOf(wash),
                       hexOf(lightink::kPapers[_paper].tone)];
  [self rebuildTrackGradient];
}

- (void)inkTapped:(UIButton *)b {
  _ink = (int)b.tag;
  _density = lightink::clampDensityPct(_ink, _paper, _density);
  applySelection(_ink, _paper, _density, /*renderPage=*/false);
  [self refresh];
  [self scheduleSettle];
}

- (void)paperTapped:(UIButton *)b {
  _paper = (int)b.tag;
  _density = lightink::clampDensityPct(_ink, _paper, _density);
  applySelection(_ink, _paper, _density, /*renderPage=*/false);
  [self refresh];
  [self scheduleSettle];
}

- (void)densityMoved:(UISlider *)s {
  [self cancelPendingSettle];
  _density = lightink::clampDensityPct(_ink, _paper, (int)lroundf(s.value));
  applySelection(_ink, _paper, _density, /*renderPage=*/false);
  [self refresh];
}

- (void)densityDropped:(UISlider *)s {
  [self cancelPendingSettle];
  applySelection(_ink, _paper, _density, /*renderPage=*/true);
}

// The deferred, COALESCED firmware re-render -- the mixer's settle, same
// 0.35 s, same reason: a re-dither costs hundreds of ms and must not ride a
// fast series of picks or a drag tick.
- (void)scheduleSettle {
  [self cancelPendingSettle];
  _pendingSettle = dispatch_block_create((dispatch_block_flags_t)0, ^{
    crosspointRequestRender();
  });
  dispatch_after(
      dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.35 * NSEC_PER_SEC)),
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

// Disappearing means DISMISSED (Done is the only exit; modalInPresentation
// pins pull-down). Cleared here so any dismissal path UIKit ever grows also
// clears the flag -- the mixer's shape.
- (void)viewDidDisappear:(BOOL)animated {
  [super viewDidDisappear:animated];
  g_pickerPresented.store(false);
}

@end

// Headless test hook: drive the EXACT function the controls call, so a
// scripted run exercises the same write path a finger does -- including the
// one-time dark snapshot. Same family as CrossPointMixer_applyGunsForTest;
// driven by CROSSPOINT_SIM_APPLY_INK="ink,paper,density" in the shim.
extern "C" void CrossPointInkPicker_applyForTest(int ink, int paper,
                                                 int density) {
  ink = lightink::clampInkIndex(ink);
  paper = lightink::clampPaperIndex(paper);
  density = lightink::clampDensityPct(ink, paper, density);
  applySelection(ink, paper, density, /*renderPage=*/true);
  uint8_t wash[3];
  lightink::inkAtDensity(ink, paper, density, wash);
  SDL_Log("[inkpicker] test hook applied %s %d%% on %s -> %s on %s",
          lightink::kInks[ink].name, density, lightink::kPapers[paper].name,
          hexOf(wash).UTF8String,
          hexOf(lightink::kPapers[paper].tone).UTF8String);
}

// --- entry point ------------------------------------------------------------

extern "C" void CrossPointInkPicker_present(void) {
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
    CPXLightInkPickerController *picker = [CPXLightInkPickerController new];
    // Standard Done lives in a nav bar, so the sheet is a nav controller. No
    // title string is ever set on it -- the build 110 crash note.
    UINavigationController *nav =
        [[UINavigationController alloc] initWithRootViewController:picker];
    nav.modalPresentationStyle = UIModalPresentationPageSheet;
    nav.modalInPresentation = YES;
    if (nav.sheetPresentationController) {
      nav.sheetPresentationController.detents =
          @[ UISheetPresentationControllerDetent.mediumDetent ];
      nav.sheetPresentationController.prefersGrabberVisible = NO;
      // Undimmed at medium: the page above the sheet IS the preview.
      nav.sheetPresentationController.largestUndimmedDetentIdentifier =
          UISheetPresentationControllerDetentIdentifierMedium;
    }
    g_pickerPresented.store(true);
    [root presentViewController:nav animated:YES completion:nil];
  });
}
