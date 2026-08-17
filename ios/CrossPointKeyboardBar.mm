#include "CrossPointKeyboardBar.h"

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include "HalGPIO.h"
#include "PanelPrefs.h"

// The SDL window, from the translation unit that owns it. Declared here rather
// than published in a header for the same reason HalGPIO.cpp declares it the
// same way: it is one pointer, and giving it a header would invite code that
// has no business holding it.
extern SDL_Window *simulatorWindow();

namespace {

// SDL's hidden text field, found by public traversal only.
//
// SDL adds it directly to the root view controller's view
// (SDL_uikitviewcontroller.m:350), so depth 1 is the expected answer. The sweep
// goes a little deeper anyway, and logs the depth it succeeded at: if SDL ever
// reparents the field, the log says so rather than the bar just silently
// vanishing.
UITextField *findTextField(UIView *root, int depth, int *foundAt) {
  if (!root || depth > 3) return nil;
  for (UIView *v in root.subviews) {
    if ([v isKindOfClass:UITextField.class]) {
      *foundAt = depth;
      return (UITextField *)v;
    }
  }
  for (UIView *v in root.subviews) {
    UITextField *found = findTextField(v, depth + 1, foundAt);
    if (found) return found;
  }
  return nil;
}

UITextField *sdlTextField() {
  SDL_Window *window = simulatorWindow();
  if (!window) return nil;
  // The window SDL itself published, not whichever one happens to be key --
  // there is only one here, but asking SDL removes the guesswork entirely.
  UIWindow *uiWindow = (__bridge UIWindow *)SDL_GetPointerProperty(
      SDL_GetWindowProperties(window), SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER,
      NULL);
  if (!uiWindow) {
    SDL_Log("[harness] keyboard bar: SDL published no UIKit window");
    return nil;
  }
  int depth = 0;
  UITextField *field = findTextField(uiWindow.rootViewController.view, 1, &depth);
  if (!field) {
    // Loud, because a silent miss looks exactly like the bug this fixes: the
    // keyboard comes up and nothing will put it down.
    SDL_Log("[harness] keyboard bar: no UITextField under the root view -- "
            "SDL's text field was not found, so there is no way to dismiss "
            "the keyboard");
    return nil;
  }
  if (depth != 1)
    SDL_Log("[harness] keyboard bar: SDL's text field is at depth %d, not 1 "
            "-- SDL reparented it; expected a direct subview",
            depth);
  return field;
}

// The hide glyph, drawn to MATCH the show chip the pad paints — same
// construction, same proportions, chevron mirrored (owner ruling 2026-08-11:
// "make the hide and show keyboard icons match").
//
// Not an SF Symbol. keyboard.chevron.compact.down is a different drawing in a
// different weight from the chip beside it, and as a UIButton image it arrived
// in the system's blue accent — in an app that is otherwise entirely
// monochrome. Owner: "wtf?! why a blue tint? this is an entirely monochromatic
// app."
//
// Proportions are lifted from paintKeyboardChip in CrossPointIOSShim.cpp:
// chevron 0.26 of the glyph height, body 0.56, body width 1.75x its height,
// key gaps 0.13 of the body. Change one and change the other, or the pair stops
// matching — which is the whole point of this function existing.
//
// Rendered as a TEMPLATE image with the keys punched to transparent, so the
// caller's tintColor is the only thing that decides its color and the punched
// keys show whatever is behind.
UIImage *hideKeyboardGlyph(CGFloat side) {
  const CGFloat glyphH = side * 0.58;
  const CGFloat chevH = glyphH * 0.26;
  const CGFloat bodyH = glyphH * 0.56;
  const CGFloat bodyW = bodyH * 1.75;

  UIGraphicsImageRendererFormat *fmt = [UIGraphicsImageRendererFormat preferredFormat];
  fmt.opaque = NO;
  UIGraphicsImageRenderer *r =
      [[UIGraphicsImageRenderer alloc] initWithSize:CGSizeMake(side, side) format:fmt];

  UIImage *img = [r imageWithActions:^(UIGraphicsImageRendererContext *ctx) {
    CGContextRef c = ctx.CGContext;
    const CGFloat cx = side / 2;
    const CGFloat top = (side - glyphH) / 2;
    [UIColor.blackColor setFill];

    // Body FIRST, at the top — the chevron hangs below it, the mirror of the
    // chip, where the chevron sits above and points up.
    const CGFloat bx = cx - bodyW / 2;
    const CGFloat by = top;
    UIBezierPath *body = [UIBezierPath bezierPathWithRoundedRect:CGRectMake(bx, by, bodyW, bodyH)
                                                    cornerRadius:bodyH * 0.2];
    [body fill];

    // Keys punched straight through to transparent.
    CGContextSetBlendMode(c, kCGBlendModeClear);
    const CGFloat gap = MAX(1.0, round(bodyH * 0.13));
    const CGFloat innerW = bodyW - gap * 2;
    const CGFloat keyH = (bodyH - gap * 4) / 3;
    const CGFloat keyW = (innerW - gap * 3) / 4;
    for (int row = 0; row < 2; row++) {
      for (int col = 0; col < 4; col++) {
        CGContextFillRect(c, CGRectMake(bx + gap + col * (keyW + gap), by + gap + row * (keyH + gap), keyW, keyH));
      }
    }
    CGContextFillRect(c, CGRectMake(bx + gap + keyW * 0.5, by + gap + 2 * (keyH + gap), innerW - keyW, keyH));
    CGContextSetBlendMode(c, kCGBlendModeNormal);

    // Chevron BELOW, pointing down: wide at the top, converging at the bottom.
    // The chip's is the same shape flipped, which is what makes the pair read
    // as one control in two states.
    const CGFloat arm = MAX(1.0, round(chevH * 0.42));
    const CGFloat chevTop = by + bodyH + chevH * 0.7;
    for (CGFloat i = 0; i < chevH; i += 1) {
      const CGFloat off = chevH - i;
      CGContextFillRect(c, CGRectMake(cx - off - arm / 2, chevTop + i, arm, 1));
      CGContextFillRect(c, CGRectMake(cx + off - arm / 2, chevTop + i, arm, 1));
    }
  }];
  return [img imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate];
}

// Panel ink and paper, read LIVE from the owner's palette choice rather than
// pinned to the shipped tones.
//
// These used to be the kDefaultLight / kDefaultDark constants written out by
// hand. That was invisible until the palette became settable: the SHOW chip is
// painted by the SDL side from the pad palette, which follows the chosen paper,
// while this HIDE chip stayed gray. Pick Green CRT and one chip was phosphor
// and the other was not (owner, 2026-08-15: "match hide keyboard color to show
// keyboard color").
//
// Dynamic provider, so a light/dark switch still re-resolves without anyone
// rebuilding the bar. A PALETTE change does not raise a trait change, though,
// so CrossPointKeyboardBar_refreshTint() below is what carries that half --
// and it is required for the border in any case, since a CGColor is resolved
// once at assignment and never re-evaluated.
UIColor *colorFromPanel(bool wantInk) {
  return [UIColor colorWithDynamicProvider:^UIColor *(UITraitCollection *t) {
    const bool dark = t.userInterfaceStyle == UIUserInterfaceStyleDark;
    const panelpalette::Palette p = crosspoint::panelForPrefs(dark);
    const unsigned char *c = wantInk ? p.ink : p.paper;
    return [UIColor colorWithRed:c[0] / 255.0
                           green:c[1] / 255.0
                            blue:c[2] / 255.0
                            alpha:1];
  }];
}

// The chip's own LIGHT GRAY stroke, from the same crosspoint:: definition the
// SHOW chip paints with. It used to be panelInk() -- full page ink -- which is
// how this half went black alongside the SDL half when the pad's outline default
// became Black & White. The chips were asked to be light gray; see
// ios/PanelPrefs.h.
UIColor *chipStroke(void) {
  return [UIColor colorWithDynamicProvider:^UIColor *(UITraitCollection *t) {
    const bool dark = t.userInterfaceStyle == UIUserInterfaceStyleDark;
    const padpalette::Palette p = crosspoint::chipPaletteForPrefs(dark);
    return [UIColor colorWithRed:p.hairline[0] / 255.0
                           green:p.hairline[1] / 255.0
                            blue:p.hairline[2] / 255.0
                           alpha:1];
  }];
}

UIColor *panelInk(void) { return colorFromPanel(true); }

UIColor *panelPaper(void) { return colorFromPanel(false); }

} // namespace

// The bar's target. An object, because UIBarButtonItem holds its target
// weakly and a block would need somewhere to live regardless; a file-static
// strong reference keeps it alive for the process.
@interface CPKeyboardBarTarget : NSObject
@end

@implementation CPKeyboardBarTarget
- (void)dismiss {
  // Only lowers the keyboard. The firmware's field stays open, its on-screen
  // grid keeps working, and typed text routes through again the moment the
  // keyboard is back.
  gpio.setHostKeyboardVisible(false);
}
@end

// File scope, not block scope: the tint refresh below has to reach the button
// after it is built, and a palette change can arrive at any time.
static CPKeyboardBarTarget *g_target = nil;
static UIView *g_bar = nil;
static UIButton *g_hide = nil;

// Re-apply the current palette to an already-built chip.
//
// Needed because neither half re-resolves on its own: a dynamic UIColor
// re-evaluates on a TRAIT change, and a palette change is not one; and
// layer.borderColor is a CGColor, resolved once at assignment. Safe to call
// before the bar exists -- it is a no-op then, and install() picks up the
// current colors anyway.
void CrossPointKeyboardBar_refreshTint(void) {
  dispatch_block_t work = ^{
    if (!g_hide) return;
    g_hide.tintColor = chipStroke();
    g_hide.backgroundColor = panelPaper();
    g_hide.layer.borderColor = chipStroke().CGColor;
  };
  if (NSThread.isMainThread)
    work();
  else
    dispatch_async(dispatch_get_main_queue(), work);
}

void CrossPointKeyboardBar_install(void) {
  dispatch_block_t work = ^{
    CPKeyboardBarTarget *__strong &target = g_target;
    UIView *__strong &bar = g_bar;

    UITextField *field = sdlTextField();
    if (!field) return;
    if (field.inputAccessoryView == bar && bar != nil) return; // already on

    if (!bar) {
      target = [[CPKeyboardBarTarget alloc] init];

      // A TRANSPARENT container, taller than the button, so there is real space
      // between the button and the top of the keyboard (owner 2026-08-11: "the
      // ask for the hide ios keyboard was to give a gap between ios keyboard
      // and the button. that's the goal").
      //
      // This started as a UIToolbar and the first attempt at the gap nudged the
      // item up with imageInsets -- which moved the glyph WITHIN the bar and
      // left it sitting on the keyboard exactly as before, because a toolbar
      // paints its own background across its full height. Nothing can open a
      // gap inside an opaque bar. The container is clear, so its lower strip
      // shows the page behind and reads as space.
      // 48, not the 44 pt HIG minimum (owner ruling 2026-08-11). Snapping UP
      // keeps it compliant and puts two numbers on the grid at once: the button
      // itself, and the container at kButton + kGap = 56. Snapping down to 40
      // would have broken the minimum.
      const CGFloat kButton = 48;
      const CGFloat kGap = 8;      // the gap itself, on the 8 pt grid
      const CGFloat kEdge = 8;     // inset from the right edge
      bar = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 320, kButton + kGap)];
      bar.backgroundColor = UIColor.clearColor;
      bar.autoresizingMask = UIViewAutoresizingFlexibleWidth;

      // Custom, NOT UIButtonTypeSystem: a system button pulls the app's accent
      // color, and this app has no accent -- the panel is ink on paper and
      // nothing else. Type Custom plus an explicit tint keeps it monochrome.
      UIButton *hide = [UIButton buttonWithType:UIButtonTypeCustom];
      [hide setImage:hideKeyboardGlyph(kButton) forState:UIControlStateNormal];
      hide.tintColor = chipStroke();
      // Stroke-then-face, the same construction the pad gives every control and
      // the show chip. Without a backing the glyph floated over whatever the
      // page happened to be drawing and merged with it -- the first render sat
      // squarely on top of the panel's own Return arrow and read as one mark.
      // Paper fill separates it from the page; the hairline says it is a
      // control rather than page content.
      hide.backgroundColor = panelPaper();
      hide.layer.cornerRadius = 8;  // the 8 pt grid the pad aligns to
      hide.layer.borderWidth = 1;
      hide.layer.borderColor = chipStroke().CGColor;
      // Top-aligned in the container, so the whole gap falls BELOW it.
      hide.frame = CGRectMake(bar.bounds.size.width - kEdge - kButton, 0, kButton, kButton);
      hide.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
      hide.accessibilityLabel = @"Hide keyboard";
      hide.accessibilityHint =
          @"Lowers the keyboard. Tap the keyboard key to bring it back.";
      [hide addTarget:target
                    action:@selector(dismiss)
          forControlEvents:UIControlEventTouchUpInside];
      g_hide = hide;
      [bar addSubview:hide];
    }

    field.inputAccessoryView = bar;
    // The field is usually not first responder yet -- SDL raises
    // SDL_EVENT_SCREEN_KEYBOARD_SHOWN from inside -startTextInput, before
    // becomeFirstResponder -- in which case this is a no-op and the accessory
    // is picked up when it does become first responder. When the keyboard IS
    // already up (a re-install after SDL re-added the field), this is what
    // swaps the bar in live.
    [field reloadInputViews];
    SDL_Log("[harness] keyboard bar attached");
  };
  if (NSThread.isMainThread)
    work();
  else
    dispatch_async(dispatch_get_main_queue(), work);
}
