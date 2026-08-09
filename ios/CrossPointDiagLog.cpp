#include "CrossPointDiagLog.h"

#include "CrossPointPrefs.h"

#include <SDL3/SDL.h>
#include <sys/stat.h>

#include <cstdio>
#include <cstring>
#include <mutex>

namespace {

// Rotate rather than truncate: the question is usually about a launch that
// already ended. One generation back is enough -- two files, ~256 KB ceiling,
// on a card measured in gigabytes.
constexpr long kRotateBytes = 128 * 1024;

std::mutex g_mutex;

// Relative paths, resolved against the cwd the harness set (the card root).
// If the cwd is somewhere unexpected the fopen simply fails and the mirror to
// SDL_Log still happens, so diagnostics degrade to what they were before this
// file existed rather than taking the app down.
void rotateIfNeeded() {
  struct stat st{};
  if (::stat(kCrossPointDiagPath, &st) != 0) return;
  if (st.st_size < kRotateBytes) return;
  char prev[128];
  snprintf(prev, sizeof(prev), "%s.1", kCrossPointDiagPath);
  ::remove(prev);
  ::rename(kCrossPointDiagPath, prev);
}

}  // namespace

void CrossPointDiag_log(const char *fmt, ...) {
  // Owner ruling 2026-08-09: diagnostics OFF by default now that Speak Screen
  // works. One gate here silences the file, the SDL_Log mirror, the tree
  // dumps and every probe that routes through them; the Settings.app toggle
  // brings the whole instrument back for a future investigation.
  if (!CrossPointPrefs_diagnosticsEnabled()) return;
  char line[512];
  va_list args;
  va_start(args, fmt);
  vsnprintf(line, sizeof(line), fmt, args);
  va_end(args);

  // Mirror first: the file write can fail, the mirror cannot.
  SDL_Log("[A11Y-FILE] %s", line);

  std::lock_guard<std::mutex> lock(g_mutex);
  ::mkdir("diagnostics", 0755);  // idempotent; EEXIST is the normal case
  rotateIfNeeded();
  FILE *f = ::fopen(kCrossPointDiagPath, "a");
  if (!f) return;
  // Seconds since launch, one decimal: enough to order events and correlate
  // with "I pressed it about a minute in", which is the precision reports
  // actually arrive at.
  fprintf(f, "[%8.1f] %s\n", (double)SDL_GetTicks() / 1000.0, line);
  ::fclose(f);
}
