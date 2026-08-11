#include "CrossPointKeyboardBar.h"

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include "HalGPIO.h"

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
// caller's tintColor is the only thing that decides its colour and the punched
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

// Panel ink, the two tones HalDisplay's PanelPalette uses. Monochrome by
// definition — no system accent anywhere near this control.
UIColor *panelInk(void) {
  return [UIColor colorWithDynamicProvider:^UIColor *(UITraitCollection *t) {
    return t.userInterfaceStyle == UIUserInterfaceStyleDark
               ? [UIColor colorWithRed:0xE0 / 255.0 green:0xE0 / 255.0 blue:0xDE / 255.0 alpha:1]
               : [UIColor colorWithRed:0x2D / 255.0 green:0x2D / 255.0 blue:0x2D / 255.0 alpha:1];
  }];
}

// The paper the ink sits on, the other half of the same palette.
UIColor *panelPaper(void) {
  return [UIColor colorWithDynamicProvider:^UIColor *(UITraitCollection *t) {
    return t.userInterfaceStyle == UIUserInterfaceStyleDark
               ? [UIColor colorWithRed:0x12 / 255.0 green:0x12 / 255.0 blue:0x12 / 255.0 alpha:1]
               : [UIColor colorWithRed:0xFB / 255.0 green:0xFB / 255.0 blue:0xF9 / 255.0 alpha:1];
  }];
}

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

void CrossPointKeyboardBar_install(void) {
  dispatch_block_t work = ^{
    static CPKeyboardBarTarget *target = nil;
    static UIView *bar = nil;

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
      const CGFloat kButton = 44;  // HIG minimum, and the button stays square
      const CGFloat kGap = 8;      // the gap itself, on the 8 pt grid
      const CGFloat kEdge = 8;     // inset from the right edge
      bar = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 320, kButton + kGap)];
      bar.backgroundColor = UIColor.clearColor;
      bar.autoresizingMask = UIViewAutoresizingFlexibleWidth;

      // Custom, NOT UIButtonTypeSystem: a system button pulls the app's accent
      // colour, and this app has no accent -- the panel is ink on paper and
      // nothing else. Type Custom plus an explicit tint keeps it monochrome.
      UIButton *hide = [UIButton buttonWithType:UIButtonTypeCustom];
      [hide setImage:hideKeyboardGlyph(kButton) forState:UIControlStateNormal];
      hide.tintColor = panelInk();
      // Stroke-then-face, the same construction the pad gives every control and
      // the show chip. Without a backing the glyph floated over whatever the
      // page happened to be drawing and merged with it -- the first render sat
      // squarely on top of the panel's own Return arrow and read as one mark.
      // Paper fill separates it from the page; the hairline says it is a
      // control rather than page content.
      hide.backgroundColor = panelPaper();
      hide.layer.cornerRadius = 8;  // the 8 pt grid the pad aligns to
      hide.layer.borderWidth = 1;
      hide.layer.borderColor = panelInk().CGColor;
      // Top-aligned in the container, so the whole gap falls BELOW it.
      hide.frame = CGRectMake(bar.bounds.size.width - kEdge - kButton, 0, kButton, kButton);
      hide.autoresizingMask = UIViewAutoresizingFlexibleLeftMargin;
      hide.accessibilityLabel = @"Hide keyboard";
      hide.accessibilityHint =
          @"Lowers the keyboard. Tap the keyboard key to bring it back.";
      [hide addTarget:target
                    action:@selector(dismiss)
          forControlEvents:UIControlEventTouchUpInside];
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
