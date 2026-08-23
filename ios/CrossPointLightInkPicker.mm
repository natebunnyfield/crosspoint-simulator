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
//   * the PAPER STOCK swatches, six per row.
//
// THE SHEET'S PARAMETERS ARE FROZEN (owner ruling 2026-08-23: "set Paper,
// tooth, formation, defects and press to these parameter values, then remove
// sliders and option to set this in app"). Paper strength, tooth, formation,
// defects, sheet drift and the three press parts are the constants below,
// read from no store, with no control anywhere that reaches them. The ink and
// the stock are still the owner's to choose, and density is still a slider.
//
// The paper strength is frozen at FULL and RE-DERIVED on every change rather
// than carried, because clampPaperStrengthPct is a ceiling that moves with the
// ink: a strength once lowered by a dark pick would have no control left that
// could raise it again. Derivation and the swept grid:
// docs/light-ink-picker.md.
//
// The sheet's TEXTURE still rides the stock. Each has a tooth factor
// (lightink::toothScaleFor) that the frozen strength scales, so a chamois is
// rougher than a bright white; the number is pushed to
// SimulatorOverlay::setPaperTooth and lands on the letterpress sheet pass.
//
// Selection applies LIVE through the existing custom light fields
// (panelInkLight/panelPaperLight + preset Custom), so the whole downstream --
// letterpress, pad-on-paper, keyboard chips -- follows through
// crosspoint::panelForPrefs() with no new plumbing. Persistence is three
// append-only integer keys -- ink, stock, density, and nothing else since the
// sheet froze -- with the applied result mirrored into the light hex fields,
// the mixer's storage discipline. The custom DARK fields stay
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

#include "CrossPointPrefs.h"
#include "LightInkPalette.h"
#include "PanelPalette.h"
#include "PanelPrefs.h"
#include "SimulatorOverlay.h"

// C++ LINKAGE, deliberately -- defined in the firmware with no extern "C";
// declaring it C is the build 110 link death (see the mixer).
void crosspointRequestRender();

// --- persistence ------------------------------------------------------------
// The picker's own keys are APPEND-ONLY integers (LightInkPalette.h's rule);
// the four hex keys are the same store the mixer and Settings.app write.
//
// The paper instrument's seven keys are GONE (owner ruling 2026-08-23, below):
// nothing reads or writes lightPaperStrengthPercent, paperToothPercent,
// paperFormationPercent, paperDriftPercent, pressRingPercent,
// pressDebossPercent or pressPressurePercent any more, and a key naming a
// value nothing consults is worse than no key. The APPEND-ONLY rule is not
// violated by their removal: no surviving key moved.
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

// --- the paper instrument's seven, FROZEN ------------------------------------
//
// FROZEN 2026-08-23 by owner ruling: "set Paper, tooth, formation, defects and
// press to these parameter values, then remove sliders and option to set this
// in app". Each value below is the one he had chosen when he ruled, and each is
// returned WITHOUT consulting NSUserDefaults -- an install that stored a
// different value before the slider was removed must not keep rendering it, and
// with the slider gone there would be no way to change it back. The precedent
// is CrossPointPrefs.mm's own frozen getters, and it is followed exactly.
//
// Sheet drift is the one value his screenshot could not carry: it landed after
// the build he ruled against. Frozen at the TOP of its range by a later ruling
// the same day. It is deliberately NOT lightink::kPaperDriftDefault -- that
// constant still means "the model ships this off" and is read as such by the
// desktop and the tests; the app's frozen value simply differs from it.
constexpr int kFrozenPaperStrengthPct = 100;

int storedToothPct(void) { return 300; }
int storedFormationPct(void) { return 80; }
int storedDriftPct(void) { return lightink::kPaperDriftMax; }
int storedRingPct(void) { return 100; }
int storedDebossPct(void) { return 100; }
int storedPressurePct(void) { return 100; }
// Defects is frozen in CrossPointPrefs.mm rather than here, because that file
// already holds the day's other frozen getters; read through it so the two
// surfaces cannot disagree about how marked the sheet is.
int storedDefectsPct(void) { return CrossPointPrefs_paperDefectsPercent(); }

// Stored selection, clamped through the core so a restored backup from a
// future build lands on the shipped rows rather than out of bounds. The
// missing-key trap on the density is the malignant -integerForKey: one: absent
// answers 0, and 0 here is a real value nobody chose -- a floor-clamped wash.
// Absent means "never touched", which is full density.
//
// The paper strength is not stored at all any more: the request is the frozen
// constant, and it still runs through clampPaperStrengthPct because that clamp
// is what holds 7:1 against the chosen ink and stock. The owner's own screen
// read "100% (max 100%)" -- the clamped result, not the request.
//
// The two clamps run in the order the invariant needs: the paper strength is
// pinned to its ceiling for the STORED density first, then the density to its
// floor at the resulting strength.
void loadSelection(int *ink, int *paper, int *density, int *paperStrength) {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  *ink = lightink::clampInkIndex((int)[d integerForKey:kInkIndexKey]);
  *paper = lightink::clampPaperIndex((int)[d integerForKey:kPaperIndexKey]);
  id storedDensity = [d objectForKey:kInkDensityKey];
  const int rawDensity = storedDensity ? (int)[d integerForKey:kInkDensityKey]
                                       : lightink::kDensityMax;
  // BOTH CLAMPS CARRY THE DRIFT DIAL. The floor has to hold for the darkest
  // leaf the drift can produce, not for the nominal sheet -- a pair clamped
  // without it sits exactly ON 7.0 and the next leaf two code values darker is
  // under it. With drift frozen at the top of its range that is no longer a
  // worst case, it is every page.
  const int drift = storedDriftPct();
  *paperStrength = lightink::clampPaperStrengthPct(
      *ink, *paper, rawDensity, kFrozenPaperStrengthPct, drift);
  *density = lightink::clampDensityPct(*ink, *paper, rawDensity,
                                       *paperStrength, drift);
}

// The sheet's roughness for this selection, as the percent SimulatorOverlay
// carries: the STOCK's own factor times the frozen Tooth value. Two inputs, one
// number -- a stock still reads as itself and the frozen 300% is a multiplier
// on it, so choosing a chamois is still a texture change even with no Tooth
// slider left to move.
int paperToothPercentFor(int paper, int paperStrength) {
  const float stock = lightink::toothScaleFor(paper, paperStrength);
  return (int)lroundf(stock * (float)storedToothPct());
}

// The sheet's cloudiness, same composition: the STOCK's own formation factor
// (lightink::formationScaleFor -- kozo's is the one measured value in that
// ladder) times the frozen Formation value. The overlay clamps the product at
// the model's max, so a kozo saturates rather than overswings.
int paperFormationPercentFor(int paper, int paperStrength) {
  const float stock = lightink::formationScaleFor(paper, paperStrength);
  return (int)lroundf(stock * (float)storedFormationPct());
}

// The stock's WIRES: the paper-strength percent for a laid stock, 0 for every
// wove one -- the laid field rides the paper strength the way tooth and
// formation do, and a stock with no wires pushes an explicit 0 so switching
// off a laid stock takes its lines away.
int laidLinesPercentFor(int paper, int paperStrength) {
  return lightink::kPapers[lightink::clampPaperIndex(paper)].laid
             ? paperStrength
             : 0;
}

// Push every paper dial at the SDL side. Called on any change and by the shim's
// launch seed, because the drawer may never be opened and the chosen stock
// still has a texture. Six of the eight numbers are frozen constants now; the
// tooth, the formation and the wires still move with the stock.
void pushPaperDials(int paper, int paperStrength) {
  SDL_Log("[letterpress] paper: tooth %d%% (stock %.2fx x dial %d%%), "
          "formation %d%% (stock %.2fx x dial %d%%), laid %d%%, defects %d%%, "
          "drift %d%% (+/-%d code values) "
          "| press: ring %d%% deboss %d%% pressure %d%%",
          paperToothPercentFor(paper, paperStrength),
          (double)lightink::toothScaleFor(paper, paperStrength),
          storedToothPct(), paperFormationPercentFor(paper, paperStrength),
          (double)lightink::formationScaleFor(paper, paperStrength),
          storedFormationPct(), laidLinesPercentFor(paper, paperStrength),
          storedDefectsPct(), storedDriftPct(),
          lightink::maxDriftCodeValues(storedDriftPct()), storedRingPct(),
          storedDebossPct(), storedPressurePct());
  SimulatorOverlay::setPaperTooth(paperToothPercentFor(paper, paperStrength));
  SimulatorOverlay::setPaperFormation(
      paperFormationPercentFor(paper, paperStrength));
  SimulatorOverlay::setLaidLines(laidLinesPercentFor(paper, paperStrength));
  SimulatorOverlay::setPaperDefects(storedDefectsPct());
  SimulatorOverlay::setPaperDrift(storedDriftPct());
  SimulatorOverlay::setPressRing(storedRingPct());
  SimulatorOverlay::setPressDeboss(storedDebossPct());
  SimulatorOverlay::setPressPressure(storedPressurePct());
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
  // The paper strength is NOT persisted: it is frozen, and re-derived from the
  // frozen request at every load and every change.

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
  UILabel *_readout;
  // THE SCROLL VIEW. The ink list alone is longer than a medium detent, and the
  // opening size stays medium by owner-facing continuity -- so the sheet
  // scrolls and gains a LARGE detent beside it. Manual frames stay; they are
  // frames inside this view's content now, which is a smaller change than
  // adopting Auto Layout mid-flight.
  UIScrollView *_scroll;
  UILabel *_groupInk;
  UILabel *_groupPaper;
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
  int _ink;
  int _paper;
  int _density;
  // Not a control's value any more: the frozen request, re-clamped for the live
  // ink and stock on every change (reclampSelection).
  int _paperStrength;
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

  _scroll = [UIScrollView new];
  _scroll.alwaysBounceVertical = YES;
  _scroll.showsVerticalScrollIndicator = YES;
  [self.view addSubview:_scroll];

  loadSelection(&_ink, &_paper, &_density, &_paperStrength);

  UIFont *name = [UIFont monospacedSystemFontOfSize:13 weight:UIFontWeightSemibold];
  UIFont *small = [UIFont monospacedSystemFontOfSize:10 weight:UIFontWeightRegular];

  UIFont *group = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightBold];
  // TWO LABELED GROUPS -- Ink / Paper. The PRESS group went with its three
  // sliders (frozen 2026-08-23); the grouping that remains is the model's own
  // division, what the ink is and what the sheet is.
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

  // Transparent system track, both halves: the gradient underlay IS the track
  // (a track IMAGE compresses as the thumb moves -- see the mixer).
  static UIImage *clearTrack;
  static dispatch_once_t clearOnce;
  dispatch_once(&clearOnce, ^{
    UIGraphicsImageRenderer *r =
        [[UIGraphicsImageRenderer alloc] initWithSize:CGSizeMake(1, 1)];
    clearTrack = [r imageWithActions:^(UIGraphicsImageRendererContext *c){}];
  });

  _slider = [UISlider new];
  _slider.minimumValue =
      lightink::floorDensityPct(_ink, _paper, _paperStrength, storedDriftPct());
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

- (void)viewDidLayoutSubviews {
  [super viewDidLayoutSubviews];
  _scroll.frame = self.view.bounds;
  const CGFloat margin = 20;
  const CGFloat W = self.view.bounds.size.width;
  CGFloat y = 8;
  const CGFloat rowH = 25;
  constexpr CGFloat kTrackBarPt = 16.0f;

  // The density block: label + value on a line, then the slider riding on its
  // 16 pt gradient bar. Still a lambda though it is called once -- the frame
  // arithmetic between a UISlider's track rect and the bar under it is the
  // part worth keeping named.
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
  y += paperRows * (cellH + gap) + 8;

  _readout.frame = CGRectMake(margin, y, W - 2 * margin, 16);
  y += 16 + 24;
  _scroll.contentSize = CGSizeMake(W, y);

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

// The whole selection re-derived for the live ink and stock. The paper strength
// is RE-DERIVED from the frozen request rather than carried: clampPaperStrength
// Pct is a ceiling that moves with the ink, so a strength once lowered by a dark
// pick would have no control left that could raise it again. Both clamps carry
// the drift dial -- the floor and the ceiling are the DARKEST leaf's, so no page
// of the book falls under 7:1 rather than only the nominal sheet clearing it,
// and with drift frozen at the top of its range that is every page.
- (void)reclampSelection {
  const int drift = storedDriftPct();
  _paperStrength = lightink::clampPaperStrengthPct(
      _ink, _paper, _density, kFrozenPaperStrengthPct, drift);
  _density =
      lightink::clampDensityPct(_ink, _paper, _density, _paperStrength, drift);
}

// Re-clamp the selection, then refresh every swatch, the slider's floor, the
// gradient and the readout.
- (void)refresh {
  const int drift = storedDriftPct();
  [self reclampSelection];
  const int floorPct =
      lightink::floorDensityPct(_ink, _paper, _paperStrength, drift);
  _slider.minimumValue = floorPct;
  if ((int)lroundf(_slider.value) != _density) _slider.value = _density;

  for (int i = 0; i < lightink::kInkCount; i++) {
    uint8_t wash[3];
    lightink::inkAtDensity(
        i, _paper,
        lightink::clampDensityPct(i, _paper, _density, _paperStrength, drift),
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
  _readout.text = [NSString
      stringWithFormat:@"%s %d%% on %s %d%% — %.1f:1 · %@ on %@",
                       lightink::kInks[_ink].name, _density,
                       lightink::kPapers[_paper].name, _paperStrength,
                       lightink::contrastAtDensity(_ink, _paper, _density,
                                                   _paperStrength),
                       hexOf(wash), hexOf(ground)];
  [self rebuildTrackGradient];
}

// EVERY change re-derives the whole selection (reclampSelection) BEFORE it is
// applied, not after: applySelection writes the hex fields the page renders
// from, so a clamp that ran only in the following refresh would leave the page
// painted from the pre-clamp pair until the next change. With the paper slider
// gone that is not a cosmetic lag -- the strength is re-derived on every pick,
// and a dark ink lowers it while a lighter one gets it back. Density 100 is
// legal at every strength (the tables clear 7:1 at full on full), so this can
// never fail to find a legal pair.
- (void)inkTapped:(UIButton *)b {
  _ink = (int)b.tag;
  [self reclampSelection];
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/false);
  [self refresh];
  [self scheduleSettle];
}

- (void)paperTapped:(UIButton *)b {
  _paper = (int)b.tag;
  [self reclampSelection];
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/false);
  [self refresh];
  [self scheduleSettle];
}

- (void)densityMoved:(UISlider *)s {
  [self cancelPendingSettle];
  _density = (int)lroundf(s.value);
  [self reclampSelection];
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/false);
  [self refresh];
}

- (void)densityDropped:(UISlider *)s {
  [self cancelPendingSettle];
  applySelection(_ink, _paper, _density, _paperStrength, /*renderPage=*/true);
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
  paperStrength = lightink::clampPaperStrengthPct(ink, paper, density,
                                                  paperStrength,
                                                  storedDriftPct());
  density = lightink::clampDensityPct(ink, paper, density, paperStrength,
                                      storedDriftPct());
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
                       storedDriftPct(),     storedRingPct(),
                       storedDebossPct(),    storedPressurePct()};
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
      // did; LARGE beside it because the ink list alone is longer than a medium
      // detent and scrolling a half-height sheet for the stocks is worse than
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
