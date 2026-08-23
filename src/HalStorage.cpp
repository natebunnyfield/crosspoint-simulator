#include "HalStorage.h"

#include "SimCompressedFile.h"

#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cerrno>
#include <cstdio>
#include <ctime>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <sstream>
#include <vector>

#ifdef __APPLE__
#include <mach-o/dyld.h>
#endif

HalStorage HalStorage::instance;
HalStorage::HalStorage() {}

namespace {
#ifdef __APPLE__
// A .app launched from Finder (or from TestFlight) starts with its working
// directory at "/", so the default relative "./fs_" root would resolve to an
// unwritable "/fs_" and the library would come up empty. Detect the bundle and
// move the simulated SD card into Application Support instead. Under the App
// Sandbox that Mac App Store builds require, HOME already points at the app's
// container, so the same path stays inside the sandbox.
//
// Command-line dev builds are not inside a bundle and keep using "./fs_".
std::string bundleStorageRoot() {
  uint32_t size = 0;
  _NSGetExecutablePath(nullptr, &size);
  if (size == 0) {
    return {};
  }
  std::vector<char> buffer(size);
  if (_NSGetExecutablePath(buffer.data(), &size) != 0) {
    return {};
  }

  const std::string executable(buffer.data());
  const std::string marker = ".app/Contents/MacOS/";
  const size_t at = executable.rfind(marker);
  if (at == std::string::npos) {
    return {};
  }

  const std::string bundle = executable.substr(0, at); // ".../CrossPointX3"
  const size_t slash = bundle.find_last_of('/');
  const std::string name =
      slash == std::string::npos ? bundle : bundle.substr(slash + 1);
  if (name.empty()) {
    return {};
  }

  const char *home = std::getenv("HOME");
  if (!home || !*home) {
    return {};
  }
  return std::string(home) + "/Library/Application Support/" + name + "/fs_";
}
#endif

std::string configuredStorageRoot() {
  const char *root = std::getenv("CROSSPOINT_SIM_SD");
  if (!root || !*root) {
    root = std::getenv("CROSSPOINT_EMU_SD");
  }
  if (root && *root) {
    return std::string(root);
  }
#ifdef __APPLE__
  const std::string bundled = bundleStorageRoot();
  if (!bundled.empty()) {
    return bundled;
  }
#endif
  return std::string("./fs_");
}

bool containsUnsafeSegment(const std::string &path) {
  std::stringstream stream(path);
  std::string segment;
  while (std::getline(stream, segment, '/')) {
    if (segment == "..") {
      return true;
    }
  }
  return false;
}

std::string resolveStoragePath(const char *path) {
  std::string logical = path ? std::string(path) : std::string("/");
  if (logical.empty()) {
    logical = "/";
  }
  if (containsUnsafeSegment(logical)) {
    fprintf(stderr, "[SIM] rejected unsafe storage path: %s\n",
            logical.c_str());
    return {};
  }
  while (!logical.empty() && logical.front() == '/') {
    logical.erase(logical.begin());
  }

  std::string root = configuredStorageRoot();
  while (root.size() > 1 && root.back() == '/') {
    root.pop_back();
  }
  if (logical.empty()) {
    return root;
  }
  return root + "/" + logical;
}

bool ensureParentDirectories(const std::string &full) {
  const size_t slash = full.find_last_of('/');
  if (slash == std::string::npos) {
    return true;
  }
  const std::string parent = full.substr(0, slash);
  if (parent.empty()) {
    return true;
  }
  for (size_t i = 1; i < parent.size(); ++i) {
    if (parent[i] == '/') {
      ::mkdir(parent.substr(0, i).c_str(), 0777);
    }
  }
  return ::mkdir(parent.c_str(), 0777) == 0 || errno == EEXIST;
}
} // namespace

// The host-settings file sits BESIDE the simulated card, and only this file
// knows where that card is -- a Finder-launched .app puts it under Application
// Support while a command-line build uses ./fs_. Exposed rather than
// duplicated, because a second copy of that rule would drift.
std::string simulatorStorageRootForHost() { return configuredStorageRoot(); }

bool HalStorage::begin() {
  const std::string root = configuredStorageRoot();
  static bool loggedRoot = false;
  if (!loggedRoot) {
    loggedRoot = true;
    // A bundled app logs to Console.app; this is the only way a tester can
    // find where to put books.
    fprintf(stderr, "[SIM] storage root: %s\n", root.c_str());
  }
  for (size_t i = 1; i < root.size(); ++i) {
    if (root[i] == '/') {
      ::mkdir(root.substr(0, i).c_str(), 0777);
    }
  }
  return ::mkdir(root.c_str(), 0777) == 0 || errno == EEXIST;
}
bool HalStorage::ready() const { return true; }

class HalFile::Impl {
public:
  int fd = -1;
  std::string path;
  DIR *dir = nullptr;
  // Set only when the bytes on disk are a CPZ1 container (SimCompressedFile.h).
  // Everything below then works in the container's LOGICAL space -- the size,
  // the position, the seeks and the reads are all about the payload, and the
  // firmware above cannot tell the difference. `pos` exists because the fd's
  // own offset stops being the answer once reads are served from an inflated
  // block instead of from the fd.
  std::unique_ptr<SimCpzFile> cpz;
  uint64_t pos = 0;

  bool open(const char *p, int flags) {
    path = p;
    // The simulator's FsApiConstants.h just includes <fcntl.h> and typedef int
    // oflag_t, so all O_* constants are already native POSIX values — pass them
    // straight through.
    fd = ::open(path.c_str(), flags, 0666);
    if (fd < 0) {
      fprintf(stderr, "[SIM] open failed: %s (flags=0x%x errno=%d %s)\n",
              path.c_str(), flags, errno, strerror(errno));
      return false;
    }
    pos = 0;
    // Sniff for the container, READ-ONLY opens only: a writer that found the
    // magic and then wrote through the decoder would corrupt the file, and
    // nothing in this simulator writes a .cpfont anyway.
    if ((flags & O_ACCMODE) == O_RDONLY) {
      unsigned char probe[sizeof(simcpz::kMagic)];
      if (::pread(fd, probe, sizeof(probe), 0) ==
              static_cast<ssize_t>(sizeof(probe)) &&
          std::memcmp(probe, simcpz::kMagic, sizeof(probe)) == 0) {
        std::unique_ptr<SimCpzFile> reader(new SimCpzFile());
        if (!reader->open(fd, path.c_str())) {
          // FAIL, do not fall back. Handing the caller the container's own
          // bytes as if they were the payload is the silent version of this
          // failure, and for a font it surfaces as a blank page with
          // successful renders in the log.
          ::close(fd);
          fd = -1;
          return false;
        }
        cpz = std::move(reader);
      }
    }
    return true;
  }

  bool openAsDir(const char *p) {
    path = p;
    dir = opendir(p);
    return dir != nullptr;
  }

  bool isDir() const { return dir != nullptr; }
  bool isOpen() const { return fd >= 0 || dir != nullptr; }
};

HalFile::HalFile() : impl(new Impl()) {}
HalFile::~HalFile() {
  // close() releases BOTH handles; this used to inline only the fd half, so a
  // HalFile holding a directory (openNextFile, and HalStorage::open on a dir)
  // leaked its DIR* and the fd under it. Walking the two font roots and
  // recursing Manage Files leaked one per directory until open() started
  // failing with EMFILE -- which surfaces as books that stop loading, naming an
  // innocent file in the log.
  if (impl)
    close();
}
HalFile::HalFile(HalFile &&other) : impl(std::move(other.impl)) {}
HalFile &HalFile::operator=(HalFile &&other) {
  if (this != &other) {
    if (impl)
      close();  // both handles -- see the note on ~HalFile
    impl = std::move(other.impl);
  }
  return *this;
}

void HalFile::flush() {
  if (impl && impl->fd >= 0)
    fsync(impl->fd);
}
bool HalFile::sync() {
  if (!impl || impl->fd < 0)
    return false;
  return fsync(impl->fd) == 0;
}
size_t HalFile::getName(char *name, size_t len) {
  if (!impl || impl->path.empty())
    return 0;
  size_t slash = impl->path.rfind('/');
  std::string fname =
      (slash == std::string::npos) ? impl->path : impl->path.substr(slash + 1);
  size_t n = std::min(fname.size(), len - 1);
  memcpy(name, fname.c_str(), n);
  name[n] = '\0';
  return n;
}
size_t HalFile::size() {
  if (!impl || impl->fd < 0)
    return 0;
  if (impl->cpz)
    return (size_t)impl->cpz->size();
  off_t cur = lseek(impl->fd, 0, SEEK_CUR);
  off_t end = lseek(impl->fd, 0, SEEK_END);
  lseek(impl->fd, cur, SEEK_SET);
  return end < 0 ? 0 : (size_t)end;
}
size_t HalFile::fileSize() { return size(); }
uint64_t HalFile::fileSize64() { return size(); }

static bool fatEncodeTime(time_t t, uint16_t *pdate, uint16_t *ptime) {
  struct tm tmv;
  if (!localtime_r(&t, &tmv))
    return false;
  int year = tmv.tm_year + 1900;
  if (year < 1980)
    year = 1980;
  if (pdate)
    *pdate = (uint16_t)(((year - 1980) << 9) | ((tmv.tm_mon + 1) << 5) |
                        tmv.tm_mday);
  if (ptime)
    *ptime = (uint16_t)((tmv.tm_hour << 11) | (tmv.tm_min << 5) |
                        (tmv.tm_sec / 2));
  return true;
}

bool HalFile::getCreateDateTime(uint16_t *pdate, uint16_t *ptime) {
  if (!impl || impl->path.empty())
    return false;
  struct stat st;
  if (::stat(impl->path.c_str(), &st) != 0)
    return false;
#ifdef __APPLE__
  return fatEncodeTime(st.st_birthtimespec.tv_sec, pdate, ptime);
#else
  return fatEncodeTime(st.st_ctime, pdate, ptime);
#endif
}

bool HalFile::getModifyDateTime(uint16_t *pdate, uint16_t *ptime) {
  if (!impl || impl->path.empty())
    return false;
  struct stat st;
  if (::stat(impl->path.c_str(), &st) != 0)
    return false;
  return fatEncodeTime(st.st_mtime, pdate, ptime);
}

bool HalFile::seek(size_t pos) {
  if (!impl || impl->fd < 0)
    return false;
  if (impl->cpz) {
    impl->pos = pos;
    return true;
  }
  return lseek(impl->fd, (off_t)pos, SEEK_SET) >= 0;
}
bool HalFile::seek64(uint64_t pos) {
  if (!impl || impl->fd < 0)
    return false;
  if (pos > static_cast<uint64_t>(std::numeric_limits<off_t>::max()))
    return false;
  if (impl->cpz) {
    impl->pos = pos;
    return true;
  }
  return lseek(impl->fd, static_cast<off_t>(pos), SEEK_SET) >= 0;
}
bool HalFile::seekCur(int64_t offset) {
  if (!impl || impl->fd < 0)
    return false;
  if (impl->cpz) {
    if (offset < 0 && static_cast<uint64_t>(-offset) > impl->pos)
      return false;
    impl->pos = (uint64_t)((int64_t)impl->pos + offset);
    return true;
  }
  return lseek(impl->fd, (off_t)offset, SEEK_CUR) >= 0;
}
bool HalFile::seekSet(size_t offset) {
  if (!impl || impl->fd < 0)
    return false;
  if (impl->cpz) {
    impl->pos = offset;
    return true;
  }
  return lseek(impl->fd, (off_t)offset, SEEK_SET) >= 0;
}
int HalFile::available() const {
  if (!impl || impl->fd < 0)
    return 0;
  if (impl->cpz) {
    const uint64_t total = impl->cpz->size();
    return impl->pos >= total ? 0 : (int)(total - impl->pos);
  }
  off_t cur = lseek(impl->fd, 0, SEEK_CUR);
  off_t end = lseek(impl->fd, 0, SEEK_END);
  lseek(impl->fd, cur, SEEK_SET);
  return (int)(end - cur);
}
size_t HalFile::position() const {
  if (!impl || impl->fd < 0)
    return 0;
  if (impl->cpz)
    return (size_t)impl->pos;
  off_t pos = lseek(impl->fd, 0, SEEK_CUR);
  return pos < 0 ? 0 : (size_t)pos;
}
int HalFile::read(void *buf, size_t count) {
  if (!impl || impl->fd < 0)
    return -1;
  if (impl->cpz) {
    const int n = impl->cpz->read(impl->pos, buf, count);
    if (n > 0)
      impl->pos += (uint64_t)n;
    return n;
  }
  ssize_t n = ::read(impl->fd, buf, count);
  return (int)n;
}
int HalFile::read() {
  if (!impl || impl->fd < 0)
    return -1;
  uint8_t c;
  if (impl->cpz)
    return read(&c, 1) == 1 ? c : -1;
  return (::read(impl->fd, &c, 1) == 1) ? c : -1;
}
size_t HalFile::write(const void *buf, size_t count) {
  if (!impl || impl->fd < 0)
    return 0;
  // Unreachable by construction -- the decoder is only attached to O_RDONLY
  // opens -- and refused rather than left to ::write's EBADF, because the
  // failure it would guard against is not a failed write but a SUCCESSFUL one:
  // raw bytes landing at the fd's offset inside a container.
  if (impl->cpz)
    return 0;
  ssize_t n = ::write(impl->fd, buf, count);
  return n < 0 ? 0 : (size_t)n;
}
size_t HalFile::write(const uint8_t *buf, size_t count) {
  return write(static_cast<const void *>(buf), count);
}
size_t HalFile::write(uint8_t b) {
  if (!impl || impl->fd < 0)
    return 0;
  return (::write(impl->fd, &b, 1) == 1) ? 1 : 0;
}
bool HalFile::rename(const char *newPath) {
  if (!impl || impl->path.empty()) {
    return false;
  }
  const std::string resolved = resolveStoragePath(newPath);
  if (resolved.empty()) {
    return false;
  }
  close();
  ensureParentDirectories(resolved);
  return ::rename(impl->path.c_str(), resolved.c_str()) == 0;
}
bool HalFile::isDirectory() const { return impl && impl->isDir(); }
void HalFile::rewindDirectory() {
  if (impl && impl->dir)
    rewinddir(impl->dir);
}
bool HalFile::close() {
  if (!impl)
    return true;
  if (impl->dir) {
    closedir(impl->dir);
    impl->dir = nullptr;
  }
  if (impl->fd >= 0) {
    // The decoder borrows the fd, so it goes first.
    impl->cpz.reset();
    impl->pos = 0;
    ::close(impl->fd);
    impl->fd = -1;
  }
  return true;
}
HalFile HalFile::openNextFile() {
  if (!impl || !impl->dir)
    return HalFile();
  while (true) {
    struct dirent *entry = readdir(impl->dir);
    if (!entry)
      return HalFile();
    const char *nm = entry->d_name;
    if (nm[0] == '.' && (nm[1] == '\0' || (nm[1] == '.' && nm[2] == '\0')))
      continue; // skip . and .. only — SdFat on device DOES return dotfiles
                // (.crosspoint, .fonts), and firmware filters them itself
                // (FileBrowserActivity, WebDAV PROPFIND)

    std::string childFsPath = impl->path;
    if (childFsPath.back() != '/')
      childFsPath += '/';
    childFsPath += entry->d_name;

    HalFile child;
    struct stat st;
    if (stat(childFsPath.c_str(), &st) != 0)
      continue;

    if (S_ISDIR(st.st_mode)) {
      child.impl->openAsDir(childFsPath.c_str());
    } else {
      child.impl->open(childFsPath.c_str(), O_RDONLY);
    }
    return child;
  }
}
bool HalFile::isOpen() const {
  if (!impl)
    return false;
  return impl->isOpen();
}
HalFile::operator bool() const { return isOpen(); }

HalFile HalStorage::open(const char *path, const oflag_t oflag) {
  std::string full = resolveStoragePath(path);
  HalFile f;
  if (full.empty()) {
    return f;
  }
  if ((oflag & O_CREAT) != 0) {
    ensureParentDirectories(full);
  }
  struct stat st;
  if (stat(full.c_str(), &st) == 0 && S_ISDIR(st.st_mode)) {
    f.impl->openAsDir(full.c_str());
  } else {
    f.impl->open(full.c_str(), oflag);
  }
  return f;
}
bool HalStorage::mkdir(const char *path, const bool /*pFlag*/) {
  std::string full = resolveStoragePath(path);
  if (full.empty()) {
    return false;
  }
  // Create all intermediate directories (mkdir -p semantics).
  for (size_t i = 1; i < full.size(); ++i) {
    if (full[i] == '/') {
      ::mkdir(full.substr(0, i).c_str(),
              0777); // ignore errors (may already exist)
    }
  }
  return ::mkdir(full.c_str(), 0777) == 0 || errno == EEXIST;
}
bool HalStorage::exists(const char *path) {
  std::string full = resolveStoragePath(path);
  if (full.empty()) {
    return false;
  }
  struct stat buffer;
  return (stat(full.c_str(), &buffer) == 0);
}
bool HalStorage::remove(const char *path) {
  std::string full = resolveStoragePath(path);
  if (full.empty()) {
    return false;
  }
  return ::remove(full.c_str()) == 0;
}
bool HalStorage::rename(const char *oldPath, const char *newPath) {
  std::string o = resolveStoragePath(oldPath);
  std::string n = resolveStoragePath(newPath);
  if (o.empty() || n.empty()) {
    return false;
  }
  ensureParentDirectories(n);
  return ::rename(o.c_str(), n.c_str()) == 0;
}
static bool removeDirRecursive(const std::string &full) {
  DIR *d = opendir(full.c_str());
  if (!d)
    return ::remove(full.c_str()) == 0; // might be a plain file
  struct dirent *entry;
  while ((entry = readdir(d)) != nullptr) {
    // Skip only "." and "..", NOT every dot-entry. Elsewhere in this file a
    // leading dot means "hidden, do not list"; here it meant "do not delete",
    // and the rmdir() below then failed with ENOTEMPTY on anything the host
    // had left behind. On iOS the card is the app's Documents folder,
    // browsable in Files and iCloud, so .DS_Store and ._* appear routinely --
    // a folder delete from the file browser, cache clear, font installer, web
    // server or WebDAV would just return false with nothing to show for it.
    const char *nm = entry->d_name;
    if (nm[0] == '.' && (nm[1] == '\0' || (nm[1] == '.' && nm[2] == '\0')))
      continue;
    std::string child = full + "/" + entry->d_name;
    struct stat st;
    if (stat(child.c_str(), &st) == 0 && S_ISDIR(st.st_mode)) {
      removeDirRecursive(child);
    } else {
      ::remove(child.c_str());
    }
  }
  closedir(d);
  return ::rmdir(full.c_str()) == 0;
}

bool HalStorage::rmdir(const char *path) {
  std::string full = resolveStoragePath(path);
  if (full.empty()) {
    return false;
  }
  return removeDirRecursive(full);
}
bool HalStorage::removeDir(const char *path) {
  std::string full = resolveStoragePath(path);
  if (full.empty()) {
    return false;
  }
  return removeDirRecursive(full);
}

String HalStorage::readFile(const char *path) {
  HalFile f = open(path, O_RDONLY);
  if (!f)
    return String("");
  size_t s = f.size();
  std::string content(s, '\0');
  f.read((void *)content.data(), s);
  return String(content);
}
bool HalStorage::readFileToStream(const char *path, Print &out,
                                  size_t chunkSize) {
  HalFile f = open(path, O_RDONLY);
  if (!f)
    return false;
  std::vector<char> buf(chunkSize);
  int n;
  while ((n = f.read(buf.data(), chunkSize)) > 0) {
    out.write(reinterpret_cast<const uint8_t *>(buf.data()), n);
  }
  return true;
}
size_t HalStorage::readFileToBuffer(const char *path, char *buffer,
                                    size_t bufferSize, size_t maxBytes) {
  HalFile f = open(path, O_RDONLY);
  if (!f)
    return 0;
  size_t toRead = bufferSize - 1;
  if (maxBytes > 0 && maxBytes < toRead)
    toRead = maxBytes;
  int n = f.read(buffer, toRead);
  if (n < 0)
    n = 0;
  buffer[n] = '\0';
  return n;
}
bool HalStorage::writeFile(const char *path, const String &content) {
  HalFile f = open(path, O_WRONLY | O_CREAT | O_TRUNC);
  if (!f)
    return false;
  f.write(content.c_str(), content.length());
  return true;
}
bool HalStorage::ensureDirectoryExists(const char *path) { return mkdir(path); }

bool HalStorage::openFileForRead(const char *moduleName, const char *path,
                                 HalFile &file) {
  file = open(path, O_RDONLY);
  return file.isOpen();
}
bool HalStorage::openFileForRead(const char *moduleName,
                                 const std::string &path, HalFile &file) {
  return openFileForRead(moduleName, path.c_str(), file);
}
bool HalStorage::openFileForRead(const char *moduleName, const String &path,
                                 HalFile &file) {
  return openFileForRead(moduleName, path.c_str(), file);
}
// O_RDWR, not O_WRONLY, and that is not a nicety: the firmware reads back
// through this handle. The SD card opens it read-write --
// freeink-sdk/libs/hardware/SDCardManager/src/SDCardManager.cpp:286
// `vol().open(path, O_RDWR | O_CREAT | O_TRUNC)` -- so a write handle on the
// device is also readable, and Section relies on exactly that:
// Section::loadPageDuringBuild() (lib/Epub/Epub/Section.cpp:691-697) serves the
// page being displayed by seeking BACK in the .bin the build is still writing
// ("The .bin is open O_RDWR for the build"), reading it, and restoring the write
// cursor.
//
// Under O_WRONLY every ::read() on that fd fails with EBADF and returns -1.
// Page::deserialize() then yields an EMPTY page rather than an error, so the
// reader drew a blank screen for any chapter whose build had not finalized --
// i.e. every chapter big enough to need a windowed build. Changing the font
// family or size is the everyday way to land in that state: the new font ID
// invalidates the section cache ("Deserialization failed: Parameters do not
// match"), the rebuild starts, and the page comes back empty.
bool HalStorage::openFileForWrite(const char *moduleName, const char *path,
                                  HalFile &file) {
  file = open(path, O_RDWR | O_CREAT | O_TRUNC);
  return file.isOpen();
}
bool HalStorage::openFileForWrite(const char *moduleName,
                                  const std::string &path, HalFile &file) {
  return openFileForWrite(moduleName, path.c_str(), file);
}
bool HalStorage::openFileForWrite(const char *moduleName, const String &path,
                                  HalFile &file) {
  return openFileForWrite(moduleName, path.c_str(), file);
}

std::vector<String> HalStorage::listFiles(const char *path, int maxFiles) {
  std::vector<String> result;
  std::string full = resolveStoragePath(path);
  if (full.empty()) {
    return result;
  }
  DIR *dir = opendir(full.c_str());
  if (!dir)
    return result;
  struct dirent *entry;
  while ((entry = readdir(dir)) != nullptr && (int)result.size() < maxFiles) {
    const char *nm = entry->d_name;
    if (nm[0] == '.' && (nm[1] == '\0' || (nm[1] == '.' && nm[2] == '\0')))
      continue; // skip . and .. only — device SdFat returns dotfiles
    result.push_back(String(nm));
  }
  closedir(dir);
  return result;
}
