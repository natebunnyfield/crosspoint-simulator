// The page-color modal: the four-gun (RGBW) mixer.
//
// NOTHING ON THE PHONE OPENS THIS DRAWER, since 2026-08-24. The page-color chip
// beside POWER was removed from the pad by owner ruling ("remove the color
// button from single finger (not zen) mode ui"), and the dark page is frozen at
// the four-gun blend he chose in this very mixer -- P38 at 19, P45 at 88, P20
// at 17, P22R at 36, which resolves to CFD4CC on 171B1B with a 1095 ms fade
// (src/FrozenPage.h). THE ENTRY POINT WAS REMOVED, NOT THIS FILE: it is still
// compiled and still opened by CROSSPOINT_SIM_OPEN_MIXER for a headless QA run.
// "For now" is explicitly reversible and this drawer is what there would be to
// go back to.
//
// BUT IT NO LONGER DRIVES THE PAGE, and saying so is the point of this
// paragraph. applyGuns writes panelInkDark / panelPaperDark /
// phosphorMixActive and asks for a present, while the render reads
// crosspoint::panelStoreFromPrefs(), which since the freeze consults the store
// for none of them -- so a gun move updates this drawer's own swatches and its
// local preview, and leaves the page alone. That is the freeze working, not a
// rendering bug, and unfreezing is one function body in ios/PanelPrefs.h.
// An earlier version of this comment claimed the drawer was "still correct",
// which was wrong and would have sent the next reader hunting a bug that is
// not there. Found by adversarial review, 2026-08-24.
//
// gunstore::load is frozen to that recipe, so opening it shows the page the
// owner is looking at; gunstore::save still writes, and nothing reads what it
// writes while the freeze holds.
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
// Storage: ios/GunStore.h. phosphorGunAssign is the CSV of four assigned preset
// ints; phosphorMixBlend stays the mix of record, the same "preset:weight" CSV
// as before (weight-0 guns included) -- so a mix built here reads back on the
// desktop through settings.json exactly as before, and old stored mixes from
// the removed UI still compute (the core kept every mode; only the UI
// narrowed).
//
// Owner's device crash (build 110, iOS 26.6) note carried forward: NO
// self.title anywhere in this controller -- and none on the navigationItem
// either. objc_retain(0x1) inside UIKit's setTitle: was the crash site,
// sidestepped in build 111; this rewrite keeps the sidestep.

#import <QuartzCore/QuartzCore.h>  // CACurrentMediaTime, for the rebuild-cost log
#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <atomic>
#include <vector>

#include "CrossPointPresetList.h"

#include "GunMixCsv.h"
#include "GunStore.h"
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
// THE TWO GUN KEYS ARE NOT NAMED HERE ANY MORE. They moved to ios/GunStore.h
// on 2026-08-23, when preset selection gained a second, legitimate reason to
// write them (it seeds the guns to match the preset chosen). One reader and one
// writer for that pair, in a file that decides nothing -- the lesson of the
// same day's P1.
static NSString *const kMixActive = @"phosphorMixActive";
// THE LIGHT PAGE'S TWO KEYS ARE DELIBERATELY NOT NAMED IN THIS FILE, and
// tests/panel_source_test.py fails if they come back. This is DARK mode's
// editor (2026-08-22 doctrine, docs/light-ink-picker.md); writing the light
// pair from here is the owner's P1 of 2026-08-23. The one legal exception --
// freezing the light page once, when this editor claims the shared Custom
// slot -- goes through CrossPointPrefs_claimCustomFor, so it cannot be done
// two different ways in two files.
static NSString *const kInkDark = @"panelInkDark";
static NSString *const kPaperDark = @"panelPaperDark";

namespace {

constexpr int kGunCount = 4;
static_assert(kGunCount == gunmix::kGunCount,
              "the mixer's gun count and the CSV codec's must agree");

// The channel labels: the industry-standard four-emitter scheme.
constexpr const char *kGunLabel[kGunCount] = {"R", "G", "B", "W"};

// Slider range. 0 = that gun off (component omitted); the core clamps weights
// below 1, so omission is the only honest zero.
constexpr int kWeightMax = 100;
static_assert(kWeightMax == gunmix::kWeightMax,
              "the slider's ceiling and the codec's clamp must agree");

// The channel scheme and its shipped starting recipe live in the core now
// (phosphormix::kDefaultGunPreset / kDefaultGunWeight), because seedForPreset
// has to be able to fill a slot the store cannot supply and a second copy of a
// default set is a second opinion about what an unwritten key means.

// Samples along a gradient track. The mix is smooth in the weight, so 16
// stops interpolated by CoreGraphics are indistinguishable from per-pixel.
constexpr int kGradientSamples = 16;

// The FACETS each gun's track previews, stacked top to bottom inside the one
// 16 pt bar (owner 2026-08-22: "the gun mixer needs multiple preview gradient
// for each gun, not just the paper or whatever one it currently has"). The
// order is the LIFE OF A GLYPH, which is the only ordering that needs no
// labels once you know it:
//
//   band 0  dark INK    the lit glyph at the instant the beam paints it
//   band 1  dark TAIL   the color the afterglow hands over to as it decays
//   band 2  dark PAPER  the unlit ground it settles back into
//
// All three are the DARK appearance, for the same reason the single gradient
// was: a CRT page is a dark-mode object. The light pair gets no fourth band
// because it is not this editor's page at all -- the 2026-08-22 doctrine split
// gave light its own ink picker, and this editor only FREEZES the light pair it
// finds (see claimCustomFor below). Previewing a rendition the light page will
// never show is what the dropped light swatch did, owner 2026-08-23.
//
// Why TAIL earns a band the other two cannot supply: the tail is normalized by
// the FULL mix weight, so raising a FAST gun steals emission share from the
// slow survivor and dims the afterglow, while ink and paper barely move. That
// is the one thing about a mix a static pair of swatches cannot show.
constexpr int kTrackBands = 3;

// Left transparent between bands so the sheet's own background shows through:
// black between bands in dark appearance, white in light, which is the correct
// separator in both without a second dynamic color to keep re-resolved.
constexpr CGFloat kBandGapPt = 0.5f;

NSString *hexOf(const unsigned char c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
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
  NSUserDefaults *d = [NSUserDefaults standardUserDefaults];
  gunstore::save(presets, w);

  // CLAIM THE CUSTOM SLOT FOR DARK, which freezes LIGHT first.
  //
  // THIS IS THE OWNER'S P1 OF 2026-08-23 ("ink is not being picked up"). Until
  // it was written, the four lines below were SIX: this function also wrote
  // r.light.ink and r.light.paper. That was correct while the mixer was the
  // editor for both polarities, and became the bug on 2026-08-22 when the
  // doctrine split them -- light is paper and ink with its own historical-ink
  // picker, dark is the CRT and keeps this mixer (docs/light-ink-picker.md,
  // which says in as many words that this file "remains dark mode's picker").
  // The split moved the chip's branch and left this write, so every gun move in
  // dark mode silently overwrote the light page's chosen ink. Measured: an
  // applied Payne's Gray (the light ink field 323D47, page text (30,37,43))
  // became
  // 6E0500 and (64,3,0) after one gun move, with lightInkIndex still reading 15.
  //
  // The freeze is the mirror image of the ink picker's, through the same shared
  // rule, so neither editor can be updated without the other being obviously
  // wrong. src/PanelSource.h.
  CrossPointPrefs_claimCustomFor(/*editingDark=*/1);

  // DARK ONLY, from here down.
  const phosphormix::Result r = computeGuns(presets, w);
  [d setObject:hexOf(r.dark.ink) forKey:kInkDark];
  [d setObject:hexOf(r.dark.paper) forKey:kPaperDark];
  [d setBool:YES forKey:kMixActive];
  CrossPointMixer_glowChanged();
  SimulatorOverlay::requestPresent();
  if (renderPage) crosspointRequestRender();
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
// contract from the previous UI: the mix computes through the core.
//
// THE `kMixActive` GATE IS GONE, 2026-08-24. The dark page is frozen at a
// four-gun blend (src/FrozenPage.h), and ios/PanelPrefs.h says so
// unconditionally -- so the store's flag no longer decides anything, and
// reading it here would have answered NO on any install that never touched the
// mixer: correct tones, dead tube, 0 ms trail. gunstore::load is frozen to the
// same recipe, so this returns the frozen decay (1095 ms, handing over to a
// 613B27 tail at 400 ms) without consulting NSUserDefaults at all.
extern "C" bool CrossPointMixer_glowForCustom(float *trailMs,
                                              unsigned char tail[3],
                                              bool *hasTail,
                                              float *tailOnsetMs) {
  int presets[kGunCount];
  int w[kGunCount];
  gunstore::load(presets, w);
  const phosphormix::Result r = computeGuns(presets, w);
  *trailMs = r.trailMs;
  *hasTail = r.hasTail;
  for (int c = 0; c < 3; c++) tail[c] = r.tail[c];
  if (tailOnsetMs) *tailOnsetMs = r.tailOnsetMs;
  return true;
}

// --- the controller ---------------------------------------------------------

// The sheet's live presentation state, for the input layers underneath. The
// sheet is a pageSheet with an undimmed medium detent, so UIKit passes every
// touch OUTSIDE the sheet through to the presenting (SDL) view — the shim's
// finger paths and the zen recognizers ask this before acting (2026-08-21
// input-lifecycle audit, finding #6). Touches ON the sheet's own controls
// never reach SDL, so slider drags need no exemption. Atomic because the
// askers sit on the SDL/firmware loop.
static std::atomic<bool> g_mixerPresented{false};

extern "C" bool CrossPointMixer_isPresented(void) {
  return g_mixerPresented.load();
}

@interface CPXGunMixerController : UIViewController
// Declared so the presenter's completion block can drive the diagnostic push
// (CROSSPOINT_SIM_OPEN_PRESETS); the bar button reaches it by selector.
- (void)showPresets;
@end

@implementation CPXGunMixerController {
  UIButton *_name[kGunCount];
  UISlider *_slider[kGunCount];
  // The LIVE GRADIENT track (owner-approved 2026-08-22): each gun's track
  // previews the actual resulting mix at every position of that slider,
  // computed through the shipped core (computeGuns -> phosphormix::mixBlend)
  // exactly like the readout swatches. THREE stacked facet bands per track --
  // ink, tail, paper, see kTrackBands. A UISlider track IMAGE cannot do this
  // continuously -- UIKit stretches the minimum-track image into the segment
  // left of the thumb, so the gradient would compress as the thumb moves --
  // so the gradient lives in a UIImageView placed on the slider's own track
  // rect, and the slider's min/max track images are transparent.
  UIImageView *_track[kGunCount];
  UILabel *_value[kGunCount];
  UIView *_swatchDark;
  UILabel *_readout;
  int _presets[kGunCount];
  int _w[kGunCount];
  CGFloat _trackWidth;  // last width the gradients were built at
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
  // PRESETS, opposite Done, and the same control the ink picker carries. A bar
  // button rather than a row because this sheet has no vertical space to give:
  // it is pinned to the medium detent with no grabber (owner 2026-08-21), and
  // the four guns, the swatches and the readout already fill it. Pushing onto
  // the nav controller keeps that pin intact -- no detent moves.
  self.navigationItem.leftBarButtonItem =
      [[UIBarButtonItem alloc] initWithTitle:@"Presets"
                                       style:UIBarButtonItemStylePlain
                                      target:self
                                      action:@selector(showPresets)];

  gunstore::load(_presets, _w);

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

    _track[g] = [UIImageView new];
    _track[g].userInteractionEnabled = NO;
    _track[g].clipsToBounds = YES;
    // Shows through the transparent gaps between the facet bands. A dynamic
    // UIColor on a UIView DOES re-resolve on an appearance flip (unlike the
    // flattened CGColors on the swatch borders below), so this one needs no
    // trait handler.
    _track[g].backgroundColor = UIColor.systemBackgroundColor;
    [self.view addSubview:_track[g]];

    _slider[g] = [UISlider new];
    _slider[g].minimumValue = 0;
    _slider[g].maximumValue = kWeightMax;
    _slider[g].value = _w[g];
    _slider[g].tag = g;
    // Transparent system track, both halves: the gradient underlay IS the
    // track. (This also supersedes the old per-gun minimumTrackTintColor.)
    static UIImage *clearTrack;
    static dispatch_once_t clearOnce;
    dispatch_once(&clearOnce, ^{
      UIGraphicsImageRenderer *r = [[UIGraphicsImageRenderer alloc]
          initWithSize:CGSizeMake(1, 1)];
      clearTrack = [r imageWithActions:^(UIGraphicsImageRendererContext *c){}];
    });
    [_slider[g] setMinimumTrackImage:clearTrack forState:UIControlStateNormal];
    [_slider[g] setMaximumTrackImage:clearTrack forState:UIControlStateNormal];
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

  // The computed DARK ground, with exact hex below it. The page behind the
  // sheet is the real preview; this is the number.
  //
  // There is deliberately no LIGHT swatch (owner 2026-08-23, "drop the light
  // swatch entirely"). It used to sit beside this one and preview the blend's
  // light rendition, which was honest while this sheet owned both polarities.
  // Since the doctrine split it has been a preview of a page that will never
  // render: light is the ink picker's, and the moment this editor claims the
  // Custom slot it FREEZES the light pair rather than computing one.
  _swatchDark = [UIView new];
  _swatchDark.layer.cornerRadius = 8;
  _swatchDark.layer.borderWidth = 1;
  _swatchDark.layer.borderColor = UIColor.separatorColor.CGColor;
  [self.view addSubview:_swatchDark];

  // A CGColor never re-resolves: separatorColor was flattened at creation, so
  // an appearance flip while the sheet is up kept the stale border -- the
  // keyboard-bar-chip bug, one file over (CrossPointKeyboardBar_refreshTint).
  // Re-push it on every color-appearance change. registerForTraitChanges is
  // the iOS 17+ replacement for traitCollectionDidChange:; the deployment
  // target is 26.0. Self arrives as the handler's parameter, so nothing is
  // captured and there is no retain cycle.
  [self registerForTraitChanges:@[ UITraitUserInterfaceStyle.class ]
                    withHandler:^(CPXGunMixerController *vc,
                                  UITraitCollection *previous) {
                      CGColorRef border =
                          [UIColor.separatorColor
                              resolvedColorWithTraitCollection:vc.traitCollection]
                              .CGColor;
                      vc->_swatchDark.layer.borderColor = border;
                    }];

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
    // A THICK gradient bar, not the slider's own hairline track rect (owner
    // 2026-08-22, from a device screenshot: "sliders need to have thick
    // gradient color preview instead of thin line" -- the 4 pt system track
    // read as a dark thread on the light sheet). 16 pt tall, centered on the
    // track's own centerline so the thumb still rides it naturally.
    constexpr CGFloat kTrackBarPt = 16.0f;
    const CGRect tr = [_slider[g] trackRectForBounds:_slider[g].bounds];
    CGRect bar = [_slider[g] convertRect:tr toView:self.view];
    bar.origin.y += (bar.size.height - kTrackBarPt) / 2;
    bar.size.height = kTrackBarPt;
    _track[g].frame = bar;
    _track[g].layer.cornerRadius = kTrackBarPt / 2;
    _track[g].clipsToBounds = YES;
    y += 60;
  }
  if (_track[0].bounds.size.width != _trackWidth) {
    _trackWidth = _track[0].bounds.size.width;
    [self rebuildTrackGradients:-1];
  }
  y += 6;
  // Full width: this row used to be a half-and-half pair and the light half
  // is gone, so the dark ground takes the whole row rather than leaving a
  // hole. Height and the row's advance are unchanged, so nothing below moves.
  _swatchDark.frame = CGRectMake(margin, y, W - 2 * margin, 44);
  y += 52;
  _readout.frame = CGRectMake(margin, y, W - 2 * margin, 36);
}

// Retitles the gun's menu button. Called at build time and on every
// reassignment. The menu itself never needs rebuilding: it is a deferred
// element whose provider reads _presets when opened. (The old per-gun
// minimumTrackTintColor is gone: the gradient track underlay replaced it.)
- (void)applyAssignment:(int)g {
  const panelpalette::PresetInfo *info =
      panelpalette::infoForPreset(_presets[g]);
  NSString *title =
      [NSString stringWithFormat:@"%s — %s %s", kGunLabel[g],
                                 info && info->phosphor ? info->phosphor : "?",
                                 info ? info->name : "?"];
  [_name[g] setTitle:title forState:UIControlStateNormal];
}

// The live gradient stack for gun g's track: at track position t (weight
// 0..100), each band is one facet of the mix -- ink, tail, paper, per
// kTrackBands above -- with gun g's weight set to t and the other three guns
// at their current weights, computed through the same computeGuns -> mixBlend
// path as the readout swatches (so duplicate-gun assignments sum in linear
// light here too).
//
// ONE SWEEP, THREE GRADIENTS. Every facet falls out of the SAME mixBlend call,
// so previewing three quantities costs no extra mixing at all -- only two more
// small clipped fills per gun. That is what keeps the x4 rebuild inside the
// drag budget (see the [mixer] log line) rather than tripling it.
- (UIImage *)trackGradientForGun:(int)g size:(CGSize)size {
  CGFloat comps[kTrackBands][kGradientSamples * 4];
  CGFloat locs[kGradientSamples];
  int w[kGunCount];
  for (int i = 0; i < kGunCount; i++) w[i] = _w[i];
  for (int s = 0; s < kGradientSamples; s++) {
    const float t = (float)s / (kGradientSamples - 1);
    w[g] = (int)lroundf(t * kWeightMax);
    const phosphormix::Result r = computeGuns(_presets, w);
    // hasTail is false when every component fades at the same rate: there is
    // no hue handover, the trail simply DIMS, and the color it dims along is
    // the ink itself (HalDisplay's kNoGlowTail path, pushed as a null tint).
    // Painting the ink there is the honest answer -- the alternative, a hole
    // or a black band, would read as "no afterglow" when there is one.
    const unsigned char *facet[kTrackBands] = {
        r.dark.ink, r.hasTail ? r.tail : r.dark.ink, r.dark.paper};
    for (int b = 0; b < kTrackBands; b++) {
      comps[b][s * 4 + 0] = facet[b][0] / 255.0;
      comps[b][s * 4 + 1] = facet[b][1] / 255.0;
      comps[b][s * 4 + 2] = facet[b][2] / 255.0;
      comps[b][s * 4 + 3] = 1.0;
    }
    locs[s] = t;
  }
  CGColorSpaceRef space = CGColorSpaceCreateWithName(kCGColorSpaceSRGB);
  CGGradientRef grad[kTrackBands];
  for (int b = 0; b < kTrackBands; b++)
    grad[b] = CGGradientCreateWithColorComponents(space, comps[b], locs,
                                                  kGradientSamples);
  CGColorSpaceRelease(space);
  // The bar's full height is unchanged (owner asked for thick, 2026-08-22);
  // it is DIVIDED, not shrunk. 16 pt -> three 5 pt bands with 0.5 pt gaps.
  const CGFloat bandH =
      (size.height - kBandGapPt * (kTrackBands - 1)) / kTrackBands;
  // Explicitly NON-opaque: the gaps between bands are transparent, and the
  // track view's background paints them. An opaque format would fill them
  // black, which is invisible in dark appearance and a bug in light.
  UIGraphicsImageRendererFormat *fmt =
      [UIGraphicsImageRendererFormat preferredFormat];
  fmt.opaque = NO;
  UIGraphicsImageRenderer *ren =
      [[UIGraphicsImageRenderer alloc] initWithSize:size format:fmt];
  // A block cannot capture a C array by name; the pointer is fine, and the
  // block runs synchronously inside this scope so the array outlives it.
  CGGradientRef *grads = grad;
  UIImage *img = [ren imageWithActions:^(UIGraphicsImageRendererContext *ctx) {
    for (int b = 0; b < kTrackBands; b++) {
      const CGRect band =
          CGRectMake(0, b * (bandH + kBandGapPt), size.width, bandH);
      CGContextSaveGState(ctx.CGContext);
      CGContextClipToRect(ctx.CGContext, band);
      CGContextDrawLinearGradient(ctx.CGContext, grads[b],
                                  CGPointMake(0, CGRectGetMidY(band)),
                                  CGPointMake(size.width, CGRectGetMidY(band)),
                                  0);
      CGContextRestoreGState(ctx.CGContext);
    }
  }];
  for (int b = 0; b < kTrackBands; b++) CGGradientRelease(grad[b]);
  return img;
}

// Rebuild the gradient tracks. skip = the gun whose gradient is already
// current (a gun's own gradient does not depend on its own weight, so a drag
// only invalidates the OTHER three), or -1 for all four -- a reassignment
// changes gun g's tint base as well as the others' mixes. Inline on the main
// thread: a full x4 rebuild is 4 x 16 mixBlend calls plus four small images,
// measured well under the ~5 ms drag budget (see the [mixer] log line).
- (void)rebuildTrackGradients:(int)skip {
  const CFTimeInterval t0 = CACurrentMediaTime();
  int built = 0;
  for (int g = 0; g < kGunCount; g++) {
    if (g == skip) continue;
    const CGSize sz = _track[g].bounds.size;
    if (sz.width < 1 || sz.height < 1) continue;  // pre-layout: nothing to draw
    _track[g].image = [self trackGradientForGun:g size:sz];
    built++;
  }
  if (built)
    SDL_Log("[mixer] gradient rebuild x%d: %.2f ms", built,
            (CACurrentMediaTime() - t0) * 1000.0);
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
  [self rebuildTrackGradients:-1];
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

// The shared named-preset list. DARK previews, because this is dark mode's
// editor and the page behind the sheet is the dark page; every preset it
// offers is a phosphor, since a paper row belongs to the ink picker.
//
// A selection clears the mix flag (the shared release protocol), so the guns
// below stop owning the page -- and moving one afterwards claims the slot back
// through applyGuns, freezing the light page at the preset's own light pair.
// Both directions are the shared protocol; neither is special-cased here.
//
// IT ALSO SEEDS THE GUNS to the preset (owner 2026-08-23, "selecting a preset
// should set the guns' values too"), so this controller must RE-READ the store
// rather than trust the arrays it loaded in viewDidLoad. Nothing here decides
// what the seed is -- CrossPointPrefs_selectPanelPreset has already written it
// by the time the block runs, and phosphormix::seedForPreset decided it.
- (void)showPresets {
  __weak CPXGunMixerController *weakSelf = self;
  UIViewController *list = CrossPointPresetList_make(/*dark=*/YES, ^{
    [weakSelf reloadGunsFromStore];
  });
  [self.navigationController pushViewController:list animated:YES];
}

// The store moved under us. Sliders, menus, gradients and readout all follow
// the two arrays, so every one of them is stale until this runs -- and a
// selection that left the guns alone (a cascade premix) must move nothing,
// which falls out of simply reading what is there.
- (void)reloadGunsFromStore {
  gunstore::load(_presets, _w);
  for (int g = 0; g < kGunCount; g++) {
    _slider[g].value = _w[g];
    [self applyAssignment:g];
  }
  [self refresh];
  [self rebuildTrackGradients:-1];
}

- (void)dismissSelf {
  [self dismissViewControllerAnimated:YES completion:nil];
}

// THE FLAG MEANS "A PAGE-COLOR SHEET IS COVERING THE SDL VIEW", and a PUSH is
// not the end of one.
//
// What used to stand here said "the nav never pushes a second controller, so
// disappearing means DISMISSED". The Presets list falsified that the same day
// it was written (owner 2026-08-23, "add a Presets row back to the pickers"),
// and the consequence is not cosmetic: UIKit sends viewDidDisappear: to this
// controller when the list is pushed ON TOP of it, so the gate was cleared
// while the sheet was still on screen and never came back. The sheet is an
// undimmed medium detent, which means UIKit passes every touch OUTSIDE it
// straight through to SDL -- so from the moment Presets was tapped, a tap on
// the page above turned it, a swipe drove font size and a three-finger tap
// toggled zen, all while the owner believed he was in a color picker. Five
// call sites read this (CrossPointIOSShim.cpp's finger paths,
// CrossPointZenRecognizers.mm's three recognizers).
//
// So: reassert on every appearance -- a pop back from the list is one -- and
// clear only when this controller is LEAVING the stack rather than being
// covered by something pushed onto it. The sheet cannot be dismissed while the
// list is up (modalInPresentation pins pull-down and the list carries no Done),
// so "top of the stack" is the whole distinction.
- (void)viewDidAppear:(BOOL)animated {
  [super viewDidAppear:animated];
  g_mixerPresented.store(true);
  SDL_Log("[mixer] on screen; touch gate UP");
}

- (void)viewDidDisappear:(BOOL)animated {
  [super viewDidDisappear:animated];
  UINavigationController *nav = self.navigationController;
  if (nav && nav.topViewController != self) {
    // Covered by a push, not dismissed. Logged because the failure it replaces
    // was invisible: nothing said the gate had dropped.
    SDL_Log("[mixer] covered by a push; touch gate HELD");
    return;
  }
  g_mixerPresented.store(false);
  SDL_Log("[mixer] dismissed; touch gate released");
}

- (void)gunMoved:(UISlider *)s {
  // A drag is a newer change: a settle pending from a reassignment must not
  // fire mid-drag and put a re-render on the drag path.
  [self cancelPendingSettle];
  _w[s.tag] = (int)lroundf(s.value);
  applyGuns(_presets, _w, /*renderPage=*/false);
  [self refresh];
  [self rebuildTrackGradients:(int)s.tag];
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
  // r.light is deliberately not painted anywhere: see the swatch's own note in
  // viewDidLoad. It still EXISTS on the Result because a preset defines both
  // appearances and claimCustomFor needs the light pair to freeze.
  //
  // The band order is named here rather than on the tracks: three 5 pt bands
  // hold no text, and one legend for four identical stacks is not clutter.
  //
  // ...unless a NAMED PRESET owns the page, which it does from the moment one
  // is chosen in the Presets list until a gun is moved. The mix below is then
  // still a valid recipe and is simply not what is on screen, so the readout
  // says which -- a drawer describing a page it no longer owns is the lie
  // S-020 shipped.
  //
  // Since 2026-08-23 a selection also SEEDS the guns, so the second line says
  // whether they hold that preset. MEASURED against the arrays rather than
  // assumed from seed.apply: the two agree today, and a readout that trusts
  // its own reasoning instead of the store is the exact shape of the bug this
  // whole area was rewritten for. The three presets a blend cannot be -- the
  // P7 / P14 / P17 cascades -- say so instead of pretending.
  const int livePreset = CrossPointPrefs_panelPalettePreset();
  const panelpalette::PresetInfo *live = panelpalette::infoForPreset(livePreset);
  NSString *presetLine = nil;
  if (live) {
    const phosphormix::GunSeed seed =
        phosphormix::seedForPreset(livePreset, _presets);
    bool seeded = seed.apply;
    for (int g = 0; g < kGunCount && seeded; g++)
      seeded = _presets[g] == seed.preset[g] && _w[g] == seed.weight[g];
    presetLine =
        seeded
            ? [NSString stringWithFormat:@"Preset %s — the guns are set to it\n"
                                         @"move one to take over",
                                         live->name]
            : [NSString stringWithFormat:@"Preset %s — %s\nthe guns keep their "
                                         @"own recipe",
                                         live->name,
                                         phosphormix::seedReasonText(seed.reason)];
  }
  _readout.text =
      presetLine
           ? presetLine
           : [NSString
                 stringWithFormat:
                     @"dark %@ on %@ · light %@ on %@\nfade %.0f ms · track: "
                     @"ink/tail/paper",
                     hexOf(r.dark.ink), hexOf(r.dark.paper), hexOf(r.light.ink),
                     hexOf(r.light.paper), (double)r.trailMs];
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
    // "The color tray is very slideable" (owner 2026-08-21): working the
    // sliders near the sheet's edge kept pulling the whole tray down. Pinned:
    // pull-down dismissal is dead, and the Done button is the only exit.
    nav.modalInPresentation = YES;
    if (nav.sheetPresentationController) {
      // Medium: about 340 pt of controls, and the PAGE stays visible above the
      // sheet -- the page is the preview. ONLY the medium detent, and no
      // grabber -- a grabber is an invitation to drag the thing that must not
      // drag.
      nav.sheetPresentationController.detents =
          @[ UISheetPresentationControllerDetent.mediumDetent ];
      nav.sheetPresentationController.prefersGrabberVisible = NO;
      // Undimmed at medium: without this, UIKit dims the presenting view AND
      // pulls it back (down and slightly scaled), so the panel slid every time
      // the tray opened or closed (owner 2026-08-21: "prevent the panel from
      // sliding up and down"). The page above the sheet stays full-bright and
      // in place -- it IS the preview.
      nav.sheetPresentationController.largestUndimmedDetentIdentifier =
          UISheetPresentationControllerDetentIdentifierMedium;
    }
    g_mixerPresented.store(true);
    [root presentViewController:nav
                       animated:YES
                     completion:^{
                       // CROSSPOINT_SIM_OPEN_PRESETS=1 -- the diagnostic push,
                       // so a headless run can screenshot the preset list on
                       // the stack it really lives on.
                       if (CrossPointPresetList_autoOpen())
                         [mixer showPresets];
                     }];
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
  applyGuns(phosphormix::kDefaultGunPreset, weights, /*renderPage=*/true);
  SDL_Log("[mixer] test hook applied guns %d/%d/%d/%d", weights[0], weights[1],
          weights[2], weights[3]);
}
