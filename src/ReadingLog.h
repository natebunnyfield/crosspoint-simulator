#pragma once

// THE READING LEDGER — what was read, under what settings, for how long.
//
// Owner's ask, 2026-08-25: *"usage tracking into the iOS app that tracks which
// font, color, and other settings I used the most and got the most reading
// done with and got the least reading done with. We wanna be able to
// empirically base what actually worked for me."*
//
// The design, the outcome definitions, the confound strategy and the power
// estimate — including the part where the honest answer to "how long until
// this can tell two good fonts apart" is *longer than you want* — are in
// docs/reading-experiments.md. Read that before changing the schema. This
// header is only the model and the sink.
//
// WHAT IT IS. An append-only JSONL file. Three line kinds:
//
//   cfg    the typography + host dials in force, written ONLY when they change
//   page   one displayed reader page: which page, how much text, which cfg
//   evt    a boundary — launch, sleep, or the reader leaving for another screen
//
// A `page` line names its `cfg` by id rather than restating twenty fields, so
// a page line stays about 150 bytes and the settings are still exact. Every
// outcome — words per minute, session length, time to abandonment, volume per
// day — is DERIVED from that stream by tools/reading_report.py, offline, and
// nothing is computed on the device. That is deliberate: an outcome definition
// baked into the logger is an outcome definition that cannot be revised when
// it turns out to be the wrong one, and it will.
//
// WHAT IT COSTS. One `page` line per page turn: a struct walk, an FNV-1a over
// about fifty bytes, a ~150-byte snprintf and an fopen/fwrite/fclose. Against
// the 30–130 ms a page turn already costs to composite, that is noise. It is
// deliberately NOT batched in memory: a phone that is killed while backgrounded
// would lose the buffer, and the whole value of the file is that it is complete.
//
// WHERE IT IS NOT. It never leaves the device. There is no endpoint, no
// upload, no analytics, and nothing in this header opens a socket. The one
// place that ruling has teeth beyond good intentions is the PATH: on iOS the
// app's Documents directory IS the emulated SD card (ios/CrossPointFsPrep.cpp),
// and the file-transfer screen serves that card over HTTP/WebDAV bound to ALL
// interfaces. A log written into the card would therefore be published on the
// LAN every time the owner moved a book across. So it is written to
// Library/Application Support instead, which UIFileSharingEnabled does not
// expose and the web server cannot reach. Getting it OFF the phone is a
// deliberate act — see kExportRequestPath below.
//
// PURE WHERE IT DECIDES, INLINE WHERE IT WRITES. configId, the escaping, the
// three line builders and the rotation rule are pure and host-tested
// (tests/reading_log_test.cpp), because their entire failure surface is a WRONG
// NUMBER IN A FILE: nothing renders differently, nothing crashes, no compiler
// sees it, and the mistake surfaces a year later as a conclusion that was never
// true. A config id that collides silently merges two arms into one. A config
// id that changes when nothing changed shatters a comparison into singletons.
// Neither announces itself.

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>

#include "ReadingChannel.h"

namespace readinglog {

// Bump when a line's MEANING changes, never for an added field: every reader of
// this file must tolerate unknown keys, and tools/reading_report.py does.
inline constexpr int kSchemaVersion = 1;

// RETENTION. 4 MiB per generation, twelve generations kept, so 48 MiB is the
// hard ceiling and nothing here can grow without bound. At roughly 150 bytes a
// page line and a page turn every 30 s of reading, an hour of reading a day is
// ~430 KB a year — so twelve generations is on the order of a century of this
// owner's reading, and the cap exists for the pathological case (a stuck
// re-render loop) rather than the ordinary one. Rotation is a rename chain,
// never a truncate: the question a ledger answers is usually about a month
// that already ended.
inline constexpr long kRotateBytes = 4L * 1024 * 1024;
inline constexpr int kGenerations = 12;

// configId's "nothing published yet" sentinel. No id this header produces may
// be 0; configId folds to kNeverZero instead. Same discipline as
// SheetIdentity.h's seeds, and for the same reason — a 0 coming out of a hash
// would be read as "no config line has been written", and the first genuine
// config of a session would silently never be recorded.
inline constexpr uint32_t kNeverZero = 0x52444347u;  // 'RDCG'

// WHAT THE HOST ADDS to the firmware's typography. Split this way because the
// two halves have different owners: the firmware knows what it laid the text
// out with, and only the simulator knows what the page was PAINTED with.
//
// Note what is absent. The page palette is FROZEN on iOS (src/FrozenPage.h,
// owner ruling 2026-08-24) — one ink, one paper, one phosphor blend — so `ink`
// and `paper` are constants today and are recorded anyway, precisely so that
// the day the freeze lifts, every line already says which side of that change
// it was on. A field that starts being recorded on the day it starts varying
// is a field whose "before" is missing.
struct HostSnapshot {
  const char* device = "";  // "X3", "X4", ...
  int renderScale = 1;
  int panelW = 0;
  int panelH = 0;
  bool dark = false;   // the live polarity: it changes the page and the reader chose it
  uint32_t ink = 0;    // 0xRRGGBB
  uint32_t paper = 0;  // 0xRRGGBB

  // PHASE 2, and empty in Phase 1. When the randomizer is switched on these say
  // which experiment assigned this configuration and which arm it is, and
  // `armSeed` is what makes the whole assignment re-derivable from the log
  // rather than taken on trust. See ReadingArm.h.
  const char* experiment = "";
  const char* arm = "";
  uint64_t armSeed = 0;
};

// --- pure: identity -------------------------------------------------------

namespace detail {

inline void fnvBytes(uint32_t& h, const void* p, size_t n) {
  const unsigned char* b = static_cast<const unsigned char*>(p);
  for (size_t i = 0; i < n; i++) {
    h ^= b[i];
    h *= 16777619u;
  }
}

inline void fnvStr(uint32_t& h, const char* s) {
  // The NUL is folded in as well, so ("ab","c") and ("a","bc") cannot collide.
  fnvBytes(h, s ? s : "", s ? std::strlen(s) : 0);
  const unsigned char z = 0;
  fnvBytes(h, &z, 1);
}

inline void fnvU32(uint32_t& h, uint32_t v) { fnvBytes(h, &v, sizeof v); }

}  // namespace detail

// WHICH CONFIGURATION THIS PAGE WAS READ UNDER.
//
// FNV-1a over exactly the fields that change what the reader sees, and nothing
// else. The book, the page ordinal, the counts and the clock are deliberately
// NOT in it: a config id has to be the same for two pages read the same way in
// two different books, or there is nothing to compare.
//
// Every field of both structs that affects the page is folded in. If a new one
// is added to either and not added here, two genuinely different renderings
// share an id and the analysis averages them together — which is the silent
// failure this whole header is written pure to make testable.
inline uint32_t configId(const ReadingPageSample& s, const HostSnapshot& h) {
  uint32_t v = 2166136261u;
  detail::fnvStr(v, s.fontFamily);
  detail::fnvU32(v, s.fontPointSize);
  detail::fnvU32(v, s.fontSizeSlot);
  detail::fnvU32(v, s.lineSpacing);
  detail::fnvU32(v, s.lineGridEnabled);
  detail::fnvU32(v, s.justifyThresholdChars);
  detail::fnvU32(v, s.ligaturesEnabled);
  detail::fnvStr(v, s.ligaturesOff);
  detail::fnvU32(v, s.lineBreakMode);
  detail::fnvU32(v, s.screenMargin);
  detail::fnvStr(v, h.device);
  detail::fnvU32(v, static_cast<uint32_t>(h.renderScale));
  detail::fnvU32(v, static_cast<uint32_t>(h.panelW));
  detail::fnvU32(v, static_cast<uint32_t>(h.panelH));
  detail::fnvU32(v, h.dark ? 1u : 0u);
  detail::fnvU32(v, h.ink);
  detail::fnvU32(v, h.paper);
  detail::fnvStr(v, h.experiment);
  detail::fnvStr(v, h.arm);
  detail::fnvU32(v, static_cast<uint32_t>(h.armSeed & 0xFFFFFFFFu));
  detail::fnvU32(v, static_cast<uint32_t>(h.armSeed >> 32));
  return v ? v : kNeverZero;
}

// Must a `cfg` line be written before this page's line?
//
// `prev` is 0 when nothing has been written this run — which is the case that
// matters, and the reason this is a named function rather than an inline `!=`.
// A relaunch starts a new FILE POSITION, not a new configuration, so the first
// page after a launch must always be preceded by a cfg line even though the
// settings did not change: otherwise a reader of the log that starts at the
// launch boundary has a `cfg` reference it cannot resolve.
inline bool needsConfigLine(uint32_t prev, uint32_t cur) { return prev != cur; }

// --- pure: escaping and line building -------------------------------------

// JSON string body, escaped, with no surrounding quotes.
//
// Conservative on purpose: the two strings that reach it are a font family name
// off the SD card and a ligature spec, and a family name is whatever a person
// called a folder. A raw control byte or a quote in one of those would produce
// a line no JSON parser accepts, and the loss would be silent — the append
// succeeds, the report skips the line.
inline void appendEscaped(std::string& out, const char* s) {
  if (!s) return;
  for (const unsigned char* p = reinterpret_cast<const unsigned char*>(s); *p; ++p) {
    switch (*p) {
      case '"': out += "\\\""; break;
      case '\\': out += "\\\\"; break;
      case '\n': out += "\\n"; break;
      case '\r': out += "\\r"; break;
      case '\t': out += "\\t"; break;
      default:
        if (*p < 0x20) {
          char b[7];
          std::snprintf(b, sizeof b, "\\u%04x", static_cast<unsigned>(*p));
          out += b;
        } else {
          out += static_cast<char>(*p);
        }
    }
  }
}

namespace detail {

inline void addU(std::string& out, const char* key, unsigned long long v) {
  char b[48];
  std::snprintf(b, sizeof b, ",\"%s\":%llu", key, v);
  out += b;
}

inline void addI(std::string& out, const char* key, long long v) {
  char b[48];
  std::snprintf(b, sizeof b, ",\"%s\":%lld", key, v);
  out += b;
}

inline void addS(std::string& out, const char* key, const char* v) {
  out += ",\"";
  out += key;
  out += "\":\"";
  appendEscaped(out, v);
  out += '"';
}

inline void addHex(std::string& out, const char* key, uint32_t rgb) {
  char b[40];
  std::snprintf(b, sizeof b, ",\"%s\":\"%06X\"", key, rgb & 0xFFFFFFu);
  out += b;
}

// Every line opens the same way: kind, wall clock, monotonic clock.
//
// BOTH clocks, always. `ts` is unix seconds and is the only thing that can put
// a session at a time of day or order two launches; `ms` is the only thing that
// is monotonic. A phone's wall clock moves — timezone, NTP, the owner changing
// it — and a dwell computed across such a step is a negative number or an
// eight-hour page. The report groups on `ts` and can see when they disagree.
//
// `ms` IS MILLISECONDS SINCE THE PROCESS STARTED, NOT SINCE THE LAST `boot`
// LINE, and the two differ on exactly the platform that matters. The iOS wake
// is an in-process longjmp back into setup(), so publishBoot() runs again while
// upMs()'s epoch does not move — one iOS process spans every sleep/wake cycle
// until the OS kills it, and `ms` counts straight through them. That is the
// more useful of the two behaviours (it is the only clock that can measure a
// gap across a sleep without trusting the wall clock) but it is NOT what
// "since this launch" would lead you to expect, so it is written down here.
// tools/reading_report.py uses `ts` exclusively today.
inline std::string open(const char* kind, int64_t epochSec, uint32_t upMs) {
  std::string out = "{\"t\":\"";
  out += kind;
  out += '"';
  addI(out, "ts", epochSec);
  addU(out, "ms", upMs);
  return out;
}

}  // namespace detail

// The settings in force. Written whenever they change, and once after launch.
inline std::string configLine(const ReadingPageSample& s, const HostSnapshot& h, uint32_t cfg, int64_t epochSec,
                              uint32_t upMs) {
  std::string o = detail::open("cfg", epochSec, upMs);
  detail::addU(o, "id", cfg);
  detail::addS(o, "fam", s.fontFamily);
  detail::addU(o, "pt", s.fontPointSize);
  detail::addU(o, "slot", s.fontSizeSlot);
  detail::addU(o, "ls", s.lineSpacing);
  detail::addU(o, "grid", s.lineGridEnabled);
  detail::addU(o, "jt", s.justifyThresholdChars);
  detail::addU(o, "lig", s.ligaturesEnabled);
  detail::addS(o, "ligoff", s.ligaturesOff);
  detail::addU(o, "lb", s.lineBreakMode);
  detail::addU(o, "marg", s.screenMargin);
  detail::addS(o, "dev", h.device);
  detail::addU(o, "scale", static_cast<unsigned>(h.renderScale));
  detail::addU(o, "pw", static_cast<unsigned>(h.panelW));
  detail::addU(o, "ph", static_cast<unsigned>(h.panelH));
  detail::addU(o, "dark", h.dark ? 1u : 0u);
  detail::addHex(o, "ink", h.ink);
  detail::addHex(o, "paper", h.paper);
  detail::addS(o, "exp", h.experiment);
  detail::addS(o, "arm", h.arm);
  detail::addU(o, "armseed", h.armSeed);
  o += '}';
  return o;
}

// One displayed page.
//
// `bk` is the book key as sixteen hex digits rather than a path, and that is a
// privacy property as much as a compactness one: the ledger names no titles.
// It is still resolvable — readerBookKey() is FNV-1a over the path and
// tools/reading_report.py rehashes the paths on the card to put names back —
// so nothing is lost, and a log copied off the phone does not carry a reading
// list with it.
inline std::string pageLine(const ReadingPageSample& s, uint32_t cfg, int64_t epochSec, uint32_t upMs) {
  std::string o = detail::open("page", epochSec, upMs);
  detail::addU(o, "cfg", cfg);
  char b[40];
  std::snprintf(b, sizeof b, ",\"bk\":\"%016llx\"", static_cast<unsigned long long>(s.bookKey));
  o += b;
  detail::addS(o, "fmt", s.format);
  detail::addI(o, "sp", s.spineIndex);
  detail::addI(o, "pg", s.pageInSpine);
  detail::addU(o, "w", s.words);
  detail::addU(o, "c", s.chars);
  detail::addU(o, "ln", s.lines);
  o += '}';
  return o;
}

// A boundary: "boot", "sleep", "screen", "wake".
//
// `why` carries the sub-kind — the sleep reason, the screen's FNV key as a
// decimal string. One builder rather than three, because a boundary line has no
// structure worth three functions and the report treats them uniformly.
inline std::string eventLine(const char* kind, const char* why, int64_t epochSec, uint32_t upMs) {
  std::string o = detail::open("evt", epochSec, upMs);
  detail::addS(o, "k", kind);
  detail::addS(o, "why", why ? why : "");
  detail::addU(o, "v", kSchemaVersion);
  o += '}';
  return o;
}

// --- pure: retention ------------------------------------------------------

// Rotate BEFORE the write that would cross the ceiling, not after — so a
// generation never exceeds kRotateBytes and the 48 MiB cap is a real bound
// rather than a bound plus one line. `bytes` is the file's current size;
// `incoming` includes the newline.
inline bool shouldRotate(long bytes, size_t incoming) {
  if (bytes < 0) return false;  // stat failed: do not rotate on ignorance
  return bytes + static_cast<long>(incoming) > kRotateBytes;
}

// --- the sink -------------------------------------------------------------

// Filled by HalDisplay.cpp, which is the only place that knows the live palette
// and the live polarity. Declared here and defined there so this header does
// not have to include the display, which would make it untestable on a host
// with no SDL.
HostSnapshot hostSnapshot();

// Absolute path of the current generation. Empty when logging is off.
//
// Resolution order:
//   CROSSPOINT_SIM_READING_LOG   an explicit file path (tests, headless QA)
//   iOS      $HOME/Library/Application Support/CrossPointReading/reading.jsonl
//   desktop  <beside the simulated card>/reading.jsonl, like settings.json
std::string logPath();

// Append one line plus a newline, rotating first if it would cross the ceiling.
// Never throws, never blocks on anything but the file, and fails silently: a
// ledger that could take the reader down would be worse than no ledger.
void append(const std::string& line);

// PUBLISH ONE PAGE. The channel's whole consumer: emits a `cfg` line when the
// configuration has moved since the last one, then the `page` line.
void publishPage(const ReadingPageSample& s);

// Boundaries. Called from the simulator's own seams — no firmware change
// needed for any of them, because all three already reach this repo.
void publishBoot();
void publishSleep(const char* why);
void publishScreen(uint32_t screenKey);

// HOW THE DATA GETS OFF THE PHONE, and why it is a marker file rather than a
// button. The log deliberately lives where the Files app and the WebDAV server
// cannot see it (see the header note). That makes it unreachable, which for a
// tool whose entire output is a file the owner reads would be fatal. So: drop
// an empty file with this name into the card root from the Files app, relaunch,
// and every generation is copied into <card>/reading-log/ where Files can share
// it; the marker is removed so it happens once.
//
// A Settings.app row would be the obvious alternative and is the wrong one. The
// same day removed nine of them and the standing ruling is that a new row has
// to earn itself; an export that runs twice a year does not, and this costs no
// UI, no stored preference and no NSUserDefaults key.
inline constexpr const char* kExportRequestPath = "EXPORT-READING-LOG";

}  // namespace readinglog

// ---------------------------------------------------------------------------
// Implementation. Inline rather than a .cpp because the iOS source set is
// GENERATED from the firmware's compile database (cmake/CrossPointSources.cmake)
// and a new translation unit here means regenerating it against a firmware
// checkout. Every other pure model in this repo is a header for its own
// reasons; this one is a header for that one as well.
// ---------------------------------------------------------------------------

#include <sys/stat.h>
#include <unistd.h>

// REQUIRED, not decorative: without it TARGET_OS_IPHONE is simply undefined and
// the #if below silently selects the DESKTOP path on a phone, which would put
// the ledger inside the emulated SD card -- the one place the header's privacy
// note says it must never be. A wrong answer here compiles, runs, and publishes
// the file on the LAN the next time the owner transfers a book.
#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <ctime>
#include <mutex>

// Declared rather than included. HalStorage.h drags in the whole Arduino/SdFat
// shim, and this header has to compile in a host test that links neither --
// which is the only way its pure half can be tested at all. One free-function
// declaration, matching HalStorage.h's exactly; a host test supplies a
// one-line stub.
std::string simulatorStorageRootForHost();

namespace readinglog {
namespace detail {

inline std::mutex& lock() {
  static std::mutex m;
  return m;
}

inline std::string defaultDir() {
  const char* home = std::getenv("HOME");
#if defined(TARGET_OS_IPHONE) && TARGET_OS_IPHONE
  // Application Support: written by the app, invisible to UIFileSharingEnabled,
  // unreachable by the file-transfer server. The directory is NOT created for
  // us on iOS, so append() makes it.
  if (home) return std::string(home) + "/Library/Application Support/CrossPointReading";
  return {};
#else
  // Desktop: beside the simulated card, exactly where settings.json goes, and
  // for the same reason -- a host artifact is not a file the firmware should
  // ever see through HalStorage.
  const std::string root = simulatorStorageRootForHost();
  const size_t slash = root.find_last_of('/');
  if (slash != std::string::npos && slash > 0) return root.substr(0, slash);
  (void)home;
  return ".";
#endif
}

// mkdir -p over one path. Idempotent; EEXIST is the normal case.
inline void makeDirs(const std::string& path) {
  for (size_t i = 1; i < path.size(); i++) {
    if (path[i] != '/') continue;
    ::mkdir(path.substr(0, i).c_str(), 0755);
  }
  ::mkdir(path.c_str(), 0755);
}

inline long fileSize(const char* path) {
  struct stat st {};
  if (::stat(path, &st) != 0) return -1;
  return static_cast<long>(st.st_size);
}

// Rename chain, oldest first, so nothing is ever overwritten by a younger
// generation. reading.11.jsonl is dropped; everything else steps down one.
inline void rotate(const std::string& base) {
  char from[512], to[512];
  std::snprintf(to, sizeof to, "%s.%d", base.c_str(), kGenerations - 1);
  ::remove(to);
  for (int i = kGenerations - 2; i >= 1; i--) {
    std::snprintf(from, sizeof from, "%s.%d", base.c_str(), i);
    std::snprintf(to, sizeof to, "%s.%d", base.c_str(), i + 1);
    ::rename(from, to);
  }
  std::snprintf(to, sizeof to, "%s.1", base.c_str());
  ::rename(base.c_str(), to);
}

inline int64_t nowEpochSec() { return static_cast<int64_t>(std::time(nullptr)); }

// Milliseconds since this process started.
//
// NOT SDL_GetTicks: this header must compile in a host test with no SDL linked,
// and the ledger only needs a monotonic origin, not the same one the input
// layer uses. NOT std::clock() either, which is CPU time -- an e-ink app that
// spends a page turn blocked would report a dwell of a few milliseconds, and
// the number would look entirely reasonable.
inline uint32_t upMs() {
  using clock = std::chrono::steady_clock;
  static const clock::time_point start = clock::now();
  return static_cast<uint32_t>(
      std::chrono::duration_cast<std::chrono::milliseconds>(clock::now() - start).count());
}

// The last config id written, per process. 0 means "nothing yet this launch",
// which needsConfigLine() treats as "write one" -- see its note.
//
// ATOMIC, AND NOT BECAUSE THERE IS A RACE TODAY. Traced 2026-08-25 by an
// adversarial pass: every access is already serialized by machinery outside
// this header. publishBoot() runs on the main thread strictly before the render
// task is first notified, and publishPage() runs on the render task inside
// ActivityManager's renderingMutex, which also wraps every activity transition
// -- so a transition cannot run while a page render is in flight. That is a
// real invariant and it holds; it is also entirely invisible from here,
// undocumented at either end, and a plain `static uint32_t` would depend on it
// silently. A future change that makes rendering concurrent with transitions,
// or a second consumer calling publishPage(), reintroduces genuine UB with no
// diagnostic anywhere near the mistake.
//
// The load/compare/store in publishPage() is deliberately NOT one atomic
// operation, because it does not need to be: the worst outcome of two threads
// interleaving there is a duplicate `cfg` line, which the report resolves to
// the same id and ignores. What relaxed atomics buy is that the race stops
// being undefined behaviour, which is the part that cannot be reasoned about.
inline std::atomic<uint32_t>& lastConfig() {
  static std::atomic<uint32_t> v{0};
  return v;
}

// One copy of the export, at boot. Silent on every failure: a missing marker is
// the normal case and a failed copy must not take the reader down.
inline void serviceExportRequest(const std::string& dir) {
  // Resolved against the CARD, not the cwd. On iOS those are the same directory
  // (the harness chdir()s into it) but on the desktop they are not -- the card
  // is ./fs_ under the working directory -- and a marker that only worked on
  // one platform is a marker nobody can test.
  const std::string root = simulatorStorageRootForHost();
  const std::string marker = root + "/" + kExportRequestPath;
  if (::access(marker.c_str(), F_OK) != 0) return;
  const std::string out = root + "/reading-log";
  ::mkdir(out.c_str(), 0755);
  // `dir` is the directory the ledger ACTUALLY lives in, passed in rather than
  // recomputed, so a run with CROSSPOINT_SIM_READING_LOG pointed somewhere else
  // exports the file it is really writing. std::string rather than a char[512]
  // for the same class of reason: an sandbox path plus a bundle name is not
  // obviously under any fixed length, and a silent snprintf truncation would
  // export a file that does not exist and report nothing.
  const std::string base = dir + "/reading.jsonl";
  for (int i = 0; i < kGenerations; i++) {
    const std::string suffix = i == 0 ? std::string() : ("." + std::to_string(i));
    const std::string src = base + suffix;
    const std::string dst = out + "/reading.jsonl" + suffix;
    FILE* in = ::fopen(src.c_str(), "rb");
    if (!in) continue;
    FILE* o = ::fopen(dst.c_str(), "wb");
    if (!o) {
      ::fclose(in);
      continue;
    }
    char buf[8192];
    size_t n;
    while ((n = ::fread(buf, 1, sizeof buf, in)) > 0) ::fwrite(buf, 1, n, o);
    ::fclose(o);
    ::fclose(in);
  }
  ::remove(marker.c_str());
}

}  // namespace detail

inline std::string logPath() {
  if (const char* env = std::getenv("CROSSPOINT_SIM_READING_LOG")) {
    if (env[0]) return env;
  }
  const std::string dir = detail::defaultDir();
  if (dir.empty()) return {};
  return dir + "/reading.jsonl";
}

inline void append(const std::string& line) {
  const std::string path = logPath();
  if (path.empty()) return;
  std::lock_guard<std::mutex> guard(detail::lock());
  const size_t slash = path.find_last_of('/');
  if (slash != std::string::npos) detail::makeDirs(path.substr(0, slash));
  if (shouldRotate(detail::fileSize(path.c_str()), line.size() + 1)) detail::rotate(path);
  FILE* f = ::fopen(path.c_str(), "a");
  if (!f) return;
  std::fwrite(line.data(), 1, line.size(), f);
  std::fputc('\n', f);
  std::fclose(f);
}

inline void publishPage(const ReadingPageSample& s) {
  const HostSnapshot h = hostSnapshot();
  const uint32_t cfg = configId(s, h);
  const int64_t ts = detail::nowEpochSec();
  const uint32_t ms = detail::upMs();
  if (needsConfigLine(detail::lastConfig().load(std::memory_order_relaxed), cfg)) {
    append(configLine(s, h, cfg, ts, ms));
    detail::lastConfig().store(cfg, std::memory_order_relaxed);
  }
  append(pageLine(s, cfg, ts, ms));
}

inline void publishBoot() {
  detail::lastConfig().store(0, std::memory_order_relaxed);
  // The directory the ledger is really in -- logPath()'s parent, so an explicit
  // CROSSPOINT_SIM_READING_LOG is honoured rather than quietly bypassed.
  {
    const std::string path = logPath();
    const size_t slash = path.find_last_of('/');
    detail::serviceExportRequest(slash == std::string::npos ? std::string(".") : path.substr(0, slash));
  }
  append(eventLine("boot", "", detail::nowEpochSec(), detail::upMs()));
}

inline void publishSleep(const char* why) {
  append(eventLine("sleep", why, detail::nowEpochSec(), detail::upMs()));
}

inline void publishScreen(uint32_t screenKey) {
  char b[24];
  std::snprintf(b, sizeof b, "%u", screenKey);
  append(eventLine("screen", b, detail::nowEpochSec(), detail::upMs()));
}

}  // namespace readinglog
