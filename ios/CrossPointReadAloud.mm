#include "CrossPointReadAloud.h"

#import <AVFoundation/AVFoundation.h>
#import <UIKit/UIKit.h>
#import <objc/message.h>
#import <objc/runtime.h>

#include <cstdlib>

#include <SDL3/SDL.h>

#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

#include "CrossPointAccessibility.h"
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
uint32_t g_spokeSerial = 0;              // last serial seen to actually speak
uint32_t g_utteranceBaseByte = 0;        // page byte the utterance starts at
int g_lastEnabled = -1;                  // pref edge detector; -1 = re-apply
int g_lastRatePercent = -1;              // speaking-rate edge; -1 = first read
int g_lastCaptureWanted = -1;            // capture edge; toggle OR assistive tech
int g_awaitTicks = -1;                   // >0: frames left in AwaitingNextPage
int g_idleTicks = -1;                    // >0: frames stopped with the session up
bool g_highlightActive = false;
uint32_t g_hlOffset = 0;
uint32_t g_hlLen = 0;

// ~5 s at the main loop's ~1 kHz (SDL_Delay(1)): the end-of-book detector.
constexpr int kAwaitTimeoutTicks = 5000;
// ~1.5 s on the same clock: how long the reader stays stopped before the audio
// session is handed back. Not immediate, because stopSpeakingAtBoundary winds
// the engine down asynchronously and deactivating into that returns "busy".
constexpr int kIdleReleaseTicks = 1500;
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

bool g_sessionActive = false;

// Lazy: the session is configured on the first actual speak, so a phone with
// the toggle off never has its audio session touched.
//
// Playback + spoken-audio is what makes this work everywhere it has to:
// audible with the ring/silent switch on silent, and — together with the
// UIBackgroundModes `audio` entry in Info.plist.in — still running with the
// screen locked, which is the whole point of listening to a book. Change
// either half and the other stops meaning anything.
void ensureAudioSession() {
  static bool categorySet = false;
  AVAudioSession *session = [AVAudioSession sharedInstance];
  NSError *err = nil;
  if (!categorySet) {
    categorySet = true;
    [session setCategory:AVAudioSessionCategoryPlayback
                    mode:AVAudioSessionModeSpokenAudio
                 options:0
                   error:&err];
    if (err) SDL_Log("[READALOUD] audio session category failed: %s",
                     err.localizedDescription.UTF8String);
    err = nil;
  }
  if (g_sessionActive) return;
  [session setActive:YES error:&err];
  if (err) {
    SDL_Log("[READALOUD] audio session activate failed: %s",
            err.localizedDescription.UTF8String);
    return;
  }
  g_sessionActive = true;
  g_idleTicks = -1;
}

// Hand the audio system back once the reader has been quiet for a moment.
//
// A playback session is NOT mixable, so holding one after the last word
// leaves whatever was playing before — a podcast, music — interrupted with no
// prospect of resuming. NotifyOthersOnDeactivation is the half that tells them
// to start again. It also stops the app holding background execution it is no
// longer using: with `audio` in UIBackgroundModes, an active session and a
// running loop is a phone that never sleeps.
//
// PAUSED IS NOT IDLE. The core keeps its state out of Off while an utterance
// is held, so a paused reader keeps the session and resumes instantly.
void releaseAudioSessionWhenIdle() {
  if (!g_sessionActive) return;
  if (g_core.state() != ReadAloudCore::State::Off) {
    g_idleTicks = -1;
    return;
  }
  if (g_idleTicks < 0) g_idleTicks = 0;
  if (++g_idleTicks < kIdleReleaseTicks) return;
  g_idleTicks = -1; // whether or not it works, restart the countdown
  NSError *err = nil;
  [[AVAudioSession sharedInstance]
        setActive:NO
      withOptions:AVAudioSessionSetActiveOptionNotifyOthersOnDeactivation
            error:&err];
  if (err) {
    // Busy is the expected failure and it cures itself; log it once so a
    // permanent one is still visible without a line every 1.5 s forever.
    static bool logged = false;
    if (!logged) {
      logged = true;
      SDL_Log("[READALOUD] audio session deactivate failed: %s (will retry)",
              err.localizedDescription.UTF8String);
    }
    return;
  }
  g_sessionActive = false;
  SDL_Log("[READALOUD] audio session released");
}

// The owner's percentage-of-normal onto AVSpeech's own 0..1 scale.
//
// That scale's DEFAULT is its MIDPOINT, not its top: 0.5 is ordinary speech,
// 1.0 is roughly double and 0.0 is unusably slow. So a percentage scales from
// Default, and 200% lands exactly on Maximum. Derived from the constants
// rather than hardcoded, so the day Apple moves them this still means "twice
// as fast as normal".
float rateForPercent(int percent) {
  float rate = AVSpeechUtteranceDefaultSpeechRate * (float)percent / 100.0f;
  if (rate < AVSpeechUtteranceMinimumSpeechRate)
    rate = AVSpeechUtteranceMinimumSpeechRate;
  if (rate > AVSpeechUtteranceMaximumSpeechRate)
    rate = AVSpeechUtteranceMaximumSpeechRate;
  return rate;
}

void startUtterance(uint32_t byteOffset) {
  if (byteOffset >= g_pageUtf8.size()) return;
  ensureAudioSession();
  // A stop delivered while the engine is PAUSED can leave the paused flag
  // standing, and speakUtterance: then queues behind it in silence — the
  // failure looks exactly like speech that simply did not start. Cheap to
  // rule out; continueSpeaking with nothing held is a no-op.
  if (g_synth.isPaused) {
    SDL_Log("[READALOUD] clearing a stale paused state before speaking");
    [g_synth continueSpeaking];
  }
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
  // Read LIVE, per utterance. rate is fixed once an utterance is speaking, so
  // this is the only moment it can be set at all; reading it here means every
  // new utterance — page, tap, resume-from-stop — already carries the current
  // setting, and restartAtCurrentWord is only needed to apply a change to the
  // utterance already in flight.
  const int percent = CrossPointPrefs_readAloudRatePercent();
  utt.rate = rateForPercent(percent);
  objc_setAssociatedObject(utt, kSerialKey, @(g_serial),
                           OBJC_ASSOCIATION_RETAIN_NONATOMIC);
  [g_synth speakUtterance:utt];
  // The voice is worth a line: voiceWithLanguage:nil answering nil is the
  // difference between "speech is silent" and "speech never started", and the
  // two look identical from anywhere else.
  SDL_Log("[READALOUD] utterance start serial=%u byteOff=%u rate=%d%% (%.3f) "
          "voice=%s",
          g_serial, byteOffset, percent, utt.rate,
          utt.voice ? utt.voice.identifier.UTF8String : "(none)");
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
        // Logged because a stop is otherwise INVISIBLE in a log: a tap that
        // stops reading and a tap that missed every word look the same from
        // outside, and a page turn's stop looks the same as neither.
        SDL_Log("[READALOUD] stopped serial=%u", g_serial);
        break;
      case ReadAloudCore::Action::PauseUtterance:
        // Immediate, not AVSpeechBoundaryWord. Play/pause has to answer like a
        // button; at 50% a word boundary is most of a second away, and a
        // control that responds when it feels like it reads as broken. The
        // resume picks up mid-word, which is what a pause is.
        [g_synth pauseSpeakingAtBoundary:AVSpeechBoundaryImmediate];
        SDL_Log("[READALOUD] paused");
        break;
      case ReadAloudCore::Action::ResumeUtterance:
        [g_synth continueSpeaking];
        SDL_Log("[READALOUD] resumed");
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

// --- Magic tap --------------------------------------------------------------
//
// THE APPLICATION DELEGATE IS THE RIGHT ANCHOR, and it is the only one needed.
// UIKit offers the magic tap to the focused accessibility element, then walks
// the responder chain, and asks the app delegate last — so a handler there
// catches the gesture no matter which of this app's surfaces the owner was on
// (the SDL view, an accessibility line element, the Speak Screen text input).
// Anchoring it on any one of those would cover only that one.
//
// Installed with the runtime because the delegate class is SDL's
// (SDLUIKitSceneDelegate, as of SDL3) and this repo does not own its header.
//
// THE GUARD IS class_addMethod's RETURN VALUE, not respondsToSelector, and
// that distinction is the whole reason this ever worked. UIKit declares
// accessibilityPerformMagicTap in a CATEGORY ON NSObject with a default that
// returns NO, so EVERY class in the process responds to it and the obvious
// guard refuses to install every single time — measured, on the first run of
// this code: "magic tap: SDLUIKitSceneDelegate already handles it", with no
// handler installed. class_addMethod overrides an inherited implementation
// and returns NO only when the class ITSELF implements one, which is exactly
// the question worth asking: an SDL that grows its own magic tap keeps it.
//
// WHAT THIS DOES NOT DO: conjure a gesture for everyone. Two-finger double tap
// is a VoiceOver gesture and only exists while VoiceOver (or AssistiveTouch,
// which can be given the same action) is on. For everyone else the
// finger-reachable control is tap-to-stop on the word being read.
BOOL cpPerformMagicTap(id self, SEL cmd) {
  (void)self;
  (void)cmd;
  return CrossPointReadAloud_magicTap() ? YES : NO;
}

void installMagicTapHandler() {
  id delegate = UIApplication.sharedApplication.delegate;
  if (!delegate) {
    SDL_Log("[READALOUD] magic tap: no application delegate to install on");
    return;
  }
  Class cls = object_getClass(delegate);
  SEL sel = @selector(accessibilityPerformMagicTap);
  // Built from @encode rather than a literal "B@:" so the BOOL encoding stays
  // right wherever this is compiled.
  NSString *types = [NSString stringWithFormat:@"%s%s%s", @encode(BOOL),
                                               @encode(id), @encode(SEL)];
  if (class_addMethod(cls, sel, (IMP)cpPerformMagicTap, types.UTF8String))
    SDL_Log("[READALOUD] magic tap installed on %s", class_getName(cls));
  else
    SDL_Log("[READALOUD] magic tap: %s implements its own; standing aside",
            class_getName(cls));
}

// --- QA hook ----------------------------------------------------------------
//
// Neither control added alongside it can be driven by an ordinary headless
// run: speech is inaudible to a test, and the magic tap is a VoiceOver gesture
// no script can perform. Without this they would ship on a unit test and a
// clean compile, which is not evidence that the platform half works.
//
// CROSSPOINT_SIM_READALOUD_SCRIPT fires them on the SDL_GetTicks millisecond
// clock CROSSPOINT_SIM_INPUT_SCRIPT already uses, through exactly the entry
// points UIKit and a finger use:
//
//   CROSSPOINT_SIM_READALOUD_SCRIPT='6000:MAGICTAP;8000:MAGICTAP;10000:TAPWORD'
//
//   MAGICTAP   what accessibilityPerformMagicTap calls
//   DELEGATETAP
//              sends accessibilityPerformMagicTap TO THE APPLICATION DELEGATE,
//              which is the message UIKit itself sends when the gesture goes
//              unhandled all the way up the responder chain. The only part of
//              the gesture left unproven after this is Apple's own routing.
//   TAPWORD    a tap at the centre of the word being spoken, in SCREEN pixels,
//              so the panel geometry and the hit-test are exercised too — which
//              makes it precisely the tap-to-stop case
//
// Parsed once, fired in order, never rearmed.
struct QaEvent {
  uint64_t atMs;
  int verb; // 0 = MAGICTAP, 1 = TAPWORD, 2 = DELEGATETAP
};
std::vector<QaEvent> g_qa;
size_t g_qaNext = 0;

void parseQaScript() {
  static bool parsed = false;
  if (parsed) return;
  parsed = true;
  const char *env = std::getenv("CROSSPOINT_SIM_READALOUD_SCRIPT");
  if (!env || !*env) return;
  const std::string spec(env);
  size_t pos = 0;
  while (pos < spec.size()) {
    size_t end = spec.find(';', pos);
    if (end == std::string::npos) end = spec.size();
    const std::string item = spec.substr(pos, end - pos);
    pos = end + 1;
    const size_t colon = item.find(':');
    if (colon == std::string::npos) continue;
    const std::string verb = item.substr(colon + 1);
    QaEvent ev;
    ev.atMs = std::strtoull(item.substr(0, colon).c_str(), nullptr, 10);
    if (verb == "MAGICTAP")
      ev.verb = 0;
    else if (verb == "TAPWORD")
      ev.verb = 1;
    else if (verb == "DELEGATETAP")
      ev.verb = 2;
    else {
      SDL_Log("[READALOUD] qa: unknown verb '%s'", verb.c_str());
      continue;
    }
    g_qa.push_back(ev);
  }
  SDL_Log("[READALOUD] qa script armed: %zu event(s)", g_qa.size());
}

void qaTapCurrentWord() {
  float x0, y0, S, w, h;
  if (!g_highlightActive || !panelGeometry(&x0, &y0, &S, &w, &h)) {
    SDL_Log("[READALOUD] qa: no highlighted word to tap");
    return;
  }
  for (const ReadAloudWordRect &r : g_rects) {
    if (r.byteOffset != g_hlOffset || r.byteLen != g_hlLen) continue;
    const float cx = x0 + ((float)r.x + (float)r.w * 0.5f) * S;
    const float cy = y0 + ((float)r.y + (float)r.h * 0.5f) * S;
    SDL_Log("[READALOUD] qa: tapping spoken word byte=%u at %.0f,%.0f px",
            r.byteOffset, cx, cy);
    CrossPointReadAloud_tapAtScreen(cx, cy);
    return;
  }
  SDL_Log("[READALOUD] qa: highlighted word has no rect to aim at");
}

// Deliver the gesture the way UIKit delivers it: as a message to the object
// UIApplication calls its delegate. Proves the installed override is the one
// that answers, which class_addMethod returning YES does not.
void qaDelegateMagicTap() {
  id delegate = UIApplication.sharedApplication.delegate;
  if (!delegate) {
    SDL_Log("[READALOUD] qa: no application delegate");
    return;
  }
  using MagicTapFn = BOOL (*)(id, SEL);
  const BOOL handled = ((MagicTapFn)objc_msgSend)(
      delegate, @selector(accessibilityPerformMagicTap));
  SDL_Log("[READALOUD] qa: delegate accessibilityPerformMagicTap -> %s",
          handled ? "YES" : "NO");
}

void pumpQaScript() {
  if (g_qaNext >= g_qa.size()) return;
  const uint64_t now = SDL_GetTicks();
  while (g_qaNext < g_qa.size() && now >= g_qa[g_qaNext].atMs) {
    const int verb = g_qa[g_qaNext].verb;
    g_qaNext++;
    switch (verb) {
      case 0:
        SDL_Log("[READALOUD] qa: magic tap");
        CrossPointReadAloud_magicTap();
        break;
      case 1:
        qaTapCurrentWord();
        break;
      default:
        qaDelegateMagicTap();
        break;
    }
  }
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
    installMagicTapHandler();
    parseQaScript();
    SDL_Log("[READALOUD] adapter installed");
  }
  // Seed the capture flag NOW, before the first loop() runs: a resumed book
  // renders its first page inside that first iteration, and a flag applied
  // lazily from perFrame (which runs after loop()) misses that page — the
  // exact race the desktop logger had. perFrame's edge detector then merely
  // confirms this value.
  gpio.setReadAloudCaptureWanted(CrossPointPrefs_readAloudEnabled() != 0);
  // Re-apply the prefs on the next perFrame — a wake is exactly when the
  // owner may have changed them in Settings. -1 on the rate also means "first
  // read", which suppresses the restart: there is nothing speaking to restart.
  g_lastEnabled = -1;
  g_lastRatePercent = -1;
}

void CrossPointReadAloud_perFrame(void) {
  if (!g_synth) return;

  // 1. The Settings toggle, edge-triggered.
  //
  // SPEECH follows the toggle alone -- turning VoiceOver on must not start the
  // app talking over it. CAPTURE follows either, because the accessibility
  // elements are built from the same published page and are worthless without
  // it. So the two are tracked separately: g_lastEnabled gates the core,
  // g_lastCaptureWanted gates the firmware's display-list walk.
  const int want = CrossPointPrefs_readAloudEnabled();
  if (want != g_lastEnabled) {
    g_lastEnabled = want;
    applyActions(g_core.setEnabled(want != 0));
    SDL_Log("[READALOUD] %s", want ? "enabled" : "disabled");
  }

  // 1b. The speaking rate, on the same terms and for the same reason: Settings
  // is a separate app, so a change to it arrives while this one is
  // backgrounded and there is no event to hang it on.
  const int ratePercent = CrossPointPrefs_readAloudRatePercent();
  if (ratePercent != g_lastRatePercent) {
    const bool firstRead = g_lastRatePercent < 0;
    g_lastRatePercent = ratePercent;
    SDL_Log("[READALOUD] speaking rate %d%% (AVSpeech rate %.3f)", ratePercent,
            rateForPercent(ratePercent));
    // An utterance's rate is fixed the moment it starts speaking, so applying
    // this to what is already in flight means a new utterance — from the same
    // word, so it sounds like a change of speed rather than a page reset. On
    // the first read nothing is speaking and there is nothing to restart.
    if (!firstRead) applyActions(g_core.restartAtCurrentWord());
  }
  // CAPTURE IS UNCONDITIONAL ON THE PHONE, and that is a deliberate reversal.
  //
  // It used to be gated on (toggle || assistive tech). The firmware publishes a
  // page only when it RENDERS one, so switching Speak Screen on while a page was
  // already drawn flipped capture to wanted and then published nothing until the
  // next page turn -- and the owner got "no speakable content could be found on
  // the screen" while looking at a perfectly good page. Reported on build 42.
  //
  // Gating bought a display-list walk per render, on a phone, where that is
  // noise. Correctness is worth more than that, and an always-current page also
  // removes the wake and first-launch orderings that had the same hole.
  CrossPointAccessibility_keepFront();
  const bool a11yWants = CrossPointAccessibility_wantsPage();
  if (g_lastCaptureWanted != 1) {
    g_lastCaptureWanted = 1;
    gpio.setReadAloudCaptureWanted(true);
    SDL_Log("[READALOUD] page capture wanted (always, on iOS)");
  }
  (void)a11yWants;  // logged by wantsPage() on change; kept for that visibility

  // The container can be empty while we still hold a page: assistive tech
  // switched on after the last render, or a wake rebuilt the container. Push
  // what we have rather than waiting for a page turn that may never come.
  if (!g_pageUtf8.empty() && !g_rects.empty() &&
      (!CrossPointAccessibility_hasElements() || CrossPointAccessibility_modeChanged())) {
    CrossPointAccessibility_setPage(g_pageUtf8.data(), (unsigned)g_pageUtf8.size(),
                                    g_rects.data(), (unsigned)g_rects.size());
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
      // The SAME page, handed to assistive technology. This is why there is no
      // second channel consumer: the contract is one per build, and this drain
      // is it.
      CrossPointAccessibility_setPage(g_pageUtf8.empty() ? nullptr : g_pageUtf8.data(),
                                      (unsigned)g_pageUtf8.size(),
                                      g_rects.empty() ? nullptr : g_rects.data(),
                                      (unsigned)g_rects.size());
      static bool dumpedOnce = false;
      if (!dumpedOnce) { dumpedOnce = true; CrossPointAccessibility_dumpTree(); }
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
          // One line per utterance, on its first word. It is the only proof
          // that the engine is actually speaking rather than holding a silent
          // utterance, and without it a highlight that never appears has two
          // indistinguishable explanations.
          if (ev.serial != g_spokeSerial) {
            g_spokeSerial = ev.serial;
            SDL_Log("[READALOUD] speaking serial=%u (first word at byte %u)",
                    ev.serial, g_utteranceBaseByte + ev.byteOffset);
          }
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

  // 5. Give the audio system back once the reader has been stopped a while,
  // and run the QA hook. Both are counted/clocked here for the same reason as
  // the timeout above: the core is clock-free.
  releaseAudioSessionWhenIdle();
  pumpQaScript();
}

int CrossPointReadAloud_magicTap(void) {
  if (!g_synth) return 0;
  const std::vector<ReadAloudCore::Action> actions = g_core.toggleSpeech();
  if (actions.empty()) {
    // Nothing to toggle: read-aloud is off, or no book page is held. Reported
    // as unhandled so the system is free to offer the gesture elsewhere.
    SDL_Log("[READALOUD] magic tap ignored (nothing to toggle)");
    return 0;
  }
  applyActions(actions);
  return 1;
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
