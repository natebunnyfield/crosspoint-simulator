#pragma once

// The WWDC26-219 pattern: a view that IS the accessibility element for the
// page and adopts UITextInput in its entirety.
//
// Apple's "Enhance the accessibility of your reading app" (WWDC26 session 219)
// is the shipped contract for custom-rendered reading apps on iOS 26, and it
// names the goal exactly: "Fully implementing UITextInput gives you ...
// granular navigation with the VoiceOver rotor and Speak Screen." Their sample
// is `class ScannedPage: UIView, UITextInput` -- the protocol adopted on the
// accessibility element itself, not a hidden native text view.
//
// Empirical grounding, same device: Kindle's Speak Screen works on the owner's
// iOS 26 iPad while six generations of synthetic-element and hidden-text-view
// exposure here did not. This is the first mechanism that is both documented
// by Apple for Speak Screen and consistent with every measurement.
//
// The firmware already publishes everything the protocol needs: the page text
// and per-word rects with byte ranges (ReadAloudWordRect). This view converts
// those to UTF-16 offsets once per page and answers geometry from them.
//
// Every protocol method logs (throttled) to the diagnostics file, so the next
// device log SHOWS Speak Screen walking the protocol -- or proves it does not.

#import <UIKit/UIKit.h>

#include <vector>

#include "ReadAloudChannel.h"

@interface CPPageTextInputView : UIView <UITextInput>

// Replace the page. Rects are logical portrait panel pixels; x0/y0/scale map
// them into this view's coordinate space (the caller positions the view over
// the panel and passes the panel's own transform).
- (void)setPageText:(NSString *)text
              rects:(const std::vector<ReadAloudWordRect> &)rects
            originX:(CGFloat)x0
            originY:(CGFloat)y0
              scale:(CGFloat)scale;

- (void)clearPage;

@end
