#include "SimulatorDocumentOpen.h"

#include <SDL3/SDL.h>
#include <fcntl.h>
#include <unistd.h>

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>

#include "CrossPointState.h"
#include "HalStorage.h"
#include "SimulatorLifecycle.h"

namespace {

// How long to let the OS deliver a launch document (macOS LaunchServices'
// 'odoc' Apple Event, or iOS's launch URLContexts) before giving up and
// booting normally.
//
// This is a real cost on every ordinary launch, so it is a budget, not a sleep:
// the wait returns the instant a document arrives, and a launch with no document
// is the only case that pays it in full. 400 ms was chosen because it is long
// enough for the 'odoc' Apple Event to land on a cold start (measured well under
// 100 ms on desktop; not yet measured on iOS) and short enough to be invisible
// against the firmware's own boot, which spends longer than that painting the
// splash.
//
// Getting this wrong is not fatal in either direction: too short and the
// document falls through to the warm path, which still opens the book, just with
// a relaunch. That fallback is why this can stay conservative.
constexpr Uint64 kLaunchDocumentWaitMs = 400;

std::mutex gMutex;
std::string gPendingPath;   // set by the SDL watch, drained by the two entry points
std::string gPendingCardPath;  // set by requestOpenOfCardCopy (iOS import), card-relative
bool gStagedLaunchDocument = false;

// Extensions ReaderActivity can actually open. Finder and iOS only ever send
// .epub here -- CFBundleDocumentTypes is the one type each Info.plist declares
// -- but a desktop drag-and-drop onto the window can carry anything, and
// silently "opening" a .png as a book would be worse than declining it.
bool isReadableBook(const std::string &path) {
  static const char *kExtensions[] = {".epub", ".txt", ".xtc"};
  for (const char *ext : kExtensions) {
    const size_t extLen = std::strlen(ext);
    if (path.size() > extLen &&
        strcasecmp(path.c_str() + path.size() - extLen, ext) == 0) {
      return true;
    }
  }
  return false;
}

std::string baseName(const std::string &path) {
  const size_t slash = path.find_last_of('/');
  return slash == std::string::npos ? path : path.substr(slash + 1);
}

// SDL owns event->drop.data and frees it once the event is handled, so the
// string must be copied here and not held by pointer.
bool SDLCALL onSdlEvent(void * /*userdata*/, SDL_Event *event) {
  if (event && event->type == SDL_EVENT_DROP_FILE && event->drop.data) {
    std::lock_guard<std::mutex> lock(gMutex);
    gPendingPath = event->drop.data;
  }
  return true;  // a watch observes; it must not consume
}

std::string takePendingPath() {
  std::lock_guard<std::mutex> lock(gMutex);
  std::string path;
  path.swap(gPendingPath);
  return path;
}

std::string takePendingCardPath() {
  std::lock_guard<std::mutex> lock(gMutex);
  std::string path;
  path.swap(gPendingCardPath);
  return path;
}

// Point the firmware's boot routing at a book that is already on the card.
//
// The state-writing half of stageDocument(), without the copy: the caller (the
// iOS import) has already put the file at `cardPath` with its own collision
// rules, and re-copying it here would be at best redundant and at worst a
// truncating write racing the copy that just finished. Same three fields, same
// reasoning as stageDocument() below. No isReadableBook() re-check either: the
// import vetted the file against the firmware's own format list
// (.epub/.xtc/.xtch/.txt/.md, FsHelpers-cited in CrossPointBookImport.mm),
// which is broader than this module's desktop drag-and-drop list and is the
// authority for what ReaderActivity opens.
bool stageCardResident(const std::string &cardPath) {
  if (cardPath.empty()) return false;

  // Idempotent, and required when this runs before setup() (a cold-launch
  // import landing inside captureLaunchDocument's wait).
  Storage.begin();

  APP_STATE.loadFromFile();
  APP_STATE.openEpubPath = cardPath;
  APP_STATE.readerActivityLoadCount = 0;
  APP_STATE.lastSleepFromReader = true;
  APP_STATE.saveToFile();

  std::fprintf(stderr, "[SIM] document open: staged card copy %s\n",
               cardPath.c_str());
  return true;
}

// Read the whole book into memory before writing any of it.
//
// This is what makes it safe to "copy" a file onto itself, which happens the
// moment someone opens a book that already lives in the simulated SD card's
// /books -- the obvious streaming copy would open the destination O_TRUNC and
// destroy the source it was still reading. Buffering is not a perf choice here;
// it is the correctness one. Books are a few MB, and this is a desktop.
bool readHostFile(const std::string &path, std::vector<char> &out) {
  constexpr size_t kMaxBytes = 512u * 1024u * 1024u;

  const int fd = ::open(path.c_str(), O_RDONLY);
  if (fd < 0) {
    std::fprintf(stderr, "[SIM] document open: cannot read %s\n", path.c_str());
    return false;
  }

  char buffer[64 * 1024];
  ssize_t got;
  while ((got = ::read(fd, buffer, sizeof(buffer))) > 0) {
    if (out.size() + static_cast<size_t>(got) > kMaxBytes) {
      std::fprintf(stderr, "[SIM] document open: %s exceeds %zu bytes\n",
                   path.c_str(), kMaxBytes);
      ::close(fd);
      return false;
    }
    out.insert(out.end(), buffer, buffer + got);
  }
  const bool ok = got == 0;
  ::close(fd);
  if (!ok) {
    std::fprintf(stderr, "[SIM] document open: read failed for %s\n", path.c_str());
  }
  return ok;
}

// Put the book on the card and point the firmware's boot routing at it.
//
// Returns false when nothing was staged, so callers can skip the relaunch rather
// than restart into an unchanged state.
bool stageDocument(const std::string &hostPath) {
  if (hostPath.empty()) return false;
  if (!isReadableBook(hostPath)) {
    std::fprintf(stderr, "[SIM] document open: not a book, ignoring %s\n",
                 hostPath.c_str());
    return false;
  }

  const std::string name = baseName(hostPath);
  if (name.empty()) return false;

  std::vector<char> contents;
  if (!readHostFile(hostPath, contents)) return false;

  // Idempotent, and required: this runs before setup(), which is where the
  // firmware would otherwise be the first to call it.
  Storage.begin();
  Storage.ensureDirectoryExists("/books");

  const std::string cardPath = "/books/" + name;
  HalFile file;
  if (!Storage.openFileForWrite("DOC", cardPath.c_str(), file)) {
    std::fprintf(stderr, "[SIM] document open: cannot write %s\n", cardPath.c_str());
    return false;
  }
  const size_t written = contents.empty() ? 0 : file.write(contents.data(), contents.size());
  file.close();
  if (written != contents.size()) {
    std::fprintf(stderr, "[SIM] document open: short write for %s (%zu of %zu)\n",
                 cardPath.c_str(), written, contents.size());
    return false;
  }

  // The three fields main.cpp's boot routing reads to decide where to land.
  //
  // openEpubPath alone is not enough. readerActivityLoadCount is the crash
  // -recovery counter -- non-zero means "the last book wedged us, go to Home
  // instead" -- and a stale count from an earlier session would send this launch
  // to Home with the book ignored. lastSleepFromReader picks the branch that
  // clears openEpubPath before opening, which is the firmware's own guard
  // against a bad book bricking the boot: if this one crashes, the next launch
  // comes up on Home rather than crashing again.
  APP_STATE.loadFromFile();
  APP_STATE.openEpubPath = cardPath;
  APP_STATE.readerActivityLoadCount = 0;
  APP_STATE.lastSleepFromReader = true;
  APP_STATE.saveToFile();

  std::fprintf(stderr, "[SIM] document open: staged %s -> %s\n", hostPath.c_str(),
               cardPath.c_str());
  return true;
}

}  // namespace

namespace SimulatorDocumentOpen {

void captureLaunchDocument() {
  // ONCE PER PROCESS, not once per boot. This call sits after main()'s setjmp,
  // so the in-process (iOS) reboot re-runs it on every wake -- and it used to
  // install another SDL event watch each time (N wakes = N stacked watches,
  // each drop event delivered N times) and pay the 400 ms launch-document wait
  // again. A wake is not a launch: the OS delivers a launch document once, and
  // anything arriving later lands in pumpPendingOpen() from the main loop.
  // Same shape as CrossPointHarness_begin's s_watchesInstalled guard.
  //
  // Deliberately NOT a simreset-cleared static -- surviving the reboot is the
  // point. The desktop reboot is execvp, where a fresh process re-runs the
  // full path anyway.
  static bool s_ranThisProcess = false;
  if (s_ranThisProcess) return;
  s_ranThisProcess = true;

  // Early, because the event queue has to exist before LaunchServices delivers.
  // Refcounted against HalDisplay::begin()'s own SDL_Init, so the single
  // SDL_Quit() at the end of main() still tears everything down.
  if (!SDL_Init(SDL_INIT_VIDEO)) {
    std::fprintf(stderr, "[SIM] document open: SDL_Init failed: %s\n", SDL_GetError());
    return;
  }
  SDL_AddEventWatch(onSdlEvent, nullptr);

  // HalGPIO owns the event pump for the running simulator, but it does not exist
  // yet -- setup() has not been called. Pumping here is the one window where
  // nothing else is reading the queue, and the watch above is what keeps the
  // two from stealing from each other once it is.
  const Uint64 deadline = SDL_GetTicks() + kLaunchDocumentWaitMs;
  std::string cardPath;
  std::string path;
  do {
    SDL_PumpEvents();
    // Card copy first: on iOS the import watch runs before this module's watch
    // on the same drop event (it registered earlier), imports the file, and
    // requests its CARD copy -- which supersedes the raw source path, whose
    // Inbox original the import may already have deleted.
    cardPath = takePendingCardPath();
    if (!cardPath.empty()) break;
    path = takePendingPath();
    if (!path.empty()) break;
    SDL_Delay(5);
  } while (SDL_GetTicks() < deadline);

  if (!cardPath.empty()) {
    takePendingPath();  // the raw drop of the same document; do not double-handle
    gStagedLaunchDocument = stageCardResident(cardPath);
    return;
  }
  if (path.empty()) return;
  gStagedLaunchDocument = stageDocument(path);
}

void pumpPendingOpen() {
  const std::string cardPath = takePendingCardPath();
  if (!cardPath.empty()) {
    // The raw drop that produced this import (if any) is the same document;
    // the card copy is the one to open, never the Inbox/source original.
    takePendingPath();

    // The launch document arriving a second time -- iOS can replay a launch
    // URL late enough that the import runs again (an identical-size skip) and
    // re-requests the card copy captureLaunchDocument() already staged.
    if (gStagedLaunchDocument) {
      gStagedLaunchDocument = false;
      if (APP_STATE.openEpubPath == cardPath) return;
    }

    if (!stageCardResident(cardPath)) return;
    std::fprintf(stderr, "[SIM] document open: relaunching into %s\n",
                 APP_STATE.openEpubPath.c_str());
    SimulatorLifecycle::rebootForDocumentOpen();
    return;
  }

  const std::string path = takePendingPath();
  if (path.empty()) return;

  // The launch document, arriving a second time. macOS can deliver 'odoc' late
  // enough that captureLaunchDocument() misses it and it lands here instead --
  // in which case setup() has already run against the staged state and there is
  // nothing to do but let the book that is already opening finish.
  if (gStagedLaunchDocument) {
    gStagedLaunchDocument = false;
    if (APP_STATE.openEpubPath == "/books/" + baseName(path)) return;
  }

  if (!stageDocument(path)) return;

  // Relaunch, because the firmware chose its activity during setup() and offers
  // no way to be told "open this other book now" from outside. Deliberately not
  // rebootAsPowerWake() (which would have the firmware believe POWER was
  // pressed) nor rebootAsFirmwareRestart() (which is opt-in on desktop because a
  // firmware-initiated restart loses RTC_NOINIT state it depends on). This
  // restart carries its intent in a file the new process reads on the way up, so
  // it needs neither.
  std::fprintf(stderr, "[SIM] document open: relaunching into %s\n",
               APP_STATE.openEpubPath.c_str());
  SimulatorLifecycle::rebootForDocumentOpen();
}

void requestOpenOfCardCopy(const char *cardPath) {
  if (!cardPath || !*cardPath) return;
  std::lock_guard<std::mutex> lock(gMutex);
  gPendingCardPath = cardPath;
}

}  // namespace SimulatorDocumentOpen
