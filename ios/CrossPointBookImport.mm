// CrossPointBookImport.mm -- copy a book handed to the app from OUTSIDE its
// own card into <card>/books/, so the firmware's library sees it.
//
// The delivery mechanism is SDL3's own: the UIKit app delegate forwards
// application:openURL: (Files "Copy to CrossPoint X3", the share sheet,
// "Open in..." from Mail/Safari) as an SDL_EVENT_DROP_FILE
// (build-simsdk/_deps/sdl3-src/src/video/uikit/SDL_uikitappdelegate.m:677 and
// :665, scene path :422; cold-launch URLs are replayed by processLaunchURLs
// after SDL main starts). We observe it with SDL_AddEventWatch -- HalGPIO owns
// the event pump for the whole simulator, watchers see events as they are
// queued without consuming them (same pattern as the shim's finger watch).
// The watch is registered from a static constructor, which is safe and
// survives SDL_Init: SDL_InitEventWatchList only creates the lock and never
// clears the list (sdl3-src/src/events/SDL_eventwatch.c:26).
//
// Import rules (owner ask 2026-08-21, "copy over any book that is opened
// outside of app's own ios local folder"):
//   * copy, never move, never auto-open;
//   * only extensions the firmware actually reads as books -- .epub, .xtc,
//     .xtch, .txt, .md (firmware FsHelpers.cpp:166-183, NextBookFinder.cpp:15
//     -- .bmp is a viewer, not a book, and is deliberately excluded);
//   * a same-name same-size file in books/ means "already imported": skip;
//   * a same-name different-size file gets " 2" (then " 3"...) before the
//     extension rather than being overwritten;
//   * a file that arrived in Documents/Inbox (the "Copy to" path) is app-owned
//     temp: the original is deleted after a successful import;
//   * every action logs with an "[import]" prefix -- the log IS the interface
//     for headless verification.
//
// CROSSPOINT_SIM_IMPORT_FILE=<path> is the QA hook: processed once shortly
// after launch through the exact same import function the drop event calls,
// because nothing outside the process can synthesize an SDL drop event.

#include <SDL3/SDL.h>

#import <Foundation/Foundation.h>

#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <dirent.h>

#include <cctype>
#include <cstdlib>
#include <cstring>
#include <string>

#include "SimulatorOverlay.h"

// Ask the firmware to RE-RENDER the current activity, so an open library
// screen repaints with the new book. C++ linkage, NOT extern "C" -- it is
// defined that way in the firmware's src/SimulatorRenderRequest.cpp, and a
// wrong linkage here fails at link time.
void crosspointRequestRender();

namespace {

// The card root: CrossPointFsPrep roots HalStorage at the app's Documents
// directory and publishes it as CROSSPOINT_SIM_SD (overwrite=0, so a QA
// harness's own root stays authoritative). Fall back to $HOME/Documents,
// which is the same place on iOS.
std::string cardRoot() {
  const char *sd = std::getenv("CROSSPOINT_SIM_SD");
  if (sd && *sd) {
    return std::string(sd);
  }
  const char *home = std::getenv("HOME");
  if (home && *home) {
    return std::string(home) + "/Documents";
  }
  return {};
}

bool hasSuffixCaseInsensitive(const std::string &name, const char *ext) {
  const size_t extLen = std::strlen(ext);
  if (name.size() < extLen) {
    return false;
  }
  const size_t off = name.size() - extLen;
  for (size_t i = 0; i < extLen; ++i) {
    if (std::tolower(static_cast<unsigned char>(name[off + i])) !=
        std::tolower(static_cast<unsigned char>(ext[i]))) {
      return false;
    }
  }
  return true;
}

// The firmware's book formats: FsHelpers::hasEpubExtension / hasXtcExtension /
// hasTxtExtension / hasMarkdownExtension, matched case-insensitively exactly
// as FsHelpers::checkFileExtension does.
bool isBookFile(const std::string &name) {
  static const char *kBookExts[] = {".epub", ".xtc", ".xtch", ".txt", ".md"};
  for (const char *ext : kBookExts) {
    if (hasSuffixCaseInsensitive(name, ext)) {
      return true;
    }
  }
  return false;
}

bool fileSize(const std::string &path, off_t *outSize) {
  struct stat st{};
  if (::stat(path.c_str(), &st) != 0 || !S_ISREG(st.st_mode)) {
    return false;
  }
  *outSize = st.st_size;
  return true;
}

bool copyFileContents(const std::string &src, const std::string &dst) {
  const int in = ::open(src.c_str(), O_RDONLY);
  if (in < 0) {
    return false;
  }
  const int out = ::open(dst.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
  if (out < 0) {
    ::close(in);
    return false;
  }
  bool ok = true;
  char buffer[64 * 1024];
  for (;;) {
    const ssize_t got = ::read(in, buffer, sizeof(buffer));
    if (got == 0) {
      break;
    }
    if (got < 0) {
      ok = false;
      break;
    }
    ssize_t written = 0;
    while (written < got) {
      const ssize_t put = ::write(out, buffer + written, got - written);
      if (put < 0) {
        ok = false;
        break;
      }
      written += put;
    }
    if (!ok) {
      break;
    }
  }
  ::close(in);
  if (::close(out) != 0) {
    ok = false;
  }
  if (!ok) {
    ::unlink(dst.c_str()); // never leave a truncated book on the card
  }
  return ok;
}

// "name 2.epub" -- the collision suffix goes before the extension.
std::string withCollisionSuffix(const std::string &base, int n) {
  const size_t dot = base.find_last_of('.');
  const std::string stem = dot == std::string::npos ? base : base.substr(0, dot);
  const std::string ext = dot == std::string::npos ? "" : base.substr(dot);
  return stem + " " + std::to_string(n) + ext;
}

// True when `path` sits inside directory `dir` (string-prefix; both are
// absolute paths from the same sandbox, no symlink games expected).
bool isUnderDirectory(const std::string &path, const std::string &dir) {
  return !dir.empty() && path.size() > dir.size() + 1 &&
         path.compare(0, dir.size(), dir) == 0 && path[dir.size()] == '/';
}

// The one entry point; the drop event, the Inbox sweep and the env hook all
// come through here.
void importBookFile(const char *sourcePath) {
  if (!sourcePath || sourcePath[0] != '/') {
    // SDL forwards non-file URLs as their absoluteString; we only import files.
    SDL_Log("[import] ignoring non-file URL: %s", sourcePath ? sourcePath : "(null)");
    return;
  }
  const std::string src(sourcePath);
  const size_t slash = src.find_last_of('/');
  const std::string base = slash == std::string::npos ? src : src.substr(slash + 1);

  if (!isBookFile(base)) {
    SDL_Log("[import] ignoring %s: not a book format the firmware reads "
            "(.epub/.xtc/.xtch/.txt/.md)", src.c_str());
    return;
  }

  const std::string root = cardRoot();
  if (root.empty()) {
    SDL_Log("[import] no card root resolvable; cannot import %s", src.c_str());
    return;
  }
  const std::string booksDir = root + "/books";
  const std::string inboxDir = root + "/Inbox";

  if (isUnderDirectory(src, booksDir)) {
    SDL_Log("[import] %s is already on the card's books folder; nothing to do",
            src.c_str());
    return;
  }

  // Files handed over from another provider arrive security-scoped. SDL's
  // delegate drops the NSURL, so re-wrap the path and take the scope
  // best-effort; startAccessingSecurityScopedResource returning NO just means
  // the file was reachable without one (our own Inbox, shared /tmp in QA).
  NSURL *scopedURL = [NSURL fileURLWithPath:[NSString stringWithUTF8String:src.c_str()]];
  const BOOL scoped = [scopedURL startAccessingSecurityScopedResource];

  off_t srcSize = 0;
  if (!fileSize(src, &srcSize)) {
    SDL_Log("[import] cannot stat %s; not imported", src.c_str());
    if (scoped) [scopedURL stopAccessingSecurityScopedResource];
    return;
  }

  ::mkdir(booksDir.c_str(), 0777); // exists already on any booted card

  bool handled = false;
  for (int attempt = 1; attempt <= 99 && !handled; ++attempt) {
    const std::string name = attempt == 1 ? base : withCollisionSuffix(base, attempt);
    const std::string dst = booksDir + "/" + name;
    off_t dstSize = 0;
    if (fileSize(dst, &dstSize)) {
      if (dstSize == srcSize) {
        SDL_Log("[import] %s already imported as %s (same size %lld); skipping copy",
                src.c_str(), dst.c_str(), static_cast<long long>(dstSize));
        handled = true;
      } else {
        SDL_Log("[import] %s exists with different size (%lld vs %lld); trying \"%s\"",
                dst.c_str(), static_cast<long long>(dstSize),
                static_cast<long long>(srcSize),
                withCollisionSuffix(base, attempt + 1).c_str());
      }
      continue;
    }
    if (copyFileContents(src, dst)) {
      SDL_Log("[import] copied %s -> %s (%lld bytes)", src.c_str(), dst.c_str(),
              static_cast<long long>(srcSize));
      handled = true;
    } else {
      SDL_Log("[import] copy %s -> %s FAILED: %s", src.c_str(), dst.c_str(),
              std::strerror(errno));
      break;
    }
  }

  if (scoped) {
    [scopedURL stopAccessingSecurityScopedResource];
  }
  if (!handled) {
    return;
  }

  // The "Copy to" path lands files in Documents/Inbox, which is app-owned
  // temp; the imported copy is now the real one, so the original goes.
  if (isUnderDirectory(src, inboxDir)) {
    if (::unlink(src.c_str()) == 0) {
      SDL_Log("[import] deleted Inbox original %s", src.c_str());
    } else {
      SDL_Log("[import] could not delete Inbox original %s: %s", src.c_str(),
              std::strerror(errno));
    }
  }

  // Re-push the frame AND re-render the activity: requestPresent() only
  // re-presents the framebuffer that already exists, so an open library
  // screen needs the firmware to paint again (same pairing as the shim's
  // applyTheme()).
  SimulatorOverlay::requestPresent();
  crosspointRequestRender();
}

// Cold-launch "Copy to" files can already be sitting in Documents/Inbox when
// the process starts; sweep them through the same import.
void sweepInbox() {
  const std::string root = cardRoot();
  if (root.empty()) {
    return;
  }
  const std::string inboxDir = root + "/Inbox";
  DIR *dir = ::opendir(inboxDir.c_str());
  if (!dir) {
    return;
  }
  struct dirent *entry;
  while ((entry = ::readdir(dir)) != nullptr) {
    if (entry->d_name[0] == '.') {
      continue;
    }
    importBookFile((inboxDir + "/" + entry->d_name).c_str());
  }
  ::closedir(dir);
}

bool SDLCALL bookImportWatch(void *, SDL_Event *event) {
  if (event->type == SDL_EVENT_DROP_FILE && event->drop.data) {
    importBookFile(event->drop.data);
  }
  return true; // watchers observe; the return value does not consume
}

__attribute__((constructor)) void registerBookImport() {
  SDL_AddEventWatch(bookImportWatch, nullptr);
  // Deferred once-per-process pass: by then CrossPointFsPrep has rooted the
  // card and exported CROSSPOINT_SIM_SD. Covers the Inbox sweep and the QA
  // env hook; the drop-event path needs no delay.
  dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(2 * NSEC_PER_SEC)),
                 dispatch_get_main_queue(), ^{
    sweepInbox();
    const char *hook = std::getenv("CROSSPOINT_SIM_IMPORT_FILE");
    if (hook && *hook) {
      SDL_Log("[import] env hook CROSSPOINT_SIM_IMPORT_FILE=%s", hook);
      importBookFile(hook);
    }
  });
}

} // namespace
