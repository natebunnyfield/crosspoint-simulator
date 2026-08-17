#include "CrossPointPalettePicker.h"

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include "CrossPointPrefs.h"
#include "PanelPalette.h"

// The SDL window, for finding the view controller to present from. Declared the
// same way CrossPointKeyboardBar.mm declares it, and for the same reason.
extern SDL_Window *simulatorWindow();

namespace {

UIColor *colorOf(const unsigned char c[3]) {
  return [UIColor colorWithRed:c[0] / 255.0 green:c[1] / 255.0 blue:c[2] / 255.0 alpha:1];
}

NSString *hexOf(const unsigned char c[3]) {
  return [NSString stringWithFormat:@"%02X%02X%02X", c[0], c[1], c[2]];
}

// One preview tile: the paper as the ground with three ink bars on it, which is
// what a page of text actually looks like at a glance. A flat pair of colour
// chips would show the same two values and read as an abstraction; the bars are
// what make it obvious which of two similar sepias is the readable one.
UIView *previewTile(const panelpalette::Palette &p, NSString *label) {
  UIView *tile = [[UIView alloc] initWithFrame:CGRectZero];
  tile.backgroundColor = colorOf(p.paper);
  tile.layer.cornerRadius = 6;
  tile.layer.borderWidth = 1.0 / UIScreen.mainScreen.scale;
  // Separator, not decoration: a white tile on a white sheet has no edge.
  tile.layer.borderColor = UIColor.separatorColor.CGColor;
  tile.clipsToBounds = YES;
  tile.translatesAutoresizingMaskIntoConstraints = NO;
  [tile.widthAnchor constraintEqualToConstant:78].active = YES;
  [tile.heightAnchor constraintEqualToConstant:46].active = YES;

  UIStackView *bars = [[UIStackView alloc] initWithFrame:CGRectZero];
  bars.axis = UILayoutConstraintAxisVertical;
  bars.spacing = 5;
  bars.alignment = UIStackViewAlignmentLeading;
  bars.translatesAutoresizingMaskIntoConstraints = NO;
  // Ragged lengths so it reads as text rather than as a bar chart.
  const CGFloat widths[] = {50, 42, 30};
  for (int i = 0; i < 3; i++) {
    UIView *bar = [[UIView alloc] initWithFrame:CGRectZero];
    bar.backgroundColor = colorOf(p.ink);
    bar.layer.cornerRadius = 1.5;
    bar.translatesAutoresizingMaskIntoConstraints = NO;
    [bar.widthAnchor constraintEqualToConstant:widths[i]].active = YES;
    [bar.heightAnchor constraintEqualToConstant:4].active = YES;
    [bars addArrangedSubview:bar];
  }
  [tile addSubview:bars];
  [NSLayoutConstraint activateConstraints:@[
    [bars.leadingAnchor constraintEqualToAnchor:tile.leadingAnchor constant:10],
    [bars.centerYAnchor constraintEqualToAnchor:tile.centerYAnchor],
  ]];

  UIStackView *wrap = [[UIStackView alloc] initWithFrame:CGRectZero];
  wrap.axis = UILayoutConstraintAxisVertical;
  wrap.spacing = 3;
  wrap.alignment = UIStackViewAlignmentCenter;
  wrap.translatesAutoresizingMaskIntoConstraints = NO;
  [wrap addArrangedSubview:tile];

  UILabel *cap = [[UILabel alloc] initWithFrame:CGRectZero];
  cap.text = label;
  cap.font = [UIFont monospacedDigitSystemFontOfSize:10 weight:UIFontWeightRegular];
  cap.textColor = UIColor.secondaryLabelColor;
  [wrap addArrangedSubview:cap];
  return wrap;
}

}  // namespace

// ---------------------------------------------------------------------------

@interface CPPaletteRow : UITableViewCell
@end

@implementation CPPaletteRow
- (instancetype)initWithStyle:(UITableViewCellStyle)style reuseIdentifier:(NSString *)rid {
  // Cells are built per row and never reused: there are sixteen of them, each
  // with different colours, and a reuse pool would just be a way to show the
  // wrong palette after a scroll.
  return [super initWithStyle:UITableViewCellStyleDefault reuseIdentifier:nil];
}
@end

@interface CPPalettePicker : UITableViewController
@end

@implementation CPPalettePicker

- (void)viewDidLoad {
  [super viewDidLoad];
  self.title = @"Page Colors";
  self.navigationItem.rightBarButtonItem =
      [[UIBarButtonItem alloc] initWithBarButtonSystemItem:UIBarButtonSystemItemDone
                                                    target:self
                                                    action:@selector(done)];
  self.tableView.rowHeight = UITableViewAutomaticDimension;
  self.tableView.estimatedRowHeight = 96;
}

- (void)done {
  [self dismissViewControllerAnimated:YES completion:nil];
}

- (void)viewDidDisappear:(BOOL)animated {
  [super viewDidDisappear:animated];
  CrossPointPalettePicker_noteDismissed();
}

- (NSInteger)numberOfSectionsInTableView:(UITableView *)tv {
  return 2;  // the presets, then Custom
}

- (NSInteger)tableView:(UITableView *)tv numberOfRowsInSection:(NSInteger)section {
  return section == 0 ? panelpalette::kPresetInfoCount : 1;
}

- (NSString *)tableView:(UITableView *)tv titleForHeaderInSection:(NSInteger)section {
  return section == 0 ? @"Presets" : @"Custom";
}

- (NSString *)tableView:(UITableView *)tv titleForFooterInSection:(NSInteger)section {
  if (section != 1) return nil;
  return @"Set the four hex fields in Settings › CrossPoint X3 › Page Colors — "
         @"Custom, then choose Custom here.";
}

- (UITableViewCell *)tableView:(UITableView *)tv cellForRowAtIndexPath:(NSIndexPath *)ip {
  UITableViewCell *cell = [[CPPaletteRow alloc] initWithStyle:UITableViewCellStyleDefault
                                              reuseIdentifier:nil];
  const int current = CrossPointPrefs_panelPalettePreset();

  if (ip.section == 1) {
    cell.textLabel.text = @"Custom";
    cell.textLabel.font = [UIFont preferredFontForTextStyle:UIFontTextStyleBody];
    cell.accessoryType = current == panelpalette::kPresetCustom ? UITableViewCellAccessoryCheckmark
                                                                : UITableViewCellAccessoryNone;
    return cell;
  }

  const panelpalette::PresetInfo &info = panelpalette::kPresetInfo[ip.row];
  const panelpalette::Palette light =
      panelpalette::resolve(info.preset, false, panelpalette::kInvalidColor,
                            panelpalette::kInvalidColor);
  const panelpalette::Palette dark =
      panelpalette::resolve(info.preset, true, panelpalette::kInvalidColor,
                            panelpalette::kInvalidColor);

  UILabel *name = [[UILabel alloc] initWithFrame:CGRectZero];
  name.text = [NSString stringWithFormat:@"%s · %s", info.family, info.name];
  name.font = [UIFont preferredFontForTextStyle:UIFontTextStyleHeadline];
  name.adjustsFontForContentSizeCategory = YES;

  UILabel *note = [[UILabel alloc] initWithFrame:CGRectZero];
  note.text = @(info.note);
  note.font = [UIFont preferredFontForTextStyle:UIFontTextStyleFootnote];
  note.textColor = UIColor.secondaryLabelColor;
  note.adjustsFontForContentSizeCategory = YES;

  // THE VALUES, because the preview is a picture and a picture cannot be typed
  // into the Custom fields. Monospaced so the six pairs line up down the list.
  UILabel *values = [[UILabel alloc] initWithFrame:CGRectZero];
  values.text = [NSString stringWithFormat:@"%@ on %@   ·   %@ on %@", hexOf(light.ink),
                                           hexOf(light.paper), hexOf(dark.ink),
                                           hexOf(dark.paper)];
  values.font = [UIFont monospacedSystemFontOfSize:11 weight:UIFontWeightRegular];
  values.textColor = UIColor.tertiaryLabelColor;
  values.adjustsFontSizeToFitWidth = YES;
  values.minimumScaleFactor = 0.7;

  UIStackView *text = [[UIStackView alloc] initWithArrangedSubviews:@[ name, note, values ]];
  text.axis = UILayoutConstraintAxisVertical;
  text.spacing = 2;

  UIStackView *tiles = [[UIStackView alloc]
      initWithArrangedSubviews:@[ previewTile(light, @"Day"), previewTile(dark, @"Night") ]];
  tiles.axis = UILayoutConstraintAxisHorizontal;
  tiles.spacing = 8;
  tiles.alignment = UIStackViewAlignmentCenter;

  UIStackView *row = [[UIStackView alloc] initWithArrangedSubviews:@[ tiles, text ]];
  row.axis = UILayoutConstraintAxisHorizontal;
  row.spacing = 14;
  row.alignment = UIStackViewAlignmentCenter;
  row.translatesAutoresizingMaskIntoConstraints = NO;
  [cell.contentView addSubview:row];
  [NSLayoutConstraint activateConstraints:@[
    [row.leadingAnchor constraintEqualToAnchor:cell.contentView.layoutMarginsGuide.leadingAnchor],
    [row.trailingAnchor constraintEqualToAnchor:cell.contentView.layoutMarginsGuide.trailingAnchor],
    [row.topAnchor constraintEqualToAnchor:cell.contentView.topAnchor constant:10],
    [row.bottomAnchor constraintEqualToAnchor:cell.contentView.bottomAnchor constant:-10],
  ]];

  cell.accessoryType = current == info.preset ? UITableViewCellAccessoryCheckmark
                                              : UITableViewCellAccessoryNone;
  // The tiles are decoration to a screen reader; the text already says it all.
  tiles.accessibilityElementsHidden = YES;
  cell.accessibilityLabel =
      [NSString stringWithFormat:@"%@, %@", name.text, note.text];
  return cell;
}

- (void)tableView:(UITableView *)tv didSelectRowAtIndexPath:(NSIndexPath *)ip {
  const int chosen = ip.section == 1 ? panelpalette::kPresetCustom
                                     : panelpalette::kPresetInfo[ip.row].preset;
  CrossPointPrefs_setPanelPalettePreset(chosen);
  // No apply call: pollPanelPalette() in CrossPointIOSShim.cpp compares the
  // resolved pair every frame and repaints the page, the pad and both keyboard
  // chips when it changes. Writing the key IS applying it.
  [tv reloadData];  // move the checkmark
  [self dismissViewControllerAnimated:YES completion:nil];
}

@end

// ---------------------------------------------------------------------------

// Raw, not __weak: these files compile under manual reference counting, where
// ownership qualifiers are a compile error. The presentation itself holds the
// controller alive; this is only a "is it up?" flag, cleared on dismissal.
static UIViewController *g_presented = nil;

extern "C" void CrossPointPalettePicker_present(void) {
  @autoreleasepool {
    if (g_presented != nil) return;  // already up; a second tap is a no-op

    SDL_Window *window = simulatorWindow();
    if (!window) return;
    UIWindow *uiWindow = (__bridge UIWindow *)SDL_GetPointerProperty(
        SDL_GetWindowProperties(window), SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER, NULL);
    UIViewController *root = uiWindow.rootViewController;
    if (!root) {
      SDL_Log("[palette] no root view controller; cannot present the picker");
      return;
    }

    // UIKit is main-thread only. The tap that gets here arrives through SDL's
    // event watch, which UIKit delivers on the main thread today -- but a watch
    // callback is not contractually main-thread, and presenting from the wrong
    // one fails in a way that looks like "the button does nothing".
    if (![NSThread isMainThread]) {
      dispatch_async(dispatch_get_main_queue(), ^{ CrossPointPalettePicker_present(); });
      return;
    }

    CPPalettePicker *picker = [[CPPalettePicker alloc] initWithStyle:UITableViewStyleInsetGrouped];
    UINavigationController *nav =
        [[UINavigationController alloc] initWithRootViewController:picker];
    // A sheet rather than full screen: the page stays visible behind it, which
    // is the point -- the choice is about that page.
    nav.modalPresentationStyle = UIModalPresentationPageSheet;
    g_presented = nav;
    [root presentViewController:nav animated:YES completion:nil];
  }
}

extern "C" void CrossPointPalettePicker_noteDismissed(void) { g_presented = nil; }

extern "C" int CrossPointPalettePicker_isOpen(void) {
  return g_presented != nil ? 1 : 0;
}
