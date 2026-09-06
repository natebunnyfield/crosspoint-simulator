// The phone-readable firmware log (src/FirmwareLogFile.h).
//
// Every assertion here is about a property a person on a phone depends on and
// cannot check for themselves: that the file does not exist until they ask for
// it, that what lands in it is byte-for-byte what the firmware wrote (a log
// that paraphrases is not evidence), that turning the switch back off actually
// stops it, and that a long sitting rotates instead of growing without bound
// on a device whose storage is the same storage the books live on.
//
// Runs in a scratch directory, because the paths are relative to the card root
// exactly as they are on the phone.

#include "FirmwareLogFile.h"
#include "HardwareSerial.h"
#include "TestCheck.h"

#include <string>
#include <unistd.h>

using testcheck::check;
using testcheck::checkEq;

namespace {

int g_answer = 0;
int provider() { return g_answer; }

// Re-installing forces an immediate re-poll, so a test can flip the switch
// without waiting out kProviderPollSeconds. This is the same call the harness
// makes at launch, not a test-only back door.
void setSwitch(int on) {
  g_answer = on;
  firmwarelog::setEnabledProvider(&provider);
}

bool exists(const char *path) { return ::access(path, F_OK) == 0; }

std::string slurp(const char *path) {
  FILE *f = ::fopen(path, "rb");
  if (!f) return {};
  std::string out;
  char buf[4096];
  size_t n;
  while ((n = ::fread(buf, 1, sizeof(buf), f)) > 0) out.append(buf, n);
  ::fclose(f);
  return out;
}

long sizeOf(const char *path) {
  FILE *f = ::fopen(path, "rb");
  if (!f) return -1;
  ::fseek(f, 0, SEEK_END);
  const long n = ::ftell(f);
  ::fclose(f);
  return n;
}

}  // namespace

int main() {
  char tmpl[] = "/tmp/fwlogXXXXXX";
  const char *dir = ::mkdtemp(tmpl);
  testcheck::expect(dir != nullptr, "could not make a scratch card root");
  testcheck::expect(::chdir(dir) == 0, "could not enter the scratch card root");

  const char *path = firmwarelog::kFirmwareLogPath;
  const std::string rotated = std::string(path) + ".1";

  // OFF is the shipped state, and off means no file at all -- not an empty one.
  // Someone who never asked for diagnostics should not find a diagnostics
  // folder sitting in their Files app next to their books.
  firmwarelog::write("nobody asked for this\n", 22);
  firmwarelog::hostLine("nor this");
  check(!exists(path), "a log file must not exist while the switch is off");
  check(!exists("diagnostics"), "the diagnostics folder must not be created while the switch is off");

  // ON: byte-for-byte, because the firmware's own line already carries its
  // "[millis] [LVL] [ORIGIN] " prefix and anything added here would corrupt a
  // grep the owner is asked to run.
  setSwitch(1);
  const char *line = "[1234] [DBG] [ERS] Resolved anchor 'ch4' to page 7\n";
  firmwarelog::write(line, ::strlen(line));
  firmwarelog::flush();
  checkEq(slurp(path), std::string(line), "the firmware's bytes must land verbatim");

  // Host lines are tagged, so a reader of the file can tell the device's own
  // log apart from the harness reporting on it.
  firmwarelog::hostLine("[power] foreground return counts as activity");
  firmwarelog::flush();
  checkEq(slurp(path),
          std::string(line) + "[host] [power] foreground return counts as activity\n",
          "a host line must be tagged and newline-terminated");

  // OFF again stops it. A switch that only ever added output would be a switch
  // nobody could trust to be off.
  setSwitch(0);
  firmwarelog::write("after the switch\n", 17);
  firmwarelog::flush();
  check(slurp(path).find("after the switch") == std::string::npos,
        "turning the switch off must stop the writing");

  // A long sitting rotates rather than growing forever. One generation back:
  // the older half survives as .1, and the live file starts over.
  setSwitch(1);
  std::string chunk(1024, 'x');
  chunk.back() = '\n';
  for (int i = 0; i < 300; i++) firmwarelog::write(chunk.data(), chunk.size());
  firmwarelog::flush();
  check(exists(rotated.c_str()), "crossing the cap must leave one rotated generation");
  check(sizeOf(rotated.c_str()) >= firmwarelog::detail::kRotateBytes,
        "the rotated generation is the one that reached the cap");
  check(sizeOf(path) < firmwarelog::detail::kRotateBytes,
        "the live file starts over after a rotation");

  // And the rotation is a rename, not a truncation: what was written before it
  // is still readable, which is the whole point of rotating.
  check(slurp(rotated.c_str()).rfind(line, 0) == 0,
        "the first line ever written must survive in the rotated generation");

  // Deleting the log from the Files app mid-session is the obvious thing to do
  // before reproducing a bug, and an app holding the old handle would go on
  // appending into the deleted inode -- silently, forever. The next line must
  // bring the file back.
  ::remove(path);
  firmwarelog::write("after the owner cleared it\n", 26);
  firmwarelog::flush();
  check(slurp(path).find("after the owner cleared it") != std::string::npos,
        "a log deleted from under the app must come back on the next line");

  // THE WIRING. Everything above proves the sink; this proves the firmware is
  // actually plugged into it. logPrintf() builds a whole line and hands it to
  // logSerial.print(), which is Print::print -> HWCDC::write(buffer, size), so
  // that overload is the one every LOG_DBG in the reader travels through. A
  // local instance, not the Serial global, so the test needs no ESP.cpp.
  {
    ::remove(path);
    ::remove(rotated.c_str());
    setSwitch(1);
    HWCDC serial;
    serial.print("[5678] [DBG] [ERS] Rendered spine 3 page 6/40 in 120ms\n");
    firmwarelog::flush();
    check(slurp(path).find("Rendered spine 3 page 6/40") != std::string::npos,
          "a line written through Serial must reach the file");
  }

  if (testcheck::g_failures > 0) {
    std::printf("firmware_log_file: %d FAILED\n", testcheck::g_failures);
    return 1;
  }
  std::puts("firmware_log_file: PASS");
  return 0;
}
