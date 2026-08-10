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
    static UIToolbar *bar = nil;

    UITextField *field = sdlTextField();
    if (!field) return;
    if (field.inputAccessoryView == bar && bar != nil) return; // already on

    if (!bar) {
      target = [[CPKeyboardBarTarget alloc] init];
      bar = [[UIToolbar alloc] initWithFrame:CGRectMake(0, 0, 320, 44)];
      // No barStyle or tint: the bar is native chrome and should follow the
      // system appearance, unlike the panel, whose polarity the firmware owns.
      UIBarButtonItem *spacer = [[UIBarButtonItem alloc]
          initWithBarButtonSystemItem:UIBarButtonSystemItemFlexibleSpace
                               target:nil
                               action:nil];
      UIImage *glyph =
          [UIImage systemImageNamed:@"keyboard.chevron.compact.down"];
      UIBarButtonItem *hide =
          glyph ? [[UIBarButtonItem alloc] initWithImage:glyph
                                                   style:UIBarButtonItemStylePlain
                                                  target:target
                                                  action:@selector(dismiss)]
                : [[UIBarButtonItem alloc] initWithTitle:@"Hide Keyboard"
                                                   style:UIBarButtonItemStylePlain
                                                  target:target
                                                  action:@selector(dismiss)];
      hide.accessibilityLabel = @"Hide keyboard";
      hide.accessibilityHint =
          @"Lowers the keyboard. Tap the page to bring it back.";
      bar.items = @[ spacer, hide ];
      [bar sizeToFit];
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
