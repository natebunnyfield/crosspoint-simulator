#include "CrossPointAccessibility.h"

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <algorithm>
#include <string>
#include <vector>

#include "HalDisplay.h"
#include "HalGPIO.h"
#include "CrossPointDiagLog.h"
#import "CrossPointPageTextInput.h"
#include "ReadAloudLines.h"
#include "SimulatorOverlay.h"

// A transparent, non-interactive container over the SDL view whose only job is
// to vend accessibility elements. Adding a view rather than trying to override
// a getter on SDL's own view: SDL owns that instance, and a category or
// associated-object hack there would fight it on every window rebuild.
// Throttled query log; defined below the namespace block.
void CrossPointAccessibility_noteQuery(const char *what, long value);
extern "C" void CrossPointIOS_setKeyboardHeight(float heightPt);
void CrossPointAccessibility_installFocusObserver(void);
void CrossPointAccessibility_installKeyboardObserver(void);

// THE FIX SELECTED BY MEASUREMENT, and the probe that will judge it.
//
// The evidence chain across builds 46-48: the page publishes, the hierarchy is
// clean, the device AX server serves our per-line elements (VoiceOver read
// them aloud on the owner's phone), and Speak Screen still reports "no
// speakable content" WITHOUT ever querying the container. So Speak Screen's
// content filter rejects a bag of plain static-text elements as page content.
//
// UIAccessibilityReadingContent is Apple's designed marker for exactly this --
// paged reading apps; it is what Books adopts. One element spans the page,
// vends the text per line and as a whole, and carries CausesPageTurn so
// continuous reading can turn pages through the same BTN_RIGHT injection the
// read-aloud adapter already uses.
//
// Every protocol method logs (throttled), so the next device log SHOWS Speak
// Screen consuming this -- or proves it does not, in which case this class is
// measured out the way four other hypotheses were.
@interface CPReadingPageElement : UIAccessibilityElement <UIAccessibilityReadingContent>
@property(nonatomic, strong) NSArray<NSString *> *cpLines;
@property(nonatomic, strong) NSArray<NSValue *> *cpLineFrames;  // screen pts
@property(nonatomic, copy) NSString *cpPageText;
@end

void CrossPointAccessibility_noteReading(const char *what, long value);

@implementation CPReadingPageElement

- (NSInteger)accessibilityLineNumberForPoint:(CGPoint)point {
  for (NSUInteger i = 0; i < self.cpLineFrames.count; i++) {
    if (CGRectContainsPoint(self.cpLineFrames[i].CGRectValue, point)) {
      CrossPointAccessibility_noteReading("lineNumberForPoint", (long)i);
      return (NSInteger)i;
    }
  }
  CrossPointAccessibility_noteReading("lineNumberForPoint", -1);
  return NSNotFound;
}

- (NSString *)accessibilityContentForLineNumber:(NSInteger)lineNumber {
  CrossPointAccessibility_noteReading("contentForLine", (long)lineNumber);
  if (lineNumber < 0 || lineNumber >= (NSInteger)self.cpLines.count) return nil;
  return self.cpLines[(NSUInteger)lineNumber];
}

- (CGRect)accessibilityFrameForLineNumber:(NSInteger)lineNumber {
  if (lineNumber < 0 || lineNumber >= (NSInteger)self.cpLineFrames.count) return CGRectZero;
  return self.cpLineFrames[(NSUInteger)lineNumber].CGRectValue;
}

- (NSString *)accessibilityPageContent {
  CrossPointAccessibility_noteReading("pageContent", (long)self.cpLines.count);
  return self.cpPageText;
}

// Continuous reading turns the page: CausesPageTurn tells the reader to scroll
// when it exhausts this element, and the scroll lands here. The injection is
// the SAME tap the read-aloud adapter uses, already verified against the
// firmware's detectPageTurn (BTN_RIGHT = next; nav-swap caveat noted there).
- (BOOL)accessibilityScroll:(UIAccessibilityScrollDirection)direction {
  if (direction == UIAccessibilityScrollDirectionNext ||
      direction == UIAccessibilityScrollDirectionRight) {
    CrossPointAccessibility_noteReading("scroll next -> page turn", +1);
    gpio.queueButtonTap(HalGPIO::BTN_RIGHT, 60);
    return YES;
  }
  if (direction == UIAccessibilityScrollDirectionPrevious ||
      direction == UIAccessibilityScrollDirectionLeft) {
    CrossPointAccessibility_noteReading("scroll prev -> page back", -1);
    gpio.queueButtonTap(HalGPIO::BTN_LEFT, 60);
    return YES;
  }
  return NO;
}
@end

@interface CPAccessibilityOverlay : UIView
@property(nonatomic, strong) NSArray *cpElements;
@end

@implementation CPAccessibilityOverlay
// The container itself is not an element; its children are.
- (BOOL)isAccessibilityElement {
  return NO;
}

// THE CONTAINER API IS IMPLEMENTED EXPLICITLY, and that is the whole bug fix.
//
// The first version only overrode -accessibilityElements. That reads like the
// obvious thing and is silently useless: UIKit answers assistive technology
// through the UIAccessibilityContainer methods below, and UIView derives those
// from the STORED accessibilityElements property -- not from an override of its
// getter. So the container sat in the tree, front-most, correctly framed,
// reporting accessibilityElementCount = 0. Every build reported "no speakable
// content could be found on the screen", with or without a page turn, because
// there genuinely were no children as far as iOS could see.
//
// Diagnosed by walking the tree with the same public API an assistive
// technology uses (CrossPointAccessibility_dumpTree) instead of reasoning about
// what UIKit "should" do. Both are implemented now: the property is set for the
// paths that read it, and these three answer the ones that ask directly.
// The OTHER door. iOS can read a container two ways: the explicit
// count/atIndex methods below, or the stored accessibilityElements property.
// Build 47 probed only the first and logged total silence while Speak Screen
// reported no content -- which is ambiguous until this getter is watched too.
// Overriding a getter is exactly what broke build 42, but the trap there was
// overriding it INSTEAD of implementing the container methods; with all three
// implemented below, delegating to super preserves the stored property's
// semantics bit for bit while recording that the read happened.
- (NSArray *)accessibilityElements {
  CrossPointAccessibility_noteQuery("elementsGetter", (long)self.cpElements.count);
  return [super accessibilityElements];
}

- (NSInteger)accessibilityElementCount {
  // Query logging, throttled hard: the first few calls after each page are the
  // signal ("iOS consulted the container at t=X"), the rest are noise. The
  // build-46 log proved the container ANSWERS correctly when asked; what it
  // could not prove is that assistive tech ever ASKS. This is that probe.
  CrossPointAccessibility_noteQuery("elementCount", (long)self.cpElements.count);
  return (NSInteger)self.cpElements.count;
}

- (id)accessibilityElementAtIndex:(NSInteger)index {
  CrossPointAccessibility_noteQuery("elementAtIndex", (long)index);
  if (index < 0 || index >= (NSInteger)self.cpElements.count) return nil;
  return self.cpElements[(NSUInteger)index];
}

- (NSInteger)indexOfAccessibilityElement:(id)element {
  const NSUInteger i = [self.cpElements indexOfObject:element];
  return i == NSNotFound ? NSNotFound : (NSInteger)i;
}
@end

namespace {

__weak CPAccessibilityOverlay *g_overlay = nil;
// The REAL text view. Builds 46-50 measured Speak Screen ignoring every
// synthetic exposure -- container methods, elements getter, ReadingContent,
// even elements vended straight from the window -- without issuing a single
// query, while the owner's Safari control test shows it reading real text
// machinery fine. So the page is also carried by an actual UITextView: real
// TextKit storage, which Speak Screen's extraction reads without ever calling
// application code. Glyphs are clear (the panel already draws the page);
// non-editable, non-interactive, so it can neither take the keyboard nor eat
// a touch.
// The WWDC26-219 page view: the accessibility element that adopts UITextInput
// in its entirety. See CrossPointPageTextInput.h for the evidence chain; the
// short form is that this is Apple's shipped recipe for Speak Screen on
// custom-rendered reading apps, and Kindle -- working on the owner's device --
// is the empirical proof the route functions on this OS.
__weak CPPageTextInputView *g_pageInput = nil;
long g_queryBudget = 0;
bool g_pageTurnRequested = false;
long g_readingBudget = 0;
bool g_inDump = false;
// Element-set mode: whether the page element was included when the current
// elements were built. Speak Screen can be toggled while a page is on screen,
// and the adapter re-pushes the held page when this goes stale.
int g_builtMode = -1;

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
// The page element rides along whenever Speak Screen is on (or the sim run
// forces it, so the branch is testable off-device). NOT unconditionally: the
// owner just verified VoiceOver's per-line swipe on the device, and appending
// a page element that VoiceOver would also stop on re-reads the page to them.
// Speak Screen users get the protocol; the confirmed VoiceOver experience
// stays byte-identical.
bool wantsReadingPage() {
  static const bool forced = [] {
    const char *v = std::getenv("CROSSPOINT_SIM_FORCE_SPEAKSCREEN");
    return v != nullptr && v[0] == '1';
  }();
  return forced || UIAccessibilityIsSpeakScreenEnabled();
}

NSArray *buildElements(UIView *container, const std::string &text,
                       const std::vector<ReadAloudWordRect> &rects) {
  CGFloat x0 = 0, y0 = 0, s = 0;
  if (rects.empty() || !panelGeometryPts(&x0, &y0, &s)) return @[];

  NSMutableArray *out = [NSMutableArray array];
  // Grouping lives in readaloud::groupIntoLines (src/ReadAloudLines.h), not
  // here. This file cannot be compiled or run anywhere but a phone, and the
  // grouping is the part that has actually been wrong -- so it belongs
  // somewhere a host test and the desktop dump can both reach it. What is left
  // here is the UIKit half: labels to elements, panel pixels to screen points.
  for (const readaloud::LineLabel &line : readaloud::groupIntoLines(text, rects)) {
    NSString *label = [[NSString alloc] initWithBytes:line.text.data()
                                               length:line.text.size()
                                             encoding:NSUTF8StringEncoding];
    if (label.length == 0) continue;
    UIAccessibilityElement *el =
        [[UIAccessibilityElement alloc] initWithAccessibilityContainer:container];
    el.accessibilityLabel = label;
    el.accessibilityTraits = UIAccessibilityTraitStaticText;
    // Screen coordinates, which is what accessibilityFrame wants.
    el.accessibilityFrame =
        CGRectMake(x0 + line.x * s, y0 + line.y * s, line.w * s, line.h * s);
    [out addObject:el];
  }
  // The build-49 UIAccessibilityReadingContent page element is retired: the
  // measured Speak Screen consumer is the UITextInput page view, and an extra
  // whole-page element here was one more VoiceOver stop re-reading what the
  // per-line elements already cover.
  return out;
}

}  // namespace

void CrossPointAccessibility_begin(void) {
  UIWindow *window = resolveWindow();
  if (!window) return;
  if (g_overlay && g_overlay.superview == window) {
    // Already installed -- but SDL adds its own views, and a deep-sleep wake
    // rebuilds them, which can leave this one buried. Accessibility traversal
    // is front-to-back, so a buried container is a container nobody reads.
    [window bringSubviewToFront:g_overlay];
    return;
  }

  CPAccessibilityOverlay *overlay =
      [[CPAccessibilityOverlay alloc] initWithFrame:window.bounds];
  overlay.backgroundColor = UIColor.clearColor;
  // Never take a touch: the pad and the read-aloud tap both live underneath.
  overlay.userInteractionEnabled = NO;
  overlay.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
  overlay.cpElements = @[];
  overlay.accessibilityElements = @[];
  [window addSubview:overlay];
  [window bringSubviewToFront:overlay];
  g_overlay = overlay;
  // The launch header: every report needs this context, and asking the owner
  // for it costs a round trip. Marketing/build versions come from the bundle,
  // so the log itself says which TestFlight build produced it.
  NSDictionary *info = NSBundle.mainBundle.infoDictionary;
  // Scene hosting state, logged because the scene shim exists for Speak
  // Screen and silently failing to be scene-hosted would invalidate the whole
  // experiment: connectedScenes says whether iOS runs us scene-based at all,
  // hosted says whether SDL's window was adopted into one.
  const NSUInteger sceneCount = UIApplication.sharedApplication.connectedScenes.count;
  CrossPointDiag_log("scenes=%lu windowHosted=%d", (unsigned long)sceneCount,
                     (int)(window.windowScene != nil));
  CrossPointDiag_log("---- launch: v%s (%s), screen %.0fx%.0f pt @%.2fx ----",
                     [info[@"CFBundleShortVersionString"] UTF8String] ?: "?",
                     [info[@"CFBundleVersion"] UTF8String] ?: "?",
                     window.bounds.size.width, window.bounds.size.height,
                     (double)window.screen.scale);
  CrossPointDiag_log("container installed over the panel (keyWindow=%d)", (int)window.isKeyWindow);
  CrossPointAccessibility_installFocusObserver();
  CrossPointAccessibility_installKeyboardObserver();
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
    const bool turnedOn = now != 0 && last <= 0;
    last = now;
    CrossPointDiag_log("assistive tech: speakScreen=%d voiceOver=%d switchControl=%d", speak, vo, sw);
    // The moment assistive tech turns ON is the moment the report happens, so
    // dump what it can actually reach RIGHT NOW -- not once at launch, when the
    // interesting state has not happened yet. This is the line that separates
    // "the container is empty" from "the container is unreachable" from "there
    // is simply no page on this screen".
    if (turnedOn) CrossPointAccessibility_dumpTree();
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
  overlay.accessibilityElements = overlay.cpElements;
  // THE WINDOW-LEVEL DOOR. Every prior exposure lives on the overlay, one
  // level down from the window, and VoiceOver demonstrably descends to it. A
  // top-down reader that asks only the WINDOW for its elements gets nil there
  // and can conclude "no content" without a single query reaching the overlay
  // -- which is the precise signature builds 47-49 logged. Mirroring the same
  // element objects onto the window costs nothing SDL uses (it never touches
  // window.accessibilityElements) and is gated like the page element so the
  // confirmed VoiceOver experience keeps its single un-duplicated source.
  // THE HOST MOVES INTO THE ROOT VIEW CONTROLLER'S HIERARCHY (build 53).
  // Build 52's screenshot is the controlled experiment: all four candidates
  // visibly rendered -- Bravo in plain, ordinary gray ink -- and Speak Screen
  // still reported no content. Every candidate was a bare WINDOW subview.
  // Safari-class content lives under the root view controller, and SDL's own
  // text field lives inside the metal view (the root VC's view), so subviews
  // there are tolerated. If Speak Screen extracts from the root VC hierarchy
  // only, window-level siblings are invisible to it no matter how visible
  // their ink -- which is exactly what the screenshot shows.
  UIView *host = overlay.window.rootViewController.view ?: (UIView *)overlay.window;
  // NO window-level accessibilityElements mirror. Build 50 measured it doing
  // nothing on the device (Speak Screen still issued zero queries with the
  // page vending straight from the window), and the AX probe then caught it
  // doing active harm: an explicit accessibilityElements list on the window
  // REPLACES automatic subview traversal, which hid the real text view below
  // from the very reader it exists for.
  if (overlay.window) overlay.window.accessibilityElements = nil;
  if (host && wantsReadingPage()) {
    NSString *pageText = [[NSString alloc] initWithBytes:text.data() length:text.size()
                                                encoding:NSUTF8StringEncoding] ?: @"";
    CGFloat px0 = 0, py0 = 0, ps = 0;
    const bool geo = panelGeometryPts(&px0, &py0, &ps);
    CPPageTextInputView *page = g_pageInput;
    if (!page || page.superview != host) {
      [g_pageInput removeFromSuperview];
      page = [[CPPageTextInputView alloc] initWithFrame:host.bounds];
      [host addSubview:page];
      g_pageInput = page;
      // Assistive tech may already have concluded this screen has no content;
      // a fresh element that nobody is told about stays unread until the next
      // screen change. Post it with the new view as the focus target.
      UIAccessibilityPostNotification(UIAccessibilityScreenChangedNotification, page);
      CrossPointDiag_log("UITextInput page view installed (WWDC26-219 pattern)");
    }
    if (geo) {
      const CGFloat panelW = (CGFloat)HalDisplay::LOGICAL_HEIGHT * ps;
      const CGFloat panelH = (CGFloat)HalDisplay::LOGICAL_WIDTH * ps;
      page.frame = CGRectMake(px0, py0, panelW, panelH);
      // Word rects are logical panel px; the view's own origin is the panel's
      // top-left, so words map with origin 0 and the panel scale.
      [page setPageText:pageText rects:v originX:0 originY:0 scale:ps];
    } else {
      // No geometry yet (before the first present). Text is still correct, but
      // the frame is a guess -- keep the view and let the level-triggered
      // rebuild above re-frame it once the panel has published its geometry.
      [page setPageText:pageText rects:v originX:0 originY:0 scale:1];
      CrossPointDiag_log("page view built before panel geometry -- will re-frame");
    }
    if (overlay.superview) [overlay.superview bringSubviewToFront:overlay];
  } else if (g_pageInput) {
    [g_pageInput removeFromSuperview];
    g_pageInput = nil;
    CrossPointDiag_log("UITextInput page view removed (mode off)");
  }
  g_queryBudget = 6;
  g_readingBudget = 8;
  g_builtMode = wantsReadingPage() ? 1 : 0;
  // Greppable like the rest: [A11Y]. The count and the first label are what
  // distinguish "elements built" from "assistive tech saw nothing".
  if (overlay.cpElements.count > 0) {
    UIAccessibilityElement *first = overlay.cpElements.firstObject;
    const CGRect f = first.accessibilityFrame;
    // rects -> lines makes the grouping visible: if these are equal, the
    // per-line grouping has silently degenerated to per-word and Speak Screen
    // will read with a pause after every word.
    CrossPointDiag_log("%u word rects -> %lu line elements; first \"%.40s\" at (%.0f,%.0f %.0fx%.0f) pts",
                       rectCount, (unsigned long)overlay.cpElements.count,
                       first.accessibilityLabel.UTF8String ?: "", f.origin.x, f.origin.y,
                       f.size.width, f.size.height);
    // Frames outside the screen are frames Speak Screen may simply skip. This
    // is not hypothetical: on an iPhone 13 mini the panel itself was measured
    // rendering at dst -252,510 -- off the left edge -- so on any device where
    // the panel lands off-screen, every element goes with it and the owner
    // gets "no speakable content" over a page that IS published and IS
    // reachable. The union-vs-bounds numbers make that diagnosis one line.
    CGRect unionF = CGRectNull;
    for (UIAccessibilityElement *el in overlay.cpElements)
      unionF = CGRectUnion(unionF, el.accessibilityFrame);
    const CGRect screen = overlay.window ? overlay.window.bounds : UIScreen.mainScreen.bounds;
    if (!CGRectIntersectsRect(unionF, screen)) {
      CrossPointDiag_log("WARNING: all %lu element frames are OFF-SCREEN (union %.0f,%.0f %.0fx%.0f vs screen %.0fx%.0f) -- assistive tech may skip them",
                         (unsigned long)overlay.cpElements.count, unionF.origin.x, unionF.origin.y,
                         unionF.size.width, unionF.size.height, screen.size.width, screen.size.height);
    } else if (!CGRectContainsRect(screen, unionF)) {
      CrossPointDiag_log("note: element union (%.0f,%.0f %.0fx%.0f) extends past the %.0fx%.0f screen",
                         unionF.origin.x, unionF.origin.y, unionF.size.width, unionF.size.height,
                         screen.size.width, screen.size.height);
    }
  } else {
    CrossPointDiag_log("page had %u rects but produced no elements", rectCount);
  }
  // Tell assistive tech the screen changed. After a page turn IT requested,
  // PageScrolled is the notification that means "same context, next page --
  // keep reading"; ScreenChanged would reset the reading session.
  if (g_pageTurnRequested) {
    g_pageTurnRequested = false;
    UIAccessibilityPostNotification(UIAccessibilityPageScrolledNotification, nil);
  } else {
    UIAccessibilityPostNotification(UIAccessibilityScreenChangedNotification, nil);
  }
}

// Keep the container reachable. Accessibility traversal is front-to-back, and
// SDL adds and rebuilds its own views (notably across a deep-sleep wake), so a
// container installed once can end up buried -- at which point assistive tech
// reports an empty screen even though the elements are perfectly well formed.
// Cheap enough to check every frame: a pointer compare against the last
// subview, and a re-order only when it has actually moved.
void CrossPointAccessibility_keepFront(void) {
  CPAccessibilityOverlay *overlay = g_overlay;
  if (!overlay) return;
  UIView *parent = overlay.superview;
  if (!parent) {
    // Lost its window entirely (a wake rebuilt the hierarchy). Reinstall.
    CrossPointDiag_log("container lost its window; reinstalling");
    CrossPointAccessibility_begin();
    return;
  }
  if (parent.subviews.lastObject != overlay) {
    CrossPointDiag_log("container was buried behind %lu view(s); raising",
                       (unsigned long)(parent.subviews.count - 1));
    [parent bringSubviewToFront:overlay];
  }
}

// Walk the tree the way an assistive technology does -- from the window, via
// the public UIAccessibility container API -- and report what is actually
// reachable. Reasoning about why VoiceOver "should" find the elements produced
// one wrong fix already; this answers it instead.
static void dumpTree(id node, int depth, int *found) {
  if (depth > 6 || !node) return;
  NSString *pad = [@"" stringByPaddingToLength:depth * 2 withString:@" " startingAtIndex:0];
  const BOOL isEl = [node isAccessibilityElement];
  // NSNotFound means "not a container", and on DEVICE (unlike the simulator)
  // plain views report exactly that -- build 46's log printed it as
  // 9223372036854775807 on every node, which buried the real numbers.
  NSInteger count = 0;
  if ([node respondsToSelector:@selector(accessibilityElementCount)])
    count = [node accessibilityElementCount];
  const bool container = count != NSNotFound && count > 0;
  NSString *label = [node respondsToSelector:@selector(accessibilityLabel)]
                        ? ([node accessibilityLabel] ?: @"")
                        : @"";
  if (isEl && label.length > 0) (*found)++;
  // The flags UIKit's own traversal filters on. The dump walks subviews
  // manually, so it can SEE elements UIKit would skip -- hidden, transparent,
  // or behind a modal -- and without these flags that difference is invisible,
  // which is precisely the gap between "my walk found 15" and "Speak Screen
  // found nothing".
  char flags[64] = "";
  if ([node isKindOfClass:UIView.class]) {
    UIView *v = (UIView *)node;
    snprintf(flags, sizeof(flags), "%s%s%s%s%s",
             v.hidden ? " HIDDEN" : "",
             v.alpha < 0.01 ? " ALPHA0" : "",
             v.accessibilityElementsHidden ? " ELEMS-HIDDEN" : "",
             v.accessibilityViewIsModal ? " MODAL" : "",
             [v isKindOfClass:UITextField.class] && ((UITextField *)v).isFirstResponder
                 ? " FIRST-RESPONDER" : "");
  }
  CrossPointDiag_log("TREE %s%s isElement=%d children=%s%s label=\"%s\"", pad.UTF8String,
                     NSStringFromClass([node class]).UTF8String, (int)isEl,
                     count == NSNotFound ? "nc" : [@(count).stringValue UTF8String], flags,
                     [label substringToIndex:MIN((NSUInteger)28, label.length)].UTF8String);
  if (container) {
    for (NSInteger i = 0; i < count && i < 6; i++) {
      if ([node respondsToSelector:@selector(accessibilityElementAtIndex:)])
        dumpTree([node accessibilityElementAtIndex:i], depth + 1, found);
    }
  }
  if ([node isKindOfClass:UIView.class]) {
    for (UIView *sub in [(UIView *)node subviews]) dumpTree(sub, depth + 1, found);
  }
}

void CrossPointAccessibility_dumpTree(void) {
  UIWindow *window = resolveWindow();
  if (!window) { CrossPointDiag_log("TREE: no window"); return; }
  int found = 0;
  g_inDump = true;
  CrossPointDiag_log("TREE ---- traversal from the window ----");
  dumpTree(window, 0, &found);
  CrossPointDiag_log("TREE ---- reachable labelled elements: %d ----", found);
  g_inDump = false;
}

bool CrossPointAccessibility_hasElements(void) {
  CPAccessibilityOverlay *overlay = g_overlay;
  return overlay != nil && overlay.cpElements.count > 0;
}

// Throttled: the first 6 queries after each page change are logged with
// timestamps, then silence until the next page. Speak Screen reading a page
// produces dozens of calls; the SIGNAL is that any arrived at all, and when.
void CrossPointAccessibility_noteReading(const char *what, long value) {
  if (g_readingBudget <= 0) return;
  g_readingBudget--;
  CrossPointDiag_log("READING %s(%ld) -- Speak Screen is consuming the page protocol", what, value);
  if (g_readingBudget == 0) CrossPointDiag_log("READING (muted until the next page)");
}

void CrossPointAccessibility_noteQuery(const char *what, long value) {
  // The tree dump walks the container through these same methods; logging its
  // own traversal as "assistive tech consulted us" would both lie and burn the
  // budget, muting the REAL query that follows.
  if (g_inDump) return;
  if (g_queryBudget <= 0) return;
  g_queryBudget--;
  CrossPointDiag_log("QUERY %s(%ld) -- assistive tech is consulting the container", what, value);
  if (g_queryBudget == 0) CrossPointDiag_log("QUERY (further queries muted until the next page)");
}

// Focus landing on one of our elements is the strongest possible signal: the
// assistive technology not only asked, it arrived. Speak Screen does not focus
// the way VoiceOver does, so absence proves nothing -- but presence ends the
// investigation of the exposure half outright.
// Keyboard clearance (owner ruling 2026-08-09). WillChangeFrame carries the
// final frame and fires for show, hide, split/undock and height changes
// (predictive bar, language switch) -- the one notification that covers every
// way the keyboard's height can move. The height is converted to the window's
// point space and handed to the layout, which reserves it at the bottom so the
// panel lifts clear.
void CrossPointAccessibility_installKeyboardObserver(void) {
  static bool installed = false;
  if (installed) return;
  installed = true;
  [NSNotificationCenter.defaultCenter
      addObserverForName:UIKeyboardWillChangeFrameNotification
                  object:nil
                   queue:NSOperationQueue.mainQueue
              usingBlock:^(NSNotification *note) {
                UIWindow *window = resolveWindow();
                if (!window) return;
                const CGRect endFrame =
                    [note.userInfo[UIKeyboardFrameEndUserInfoKey] CGRectValue];
                // Intersect with the window: an off-screen (dismissed) frame
                // sits below the bottom edge and must read as zero, and a
                // floating/split keyboard only counts for what it covers.
                const CGRect covered = CGRectIntersection(window.bounds, endFrame);
                const CGFloat h = CGRectIsNull(covered) ? 0 : covered.size.height;
                CrossPointIOS_setKeyboardHeight((float)h);
                CrossPointDiag_log("keyboard height %.0f pt", (double)h);
              }];
}

void CrossPointAccessibility_installFocusObserver(void) {
  static bool installed = false;
  if (installed) return;
  installed = true;
  [NSNotificationCenter.defaultCenter
      addObserverForName:UIAccessibilityElementFocusedNotification
                  object:nil
                   queue:NSOperationQueue.mainQueue
              usingBlock:^(NSNotification *note) {
                id el = note.userInfo[UIAccessibilityFocusedElementKey];
                NSString *label = [el respondsToSelector:@selector(accessibilityLabel)]
                                      ? ([el accessibilityLabel] ?: @"")
                                      : @"";
                CrossPointDiag_log("FOCUS %s \"%s\"",
                                   NSStringFromClass([el class]).UTF8String,
                                   [label substringToIndex:MIN((NSUInteger)28, label.length)].UTF8String);
              }];
}

bool CrossPointAccessibility_modeChanged(void) {
  // LEVEL-triggered, not edge-triggered, and that is the fix for "Speak Screen
  // sometimes needs a page turn before it works" (owner, 2026-08-09).
  //
  // This used to compare the current mode against the mode the elements were
  // BUILT in -- an edge. One rebuild that did not produce a page view (the
  // classic case: panelGeometryPts is not answerable before the first present,
  // so a rebuild racing the first frame builds nothing) cleared the edge
  // anyway, and nothing retried until the next publish. A page turn republished
  // and it worked, which is exactly the reported shape.
  //
  // Asking "does the world match what it should be" instead means any failed
  // or half-finished rebuild self-heals on the very next frame.
  if (g_builtMode < 0) return false;
  const bool wants = wantsReadingPage();
  if (wants != (g_pageInput != nil)) return true;
  return wants != (g_builtMode == 1);
}

void CrossPointAccessibility_notePageTurnRequested(void) { g_pageTurnRequested = true; }

void CrossPointAccessibility_clear(void) {
  CPAccessibilityOverlay *overlay = g_overlay;
  if (!overlay) return;
  // Only log a transition, not every no-op clear: Home repaints often, and a
  // log line per repaint would bury the signal.
  if (overlay.cpElements.count > 0) {
    CrossPointDiag_log("page cleared (reader left) -- Speak Screen correctly finds nothing until a book page renders");
  }
  overlay.cpElements = @[];
  overlay.accessibilityElements = @[];
  [g_pageInput clearPage];
  UIAccessibilityPostNotification(UIAccessibilityScreenChangedNotification, nil);
}
