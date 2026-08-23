// The CPZ1 block-compressed container, end to end: the Python writer
// (tools/compress_seed_fonts.py) and the C++ reader (src/SimCompressedFile.h)
// against each other and against the original bytes.
//
// WHY A TEST AND NOT A LOOK AT THE PICTURE. Every failure mode here is silent
// or nearly so. A container that decodes to almost-right bytes gives a font
// with wrong glyph offsets, which renders as a page of the wrong letters or as
// nothing at all while the firmware logs successful renders -- the exact shape
// of the 2026-08-21 blank-page bug. A reader that returns a SHORT read instead
// of an error looks to SdCardFont like end of file. And a writer and reader
// that disagree about the header layout by four bytes still open, still parse,
// and still produce plausible garbage.
//
// So this drives the REAL writer through std::system rather than reimplementing
// its packing here: two implementations of one layout that agree with each
// other and not with the spec is the drift this is meant to catch.
//
// Build (see tests/run_all.sh):
//   c++ -std=c++17 -Isrc $(python3 tools/fw_include_flags.py) \
//       tests/cpz_container_test.cpp \
//       <firmware>/lib/miniz/src/InflateStream.cpp \
//       <firmware>/lib/miniz/src/miniz_impl.c -o /tmp/cpz_container_test

#include "SimCompressedFile.h"

// The repo root, so the writer can be found however the test is invoked.
// tests/run_all.sh passes it; a hand build from the repo root gets the default.
#ifndef CPZ_REPO_ROOT
#define CPZ_REPO_ROOT "."
#endif

#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    ++failures;
  }
}

namespace {

std::string g_dir;

std::string path(const char *leaf) { return g_dir + "/" + leaf; }

std::vector<unsigned char> readAll(const std::string &p) {
  std::vector<unsigned char> out;
  const int fd = ::open(p.c_str(), O_RDONLY);
  if (fd < 0) return out;
  unsigned char buf[65536];
  for (;;) {
    const ssize_t n = ::read(fd, buf, sizeof(buf));
    if (n <= 0) break;
    out.insert(out.end(), buf, buf + n);
  }
  ::close(fd);
  return out;
}

void writeAll(const std::string &p, const std::vector<unsigned char> &bytes) {
  const int fd = ::open(p.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
  if (fd < 0) {
    std::printf("FAIL: cannot write %s\n", p.c_str());
    ++failures;
    return;
  }
  if (!bytes.empty()) {
    (void)!::write(fd, bytes.data(), bytes.size());
  }
  ::close(fd);
}

// A payload shaped like a .cpfont's bitmap section: long runs of zero (54 % of
// a real file is zero bytes) with structured noise between them, so the blocks
// actually compress and the test is measuring the real path rather than
// incompressible random data that deflate would store verbatim.
std::vector<unsigned char> fontish(size_t bytes, uint32_t seed) {
  std::mt19937 rng(seed);
  std::vector<unsigned char> out;
  out.reserve(bytes);
  while (out.size() < bytes) {
    const size_t run = 1 + (rng() % 64);
    if (rng() % 3 == 0) {
      out.insert(out.end(), run, 0);
    } else {
      for (size_t i = 0; i < run && out.size() < bytes; ++i) {
        out.push_back(static_cast<unsigned char>(rng() % 4) * 0x55u);
      }
    }
  }
  out.resize(bytes);
  return out;
}

// Runs the shipped writer over a one-file tree and returns the container path.
std::string pack(const std::vector<unsigned char> &payload, const char *name,
                 int block) {
  const std::string in = path("in");
  const std::string out = path("out");
  ::mkdir(in.c_str(), 0777);
  ::mkdir(out.c_str(), 0777);
  const std::string src = in + "/" + name + ".cpfont";
  const std::string dst = out + "/" + name + ".cpfont";
  ::unlink(dst.c_str());
  writeAll(src, payload);
  char cmd[1024];
  std::snprintf(cmd, sizeof(cmd),
                "python3 '%s/tools/compress_seed_fonts.py' --input '%s' "
                "--output '%s' --block %d --quiet >/dev/null 2>&1",
                CPZ_REPO_ROOT, in.c_str(), out.c_str(), block);
  if (std::system(cmd) != 0) {
    std::printf("FAIL: writer failed for %s\n", name);
    ++failures;
    return {};
  }
  return dst;
}

void testRoundTrip() {
  const std::vector<unsigned char> payload = fontish(500000, 1);
  const std::string container = pack(payload, "RoundTrip", 4096);
  if (container.empty()) return;

  const auto packed = readAll(container);
  check(packed.size() < payload.size(),
        "the container is smaller than what it wraps");
  check(std::memcmp(packed.data(), simcpz::kMagic, 4) == 0,
        "the writer emits the magic the reader sniffs for");

  const int fd = ::open(container.c_str(), O_RDONLY);
  SimCpzFile file;
  check(file.open(fd, container.c_str()), "a written container opens");
  check(file.size() == payload.size(),
        "size() answers the PAYLOAD length, not the file's -- Content-Length "
        "and every firmware length check read this");

  // Sequential, in chunk sizes that straddle block boundaries in both
  // directions: a chunk smaller than a block, one larger, one coprime.
  for (size_t chunk : {1u, 7u, 4095u, 4096u, 4097u, 100000u}) {
    std::vector<unsigned char> got(payload.size());
    size_t at = 0;
    while (at < got.size()) {
      const int n = file.read(at, got.data() + at,
                              std::min(chunk, got.size() - at));
      if (n <= 0) break;
      at += static_cast<size_t>(n);
    }
    check(at == payload.size() && got == payload,
          "sequential read reproduces the payload byte for byte");
  }

  // Random access, which is the whole reason the container is blocked at all:
  // SdCardFont seeks per glyph run.
  std::mt19937 rng(99);
  bool exact = true;
  for (int i = 0; i < 400; ++i) {
    const size_t off = rng() % payload.size();
    const size_t len = 1 + (rng() % 9000);
    std::vector<unsigned char> got(len, 0xAB);
    const int n = file.read(off, got.data(), len);
    const size_t want = std::min(len, payload.size() - off);
    if (n != static_cast<int>(want) ||
        std::memcmp(got.data(), payload.data() + off, want) != 0) {
      exact = false;
      break;
    }
  }
  check(exact, "400 random (offset, length) reads all match the payload");

  check(file.read(payload.size(), nullptr, 0) == 0,
        "a read at exactly EOF returns 0, not an error");
  unsigned char one = 0;
  check(file.read(payload.size() + 10, &one, 1) == 0,
        "a read past EOF returns 0");
  ::close(fd);
}

// A payload shorter than one block: the single-block case, where blockCount is
// 1 and the tail is partial. Its own test because ceil() arithmetic that is
// wrong by one is invisible everywhere else.
void testShortPayload() {
  const std::vector<unsigned char> payload = fontish(700, 2);
  const std::string container = pack(payload, "Short", 1024);
  if (container.empty()) return;
  const int fd = ::open(container.c_str(), O_RDONLY);
  SimCpzFile file;
  check(file.open(fd, container.c_str()), "a sub-block container opens");
  check(file.size() == payload.size(), "a sub-block container reports its size");
  std::vector<unsigned char> got(payload.size());
  check(file.read(0, got.data(), got.size()) ==
            static_cast<int>(payload.size()) &&
        got == payload, "a sub-block container round trips");
  ::close(fd);
}

// Every way the header can be wrong must FAIL THE OPEN. Falling back to the raw
// bytes would hand container headers to the font loader as glyph data.
void testHeaderRejection() {
  const std::vector<unsigned char> payload = fontish(200000, 3);
  const std::string container = pack(payload, "Reject", 8192);
  if (container.empty()) return;
  const auto good = readAll(container);

  struct Case {
    const char *what;
    size_t at;
    unsigned char value;
  };
  // blockSize below the floor (offset 4) and above the ceiling (offset 7), and
  // a blockCount that no longer equals ceil(size / blockSize) (offset 16).
  const Case cases[] = {
      {"blockSize under the 1 KiB floor", 5, 0},
      {"blockSize over the 1 MiB ceiling", 7, 0xFF},
      {"blockCount disagreeing with the size", 16, 0xFE},
  };
  for (const Case &c : cases) {
    auto bad = good;
    bad[c.at] = c.value;
    const std::string p = path("bad.cpfont");
    writeAll(p, bad);
    const int fd = ::open(p.c_str(), O_RDONLY);
    SimCpzFile file;
    check(!file.open(fd, p.c_str()), c.what);
    ::close(fd);
  }

  // The same disagreement from the other side: a payload length one whole
  // block longer than the index can describe. Computed rather than written as
  // a byte poke, so it stays true if the test payload changes size.
  {
    auto bad = good;
    simcpz::Header h{};
    if (simcpz::parseHeader(bad.data(), bad.size(), h)) {
      const uint64_t grown = h.originalSize + h.blockSize;
      std::memcpy(bad.data() + 8, &grown, 8);
      const std::string p = path("grown.cpfont");
      writeAll(p, bad);
      const int fd = ::open(p.c_str(), O_RDONLY);
      SimCpzFile file;
      check(!file.open(fd, p.c_str()),
            "an originalSize the block index cannot cover is refused");
      ::close(fd);
    }
  }

  // A non-monotonic block index. Byte 0 of the LAST index entry, dropped to
  // zero, makes that block's computed length negative.
  {
    auto bad = good;
    simcpz::Header h{};
    check(simcpz::parseHeader(bad.data(), bad.size(), h),
          "the good container's header parses");
    if (h.blockCount >= 2) {
      const size_t last = simcpz::kHeaderBytes + 4u * (h.blockCount - 1);
      bad[last] = 0;
      bad[last + 1] = 0;
      bad[last + 2] = 0;
      bad[last + 3] = 0;
      const std::string p = path("nonmono.cpfont");
      writeAll(p, bad);
      const int fd = ::open(p.c_str(), O_RDONLY);
      SimCpzFile file;
      check(!file.open(fd, p.c_str()), "a non-monotonic block index is refused");
      ::close(fd);
    }
  }

  // Truncated to less than a header.
  {
    std::vector<unsigned char> stub(good.begin(), good.begin() + 12);
    const std::string p = path("stub.cpfont");
    writeAll(p, stub);
    const int fd = ::open(p.c_str(), O_RDONLY);
    SimCpzFile file;
    check(!file.open(fd, p.c_str()), "a file too short to hold a header is refused");
    ::close(fd);
  }
}

// A block whose bytes have been damaged must make read() return -1. Returning
// what it managed to inflate would be a short read, which SdCardFont's
// `read(...) != dataLength` check reports as "short bitmap read" -- true but
// misleading -- and returning the damaged bytes would be silent.
void testCorruptBlockIsLoud() {
  const std::vector<unsigned char> payload = fontish(300000, 4);
  const std::string container = pack(payload, "Corrupt", 8192);
  if (container.empty()) return;
  auto bad = readAll(container);
  simcpz::Header h{};
  check(simcpz::parseHeader(bad.data(), bad.size(), h), "corrupt case parses first");
  // Scribble over the middle of the compressed data, past the index.
  const size_t start = static_cast<size_t>(simcpz::dataStart(h));
  for (size_t i = start + 64; i < start + 256 && i < bad.size(); ++i) {
    bad[i] ^= 0xFFu;
  }
  const std::string p = path("corrupt.cpfont");
  writeAll(p, bad);
  const int fd = ::open(p.c_str(), O_RDONLY);
  SimCpzFile file;
  check(file.open(fd, p.c_str()), "a container with intact header still opens");
  std::vector<unsigned char> got(payload.size());
  const int n = file.read(0, got.data(), got.size());
  check(n == -1 || got != payload,
        "a damaged block is reported, never silently wrong");
  check(n <= 0, "a damaged block does not come back as a short read");
  ::close(fd);
}

// parseHeader is the gate everything else stands on, and it is pure.
void testParseHeaderIsPure() {
  unsigned char buf[simcpz::kHeaderBytes] = {};
  simcpz::Header h{};
  check(!simcpz::parseHeader(buf, sizeof(buf), h), "an all-zero header is refused");
  std::memcpy(buf, simcpz::kMagic, 4);
  const uint32_t block = 4096;
  const uint64_t size = 4096ull * 3 + 17;
  std::memcpy(buf + 4, &block, 4);
  std::memcpy(buf + 8, &size, 8);
  uint32_t count = 4;
  std::memcpy(buf + 16, &count, 4);
  check(simcpz::parseHeader(buf, sizeof(buf), h), "a consistent header parses");
  check(h.blockSize == block && h.originalSize == size && h.blockCount == count,
        "the parsed fields are the written fields");
  check(simcpz::dataStart(h) == simcpz::kHeaderBytes + 4 * count,
        "data starts after the header and the whole index");
  count = 3;  // one short: the 17-byte tail block would have nowhere to live
  std::memcpy(buf + 16, &count, 4);
  check(!simcpz::parseHeader(buf, sizeof(buf), h),
        "a blockCount one short of ceil() is refused");
}

}  // namespace

int main(int argc, char **argv) {
  // A scratch directory for the containers this writes and damages. Given as
  // argv[1] when a caller wants it somewhere specific.
  g_dir = argc > 1 ? argv[1] : "/tmp/cpz_container_test_dir";
  ::mkdir(g_dir.c_str(), 0777);

  testParseHeaderIsPure();
  testRoundTrip();
  testShortPayload();
  testHeaderRejection();
  testCorruptBlockIsLoud();

  if (failures == 0) {
    std::printf("cpz_container_test: all checks passed\n");
    return 0;
  }
  std::printf("cpz_container_test: %d FAILED\n", failures);
  return 1;
}
