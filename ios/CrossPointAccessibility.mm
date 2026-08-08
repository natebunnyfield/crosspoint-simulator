#include "CrossPointAccessibility.h"

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <string>
#include <vector>

#include "HalDisplay.h"
#include "SimulatorOverlay.h"

// A transparent, non-interactive container over the SDL view whose only job is
// to vend accessibility elements. Adding a view rather than trying to override
// a getter on SDL's own view: SDL owns that instance, and a category or
// associated-object hack there would fight it on every window rebuild.
@interface CPAccessibilityOverlay : UIView
@property(nonatomic, strong) NSArray *cpElements;
@end

@implementation CPAccessibilityOverlay
// The container itself is not an element; its children are.
- (BOOL)isAccessibilityElement {
  return NO;
}
- (NSArray *)accessibilityElements {
  return self.cpElements;
}
@end

namespace {

__weak CPAccessibilityOverlay *g_overlay = nil;

UIWindow *resolveWindow() {
  UIWindow *fallback = nil;
  for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
    if (![scene isKindOfClass:UIWindowScene.class]) continue;
    for (UIWindow *w in ((UIWindowScene *)scene).windows) {
      if (w.isKeyWindow) return w;
      if (!fallback) fallback = w;
    }
  }
  return fallback;
}

// Panel geometry in POINTS. The channel's rects are logical panel pixels and
// SimulatorOverlay reports device pixels, but accessibilityFrame is in screen
// points -- so the device-pixel figures are divided by the screen scale.
//
// LOGICAL_HEIGHT, not DISPLAY_HEIGHT: the latter is multiplied by
// CROSSPOINT_RENDER_SCALE, which is 2 here. Getting that wrong put the
// read-aloud highlight at half size on the phone and would put every
// accessibility frame in the wrong place the same way.
bool panelGeometryPts(CGFloat *x0, CGFloat *y0, CGFloat *scale) {
  UIWindow *window = resolveWindow();
  if (!window) return false;
  const CGFloat screenScale = window.screen.scale > 0 ? window.screen.scale : 1;
  const CGFloat panelW = (CGFloat)SimulatorOverlay::panelWidthPx();
  const CGFloat panelH = (CGFloat)SimulatorOverlay::panelHeightPx();
  if (panelW <= 0 || panelH <= 0) return false;
  *scale = (panelW / (CGFloat)HalDisplay::LOGICAL_HEIGHT) / screenScale;
  *x0 = (CGFloat)SimulatorOverlay::panelLeftPx() / screenScale;
  *y0 = (CGFloat)(SimulatorOverlay::panelBottomPx() - SimulatorOverlay::panelHeightPx()) / screenScale;
  return true;
}

// One element per LINE. Rects arrive in reading order, one per visual word
// fragment, and a line is a run sharing the same y.
NSArray *buildElements(UIView *container, const std::string &text,
                       const std::vector<ReadAloudWordRect> &rects) {
  CGFloat x0 = 0, y0 = 0, s = 0;
  if (rects.empty() || !panelGeometryPts(&x0, &y0, &s)) return @[];

  NSMutableArray *out = [NSMutableArray array];
  size_t i = 0;
  while (i < rects.size()) {
    const uint16_t lineY = rects[i].y;
    size_t j = i;
    uint32_t lo = rects[i].byteOffset;
    uint32_t hi = rects[i].byteOffset + rects[i].byteLen;
    CGFloat left = rects[i].x, right = rects[i].x + rects[i].w;
    CGFloat top = rects[i].y, bottom = rects[i].y + rects[i].h;
    while (j < rects.size() && rects[j].y == lineY) {
      lo = std::min(lo, rects[j].byteOffset);
      hi = std::max(hi, rects[j].byteOffset + rects[j].byteLen);
      left = std::min(left, (CGFloat)rects[j].x);
      right = std::max(right, (CGFloat)(rects[j].x + rects[j].w));
      top = std::min(top, (CGFloat)rects[j].y);
      bottom = std::max(bottom, (CGFloat)(rects[j].y + rects[j].h));
      j++;
    }

    if (lo < hi && hi <= text.size()) {
      // A hyphen-split word shares its byte range across two lines, so a line's
      // slice can legitimately overlap the next one's. Reading the whole word
      // on both lines is better than truncating it mid-word.
      NSString *label = [[NSString alloc] initWithBytes:text.data() + lo
                                                 length:hi - lo
                                               encoding:NSUTF8StringEncoding];
      if (label.length > 0) {
        UIAccessibilityElement *el =
            [[UIAccessibilityElement alloc] initWithAccessibilityContainer:container];
        el.accessibilityLabel = label;
        el.accessibilityTraits = UIAccessibilityTraitStaticText;
        // Screen coordinates, which is what accessibilityFrame wants.
        el.accessibilityFrame =
            CGRectMake(x0 + left * s, y0 + top * s, (right - left) * s, (bottom - top) * s);
        [out addObject:el];
      }
    }
    i = j;
  }
  return out;
}

}  // namespace

void CrossPointAccessibility_begin(void) {
  UIWindow *window = resolveWindow();
  if (!window) return;
  if (g_overlay && g_overlay.superview == window) return;  // already installed

  CPAccessibilityOverlay *overlay =
      [[CPAccessibilityOverlay alloc] initWithFrame:window.bounds];
  overlay.backgroundColor = UIColor.clearColor;
  // Never take a touch: the pad and the read-aloud tap both live underneath.
  overlay.userInteractionEnabled = NO;
  overlay.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
  overlay.cpElements = @[];
  [window addSubview:overlay];
  g_overlay = overlay;
}

bool CrossPointAccessibility_wantsPage(void) {
  // Speak Screen is the one the owner asked for; the others read the same
  // elements and cost nothing extra to serve.
  const bool speak = UIAccessibilityIsSpeakScreenEnabled();
  const bool vo = UIAccessibilityIsVoiceOverRunning();
  const bool sw = UIAccessibilityIsSwitchControlRunning();
  // Logged on CHANGE only: this is called every frame. Without it there is no
  // way to tell "assistive tech is off" from "detection is broken", which is
  // exactly the ambiguity that wastes an afternoon.
  static int last = -1;
  const int now = (speak ? 1 : 0) | (vo ? 2 : 0) | (sw ? 4 : 0);
  if (now != last) {
    last = now;
    SDL_Log("[A11Y] assistive tech: speakScreen=%d voiceOver=%d switchControl=%d", speak, vo, sw);
  }
  return speak || vo || sw;
}

void CrossPointAccessibility_setPage(const char *utf8, unsigned len,
                                     const ReadAloudWordRect *rects, unsigned rectCount) {
  CPAccessibilityOverlay *overlay = g_overlay;
  if (!overlay) return;
  if (!utf8 || len == 0 || !rects || rectCount == 0) {
    CrossPointAccessibility_clear();
    return;
  }
  const std::string text(utf8, len);
  const std::vector<ReadAloudWordRect> v(rects, rects + rectCount);
  overlay.cpElements = buildElements(overlay, text, v);
  // Greppable like the rest: [A11Y]. The count and the first label are what
  // distinguish "elements built" from "assistive tech saw nothing".
  if (overlay.cpElements.count > 0) {
    UIAccessibilityElement *first = overlay.cpElements.firstObject;
    const CGRect f = first.accessibilityFrame;
    // rects -> lines makes the grouping visible: if these are equal, the
    // per-line grouping has silently degenerated to per-word and Speak Screen
    // will read with a pause after every word.
    SDL_Log("[A11Y] %u word rects -> %lu line elements; first \"%s\" at (%.0f,%.0f %.0fx%.0f) pts",
            rectCount, (unsigned long)overlay.cpElements.count,
            first.accessibilityLabel.UTF8String ?: "", f.origin.x, f.origin.y, f.size.width,
            f.size.height);
  } else {
    SDL_Log("[A11Y] page had %u rects but produced no elements", rectCount);
  }
  // Tell assistive tech the screen changed, or Speak Screen keeps reading the
  // page it already had.
  UIAccessibilityPostNotification(UIAccessibilityScreenChangedNotification, nil);
}

void CrossPointAccessibility_clear(void) {
  CPAccessibilityOverlay *overlay = g_overlay;
  if (!overlay) return;
  overlay.cpElements = @[];
  UIAccessibilityPostNotification(UIAccessibilityScreenChangedNotification, nil);
}
