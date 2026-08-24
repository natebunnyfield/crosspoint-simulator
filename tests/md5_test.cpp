// The host MD5Builder shim, against the published RFC 1321 test suite.
//
// SAME ARGUMENT AS sha256_test, never applied here until now. That shim WAS a
// fake once -- `digest[i % 32] ^= input[i]`, returning success -- and nothing in
// the build could see it, because a wrong digest has the right signature, the
// right length and perfect determinism. Only a known-answer vector catches such
// a thing.
//
// The exposure here is different and slightly worse: src/MD5Builder.h is a
// DISPATCHER over two implementations that must agree -- CommonCrypto on macOS,
// OpenSSL on Linux -- and neither had a single vector. A divergence between
// them is not even a wrong answer on one machine; it is the same book hashing
// two ways on two developers' machines, which the firmware's file-transfer and
// font-download paths compare.
//
// So this file tests whatever implementation the HOST selected. It is meant to
// be run on both platforms; each run pins that platform's half against the same
// published constants, which is what makes "they agree" a checkable claim
// rather than an assumption.
#include "MD5Builder.h"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>

#include "TestCheck.h"

using testcheck::check;
using testcheck::checkEq;

namespace {

// The one-shot path, through the same call sequence the firmware uses.
std::string md5Of(const void *data, size_t len) {
  MD5Builder b;
  b.begin();
  b.add(static_cast<const uint8_t *>(data), len);
  b.calculate();
  return b.toString().s;
}

std::string md5Of(const char *s) {
  MD5Builder b;
  b.begin();
  b.add(s);
  b.calculate();
  return b.toString().s;
}

// ------------------------------------------------------------- RFC 1321 A.5 --
//
// "MD5 test suite", verbatim. These seven are the whole published set.
void testRfc1321Vectors() {
  checkEq(md5Of(""), "d41d8cd98f00b204e9800998ecf8427e", "RFC 1321: \"\"");
  checkEq(md5Of("a"), "0cc175b9c0f1b6a831c399e269772661", "RFC 1321: \"a\"");
  checkEq(md5Of("abc"), "900150983cd24fb0d6963f7d28e17f72", "RFC 1321: \"abc\"");
  checkEq(md5Of("message digest"), "f96b697d7cb7938d525a2f31aaf161d0",
          "RFC 1321: \"message digest\"");
  checkEq(md5Of("abcdefghijklmnopqrstuvwxyz"),
          "c3fcd3d76192e4007dfb496cca67e13b", "RFC 1321: a-z");
  checkEq(md5Of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"),
          "d174ab98d277d9f5a5611c2c9f419d9f", "RFC 1321: A-Za-z0-9");
  checkEq(md5Of("123456789012345678901234567890123456789012345678901234567890"
                "12345678901234567890"),
          "57edf4a22be3c955ac49da2e2107b67a", "RFC 1321: eighty digits");
}

// ---------------------------------------------------------- the block edges --
//
// MD5 buffers into 64-byte blocks and appends a length. The vectors above
// straddle a block boundary only once (the 80-digit one, at 80 bytes), so these
// pin the edges themselves -- 55, 56, 63, 64 and 65 bytes, where 56 is the
// length at which the padding no longer fits in the final block and a second
// one is emitted. A shim that mishandled that would pass every short vector.
void testBlockBoundaries() {
  // Computed with the reference algorithm; each is `n` repetitions of 'a'.
  struct { int n; const char *want; } kCases[] = {
      {55, "ef1772b6dff9a122358552954ad0df65"},
      {56, "3b0c8ac703f828b04c6c197006d17218"},
      {63, "b06521f39153d618550606be297466d5"},
      {64, "014842d480b571495a4a0363793f7367"},
      {65, "c743a45e0d2e6a95cb859adae0248435"},
  };
  for (const auto &c : kCases) {
    const std::string in(static_cast<size_t>(c.n), 'a');
    const std::string what =
        std::string("block edge: ") + std::to_string(c.n) + " x 'a'";
    checkEq(md5Of(in.data(), in.size()), c.want, what.c_str());
  }
}

// -------------------------------------------------------------- the streaming --
//
// The firmware hashes files in chunks, so add() is called many times before
// calculate(). A shim that reset its context per add, or that only ever hashed
// the last chunk, would pass every one-shot vector above and corrupt every
// file-transfer checksum.
void testChunkedMatchesOneShot() {
  std::string big;
  for (int i = 0; i < 5000; i++) big += static_cast<char>('a' + (i % 26));
  const std::string oneShot = md5Of(big.data(), big.size());

  for (size_t chunk : {size_t(1), size_t(7), size_t(63), size_t(64),
                       size_t(65), size_t(1024)}) {
    MD5Builder b;
    b.begin();
    for (size_t off = 0; off < big.size(); off += chunk) {
      const size_t n = std::min(chunk, big.size() - off);
      b.add(reinterpret_cast<const uint8_t *>(big.data() + off), n);
    }
    b.calculate();
    const std::string what = std::string("chunked at ") +
                             std::to_string(chunk) +
                             " matches the one-shot digest";
    checkEq(b.toString().s, oneShot, what.c_str());
  }
}

// ----------------------------------------------------------------- the shape --

void testSurface() {
  // toString is 32 LOWERCASE hex digits. The firmware compares these as
  // strings, so a case change or a stray prefix is a mismatch on every file.
  const std::string d = md5Of("abc");
  checkEq(static_cast<int>(d.size()), 32, "the digest prints as 32 characters");
  bool lowerHex = true;
  for (char ch : d)
    if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f'))) lowerHex = false;
  check(lowerHex, "...all of them lowercase hex");

  // add(const char *) must tolerate null -- it is reached from firmware paths
  // that pass a possibly-absent header value -- and must then hash nothing,
  // giving the empty digest rather than reading through the pointer.
  {
    MD5Builder b;
    b.begin();
    b.add(static_cast<const char *>(nullptr));
    b.calculate();
    checkEq(b.toString().s, "d41d8cd98f00b204e9800998ecf8427e",
            "add(nullptr) hashes nothing rather than dereferencing it");
  }

  // The two add() overloads agree: the char* one is documented as strlen of the
  // pointer form, and a firmware caller picks whichever it has.
  checkEq(md5Of("message digest"),
          md5Of("message digest", sizeof("message digest") - 1),
          "add(const char *) and add(bytes, len) agree");

  // A fresh builder that never adds anything still produces the empty digest,
  // not the zeroed constructor state -- begin() must actually initialize.
  {
    MD5Builder b;
    b.begin();
    b.calculate();
    checkEq(b.toString().s, "d41d8cd98f00b204e9800998ecf8427e",
            "begin() + calculate() with no data is the empty-string digest");
  }
}

}  // namespace

int main() {
  testRfc1321Vectors();
  testBlockBoundaries();
  testChunkedMatchesOneShot();
  testSurface();

  if (testcheck::g_failures) {
    std::printf("%d failure(s)\n", testcheck::g_failures);
    return 1;
  }
  std::printf("md5: all checks passed\n");
  return 0;
}
