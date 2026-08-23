// The named-preset list both page-color editors push. See
// ios/CrossPointPresetList.h for what it is and why there is only one of it.
//
// THE LAYOUT IS THE INK PICKER'S PAPER GRID, deliberately: a wrapped grid of
// swatch cells with a family heading above each block, manual frames inside a
// scroll view. A preset is a PAIR OF COLORS with a name, which is exactly what
// that control already shows for the paper stocks -- so each cell is painted in
// the preset's own paper with its own name in its own ink, and the cell IS the
// preview. A menu of fifty titles would have been less code and would have
// shown the reader nothing.
//
// The cells are previewed in ONE appearance -- the one the presenting editor
// renders. Every row is offered in both, though: a preset defines both halves,
// and the list is the only place they are reachable at all now.
//
// Selection applies LIVE and does not pop. The drawer above it is undimmed at
// the medium detent precisely so the page stays visible as the preview, and
// walking the list watching the page is the whole point; the firmware
// re-dither is coalesced behind the editors' own 0.35 s settle so a walk does
// not queue fifty of them.
//
// No setTitle: on this controller or its navigationItem either -- the build 110
// device crash (objc_retain(0x1) inside UIKit's setTitle:) is not specific to
// the two drawers.

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <cstdlib>
#include <cstring>

#include "CrossPointPresetList.h"

#include "CrossPointPrefs.h"
#include "PanelPalette.h"
#include "PanelPrefs.h"
#include "SimulatorOverlay.h"

// C++ LINKAGE, deliberately -- defined in the firmware with no extern "C";
// declaring it C is the build 110 link death (see the mixer).
void crosspointRequestRender();

namespace {

constexpr int kPerRow = 3;      // 3 cells across reads the two-word names
constexpr CGFloat kCellH = 52;  // clears the 44 pt touch minimum with room
constexpr CGFloat kGap = 6;

UIColor *colorOf(const uint8_t c[3]) {
  return [UIColor colorWithRed:c[0] / 255.0
                         green:c[1] / 255.0
                          blue:c[2] / 255.0
                         alpha:1];
}

NSString *hexOf(const uint8_t c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
}

// Apply a selection through the shared protocol, then repaint. The prefs call
// is the whole decision (src/PanelSource.h::Release); everything after it is
// getting the result onto the glass, on exactly the terms the two editors use:
// requestPresent recolors the CACHED framebuffer immediately, and the firmware
// re-dither is the caller's to schedule because it costs hundreds of ms.
void selectPreset(int preset) {
  CrossPointPrefs_selectPanelPreset(preset);
  const panelpalette::PresetInfo *info = panelpalette::infoForPreset(preset);
  SDL_Log("[presets] selected %d (%s %s) -> %.0f ms trail", preset,
          info ? info->family : "?", info ? info->name : "?",
          (double)panelpalette::trailMsForPreset(preset));
  SimulatorOverlay::requestPresent();
}

}  // namespace

@interface CPXPresetListController : UIViewController
@end

@implementation CPXPresetListController {
  BOOL _dark;
  void (^_onSelect)(void);
  UIScrollView *_scroll;
  UILabel *_readout;
  UIButton *_cell[panelpalette::kPresetInfoCount];
  // One heading per GROUP BOUNDARY in the table's own order, so the count is
  // bounded by the row count and the walk fills whatever it needs. Grouping is
  // panelpalette::groupNameForRow's, not this file's -- appending a preset must
  // not require editing a layout list here.
  UILabel *_heading[panelpalette::kPresetInfoCount];
  int _headingCount;
  int _headingBeforeRow[panelpalette::kPresetInfoCount];  // row -> heading, or -1
  dispatch_block_t _pendingSettle;
}

- (instancetype)initWithDark:(BOOL)dark onSelect:(void (^)(void))onSelect {
  self = [super init];
  if (self) {
    _dark = dark;
    _onSelect = [onSelect copy];
  }
  return self;
}

- (void)viewDidLoad {
  [super viewDidLoad];
  SDL_Log("[presets] list viewDidLoad (%s appearance)", _dark ? "dark" : "light");
  self.view.backgroundColor = UIColor.systemBackgroundColor;

  _scroll = [UIScrollView new];
  _scroll.alwaysBounceVertical = YES;
  [self.view addSubview:_scroll];

  UIFont *cellFont = [UIFont monospacedSystemFontOfSize:9
                                                 weight:UIFontWeightMedium];
  UIFont *groupFont = [UIFont monospacedSystemFontOfSize:11
                                                  weight:UIFontWeightBold];
  UIFont *small = [UIFont monospacedSystemFontOfSize:10
                                              weight:UIFontWeightRegular];

  _readout = [UILabel new];
  _readout.font = small;
  _readout.textColor = UIColor.secondaryLabelColor;
  _readout.adjustsFontSizeToFitWidth = YES;
  _readout.minimumScaleFactor = 0.7;
  [_scroll addSubview:_readout];

  // Walk the table in ITS order, emitting a heading whenever the group changes.
  _headingCount = 0;
  const char *prevGroup = nullptr;
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const char *group = panelpalette::groupNameForRow(i);
    _headingBeforeRow[i] = -1;
    if (!prevGroup || std::strcmp(group, prevGroup) != 0) {
      UILabel *l = [UILabel new];
      l.font = groupFont;
      l.textColor = UIColor.secondaryLabelColor;
      l.text = [@(group) uppercaseString];
      [_scroll addSubview:l];
      _heading[_headingCount] = l;
      _headingBeforeRow[i] = _headingCount;
      _headingCount++;
      prevGroup = group;
    }

    const panelpalette::PresetInfo &info = panelpalette::kPresetInfo[i];
    const panelpalette::Palette pair =
        panelpalette::presetPalette(info.preset, _dark != NO);
    _cell[i] = [UIButton buttonWithType:UIButtonTypeCustom];
    _cell[i].tag = i;
    _cell[i].layer.cornerRadius = 6;
    _cell[i].backgroundColor = colorOf(pair.paper);
    _cell[i].titleLabel.font = cellFont;
    _cell[i].titleLabel.numberOfLines = 2;
    _cell[i].titleLabel.textAlignment = NSTextAlignmentCenter;
    _cell[i].titleLabel.lineBreakMode = NSLineBreakByWordWrapping;
    _cell[i].titleLabel.adjustsFontSizeToFitWidth = YES;
    _cell[i].titleLabel.minimumScaleFactor = 0.7;
    [_cell[i] setTitle:@(info.name) forState:UIControlStateNormal];
    // THE CELL'S OWN INK, not a fixed dark like the paper stocks': a preset is
    // two tones and this is the only place both are visible at once. Every row
    // clears 7:1 except Solarized, which is 4.1:1 by design.
    [_cell[i] setTitleColor:colorOf(pair.ink) forState:UIControlStateNormal];
    // VoiceOver gets what the swatch cannot say: the family, the phosphor and
    // its persistence, in the order the row reads.
    _cell[i].accessibilityLabel = [NSString
        stringWithFormat:@"%s, %s%s%s", info.name,
                         panelpalette::groupNameForRow(i),
                         info.note ? ", " : "", info.note ? info.note : ""];
    _cell[i].accessibilityTraits = UIAccessibilityTraitButton;
    [_cell[i] addTarget:self
                  action:@selector(cellTapped:)
        forControlEvents:UIControlEventTouchUpInside];
    [_scroll addSubview:_cell[i]];
  }

  [self refresh];
  SDL_Log("[presets] %d rows in %d groups", panelpalette::kPresetInfoCount,
          _headingCount);
}

- (void)viewDidLayoutSubviews {
  [super viewDidLayoutSubviews];
  _scroll.frame = self.view.bounds;
  const CGFloat margin = 20;
  const CGFloat W = self.view.bounds.size.width;
  const CGFloat cellW = (W - 2 * margin - kGap * (kPerRow - 1)) / kPerRow;
  CGFloat y = 10;

  _readout.frame = CGRectMake(margin, y, W - 2 * margin, 16);
  y += 24;

  // Each group starts a fresh row, so the blocks read as blocks. `col` resets
  // with the heading rather than running on from the previous family.
  int col = 0;
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    if (_headingBeforeRow[i] >= 0) {
      if (col != 0) {
        y += kCellH + kGap;
        col = 0;
      }
      _heading[_headingBeforeRow[i]].frame =
          CGRectMake(margin, y + 2, W - 2 * margin, 14);
      y += 20;
    }
    _cell[i].frame =
        CGRectMake(margin + col * (cellW + kGap), y, cellW, kCellH);
    if (++col == kPerRow) {
      col = 0;
      y += kCellH + kGap;
    }
  }
  if (col != 0) y += kCellH + kGap;
  _scroll.contentSize = CGSizeMake(W, y + 24);
}

// The live selection, read from the store rather than remembered: the drawer
// underneath can claim the Custom slot while this list is on the stack (its
// sliders are still live behind the push), and a remembered index would go on
// showing a preset the page no longer uses.
- (void)refresh {
  const int stored = CrossPointPrefs_panelPalettePreset();
  const int live = panelpalette::migratePreset(stored);
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const BOOL on = panelpalette::kPresetInfo[i].preset == live;
    _cell[i].layer.borderWidth = on ? 3 : 1;
    _cell[i].layer.borderColor = on ? UIColor.labelColor.CGColor
                                    : UIColor.separatorColor.CGColor;
    _cell[i].accessibilityTraits =
        on ? UIAccessibilityTraitButton | UIAccessibilityTraitSelected
           : UIAccessibilityTraitButton;
  }
  const panelpalette::PresetInfo *info = panelpalette::infoForPreset(live);
  const panelpalette::Palette pair = crosspoint::panelForPrefs(_dark != NO);
  if (info) {
    _readout.text =
        [NSString stringWithFormat:@"%s — %s · %@ on %@ · %.0f ms trail",
                                   info->name, info->note ? info->note : "",
                                   hexOf(pair.ink), hexOf(pair.paper),
                                   (double)panelpalette::trailMsForPreset(live)];
  } else {
    // Custom is not a row, so nothing is outlined and the line says what the
    // page IS -- the tones an editor put there.
    _readout.text = [NSString stringWithFormat:@"Custom — %@ on %@ · %s",
                                               hexOf(pair.ink),
                                               hexOf(pair.paper),
                                               _dark ? "mixed" : "inked"];
  }
}

- (void)cellTapped:(UIButton *)b {
  const int i = (int)b.tag;
  if (i < 0 || i >= panelpalette::kPresetInfoCount) return;
  selectPreset(panelpalette::kPresetInfo[i].preset);
  [self refresh];
  if (_onSelect) _onSelect();
  [self scheduleSettle];
}

// The deferred, COALESCED firmware re-render -- the drawers' settle, same
// 0.35 s, same reason: a re-dither costs hundreds of ms and must not ride a
// walk down the list.
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

// Leaving the list settles whatever is pending, so the page the drawer goes
// back to is dithered for the pair it is actually showing.
- (void)viewDidDisappear:(BOOL)animated {
  [super viewDidDisappear:animated];
  if (_pendingSettle) {
    [self cancelPendingSettle];
    crosspointRequestRender();
  }
}

@end

UIViewController *CrossPointPresetList_make(BOOL dark, void (^onSelect)(void)) {
  return [[CPXPresetListController alloc] initWithDark:dark onSelect:onSelect];
}

BOOL CrossPointPresetList_autoOpen(void) {
  const char *e = getenv("CROSSPOINT_SIM_OPEN_PRESETS");
  return (e && e[0] == '1') ? YES : NO;
}

extern "C" void CrossPointPresetList_selectForTest(int preset) {
  selectPreset(preset);
  // renderPage, unconditionally: a scripted run has no finger to lift and no
  // list to leave, so the settle that a tap would eventually get is taken here.
  crosspointRequestRender();
}
