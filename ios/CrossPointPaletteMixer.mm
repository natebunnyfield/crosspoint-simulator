// The page-color modal: presets, and the phosphor mixer.
//
// Owner rulings 2026-08-20, in order:
//   - press OR hold on the page-color chip opens this modal (it no longer
//     cycles; the modal is the whole page-color surface now)
//   - all three mix models: Blend, Parts, Cascade
//   - one live mix slot, persisted, occupying the Custom preset
//   - premixed phosphors (P4, P6, P7, P14, P17, P18, P23, P40) are NOT
//     ingredients; they are offered as preset mixes instead
//   - every phosphor row shows the exact colors -- dark and light, ink and
//     paper -- and its time to fade
//
// The mixing MATH lives in src/PhosphorMix.h, pure and host-tested. This file
// is only UIKit: rows, swatches, sliders, and writing the result into the
// stores the rest of the app already reads. The page updates live because
// pollPanelPalette/pollPanelGlow compare stored values every frame -- writing
// the keys IS applying them.

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <vector>

#include "PanelPalette.h"
#include "PhosphorMix.h"
#include "SimulatorOverlay.h"
#include "CrossPointPrefs.h"

extern "C" void crosspointRequestRender(void);
extern "C" void CrossPointMixer_glowChanged(void);

// --- persistence -----------------------------------------------------------
// The mix is ONE slot, stored small and flat. Component lists are a CSV of
// "preset:weight" because NSUserDefaults arrays of dictionaries are noisy to
// version; a string either parses or the mix is simply absent.
static NSString *const kMixMode = @"phosphorMixMode";
static NSString *const kMixBlend = @"phosphorMixBlend";        // "6:2,15:1"
static NSString *const kMixInkFrom = @"phosphorMixInkFrom";
static NSString *const kMixPaperFrom = @"phosphorMixPaperFrom";
static NSString *const kMixTrailFrom = @"phosphorMixTrailFrom";
static NSString *const kMixFlash = @"phosphorMixFlash";
static NSString *const kMixPersist = @"phosphorMixPersist";
static NSString *const kMixActive = @"phosphorMixActive";

// Custom-slot hex fields the palette pipeline already reads (CrossPointPrefs
// parses them exactly as Settings.app writes them).
static NSString *const kInkLight = @"panelInkLight";
static NSString *const kPaperLight = @"panelPaperLight";
static NSString *const kInkDark = @"panelInkDark";
static NSString *const kPaperDark = @"panelPaperDark";

namespace {

NSString *hexOf(const unsigned char c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
}

UIColor *colorOf(const unsigned char c[3]) {
  return [UIColor colorWithRed:c[0] / 255.0 green:c[1] / 255.0 blue:c[2] / 255.0 alpha:1];
}

NSString *trailLabel(float ms) {
  if (ms <= 0.0f) return @"no glow";
  if (ms >= 1000.0f) return [NSString stringWithFormat:@"%.1f s fade", ms / 1000.0];
  return [NSString stringWithFormat:@"%.0f ms fade", ms];
}

// The current blend components, parsed from the store.
int loadBlend(phosphormix::Component *out, int cap) {
  NSString *csv = [[NSUserDefaults standardUserDefaults] stringForKey:kMixBlend];
  if (!csv.length) return 0;
  int n = 0;
  for (NSString *pair in [csv componentsSeparatedByString:@","]) {
    if (n >= cap) break;
    NSArray<NSString *> *kv = [pair componentsSeparatedByString:@":"];
    if (kv.count != 2) continue;
    const int preset = kv[0].intValue;
    if (!phosphormix::isMixablePreset(preset)) continue;   // stale premix, drop
    out[n].preset = preset;
    out[n].weight = MAX(1, MIN(9, kv[1].intValue));
    n++;
  }
  return n;
}

void saveBlend(const phosphormix::Component *comps, int n) {
  NSMutableArray *parts = [NSMutableArray array];
  for (int i = 0; i < n; i++)
    [parts addObject:[NSString stringWithFormat:@"%d:%d", comps[i].preset,
                                                comps[i].weight]];
  [[NSUserDefaults standardUserDefaults]
      setObject:[parts componentsJoinedByString:@","]
         forKey:kMixBlend];
}

// Compute the live mix from the store, whatever mode it is in.
phosphormix::Result computeStoredMix() {
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  const int mode = (int)[d integerForKey:kMixMode];
  if (mode == phosphormix::Parts)
    return phosphormix::mixParts((int)[d integerForKey:kMixInkFrom],
                                 (int)[d integerForKey:kMixPaperFrom],
                                 (int)[d integerForKey:kMixTrailFrom]);
  if (mode == phosphormix::Cascade)
    return phosphormix::mixCascade((int)[d integerForKey:kMixFlash],
                                   (int)[d integerForKey:kMixPersist]);
  phosphormix::Component comps[phosphormix::kMaxComponents];
  const int n = loadBlend(comps, phosphormix::kMaxComponents);
  return phosphormix::mixBlend(comps, n);
}

// Write the mix into the Custom slot and select it. This is the ONLY writer of
// the four hex fields outside Settings.app, and it goes through the same keys
// so the pipeline cannot tell the difference.
void applyStoredMix() {
  const phosphormix::Result r = computeStoredMix();
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  [d setObject:hexOf(r.light.ink) forKey:kInkLight];
  [d setObject:hexOf(r.light.paper) forKey:kPaperLight];
  [d setObject:hexOf(r.dark.ink) forKey:kInkDark];
  [d setObject:hexOf(r.dark.paper) forKey:kPaperDark];
  [d setBool:YES forKey:kMixActive];
  CrossPointPrefs_setPanelPalettePreset(panelpalette::kPresetCustom);
  // The preset integer may not have moved (editing a mix while already on
  // Custom), so tell the glow poll its dedupe is stale.
  CrossPointMixer_glowChanged();
  SimulatorOverlay::requestPresent();
  crosspointRequestRender();
}

}  // namespace

// The glow branch for the Custom slot, called from pollPanelGlow: a mix has a
// trail of its own where plain Custom has none. Returns false when no mix is
// active, and the caller falls back to trail 0.
extern "C" bool CrossPointMixer_glowForCustom(float *trailMs,
                                              unsigned char tail[3],
                                              bool *hasTail) {
  if (![[NSUserDefaults standardUserDefaults] boolForKey:kMixActive]) return false;
  const phosphormix::Result r = computeStoredMix();
  *trailMs = r.trailMs;
  *hasTail = r.hasTail;
  for (int c = 0; c < 3; c++) tail[c] = r.tail[c];
  return true;
}

// --- the swatch row --------------------------------------------------------
// One phosphor, exactly as the owner asked to see it: four color chips (dark
// ink, dark paper, light ink, light paper) with their hex values, the name, and
// the time to fade.

@interface CPXSwatchCell : UITableViewCell
@property(nonatomic, strong) NSMutableArray<UIView *> *chips;
@property(nonatomic, strong) NSMutableArray<UILabel *> *hexes;
@property(nonatomic, strong) UILabel *name;
@property(nonatomic, strong) UILabel *fade;
@property(nonatomic, strong) UISlider *weight;      // blend rows only
@property(nonatomic, copy) void (^onWeight)(int);
@end

@implementation CPXSwatchCell
- (instancetype)initWithStyle:(UITableViewCellStyle)style
              reuseIdentifier:(NSString *)reuse {
  self = [super initWithStyle:style reuseIdentifier:reuse];
  if (!self) return nil;
  _name = [UILabel new];
  _name.font = [UIFont monospacedSystemFontOfSize:14 weight:UIFontWeightSemibold];
  _fade = [UILabel new];
  _fade.font = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightRegular];
  _fade.textColor = UIColor.secondaryLabelColor;
  _chips = [NSMutableArray array];
  _hexes = [NSMutableArray array];
  for (int i = 0; i < 4; i++) {
    UIView *chip = [UIView new];
    chip.layer.cornerRadius = 4;
    chip.layer.borderWidth = 1;
    chip.layer.borderColor = UIColor.separatorColor.CGColor;
    [_chips addObject:chip];
    [self.contentView addSubview:chip];
    UILabel *hex = [UILabel new];
    hex.font = [UIFont monospacedSystemFontOfSize:9 weight:UIFontWeightRegular];
    hex.textColor = UIColor.secondaryLabelColor;
    hex.textAlignment = NSTextAlignmentCenter;
    [_hexes addObject:hex];
    [self.contentView addSubview:hex];
  }
  _weight = [UISlider new];
  _weight.minimumValue = 1;
  _weight.maximumValue = 9;
  _weight.hidden = YES;
  [_weight addTarget:self action:@selector(weightMoved)
     forControlEvents:UIControlEventValueChanged];
  [self.contentView addSubview:_name];
  [self.contentView addSubview:_fade];
  [self.contentView addSubview:_weight];
  return self;
}

- (void)weightMoved {
  if (self.onWeight) self.onWeight((int)lroundf(self.weight.value));
}

- (void)layoutSubviews {
  [super layoutSubviews];
  const CGFloat W = self.contentView.bounds.size.width;
  self.name.frame = CGRectMake(16, 8, W - 140, 18);
  self.fade.frame = CGRectMake(W - 120, 10, 104, 14);
  // four chips in a row: dark ink, dark paper, light ink, light paper
  const CGFloat chipW = 44, gap = 8, y = 32;
  CGFloat x = 16;
  for (int i = 0; i < 4; i++) {
    self.chips[i].frame = CGRectMake(x, y, chipW, 22);
    self.hexes[i].frame = CGRectMake(x - 4, y + 24, chipW + 8, 12);
    x += chipW + gap;
  }
  if (!self.weight.hidden)
    self.weight.frame = CGRectMake(x + 8, y + 4, W - x - 28, 30);
}

- (void)fillWithPreset:(int)preset info:(const panelpalette::PresetInfo *)info {
  using panelpalette::resolve;
  const panelpalette::Palette d = resolve(preset, true, -1, -1);
  const panelpalette::Palette l = resolve(preset, false, -1, -1);
  const unsigned char *tones[4] = {d.ink, d.paper, l.ink, l.paper};
  static const char *roles[4] = {"D ink", "D paper", "L ink", "L paper"};
  for (int i = 0; i < 4; i++) {
    self.chips[i].backgroundColor = colorOf(tones[i]);
    self.hexes[i].text =
        [NSString stringWithFormat:@"%s %@", roles[i], hexOf(tones[i])];
  }
  self.name.text =
      info ? [NSString stringWithFormat:@"%s %s", info->phosphor ? info->phosphor : "",
                                        info->name]
           : @"?";
  self.fade.text = trailLabel(panelpalette::trailMsForPreset(preset));
  self.fade.textAlignment = NSTextAlignmentRight;
}
@end

// --- the controller --------------------------------------------------------

typedef NS_ENUM(NSInteger, CPXMixerTab) {
  CPXTabPresets = 0,   // every preset, including premixes, selectable as-is
  CPXTabBlend,
  CPXTabParts,
  CPXTabCascade,
};

@interface CPXMixerController
    : UITableViewController <UIAdaptivePresentationControllerDelegate>
@property(nonatomic) CPXMixerTab tab;
@property(nonatomic) int partsRole;      // 0 ink, 1 paper, 2 trail
@property(nonatomic) int cascadeRole;    // 0 flash, 1 persist
@end

@implementation CPXMixerController {
  // The ingredient shelf: every pure phosphor row, grouped by persistence band
  // (owner ruling 2026-08-21: "group ingredient shelf by natural breaks of
  // persistence fade"). Within a band, kPresetInfo order.
  std::vector<int> _shelf[phosphormix::kTrailBandCount];
  // The premixes, offered as preset mixes (owner ruling: not ingredients).
  std::vector<int> _premix;
  // Everything, for the Presets tab (kPresetInfo order = picker order).
  std::vector<int> _all;
}

- (instancetype)init {
  self = [super initWithStyle:UITableViewStyleInsetGrouped];
  if (!self) return nil;
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const auto &info = panelpalette::kPresetInfo[i];
    _all.push_back(info.preset);
    if (!info.phosphor) continue;
    if (phosphormix::isPremixPhosphor(info.phosphor))
      _premix.push_back(info.preset);
    else
      _shelf[phosphormix::trailBand(
                 panelpalette::trailMsForPreset(info.preset))]
          .push_back(info.preset);
  }
  self.tab = (CPXMixerTab)([[NSUserDefaults standardUserDefaults]
                               boolForKey:kMixActive]
                               ? [[NSUserDefaults standardUserDefaults]
                                     integerForKey:kMixMode] + 1
                               : CPXTabPresets);
  self.title = @"Page Color";
  return self;
}

- (void)viewDidLoad {
  [super viewDidLoad];
  [self.tableView registerClass:CPXSwatchCell.class forCellReuseIdentifier:@"sw"];
  UILongPressGestureRecognizer *lp = [[UILongPressGestureRecognizer alloc]
      initWithTarget:self action:@selector(longPressed:)];
  [self.tableView addGestureRecognizer:lp];
  self.tableView.rowHeight = 74;
  UISegmentedControl *seg = [[UISegmentedControl alloc]
      initWithItems:@[ @"Presets", @"Blend", @"Parts", @"Cascade" ]];
  seg.selectedSegmentIndex = self.tab;
  [seg addTarget:self action:@selector(tabChanged:)
      forControlEvents:UIControlEventValueChanged];
  self.navigationItem.titleView = seg;
  self.navigationItem.rightBarButtonItem = [[UIBarButtonItem alloc]
      initWithBarButtonSystemItem:UIBarButtonSystemItemDone
                           target:self
                           action:@selector(done)];
}

- (void)done {
  [self dismissViewControllerAnimated:YES completion:nil];
}

- (void)tabChanged:(UISegmentedControl *)seg {
  self.tab = (CPXMixerTab)seg.selectedSegmentIndex;
  if (self.tab != CPXTabPresets) {
    [[NSUserDefaults standardUserDefaults] setInteger:self.tab - 1 forKey:kMixMode];
    applyStoredMix();
  }
  [self.tableView reloadData];
}

// Long-press on a preset-mix row loads its recipe into the mixer (owner
// ruling 2026-08-20: "Both — tap applies, long-press loads"). The mapping is
// approximate by construction -- see kPremixRecipes -- and the footer says so.
- (void)longPressed:(UILongPressGestureRecognizer *)g {
  if (g.state != UIGestureRecognizerStateBegan) return;
  if (self.tab != CPXTabPresets) return;
  NSIndexPath *ip = [self.tableView
      indexPathForRowAtPoint:[g locationInView:self.tableView]];
  if (!ip || ip.section != 1) return;
  const int preset = [self presetAt:ip];
  const panelpalette::PresetInfo *info = [self infoFor:preset];
  const phosphormix::PremixRecipe *r =
      phosphormix::recipeFor(info ? info->phosphor : nullptr);
  if (!r) return;
  // Resolve the component P-numbers to preset integers through kPresetInfo.
  int pa = -1, pb = -1, pc = -1;
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const char *ph = panelpalette::kPresetInfo[i].phosphor;
    if (!ph) continue;
    if (!strcmp(ph, r->a)) pa = panelpalette::kPresetInfo[i].preset;
    if (!strcmp(ph, r->b)) pb = panelpalette::kPresetInfo[i].preset;
    if (r->c && !strcmp(ph, r->c)) pc = panelpalette::kPresetInfo[i].preset;
  }
  if (pa < 0 || pb < 0 || (r->c && pc < 0)) return;
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  if (r->mode == phosphormix::Cascade) {
    [d setInteger:pa forKey:kMixFlash];
    [d setInteger:pb forKey:kMixPersist];
    [d setInteger:phosphormix::Cascade forKey:kMixMode];
    self.tab = CPXTabCascade;
  } else {
    phosphormix::Component comps[3] = {{pa, r->weightA}, {pb, r->weightB},
                                       {pc, r->weightC}};
    saveBlend(comps, pc >= 0 ? 3 : 2);
    [d setInteger:phosphormix::Blend forKey:kMixMode];
    self.tab = CPXTabBlend;
  }
  applyStoredMix();
  UISegmentedControl *seg = (UISegmentedControl *)self.navigationItem.titleView;
  if ([seg isKindOfClass:UISegmentedControl.class])
    seg.selectedSegmentIndex = self.tab;
  [self.tableView reloadData];
  SDL_Log("[mixer] recipe %s loaded -> %s", info->phosphor,
          r->mode == phosphormix::Cascade ? "cascade" : "blend");
}

// --- table shape -----------------------------------------------------------

- (NSInteger)numberOfSectionsInTableView:(UITableView *)tv {
  switch (self.tab) {
    case CPXTabPresets: return 2;             // presets, then preset mixes
    case CPXTabBlend: return phosphormix::kTrailBandCount;
    case CPXTabParts: return 1 + phosphormix::kTrailBandCount;
    case CPXTabCascade: return 1 + phosphormix::kTrailBandCount;
  }
  return 1;
}

- (NSString *)tableView:(UITableView *)tv titleForHeaderInSection:(NSInteger)s {
  switch (self.tab) {
    case CPXTabPresets:
      return s == 0 ? @"Presets"
                    : @"Preset mixes — already blends or cascades, picked whole";
    case CPXTabBlend:
      return s == 0
                 ? [NSString stringWithFormat:
                       @"Blend — up to 4 phosphors, slider weights · %s",
                       phosphormix::trailBandName(0)]
                 : @(phosphormix::trailBandName((int)s));
    case CPXTabParts: {
      if (s == 0)
        return self.partsRole == 0
                   ? @"Pick the INK phosphor"
                   : self.partsRole == 1 ? @"Pick the PAPER phosphor"
                                         : @"Pick the FADE phosphor";
      return @(phosphormix::trailBandName((int)s - 1));
    }
    case CPXTabCascade: {
      if (s == 0)
        return self.cascadeRole == 0
                   ? @"Pick the FLASH layer — it paints the page"
                   : @"Pick the PERSISTENCE layer — it lingers";
      return @(phosphormix::trailBandName((int)s - 1));
    }
  }
  return nil;
}

- (NSString *)tableView:(UITableView *)tv titleForFooterInSection:(NSInteger)sec {
  if (self.tab == CPXTabPresets && sec == 1)
    return @"Long-press a preset mix to load it into the mixer as an editable "
           @"recipe. The recipe maps its compounds to the nearest pure "
           @"phosphors, so it is a starting point, not an exact reproduction.";
  return nil;
}

- (NSInteger)tableView:(UITableView *)tv numberOfRowsInSection:(NSInteger)s {
  switch (self.tab) {
    case CPXTabPresets: return s == 0 ? (NSInteger)(_all.size() - _premix.size())
                                      : (NSInteger)_premix.size();
    case CPXTabBlend: return (NSInteger)_shelf[s].size();
    case CPXTabParts: return s == 0 ? 1 : (NSInteger)_shelf[s - 1].size();
    case CPXTabCascade: return s == 0 ? 1 : (NSInteger)_shelf[s - 1].size();
  }
  return 0;
}

- (const panelpalette::PresetInfo *)infoFor:(int)preset {
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++)
    if (panelpalette::kPresetInfo[i].preset == preset)
      return &panelpalette::kPresetInfo[i];
  return nullptr;
}

- (int)presetAt:(NSIndexPath *)ip {
  switch (self.tab) {
    case CPXTabPresets: {
      if (ip.section == 1) return _premix[ip.row];
      // presets minus premixes, keeping order
      NSInteger n = -1;
      for (int p : _all) {
        bool isPre = false;
        for (int q : _premix) if (q == p) { isPre = true; break; }
        if (isPre) continue;
        if (++n == ip.row) return p;
      }
      return _all[0];
    }
    case CPXTabBlend:
      return _shelf[ip.section][ip.row];
    default:
      return _shelf[ip.section - 1][ip.row];
  }
}

- (UITableViewCell *)tableView:(UITableView *)tv
         cellForRowAtIndexPath:(NSIndexPath *)ip {
  // The role-picker row on Parts/Cascade
  if ((self.tab == CPXTabParts || self.tab == CPXTabCascade) && ip.section == 0) {
    UITableViewCell *cell =
        [tv dequeueReusableCellWithIdentifier:@"role"]
            ?: [[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle
                                      reuseIdentifier:@"role"];
    NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
    if (self.tab == CPXTabParts) {
      const panelpalette::PresetInfo *ink = [self infoFor:(int)[d integerForKey:kMixInkFrom]];
      const panelpalette::PresetInfo *pap = [self infoFor:(int)[d integerForKey:kMixPaperFrom]];
      const panelpalette::PresetInfo *tr = [self infoFor:(int)[d integerForKey:kMixTrailFrom]];
      cell.textLabel.text = [NSString
          stringWithFormat:@"ink %s · paper %s · fade %s",
                           ink && ink->phosphor ? ink->phosphor : "—",
                           pap && pap->phosphor ? pap->phosphor : "—",
                           tr && tr->phosphor ? tr->phosphor : "—"];
      cell.detailTextLabel.text = @"Tap to switch which role you are picking";
    } else {
      const panelpalette::PresetInfo *fl = [self infoFor:(int)[d integerForKey:kMixFlash]];
      const panelpalette::PresetInfo *pe = [self infoFor:(int)[d integerForKey:kMixPersist]];
      cell.textLabel.text = [NSString
          stringWithFormat:@"flash %s · persistence %s",
                           fl && fl->phosphor ? fl->phosphor : "—",
                           pe && pe->phosphor ? pe->phosphor : "—"];
      cell.detailTextLabel.text = @"Tap to switch which layer you are picking";
    }
    cell.textLabel.font = [UIFont monospacedSystemFontOfSize:13 weight:UIFontWeightMedium];
    return cell;
  }

  CPXSwatchCell *cell = [tv dequeueReusableCellWithIdentifier:@"sw"];
  const int preset = [self presetAt:ip];
  [cell fillWithPreset:preset info:[self infoFor:preset]];

  cell.weight.hidden = YES;
  cell.onWeight = nil;
  cell.accessoryType = UITableViewCellAccessoryNone;

  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  if (self.tab == CPXTabPresets) {
    const int current =
        panelpalette::migratePreset(CrossPointPrefs_panelPalettePreset());
    if (preset == current)
      cell.accessoryType = UITableViewCellAccessoryCheckmark;
  } else if (self.tab == CPXTabBlend) {
    phosphormix::Component comps[phosphormix::kMaxComponents];
    const int n = loadBlend(comps, phosphormix::kMaxComponents);
    for (int i = 0; i < n; i++) {
      if (comps[i].preset != preset) continue;
      cell.accessoryType = UITableViewCellAccessoryCheckmark;
      cell.weight.hidden = NO;
      cell.weight.value = comps[i].weight;
      cell.onWeight = ^(int w) {
        phosphormix::Component cc[phosphormix::kMaxComponents];
        const int m = loadBlend(cc, phosphormix::kMaxComponents);
        for (int j = 0; j < m; j++)
          if (cc[j].preset == preset) cc[j].weight = w;
        saveBlend(cc, m);
        applyStoredMix();
      };
    }
  } else if (self.tab == CPXTabParts) {
    const int sel = (int)[d integerForKey:self.partsRole == 0
                                              ? kMixInkFrom
                                              : self.partsRole == 1 ? kMixPaperFrom
                                                                    : kMixTrailFrom];
    if (preset == sel) cell.accessoryType = UITableViewCellAccessoryCheckmark;
  } else if (self.tab == CPXTabCascade) {
    const int sel = (int)[d
        integerForKey:self.cascadeRole == 0 ? kMixFlash : kMixPersist];
    if (preset == sel) cell.accessoryType = UITableViewCellAccessoryCheckmark;
  }
  return cell;
}

- (void)tableView:(UITableView *)tv didSelectRowAtIndexPath:(NSIndexPath *)ip {
  [tv deselectRowAtIndexPath:ip animated:YES];
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];

  if ((self.tab == CPXTabParts || self.tab == CPXTabCascade) && ip.section == 0) {
    if (self.tab == CPXTabParts) self.partsRole = (self.partsRole + 1) % 3;
    else self.cascadeRole = (self.cascadeRole + 1) % 2;
    [tv reloadData];
    return;
  }

  const int preset = [self presetAt:ip];
  switch (self.tab) {
    case CPXTabPresets:
      // A preset -- or a preset MIX -- picked whole. Leaves the mix stored but
      // inactive, so coming back to a mix tab restores it.
      [d setBool:NO forKey:kMixActive];
      CrossPointPrefs_setPanelPalettePreset(preset);
      SimulatorOverlay::requestPresent();
      crosspointRequestRender();
      break;
    case CPXTabBlend: {
      phosphormix::Component comps[phosphormix::kMaxComponents];
      int n = loadBlend(comps, phosphormix::kMaxComponents);
      int at = -1;
      for (int i = 0; i < n; i++)
        if (comps[i].preset == preset) at = i;
      if (at >= 0) {           // deselect
        for (int i = at; i < n - 1; i++) comps[i] = comps[i + 1];
        n--;
      } else if (n < phosphormix::kMaxComponents) {
        comps[n].preset = preset;
        comps[n].weight = 3;
        n++;
      }
      saveBlend(comps, n);
      [d setInteger:phosphormix::Blend forKey:kMixMode];
      applyStoredMix();
      break;
    }
    case CPXTabParts:
      [d setInteger:preset
             forKey:self.partsRole == 0 ? kMixInkFrom
                    : self.partsRole == 1 ? kMixPaperFrom : kMixTrailFrom];
      [d setInteger:phosphormix::Parts forKey:kMixMode];
      applyStoredMix();
      break;
    case CPXTabCascade:
      [d setInteger:preset forKey:self.cascadeRole == 0 ? kMixFlash : kMixPersist];
      [d setInteger:phosphormix::Cascade forKey:kMixMode];
      applyStoredMix();
      break;
  }
  [tv reloadData];
}
@end

// --- entry point -----------------------------------------------------------

extern "C" void CrossPointMixer_present(void) {
  dispatch_async(dispatch_get_main_queue(), ^{
    int count = 0;
    SDL_Window **wins = SDL_GetWindows(&count);
    SDL_Window *win = (wins && count > 0) ? wins[0] : nullptr;
    SDL_free(wins);
    if (!win) return;
    UIWindow *uiWindow = (__bridge UIWindow *)SDL_GetPointerProperty(
        SDL_GetWindowProperties(win), SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER, nullptr);
    UIViewController *root = uiWindow.rootViewController;
    if (!root || root.presentedViewController) return;
    CPXMixerController *mixer = [CPXMixerController new];
    UINavigationController *nav =
        [[UINavigationController alloc] initWithRootViewController:mixer];
    nav.modalPresentationStyle = UIModalPresentationPageSheet;
    if (nav.sheetPresentationController) {
      nav.sheetPresentationController.detents = @[
        UISheetPresentationControllerDetent.mediumDetent,
        UISheetPresentationControllerDetent.largeDetent
      ];
      // Medium first: the page stays visible behind the sheet, which is the
      // whole point of a LIVE mixer.
      nav.sheetPresentationController.selectedDetentIdentifier =
          UISheetPresentationControllerDetentIdentifierMedium;
    }
    [root presentViewController:nav animated:YES completion:nil];
  });
}
