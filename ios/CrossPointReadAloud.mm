#include "CrossPointReadAloud.h"

#import <AVFoundation/AVFoundation.h>
#import <objc/runtime.h>

#include <SDL3/SDL.h>

#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

#include "CrossPointPrefs.h"
#include "HalDisplay.h"
#include "HalGPIO.h"
#include "ReadAloudCore.h"
#include "SimulatorOverlay.h"

// The AVSpeech adapter. Everything below runs on the main thread EXCEPT the
// AVSpeechSynthesizerDelegate callbacks, which arrive on a private queue and
// therefore only enqueue events; perFrame drains them. The one decision the
// adapter makes itself is the serial filter: stopSpeakingAtBoundary: delivers
// its didCancel asynchronously, and without the filter that stale cancel
// lands after the next utterance has started and kills it.

namespace {

enum EvKind { kEvFinished, kEvCanceled, kEvWillSpeak };

struct Ev {
  EvKind kind;
  uint32_t serial;
  uint32_t byteOffset; // kEvWillSpeak: UTF-8 bytes into the UTTERANCE string
};

std::mutex g_evMutex;
std::vector<Ev> g_events; // delegate queue -> drained by perFrame

ReadAloudCore g_core;
std::string g_pageUtf8;                  // current page, the slicing source
std::vector<ReadAloudWordRect> g_rects;  // copy for the painter / hit-test
uint32_t g_serial = 0;                   // current utterance's serial
uint32_t g_utteranceBaseByte = 0;        // page byte the utterance starts at
int g_lastEnabled = -1;                  // pref edge detector; -1 = re-apply
int g_awaitTicks = -1;                   // >0: frames left in AwaitingNextPage
bool g_highlightActive = false;
uint32_t g_hlOffset = 0;
uint32_t g_hlLen = 0;

// ~5 s at the main loop's ~1 kHz (SDL_Delay(1)): the end-of-book detector.
constexpr int kAwaitTimeoutTicks = 5000;
// How long the injected page-forward press is held.
constexpr unsigned long kTurnHoldMs = 60;

const void *kSerialKey = &kSerialKey;

void enqueueEv(EvKind kind, uint32_t serial, uint32_t byteOffset) {
  std::lock_guard<std::mutex> lock(g_evMutex);
  g_events.push_back({kind, serial, byteOffset});
}

uint32_t serialOf(AVSpeechUtterance *utt) {
  NSNumber *n = objc_getAssociatedObject(utt, kSerialKey);
  return n ? n.unsignedIntValue : 0;
}

} // namespace

@interface CPReadAloudDelegate : NSObject <AVSpeechSynthesizerDelegate>
@end

@implementation CPReadAloudDelegate
- (void)speechSynthesizer:(AVSpeechSynthesizer *)syn
    didFinishSpeechUtterance:(AVSpeechUtterance *)utt {
  enqueueEv(kEvFinished, serialOf(utt), 0);
}
- (void)speechSynthesizer:(AVSpeechSynthesizer *)syn
    didCancelSpeechUtterance:(AVSpeechUtterance *)utt {
  enqueueEv(kEvCanceled, serialOf(utt), 0);
}
- (void)speechSynthesizer:(AVSpeechSynthesizer *)syn
    willSpeakRangeOfSpeechString:(NSRange)range
                       utterance:(AVSpeechUtterance *)utt {
  // range.location is UTF-16 CODE UNITS into utt.speechString; the channel
  // text and every rect offset are UTF-8 BYTES. Convert by measuring the
  // UTF-8 length of the prefix. perFrame rebases by the utterance's start
  // byte, because a tap can start an utterance mid-page.
  NSUInteger b = [[utt.speechString substringToIndex:range.location]
      lengthOfBytesUsingEncoding:NSUTF8StringEncoding];
  enqueueEv(kEvWillSpeak, serialOf(utt), (uint32_t)b);
}
@end

namespace {

AVSpeechSynthesizer *g_synth = nil;
CPReadAloudDelegate *g_delegate = nil;

// Lazy: the session is configured on the first actual speak, so a phone with
// the toggle off never has its audio session touched. Playback is what makes
// speech audible with the ring/silent switch on silent.
void ensureAudioSession() {
  static bool configured = false;
  if (configured) return;
  configured = true;
  AVAudioSession *session = [AVAudioSession sharedInstance];
  NSError *err = nil;
  [session setCategory:AVAudioSessionCategoryPlayback
                  mode:AVAudioSessionModeSpokenAudio
               options:0
                 error:&err];
  if (err) SDL_Log("[READALOUD] audio session category failed: %s",
                   err.localizedDescription.UTF8String);
  err = nil;
  [session setActive:YES error:&err];
  if (err) SDL_Log("[READALOUD] audio session activate failed: %s",
                   err.localizedDescription.UTF8String);
}

void startUtterance(uint32_t byteOffset) {
  if (byteOffset >= g_pageUtf8.size()) return;
  ensureAudioSession();
  g_serial++;
  g_utteranceBaseByte = byteOffset;
  // byteOffset is always a channel-derived word start, so a valid UTF-8
  // boundary by construction.
  NSString *text =
      [[NSString alloc] initWithBytes:g_pageUtf8.data() + byteOffset
                               length:g_pageUtf8.size() - byteOffset
                             encoding:NSUTF8StringEncoding];
  if (!text) {
    SDL_Log("[READALOUD] page text not valid UTF-8 at byte %u", byteOffset);
    return;
  }
  AVSpeechUtterance *utt = [AVSpeechUtterance speechUtteranceWithString:text];
  // nil language = the system default voice, which is the voice the owner
  // picked under Settings > Accessibility > Spoken Content > Voices.
  utt.voice = [AVSpeechSynthesisVoice voiceWithLanguage:nil];
  objc_setAssociatedObject(utt, kSerialKey, @(g_serial),
                           OBJC_ASSOCIATION_RETAIN_NONATOMIC);
  [g_synth speakUtterance:utt];
  SDL_Log("[READALOUD] utterance start serial=%u byteOff=%u", g_serial,
          byteOffset);
}

void applyActions(const std::vector<ReadAloudCore::Action> &actions) {
  for (const ReadAloudCore::Action &a : actions) {
    switch (a.type) {
      case ReadAloudCore::Action::StartUtterance:
        startUtterance(a.utteranceByteOffset);
        break;
      case ReadAloudCore::Action::StopUtterance:
        // The async didCancel this produces carries the old serial and is
        // dropped by the filter in perFrame.
        [g_synth stopSpeakingAtBoundary:AVSpeechBoundaryImmediate];
        break;
      case ReadAloudCore::Action::TurnPageForward:
        // A REAL button press, fired inside HalGPIO::update() where its
        // edges are visible to the firmware (queueButtonTap's header says
        // why perFrame injection cannot work). The firmware paginates,
        // persists progress, and re-publishes; the loop closes when that
        // page arrives on the channel.
        //
        // BTN_RIGHT, not BTN_DOWN: verified against the firmware 2026-08-08
        // (ReaderUtils::detectPageTurn) — next page is the RIGHT front button
        // (or the side PageForward, which the owner can disable entirely).
        // Known limitation: the firmware's nav-swap setting turns RIGHT into
        // page-back; accepted for v1 and noted in the plan.
        gpio.queueButtonTap(HalGPIO::BTN_RIGHT, kTurnHoldMs);
        g_awaitTicks = kAwaitTimeoutTicks;
        SDL_Log("[READALOUD] page turn queued");
        break;
      case ReadAloudCore::Action::SetHighlight:
        g_highlightActive = true;
        g_hlOffset = a.highlightByteOffset;
        g_hlLen = a.highlightByteLen;
        SimulatorOverlay::requestPresent();
        break;
      case ReadAloudCore::Action::ClearHighlight:
        g_highlightActive = false;
        SimulatorOverlay::requestPresent();
        break;
    }
  }
}

// Presented-panel geometry, shared by the painter and the tap hit-test so it
// lives in exactly one place. False until the first manual-placement present.
bool panelGeometry(float *x0, float *y0, float *scale, float *w, float *h) {
  const float panelW = (float)SimulatorOverlay::panelWidthPx();
  const float panelH = (float)SimulatorOverlay::panelHeightPx();
  if (panelW <= 0.0f || panelH <= 0.0f) return false;
  // Portrait presented width == landscape panel height, in LOGICAL panel
  // pixels, because the channel's rects are logical (the firmware lays out at
  // 1x whatever the render scale is).
  //
  // MUST be LOGICAL_HEIGHT, not DISPLAY_HEIGHT: the latter is multiplied by
  // CROSSPOINT_RENDER_SCALE (HalDisplay.h:57). On the desktop that scale is 1
  // and the two are identical, so this reads correct and tests clean; on iOS
  // it is 2, and every highlight came out half-width at half the x-offset --
  // a box sitting inside the wrong word. That is risk R5 in the plan, and it
  // can only ever show up on the 2x build.
  *scale = panelW / (float)HalDisplay::LOGICAL_HEIGHT;
  *x0 = (float)SimulatorOverlay::panelLeftPx();
  *y0 = (float)(SimulatorOverlay::panelBottomPx() -
                SimulatorOverlay::panelHeightPx());
  *w = panelW;
  *h = panelH;
  return true;
}

} // namespace

void CrossPointReadAloud_begin(void) {
  // Registrations once; state refreshes every call (deep-sleep wake contract,
  // same as CrossPointHarness_begin).
  static bool s_created = false;
  if (!s_created) {
    s_created = true;
    g_synth = [[AVSpeechSynthesizer alloc] init];
    g_delegate = [[CPReadAloudDelegate alloc] init];
    g_synth.delegate = g_delegate;
    SDL_Log("[READALOUD] adapter installed");
  }
  // Seed the capture flag NOW, before the first loop() runs: a resumed book
  // renders its first page inside that first iteration, and a flag applied
  // lazily from perFrame (which runs after loop()) misses that page — the
  // exact race the desktop logger had. perFrame's edge detector then merely
  // confirms this value.
  gpio.setReadAloudCaptureWanted(CrossPointPrefs_readAloudEnabled() != 0);
  // Re-apply the pref on the next perFrame — a wake is exactly when the
  // owner may have flipped it in Settings.
  g_lastEnabled = -1;
}

void CrossPointReadAloud_perFrame(void) {
  if (!g_synth) return;

  // 1. The Settings toggle, edge-triggered.
  const int want = CrossPointPrefs_readAloudEnabled();
  if (want != g_lastEnabled) {
    g_lastEnabled = want;
    gpio.setReadAloudCaptureWanted(want != 0);
    applyActions(g_core.setEnabled(want != 0));
    SDL_Log("[READALOUD] %s", want ? "enabled" : "disabled");
  }

  // 2. The page channel. Drain fully; only the last page matters.
  {
    ReadAloudPage page;
    bool got = false;
    ReadAloudPage last;
    while (gpio.consumeReadAloudPage(page)) {
      last = std::move(page);
      got = true;
    }
    if (got) {
      g_pageUtf8 = last.utf8;
      g_rects = last.rects;
      g_awaitTicks = -1; // the awaited page (or a clear) arrived
      applyActions(g_core.pageArrived(last));
    }
  }

  // 3. Speech-engine events, with the stale-serial filter.
  {
    std::vector<Ev> events;
    {
      std::lock_guard<std::mutex> lock(g_evMutex);
      events.swap(g_events);
    }
    for (const Ev &ev : events) {
      if (ev.serial != g_serial) continue; // a dead utterance's event
      switch (ev.kind) {
        case kEvFinished:
          applyActions(g_core.utteranceFinished());
          break;
        case kEvCanceled:
          applyActions(g_core.utteranceCanceled());
          break;
        case kEvWillSpeak:
          applyActions(
              g_core.willSpeakByte(g_utteranceBaseByte + ev.byteOffset));
          break;
      }
    }
  }

  // 4. End-of-book: the page turn produced no page. Counted here because the
  // core is clock-free.
  if (g_awaitTicks > 0 && --g_awaitTicks == 0) {
    g_awaitTicks = -1;
    SDL_Log("[READALOUD] page timeout — end of book?");
    applyActions(g_core.pageTimeout());
  }
}

void CrossPointReadAloud_paintHighlight(struct SDL_Renderer *r, int outWidthPx,
                                        int outHeightPx, int dark) {
  (void)outWidthPx;
  (void)outHeightPx;
  float x0, y0, S, w, h;
  if (!panelGeometry(&x0, &y0, &S, &w, &h)) return;
  SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
  // A warm marker wash over the panel palette's paper; dimmer in dark, where
  // the same alpha would glare against 121212.
  SDL_SetRenderDrawColor(r, 255, 200, 0, dark ? 60 : 80);
  // Every rect carrying the spoken range: a line-wrapped word owns several,
  // and this is what lights both halves with no special cases.
  for (const ReadAloudWordRect &rect : g_rects) {
    if (rect.byteOffset != g_hlOffset || rect.byteLen != g_hlLen) continue;
    SDL_FRect hl = {x0 + rect.x * S - 2.0f, y0 + rect.y * S - 2.0f,
                    rect.w * S + 4.0f, rect.h * S + 4.0f};
    SDL_RenderFillRect(r, &hl);
  }
}

void CrossPointReadAloud_tapAtScreen(float xPx, float yPx) {
  float x0, y0, S, w, h;
  if (!panelGeometry(&x0, &y0, &S, &w, &h)) return;
  if (xPx < x0 || xPx >= x0 + w || yPx < y0 || yPx >= y0 + h) return;
  const int lx = (int)((xPx - x0) / S);
  const int ly = (int)((yPx - y0) / S);
  applyActions(g_core.tapAtLogical(lx, ly));
}
