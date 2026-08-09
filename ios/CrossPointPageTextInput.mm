#import "CrossPointPageTextInput.h"

#include <SDL3/SDL.h>

#include <algorithm>

#include "CrossPointDiagLog.h"
#include "HalGPIO.h"

#import "CrossPointAccessibility.h"

// ---- integer-offset position/range, the standard UITextInput backing ----

@interface CPTextPosition : UITextPosition
@property(nonatomic) NSInteger idx;  // UTF-16 offset into the page text
+ (instancetype)pos:(NSInteger)i;
@end

@implementation CPTextPosition
+ (instancetype)pos:(NSInteger)i {
  CPTextPosition *p = [CPTextPosition new];
  p.idx = i;
  return p;
}
- (BOOL)isEqual:(id)other {
  return [other isKindOfClass:CPTextPosition.class] && ((CPTextPosition *)other).idx == self.idx;
}
- (NSUInteger)hash {
  return (NSUInteger)self.idx;
}
@end

@interface CPTextRange : UITextRange
@property(nonatomic) NSInteger s, e;
+ (instancetype)from:(NSInteger)s to:(NSInteger)e;
@end

@implementation CPTextRange
+ (instancetype)from:(NSInteger)s to:(NSInteger)e {
  CPTextRange *r = [CPTextRange new];
  r.s = MIN(s, e);
  r.e = MAX(s, e);
  return r;
}
- (BOOL)isEmpty {
  return self.s == self.e;
}
- (UITextPosition *)start {
  return [CPTextPosition pos:self.s];
}
- (UITextPosition *)end {
  return [CPTextPosition pos:self.e];
}
@end

@interface CPTextSelectionRect : UITextSelectionRect
@property(nonatomic) CGRect r;
@property(nonatomic) BOOL first, last;
@end

@implementation CPTextSelectionRect
- (CGRect)rect {
  return self.r;
}
- (NSWritingDirection)writingDirection {
  return NSWritingDirectionLeftToRight;
}
- (BOOL)containsStart {
  return self.first;
}
- (BOOL)containsEnd {
  return self.last;
}
- (BOOL)isVertical {
  return NO;
}
@end

// ---- the page view ----

namespace {
// One word, mapped to view coordinates and UTF-16 offsets.
struct Word {
  CGRect rect;
  NSInteger start, end;  // UTF-16
};
long g_tiBudget = 0;
void note(const char *what) {
  if (g_tiBudget <= 0) return;
  g_tiBudget--;
  CrossPointDiag_log("TEXTINPUT %s -- the UITextInput protocol is being consumed", what);
  if (g_tiBudget == 0) CrossPointDiag_log("TEXTINPUT (muted until the next page)");
}
}  // namespace

@implementation CPPageTextInputView {
  NSString *_text;
  std::vector<Word> _words;
  CPTextRange *_selected;
  __weak id<UITextInputDelegate> _cpInputDelegate;
  UITextInputStringTokenizer *_tokenizer;
}

@synthesize markedTextStyle = _markedTextStyle;

- (instancetype)initWithFrame:(CGRect)frame {
  if ((self = [super initWithFrame:frame])) {
    _text = @"";
    _selected = [CPTextRange from:0 to:0];
    // The stock tokenizer answers word/sentence/character granularity off this
    // view's own position math -- exactly what 219's sample leans on.
    _tokenizer = [[UITextInputStringTokenizer alloc] initWithTextInput:self];
    self.backgroundColor = UIColor.clearColor;
    self.userInteractionEnabled = NO;
    self.isAccessibilityElement = YES;
    // CausesPageTurn: when continuous reading exhausts this element, the
    // system sends accessibilityScroll(.next) -- the pairing WWDC26-219
    // documents. The turn is the same BTN_RIGHT tap the read-aloud adapter
    // uses, verified against the firmware's detectPageTurn.
    self.accessibilityTraits = UIAccessibilityTraitStaticText | UIAccessibilityTraitCausesPageTurn;
    self.accessibilityIdentifier = @"crosspoint.page-textinput";
  }
  return self;
}

- (void)setPageText:(NSString *)text
              rects:(const std::vector<ReadAloudWordRect> &)rects
            originX:(CGFloat)x0
            originY:(CGFloat)y0
              scale:(CGFloat)s {
  _text = text ?: @"";
  _words.clear();
  _words.reserve(rects.size());
  // The channel's offsets are UTF-8; UITextInput speaks UTF-16 through
  // NSString. Build the mapping once by walking the UTF-8 bytes alongside the
  // UTF-16 length of each decoded scalar.
  NSData *utf8 = [_text dataUsingEncoding:NSUTF8StringEncoding];
  const uint8_t *bytes = (const uint8_t *)utf8.bytes;
  const NSUInteger byteLen = utf8.length;
  std::vector<NSInteger> u8_to_u16(byteLen + 1, 0);
  NSInteger u16 = 0;
  for (NSUInteger i = 0; i < byteLen;) {
    u8_to_u16[i] = u16;
    const uint8_t b = bytes[i];
    NSUInteger adv = b < 0x80 ? 1 : (b < 0xE0 ? 2 : (b < 0xF0 ? 3 : 4));
    // A 4-byte UTF-8 scalar is a surrogate pair in UTF-16.
    u16 += adv == 4 ? 2 : 1;
    for (NSUInteger k = 1; k < adv && i + k <= byteLen; k++) u8_to_u16[i + k] = u8_to_u16[i];
    i += adv;
  }
  u8_to_u16[byteLen] = u16;
  for (const ReadAloudWordRect &r : rects) {
    if (r.byteOffset + r.byteLen > byteLen) continue;
    Word w;
    w.rect = CGRectMake(x0 + r.x * s, y0 + r.y * s, r.w * s, r.h * s);
    w.start = u8_to_u16[r.byteOffset];
    w.end = u8_to_u16[r.byteOffset + r.byteLen];
    _words.push_back(w);
  }
  _selected = [CPTextRange from:0 to:0];
  g_tiBudget = 12;
  // The element's plain-accessibility face, for technologies that read value
  // rather than walking the protocol.
  self.accessibilityValue = _text;
}

- (void)clearPage {
  _text = @"";
  _words.clear();
  _selected = [CPTextRange from:0 to:0];
  self.accessibilityValue = @"";
}

// ---- UITextInput: text and ranges ----

- (NSString *)textInRange:(UITextRange *)range {
  note("textInRange");
  CPTextRange *r = (CPTextRange *)range;
  if (!r) return nil;
  const NSInteger len = (NSInteger)_text.length;
  const NSInteger s = MAX((NSInteger)0, MIN(r.s, len));
  const NSInteger e = MAX(s, MIN(r.e, len));
  return [_text substringWithRange:NSMakeRange((NSUInteger)s, (NSUInteger)(e - s))];
}

- (void)replaceRange:(UITextRange *)range withText:(NSString *)text {
  // Read-only page.
}

- (UITextRange *)selectedTextRange {
  return _selected;
}

- (void)setSelectedTextRange:(UITextRange *)selectedTextRange {
  note("setSelectedTextRange");
  if ([selectedTextRange isKindOfClass:CPTextRange.class]) _selected = (CPTextRange *)selectedTextRange;
}

- (UITextRange *)markedTextRange {
  return nil;
}

- (void)setMarkedText:(NSString *)markedText selectedRange:(NSRange)selectedRange {
}

- (void)unmarkText {
}

- (UITextPosition *)beginningOfDocument {
  return [CPTextPosition pos:0];
}

- (UITextPosition *)endOfDocument {
  return [CPTextPosition pos:(NSInteger)_text.length];
}

- (UITextRange *)textRangeFromPosition:(UITextPosition *)fromPosition toPosition:(UITextPosition *)toPosition {
  return [CPTextRange from:((CPTextPosition *)fromPosition).idx to:((CPTextPosition *)toPosition).idx];
}

- (UITextPosition *)positionFromPosition:(UITextPosition *)position offset:(NSInteger)offset {
  const NSInteger i = ((CPTextPosition *)position).idx + offset;
  if (i < 0 || i > (NSInteger)_text.length) return nil;
  return [CPTextPosition pos:i];
}

- (UITextPosition *)positionFromPosition:(UITextPosition *)position
                             inDirection:(UITextLayoutDirection)direction
                                  offset:(NSInteger)offset {
  switch (direction) {
    case UITextLayoutDirectionRight:
      return [self positionFromPosition:position offset:offset];
    case UITextLayoutDirectionLeft:
      return [self positionFromPosition:position offset:-offset];
    case UITextLayoutDirectionDown:
    case UITextLayoutDirectionUp: {
      // Line-wise movement: hop to the word on the neighbouring line nearest in x.
      const NSInteger idx = ((CPTextPosition *)position).idx;
      const Word *cur = [self wordContaining:idx];
      if (!cur) return position;
      const CGFloat targetY = direction == UITextLayoutDirectionDown ? CGRectGetMaxY(cur->rect) + 1
                                                                     : CGRectGetMinY(cur->rect) - 1;
      const Word *best = nullptr;
      CGFloat bestDx = 1e9;
      for (const Word &w : _words) {
        if (!(CGRectGetMinY(w.rect) <= targetY && targetY <= CGRectGetMaxY(w.rect))) continue;
        const CGFloat dx = fabs(CGRectGetMidX(w.rect) - CGRectGetMidX(cur->rect));
        if (dx < bestDx) {
          bestDx = dx;
          best = &w;
        }
      }
      return best ? [CPTextPosition pos:best->start] : position;
    }
  }
  return position;
}

- (const Word *)wordContaining:(NSInteger)idx {
  for (const Word &w : _words) {
    if (idx >= w.start && idx < w.end) return &w;
  }
  return _words.empty() ? nullptr : &_words.front();
}

- (NSComparisonResult)comparePosition:(UITextPosition *)position toPosition:(UITextPosition *)other {
  const NSInteger a = ((CPTextPosition *)position).idx, b = ((CPTextPosition *)other).idx;
  return a < b ? NSOrderedAscending : (a > b ? NSOrderedDescending : NSOrderedSame);
}

- (NSInteger)offsetFromPosition:(UITextPosition *)from toPosition:(UITextPosition *)toPosition {
  return ((CPTextPosition *)toPosition).idx - ((CPTextPosition *)from).idx;
}

- (id<UITextInputDelegate>)inputDelegate {
  return _cpInputDelegate;
}

- (void)setInputDelegate:(id<UITextInputDelegate>)inputDelegate {
  note("setInputDelegate");
  _cpInputDelegate = inputDelegate;
}

- (id<UITextInputTokenizer>)tokenizer {
  note("tokenizer");
  return _tokenizer;
}

- (UITextPosition *)positionWithinRange:(UITextRange *)range farthestInDirection:(UITextLayoutDirection)direction {
  CPTextRange *r = (CPTextRange *)range;
  return (direction == UITextLayoutDirectionLeft || direction == UITextLayoutDirectionUp)
             ? [CPTextPosition pos:r.s]
             : [CPTextPosition pos:r.e];
}

- (UITextRange *)characterRangeByExtendingPosition:(UITextPosition *)position
                                       inDirection:(UITextLayoutDirection)direction {
  const NSInteger idx = ((CPTextPosition *)position).idx;
  return (direction == UITextLayoutDirectionLeft || direction == UITextLayoutDirectionUp)
             ? [CPTextRange from:0 to:idx]
             : [CPTextRange from:idx to:(NSInteger)_text.length];
}

- (NSWritingDirection)baseWritingDirectionForPosition:(UITextPosition *)position
                                          inDirection:(UITextStorageDirection)direction {
  return NSWritingDirectionLeftToRight;
}

- (void)setBaseWritingDirection:(NSWritingDirection)writingDirection forRange:(UITextRange *)range {
}

// ---- UITextInput: geometry ----

- (CGRect)firstRectForRange:(UITextRange *)range {
  note("firstRectForRange");
  CPTextRange *r = (CPTextRange *)range;
  CGRect acc = CGRectNull;
  CGFloat lineY = -1;
  for (const Word &w : _words) {
    if (w.end <= r.s || w.start >= r.e) continue;
    if (lineY < 0) lineY = CGRectGetMinY(w.rect);
    if (fabs(CGRectGetMinY(w.rect) - lineY) > 1) break;  // first line only
    acc = CGRectIsNull(acc) ? w.rect : CGRectUnion(acc, w.rect);
  }
  return CGRectIsNull(acc) ? CGRectZero : acc;
}

- (CGRect)caretRectForPosition:(UITextPosition *)position {
  const Word *w = [self wordContaining:((CPTextPosition *)position).idx];
  if (!w) return CGRectZero;
  return CGRectMake(CGRectGetMinX(w->rect), CGRectGetMinY(w->rect), 2, CGRectGetHeight(w->rect));
}

// The rects also drive Speak Screen's reading highlight (owner ruling
// 2026-08-09: leave it -- no workarounds; the system draws what it draws).
- (NSArray<UITextSelectionRect *> *)selectionRectsForRange:(UITextRange *)range {
  note("selectionRectsForRange");
  CPTextRange *r = (CPTextRange *)range;
  NSMutableArray<UITextSelectionRect *> *out = [NSMutableArray array];
  // Per-line unions of the intersecting words, the shape 219's sample returns.
  CGRect acc = CGRectNull;
  CGFloat lineY = -1e9;
  BOOL emittedAny = NO;
  for (const Word &w : _words) {
    if (w.end <= r.s || w.start >= r.e) continue;
    if (fabs(CGRectGetMinY(w.rect) - lineY) > 1 && !CGRectIsNull(acc)) {
      CPTextSelectionRect *sr = [CPTextSelectionRect new];
      sr.r = acc;
      sr.first = !emittedAny;
      emittedAny = YES;
      [out addObject:sr];
      acc = CGRectNull;
    }
    lineY = CGRectGetMinY(w.rect);
    acc = CGRectIsNull(acc) ? w.rect : CGRectUnion(acc, w.rect);
  }
  if (!CGRectIsNull(acc)) {
    CPTextSelectionRect *sr = [CPTextSelectionRect new];
    sr.r = acc;
    sr.first = !emittedAny;
    [out addObject:sr];
  }
  ((CPTextSelectionRect *)out.lastObject).last = YES;
  return out;
}

- (UITextPosition *)closestPositionToPoint:(CGPoint)point {
  note("closestPositionToPoint");
  const Word *best = nullptr;
  CGFloat bestD = 1e12;
  for (const Word &w : _words) {
    if (CGRectContainsPoint(w.rect, point)) return [CPTextPosition pos:w.start];
    const CGFloat dx = MAX(0.0, MAX(CGRectGetMinX(w.rect) - point.x, point.x - CGRectGetMaxX(w.rect)));
    const CGFloat dy = MAX(0.0, MAX(CGRectGetMinY(w.rect) - point.y, point.y - CGRectGetMaxY(w.rect)));
    const CGFloat d = dx * dx + dy * dy;
    if (d < bestD) {
      bestD = d;
      best = &w;
    }
  }
  return best ? [CPTextPosition pos:best->start] : [CPTextPosition pos:0];
}

- (UITextPosition *)closestPositionToPoint:(CGPoint)point withinRange:(UITextRange *)range {
  return [self closestPositionToPoint:point];
}

- (UITextRange *)characterRangeAtPoint:(CGPoint)point {
  CPTextPosition *p = (CPTextPosition *)[self closestPositionToPoint:point];
  const Word *w = [self wordContaining:p.idx];
  if (!w) return nil;
  return [CPTextRange from:w->start to:w->end];
}

// ---- UIKeyInput (required by UITextInput) ----

- (BOOL)hasText {
  return _text.length > 0;
}

- (void)insertText:(NSString *)text {
}

- (void)deleteBackward {
}

- (BOOL)accessibilityScroll:(UIAccessibilityScrollDirection)direction {
  if (direction == UIAccessibilityScrollDirectionNext ||
      direction == UIAccessibilityScrollDirectionRight) {
    CrossPointDiag_log("TEXTINPUT scroll next -> page turn");
    CrossPointAccessibility_notePageTurnRequested();
    gpio.queueButtonTap(HalGPIO::BTN_RIGHT, 60);
    return YES;
  }
  if (direction == UIAccessibilityScrollDirectionPrevious ||
      direction == UIAccessibilityScrollDirectionLeft) {
    CrossPointDiag_log("TEXTINPUT scroll prev -> page back");
    CrossPointAccessibility_notePageTurnRequested();
    gpio.queueButtonTap(HalGPIO::BTN_LEFT, 60);
    return YES;
  }
  return NO;
}

// Read-only: never become first responder, never take the keyboard.
- (BOOL)canBecomeFirstResponder {
  return NO;
}

@end
