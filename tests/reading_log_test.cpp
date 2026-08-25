// THE READING LEDGER'S MODEL. src/ReadingLog.h, src/ReadingChannel.h.
//
// Every failure this file exists to catch is a WRONG NUMBER IN A FILE. Nothing
// renders differently, nothing crashes, no compiler sees it, and the mistake
// surfaces a year later as a conclusion that was never true — which is worse
// than no conclusion, because it will have been acted on. Four shapes:
//
//   1. A CONFIG ID THAT COLLIDES. Two genuinely different renderings share an
//      id, the report averages them, and the effect it was measuring is halved
//      or erased. This is the failure that arrives when a new typography field
//      is added to the channel and not folded into configId — so every field
//      is swept here, one at a time, and adding one without a case makes this
//      test fail rather than making the data quietly wrong.
//   2. A CONFIG ID THAT MOVES WHEN NOTHING MOVED. The other direction, equally
//      silent: the comparison shatters into singletons and nothing ever reaches
//      significance. The book, the page ordinal and the counts must not touch
//      it.
//   3. A LINE NO PARSER ACCEPTS. A font family is whatever a person called a
//      folder on their card. One quote in it and the line is skipped by the
//      report, silently, and only that configuration's data disappears — which
//      looks exactly like "he didn't read much with that font."
//   4. A RETENTION RULE THAT DOES NOT BOUND. The whole ledger is an
//      append-only file on a phone.
//
// It also cross-checks the mirrored POD against the FIRMWARE's copy as text,
// where a sibling checkout exists — the same technique sheet_identity_test.cpp
// uses, and for the same reason: the two definitions cannot share a header (the
// firmware is not linked against this repo on device), and a divergence would
// not fail to compile. It would write plausible wrong numbers.

#include "../src/ReadingLog.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "TestCheck.h"

// The one symbol ReadingLog.h's desktop path needs and a host test does not
// link. See the declaration's note in that header.
std::string simulatorStorageRootForHost() { return "./fs_"; }

namespace {

ReadingPageSample baseSample() {
  ReadingPageSample s;
  s.bookKey = 0x0123456789abcdefull;
  s.spineIndex = 3;
  s.pageInSpine = 7;
  s.format = "epub";
  s.words = 214;
  s.chars = 1183;
  s.lines = 26;
  s.fontFamily = "Caledonia";
  s.fontPointSize = 15;
  s.fontSizeSlot = 1;
  s.lineSpacing = 1;
  s.lineGridEnabled = 0;
  s.justifyThresholdChars = 40;
  s.ligaturesEnabled = 1;
  s.ligaturesOff = "";
  s.lineBreakMode = 0;
  s.screenMargin = 5;
  return s;
}

readinglog::HostSnapshot baseHost() {
  readinglog::HostSnapshot h;
  h.device = "X3";
  h.renderScale = 2;
  h.panelW = 792;
  h.panelH = 528;
  h.dark = false;
  h.ink = 0x5C332B;
  h.paper = 0xF9F3E9;
  return h;
}

// --- 1. every rendering field moves the id, and nothing else does ----------

void testConfigIdSweepsEveryRenderingField() {
  const ReadingPageSample base = baseSample();
  const readinglog::HostSnapshot bh = baseHost();
  const uint32_t id0 = readinglog::configId(base, bh);

  // Each mutation is ONE field. A field added to either struct and forgotten in
  // configId has no entry here, and the totals at the foot of this function
  // catch that: they are the struct's own field counts, written out, so the
  // test fails the day a field appears rather than the day someone notices.
  int swept = 0;
  auto sweepSample = [&](ReadingPageSample s, const char* what) {
    const uint32_t id = readinglog::configId(s, bh);
    testcheck::check(id != id0, std::string("configId ignores ") + what);
    testcheck::check(id != 0, "configId never returns the 0 sentinel");
    swept++;
  };

  {
    ReadingPageSample s = base;
    s.fontFamily = "Bembo";
    sweepSample(s, "fontFamily");
  }
  {
    ReadingPageSample s = base;
    s.fontPointSize = 16;
    sweepSample(s, "fontPointSize");
  }
  {
    ReadingPageSample s = base;
    s.fontSizeSlot = 2;
    sweepSample(s, "fontSizeSlot");
  }
  {
    ReadingPageSample s = base;
    s.lineSpacing = 2;
    sweepSample(s, "lineSpacing");
  }
  {
    ReadingPageSample s = base;
    s.lineGridEnabled = 1;
    sweepSample(s, "lineGridEnabled");
  }
  {
    ReadingPageSample s = base;
    s.justifyThresholdChars = 55;
    sweepSample(s, "justifyThresholdChars");
  }
  {
    ReadingPageSample s = base;
    s.ligaturesEnabled = 0;
    sweepSample(s, "ligaturesEnabled");
  }
  {
    ReadingPageSample s = base;
    s.ligaturesOff = "st,fh";
    sweepSample(s, "ligaturesOff");
  }
  {
    ReadingPageSample s = base;
    s.lineBreakMode = 1;
    sweepSample(s, "lineBreakMode");
  }
  {
    ReadingPageSample s = base;
    s.screenMargin = 10;
    sweepSample(s, "screenMargin");
  }
  testcheck::check(swept == 10, "all ten typography fields are folded into configId");

  int hswept = 0;
  auto sweepHost = [&](readinglog::HostSnapshot h, const char* what) {
    const uint32_t id = readinglog::configId(base, h);
    testcheck::check(id != id0, std::string("configId ignores host ") + what);
    hswept++;
  };
  {
    readinglog::HostSnapshot h = bh;
    h.device = "X4";
    sweepHost(h, "device");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.renderScale = 1;
    sweepHost(h, "renderScale");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.panelW = 800;
    sweepHost(h, "panelW");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.panelH = 480;
    sweepHost(h, "panelH");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.dark = true;
    sweepHost(h, "dark");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.ink = 0x000000;
    sweepHost(h, "ink");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.paper = 0xFFFFFF;
    sweepHost(h, "paper");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.experiment = "font-size";
    sweepHost(h, "experiment");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.arm = "B";
    sweepHost(h, "arm");
  }
  {
    readinglog::HostSnapshot h = bh;
    h.armSeed = 0x1122334455667788ull;
    sweepHost(h, "armSeed");
  }
  testcheck::check(hswept == 10, "all ten host fields are folded into configId");
}

// A config id that moved with the book would make every book its own arm.
void testConfigIdIgnoresWhatIsNotAConfiguration() {
  const ReadingPageSample base = baseSample();
  const readinglog::HostSnapshot bh = baseHost();
  const uint32_t id0 = readinglog::configId(base, bh);

  ReadingPageSample other = base;
  other.bookKey = 0xdeadbeefcafef00dull;
  other.spineIndex = 99;
  other.pageInSpine = 0;
  other.format = "txt";
  other.words = 1;
  other.chars = 2;
  other.lines = 3;
  testcheck::check(readinglog::configId(other, bh) == id0,
        "configId is blind to the book, the page ordinal, the format and the counts");
}

// ("ab","c") and ("a","bc") must not collide -- the NUL is folded in for this.
void testConfigIdStringBoundaries() {
  const readinglog::HostSnapshot bh = baseHost();
  ReadingPageSample a = baseSample();
  a.fontFamily = "ab";
  a.ligaturesOff = "c";
  ReadingPageSample b = baseSample();
  b.fontFamily = "a";
  b.ligaturesOff = "bc";
  testcheck::check(readinglog::configId(a, bh) != readinglog::configId(b, bh),
        "adjacent strings cannot be shifted across their boundary");
}

// --- 2. the cfg-line decision ---------------------------------------------

void testNeedsConfigLine() {
  testcheck::check(readinglog::needsConfigLine(0, 1234u), "the first page of a launch always gets a cfg line");
  testcheck::check(!readinglog::needsConfigLine(1234u, 1234u), "an unchanged configuration is not restated");
  testcheck::check(readinglog::needsConfigLine(1234u, 5678u), "a changed configuration is written");
  // The reason the sentinel may never be produced by configId: a genuine id of
  // 0 would read as "nothing written yet" forever, and the cfg line would be
  // re-emitted on every single page turn.
  testcheck::check(!readinglog::needsConfigLine(0, 0), "0 == 0 would loop; configId can never return 0");
}

// --- 3. lines a parser accepts --------------------------------------------

std::string escaped(const char* s) {
  std::string out;
  readinglog::appendEscaped(out, s);
  return out;
}

void testEscaping() {
  testcheck::check(escaped("plain") == "plain", "ordinary text is untouched");
  testcheck::check(escaped("a\"b") == "a\\\"b", "a quote is escaped");
  testcheck::check(escaped("a\\b") == "a\\\\b", "a backslash is escaped");
  testcheck::check(escaped("a\nb") == "a\\nb", "a newline is escaped -- it would end the JSONL record");
  testcheck::check(escaped("a\tb") == "a\\tb", "a tab is escaped");
  testcheck::check(escaped("a\x01"
                "b") == "a\\u0001b",
        "a control byte becomes a \\u escape");
  testcheck::check(escaped(nullptr).empty(), "a null string is empty, not a crash");
  // UTF-8 passes through as bytes: a family name can legitimately be "Söhne".
  testcheck::check(escaped("S\xc3\xb6hne") == "S\xc3\xb6hne", "UTF-8 is not mangled");
}

// A deliberately small structural check rather than a JSON parser: the point is
// that every key the report reads is present and the record is balanced.
bool hasKey(const std::string& line, const char* key) {
  return line.find(std::string("\"") + key + "\":") != std::string::npos;
}

void testLineShapes() {
  const ReadingPageSample s = baseSample();
  const readinglog::HostSnapshot h = baseHost();
  const uint32_t cfg = readinglog::configId(s, h);

  const std::string c = readinglog::configLine(s, h, cfg, 1700000000, 4321);
  testcheck::check(c.front() == '{' && c.back() == '}', "cfg line is one balanced object");
  testcheck::check(c.find("\"t\":\"cfg\"") != std::string::npos, "cfg line is tagged");
  for (const char* k : {"ts", "ms", "id", "fam", "pt", "slot", "ls", "grid", "jt", "lig", "ligoff", "lb", "marg",
                        "dev", "scale", "pw", "ph", "dark", "ink", "paper", "exp", "arm", "armseed"}) {
    testcheck::check(hasKey(c, k), std::string("cfg line carries ") + k);
  }
  testcheck::check(c.find("\"ink\":\"5C332B\"") != std::string::npos, "ink is six upper-case hex digits");
  testcheck::check(c.find("\"fam\":\"Caledonia\"") != std::string::npos, "the family name is written out");
  testcheck::check(c.find('\n') == std::string::npos, "no line builder emits its own newline");

  const std::string p = readinglog::pageLine(s, cfg, 1700000000, 4321);
  testcheck::check(p.front() == '{' && p.back() == '}', "page line is one balanced object");
  testcheck::check(p.find("\"t\":\"page\"") != std::string::npos, "page line is tagged");
  for (const char* k : {"ts", "ms", "cfg", "bk", "fmt", "sp", "pg", "w", "c", "ln"}) {
    testcheck::check(hasKey(p, k), std::string("page line carries ") + k);
  }
  // Sixteen hex digits, zero padded: the report rehashes book PATHS to match
  // them, so a truncated or variable-width key would fail to join.
  testcheck::check(p.find("\"bk\":\"0123456789abcdef\"") != std::string::npos, "the book key is 16 zero-padded hex digits");
  // A page line stays small; the whole retention argument rests on it.
  testcheck::check(p.size() < 200, "a page line is under 200 bytes");

  const std::string e = readinglog::eventLine("sleep", "deep", 1700000000, 4321);
  testcheck::check(e.find("\"t\":\"evt\"") != std::string::npos, "event line is tagged");
  testcheck::check(e.find("\"k\":\"sleep\"") != std::string::npos, "the event kind is recorded");
  testcheck::check(e.find("\"why\":\"deep\"") != std::string::npos, "the event reason is recorded");
  testcheck::check(hasKey(e, "v"), "the event line carries the schema version");
  testcheck::check(readinglog::eventLine("boot", nullptr, 0, 0).find("\"why\":\"\"") != std::string::npos,
        "a null reason writes an empty string, not a crash");
}

// Negative unix seconds are absurd but a phone's clock can be anything before
// it first syncs; the line must still parse rather than emitting garbage.
void testHostileValues() {
  ReadingPageSample s = baseSample();
  s.fontFamily = "Bad\"Name\\Here";
  s.format = nullptr;
  s.ligaturesOff = nullptr;
  const readinglog::HostSnapshot h = baseHost();
  const std::string p = readinglog::pageLine(s, 1, -5, 0);
  testcheck::check(p.find("\"ts\":-5") != std::string::npos, "a pre-epoch clock is written as a negative number");
  testcheck::check(p.find("\"fmt\":\"\"") != std::string::npos, "a null format is an empty string");
  const std::string c = readinglog::configLine(s, h, 1, 0, 0);
  testcheck::check(c.find("\"fam\":\"Bad\\\"Name\\\\Here\"") != std::string::npos,
        "a hostile family name is escaped inside the cfg line");
  testcheck::check(c.front() == '{' && c.back() == '}', "and the record is still balanced");
}

// --- 4. retention is a bound ----------------------------------------------

void testRotation() {
  testcheck::check(!readinglog::shouldRotate(0, 200), "an empty file does not rotate");
  testcheck::check(!readinglog::shouldRotate(readinglog::kRotateBytes - 200, 200),
        "a write that exactly fills the generation does not rotate");
  testcheck::check(readinglog::shouldRotate(readinglog::kRotateBytes - 199, 200),
        "a write that would cross the ceiling rotates FIRST, so the bound is real");
  testcheck::check(readinglog::shouldRotate(readinglog::kRotateBytes, 1), "a full file rotates");
  // stat() failed. Rotating on ignorance would discard a generation for a
  // transient error; the safe answer is to try the append.
  testcheck::check(!readinglog::shouldRotate(-1, 200), "an unreadable size does not trigger a rotation");
  testcheck::check(readinglog::kRotateBytes * readinglog::kGenerations <= 64L * 1024 * 1024,
        "the ledger's whole footprint stays under 64 MiB");
}

// --- the sink, end to end -------------------------------------------------

std::string scratchPath() {
  const char* tmp = std::getenv("TMPDIR");
  std::string dir = tmp && tmp[0] ? tmp : "/tmp";
  if (dir.back() == '/') dir.pop_back();
  return dir + "/crosspoint_reading_log_test/reading.jsonl";
}

void removeAll(const std::string& base) {
  ::remove(base.c_str());
  for (int i = 1; i < readinglog::kGenerations + 2; i++) {
    char b[512];
    std::snprintf(b, sizeof b, "%s.%d", base.c_str(), i);
    ::remove(b);
  }
}

std::vector<std::string> readLines(const std::string& path) {
  std::vector<std::string> out;
  std::ifstream in(path);
  std::string line;
  while (std::getline(in, line)) out.push_back(line);
  return out;
}

void testAppendAndRotate() {
  const std::string path = scratchPath();
  removeAll(path);
  ::setenv("CROSSPOINT_SIM_READING_LOG", path.c_str(), 1);
  testcheck::check(readinglog::logPath() == path, "the env var wins over the platform default");

  readinglog::append("{\"t\":\"evt\"}");
  readinglog::append("{\"t\":\"page\"}");
  const std::vector<std::string> lines = readLines(path);
  testcheck::check(lines.size() == 2, "two appends make two lines");
  testcheck::check(lines[0] == "{\"t\":\"evt\"}", "the first line is intact");
  testcheck::check(lines[1] == "{\"t\":\"page\"}", "and appends do not overwrite");

  // Rotation is a RENAME, not a truncate: the older generation must still hold
  // the earlier lines afterwards. That is the whole reason a ledger rotates.
  {
    std::ofstream pad(path, std::ios::app);
    pad << std::string(readinglog::kRotateBytes, 'x') << '\n';
  }
  readinglog::append("{\"t\":\"after\"}");
  const std::vector<std::string> now = readLines(path);
  testcheck::check(now.size() == 1 && now[0] == "{\"t\":\"after\"}", "the live generation restarts with the new line");
  const std::vector<std::string> prev = readLines(path + ".1");
  testcheck::check(prev.size() == 3 && prev[0] == "{\"t\":\"evt\"}",
        "and generation .1 still holds every line the ledger had before");

  removeAll(path);
  ::unsetenv("CROSSPOINT_SIM_READING_LOG");
}

// WHAT IT COSTS. Not an assertion about a wall-clock budget -- a shared CI box
// will not honour one -- but a printed number beside the 30-130 ms a page turn
// already costs, so the claim in the header is a measurement rather than a
// hope. The bound is deliberately generous: it fails only if a rewrite makes
// the append hundreds of times more expensive.
void testAppendCost() {
  const std::string path = scratchPath();
  removeAll(path);
  ::setenv("CROSSPOINT_SIM_READING_LOG", path.c_str(), 1);
  const ReadingPageSample s = baseSample();
  const readinglog::HostSnapshot h = baseHost();
  const uint32_t cfg = readinglog::configId(s, h);
  const int n = 500;
  const auto t0 = std::chrono::steady_clock::now();
  for (int i = 0; i < n; i++) readinglog::append(readinglog::pageLine(s, cfg, 1700000000 + i, i));
  const auto t1 = std::chrono::steady_clock::now();
  const double usPerLine =
      std::chrono::duration_cast<std::chrono::microseconds>(t1 - t0).count() / static_cast<double>(n);
  std::printf("  [cost] one page line, built + appended: %.1f us\n", usPerLine);
  testcheck::check(usPerLine < 5000.0, "an appended line costs well under a millisecond of a 30-130 ms page turn");
  removeAll(path);
  ::unsetenv("CROSSPOINT_SIM_READING_LOG");
}

// --- the mirrored POD -----------------------------------------------------

std::string slurp(const std::string& path) {
  std::ifstream in(path, std::ios::binary);
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

// The firmware's copy of ReadingPageSample, read as text. The two cannot share
// a header -- the firmware is not linked against this repo on device -- so a
// divergence in FIELD ORDER or TYPE would compile cleanly on both sides and
// mean the reader filled a different struct from the one the sink reads.
void testFirmwareStructMirror(const char* firmwarePath) {
  const std::string src = slurp(firmwarePath);
  if (src.empty()) {
    std::printf("NOT CHECKED: firmware HalGPIO.h not at %s -- pass its path as argv[1]\n", firmwarePath);
    return;
  }
  const size_t at = src.find("struct ReadingPageSample {");
  testcheck::check(at != std::string::npos, "the firmware still declares ReadingPageSample");
  if (at == std::string::npos) return;
  const size_t end = src.find("};", at);
  testcheck::check(end != std::string::npos, "the firmware's ReadingPageSample is terminated");
  if (end == std::string::npos) return;
  // Both early returns are load-bearing rather than defensive tidiness: without
  // them a firmware checkout that has the file but not the declaration -- a
  // sibling agent mid-stash, a branch predating the channel -- aborts on
  // substr(npos) and the whole suite reports a crash where it should report one
  // failed check. That happened once, on 2026-08-25.
  const std::string body = src.substr(at, end - at);

  // Field-by-field, in order, with types. Anything the firmware renames,
  // reorders or retypes fails here.
  const char* expect[] = {"uint64_t bookKey",
                          "int32_t spineIndex",
                          "int32_t pageInSpine",
                          "const char* format",
                          "uint32_t words",
                          "uint32_t chars",
                          "uint32_t lines",
                          "const char* fontFamily",
                          "uint8_t fontPointSize",
                          "uint8_t fontSizeSlot",
                          "uint8_t lineSpacing",
                          "uint8_t lineGridEnabled",
                          "uint8_t justifyThresholdChars",
                          "uint8_t ligaturesEnabled",
                          "const char* ligaturesOff",
                          "uint8_t lineBreakMode",
                          "uint8_t screenMargin"};
  size_t cursor = 0;
  for (const char* field : expect) {
    const size_t f = body.find(field, cursor);
    testcheck::check(f != std::string::npos, std::string("firmware ReadingPageSample still has, in order: ") + field);
    cursor = f;
  }
  testcheck::check(src.find("void publishReadingPage(const ReadingPageSample& /*sample*/) {}") != std::string::npos,
        "the firmware's half is still an inline no-op -- it must cost nothing on device");
  testcheck::check(src.find("CROSSPOINT_READING_PAGE_SAMPLE") != std::string::npos,
        "the shared guard macro is still there, so a TU seeing both headers does not redefine the POD");
}

}  // namespace

int main(int argc, char** argv) {
  testConfigIdSweepsEveryRenderingField();
  testConfigIdIgnoresWhatIsNotAConfiguration();
  testConfigIdStringBoundaries();
  testNeedsConfigLine();
  testEscaping();
  testLineShapes();
  testHostileValues();
  testRotation();
  testAppendAndRotate();
  testAppendCost();
  testFirmwareStructMirror(argc > 1 ? argv[1] : "../crosspoint-reader/lib/hal/HalGPIO.h");
  if (testcheck::g_failures) {
    std::printf("%d FAILURES\n", testcheck::g_failures);
    return 1;
  }
  std::printf("reading_log_test: all checks passed\n");
  return 0;
}
