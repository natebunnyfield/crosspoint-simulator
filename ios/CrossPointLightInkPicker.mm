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
//   * SIX PAPER swatches in a row;
//   * a PAPER slider, the density's twin (owner order 2026-08-22: "paper
//     needs a 0-100 slider too"). Same 16 pt live gradient, showing the stock
//     from the neutral bright-white ground to full strength. Its CEILING is
//     wherever 7:1 would break at the current ink and density.
//
// THE FLOOR IS A SURFACE NOW, and the rule the UI implements is one sentence:
// THE SLIDER YOU ARE MOVING IS THE ONE THAT STOPS, THE OTHER HOLDS. Density
// stops at a floor, paper strength at a ceiling, each computed at the other's
// live value. Tapping an ink or a paper STOCK is not a slider move, so it
// re-clamps the density and leaves the sheet alone -- the paper you chose is
// the paper you keep, and the ink gets darker to pay for it. Derivation and
// the swept grid: docs/light-ink-picker.md.
//
// The paper dial also carries the sheet's TEXTURE. Each stock has a tooth
// factor (lightink::toothScaleFor) and the strength scales it, so dialing a
// chamois up brings its roughness up with its tone; the number is pushed to
// SimulatorOverlay::setPaperTooth and lands on the letterpress sheet pass.
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
#include <functional>
#include <vector>

#include "CrossPointPrefs.h"
#include "Letterpress.h"
#include "LightInkPalette.h"
#include "PaperDefects.h"
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
static NSString *const kPaperStrengthKey = @"lightPaperStrengthPercent";
// THE PAPER INSTRUMENT's own keys (owner order 2026-08-22: "make tooth,
// formation, pressure and all other paper variables sliders in the 'color
// button' drawer"). Append-only integers like the four above, and every one
// defaults to the value that reproduces exactly what the app already drew --
// so an install that never opens the Paper or Press group is unchanged.
//
// paperDefectsPercent is NOT here: it is ALSO a Settings.bundle row, so it goes
// through CrossPointPrefs like every other bundle-backed key. One key, two
// views onto it -- a Settings.bundle row is a view onto NSUserDefaults, which
// is what makes that one source of truth rather than two.
static NSString *const kPaperToothKey = @"paperToothPercent";
static NSString *const kPaperFormationKey = @"paperFormationPercent";
static NSString *const kPressRingKey = @"pressRingPercent";
static NSString *const kPressDebossKey = @"pressDebossPercent";
static NSString *const kPressPressureKey = @"pressPressurePercent";
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
// future build lands on the shipped rows rather than out of bounds. The
// missing-key trap on both percentages is the malignant -integerForKey: one:
// absent answers 0, and 0 here is a real value nobody chose -- a floor-clamped
// wash, or a sheet with no tint at all. Absent means "never touched", which is
// full strength on both dials.
//
// The two clamps run in the order the invariant needs: the paper strength is
// pinned to its ceiling for the STORED density first, then the density to its
// floor at the resulting strength. Either alone can be out of range in a
// restored backup, and doing it this way lands on a legal pair from any pair
// of integers whatsoever.
void loadSelection(int *ink, int *paper, int *density, int *paperStrength) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  *ink = lightink::clampInkIndex((int)[d integerForKey:kInkIndexKey]);
  *paper = lightink::clampPaperIndex((int)[d integerForKey:kPaperIndexKey]);
  id storedDensity = [d objectForKey:kInkDensityKey];
  const int rawDensity = storedDensity ? (int)[d integerForKey:kInkDensityKey]
                                       : lightink::kDensityMax;
  id storedStrength = [d objectForKey:kPaperStrengthKey];
  const int rawStrength = storedStrength
                              ? (int)[d integerForKey:kPaperStrengthKey]
                              : lightink::kPaperStrengthDefault;
  *paperStrength = lightink::clampPaperStrengthPct(*ink, *paper, rawDensity,
                                                   rawStrength);
  *density =
      lightink::clampDensityPct(*ink, *paper, rawDensity, *paperStrength);
}

// --- the paper instrument's six dials ---------------------------------------
//
// Read through -objectForKey: rather than -integerForKey:, all of them, because
// 0 is a REAL value for every one -- a perfectly even sheet, a fresh sheet, a
// press component switched off -- and -integerForKey: cannot tell "0" from
// "never chosen". Absent means the shipped value, which is what the app already
// drew.
constexpr int kPartPercentMax =
    (int)(letterpress::kPartScaleMax * 100.0f + 0.5f);

int storedIntOr(NSString *key, int fallback) {
  NSNumber *v = [[NSUserDefaults standardUserDefaults] objectForKey:key];
  if (![v isKindOfClass:[NSNumber class]]) return fallback;
  return v.intValue;
}

int clampPct(int v, int lo, int hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

int storedToothPct(void) { return clampPct(storedIntOr(kPaperToothKey, 100), 0, 400); }
int storedFormationPct(void) {
  return clampPct(storedIntOr(kPaperFormationKey,
                              (int)(letterpress::kFormationDepthDefault * 100.0f +
                                    0.5f)),
                  0, (int)(letterpress::kFormationDepthMax * 100.0f + 0.5f));
}
int storedRingPct(void) { return clampPct(storedIntOr(kPressRingKey, 100), 0, kPartPercentMax); }
int storedDebossPct(void) { return clampPct(storedIntOr(kPressDebossKey, 100), 0, kPartPercentMax); }
int storedPressurePct(void) { return clampPct(storedIntOr(kPressPressureKey, 100), 0, kPartPercentMax); }
int storedDefectsPct(void) {
  return clampPct(CrossPointPrefs_paperDefectsPercent(), paperdefects::kDialOff,
                  paperdefects::kDialMax);
}

// The sheet's roughness for this selection, as the percent SimulatorOverlay
// carries: the STOCK's own factor times the owner's Tooth dial. Two inputs, one
// number -- a stock still reads as itself and the dial is a multiplier on it,
// which is why the drawer's Tooth slider is not simply the paper strength over
// again.
int paperToothPercentFor(int paper, int paperStrength) {
  const float stock = lightink::toothScaleFor(paper, paperStrength);
  return (int)lroundf(stock * (float)storedToothPct());
}

// Push every paper dial at the SDL side. Called on any change and by the shim's
// launch seed, because the drawer may never be opened and the stored sheet
// still has a texture.
void pushPaperDials(int paper, int paperStrength) {
  SDL_Log("[letterpress] paper: tooth %d%% (stock %.2fx x dial %d%%), "
          "formation %d%%, defects %d%% | press: ring %d%% deboss %d%% "
          "pressure %d%%",
          paperToothPercentFor(paper, paperStrength),
          (double)lightink::toothScaleFor(paper, paperStrength),
          storedToothPct(), storedFormationPct(), storedDefectsPct(),
          storedRingPct(), storedDebossPct(), storedPressurePct());
  SimulatorOverlay::setPaperTooth(paperToothPercentFor(paper, paperStrength));
  SimulatorOverlay::setPaperFormation(storedFormationPct());
  SimulatorOverlay::setPaperDefects(storedDefectsPct());
  SimulatorOverlay::setPressRing(storedRingPct());
  SimulatorOverlay::setPressDeboss(storedDebossPct());
  SimulatorOverlay::setPressPressure(storedPressurePct());
}

// --- the preview strips ------------------------------------------------------
//
// A track GRADIENT is meaningless for a texture: what a tooth or a formation or
// a press does is not a colour ramp. So those sliders get a SWATCH STRIP -- the
// model itself, evaluated left to right across the dial's range on the current
// paper -- which is the honest analog of the ink slider's gradient.
using ShadeFn = std::function<void(int x, int y, int w, int h, uint8_t rgb[3])>;

UIImage *renderStrip(CGSize sizePt, CGFloat scale, const ShadeFn &shade) {
  const int w = (int)(sizePt.width * scale);
  const int h = (int)(sizePt.height * scale);
  if (w < 1 || h < 1) return nil;
  std::vector<uint8_t> buf((size_t)w * h * 4, 255);
  for (int y = 0; y < h; y++)
    for (int x = 0; x < w; x++) {
      uint8_t rgb[3] = {255, 255, 255};
      shade(x, y, w, h, rgb);
      uint8_t *px = buf.data() + ((size_t)y * w + x) * 4;
      px[0] = rgb[0];
      px[1] = rgb[1];
      px[2] = rgb[2];
      px[3] = 255;
    }
  CGColorSpaceRef space = CGColorSpaceCreateWithName(kCGColorSpaceSRGB);
  CGContextRef ctx = CGBitmapContextCreate(
      buf.data(), w, h, 8, (size_t)w * 4, space,
      kCGImageAlphaNoneSkipLast | kCGBitmapByteOrder32Big);
  CGColorSpaceRelease(space);
  if (!ctx) return nil;
  CGImageRef img = CGBitmapContextCreateImage(ctx);
  CGContextRelease(ctx);
  if (!img) return nil;
  UIImage *ui = [UIImage imageWithCGImage:img
                                    scale:scale
                              orientation:UIImageOrientationUp];
  CGImageRelease(img);
  return ui;
}

// Apply the selection: persist the three integers, mirror the computed pair
// into the light hex fields, and point the preset at Custom. renderPage on
// the same terms as the mixer's applyGuns -- the hex fields plus
// requestPresent() are the cheap live half (recolor the cached framebuffer);
// the firmware re-dither rides only on settled changes, never on a drag tick.
void applySelection(int ink, int paper, int density, int paperStrength,
                    bool renderPage) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setInteger:ink forKey:kInkIndexKey];
  [d setInteger:paper forKey:kPaperIndexKey];
  [d setInteger:density forKey:kInkDensityKey];
  [d setInteger:paperStrength forKey:kPaperStrengthKey];

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

  uint8_t wash[3], ground[3];
  lightink::inkAtDensity(ink, paper, density, wash, paperStrength);
  lightink::paperAtStrength(paper, paperStrength, ground);
  [d setObject:hexOf(wash) forKey:kInkLight];
  [d setObject:hexOf(ground) forKey:kPaperLight];
  CrossPointPrefs_setPanelPalettePreset(panelpalette::kPresetCustom);
  // The sheet's texture follows its tone: a stock dialed up is rougher as
  // well as warmer. Pushed here rather than only polled, so a drag shows the
  // grain change on the same frame the color changes.
  pushPaperDials(paper, paperStrength);
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
  UILabel *_paperLabel;
  UILabel *_paperValue;
  UISlider *_paperSlider;
  UIImageView *_paperTrack;
  UILabel *_readout;
  // THE SCROLL VIEW. Six more sliders do not fit a medium detent, and the
  // opening size stays medium by owner-facing continuity -- so the sheet
  // scrolls and gains a LARGE detent beside it. Manual frames stay; they are
  // frames inside this view's content now, which is a smaller change than
  // adopting Auto Layout mid-flight.
  UIScrollView *_scroll;
  UILabel *_groupInk;
  UILabel *_groupPaper;
  UILabel *_groupPress;
  // ONE SUB-HEADING PER INK FAMILY. The table passed a dozen rows on
  // 2026-08-22 and an undifferentiated list of eighteen inks is a wall in the
  // same way nine unlabeled sliders were. The families and the order they
  // appear in are the MODEL's (lightink::kInkGroupNames,
  // lightink::buildInkDisplayOrder), not this file's -- appending a row must
  // not require editing a layout list. A family's heading is drawn once, above
  // its first row.
  UILabel *_inkFamily[lightink::kInkGroupCount];
  // The picker's display order, filled once from the model. Slot -> ink index.
  // NOT a stored preference: the persisted value is still the ink's table
  // index, which this permutation never touches.
  int _inkOrder[lightink::kInkCount];
  // The paper instrument's six. Each is label + value + slider + a preview
  // STRIP (the model itself across the dial's range) rather than a gradient:
  // a colour ramp cannot show what a tooth does.
  UILabel *_toothLabel, *_toothValue;
  UISlider *_toothSlider;
  UIImageView *_toothStrip;
  UILabel *_formationLabel, *_formationValue;
  UISlider *_formationSlider;
  UIImageView *_formationStrip;
  UILabel *_defectsLabel, *_defectsValue;
  UISlider *_defectsSlider;
  UIImageView *_defectsStrip;
  UILabel *_ringLabel, *_ringValue;
  UISlider *_ringSlider;
  UIImageView *_ringStrip;
  UILabel *_debossLabel, *_debossValue;
  UISlider *_debossSlider;
  UIImageView *_debossStrip;
  UILabel *_pressureLabel, *_pressureValue;
  UISlider *_pressureSlider;
  UIImageView *_pressureStrip;
  CGFloat _stripWidth;
  int _ink;
  int _paper;
  int _density;
  int _paperStrength;
  CGFloat _trackWidth;
  CGFloat _paperTrackWidth;
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

  _scroll = [UIScrollView new];
  _scroll.alwaysBounceVertical = YES;
  _scroll.showsVerticalScrollIndicator = YES;
  [self.view addSubview:_scroll];

  loadSelection(&_ink, &_paper, &_density, &_paperStrength);

  UIFont *name = [UIFont monospacedSystemFontOfSize:13 weight:UIFontWeightSemibold];
  UIFont *small = [UIFont monospacedSystemFontOfSize:10 weight:UIFontWeightRegular];

  UIFont *group = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightBold];
  // THREE LABELED GROUPS -- Ink / Paper / Press. With nine controls on one
  // sheet an unlabeled list is a wall; the grouping is also the model's own
  // division (what the ink is, what the sheet is, what the press did to them).
  auto makeGroup = [&](NSString *title) {
    UILabel *l = [UILabel new];
    l.font = group;
    l.text = title;
    l.textColor = UIColor.secondaryLabelColor;
    [self->_scroll addSubview:l];
    return l;
  };
  _groupInk = makeGroup(@"INK");
  _groupPaper = makeGroup(@"PAPER");
  _groupPress = makeGroup(@"PRESS");
  lightink::buildInkDisplayOrder(_inkOrder);
  for (int g = 0; g < lightink::kInkGroupCount; g++) {
    _inkFamily[g] = makeGroup(@(lightink::kInkGroupNames[g]));
    _inkFamily[g].font =
        [UIFont monospacedSystemFontOfSize:9 weight:UIFontWeightSemibold];
    _inkFamily[g].textColor = UIColor.tertiaryLabelColor;
  }

  for (int i = 0; i < lightink::kInkCount; i++) {
    // A custom button with label/swatch SUBVIEWS rather than a titled system
    // button: contentEdgeInsets and friends are deprecated under
    // UIButtonConfiguration, and a configuration is more machinery than three
    // frames.
    _inkRow[i] = [UIButton buttonWithType:UIButtonTypeCustom];
    _inkRow[i].tag = i;
    _inkRow[i].layer.cornerRadius = 6;
    _inkRow[i].accessibilityLabel = @(lightink::kInks[i].name);
    _inkRow[i].accessibilityTraits = UIAccessibilityTraitButton;
    [_inkRow[i] addTarget:self
                   action:@selector(inkTapped:)
         forControlEvents:UIControlEventTouchUpInside];
    [_scroll addSubview:_inkRow[i]];

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
    [_scroll addSubview:_inkEra[i]];
  }

  _densityLabel = [UILabel new];
  _densityLabel.font = name;
  _densityLabel.text = @"Density";
  _densityLabel.textColor = UIColor.labelColor;
  [_scroll addSubview:_densityLabel];

  _densityValue = [UILabel new];
  _densityValue.font = small;
  _densityValue.textColor = UIColor.secondaryLabelColor;
  _densityValue.textAlignment = NSTextAlignmentRight;
  [_scroll addSubview:_densityValue];

  _track = [UIImageView new];
  _track.userInteractionEnabled = NO;
  _track.clipsToBounds = YES;
  _track.isAccessibilityElement = NO;
  [_scroll addSubview:_track];

  // Transparent system track, both halves, for BOTH sliders: the gradient
  // underlay IS the track (a track IMAGE compresses as the thumb moves -- see
  // the mixer). Built once and shared.
  static UIImage *clearTrack;
  static dispatch_once_t clearOnce;
  dispatch_once(&clearOnce, ^{
    UIGraphicsImageRenderer *r =
        [[UIGraphicsImageRenderer alloc] initWithSize:CGSizeMake(1, 1)];
    clearTrack = [r imageWithActions:^(UIGraphicsImageRendererContext *c){}];
  });

  _slider = [UISlider new];
  _slider.minimumValue =
      lightink::floorDensityPct(_ink, _paper, _paperStrength);
  _slider.maximumValue = lightink::kDensityMax;
  _slider.value = _density;
  _slider.accessibilityLabel = @"Density";
  [_slider setMinimumTrackImage:clearTrack forState:UIControlStateNormal];
  [_slider setMaximumTrackImage:clearTrack forState:UIControlStateNormal];
  [_slider addTarget:self
                action:@selector(densityMoved:)
      forControlEvents:UIControlEventValueChanged];
  [_slider addTarget:self
                action:@selector(densityDropped:)
      forControlEvents:UIControlEventTouchUpInside |
                       UIControlEventTouchUpOutside | UIControlEventTouchCancel];
  [_scroll addSubview:_slider];

  for (int p = 0; p < lightink::kPaperCount; p++) {
    _paperRow[p] = [UIButton buttonWithType:UIButtonTypeCustom];
    _paperRow[p].tag = p;
    _paperRow[p].backgroundColor = colorOf(lightink::kPapers[p].tone);
    _paperRow[p].layer.cornerRadius = 6;
    _paperRow[p].accessibilityLabel = @(lightink::kPapers[p].name);
    _paperRow[p].accessibilityTraits = UIAccessibilityTraitButton;
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
    [_scroll addSubview:_paperRow[p]];
  }

  _paperLabel = [UILabel new];
  _paperLabel.font = name;
  _paperLabel.text = @"Paper";
  _paperLabel.textColor = UIColor.labelColor;
  [_scroll addSubview:_paperLabel];

  _paperValue = [UILabel new];
  _paperValue.font = small;
  _paperValue.textColor = UIColor.secondaryLabelColor;
  _paperValue.textAlignment = NSTextAlignmentRight;
  [_scroll addSubview:_paperValue];

  _paperTrack = [UIImageView new];
  _paperTrack.userInteractionEnabled = NO;
  _paperTrack.clipsToBounds = YES;
  _paperTrack.isAccessibilityElement = NO;
  [_scroll addSubview:_paperTrack];

  // The paper dial runs 0..100 with a CEILING rather than a floor: 0 is the
  // neutral ground and is always legal, and it is the top of the dial that
  // 7:1 takes away. maximumValue therefore moves, where the ink slider's
  // minimumValue does.
  _paperSlider = [UISlider new];
  _paperSlider.minimumValue = 0;
  _paperSlider.maximumValue =
      lightink::maxPaperStrengthPct(_ink, _paper, _density);
  _paperSlider.value = _paperStrength;
  _paperSlider.accessibilityLabel = @"Paper";
  [_paperSlider setMinimumTrackImage:clearTrack forState:UIControlStateNormal];
  [_paperSlider setMaximumTrackImage:clearTrack forState:UIControlStateNormal];
  [_paperSlider addTarget:self
                   action:@selector(paperStrengthMoved:)
         forControlEvents:UIControlEventValueChanged];
  [_paperSlider addTarget:self
                   action:@selector(paperStrengthDropped:)
         forControlEvents:UIControlEventTouchUpInside |
                          UIControlEventTouchUpOutside |
                          UIControlEventTouchCancel];
  [_scroll addSubview:_paperSlider];

  // The paper instrument's six. Same shape each: label, value, slider over a
  // preview strip, live-apply on drag with the settle discipline.
  [self buildDial:&_toothLabel value:&_toothValue slider:&_toothSlider
            strip:&_toothStrip title:@"Tooth" min:0 max:400
          current:storedToothPct()
            moved:@selector(toothMoved:) dropped:@selector(dialDropped:)
       clearTrack:clearTrack name:name small:small];
  [self buildDial:&_formationLabel value:&_formationValue
           slider:&_formationSlider strip:&_formationStrip title:@"Formation"
              min:0
              max:(float)(letterpress::kFormationDepthMax * 100.0f)
          current:storedFormationPct()
            moved:@selector(formationMoved:) dropped:@selector(dialDropped:)
       clearTrack:clearTrack name:name small:small];
  [self buildDial:&_defectsLabel value:&_defectsValue slider:&_defectsSlider
            strip:&_defectsStrip title:@"Defects"
              min:paperdefects::kDialOff max:paperdefects::kDialMax
          current:storedDefectsPct()
            moved:@selector(defectsMoved:) dropped:@selector(dialDropped:)
       clearTrack:clearTrack name:name small:small];
  [self buildDial:&_ringLabel value:&_ringValue slider:&_ringSlider
            strip:&_ringStrip title:@"Ink squeeze" min:0 max:kPartPercentMax
          current:storedRingPct()
            moved:@selector(ringMoved:) dropped:@selector(dialDropped:)
       clearTrack:clearTrack name:name small:small];
  [self buildDial:&_debossLabel value:&_debossValue slider:&_debossSlider
            strip:&_debossStrip title:@"Deboss" min:0 max:kPartPercentMax
          current:storedDebossPct()
            moved:@selector(debossMoved:) dropped:@selector(dialDropped:)
       clearTrack:clearTrack name:name small:small];
  [self buildDial:&_pressureLabel value:&_pressureValue
           slider:&_pressureSlider strip:&_pressureStrip
            title:@"Plate pressure" min:0 max:kPartPercentMax
          current:storedPressurePct()
            moved:@selector(pressureMoved:) dropped:@selector(dialDropped:)
       clearTrack:clearTrack name:name small:small];

  _readout = [UILabel new];
  _readout.font = small;
  _readout.textColor = UIColor.secondaryLabelColor;
  _readout.numberOfLines = 1;
  _readout.adjustsFontSizeToFitWidth = YES;
  _readout.minimumScaleFactor = 0.7;
  [_scroll addSubview:_readout];

  [self refresh];
  SDL_Log("[inkpicker] controller ready (ink %d, paper %d, density %d, paper "
          "strength %d)",
          _ink, _paper, _density, _paperStrength);
}

// One dial's four views. Written once rather than six times: six copies of this
// is six chances for one of them to miss the transparent track image and grow a
// system track that compresses under the thumb (the mixer's note).
//
// The out-parameters are explicitly __strong. ARC reads a bare `UILabel **`
// parameter as __autoreleasing and refuses the address of a __strong ivar
// ("passing address of non-local object to __autoreleasing parameter for
// write-back"), which is the whole reason this signature is spelled out.
- (void)buildDial:(UILabel *__strong *)label
            value:(UILabel *__strong *)value
           slider:(UISlider *__strong *)slider
            strip:(UIImageView *__strong *)strip
            title:(NSString *)title
              min:(float)mn
              max:(float)mx
          current:(int)cur
            moved:(SEL)moved
          dropped:(SEL)dropped
       clearTrack:(UIImage *)clearTrack
             name:(UIFont *)name
            small:(UIFont *)small {
  *label = [UILabel new];
  (*label).font = name;
  (*label).text = title;
  (*label).textColor = UIColor.labelColor;
  [_scroll addSubview:*label];

  *value = [UILabel new];
  (*value).font = small;
  (*value).textColor = UIColor.secondaryLabelColor;
  (*value).textAlignment = NSTextAlignmentRight;
  (*value).adjustsFontSizeToFitWidth = YES;
  (*value).minimumScaleFactor = 0.7;
  [_scroll addSubview:*value];

  *strip = [UIImageView new];
  (*strip).userInteractionEnabled = NO;
  (*strip).clipsToBounds = YES;
  (*strip).isAccessibilityElement = NO;
  (*strip).layer.borderWidth = 1;
  (*strip).layer.borderColor = UIColor.separatorColor.CGColor;
  [_scroll addSubview:*strip];

  *slider = [UISlider new];
  (*slider).minimumValue = mn;
  (*slider).maximumValue = mx;
  (*slider).value = cur;
  (*slider).accessibilityLabel = title;
  [*slider setMinimumTrackImage:clearTrack forState:UIControlStateNormal];
  [*slider setMaximumTrackImage:clearTrack forState:UIControlStateNormal];
  [*slider addTarget:self action:moved forControlEvents:UIControlEventValueChanged];
  [*slider addTarget:self
                action:dropped
      forControlEvents:UIControlEventTouchUpInside |
                       UIControlEventTouchUpOutside | UIControlEventTouchCancel];
  [_scroll addSubview:*slider];
}

- (void)viewDidLayoutSubviews {
  [super viewDidLayoutSubviews];
  _scroll.frame = self.view.bounds;
  const CGFloat margin = 20;
  const CGFloat W = self.view.bounds.size.width;
  CGFloat y = 8;
  const CGFloat rowH = 25;
  constexpr CGFloat kTrackBarPt = 16.0f;

  // One dial block: label + value on a line, then the slider riding on its
  // 16 pt preview bar. 54 pt, the density slider's own figure, so every control
  // on the sheet keeps one rhythm.
  auto layoutDial = [&](UILabel *label, UILabel *value, UISlider *slider,
                        UIView *bar, CGFloat top) {
    label.frame = CGRectMake(margin, top, 150, 18);
    value.frame = CGRectMake(W - margin - 200, top, 200, 18);
    slider.frame = CGRectMake(margin, top + 18, W - 2 * margin, 32);
    const CGRect tr = [slider trackRectForBounds:slider.bounds];
    CGRect b = [slider convertRect:tr toView:self->_scroll];
    b.origin.y += (b.size.height - kTrackBarPt) / 2;
    b.size.height = kTrackBarPt;
    bar.frame = b;
    bar.layer.cornerRadius = kTrackBarPt / 2;
  };

  _groupInk.frame = CGRectMake(margin, y, W - 2 * margin, 14);
  y += 18;
  // Walk the MODEL's display order, emitting a family heading whenever the
  // family changes. Every heading is laid out exactly once, and any that the
  // walk never reaches would be a stray label -- the model's test proves no
  // family is empty, so the walk reaches all of them.
  {
    int prevGroup = -1;
    for (int s = 0; s < lightink::kInkCount; s++) {
      const int i = _inkOrder[s];
      const int g = lightink::kInks[i].group;
      if (g != prevGroup) {
        _inkFamily[g].frame = CGRectMake(margin, y + 3, W - 2 * margin, 11);
        y += 16;
        prevGroup = g;
      }
      _inkRow[i].frame = CGRectMake(margin - 8, y, W - 2 * margin + 16, rowH);
      _inkSwatch[i].frame = CGRectMake(8, (rowH - 16) / 2, 26, 16);
      _inkName[i].frame = CGRectMake(42, 0, W / 2 - 42, rowH);
      _inkEra[i].frame =
          CGRectMake(W / 2, y + (rowH - 14) / 2, W / 2 - margin, 14);
      y += rowH;
    }
  }
  y += 8;
  layoutDial(_densityLabel, _densityValue, _slider, _track, y);
  y += 54;

  _groupPaper.frame = CGRectMake(margin, y, W - 2 * margin, 14);
  y += 18;
  // THE STOCKS WRAP. One row of `kPaperCount` cells was fine at six and is a
  // 24 pt sliver at twelve -- under the 44 pt minimum touch target, with a name
  // shrunk past reading. So the grid is a fixed SIX per row and as many rows as
  // the table needs, which keeps every cell the size it has always been and
  // makes a thirteenth stock cost a row of height rather than a millimetre off
  // every existing cell.
  const CGFloat gap = 6;
  constexpr int kPapersPerRow = 6;
  const CGFloat cell =
      (W - 2 * margin - gap * (kPapersPerRow - 1)) / kPapersPerRow;
  const CGFloat cellH = 44;
  const int paperRows =
      (lightink::kPaperCount + kPapersPerRow - 1) / kPapersPerRow;
  for (int p = 0; p < lightink::kPaperCount; p++) {
    const int col = p % kPapersPerRow, row = p / kPapersPerRow;
    _paperRow[p].frame = CGRectMake(margin + col * (cell + gap),
                                    y + row * (cellH + gap), cell, cellH);
  }
  y += paperRows * (cellH + gap) + 2;
  layoutDial(_paperLabel, _paperValue, _paperSlider, _paperTrack, y);
  y += 54;
  layoutDial(_toothLabel, _toothValue, _toothSlider, _toothStrip, y);
  y += 54;
  layoutDial(_formationLabel, _formationValue, _formationSlider, _formationStrip, y);
  y += 54;
  layoutDial(_defectsLabel, _defectsValue, _defectsSlider, _defectsStrip, y);
  y += 54;

  _groupPress.frame = CGRectMake(margin, y, W - 2 * margin, 14);
  y += 18;
  layoutDial(_ringLabel, _ringValue, _ringSlider, _ringStrip, y);
  y += 54;
  layoutDial(_debossLabel, _debossValue, _debossSlider, _debossStrip, y);
  y += 54;
  layoutDial(_pressureLabel, _pressureValue, _pressureSlider, _pressureStrip, y);
  y += 54;

  _readout.frame = CGRectMake(margin, y, W - 2 * margin, 16);
  y += 16 + 24;
  _scroll.contentSize = CGSizeMake(W, y);

  if (_track.bounds.size.width != _trackWidth) {
    _trackWidth = _track.bounds.size.width;
    [self rebuildTrackGradient];
  }
  if (_paperTrack.bounds.size.width != _paperTrackWidth) {
    _paperTrackWidth = _paperTrack.bounds.size.width;
    [self rebuildPaperTrackGradient];
  }
  if (_toothStrip.bounds.size.width != _stripWidth) {
    _stripWidth = _toothStrip.bounds.size.width;
    [self rebuildStrips];
  }
}

// --- the preview strips -----------------------------------------------------
//
// Each strip is the MODEL, evaluated left to right across its own dial's range,
// on the CURRENT paper. A gradient track would be a lie about what these
// sliders do: none of them is a colour.
//
// The paper three (tooth, formation, defects) are drawn through the sheet pass;
// the press three through the panel pass over a synthetic ink bar, because ring,
// deboss and pressure are all carried by ink or its edges and are exactly
// nothing on bare paper -- a strip of blank sheet would show six identical
// white bars and say the sliders do nothing.
- (void)rebuildStrips {
  const CGSize size = _toothStrip.bounds.size;
  if (size.width < 1 || size.height < 1) return;
  const CGFloat scale = UIScreen.mainScreen.scale;

  uint8_t ground[3];
  lightink::paperAtStrength(_paper, _paperStrength, ground);
  uint8_t wash[3];
  lightink::inkAtDensity(_ink, _paper, _density, wash, _paperStrength);

  auto lum = [](const uint8_t c[3]) {
    auto ch = [](uint8_t v) {
      const float f = v / 255.0f;
      return f <= 0.04045f ? f / 12.92f : powf((f + 0.055f) / 1.055f, 2.4f);
    };
    return 0.2126f * ch(c[0]) + 0.7152f * ch(c[1]) + 0.0722f * ch(c[2]);
  };
  const float budget = letterpress::paperBudget(lum(wash), lum(ground));
  const int master = CrossPointPrefs_letterpressPercent();
  // A strip must show something even with the master dial at Off: it is
  // previewing what THIS slider does, not whether the feature is on.
  const int shownMaster = master > 0 ? master : letterpress::kStrengthStandard;

  // A PAPER strip: the sheet model, with one parameter swept across the width.
  auto paperStrip = [&](std::function<void(letterpress::Params &, float t)> set,
                        bool withDefects) {
    return renderStrip(size, scale,
        [&, set, withDefects](int x, int y, int w, int h, uint8_t rgb[3]) {
          const float t = w > 1 ? (float)x / (float)(w - 1) : 0.0f;
          letterpress::Params p;
          p.strengthPercent = shownMaster;
          p.seed = 0x50524553u;
          p.paperDarkenBudget = budget;
          p.toothScale = (float)storedToothPct() / 100.0f *
                         lightink::toothScaleFor(_paper, _paperStrength);
          p.formationDepth = (float)storedFormationPct() / 100.0f;
          set(p, t);
          const uint8_t m = letterpress::sheetToothMultiplierAt(p, x, y, w, h);
          for (int c = 0; c < 3; c++)
            rgb[c] = (uint8_t)((int)ground[c] * m / 255);
          if (!withDefects) return;
          // The defect strip sweeps the DIAL, so each column is its own sheet:
          // marks are generated per column band rather than once, which is what
          // makes the ladder visible across 40 pt of bar.
          paperdefects::Params dp;
          dp.dialPercent = (int)(t * paperdefects::kDialMax + 0.5f);
          dp.seed = 0x44454653u ^ (uint32_t)(x / 8);
          dp.remainingBudget = letterpress::remainingPaperBudget(p);
          paperdefects::Mark marks[paperdefects::kMaxMarks];
          const int n = paperdefects::generate(dp, 8, h, marks);
          for (int k = 0; k < n; k++) {
            float mult[3];
            if (!paperdefects::multiplierAt(marks[k], x % 8, y, mult)) continue;
            for (int c = 0; c < 3; c++)
              rgb[c] = (uint8_t)((float)rgb[c] * mult[c]);
          }
        });
  };

  _toothStrip.image = paperStrip(
      [](letterpress::Params &p, float t) { p.toothScale *= t * 4.0f; }, false);
  _formationStrip.image = paperStrip(
      [](letterpress::Params &p, float t) {
        p.formationDepth = t * letterpress::kFormationDepthMax;
      },
      false);
  _defectsStrip.image = paperStrip([](letterpress::Params &, float) {}, true);

  // A PRESS strip: a synthetic ink bar down the middle, so the ring, the deboss
  // and the pressure all have an edge to live on.
  auto pressStrip = [&](std::function<void(letterpress::Params &, float t)> set) {
    return renderStrip(size, scale,
        [&, set](int x, int y, int w, int h, uint8_t rgb[3]) {
          const float t = w > 1 ? (float)x / (float)(w - 1) : 0.0f;
          letterpress::Params p;
          p.strengthPercent = shownMaster;
          p.seed = 0x50524553u;
          p.paperDarkenBudget = budget;
          p.includeTooth = false;
          set(p, t);
          // Ink across the middle third of the bar's height.
          auto ink = [&](int px, int py) {
            (void)px;
            return (py >= h / 3 && py < 2 * h / 3) ? 1.0f : 0.0f;
          };
          float win[3][3];
          for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++) {
              int sx = x + dx, sy = y + dy;
              if (sx < 0) sx = 0;
              if (sy < 0) sy = 0;
              if (sx >= w) sx = w - 1;
              if (sy >= h) sy = h - 1;
              win[dy + 1][dx + 1] = ink(sx, sy);
            }
          const uint8_t m = letterpress::multiplierAt(p, win, x, y, w, h);
          const uint8_t *tone = ink(x, y) > 0.5f ? wash : ground;
          for (int c = 0; c < 3; c++)
            rgb[c] = (uint8_t)((int)tone[c] * m / 255);
        });
  };

  _ringStrip.image = pressStrip([](letterpress::Params &p, float t) {
    p.ringScale = t * letterpress::kPartScaleMax;
  });
  _debossStrip.image = pressStrip([](letterpress::Params &p, float t) {
    p.debossScale = t * letterpress::kPartScaleMax;
    p.ringScale = 0.0f;  // the ring would swamp the shadow it is previewing
  });
  _pressureStrip.image = pressStrip([](letterpress::Params &p, float t) {
    p.pressScale = t * letterpress::kPartScaleMax;
    p.ringScale = 0.0f;
  });
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

// The paper track: the selected stock from the neutral bright-white ground to
// the largest tint 7:1 allows at the CURRENT ink and density -- so, like the
// density track, it shows exactly what the thumb can reach and nothing it
// cannot. A Bright White track is a flat white bar on purpose: that row is a
// no-op at every strength, and a gradient pretending otherwise would be a lie
// about what the slider does.
- (void)rebuildPaperTrackGradient {
  const CGSize size = _paperTrack.bounds.size;
  if (size.width < 1 || size.height < 1) return;
  const int ceilingPct = (int)_paperSlider.maximumValue;
  CGFloat comps[kGradientSamples * 4];
  CGFloat locs[kGradientSamples];
  for (int s = 0; s < kGradientSamples; s++) {
    const float t = (float)s / (kGradientSamples - 1);
    const int pct = (int)lroundf(t * ceilingPct);
    uint8_t tone[3];
    lightink::paperAtStrength(_paper, pct, tone);
    comps[s * 4 + 0] = tone[0] / 255.0;
    comps[s * 4 + 1] = tone[1] / 255.0;
    comps[s * 4 + 2] = tone[2] / 255.0;
    comps[s * 4 + 3] = 1.0;
    locs[s] = t;
  }
  CGColorSpaceRef space = CGColorSpaceCreateWithName(kCGColorSpaceSRGB);
  CGGradientRef grad =
      CGGradientCreateWithColorComponents(space, comps, locs, kGradientSamples);
  CGColorSpaceRelease(space);
  UIGraphicsImageRenderer *ren =
      [[UIGraphicsImageRenderer alloc] initWithSize:size];
  _paperTrack.image = [ren imageWithActions:^(UIGraphicsImageRendererContext *ctx) {
    CGContextDrawLinearGradient(ctx.CGContext, grad,
                                CGPointMake(0, size.height / 2),
                                CGPointMake(size.width, size.height / 2), 0);
  }];
  CGGradientRelease(grad);
}

// Re-clamp the density for the current ink+paper (the floor moves with both),
// refresh every swatch, the slider's floor, the gradient and the readout.
- (void)refresh {
  const int floorPct = lightink::floorDensityPct(_ink, _paper, _paperStrength);
  _density = lightink::clampDensityPct(_ink, _paper, _density, _paperStrength);
  const int ceilingPct =
      lightink::maxPaperStrengthPct(_ink, _paper, _density);
  _paperStrength = lightink::clampPaperStrengthPct(_ink, _paper, _density,
                                                   _paperStrength);
  _slider.minimumValue = floorPct;
  if ((int)lroundf(_slider.value) != _density) _slider.value = _density;
  _paperSlider.maximumValue = ceilingPct;
  if ((int)lroundf(_paperSlider.value) != _paperStrength)
    _paperSlider.value = _paperStrength;

  for (int i = 0; i < lightink::kInkCount; i++) {
    uint8_t wash[3];
    lightink::inkAtDensity(
        i, _paper, lightink::clampDensityPct(i, _paper, _density, _paperStrength),
        wash, _paperStrength);
    _inkSwatch[i].backgroundColor = colorOf(wash);
    _inkRow[i].backgroundColor =
        i == _ink ? UIColor.tertiarySystemFillColor : UIColor.clearColor;
    _inkRow[i].accessibilityTraits =
        i == _ink ? UIAccessibilityTraitButton | UIAccessibilityTraitSelected
                  : UIAccessibilityTraitButton;
  }
  // The stock swatches show each paper AT THE CURRENT STRENGTH, not its table
  // tone: the row you tap is the sheet you get, and at 30% every row being
  // near-white is the truth rather than a bug.
  for (int p = 0; p < lightink::kPaperCount; p++) {
    uint8_t tone[3];
    lightink::paperAtStrength(p, _paperStrength, tone);
    _paperRow[p].backgroundColor = colorOf(tone);
    _paperRow[p].layer.borderWidth = p == _paper ? 2 : 1;
    _paperRow[p].layer.borderColor = p == _paper
                                         ? UIColor.labelColor.CGColor
                                         : UIColor.separatorColor.CGColor;
    _paperRow[p].accessibilityTraits =
        p == _paper ? UIAccessibilityTraitButton | UIAccessibilityTraitSelected
                    : UIAccessibilityTraitButton;
  }
  uint8_t wash[3], ground[3];
  lightink::inkAtDensity(_ink, _paper, _density, wash, _paperStrength);
  lightink::paperAtStrength(_paper, _paperStrength, ground);
  _densityValue.text =
      [NSString stringWithFormat:@"%d%% (floor %d%%)", _density, floorPct];
  _slider.accessibilityValue = _densityValue.text;
  _paperValue.text =
      [NSString stringWithFormat:@"%d%% (max %d%%) · tooth %.2fx",
                                 _paperStrength, ceilingPct,
                                 lightink::toothScaleFor(_paper, _paperStrength)];
  _paperSlider.accessibilityValue = _paperValue.text;
  _readout.text = [NSString
      stringWithFormat:@"%s %d%% on %s %d%% — %.1f:1 · %@ on %@",
                       lightink::kInks[_ink].name, _density,
                       lightink::kPapers[_paper].name, _paperStrength,
                       lightink::contrastAtDensity(_ink, _paper, _density,
                                                   _paperStrength),
                       hexOf(wash), hexOf(ground)];
  _toothValue.text = [NSString
      stringWithFormat:@"%d%% · sheet %.2fx", storedToothPct(),
                       storedToothPct() / 100.0f *
                           lightink::toothScaleFor(_paper, _paperStrength)];
  _toothSlider.accessibilityValue = _toothValue.text;
  _formationValue.text =
      [NSString stringWithFormat:@"%d%%", storedFormationPct()];
  _formationSlider.accessibilityValue = _formationValue.text;
  _defectsValue.text =
      [NSString stringWithFormat:@"%d%%%@", storedDefectsPct(),
                storedDefectsPct() == 0 ? @" (a fresh sheet)" : @""];
  _defectsSlider.accessibilityValue = _defectsValue.text;
  _ringValue.text = [NSString stringWithFormat:@"%d%% of standard", storedRingPct()];
  _ringSlider.accessibilityValue = _ringValue.text;
  _debossValue.text = [NSString stringWithFormat:@"%d%% of standard", storedDebossPct()];
  _debossSlider.accessibilityValue = _debossValue.text;
  _pressureValue.text =
      [NSString stringWithFormat:@"%d%% of standard", storedPressurePct()];
  _pressureSlider.accessibilityValue = _pressureValue.text;
  [self rebuildTrackGradient];
  [self rebuildPaperTrackGradient];
  [self rebuildStrips];
}

// A TAP IS NOT A SLIDER MOVE. Changing the ink or the stock re-clamps the
// DENSITY and leaves the paper strength where the owner put it -- the sheet is
// the deliberate choice and the ink is the variable that pays for it. Density
// 100 is legal at every strength (the tables clear 7:1 at full on full), so
// this can never fail to find a legal pair.
- (void)inkTapped:(UIButton *)b {
  _ink = (int)b.tag;
  _density =
      lightink::clampDensityPct(_ink, _paper, _density, _paperStrength);
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/false);
  [self refresh];
  [self scheduleSettle];
}

- (void)paperTapped:(UIButton *)b {
  _paper = (int)b.tag;
  _density =
      lightink::clampDensityPct(_ink, _paper, _density, _paperStrength);
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/false);
  [self refresh];
  [self scheduleSettle];
}

- (void)densityMoved:(UISlider *)s {
  [self cancelPendingSettle];
  _density = lightink::clampDensityPct(_ink, _paper, (int)lroundf(s.value),
                                       _paperStrength);
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/false);
  [self refresh];
}

- (void)densityDropped:(UISlider *)s {
  [self cancelPendingSettle];
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/true);
}

- (void)paperStrengthMoved:(UISlider *)s {
  [self cancelPendingSettle];
  _paperStrength = lightink::clampPaperStrengthPct(_ink, _paper, _density,
                                                   (int)lroundf(s.value));
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/false);
  [self refresh];
}

- (void)paperStrengthDropped:(UISlider *)s {
  [self cancelPendingSettle];
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/true);
}

// --- the paper instrument's six -------------------------------------------
//
// Same discipline as the density and paper sliders: persist, push live on the
// drag (the SDL side recolours a cached framebuffer, which is cheap), and defer
// the firmware re-dither to the settle. None of these six changes what the
// firmware DRAWS -- they are all present-time fields -- so the settle is only
// there to keep the page in step with a palette change that rode along.
- (void)storeDial:(NSString *)key value:(int)v {
  [[NSUserDefaults standardUserDefaults] setInteger:v forKey:key];
}

- (void)dialChanged {
  pushPaperDials(_paper, _paperStrength);
  SimulatorOverlay::requestPresent();
  [self refresh];
}

- (void)toothMoved:(UISlider *)s {
  [self cancelPendingSettle];
  [self storeDial:kPaperToothKey value:(int)lroundf(s.value)];
  [self dialChanged];
}

- (void)formationMoved:(UISlider *)s {
  [self cancelPendingSettle];
  [self storeDial:kPaperFormationKey value:(int)lroundf(s.value)];
  [self dialChanged];
}

- (void)defectsMoved:(UISlider *)s {
  [self cancelPendingSettle];
  // Through CrossPointPrefs, not -setInteger: here: this key is ALSO a
  // Settings.bundle row, and both views must clamp identically.
  CrossPointPrefs_setPaperDefectsPercent((int)lroundf(s.value));
  [self dialChanged];
}

- (void)ringMoved:(UISlider *)s {
  [self cancelPendingSettle];
  [self storeDial:kPressRingKey value:(int)lroundf(s.value)];
  [self dialChanged];
}

- (void)debossMoved:(UISlider *)s {
  [self cancelPendingSettle];
  [self storeDial:kPressDebossKey value:(int)lroundf(s.value)];
  [self dialChanged];
}

- (void)pressureMoved:(UISlider *)s {
  [self cancelPendingSettle];
  [self storeDial:kPressPressureKey value:(int)lroundf(s.value)];
  [self dialChanged];
}

- (void)dialDropped:(UISlider *)s {
  (void)s;
  [self cancelPendingSettle];
  crosspointRequestRender();
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
// driven by CROSSPOINT_SIM_APPLY_INK="ink,paper,density[,paperStrength]" in
// the shim. The fourth field is optional and defaults to full strength, so
// every recipe written before the paper dial existed still means what it did.
extern "C" void CrossPointInkPicker_applyForTest(int ink, int paper,
                                                 int density,
                                                 int paperStrength) {
  ink = lightink::clampInkIndex(ink);
  paper = lightink::clampPaperIndex(paper);
  paperStrength =
      lightink::clampPaperStrengthPct(ink, paper, density, paperStrength);
  density = lightink::clampDensityPct(ink, paper, density, paperStrength);
  applySelection(ink, paper, density, paperStrength, /*renderPage=*/true);
  uint8_t wash[3], ground[3];
  lightink::inkAtDensity(ink, paper, density, wash, paperStrength);
  lightink::paperAtStrength(paper, paperStrength, ground);
  SDL_Log("[inkpicker] test hook applied %s %d%% on %s %d%% -> %s on %s "
          "(tooth %d%%)",
          lightink::kInks[ink].name, density, lightink::kPapers[paper].name,
          paperStrength, hexOf(wash).UTF8String, hexOf(ground).UTF8String,
          paperToothPercentFor(paper, paperStrength));
}

// The launch-time seed for the sheet's texture. The picker may never be
// opened, and the paper the owner chose last week still has a roughness, so
// the shim polls this rather than waiting for a finger. Reads the SAME stored
// selection loadSelection does, through the same clamps.
extern "C" int CrossPointInkPicker_paperToothPercent(void) {
  int ink = 0, paper = 0, density = 0, strength = 0;
  loadSelection(&ink, &paper, &density, &strength);
  return paperToothPercentFor(paper, strength);
}

// EVERY paper dial, pushed at once. Same argument as the tooth seed above and
// one step further: the drawer may never be opened, and a sheet the owner set
// last week still has a formation, marks and a press composition. The shim
// calls this whenever the signature below moves, which covers both the launch
// seed and a change made from Settings.app (the Defects row) rather than from
// the drawer.
extern "C" void CrossPointInkPicker_pushPaperDials(void) {
  int ink = 0, paper = 0, density = 0, strength = 0;
  loadSelection(&ink, &paper, &density, &strength);
  pushPaperDials(paper, strength);
}

// A cheap value that changes whenever ANY paper dial does, so the shim's poll
// stays edge-triggered instead of pushing six setters every frame.
extern "C" uint32_t CrossPointInkPicker_paperDialSignature(void) {
  int ink = 0, paper = 0, density = 0, strength = 0;
  loadSelection(&ink, &paper, &density, &strength);
  uint32_t h = 2166136261u;
  const int parts[] = {paperToothPercentFor(paper, strength),
                       storedFormationPct(), storedDefectsPct(),
                       storedRingPct(),      storedDebossPct(),
                       storedPressurePct()};
  for (const int v : parts) {
    h ^= (uint32_t)v;
    h *= 16777619u;
  }
  return h;
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
      // MEDIUM FIRST, so the drawer still opens exactly the size it always
      // did; LARGE beside it because nine controls do not fit a medium detent
      // and scrolling a half-height sheet for the Press group is worse than
      // being able to pull it up.
      nav.sheetPresentationController.detents = @[
        UISheetPresentationControllerDetent.mediumDetent,
        UISheetPresentationControllerDetent.largeDetent
      ];
      nav.sheetPresentationController.prefersGrabberVisible = NO;
      // Undimmed at medium: the page above the sheet IS the preview.
      nav.sheetPresentationController.largestUndimmedDetentIdentifier =
          UISheetPresentationControllerDetentIdentifierMedium;
    }
    g_pickerPresented.store(true);
    [root presentViewController:nav animated:YES completion:nil];
  });
}
