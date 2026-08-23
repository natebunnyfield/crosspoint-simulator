#pragma once

// A block-compressed container the HAL's file layer opens transparently.
//
// WHY IT EXISTS. The iOS app ships every seeded font family inside its bundle
// and CrossPointFsPrep symlinks each family into the emulated card, so the
// bundle copy IS the card copy and the install cost is paid once. It is still
// the whole cost: `.cpfont` stores 2-bit glyph bitmaps raw
// (fontconvert_sdcard.py's own docstring says so), 108 MB of the 118 MB the
// 1x+2x tiers occupy, at 2.4 bits/byte of entropy. The IPA's zip already
// compresses them 3.4:1 for the DOWNLOAD and then expands them on the phone,
// which is exactly the gap this closes: compressed on disk, expanded only in
// the 32 KB the reader is looking at.
//
// WHY AT THE FILE LAYER AND NOT IN THE FORMAT. `.cpfont` is random-access by
// construction -- SdCardFont::prewarmStyle seeks per glyph run and the overflow
// ring does an open+seek+read for a single glyph -- so a whole-file stream is
// unusable and per-block groups inside the format would mean a CPFONT_VERSION
// bump, a new read path in firmware code the DEVICE also compiles, and
// re-emitting every published font pack. None of that is what "compress fonts
// in the iOS app" asked for. HalFile is host-only by definition (the device
// has SdFat), it is the single choke point every firmware read already goes
// through, and it keeps the filename: SdCardFontRegistry still sees
// `Edgar_14.cpfont`, WebDAV still serves the real bytes at the real length,
// and the firmware never learns that anything happened.
//
// WHY IT IS LOUD. A font that fails to load is a BLANK PAGE with successful
// renders in the log (firmware 2026-08-21, ios/CMakeLists.txt's OMIT_FONTS
// note). So a file carrying this magic that does not parse, or a block that
// does not inflate, fails the open or the read and says why on stderr. It is
// never allowed to degrade into handing the caller container bytes as if they
// were font bytes -- that is the failure that looks like a rendering bug.

#include <InflateStream.h>

#include <unistd.h>

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace simcpz {

// "CPZ1". Cannot collide with the payloads this wraps: a .cpfont opens with
// "CPFONT\0\0" and an epub with "PK\3\4".
inline constexpr unsigned char kMagic[4] = {'C', 'P', 'Z', '1'};

// magic(4) + blockSize(4) + originalSize(8) + blockCount(4) + reserved(4).
inline constexpr uint32_t kHeaderBytes = 24;

// Guard rails on the header's own numbers, because every field below is read
// from a file and used to size an allocation. The floor keeps the block index
// from dwarfing the data; the ceiling is what bounds the reader's two buffers.
inline constexpr uint32_t kMinBlockSize = 1024;
inline constexpr uint32_t kMaxBlockSize = 1u << 20;

inline uint32_t readU32(const unsigned char *p) {
  return static_cast<uint32_t>(p[0]) | (static_cast<uint32_t>(p[1]) << 8) |
         (static_cast<uint32_t>(p[2]) << 16) |
         (static_cast<uint32_t>(p[3]) << 24);
}

inline uint64_t readU64(const unsigned char *p) {
  return static_cast<uint64_t>(readU32(p)) |
         (static_cast<uint64_t>(readU32(p + 4)) << 32);
}

struct Header {
  uint32_t blockSize = 0;
  uint64_t originalSize = 0;
  uint32_t blockCount = 0;
};

// True only for a header whose four fields agree with each other. blockCount is
// DERIVED, not trusted: it must be exactly ceil(originalSize / blockSize), so a
// truncated or hand-edited container is rejected here rather than by an
// out-of-range index later.
inline bool parseHeader(const unsigned char *buf, size_t len, Header &out) {
  if (len < kHeaderBytes) return false;
  if (std::memcmp(buf, kMagic, sizeof(kMagic)) != 0) return false;
  const uint32_t blockSize = readU32(buf + 4);
  const uint64_t originalSize = readU64(buf + 8);
  const uint32_t blockCount = readU32(buf + 16);
  if (blockSize < kMinBlockSize || blockSize > kMaxBlockSize) return false;
  // The ceiling-divide OVERFLOWS for a large originalSize, and a crafted header
  // can aim the wrap at zero: 0xFFFF...FFFF with a 1024-byte block wraps to
  // 1022, giving expected = 0, which matches a declared blockCount of 0. The
  // header then PARSES, open() succeeds with an empty block index, and the
  // first read indexes it -- a segfault on file content, reached from any
  // read-only open of any file on the card, not only a font. Found by
  // adversarial review 2026-08-23 and reproduced under ASan from a 24-byte
  // file.
  if (originalSize > UINT64_MAX - (blockSize - 1)) return false;
  const uint64_t expected = (originalSize + blockSize - 1) / blockSize;
  if (expected != blockCount) return false;
  // ...and state the relationship the division only implies, so a zero count
  // can never coexist with a payload.
  if ((blockCount == 0) != (originalSize == 0)) return false;
  out.blockSize = blockSize;
  out.originalSize = originalSize;
  out.blockCount = blockCount;
  return true;
}

inline uint64_t dataStart(const Header &h) {
  return kHeaderBytes + 4ull * h.blockCount;
}

}  // namespace simcpz

// Random-access reader over one container, holding exactly one inflated block.
//
// ONE BLOCK IS ENOUGH because the access pattern is sorted-ascending: prewarm
// sorts its glyph reads by file offset before it issues them
// (SdCardFont.cpp's `std::sort(readOrder ...)`), so a page walks blocks
// forward and touches each once. The pathological case -- the overflow ring
// asking for one glyph at a time from scattered offsets -- costs one 32 KB
// inflate per glyph, which is the same order as the SD read it replaces.
//
// Borrows the fd; the owner (HalFile::Impl) closes it.
class SimCpzFile {
 public:
  bool open(int fd, const char *path) {
    unsigned char head[simcpz::kHeaderBytes];
    if (::pread(fd, head, sizeof(head), 0) !=
        static_cast<ssize_t>(sizeof(head))) {
      complain(path, "header short read");
      return false;
    }
    if (!simcpz::parseHeader(head, sizeof(head), header_)) {
      complain(path, "header did not parse");
      return false;
    }
    ends_.resize(header_.blockCount);
    if (header_.blockCount > 0) {
      std::vector<unsigned char> raw(4ull * header_.blockCount);
      if (::pread(fd, raw.data(), raw.size(), simcpz::kHeaderBytes) !=
          static_cast<ssize_t>(raw.size())) {
        complain(path, "block index short read");
        return false;
      }
      // Cumulative END offsets, so a block's extent is a subtraction and the
      // index needs no separate length column. Monotonic by construction, and
      // checked: a non-increasing pair would compute a negative length.
      uint32_t previous = 0;
      for (uint32_t i = 0; i < header_.blockCount; ++i) {
        ends_[i] = simcpz::readU32(raw.data() + 4ull * i);
        if (ends_[i] < previous) {
          complain(path, "block index is not monotonic");
          return false;
        }
        previous = ends_[i];
      }
    }
    fd_ = fd;
    dataStart_ = simcpz::dataStart(header_);
    path_ = path;
    return true;
  }

  uint64_t size() const { return header_.originalSize; }

  // Reads up to `count` bytes at logical offset `off`. Returns the number of
  // bytes produced, or -1 when a block will not inflate — never a short read
  // that a caller could mistake for end of file.
  int read(uint64_t off, void *dst, size_t count) {
    if (fd_ < 0) return -1;
    if (off >= header_.originalSize) return 0;
    const uint64_t remaining = header_.originalSize - off;
    if (count > remaining) count = static_cast<size_t>(remaining);
    unsigned char *out = static_cast<unsigned char *>(dst);
    size_t done = 0;
    while (done < count) {
      const uint64_t at = off + done;
      const uint32_t index = static_cast<uint32_t>(at / header_.blockSize);
      if (!loadBlock(index)) return -1;
      const uint32_t within = static_cast<uint32_t>(at % header_.blockSize);
      size_t take = blockLen_ - within;
      if (take > count - done) take = count - done;
      std::memcpy(out + done, block_.data() + within, take);
      done += take;
    }
    return static_cast<int>(done);
  }

 private:
  bool loadBlock(uint32_t index) {
    if (cached_ == index) return true;
    const uint32_t begin = index == 0 ? 0 : ends_[index - 1];
    const uint32_t compressed = ends_[index] - begin;
    comp_.resize(compressed);
    if (compressed != 0 &&
        ::pread(fd_, comp_.data(), compressed, dataStart_ + begin) !=
            static_cast<ssize_t>(compressed)) {
      complain(path_.c_str(), "block short read");
      return false;
    }
    uint64_t plain = header_.originalSize -
                     static_cast<uint64_t>(index) * header_.blockSize;
    if (plain > header_.blockSize) plain = header_.blockSize;
    block_.resize(header_.blockSize);
    // One-shot mode: the destination holds the whole block, so back-references
    // resolve inside it and no 32 KB window is allocated. init() reuses the
    // decompressor state across blocks and resets the stream, which is why it
    // is called per block rather than once.
    if (!inflate_.init(false)) {
      complain(path_.c_str(), "inflate state allocation failed");
      return false;
    }
    inflate_.setSource(comp_.data(), compressed);
    if (!inflate_.read(block_.data(), static_cast<size_t>(plain))) {
      complain(path_.c_str(), "block did not inflate");
      cached_ = UINT32_MAX;
      return false;
    }
    cached_ = index;
    blockLen_ = static_cast<uint32_t>(plain);
    return true;
  }

  static void complain(const char *path, const char *what) {
    // Same channel and prefix as HalStorage's own open failures. A silent
    // version of this is a blank page.
    std::fprintf(stderr, "[SIM] cpz %s: %s\n", path ? path : "?", what);
  }

  int fd_ = -1;
  std::string path_;
  simcpz::Header header_{};
  std::vector<uint32_t> ends_;
  uint64_t dataStart_ = 0;
  std::vector<unsigned char> comp_;
  std::vector<unsigned char> block_;
  uint32_t cached_ = UINT32_MAX;
  uint32_t blockLen_ = 0;
  InflateStream inflate_;
};
